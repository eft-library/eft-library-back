import time
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from database import V3Database
from .models import PartyMemberV3, PartyRoomV3
from .realtime_schemas import PartyHeartbeatV3, PartyPingV3, PartyPositionV3
from .realtime_store import PartyRealtimeStoreV3, get_party_realtime_store_v3, membership_epoch_v3
from .security import PartyRateLimiterV3
from .service import PartyServiceV3


@dataclass(frozen=True)
class PartyConnectionV3:
    room_id: UUID
    email: str
    member_id: UUID
    epoch: str
    connection_id: str


class PartyRealtimeServiceV3:
    def __init__(self, store: PartyRealtimeStoreV3 | None = None):
        self.store = store or get_party_realtime_store_v3()

    def _authorized_v3(self, service: PartyServiceV3, connection: PartyConnectionV3):
        room = service._room_v3(connection.room_id)
        member = service._member_v3(room.id, connection.email)
        if member.id != connection.member_id or membership_epoch_v3(member.joined_at) != connection.epoch:
            raise HTTPException(403, "PARTY_MEMBERSHIP_CHANGED")
        return room, member

    def _snapshot_v3(self, service: PartyServiceV3, room, member, reason: str) -> dict:
        snapshot = service._snapshot_v3(room, member)
        epochs = {
            str(m.id): membership_epoch_v3(m.joined_at)
            for m in snapshot.members if m.status == "joined"
        }
        data = snapshot.model_dump(mode="json")
        data.update({
            "presence": self.store.presence_v3(room.id, epochs),
            "positions": self.store.positions_v3(room.id, epochs),
            "heartbeat_interval_seconds": 15,
            "reconnect_grace_seconds": self.store.reconnect_seconds_v3,
            "reason": reason,
        })
        return self.store.event_v3(room.id, "snapshot", data)

    def connect_v3(self, room_id: UUID, email: str, connection_id: str):
        PartyRateLimiterV3(self.store.client).consume_v3(email, f"ws-connect:{room_id}", 20)
        with V3Database.SessionLocal.begin() as session:
            service = PartyServiceV3(session)
            room = service._room_v3(room_id)
            member = service._member_v3(room.id, email)
            connection = PartyConnectionV3(room.id, email, member.id, membership_epoch_v3(member.joined_at), connection_id)
            self.store.touch_v3(room.id, member.id, connection.epoch, connection_id)
            room.empty_since = None
            snapshot = self._snapshot_v3(service, room, member, "connected")
        return connection, snapshot

    def refresh_v3(self, connection: PartyConnectionV3, reason: str = "changed", touch: bool = False):
        with V3Database.SessionLocal.begin() as session:
            service = PartyServiceV3(session)
            room, member = self._authorized_v3(service, connection)
            if touch:
                self.store.touch_v3(room.id, member.id, connection.epoch, connection.connection_id)
                room.empty_since = None
            return self._snapshot_v3(service, room, member, reason)

    def message_v3(self, connection: PartyConnectionV3, message: PartyHeartbeatV3 | PartyPingV3 | PartyPositionV3):
        PartyRateLimiterV3(self.store.client).consume_v3(connection.email, f"ws-message:{connection.room_id}", 120)
        if isinstance(message, PartyHeartbeatV3):
            return self.refresh_v3(connection, message.type, touch=True)
        if isinstance(message, PartyPingV3):
            PartyRateLimiterV3(self.store.client).consume_v3(connection.email, f"ws-ping:{connection.room_id}", 30)
        with V3Database.SessionLocal.begin() as session:
            service = PartyServiceV3(session)
            room, member = self._authorized_v3(service, connection)
            service._validate_floor_v3(room, message.floor_id)
            self.store.touch_v3(room.id, member.id, connection.epoch, connection.connection_id)
            room.empty_since = None
            seconds = self.store.ping_seconds_v3 if isinstance(message, PartyPingV3) else self.store.position_seconds_v3
            payload = message.model_dump(exclude={"type"}, exclude_none=True)
            payload.update({
                "member_id": str(member.id), "membership_epoch": connection.epoch,
                "nickname": member.nickname, "color": member.color,
                "expires_at": time.time() + seconds,
            })
            event = self.store.event_v3(room.id, message.type, payload)
            if isinstance(message, PartyPositionV3):
                self.store.save_position_v3(room.id, str(member.id), connection.epoch, event)
            self.store.publish_v3(room.id, event)
        # Sender gets the same room broadcast; there is no optimistic success echo.
        return None

    def forward_v3(self, connection: PartyConnectionV3, event: dict):
        if event.get("room_id") != str(connection.room_id):
            return None
        if event.get("type") in ("room.changed", "presence.changed"):
            return self.refresh_v3(connection)
        if event.get("type") not in ("ping", "position"):
            return None
        with V3Database.SessionLocal.begin() as session:
            service = PartyServiceV3(session)
            self._authorized_v3(service, connection)
            payload = event["data"]
            actor = session.get(PartyMemberV3, UUID(payload["member_id"]))
            if (
                actor is None or actor.room_id != connection.room_id or actor.status != "joined"
                or membership_epoch_v3(actor.joined_at) != payload["membership_epoch"]
                or payload["expires_at"] <= time.time()
            ):
                return None
            return event

    def disconnect_v3(self, connection: PartyConnectionV3):
        with V3Database.SessionLocal.begin() as session:
            # Include closed rooms so their leases are also removed on socket shutdown.
            session.scalar(select(PartyRoomV3).where(PartyRoomV3.id == connection.room_id).with_for_update())
            self.store.disconnect_v3(
                connection.room_id, connection.member_id, connection.epoch, connection.connection_id,
            )

    def cleanup_room_v3(self, room_id: UUID, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        changed = False
        with V3Database.SessionLocal.begin() as session:
            room = session.scalar(select(PartyRoomV3).where(
                PartyRoomV3.id == room_id, PartyRoomV3.closed_at.is_(None),
            ).with_for_update(skip_locked=True))
            if room is None:
                return False
            service = PartyServiceV3(session)
            members = service._joined_v3(room.id)
            epochs = {str(m.id): membership_epoch_v3(m.joined_at) for m in members}
            online = set(self.store.presence_v3(room.id, epochs)["online_member_ids"])
            if online:
                room.empty_since = None
            elif room.empty_since is None:
                room.empty_since = datetime.fromtimestamp(now, timezone.utc)
            for member in members:
                if str(member.id) in online:
                    continue
                seen = self.store.last_seen_v3(room.id, member.id, epochs[str(member.id)], now)
                if now - seen >= self.store.reconnect_seconds_v3:
                    service.leave_room_v3(room.id, member.user_email)
                    changed = True
            if not members:
                room.closed_at = room.update_time = datetime.fromtimestamp(now, timezone.utc)
                changed = True
        if changed:
            self.store.changed_v3(room_id)
        return changed

    def cleanup_batch_v3(self, after_id: UUID | None, limit: int = 100) -> UUID | None:
        with V3Database.SessionLocal() as session:
            query = select(PartyRoomV3.id).where(PartyRoomV3.closed_at.is_(None))
            if after_id is not None:
                query = query.where(PartyRoomV3.id > after_id)
            room_ids = list(session.scalars(query.order_by(PartyRoomV3.id).limit(limit)))
        for room_id in room_ids:
            self.cleanup_room_v3(room_id)
        return room_ids[-1] if len(room_ids) == limit else None
