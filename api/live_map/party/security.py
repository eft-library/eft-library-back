import hashlib
import hmac
import os
import secrets
from functools import lru_cache

import requests
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from redis.exceptions import RedisError

from util.http_exceptions import HttpError


bearer = HTTPBearer(auto_error=False)


def authenticate_party_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    if credentials is None:
        raise HttpError.LOGIN_REQUIRED.exception(headers={"WWW-Authenticate": "Bearer"})
    url = os.getenv("GOOGLE_TOKEN_INFO_URL")
    if not url:
        raise HttpError.AUTH_UNAVAILABLE.exception()
    try:
        response = requests.get(url, params={"access_token": credentials.credentials}, timeout=5)
        if response.status_code >= 500 or response.status_code == 429:
            raise HttpError.AUTH_UNAVAILABLE.exception()
        if response.status_code != 200:
            raise HttpError.INVALID_TOKEN.exception(headers={"WWW-Authenticate": "Bearer"})
        payload = response.json()
    except (requests.RequestException, ValueError):
        raise HttpError.AUTH_UNAVAILABLE.exception() from None
    if not isinstance(payload, dict):
        raise HttpError.AUTH_UNAVAILABLE.exception()
    email = payload.get("email")
    verified = payload.get("verified_email", payload.get("email_verified", True))
    if not isinstance(email, str) or not email.strip() or verified in (False, "false"):
        raise HttpError.INVALID_TOKEN.exception(headers={"WWW-Authenticate": "Bearer"})
    return email


class PartyPassword:
    @staticmethod
    def hash(password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(
            password.encode(), salt=salt, n=32768, r=8, p=1, maxmem=64 * 1024 * 1024,
        )
        return f"scrypt-v3${salt.hex()}${digest.hex()}"

    @staticmethod
    def verify(password: str, encoded: str) -> bool:
        try:
            algorithm, salt_hex, digest_hex = encoded.split("$")
            if algorithm != "scrypt-v3":
                return False
            salt, expected = bytes.fromhex(salt_hex), bytes.fromhex(digest_hex)
            if len(salt) != 16 or len(expected) != 64:
                return False
            actual = hashlib.scrypt(
                password.encode(), salt=salt, n=32768, r=8, p=1, maxmem=64 * 1024 * 1024,
            )
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False


class PartyRateLimiter:
    # INCR and expiry are atomic across workers, including concurrent failed attempts.
    script = """
        local count = redis.call('INCR', KEYS[1])
        if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
        return {count, redis.call('TTL', KEYS[1])}
    """

    def __init__(self, client: Redis):
        self.client = client

    def consume(self, email: str, action: str, limit: int, seconds: int = 60):
        identity = hashlib.sha256(email.encode()).hexdigest()
        try:
            count, ttl = self.client.eval(
                self.script, 1, f"live-map:party:v3:rate:{action}:{identity}", seconds,
            )
        except RedisError:
            raise HttpError.PARTY_RATE_LIMIT_UNAVAILABLE.exception() from None
        if int(count) > limit:
            raise HttpError.TOO_MANY_ATTEMPTS.exception(headers={"Retry-After": str(max(1, int(ttl)))})


@lru_cache(maxsize=1)
def get_party_rate_limiter() -> PartyRateLimiter:
    url = os.getenv("REDIS_URL")
    host = os.getenv("REDIS_HOST")
    if not url and not host:
        raise HttpError.PARTY_RATE_LIMIT_UNAVAILABLE.exception()
    return PartyRateLimiter(Redis.from_url(
        url or f"redis://{host}", decode_responses=True,
        socket_connect_timeout=2, socket_timeout=2,
    ))
