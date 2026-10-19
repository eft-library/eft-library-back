"""Location socket authentication with explicit invalid-token vs outage handling."""
import asyncio
import logging
import os
from contextlib import suppress

import requests
from fastapi import HTTPException, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

logger_v3 = logging.getLogger('ws.location.auth.v3')


def verify_location_token_v3(token_v3):
    url_v3 = os.getenv('GOOGLE_TOKEN_INFO_URL')
    if not url_v3:
        raise HTTPException(503, 'AUTH_SERVICE_UNAVAILABLE')
    try:
        response_v3 = requests.get(url_v3, params={'access_token':token_v3}, timeout=5)
        if response_v3.status_code in (400, 401):
            raise HTTPException(401, 'AUTH_REQUIRED')
        if response_v3.status_code != 200:
            raise HTTPException(503, 'AUTH_SERVICE_UNAVAILABLE')
        data_v3 = response_v3.json()
        if not isinstance(data_v3, dict) or not isinstance(data_v3.get('email'), str) or not data_v3['email']:
            raise HTTPException(503, 'AUTH_SERVICE_UNAVAILABLE')
        return data_v3['email']
    except (requests.RequestException, ValueError):
        raise HTTPException(503, 'AUTH_SERVICE_UNAVAILABLE') from None


async def authenticate_location_socket_v3(websocket_v3, token_v3):
    try:
        return await run_in_threadpool(verify_location_token_v3, token_v3)
    except HTTPException as error_v3:
        expired_v3 = error_v3.status_code == 401
        logger_v3.info('location_auth_failed status=%s', error_v3.status_code)
        # Accept the transport before closing so browsers receive a close code,
        # rather than an opaque HTTP handshake failure / 1006.
        with suppress(WebSocketDisconnect, RuntimeError, TimeoutError, OSError):
            await asyncio.wait_for(websocket_v3.accept(), 5)
            await asyncio.wait_for(websocket_v3.send_json({
                'type':'location_connection_status',
                'status':'auth-required' if expired_v3 else 'reconnecting',
            }), 5)
            await asyncio.wait_for(websocket_v3.close(code=4401 if expired_v3 else 1013), 5)
        return None
