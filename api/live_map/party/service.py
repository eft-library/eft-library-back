from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from api.live_map.models import LiveMapFloor
from api.map.models import Map
from api.user.user_res_models import User
from .models import PartyMarker, PartyMember, PartyRoom
from .schemas import (
    PartyCreate, PartyDeleted, PartyJoin, PartyLeaveResponse,
    PartyMarkerCreate, PartyMarkerResponse, PartyMarkerUpdate,
    PartyMemberPatch, PartyMemberResponse, PartyRoomList,
    PartyRoomPatch, PartyRoomResponse, PartySnapshot,
)
from .security import PartyPassword, PartyRateLimiter, get_party_rate_limiter


class PartyService:
    colors = (
        "#EF4444", "#3B82F6", "#22C55E", "#EAB308", "#A855F7",
        "#F97316", "#06B6D4", "#EC4899", "#84CC16", "#6366F1",
    )

    def __init__(self, session: Session, limiter: PartyRateLimiter | None = None):
        self.session = session
        self.limiter = limiter

    def _limit(self, email: str, action: str, limit: int):
        (self.limiter or get_party_rate_limiter()).consume(email, action, limit)

    def _room(self, room_id: UUID) -> PartyRoom:
        # Every room read/write uses this lock, so membership checks, capacity,
        # ownership changes and marker writes have one consistent lock order.
        room = self.session.scalar(
            select(PartyRoom).where(PartyRoom.id == room_id).with_for_update()
        )
        if room is None:
            raise HTTPException(404, "ROOM_NOT_FOUND")
        if room.closed_at is not None:
            raise HTTPException(410, "ROOM_CLOSED")
        self.session.info["party_room_id_v3"] = room.id
        return room

    def _member(self, room_id: UUID, email: str) -> PartyMember:
        member = self.session.scalar(select(PartyMember).where(
            PartyMember.room_id == room_id, PartyMember.user_email == email,
        ))
        if member is None or member.status != "joined":
            raise HTTPException(403, "PARTY_MEMBERSHIP_REQUIRED")
        return member

    def _owner(self, room_id: UUID, email: str) -> PartyMember:
        member = self._member(room_id, email)
        if member.role != "owner":
            raise HTTPException(403, "PARTY_OWNER_REQUIRED")
        return member

    def _account(self, email: str) -> User:
        account = self.session.get(User, email)
        if account is None:
            raise HTTPException(403, "REGISTERED_USER_REQUIRED")
        return account

    def _joined(self, room_id: UUID) -> list[PartyMember]:
        return list(self.session.scalars(select(PartyMember).where(
            PartyMember.room_id == room_id, PartyMember.status == "joined",
        ).order_by(PartyMember.joined_at, PartyMember.id)))

    def _nickname(self, account: User, requested: str | None) -> str:
        return requested or (account.nickname or "").strip()[:30] or "플레이어"

    def _color(self, members: list[PartyMember], preferred: str | None = None) -> str:
        used = {member.color for member in members}
        if preferred is not None and preferred not in used:
            return preferred
        return next(color for color in self.colors if color not in used)

    def _room_response(self, room: PartyRoom, count: int) -> PartyRoomResponse:
        # Explicit allowlist: never serialize password_hash or account identifiers.
        return PartyRoomResponse(
            id=room.id, name=room.name, map_id=room.map_id, is_locked=room.is_locked,
            max_members=room.max_members, member_count=count,
            create_time=room.create_time, update_time=room.update_time,
        )

    def _snapshot(self, room: PartyRoom, me: PartyMember) -> PartySnapshot:
        self.session.flush()
        members = list(self.session.scalars(select(PartyMember).where(
            PartyMember.room_id == room.id,
        ).order_by(PartyMember.joined_at, PartyMember.id)))
        markers = list(self.session.scalars(select(PartyMarker).where(
            PartyMarker.room_id == room.id,
        ).order_by(PartyMarker.create_time, PartyMarker.id)))
        return PartySnapshot(
            room=self._room_response(room, sum(m.status == "joined" for m in members)),
            me=PartyMemberResponse.model_validate(me),
            members=[PartyMemberResponse.model_validate(m) for m in members],
            markers=[PartyMarkerResponse.model_validate(m) for m in markers],
        )

    def list_rooms(self, search: str | None, map_id: str | None, limit: int, offset: int):
        filters = [PartyRoom.closed_at.is_(None)]
        if search:
            filters.append(PartyRoom.name.icontains(search, autoescape=True))
        if map_id:
            filters.append(PartyRoom.map_id == map_id)
        counts = select(
            PartyMember.room_id, func.count().label("member_count"),
        ).where(PartyMember.status == "joined").group_by(PartyMember.room_id).subquery()
        rows = self.session.execute(select(
            PartyRoom, func.coalesce(counts.c.member_count, 0),
        ).outerjoin(counts, counts.c.room_id == PartyRoom.id).where(*filters)
            .order_by(PartyRoom.create_time.desc(), PartyRoom.id).limit(limit).offset(offset))
        total = self.session.scalar(select(func.count()).select_from(PartyRoom).where(*filters))
        return PartyRoomList(
            rooms=[self._room_response(room, count) for room, count in rows],
            total=total, limit=limit, offset=offset,
        )

    def create_room(self, email: str, data: PartyCreate):
        account = self._account(email)
        self._limit(email, "create", 5)
        map_data = self.session.get(Map, data.map_id)
        floor_exists = self.session.scalar(select(LiveMapFloor.id).join(
            Map, Map.id == LiveMapFloor.map_id,
        ).where(or_(Map.id == data.map_id, Map.parent_map_id == data.map_id)).limit(1))
        if map_data is None or map_data.is_use is False or floor_exists is None:
            raise HTTPException(422, "LIVE_MAP_NOT_AVAILABLE")
        now = datetime.now(timezone.utc)
        room = PartyRoom(
            id=uuid4(), name=data.name, map_id=data.map_id,
            password_hash=PartyPassword.hash(data.password.get_secret_value()),
            is_locked=False, max_members=data.max_members, create_time=now, update_time=now,
        )
        self.session.add(room)
        self.session.flush()
        self.session.info["party_room_id_v3"] = room.id
        owner = PartyMember(
            id=uuid4(), room_id=room.id, user_email=email,
            nickname=self._nickname(account, data.nickname), color=self.colors[0],
            role="owner", status="joined", joined_at=now, create_time=now, update_time=now,
        )
        self.session.add(owner)
        return self._snapshot(room, owner)

    def get_room(self, room_id: UUID, email: str):
        room = self._room(room_id)
        return self._snapshot(room, self._member(room.id, email))

    def join_room(self, room_id: UUID, email: str, data: PartyJoin):
        account = self._account(email)
        # Limit before locking the room and before the expensive password comparison.
        self._limit(email, "join", 30)
        self._limit(email, f"join:{room_id}", 5)
        room = self._room(room_id)
        member = self.session.scalar(select(PartyMember).where(
            PartyMember.room_id == room.id, PartyMember.user_email == email,
        ))
        if member is not None and member.status == "kicked":
            raise HTTPException(403, "PARTY_MEMBER_KICKED")
        if member is not None and member.status == "joined":
            return self._snapshot(room, member)
        if room.is_locked:
            raise HTTPException(403, "ROOM_LOCKED")
        if not PartyPassword.verify(data.password.get_secret_value(), room.password_hash):
            raise HTTPException(403, "INVALID_ROOM_PASSWORD")
        joined = self._joined(room.id)
        if len(joined) >= room.max_members:
            raise HTTPException(409, "ROOM_FULL")
        now = datetime.now(timezone.utc)
        if member is None:
            member = PartyMember(
                id=uuid4(), room_id=room.id, user_email=email, create_time=now,
            )
            self.session.add(member)
        member.nickname = data.nickname or member.nickname or self._nickname(account, None)
        member.color = self._color(joined, member.color)
        member.role, member.status, member.left_at = "member", "joined", None
        member.joined_at = member.update_time = now
        room.empty_since, room.update_time = None, now
        return self._snapshot(room, member)

    def patch_room(self, room_id: UUID, email: str, data: PartyRoomPatch):
        if data.password is not None:
            self._limit(email, "password-change", 5)
        room = self._room(room_id)
        me = self._owner(room.id, email)
        if data.max_members is not None and data.max_members < len(self._joined(room.id)):
            raise HTTPException(409, "CAPACITY_BELOW_MEMBER_COUNT")
        for field in data.model_fields_set:
            if field == "password":
                room.password_hash = PartyPassword.hash(data.password.get_secret_value())
            else:
                setattr(room, field, getattr(data, field))
        room.update_time = datetime.now(timezone.utc)
        return self._snapshot(room, me)

    def leave_room(self, room_id: UUID, email: str):
        room = self._room(room_id)
        me = self._member(room.id, email)
        was_owner = me.role == "owner"
        now = datetime.now(timezone.utc)
        me.role, me.status, me.left_at, me.update_time = "member", "left", now, now
        self.session.flush()  # Release the partial unique owner/color indexes first.
        joined = self._joined(room.id)
        if not joined:
            room.closed_at = room.empty_since = now
        elif was_owner:
            joined[0].role, joined[0].update_time = "owner", now
        room.update_time = now
        owner = next((m.id for m in joined if m.role == "owner"), None)
        return PartyLeaveResponse(room_id=room.id, closed=not joined, owner_member_id=owner)

    def close_room(self, room_id: UUID, email: str):
        room = self._room(room_id)
        self._owner(room.id, email)
        now = datetime.now(timezone.utc)
        for member in self._joined(room.id):
            member.role, member.status = "member", "left"
            member.left_at = member.update_time = now
        room.closed_at = room.empty_since = room.update_time = now
        return PartyDeleted(id=room.id)

    def kick_member(self, room_id: UUID, email: str, member_id: UUID):
        room = self._room(room_id)
        me = self._owner(room.id, email)
        target = self.session.get(PartyMember, member_id)
        if target is None or target.room_id != room.id or target.status != "joined":
            raise HTTPException(404, "MEMBER_NOT_FOUND")
        if target.id == me.id:
            raise HTTPException(409, "OWNER_MUST_LEAVE_OR_TRANSFER")
        now = datetime.now(timezone.utc)
        target.status, target.role = "kicked", "member"
        target.left_at = target.update_time = room.update_time = now
        return self._snapshot(room, me)

    def unkick_member(self, room_id: UUID, email: str, member_id: UUID):
        room = self._room(room_id)
        me = self._owner(room.id, email)
        target = self.session.get(PartyMember, member_id)
        if target is None or target.room_id != room.id:
            raise HTTPException(404, "MEMBER_NOT_FOUND")
        if target.status == "joined":
            raise HTTPException(409, "MEMBER_NOT_KICKED")
        if target.status == "kicked":
            now = datetime.now(timezone.utc)
            target.status, target.role = "left", "member"
            target.update_time = room.update_time = now
        return self._snapshot(room, me)

    def transfer_owner(self, room_id: UUID, email: str, member_id: UUID):
        room = self._room(room_id)
        me = self._owner(room.id, email)
        target = self.session.get(PartyMember, member_id)
        if target is None or target.room_id != room.id or target.status != "joined":
            raise HTTPException(404, "MEMBER_NOT_FOUND")
        if me.id != target.id:
            now = datetime.now(timezone.utc)
            me.role, me.update_time = "member", now
            self.session.flush()
            target.role, target.update_time, room.update_time = "owner", now, now
        return self._snapshot(room, me)

    def patch_member(self, room_id: UUID, email: str, data: PartyMemberPatch):
        room = self._room(room_id)
        me = self._member(room.id, email)
        if data.color is not None and any(
            m.id != me.id and m.color == data.color for m in self._joined(room.id)
        ):
            raise HTTPException(409, "MEMBER_COLOR_IN_USE")
        for field in data.model_fields_set:
            setattr(me, field, getattr(data, field))
        me.update_time = room.update_time = datetime.now(timezone.utc)
        return PartyMemberResponse.model_validate(me)

    def _validate_floor(self, room: PartyRoom, floor_id: str):
        floor = self.session.scalar(select(LiveMapFloor.id).join(
            Map, Map.id == LiveMapFloor.map_id,
        ).where(LiveMapFloor.id == floor_id, or_(
            Map.id == room.map_id, Map.parent_map_id == room.map_id,
        )))
        if floor is None:
            raise HTTPException(422, "FLOOR_NOT_IN_ROOM_MAP")

    def _validate_map_floor(self, map_id: str, floor_id: str):
        map_data = self.session.get(Map, map_id)
        if map_data is None or not map_data.is_use:
            raise HTTPException(422, "INVALID_MAP")
        floor = self.session.get(LiveMapFloor, floor_id)
        floor_map = self.session.get(Map, floor.map_id) if floor else None
        if floor_map is None or not floor_map.is_use or (
            floor_map.id != map_id and floor_map.parent_map_id != map_id
        ):
            raise HTTPException(422, "FLOOR_NOT_IN_MAP")
        return map_data, floor

    def list_markers(self, room_id: UUID, email: str):
        room = self._room(room_id)
        self._member(room.id, email)
        return [PartyMarkerResponse.model_validate(marker) for marker in self.session.scalars(
            select(PartyMarker).where(PartyMarker.room_id == room.id)
            .order_by(PartyMarker.create_time, PartyMarker.id)
        )]

    def create_marker(self, room_id: UUID, email: str, data: PartyMarkerCreate):
        room = self._room(room_id)
        me = self._member(room.id, email)
        map_id = data.map_id or room.map_id
        if data.map_id is None:
            self._validate_floor(room, data.floor_id)
        self._validate_map_floor(map_id, data.floor_id)
        count = self.session.scalar(select(func.count()).select_from(PartyMarker).where(
            PartyMarker.room_id == room.id,
        ))
        if count >= 200:
            raise HTTPException(409, "ROOM_MARKER_LIMIT")
        now = datetime.now(timezone.utc)
        marker = PartyMarker(
            id=uuid4(), room_id=room.id, created_by_member_id=me.id,
            **data.model_dump(exclude={"map_id"}), map_id=map_id,
            version=1, create_time=now, update_time=now,
        )
        self.session.add(marker)
        room.update_time = now
        self.session.flush()
        return PartyMarkerResponse.model_validate(marker)

    def _editable_marker(self, room_id: UUID, me: PartyMember, marker_id: UUID, version: int):
        marker = self.session.get(PartyMarker, marker_id)
        if marker is None or marker.room_id != room_id:
            raise HTTPException(404, "MARKER_NOT_FOUND")
        if me.role != "owner" and marker.created_by_member_id != me.id:
            raise HTTPException(403, "MARKER_OWNER_REQUIRED")
        if marker.version != version:
            raise HTTPException(409, "MARKER_VERSION_CONFLICT")
        return marker

    def update_marker(self, room_id: UUID, email: str, marker_id: UUID, data: PartyMarkerUpdate):
        room = self._room(room_id)
        me = self._member(room.id, email)
        marker = self._editable_marker(room.id, me, marker_id, data.version)
        map_id = data.map_id or marker.map_id
        self._validate_map_floor(map_id, data.floor_id)
        marker.map_id = map_id
        for field, value in data.model_dump(exclude={"version", "map_id"}).items():
            setattr(marker, field, value)
        marker.version += 1
        marker.update_time = room.update_time = datetime.now(timezone.utc)
        self.session.flush()
        return PartyMarkerResponse.model_validate(marker)

    def delete_marker(self, room_id: UUID, email: str, marker_id: UUID, version: int):
        room = self._room(room_id)
        me = self._member(room.id, email)
        marker = self._editable_marker(room.id, me, marker_id, version)
        self.session.delete(marker)
        room.update_time = datetime.now(timezone.utc)
        return PartyDeleted(id=marker.id)
