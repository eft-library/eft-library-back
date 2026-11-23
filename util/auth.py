"""Bearer extraction and Google token validation for HTTP endpoints."""
import hashlib
import logging
import os
from typing import NamedTuple

import requests
from fastapi import Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import Database
from util.http_exceptions import HttpError

logger = logging.getLogger("api.auth.google")


class BearerToken(OAuth2PasswordBearer):
    def __init__(self, *, tokenUrl: str, auto_error: bool = True):
        super().__init__(tokenUrl=tokenUrl, auto_error=auto_error,
                         scheme_name="OAuth2PasswordBearer")

    async def __call__(self, request: Request) -> str | None:
        # Only an absent header is anonymous. A supplied malformed credential is not.
        if "authorization" not in request.headers:
            if not self.auto_error:
                return None
            raise HttpError.LOGIN_REQUIRED.exception(headers={"WWW-Authenticate": "Bearer"})
        token = await super().__call__(request)
        if not token or not token.strip():
            raise HttpError.INVALID_TOKEN.exception(headers={"WWW-Authenticate": "Bearer"})
        return token


class GoogleIdentity(NamedTuple):
    email: str
    subject: str | None
    email_verified: bool


def verify_google_identity(access_token: str | None) -> GoogleIdentity:
    if not isinstance(access_token, str) or not access_token.strip():
        raise HttpError.LOGIN_REQUIRED.exception(headers={"WWW-Authenticate": "Bearer"})
    url = os.getenv("GOOGLE_TOKEN_INFO_URL")
    if not url:
        raise HttpError.AUTH_SERVICE_UNAVAILABLE.exception()
    try:
        response = requests.get(url, params={"access_token": access_token}, timeout=5)
        if response.status_code in (400, 401):
            raise HttpError.INVALID_TOKEN.exception(headers={"WWW-Authenticate": "Bearer"})
        if response.status_code != 200:
            raise HttpError.AUTH_SERVICE_UNAVAILABLE.exception()
        data = response.json()
    except (requests.RequestException, ValueError):
        raise HttpError.AUTH_SERVICE_UNAVAILABLE.exception() from None
    if not isinstance(data, dict):
        raise HttpError.AUTH_SERVICE_UNAVAILABLE.exception()
    email = data.get("email")
    subject = data.get("sub") or data.get("user_id")
    subject_hash = (
        hashlib.sha256(subject.encode()).hexdigest()[:16]
        if isinstance(subject, str) else None
    )
    logger.info(
        "Google token info: email=%r subject_hash=%s email_fields=%s "
        "verified_email=%r email_verified=%r",
        email if isinstance(email, str) else None,
        subject_hash,
        sorted(key for key in data if "email" in key.lower()),
        data.get("verified_email") in (True, "true") if "verified_email" in data else None,
        data.get("email_verified") in (True, "true") if "email_verified" in data else None,
    )
    if not isinstance(email, str) or not email.strip():
        raise HttpError.AUTH_SERVICE_UNAVAILABLE.exception()
    verified = data.get("verified_email", data.get("email_verified"))
    if verified in (False, "false"):
        raise HttpError.INVALID_TOKEN.exception(headers={"WWW-Authenticate": "Bearer"})
    return GoogleIdentity(
        email,
        subject if isinstance(subject, str) and subject.strip() else None,
        verified in (True, "true"),
    )


def resolve_google_account_email(email: str, subject: str | None) -> str:
    if not isinstance(subject, str) or not subject.strip():
        return email
    try:
        with Database.SessionLocal() as session:
            account = session.execute(text("""
                SELECT email, google_sub
                FROM user_info
                WHERE google_sub = :subject OR email = :email
                ORDER BY CASE WHEN google_sub = :subject THEN 0 ELSE 1 END
                LIMIT 1
                """), {"subject": subject, "email": email}).one_or_none()
    except SQLAlchemyError:
        raise HttpError.AUTH_SERVICE_UNAVAILABLE.exception() from None
    if account is None:
        return email
    if account.google_sub is not None and account.google_sub != subject:
        raise HttpError.INVALID_TOKEN.exception(headers={"WWW-Authenticate": "Bearer"})
    return account.email


def verify_google_access_token(access_token: str | None) -> str:
    identity = verify_google_identity(access_token)
    return resolve_google_account_email(identity.email, identity.subject)
