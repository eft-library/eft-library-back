"""Bearer extraction and Google token validation for HTTP endpoints."""
import os

import requests
from fastapi import Request
from fastapi.security import OAuth2PasswordBearer

from util.http_exceptions import HttpError


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


def verify_google_access_token(access_token: str | None) -> str:
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
    if not isinstance(email, str) or not email.strip():
        raise HttpError.AUTH_SERVICE_UNAVAILABLE.exception()
    if data.get("verified_email", data.get("email_verified", True)) in (False, "false"):
        raise HttpError.INVALID_TOKEN.exception(headers={"WWW-Authenticate": "Bearer"})
    return email
