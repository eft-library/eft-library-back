import time
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from database import Database
from .models import PartyMember, PartyRoom
from .realtime_schemas import PartyHeartbeat, PartyPing, PartyPosition, PartyViewMap
from .realtime_store import PartyRealtimeStore, get_party_realtime_store, membership_epoch
from .security import PartyRateLimiter
from .service import PartyService


@dataclass(frozen=True)
class PartyConnection:
    room_id: UUID
    email: str
    member_id: UUID
    epoch: str
    connection_id: str


class PartyRealtimeService:
    def __init__(self, store: PartyRealtimeStore | None = None):
        self.store = store or get_party_realtime_store()

    def _authorized(self, service: PartyService, connection: PartyConnection):
        room = service._room(connection.room_id)
        member = service._member(room.id, connection.email)
        if member.id != connection.member_id or membership_epoch(member.joined_at) != connection.epoch:
            raise HTTPException(403, "PARTY_MEMBERSHIP_CHANGED")
        return room, member

    def _snapshot(self, service: PartyService, room, member, reason: str) -> dict:
        snapshot = service._snapshot(room, member)
        epochs = {
            str(m.id): membership_epoch(m.joined_at)
            for m in snapshot.members if m.status == "joined"
        }
        data = snapshot.model_dump(mode="json")
        data.update({
            "presence": self.store.presence(room.id, epochs),
            "positions": self.store.positions(room.id, epochs),
            "view_maps": self.store.view_maps(room.id, epochs),
            "heartbeat_interval_seconds": 15,
            "reconnect_grace_seconds": self.store.reconnect_seconds,
            "reason": reason,
        })
        return self.store.build_event(room.id, "snapshot", data)

    def connect(self, room_id: UUID, email: str, connection_id: str):
        PartyRateLimiter(self.store.client).consume(email, f"ws-connect:{room_id}", 20)
        with Database.SessionLocal.begin() as session:
            service = PartyService(session)
            room = service._room(room_id)
            member = service._member(room.id, email)
            connection = PartyConnection(room.id, email, member.id, membership_epoch(member.joined_at), connection_id)
            self.store.touch(room.id, member.id, connection.epoch, connection_id)
            room.empty_since = None
            snapshot = self._snapshot(service, room, member, "connected")
        return connection, snapshot

    def refresh(self, connection: PartyConnection, reason: str = "changed", touch: bool = False):
        with Database.SessionLocal.begin() as session:
            service = PartyService(session)
            room, member = self._authorized(service, connection)
            if touch:
                self.store.touch(room.id, member.id, connection.epoch, connection.connection_id)
                room.empty_since = None
            return self._snapshot(service, room, member, reason)

    def message(self, connection: PartyConnection, message: PartyHeartbeat | PartyPing | PartyPosition | PartyViewMap):
        PartyRateLimiter(self.store.client).consume(connection.email, f"ws-message:{connection.room_id}", 120)
        if isinstance(message, PartyHeartbeat):
            return self.refresh(connection, message.type, touch=True)
        if isinstance(message, PartyPing):
            PartyRateLimiter(self.store.client).consume(connection.email, f"ws-ping:{connection.room_id}", 30)
        with Database.SessionLocal.begin() as session:
            service = PartyService(session)
            room, member = self._authorized(service, connection)
            if message.map_id is None:
                # Existing clients scope coordinates to the room's original map.
                service._validate_floor(room, message.floor_id)
            map_data, floor = service._validate_map_floor(message.map_id or room.map_id, message.floor_id)
            self.store.touch(room.id, member.id, connection.epoch, connection.connection_id)
            room.empty_since = None
            seconds = self.store.ping_seconds if isinstance(message, PartyPing) else self.store.position_seconds
            payload = message.model_dump(exclude={"type", "persistent"}, exclude_none=True)
            payload.update({
                "map_id": map_data.id,
                "member_id": str(member.id), "membership_epoch": connection.epoch,
                "nickname": member.nickname, "color": member.color,
                "expires_at": None if isinstance(message, PartyPosition) and message.persistent else time.time() + seconds,
            })
            if isinstance(message, PartyViewMap):
                payload.pop("expires_at")
                payload["map"] = {
                    "id": map_data.id,
                    **{name: getattr(map_data, name) for name in ("name_ko", "name_en", "name_ja")},
                }
                payload["floor"] = {
                    "id": floor.id, "map_id": floor.map_id, "floor_no": floor.floor_no,
                    **{name: getattr(floor, name) for name in ("name_ko", "name_en", "name_ja")},
                }
            event = self.store.build_event(room.id, message.type, payload)
            if isinstance(message, PartyViewMap):
                self.store.save_view_map(room.id, str(member.id), connection.epoch, event)
            if isinstance(message, PartyPosition):
                self.store.save_position(room.id, str(member.id), connection.epoch, event)
            self.store.publish(room.id, event)
        # Sender gets the same room broadcast; there is no optimistic success echo.
        return None

    def forward(self, connection: PartyConnection, event: dict):
        if event.get("room_id") != str(connection.room_id):
            return None
        if event.get("type") in ("room.changed", "presence.changed"):
            return self.refresh(connection)
        if event.get("type") not in ("ping", "position", "view_map"):
            return None
        with Database.SessionLocal.begin() as session:
            service = PartyService(session)
            self._authorized(service, connection)
            payload = event["data"]
            actor = session.get(PartyMember, UUID(payload["member_id"]))
            if (
                actor is None or actor.room_id != connection.room_id or actor.status != "joined"
                or membership_epoch(actor.joined_at) != payload["membership_epoch"]
                or (payload.get("expires_at") is not None and payload["expires_at"] <= time.time())
            ):
                return None
            return event

    def disconnect(self, connection: PartyConnection):
        with Database.SessionLocal.begin() as session:
            # Include closed rooms so their leases are also removed on socket shutdown.
            session.scalar(select(PartyRoom).where(PartyRoom.id == connection.room_id).with_for_update())
            self.store.disconnect(
                connection.room_id, connection.member_id, connection.epoch, connection.connection_id,
            )

    def cleanup_room(self, room_id: UUID, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        changed = False
        with Database.SessionLocal.begin() as session:
            room = session.scalar(select(PartyRoom).where(
                PartyRoom.id == room_id, PartyRoom.closed_at.is_(None),
            ).with_for_update(skip_locked=True))
            if room is None:
                return False
            service = PartyService(session)
            members = service._joined(room.id)
            epochs = {str(m.id): membership_epoch(m.joined_at) for m in members}
            online = set(self.store.presence(room.id, epochs)["online_member_ids"])
            if online:
                room.empty_since = None
            elif room.empty_since is None:
                room.empty_since = datetime.fromtimestamp(now, timezone.utc)
            for member in members:
                if str(member.id) in online:
                    continue
                seen = self.store.last_seen(room.id, member.id, epochs[str(member.id)], now)
                if now - seen >= self.store.reconnect_seconds:
                    service.leave_room(room.id, member.user_email)
                    changed = True
            if not members:
                room.closed_at = room.update_time = datetime.fromtimestamp(now, timezone.utc)
                changed = True
        if changed:
            self.store.changed(room_id)
        return changed

    def cleanup_batch(self, after_id: UUID | None, limit: int = 100) -> UUID | None:
        with Database.SessionLocal() as session:
            query = select(PartyRoom.id).where(PartyRoom.closed_at.is_(None))
            if after_id is not None:
                query = query.where(PartyRoom.id > after_id)
            room_ids = list(session.scalars(query.order_by(PartyRoom.id).limit(limit)))
        for room_id in room_ids:
            self.cleanup_room(room_id)
        return room_ids[-1] if len(room_ids) == limit else None
