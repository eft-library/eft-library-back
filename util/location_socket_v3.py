"""Connection-scoped replacement for the legacy notification/location transport."""
import asyncio
import hashlib
import json
import logging
import os
from collections import deque
from contextlib import suppress
from functools import lru_cache
from uuid import uuid4

from anyio import CancelScope
from fastapi import WebSocketDisconnect
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger_v3 = logging.getLogger('ws.location.v3')
LOCATION_TYPES_V3 = {'wpf_location', 'wpf_log_location'}


@lru_cache(maxsize=1)
def get_location_redis_v3():
    return Redis.from_url(f"redis://{os.getenv('REDIS_HOST')}", decode_responses=True,
                          socket_connect_timeout=3, socket_timeout=5, health_check_interval=20)


def latest_key_v3(email):
    return 'location:v3:latest:' + hashlib.sha256(email.encode()).hexdigest()


PUBLISH_SCRIPT_V3 = """
local event = cjson.decode(ARGV[1])
local tm = redis.call('TIME')
event.received_at_unix_us = tonumber(tm[1]) * 1000000 + tonumber(tm[2])
local encoded = cjson.encode(event)
if event.type == 'wpf_location' or event.type == 'wpf_log_location' then
    redis.call('SET', KEYS[1], encoded, 'EX', 60)
elseif event.type == 'wpf_raid_state' and event.payload.is_active == false then
    redis.call('DEL', KEYS[1])
end
if event.type == 'wpf_raid_state' then
    redis.call('SET', KEYS[3], encoded, 'EX', 60)
end
return redis.call('PUBLISH', KEYS[2], encoded)
"""


async def publish_location_v3(email, kind, payload, request_id=None):
    event_id_v3 = str(uuid4())
    subscribers_v3 = await get_location_redis_v3().eval(
        PUBLISH_SCRIPT_V3, 3, latest_key_v3(email), f'notifications_channel:{email}',
        latest_key_v3(email) + ':raid',
        json.dumps({'type': kind, 'payload': payload, 'event_id': event_id_v3,
                    'request_id': request_id}))
    logger_v3.info('location_published event_id=%s request_id=%s type=%s subscribers=%s pid=%s',
                   event_id_v3, request_id, kind, subscribers_v3, os.getpid())
    return event_id_v3


async def send_wpf_location_v3(user_email, location, request_id=None):
    return await publish_location_v3(user_email, 'wpf_location', location, request_id)


async def send_wpf_log_location_v3(user_email, location):
    return await publish_location_v3(user_email, 'wpf_log_location', location)


async def send_wpf_raid_state_v3(user_email, state):
    return await publish_location_v3(user_email, 'wpf_raid_state', state)


