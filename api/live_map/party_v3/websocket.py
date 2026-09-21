import asyncio
import json
import logging
import time
from contextlib import suppress
from uuid import UUID, uuid4

from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from .realtime_schemas import PartySocketAuthV3, socket_message_adapter_v3
from .realtime_service import PartyRealtimeServiceV3
from .realtime_store import party_redis_url_v3
from .security import authenticate_party_user_v3


logger_v3 = logging.getLogger("api.live_map.party_v3")


def create_party_subscriber_v3():
    return Redis.from_url(
        party_redis_url_v3(), decode_responses=True,
        socket_connect_timeout=2, socket_timeout=5,
    )


async def receive_packet_v3(websocket: WebSocket) -> str:
    packet = await websocket.receive()
    if packet["type"] == "websocket.disconnect":
        raise WebSocketDisconnect(packet.get("code", 1000))
    text = packet.get("text")
    if text is None:
        raise HTTPException(422, "TEXT_JSON_REQUIRED")
    if len(text.encode("utf-8")) > 8192:
        raise HTTPException(413, "MESSAGE_TOO_LARGE")
    return text


async def send_packet_v3(websocket: WebSocket, event: dict):
    # A slow tab cannot retain unlimited pending room events in application tasks.
    await asyncio.wait_for(websocket.send_json(event), timeout=5)


async def socket_error_v3(websocket: WebSocket, status: int, message: str, retry_after: str | None = None):
    await send_packet_v3(websocket, {
        "type": "error", "status": status, "msg": message,
        "retry_after": int(retry_after) if retry_after else None,
    })


async def subscribe_ready_v3(pubsub, channel: str):
    await pubsub.subscribe(channel)
    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=False, timeout=1)
        if message is not None and message["type"] == "subscribe":
            return


async def party_socket_handler_v3(websocket: WebSocket, room_id: UUID):
    await websocket.accept()
    connection = None
    service = None
    tasks = set()
    try:
        try:
            raw = await asyncio.wait_for(receive_packet_v3(websocket), timeout=10)
        except TimeoutError:
            raise HTTPException(408, "AUTH_TIMEOUT") from None
        try:
            auth = PartySocketAuthV3.model_validate_json(raw)
        except ValidationError:
            raise HTTPException(401, "AUTH_MESSAGE_REQUIRED") from None
        email = await run_in_threadpool(
            authenticate_party_user_v3,
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=auth.token.get_secret_value()),
        )
        service = await run_in_threadpool(PartyRealtimeServiceV3)
        client = create_party_subscriber_v3()
        async with client, client.pubsub() as pubsub:
            # Subscribe before loading the snapshot so intervening changes stay queued.
            await asyncio.wait_for(subscribe_ready_v3(pubsub, service.store.channel_v3(room_id)), timeout=5)
            connection, snapshot = await run_in_threadpool(service.connect_v3, room_id, email, str(uuid4()))
            await send_packet_v3(websocket, snapshot)
            started = last_received = time.monotonic()
            invalid_messages = 0
            incoming = asyncio.create_task(receive_packet_v3(websocket))
            published = asyncio.create_task(pubsub.get_message(ignore_subscribe_messages=True, timeout=1))
            tasks = {incoming, published}
            try:
                while True:
                    done, _ = await asyncio.wait(tasks, timeout=1, return_when=asyncio.FIRST_COMPLETED)
                    now = time.monotonic()
                    if now - last_received >= service.store.lease_seconds_v3:
                        raise HTTPException(408, "HEARTBEAT_TIMEOUT")
                    if now - started >= 900:
                        await socket_error_v3(websocket, 401, "SESSION_REFRESH_REQUIRED")
                        await websocket.close(code=1012)
                        return
                    if incoming in done:
                        raw = incoming.result()
                        try:
                            message = socket_message_adapter_v3.validate_json(raw)
                            event = await run_in_threadpool(service.message_v3, connection, message)
                            last_received = time.monotonic()
                            if event is not None:
                                await send_packet_v3(websocket, event)
                        except ValidationError:
                            invalid_messages += 1
                            if invalid_messages >= 3:
                                raise HTTPException(400, "TOO_MANY_INVALID_MESSAGES") from None
                            await socket_error_v3(websocket, 422, "INVALID_MESSAGE")
                        except HTTPException as exc:
                            if exc.status_code not in (422, 429):
                                raise
                            await socket_error_v3(websocket, exc.status_code, exc.detail, (exc.headers or {}).get("Retry-After"))
                        tasks.remove(incoming)
                        incoming = asyncio.create_task(receive_packet_v3(websocket))
                        tasks.add(incoming)
                    if published in done:
                        message = published.result()
                        if message is not None and message["type"] == "message":
                            event = json.loads(message["data"])
                            forwarded = await run_in_threadpool(service.forward_v3, connection, event)
                            if forwarded is not None:
                                await send_packet_v3(websocket, forwarded)
                        tasks.remove(published)
                        published = asyncio.create_task(pubsub.get_message(ignore_subscribe_messages=True, timeout=1))
                        tasks.add(published)
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
    except WebSocketDisconnect:
        pass
    except HTTPException as exc:
        codes = {401: 4401, 403: 4403, 404: 4404, 408: 4408, 410: 4410, 413: 1009, 429: 4429, 503: 1013}
        with suppress(WebSocketDisconnect, RuntimeError, TimeoutError):
            await socket_error_v3(websocket, exc.status_code, exc.detail, (exc.headers or {}).get("Retry-After"))
            await websocket.close(code=codes.get(exc.status_code, 1008))
    except (RedisError, SQLAlchemyError, TimeoutError) as exc:
        logger_v3.warning("Party socket interrupted (%s)", type(exc).__name__)
        with suppress(WebSocketDisconnect, RuntimeError, TimeoutError):
            await socket_error_v3(websocket, 503, "PARTY_REALTIME_UNAVAILABLE")
            await websocket.close(code=1013)
    finally:
        if connection is not None and service is not None:
            try:
                await run_in_threadpool(service.disconnect_v3, connection)
            except (RedisError, SQLAlchemyError, HTTPException) as exc:
                # Crash/disconnect recovery also uses expiring leases and the cleanup loop.
                logger_v3.warning("Party disconnect deferred to lease expiry (%s)", type(exc).__name__)
