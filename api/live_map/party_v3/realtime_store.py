"""Redis room notifications, connection leases and short-lived positions.

Presence mutations are called while holding the PostgreSQL room row lock.
No Google tokens, passwords or account emails are stored in these keys/events.
"""
import json
import os
import time
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from redis import Redis

from .security import get_party_rate_limiter_v3


def party_redis_url_v3() -> str:
    url = os.getenv("REDIS_URL")
    host = os.getenv("REDIS_HOST")
    if not url and not host:
        raise HTTPException(503, "PARTY_REALTIME_UNAVAILABLE")
    return url or f"redis://{host}"


def membership_epoch_v3(joined_at: datetime) -> str:
    if joined_at.tzinfo is None:
        joined_at = joined_at.replace(tzinfo=timezone.utc)
    return str(int(joined_at.timestamp() * 1_000_000))


class PartyRealtimeStoreV3:
    lease_seconds_v3 = 45
    reconnect_seconds_v3 = 90
    position_seconds_v3 = 60
    ping_seconds_v3 = 60
    max_connections_v3 = 5

    def __init__(self, client: Redis):
        self.client = client

    def key_v3(self, room_id: UUID | str, suffix: str) -> str:
        return f"live-map:party:v3:room:{room_id}:{suffix}"

    def channel_v3(self, room_id: UUID | str) -> str:
        return self.key_v3(room_id, "events")

    def event_v3(self, room_id: UUID | str, event_type: str, data: dict | None = None) -> dict:
        return {
            "type": event_type, "event_id": str(uuid4()), "room_id": str(room_id),
            "server_time": datetime.now(timezone.utc).isoformat(), "data": data or {},
        }

    def publish_v3(self, room_id: UUID | str, event: dict):
        self.client.publish(self.channel_v3(room_id), json.dumps(event, allow_nan=False))

    def changed_v3(self, room_id: UUID | str, event_type: str = "room.changed"):
        self.publish_v3(room_id, self.event_v3(room_id, event_type))

    def active_v3(self, room_id: UUID | str, now: float | None = None) -> list[str]:
        now = time.time() if now is None else now
        key = self.key_v3(room_id, "connections")
        pipe = self.client.pipeline(transaction=True)
        pipe.zremrangebyscore(key, "-inf", now)
        pipe.zrange(key, 0, -1)
        return pipe.execute()[1]

    def touch_v3(self, room_id: UUID | str, member_id: UUID | str, epoch: str, connection_id: str):
        now = time.time()
        prefix = f"{member_id}:{epoch}:"
        connection = prefix + connection_id
        active = [item for item in self.active_v3(room_id, now) if item.startswith(prefix)]
        if connection not in active and len(active) >= self.max_connections_v3:
            raise HTTPException(429, "TOO_MANY_PARTY_CONNECTIONS")
        key = self.key_v3(room_id, "connections")
        seen = self.key_v3(room_id, "last-seen")
        pipe = self.client.pipeline(transaction=True)
        pipe.zadd(key, {connection: now + self.lease_seconds_v3})
        pipe.expire(key, 300)
        pipe.hset(seen, f"{member_id}:{epoch}", now)
        pipe.expire(seen, 86400)
        pipe.execute()
        if not active:
            self.changed_v3(room_id, "presence.changed")

    def disconnect_v3(self, room_id: UUID | str, member_id: UUID | str, epoch: str, connection_id: str):
        key = self.key_v3(room_id, "connections")
        prefix = f"{member_id}:{epoch}:"
        removed = self.client.zrem(key, prefix + connection_id)
        if removed and not any(item.startswith(prefix) for item in self.active_v3(room_id)):
            seen = self.key_v3(room_id, "last-seen")
            pipe = self.client.pipeline(transaction=True)
            pipe.hset(seen, f"{member_id}:{epoch}", time.time())
            pipe.expire(seen, 86400)
            pipe.execute()
            self.changed_v3(room_id, "presence.changed")

    def last_seen_v3(self, room_id: UUID | str, member_id: UUID | str, epoch: str, now: float) -> float:
        key = self.key_v3(room_id, "last-seen")
        field = f"{member_id}:{epoch}"
        # A Redis restart grants a fresh grace period instead of immediately evicting everyone.
        self.client.hsetnx(key, field, now)
        self.client.expire(key, 86400)
        return float(self.client.hget(key, field))

    def save_position_v3(self, room_id: UUID | str, member_id: str, epoch: str, event: dict):
        key = self.key_v3(room_id, "positions")
        pipe = self.client.pipeline(transaction=True)
        pipe.hset(key, f"{member_id}:{epoch}", json.dumps(event, allow_nan=False))
        pipe.expire(key, 86400)
        pipe.execute()

    def presence_v3(self, room_id: UUID | str, epochs: dict[str, str]) -> dict:
        online = set()
        for connection in self.active_v3(room_id):
            member_id, epoch, _ = connection.split(":", 2)
            if epochs.get(member_id) == epoch:
                online.add(member_id)
        return {"online_member_ids": sorted(online), "online_count": len(online)}

    def save_view_map_v3(self, room_id: UUID | str, member_id: str, epoch: str, event: dict):
        key = self.key_v3(room_id, "view-maps")
        pipe = self.client.pipeline(transaction=True)
        pipe.hset(key, f"{member_id}:{epoch}", json.dumps(event, allow_nan=False))
        pipe.expire(key, 86400)
        pipe.execute()

    def view_maps_v3(self, room_id: UUID | str, epochs: dict[str, str]) -> list[dict]:
        key = self.key_v3(room_id, "view-maps")
        self.client.expire(key, 86400)
        events = []
        stale = []
        for field, raw in self.client.hgetall(key).items():
            member_id, epoch = field.split(":", 1)
            if epochs.get(member_id) == epoch:
                events.append(json.loads(raw))
            else:
                stale.append(field)
        if stale:
            self.client.hdel(key, *stale)
        return events

    def positions_v3(self, room_id: UUID | str, epochs: dict[str, str]) -> list[dict]:
        now = time.time()
        positions = []
        key = self.key_v3(room_id, "positions")
        # Active rooms refresh this housekeeping TTL through heartbeat snapshots.
        self.client.expire(key, 86400)
        for field, raw in self.client.hgetall(key).items():
            member_id, epoch = field.split(":", 1)
            if epochs.get(member_id) != epoch:
                continue
            event = json.loads(raw)
            if event["data"]["expires_at"] is None or event["data"]["expires_at"] > now:
                positions.append(event)
        return positions


def get_party_realtime_store_v3() -> PartyRealtimeStoreV3:
    return PartyRealtimeStoreV3(get_party_rate_limiter_v3().client)
