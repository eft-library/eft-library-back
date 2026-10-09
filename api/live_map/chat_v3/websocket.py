import asyncio
import json
import hashlib
import logging
import time
from contextlib import suppress
from uuid import uuid4

from anyio import CancelScope
from fastapi import HTTPException, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from database import V3Database
from api.live_map.party_v3.realtime_schemas import PartySocketAuthV3
from api.live_map.party_v3.security import authenticate_party_user_v3
from api.live_map.party_v3.websocket import (
    create_party_subscriber_v3, receive_packet_v3, send_packet_v3, subscribe_ready_v3,
)
from .schemas import ChatSendV3
from .service import ChatServiceV3, event_v3
from .store import ChatStoreV3, get_chat_store_v3


async def chat_error_v3(websocket, status, message, retry_after=None, request_id=None):
    await send_packet_v3(websocket, {
        'type': 'error', 'status': status, 'msg': message,
        'retry_after': int(retry_after) if retry_after else None,
        'request_id': request_id,
    })


async def transaction_v3(email, operation):
    def execute_v3():
        with V3Database.SessionLocal.begin() as session:
            service = ChatServiceV3(session)
            user = service.identity_v3(email) if email is not None else None
            result = operation(service, user)
            events = session.info.get('chat_events_v3', [])
        # Commit precedes publication and acknowledgement. Missed publication is
        # reconciled by heartbeat snapshots; never retry a committed insertion.
        available = True
        if events:
            try:
                get_chat_store_v3().publish_v3(events)
            except (RedisError, HTTPException):
                available = False
        return result, available
    return await run_in_threadpool(execute_v3)


def state_v3(service, user):
    return {'party_room_id': str(room_id) if (room_id := service.current_room_v3(user)) else None,
            'invitations': service.invitations_v3(user, None),
            'notifications': service.notifications_v3(user), 'moderation': service.moderation_state_v3(user),
            'party_invite_preferences': service.invite_preferences_v3(user)}


