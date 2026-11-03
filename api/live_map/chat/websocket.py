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

from database import Database
from api.live_map.party.realtime_schemas import PartySocketAuth
from api.live_map.party.security import authenticate_party_user
from api.live_map.party.websocket import (
    create_party_subscriber, receive_packet, send_packet, subscribe_ready,
)
from .schemas import ChatSend
from .security import GUEST_COOKIE_NAME
from .service import ChatService, build_event
from .store import ChatStore, get_chat_store


async def chat_error(websocket, status, message, retry_after=None, request_id=None):
    await send_packet(websocket, {
        'type': 'error', 'status': status, 'msg': message,
        'retry_after': int(retry_after) if retry_after else None,
        'request_id': request_id,
    })


async def transaction(email, operation):
    def execute():
        with Database.SessionLocal.begin() as session:
            service = ChatService(session)
            user = service.identity(email) if email is not None else None
            result = operation(service, user)
            events = session.info.get('chat_events_v3', [])
        # Commit precedes publication and acknowledgement. Missed publication is
        # reconciled by heartbeat snapshots; never retry a committed insertion.
        available = True
        if events:
            try:
                get_chat_store().publish(events)
            except (RedisError, HTTPException):
                available = False
        return result, available
    return await run_in_threadpool(execute)


def connection_state(service, user):
    return {'party_room_id': str(room_id) if (room_id := service.current_room(user)) else None,
            'invitations': service.invitations(user, None),
            'notifications': service.notifications(user), 'moderation': service.moderation_state(user),
            'party_invite_preferences': service.invite_preferences(user)}