async def websocket_handler_v3(websocket, user_email):
    """Each tab owns its subscriber, send lock, and cleanup; no shared user task."""
    await websocket.accept()
    connection_id_v3 = str(uuid4())
    client_v3 = get_location_redis_v3()
    send_lock_v3 = asyncio.Lock()
    seen_v3 = deque(maxlen=256)
    last_location_v3 = 0
    initialized_v3 = False

    async def send_v3(event_v3):
        async with send_lock_v3:
            await asyncio.wait_for(websocket.send_text(json.dumps(event_v3)), 5)

    async def forward_v3(event_v3, replayed_v3=False):
        nonlocal last_location_v3
        event_id_v3 = event_v3.get('event_id')
        dedup_key_v3 = event_id_v3
        if event_v3.get('type') not in LOCATION_TYPES_V3 | {'wpf_raid_state'}:
            dedup_key_v3 = 'notification:' + json.dumps([
                event_v3.get(key_v3) for key_v3 in
                ('noti_type', 'post_id', 'parent_comment_id', 'author_email', 'id')])
        if dedup_key_v3 and dedup_key_v3 in seen_v3:
            return
        if event_v3.get('type') in LOCATION_TYPES_V3 | {'wpf_raid_state'}:
            stamp_v3 = event_v3.get('received_at_unix_us', 0)
            if stamp_v3 and stamp_v3 < last_location_v3:
                return
            last_location_v3 = max(last_location_v3, stamp_v3)
        if event_v3.get('type') in LOCATION_TYPES_V3 | {'wpf_raid_state'}:
            packet_v3 = dict(event_v3, replayed=replayed_v3)
        else:
            packet_v3 = {'type': 'message', 'data': event_v3}
        await send_v3(packet_v3)
        if dedup_key_v3:
            seen_v3.append(dedup_key_v3)
        logger_v3.info('location_forwarded connection_id=%s event_id=%s type=%s replayed=%s pid=%s',
                       connection_id_v3, event_id_v3, event_v3.get('type'), replayed_v3, os.getpid())

    async def listen_v3():
        nonlocal initialized_v3
        delay_v3 = 1

        async def restore_v3():
            cached_events_v3 = []
            # Read both keys atomically so a raid-end event cannot race a cached
            # location snapshot and clear a newer position delivered first.
            for cached_v3 in await client_v3.mget(
                    latest_key_v3(user_email), latest_key_v3(user_email) + ':raid'):
                if not cached_v3:
                    continue
                try:
                    replay_v3 = json.loads(cached_v3)
                    if (not isinstance(replay_v3, dict)
                            or replay_v3.get('type') not in LOCATION_TYPES_V3 | {'wpf_raid_state'}):
                        raise ValueError('Invalid cached location')
                except (ValueError, TypeError):
                    logger_v3.warning('invalid_cached_location connection_id=%s', connection_id_v3)
                else:
                    cached_events_v3.append(replay_v3)
            for replay_v3 in sorted(cached_events_v3, key=lambda event_v3: event_v3.get('received_at_unix_us', 0)):
                await forward_v3(replay_v3, True)
            await send_v3({'type': 'location_connection_status', 'status': 'ready',
                           'connection_id': connection_id_v3})

        while True:
            try:
                async with client_v3.pubsub() as pubsub_v3:
                    await pubsub_v3.subscribe(f'notifications_channel:{user_email}')
                    # subscribe() writes the command; wait for Redis acknowledgement.
                    try:
                        async with asyncio.timeout(5):
                            while True:
                                ack_v3 = await pubsub_v3.get_message(timeout=1)
                                if ack_v3 and ack_v3['type'] == 'subscribe':
                                    break
                    except TimeoutError:
                        raise RedisError('Subscription acknowledgement timeout') from None
                    if not initialized_v3:
                        notifications_v3 = []
                        while True:
                            raw_v3 = await client_v3.lpop(f'notifications:{user_email}')
                            if raw_v3 is None:
                                break
                            try:
                                notifications_v3.append(json.loads(raw_v3))
                            except (ValueError, TypeError):
                                logger_v3.warning('invalid_pending_notification connection_id=%s', connection_id_v3)
                        await send_v3({'type': 'init', 'notifications': notifications_v3[::-1]})
                        initialized_v3 = True
                    await restore_v3()
                    delay_v3 = 1
                    while True:
                        # Poll with a bounded timeout to avoid idle socket read timeouts.
                        message_v3 = await pubsub_v3.get_message(timeout=1)
                        if message_v3 and message_v3['type'] == 'subscribe':
                            # redis-py can reconnect/resubscribe internally without
                            # raising RedisError; recover the cache on this path too.
                            await restore_v3()
                            continue
                        if not message_v3 or message_v3['type'] != 'message':
                            continue
                        try:
                            event_v3 = json.loads(message_v3['data'])
                            if not isinstance(event_v3, dict):
                                raise ValueError('Expected object')
                        except (ValueError, TypeError):
                            logger_v3.warning('invalid_pubsub_event connection_id=%s', connection_id_v3)
                            continue
                        await forward_v3(event_v3)
            except RedisError as exc_v3:
                logger_v3.warning('location_subscription_retry connection_id=%s error=%s pid=%s',
                                  connection_id_v3, type(exc_v3).__name__, os.getpid())
                await send_v3({'type': 'location_connection_status', 'status': 'reconnecting',
                               'connection_id': connection_id_v3})
                await asyncio.sleep(delay_v3)
                delay_v3 = min(delay_v3 * 2, 15)

    async def receive_v3():
        while True:
            await websocket.receive_text()  # Preserve legacy keep-alive packets.

    logger_v3.info('location_open connection_id=%s pid=%s', connection_id_v3, os.getpid())
    tasks_v3 = {asyncio.create_task(listen_v3()), asyncio.create_task(receive_v3())}
    try:
        done_v3, _ = await asyncio.wait(tasks_v3, return_when=asyncio.FIRST_COMPLETED)
        for task_v3 in done_v3:
            task_v3.result()
    except (WebSocketDisconnect, RuntimeError, TimeoutError, OSError) as exc_v3:
        logger_v3.info('location_closed connection_id=%s reason=%s pid=%s',
                       connection_id_v3, type(exc_v3).__name__, os.getpid())
    finally:
        with CancelScope(shield=True):
            for task_v3 in tasks_v3:
                task_v3.cancel()
            await asyncio.gather(*tasks_v3, return_exceptions=True)
            with suppress(WebSocketDisconnect, RuntimeError, OSError):
                await websocket.close(code=1013)
