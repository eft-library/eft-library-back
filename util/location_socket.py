"""Connection-scoped replacement for the legacy notification/location transport."""
import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from collections import deque
from contextlib import suppress
from functools import lru_cache
from uuid import uuid4

from anyio import CancelScope
from fastapi import HTTPException, WebSocketDisconnect
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger('ws.location.v3')
LOCATION_TYPES = {'wpf_location', 'wpf_log_location'}


@lru_cache(maxsize=1)
def get_location_redis():
    return Redis.from_url(f"redis://{os.getenv('REDIS_HOST')}", decode_responses=True,
                          socket_connect_timeout=3, socket_timeout=5, health_check_interval=20)


def latest_key(email):
    return 'location:v3:latest:' + hashlib.sha256(email.encode()).hexdigest()


PUBLISH_SCRIPT = """
local event = cjson.decode(ARGV[1])
local tm = redis.call('TIME')
local now = tonumber(tm[1]) + tonumber(tm[2]) / 1000000
event.received_at_unix_us = tonumber(tm[1]) * 1000000 + tonumber(tm[2])
local ttl = 60
if event.type == 'wpf_raid_state' then
    local ends = tonumber(ARGV[2])
    local started = tonumber(ARGV[3])
    local observed = tonumber(ARGV[4])
    if ends > 0 and ends <= now then return -1 end
    if ends > 0 then ttl = math.ceil(ends - now) + 60 end
    local sid = event.payload.session_id
    if type(sid) ~= 'string' then sid = '' end
    redis.call('ZREMRANGEBYSCORE', KEYS[5], '-inf', now - 86400)
    local previous = redis.call('GET', KEYS[4])
    if previous then
        previous = cjson.decode(previous)
        previous.started = tonumber(previous.started) or 0
        previous.observed = tonumber(previous.observed) or 0
        if started > 0 and previous.started > 0 and started < previous.started then return -2 end
        if sid ~= '' and sid == previous.sid and observed > 0 and previous.observed > 0
            and observed < previous.observed then return -2 end
        if sid ~= '' and sid ~= previous.sid and redis.call('ZSCORE', KEYS[5], sid) then return -2 end
        if sid ~= '' and previous.sid ~= '' and sid ~= previous.sid then
            redis.call('ZADD', KEYS[5], now, previous.sid)
            redis.call('ZREMRANGEBYRANK', KEYS[5], 0, -129)
            redis.call('EXPIRE', KEYS[5], 86400)
        end
        if sid ~= previous.sid or event.payload.map ~= previous.map or
            (started > 0 and previous.started > 0 and started ~= previous.started) then
            redis.call('DEL', KEYS[1])
        end
    elseif sid ~= '' and redis.call('ZSCORE', KEYS[5], sid) then
        return -2
    end
    -- Keep timestamp text: cjson's default number precision can otherwise make
    -- an identical retry appear a few microseconds older than its stored state.
    redis.call('SET', KEYS[4], cjson.encode({sid=sid, started=ARGV[3], observed=ARGV[4],
        map=event.payload.map}), 'EX', math.max(86400, ttl))
end
local encoded = cjson.encode(event)
if event.type == 'wpf_location' or event.type == 'wpf_log_location' then
    redis.call('SET', KEYS[1], encoded, 'EX', 60)
elseif event.type == 'wpf_raid_state' and event.payload.is_active == false then
    redis.call('DEL', KEYS[1])
end
if event.type == 'wpf_raid_state' then
    redis.call('SET', KEYS[3], encoded, 'EX', ttl)
end
return redis.call('PUBLISH', KEYS[2], encoded)
"""


async def publish_location(email, kind, payload, request_id=None):
    event_id = str(uuid4())
    def timestamp(value):
        return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp() if value else 0
    ends = timestamp(payload.get('raid_ends_at')) if kind == 'wpf_raid_state' else 0
    started = timestamp(payload.get('started_at')) if kind == 'wpf_raid_state' else 0
    observed = timestamp(payload.get('timer_observed_at')) if kind == 'wpf_raid_state' else 0
    subscribers = await get_location_redis().eval(
        PUBLISH_SCRIPT, 5, latest_key(email), f'notifications_channel:{email}',
        latest_key(email) + ':raid', latest_key(email) + ':raid-order',
        latest_key(email) + ':superseded-sessions',
        json.dumps({'type': kind, 'payload': payload, 'event_id': event_id,
                    'request_id': request_id}), ends, started, observed)
    if subscribers == -1:
        raise HTTPException(409, 'RAID_TIMER_EXPIRED')
    if subscribers == -2:
        raise HTTPException(409, 'RAID_STATE_STALE')
    logger.info('location_published event_id=%s request_id=%s type=%s subscribers=%s pid=%s',
                   event_id, request_id, kind, subscribers, os.getpid())
    return event_id


async def send_wpf_location(user_email, location, request_id=None):
    return await publish_location(user_email, 'wpf_location', location, request_id)


async def send_wpf_log_location(user_email, location):
    return await publish_location(user_email, 'wpf_log_location', location)


async def send_wpf_raid_state(user_email, state):
    return await publish_location(user_email, 'wpf_raid_state', state)