async def chat_socket_v3(websocket):
    await websocket.accept()
    tasks = set()
    leased_user_id = None
    recorded_connection = False
    connection_id = str(uuid4())
    try:
        try:
            raw = await asyncio.wait_for(receive_packet_v3(websocket), 10)
        except TimeoutError:
            raise HTTPException(408, 'AUTH_TIMEOUT') from None
        try:
            guest = json.loads(raw) == {'type': 'guest'}
            auth = None if guest else PartySocketAuthV3.model_validate_json(raw)
        except (ValidationError, ValueError):
            raise HTTPException(401, 'AUTH_MESSAGE_REQUIRED') from None
        email = None
        if guest:
            # Use only the ASGI peer (configured trusted proxy handling), not arbitrary headers.
            peer = websocket.client.host if websocket.client else 'unknown'
            leased_user_id = 'guest:' + hashlib.sha256(peer.encode()).hexdigest()
            await run_in_threadpool(get_chat_store_v3().consume_v3, leased_user_id, 'connect', 20)
        else:
            email = await run_in_threadpool(authenticate_party_user_v3,
                HTTPAuthorizationCredentials(scheme='Bearer', credentials=auth.token.get_secret_value()))
            def connect_v3(service, user):
                service.rate_v3(user, 'connect', 20)
                return str(user.id)
            leased_user_id, _ = await transaction_v3(email, connect_v3)
        await run_in_threadpool(get_chat_store_v3().lease_v3, leased_user_id, connection_id)
        client = create_party_subscriber_v3()
        async with client, client.pubsub() as pubsub:
            await asyncio.wait_for(subscribe_ready_v3(pubsub, ChatStoreV3.channel_v3), 5)
            if not guest:
                await transaction_v3(email, lambda s, u: s.connect_session_v3(u, connection_id))
                recorded_connection = True
            snapshot, _ = await transaction_v3(email, lambda s, u: s.snapshot_v3(u))
            await send_packet_v3(websocket, event_v3('snapshot', snapshot))
            invite_preferences = snapshot['party_invite_preferences']
            online_users = snapshot['online_users']
            last_presence = time.monotonic()
            known = {row['id']: row for row in snapshot['party_invitations']}
            room_id = snapshot['party_room_id']
            notifications, moderation = snapshot['notifications'], snapshot['moderation']
            started = last_received = last_state = last_lease = time.monotonic()
            invalid = 0
            incoming = asyncio.create_task(receive_packet_v3(websocket))
            published = asyncio.create_task(pubsub.get_message(ignore_subscribe_messages=True, timeout=1))
            tasks = {incoming, published}
            while True:
                done, _ = await asyncio.wait(tasks, timeout=1, return_when=asyncio.FIRST_COMPLETED)
                now = time.monotonic()
                if now - last_received >= 75:
                    raise HTTPException(408, 'HEARTBEAT_TIMEOUT')
                if now - started >= 900:
                    await chat_error_v3(websocket, 401, 'SESSION_REFRESH_REQUIRED')
                    await websocket.close(code=1012)
                    return
                if now - last_lease >= 30:
                    await run_in_threadpool(get_chat_store_v3().lease_v3, leased_user_id, connection_id)
                    last_lease = now
                if incoming in done:
                    raw = incoming.result()
                    request_id = None
                    try:
                        packet = json.loads(raw)
                        if not isinstance(packet, dict):
                            raise ValueError
                        if packet.get('type') == 'heartbeat' and set(packet) == {'type'}:
                            if guest:
                                await run_in_threadpool(get_chat_store_v3().consume_v3,
                                    'guest:' + connection_id, 'heartbeat', 4)
                            else:
                                def heartbeat_session_v3(service, user):
                                    service.rate_v3(user, 'heartbeat', 4)
                                    service.touch_session_v3(user, connection_id)
                                await transaction_v3(email, heartbeat_session_v3)
                            snapshot, _ = await transaction_v3(email, lambda s, u: s.snapshot_v3(u))
                            await send_packet_v3(websocket, event_v3('snapshot', snapshot))
                            room_id = snapshot['party_room_id']
                        else:
                            data = ChatSendV3.model_validate(packet)
                            request_id = str(data.request_id)
                            def send_session_v3(service, user):
                                result = service.send_v3(user, data)
                                service.touch_session_v3(user, connection_id)
                                return result
                            ack, available = await transaction_v3(email, send_session_v3)
                            ack['realtime_available'] = available
                            await send_packet_v3(websocket, event_v3('message_ack', ack))
                        last_received = time.monotonic()
                    except (ValidationError, ValueError):
                        invalid += 1
                        if invalid >= 3:
                            raise HTTPException(400, 'TOO_MANY_INVALID_MESSAGES') from None
                        await chat_error_v3(websocket, 422, 'INVALID_MESSAGE')
                    except HTTPException as exc:
                        if exc.status_code == 503 or (exc.status_code == 401 and not guest):
                            raise
                        await chat_error_v3(websocket, exc.status_code, exc.detail,
                                           (exc.headers or {}).get('Retry-After'), request_id)
                    tasks.remove(incoming)
                    incoming = asyncio.create_task(receive_packet_v3(websocket))
                    tasks.add(incoming)
                if published in done:
                    message = published.result()
                    if message is not None and message['type'] == 'message':
                        event = json.loads(message['data'])
                        forwarded, _ = await transaction_v3(email, lambda s, u: s.forward_v3(u, event))
                        if forwarded is not None:
                            if forwarded['type'] in ('party_invitation_created', 'party_invitation_updated'):
                                known[forwarded['data']['id']] = forwarded['data']
                            elif forwarded['type'] == 'party_invite_preferences_updated':
                                invite_preferences = forwarded['data']
                            elif forwarded['type'] == 'party_notifications_updated':
                                notifications = forwarded['data']
                            await send_packet_v3(websocket, forwarded)
                    tasks.remove(published)
                    published = asyncio.create_task(pubsub.get_message(ignore_subscribe_messages=True, timeout=1))
                    tasks.add(published)
                if now - last_presence >= 2:
                    current_users, _ = await transaction_v3(email, lambda s, u: s.online_users_v3())
                    if current_users != online_users:
                        online_users = current_users
                        await send_packet_v3(websocket, event_v3('online_users_updated', online_users))
                    last_presence = now
                # Read party state independently: old party endpoints and automatic
                # cleanup need no dependency on chat tables or the chat event bus.
                if not guest and now - last_state >= 2:
                    state, _ = await transaction_v3(email, state_v3)
                    if state['party_invite_preferences'] != invite_preferences:
                        invite_preferences = state['party_invite_preferences']
                        await send_packet_v3(websocket, event_v3('party_invite_preferences_updated', invite_preferences))
                    if state['notifications'] != notifications:
                        notifications = state['notifications']
                        await send_packet_v3(websocket, event_v3('party_notifications_updated', notifications))
                    if state['moderation'] != moderation:
                        moderation = state['moderation']
                        await send_packet_v3(websocket, event_v3('chat_moderation_updated', moderation))
                    for invitation in state['invitations']:
                        previous = known.get(invitation['id'])
                        if invitation != previous and (previous is not None or invitation['status'] == 'pending'):
                            kind = 'party_invitation_created' if previous is None and invitation['status'] == 'pending' else 'party_invitation_updated'
                            await send_packet_v3(websocket, event_v3(kind, invitation))
                    known = {row['id']: row for row in state['invitations']}
                    if state['party_room_id'] != room_id:
                        snapshot, _ = await transaction_v3(email, lambda s, u: s.snapshot_v3(u))
                        room_id = snapshot['party_room_id']
                        await send_packet_v3(websocket, event_v3('snapshot', snapshot))
                    last_state = now
    except WebSocketDisconnect:
        pass
    except HTTPException as exc:
        codes = {401: 4401, 403: 4403, 404: 4404, 408: 4408, 413: 1009, 429: 4429, 503: 1013}
        with suppress(WebSocketDisconnect, RuntimeError, TimeoutError):
            await chat_error_v3(websocket, exc.status_code, exc.detail,
                                (exc.headers or {}).get('Retry-After'))
            await websocket.close(code=codes.get(exc.status_code, 1008))
    except (RedisError, SQLAlchemyError, TimeoutError) as exc:
        logging.getLogger('api.live_map.chat_v3').warning('Chat socket unavailable (%s)', type(exc).__name__)
        with suppress(WebSocketDisconnect, RuntimeError, TimeoutError):
            await chat_error_v3(websocket, 503, 'CHAT_UNAVAILABLE')
            await websocket.close(code=1013)
    finally:
        with CancelScope(shield=True):
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if leased_user_id is not None:
                with suppress(RedisError, HTTPException):
                    await run_in_threadpool(get_chat_store_v3().disconnect_v3, leased_user_id, connection_id)
            if recorded_connection:
                try:
                    await transaction_v3(None, lambda s, u: s.disconnect_session_v3(connection_id))
                except (SQLAlchemyError, HTTPException):
                    logging.getLogger('api.live_map.chat_v3').warning('Chat connection close deferred to expiry')
