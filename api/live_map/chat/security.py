from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from api.live_map.party.security import authenticate_party_user, bearer

GUEST_COOKIE_NAME = '__Host-chat_guest_v3'


def optional_chat_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str | None:
    # Only absent credentials select guest mode; invalid credentials never downgrade.
    if 'authorization' not in request.headers:
        return None
    if credentials is None:
        raise HTTPException(401, 'INVALID_TOKEN', headers={'WWW-Authenticate': 'Bearer'})
    return authenticate_party_user(credentials)