async def websocket_handler(websocket, user_email):
    """Each tab owns its subscriber, send lock, and cleanup; no shared user task."""
    await websocket.accept()
    connection_id = str(uuid4())
    client = get_location_redis()
    send_lock = asyncio.Lock()
    seen = deque(maxlen=256)
    last_location = 0
    initialized = False

    async def send(build_event):
        async with send_lock:
            await asyncio.wait_for(websocket.send_text(json.dumps(build_event)), 5)

    async def forward(build_event, replayed=False):
        nonlocal last_location
        if build_event.get('type') == 'wpf_raid_state':
            ends = build_event.get('payload', {}).get('raid_ends_at')
            if ends and datetime.fromisoformat(ends.replace('Z', '+00:00')) <= datetime.now(timezone.utc):
                # Keep session context, but never replay an expired automatic timer.
                build_event = dict(build_event, payload=dict(build_event['payload'],
                                timer_observed_at=None, raid_ends_at=None))
        event_id = build_event.get('event_id')
        dedup_key = event_id
        if build_event.get('type') not in LOCATION_TYPES | {'wpf_raid_state'}:
            dedup_key = 'notification:' + json.dumps([
                build_event.get(key) for key in
                ('noti_type', 'post_id', 'parent_comment_id', 'author_email', 'id')])
        if dedup_key and dedup_key in seen:
            return
        if build_event.get('type') in LOCATION_TYPES | {'wpf_raid_state'}:
            stamp = build_event.get('received_at_unix_us', 0)
            if stamp and stamp < last_location:
                return
            last_location = max(last_location, stamp)
        if build_event.get('type') in LOCATION_TYPES | {'wpf_raid_state'}:
            socket_packet = dict(build_event, replayed=replayed)
        else:
            socket_packet = {'type': 'message', 'data': build_event}
        await send(socket_packet)
        if dedup_key:
            seen.append(dedup_key)
        logger.info('location_forwarded connection_id=%s event_id=%s type=%s replayed=%s pid=%s',
                       connection_id, event_id, build_event.get('type'), replayed, os.getpid())

    async def listen():
        nonlocal initialized
        delay = 1

        async def restore():
            cached_events = []
            # Read both keys atomically so a raid-end event cannot race a cached
            # location snapshot and clear a newer position delivered first.
            for cached in await client.mget(
                    latest_key(user_email), latest_key(user_email) + ':raid'):
                if not cached:
                    continue
                try:
                    replay = json.loads(cached)
                    if (not isinstance(replay, dict)
                            or replay.get('type') not in LOCATION_TYPES | {'wpf_raid_state'}):
                        raise ValueError('Invalid cached location')
                except (ValueError, TypeError):
                    logger.warning('invalid_cached_location connection_id=%s', connection_id)
                else:
                    cached_events.append(replay)
            for replay in sorted(cached_events, key=lambda build_event: build_event.get('received_at_unix_us', 0)):
                await forward(replay, True)
            await send({'type': 'location_connection_status', 'status': 'ready',
                           'connection_id': connection_id})

        while True:
            try:
                async with client.pubsub() as pubsub:
                    await pubsub.subscribe(f'notifications_channel:{user_email}')
                    # subscribe() writes the command; wait for Redis acknowledgement.
                    try:
                        async with asyncio.timeout(5):
                            while True:
                                ack = await pubsub.get_message(timeout=1)
                                if ack and ack['type'] == 'subscribe':
                                    break
                    except TimeoutError:
                        raise RedisError('Subscription acknowledgement timeout') from None
                    if not initialized:
                        notifications = []
                        while True:
                            raw = await client.lpop(f'notifications:{user_email}')
                            if raw is None:
                                break
                            try:
                                notifications.append(json.loads(raw))
                            except (ValueError, TypeError):
                                logger.warning('invalid_pending_notification connection_id=%s', connection_id)
                        await send({'type': 'init', 'notifications': notifications[::-1]})
                        initialized = True
                    await restore()
                    delay = 1
                    while True:
                        # Poll with a bounded timeout to avoid idle socket read timeouts.
                        message = await pubsub.get_message(timeout=1)
                        if message and message['type'] == 'subscribe':
                            # redis-py can reconnect/resubscribe internally without
                            # raising RedisError; recover the cache on this path too.
                            await restore()
                            continue
                        if not message or message['type'] != 'message':
                            continue
                        try:
                            build_event = json.loads(message['data'])
                            if not isinstance(build_event, dict):
                                raise ValueError('Expected object')
                        except (ValueError, TypeError):
                            logger.warning('invalid_pubsub_event connection_id=%s', connection_id)
                            continue
                        await forward(build_event)
            except RedisError as exc:
                logger.warning('location_subscription_retry connection_id=%s error=%s pid=%s',
                                  connection_id, type(exc).__name__, os.getpid())
                await send({'type': 'location_connection_status', 'status': 'reconnecting',
                               'connection_id': connection_id})
                await asyncio.sleep(delay)
                delay = min(delay * 2, 15)

    async def receive():
        while True:
            await websocket.receive_text()  # Preserve legacy keep-alive packets.

    logger.info('location_open connection_id=%s pid=%s', connection_id, os.getpid())
    tasks = {asyncio.create_task(listen()), asyncio.create_task(receive())}
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    except (WebSocketDisconnect, RuntimeError, TimeoutError, OSError) as exc:
        logger.info('location_closed connection_id=%s reason=%s pid=%s',
                       connection_id, type(exc).__name__, os.getpid())
    finally:
        with CancelScope(shield=True):
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            with suppress(WebSocketDisconnect, RuntimeError, OSError):
                await websocket.close(code=1013)
