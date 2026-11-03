"""Location socket authentication with explicit invalid-token vs outage handling."""
import asyncio
import logging
import os
from contextlib import suppress

import requests
from fastapi import HTTPException, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from util.http_exceptions import HttpError

logger = logging.getLogger('ws.location.auth.v3')


def verify_location_token(token):
    url = os.getenv('GOOGLE_TOKEN_INFO_URL')
    if not url:
        raise HttpError.AUTH_SERVICE_UNAVAILABLE.exception()
    try:
        api_response = requests.get(url, params={'access_token':token}, timeout=5)
        if api_response.status_code in (400, 401):
            raise HttpError.AUTH_REQUIRED.exception()
        if api_response.status_code != 200:
            raise HttpError.AUTH_SERVICE_UNAVAILABLE.exception()
        data = api_response.json()
        if not isinstance(data, dict) or not isinstance(data.get('email'), str) or not data['email']:
            raise HttpError.AUTH_SERVICE_UNAVAILABLE.exception()
        return data['email']
    except (requests.RequestException, ValueError):
        raise HttpError.AUTH_SERVICE_UNAVAILABLE.exception() from None


async def authenticate_location_socket(websocket, token):
    try:
        return await run_in_threadpool(verify_location_token, token)
    except HTTPException as error:
        expired = error.status_code == 401
        logger.info('location_auth_failed status=%s', error.status_code)
        # Accept the transport before closing so browsers receive a close code,
        # rather than an opaque HTTP handshake failure / 1006.
        with suppress(WebSocketDisconnect, RuntimeError, TimeoutError, OSError):
            await asyncio.wait_for(websocket.accept(), 5)
            await asyncio.wait_for(websocket.send_json({
                'type':'location_connection_status',
                'status':'auth-required' if expired else 'reconnecting',
            }), 5)
            await asyncio.wait_for(websocket.close(code=4401 if expired else 1013), 5)
        return None