async def chat_socket(websocket):
    await websocket.accept()
    tasks = set()
    leased_user_id = None
    recorded_connection = False
    connection_id = str(uuid4())
    try:
        try:
            raw = await asyncio.wait_for(receive_packet(websocket), 10)
        except TimeoutError:
            raise HTTPException(408, 'AUTH_TIMEOUT') from None
        try:
            socket_packet = json.loads(raw)
            guest = (isinstance(socket_packet, dict) and socket_packet.get('type') == 'guest'
                     and set(socket_packet) <= {'type', 'guest_token', 'session'}
                     and socket_packet.get('session', 'cookie') == 'cookie')
            auth = None if guest else PartySocketAuth.model_validate_json(raw)
        except (ValidationError, ValueError):
            raise HTTPException(401, 'AUTH_MESSAGE_REQUIRED') from None
        email = None
        if guest:
            # Use only the ASGI peer (configured trusted proxy handling), not arbitrary headers.
            peer = websocket.client.host if websocket.client else 'unknown'
            if 'guest_token' in socket_packet:
                leased_user_id = await run_in_threadpool(
                    get_chat_store().guest_identity, socket_packet['guest_token'])
            elif 'session' in socket_packet or GUEST_COOKIE_NAME in websocket.cookies:
                leased_user_id = await run_in_threadpool(
                    get_chat_store().guest_identity, websocket.cookies.get(GUEST_COOKIE_NAME))
            else:
                # Compatibility for clients that have not adopted guest sessions yet.
                leased_user_id = 'guest:' + hashlib.sha256(peer.encode()).hexdigest()
            await run_in_threadpool(get_chat_store().consume, leased_user_id, 'connect', 20)
        else:
            email = await run_in_threadpool(authenticate_party_user,
                HTTPAuthorizationCredentials(scheme='Bearer', credentials=auth.token.get_secret_value()))
            def connect(service, user):
                service.rate(user, 'connect', 20)
                return str(user.id)
            leased_user_id, _ = await transaction(email, connect)
        await run_in_threadpool(get_chat_store().lease, leased_user_id, connection_id)
        client = create_party_subscriber()
        async with client, client.pubsub() as pubsub:
            await asyncio.wait_for(subscribe_ready(pubsub, ChatStore.channel), 5)
            if not guest:
                await transaction(email, lambda s, u: s.connect_session(u, connection_id))
                recorded_connection = True
            snapshot, _ = await transaction(email, lambda s, u: s.snapshot(u))
            await send_packet(websocket, build_event('snapshot', snapshot))
            invite_preferences = snapshot['party_invite_preferences']
            online_users = snapshot['online_users']
            last_presence = time.monotonic()
            known = {row['id']: row for row in snapshot['party_invitations']}
            room_id = snapshot['party_room_id']
            notifications, moderation = snapshot['notifications'], snapshot['moderation']
            started = last_received = last_state = last_lease = time.monotonic()
            invalid = 0
            incoming = asyncio.create_task(receive_packet(websocket))
            published = asyncio.create_task(pubsub.get_message(ignore_subscribe_messages=True, timeout=1))
            tasks = {incoming, published}
            while True:
                done, _ = await asyncio.wait(tasks, timeout=1, return_when=asyncio.FIRST_COMPLETED)
                now = time.monotonic()
                if now - last_received >= 75:
                    raise HTTPException(408, 'HEARTBEAT_TIMEOUT')
                if now - started >= 900:
                    await chat_error(websocket, 401, 'SESSION_REFRESH_REQUIRED')
                    await websocket.close(code=1012)
                    return
                if now - last_lease >= 30:
                    await run_in_threadpool(get_chat_store().lease, leased_user_id, connection_id)
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
                                await run_in_threadpool(get_chat_store().consume,
                                    'guest:' + connection_id, 'heartbeat', 4)
                            else:
                                def heartbeat_session(service, user):
                                    service.rate(user, 'heartbeat', 4)
                                    service.touch_session(user, connection_id)
                                await transaction(email, heartbeat_session)
                            snapshot, _ = await transaction(email, lambda s, u: s.snapshot(u))
                            await send_packet(websocket, build_event('snapshot', snapshot))
                            room_id = snapshot['party_room_id']
                        else:
                            data = ChatSend.model_validate(packet)
                            request_id = str(data.request_id)
                            def send_session(service, user):
                                result = service.send(user, data)
                                service.touch_session(user, connection_id)
                                return result
                            ack, available = await transaction(email, send_session)
                            ack['realtime_available'] = available
                            await send_packet(websocket, build_event('message_ack', ack))
                        last_received = time.monotonic()
                    except (ValidationError, ValueError):
                        invalid += 1
                        if invalid >= 3:
                            raise HTTPException(400, 'TOO_MANY_INVALID_MESSAGES') from None
                        await chat_error(websocket, 422, 'INVALID_MESSAGE')
                    except HTTPException as exc:
                        if exc.status_code == 503 or (exc.status_code == 401 and not guest):
                            raise
                        await chat_error(websocket, exc.status_code, exc.detail,
                                           (exc.headers or {}).get('Retry-After'), request_id)
                    tasks.remove(incoming)
                    incoming = asyncio.create_task(receive_packet(websocket))
                    tasks.add(incoming)
                if published in done:
                    message = published.result()
                    if message is not None and message['type'] == 'message':
                        event = json.loads(message['data'])
                        forwarded, _ = await transaction(email, lambda s, u: s.forward(u, event))
                        if forwarded is not None:
                            if forwarded['type'] in ('party_invitation_created', 'party_invitation_updated'):
                                known[forwarded['data']['id']] = forwarded['data']
                            elif forwarded['type'] == 'party_invite_preferences_updated':
                                invite_preferences = forwarded['data']
                            elif forwarded['type'] == 'party_notifications_updated':
                                notifications = forwarded['data']
                            await send_packet(websocket, forwarded)
                    tasks.remove(published)
                    published = asyncio.create_task(pubsub.get_message(ignore_subscribe_messages=True, timeout=1))
                    tasks.add(published)
                if now - last_presence >= 2:
                    current_users, _ = await transaction(email, lambda s, u: s.online_users())
                    if current_users != online_users:
                        online_users = current_users
                        await send_packet(websocket, build_event('online_users_updated', online_users))
                    last_presence = now
                # Read party state independently: old party endpoints and automatic
                # cleanup need no dependency on chat tables or the chat event bus.
                if not guest and now - last_state >= 2:
                    state, _ = await transaction(email, connection_state)
                    if state['party_invite_preferences'] != invite_preferences:
                        invite_preferences = state['party_invite_preferences']
                        await send_packet(websocket, build_event('party_invite_preferences_updated', invite_preferences))
                    if state['notifications'] != notifications:
                        notifications = state['notifications']
                        await send_packet(websocket, build_event('party_notifications_updated', notifications))
                    if state['moderation'] != moderation:
                        moderation = state['moderation']
                        await send_packet(websocket, build_event('chat_moderation_updated', moderation))
                    for invitation in state['invitations']:
                        previous = known.get(invitation['id'])
                        if invitation != previous and (previous is not None or invitation['status'] == 'pending'):
                            kind = 'party_invitation_created' if previous is None and invitation['status'] == 'pending' else 'party_invitation_updated'
                            await send_packet(websocket, build_event(kind, invitation))
                    known = {row['id']: row for row in state['invitations']}
                    if state['party_room_id'] != room_id:
                        snapshot, _ = await transaction(email, lambda s, u: s.snapshot(u))
                        room_id = snapshot['party_room_id']
                        await send_packet(websocket, build_event('snapshot', snapshot))
                    last_state = now
    except WebSocketDisconnect:
        pass
    except HTTPException as exc:
        codes = {401: 4401, 403: 4403, 404: 4404, 408: 4408, 413: 1009, 429: 4429, 503: 1013}
        with suppress(WebSocketDisconnect, RuntimeError, TimeoutError):
            await chat_error(websocket, exc.status_code, exc.detail,
                                (exc.headers or {}).get('Retry-After'))
            await websocket.close(code=codes.get(exc.status_code, 1008))
    except (RedisError, SQLAlchemyError, TimeoutError) as exc:
        logging.getLogger('api.live_map.chat').warning('Chat socket unavailable (%s)', type(exc).__name__)
        with suppress(WebSocketDisconnect, RuntimeError, TimeoutError):
            await chat_error(websocket, 503, 'CHAT_UNAVAILABLE')
            await websocket.close(code=1013)
    finally:
        with CancelScope(shield=True):
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if leased_user_id is not None:
                with suppress(RedisError, HTTPException):
                    await run_in_threadpool(get_chat_store().disconnect, leased_user_id, connection_id)
            if recorded_connection:
                try:
                    await transaction(None, lambda s, u: s.disconnect_session(connection_id))
                except (SQLAlchemyError, HTTPException):
                    logging.getLogger('api.live_map.chat').warning('Chat connection close deferred to expiry')
