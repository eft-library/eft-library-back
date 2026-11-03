import json
import hashlib
import secrets
import re
from functools import lru_cache

from fastapi import HTTPException
from redis import Redis
from redis.exceptions import RedisError

from api.live_map.party.realtime_store import party_redis_url


class ChatStore:
    presence_key = 'live-map:chat:v3:presence'
    channel = 'live-map:chat:v3:events'
    # Sliding windows are atomic across workers and do not permit fixed-window bursts.
    rate_script = """
        local tm = redis.call('TIME')
        local now = tm[1] * 1000000 + tm[2]
        local window = tonumber(ARGV[2]) * 1000000
        redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now - window)
        if redis.call('ZCARD', KEYS[1]) >= tonumber(ARGV[1]) then
            local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
            return math.max(1, math.ceil((tonumber(oldest[2]) + window - now) / 1000000))
        end
        redis.call('ZADD', KEYS[1], now, ARGV[3])
        redis.call('EXPIRE', KEYS[1], ARGV[2])
        return 0
    """

    def __init__(self, client):
        self.client = client

    def guest_identity(self, token):
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
            raise HTTPException(401, 'CHAT_GUEST_SESSION_INVALID')
        digest = hashlib.sha256(token.encode()).hexdigest()
        try:
            valid = self.client.exists(f'live-map:chat:v3:guest-session:{digest}')
        except RedisError:
            raise HTTPException(503, 'CHAT_GUEST_SESSION_UNAVAILABLE') from None
        if not valid:
            raise HTTPException(401, 'CHAT_GUEST_SESSION_INVALID')
        return 'guest:session:' + digest

    def guest_session(self, token=None):
        if token:
            try:
                self.guest_identity(token)
                return token
            except HTTPException as exc:
                if exc.status_code != 401:
                    raise
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode()).hexdigest()
        try:
            self.client.set(f'live-map:chat:v3:guest-session:{digest}', '1', ex=86400)
        except RedisError:
            raise HTTPException(503, 'CHAT_GUEST_SESSION_UNAVAILABLE') from None
        return token

    def consume(self, user_id, action, limit, seconds=60):
        from uuid import uuid4
        try:
            retry = self.client.eval(self.rate_script, 1,
                f'live-map:chat:v3:rate:{action}:{user_id}', limit, seconds, str(uuid4()))
        except RedisError:
            raise HTTPException(503, 'CHAT_RATE_LIMIT_UNAVAILABLE') from None
        if int(retry):
            code = 'CHAT_CONNECT_RATE_LIMITED' if action == 'connect' else 'CHAT_RATE_LIMITED'
            raise HTTPException(429, code, headers={'Retry-After': str(retry)})

    lease_script = """
        local now = tonumber(redis.call('TIME')[1])
        redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
        if not redis.call('ZSCORE', KEYS[1], ARGV[1]) and redis.call('ZCARD', KEYS[1]) >= 5 then
            return 0
        end
        redis.call('ZADD', KEYS[1], now + 90, ARGV[1])
        redis.call('EXPIRE', KEYS[1], 90)
        if ARGV[2] ~= '' then
            redis.call('ZADD', KEYS[2], now + 90, ARGV[2])
            redis.call('EXPIRE', KEYS[2], 90)
        end
        return 1
    """

    def lease(self, user_id, connection_id):
        if not self.client.eval(self.lease_script, 2,
                                f'live-map:chat:v3:connections:{user_id}', self.presence_key,
                                connection_id, '' if str(user_id).startswith('guest:') else f'{user_id}/{connection_id}'):
            raise HTTPException(429, 'CHAT_CONNECTION_LIMIT', headers={'Retry-After': '90'})

    def disconnect(self, user_id, connection_id):
        with self.client.pipeline(transaction=True) as pipeline:
            pipeline.zrem(f'live-map:chat:v3:connections:{user_id}', connection_id)
            pipeline.zrem(self.presence_key, f'{user_id}/{connection_id}')
            pipeline.execute()

    presence_script = """
        local now = tonumber(redis.call('TIME')[1])
        redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
        return redis.call('ZRANGE', KEYS[1], 0, -1)
    """

    def online_user_ids(self):
        connections = self.client.eval(self.presence_script, 1, self.presence_key)
        return sorted({connection.split('/', 1)[0] for connection in connections})

    def publish(self, events):
        for event in events:
            # Only resource/user IDs travel on the shared bus. Each recipient is
            # authorized against PostgreSQL before receiving current public data.
            self.client.publish(self.channel, json.dumps(event))


@lru_cache(maxsize=1)
def get_chat_store():
    return ChatStore(Redis.from_url(party_redis_url(), decode_responses=True,
                                    socket_connect_timeout=2, socket_timeout=2))
