import hashlib
import hmac
import os
import secrets
from functools import lru_cache

import requests
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from redis.exceptions import RedisError


bearer_v3 = HTTPBearer(auto_error=False)


def authenticate_party_user_v3(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_v3),
) -> str:
    if credentials is None:
        raise HTTPException(401, "LOGIN_REQUIRED", headers={"WWW-Authenticate": "Bearer"})
    url = os.getenv("GOOGLE_TOKEN_INFO_URL")
    if not url:
        raise HTTPException(503, "AUTH_UNAVAILABLE")
    try:
        response = requests.get(url, params={"access_token": credentials.credentials}, timeout=5)
        if response.status_code >= 500 or response.status_code == 429:
            raise HTTPException(503, "AUTH_UNAVAILABLE")
        if response.status_code != 200:
            raise HTTPException(401, "INVALID_TOKEN", headers={"WWW-Authenticate": "Bearer"})
        payload = response.json()
    except (requests.RequestException, ValueError):
        raise HTTPException(503, "AUTH_UNAVAILABLE") from None
    if not isinstance(payload, dict):
        raise HTTPException(503, "AUTH_UNAVAILABLE")
    email = payload.get("email")
    verified = payload.get("verified_email", payload.get("email_verified", True))
    if not isinstance(email, str) or not email.strip() or verified in (False, "false"):
        raise HTTPException(401, "INVALID_TOKEN", headers={"WWW-Authenticate": "Bearer"})
    return email


class PartyPasswordV3:
    @staticmethod
    def hash_v3(password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(
            password.encode(), salt=salt, n=32768, r=8, p=1, maxmem=64 * 1024 * 1024,
        )
        return f"scrypt-v3${salt.hex()}${digest.hex()}"

    @staticmethod
    def verify_v3(password: str, encoded: str) -> bool:
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


class PartyRateLimiterV3:
    # INCR and expiry are atomic across workers, including concurrent failed attempts.
    script_v3 = """
        local count = redis.call('INCR', KEYS[1])
        if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
        return {count, redis.call('TTL', KEYS[1])}
    """

    def __init__(self, client: Redis):
        self.client = client

    def consume_v3(self, email: str, action: str, limit: int, seconds: int = 60):
        identity = hashlib.sha256(email.encode()).hexdigest()
        try:
            count, ttl = self.client.eval(
                self.script_v3, 1, f"live-map:party:v3:rate:{action}:{identity}", seconds,
            )
        except RedisError:
            raise HTTPException(503, "PARTY_RATE_LIMIT_UNAVAILABLE") from None
        if int(count) > limit:
            raise HTTPException(429, "TOO_MANY_ATTEMPTS", headers={"Retry-After": str(max(1, int(ttl)))})


@lru_cache(maxsize=1)
def get_party_rate_limiter_v3() -> PartyRateLimiterV3:
    url = os.getenv("REDIS_URL")
    host = os.getenv("REDIS_HOST")
    if not url and not host:
        raise HTTPException(503, "PARTY_RATE_LIMIT_UNAVAILABLE")
    return PartyRateLimiterV3(Redis.from_url(
        url or f"redis://{host}", decode_responses=True,
        socket_connect_timeout=2, socket_timeout=2,
    ))
