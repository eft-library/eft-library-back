from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from api.live_map.models import LiveMapFloorV3
from api.map.models import MapV3
from api.user.user_res_models import UserV3
from .models import PartyMarkerV3, PartyMemberV3, PartyRoomV3
from .schemas import (
    PartyCreateV3, PartyDeletedV3, PartyJoinV3, PartyLeaveResponseV3,
    PartyMarkerCreateV3, PartyMarkerResponseV3, PartyMarkerUpdateV3,
    PartyMemberPatchV3, PartyMemberResponseV3, PartyRoomListV3,
    PartyRoomPatchV3, PartyRoomResponseV3, PartySnapshotV3,
)
from .security import PartyPasswordV3, PartyRateLimiterV3, get_party_rate_limiter_v3


class PartyServiceV3:
    colors_v3 = (
        "#EF4444", "#3B82F6", "#22C55E", "#EAB308", "#A855F7",
        "#F97316", "#06B6D4", "#EC4899", "#84CC16", "#6366F1",
    )

    def __init__(self, session: Session, limiter: PartyRateLimiterV3 | None = None):
        self.session = session
        self.limiter = limiter

    def _limit_v3(self, email: str, action: str, limit: int):
        (self.limiter or get_party_rate_limiter_v3()).consume_v3(email, action, limit)

    def _room_v3(self, room_id: UUID) -> PartyRoomV3:
        # Every room read/write uses this lock, so membership checks, capacity,
        # ownership changes and marker writes have one consistent lock order.
        room = self.session.scalar(
            select(PartyRoomV3).where(PartyRoomV3.id == room_id).with_for_update()
        )
        if room is None:
            raise HTTPException(404, "ROOM_NOT_FOUND")
        if room.closed_at is not None:
            raise HTTPException(410, "ROOM_CLOSED")
        return room

    def _member_v3(self, room_id: UUID, email: str) -> PartyMemberV3:
        member = self.session.scalar(select(PartyMemberV3).where(
            PartyMemberV3.room_id == room_id, PartyMemberV3.user_email == email,
        ))
        if member is None or member.status != "joined":
            raise HTTPException(403, "PARTY_MEMBERSHIP_REQUIRED")
        return member

    def _owner_v3(self, room_id: UUID, email: str) -> PartyMemberV3:
        member = self._member_v3(room_id, email)
        if member.role != "owner":
            raise HTTPException(403, "PARTY_OWNER_REQUIRED")
        return member

    def _account_v3(self, email: str) -> UserV3:
        account = self.session.get(UserV3, email)
        if account is None:
            raise HTTPException(403, "REGISTERED_USER_REQUIRED")
        return account

    def _joined_v3(self, room_id: UUID) -> list[PartyMemberV3]:
        return list(self.session.scalars(select(PartyMemberV3).where(
            PartyMemberV3.room_id == room_id, PartyMemberV3.status == "joined",
        ).order_by(PartyMemberV3.joined_at, PartyMemberV3.id)))

    def _nickname_v3(self, account: UserV3, requested: str | None) -> str:
        return requested or (account.nickname or "").strip()[:30] or "플레이어"

    def _color_v3(self, members: list[PartyMemberV3], preferred: str | None = None) -> str:
        used = {member.color for member in members}
        if preferred is not None and preferred not in used:
            return preferred
        return next(color for color in self.colors_v3 if color not in used)

    def _room_response_v3(self, room: PartyRoomV3, count: int) -> PartyRoomResponseV3:
        # Explicit allowlist: never serialize password_hash or account identifiers.
        return PartyRoomResponseV3(
            id=room.id, name=room.name, map_id=room.map_id, is_locked=room.is_locked,
            max_members=room.max_members, member_count=count,
            create_time=room.create_time, update_time=room.update_time,
        )

    def _snapshot_v3(self, room: PartyRoomV3, me: PartyMemberV3) -> PartySnapshotV3:
        self.session.flush()
        members = list(self.session.scalars(select(PartyMemberV3).where(
            PartyMemberV3.room_id == room.id,
        ).order_by(PartyMemberV3.joined_at, PartyMemberV3.id)))
        markers = list(self.session.scalars(select(PartyMarkerV3).where(
            PartyMarkerV3.room_id == room.id,
        ).order_by(PartyMarkerV3.create_time, PartyMarkerV3.id)))
        return PartySnapshotV3(
            room=self._room_response_v3(room, sum(m.status == "joined" for m in members)),
            me=PartyMemberResponseV3.model_validate(me),
            members=[PartyMemberResponseV3.model_validate(m) for m in members],
            markers=[PartyMarkerResponseV3.model_validate(m) for m in markers],
        )

    def list_rooms_v3(self, search: str | None, map_id: str | None, limit: int, offset: int):
        filters = [PartyRoomV3.closed_at.is_(None)]
        if search:
            filters.append(PartyRoomV3.name.icontains(search, autoescape=True))
        if map_id:
            filters.append(PartyRoomV3.map_id == map_id)
        counts = select(
            PartyMemberV3.room_id, func.count().label("member_count"),
        ).where(PartyMemberV3.status == "joined").group_by(PartyMemberV3.room_id).subquery()
        rows = self.session.execute(select(
            PartyRoomV3, func.coalesce(counts.c.member_count, 0),
        ).outerjoin(counts, counts.c.room_id == PartyRoomV3.id).where(*filters)
            .order_by(PartyRoomV3.create_time.desc(), PartyRoomV3.id).limit(limit).offset(offset))
        total = self.session.scalar(select(func.count()).select_from(PartyRoomV3).where(*filters))
        return PartyRoomListV3(
            rooms=[self._room_response_v3(room, count) for room, count in rows],
            total=total, limit=limit, offset=offset,
        )

    def create_room_v3(self, email: str, data: PartyCreateV3):
        account = self._account_v3(email)
        self._limit_v3(email, "create", 5)
        map_data = self.session.get(MapV3, data.map_id)
        floor_exists = self.session.scalar(select(LiveMapFloorV3.id).join(
            MapV3, MapV3.id == LiveMapFloorV3.map_id,
        ).where(or_(MapV3.id == data.map_id, MapV3.parent_map_id == data.map_id)).limit(1))
        if map_data is None or map_data.is_use is False or floor_exists is None:
            raise HTTPException(422, "LIVE_MAP_NOT_AVAILABLE")
        now = datetime.now(timezone.utc)
        room = PartyRoomV3(
            id=uuid4(), name=data.name, map_id=data.map_id,
            password_hash=PartyPasswordV3.hash_v3(data.password.get_secret_value()),
            is_locked=False, max_members=data.max_members, create_time=now, update_time=now,
        )
        self.session.add(room)
        self.session.flush()
        owner = PartyMemberV3(
            id=uuid4(), room_id=room.id, user_email=email,
            nickname=self._nickname_v3(account, data.nickname), color=self.colors_v3[0],
            role="owner", status="joined", joined_at=now, create_time=now, update_time=now,
        )
        self.session.add(owner)
        return self._snapshot_v3(room, owner)

    def get_room_v3(self, room_id: UUID, email: str):
        room = self._room_v3(room_id)
        return self._snapshot_v3(room, self._member_v3(room.id, email))

    def join_room_v3(self, room_id: UUID, email: str, data: PartyJoinV3):
        account = self._account_v3(email)
        # Limit before locking the room and before the expensive password comparison.
        self._limit_v3(email, "join", 30)
        self._limit_v3(email, f"join:{room_id}", 5)
        room = self._room_v3(room_id)
        member = self.session.scalar(select(PartyMemberV3).where(
            PartyMemberV3.room_id == room.id, PartyMemberV3.user_email == email,
        ))
        if member is not None and member.status == "kicked":
            raise HTTPException(403, "PARTY_MEMBER_KICKED")
        if member is not None and member.status == "joined":
            return self._snapshot_v3(room, member)
        if room.is_locked:
            raise HTTPException(403, "ROOM_LOCKED")
        if not PartyPasswordV3.verify_v3(data.password.get_secret_value(), room.password_hash):
            raise HTTPException(403, "INVALID_ROOM_PASSWORD")
        joined = self._joined_v3(room.id)
        if len(joined) >= room.max_members:
            raise HTTPException(409, "ROOM_FULL")
        now = datetime.now(timezone.utc)
        if member is None:
            member = PartyMemberV3(
                id=uuid4(), room_id=room.id, user_email=email, create_time=now,
            )
            self.session.add(member)
        member.nickname = data.nickname or member.nickname or self._nickname_v3(account, None)
        member.color = self._color_v3(joined, member.color)
        member.role, member.status, member.left_at = "member", "joined", None
        member.joined_at = member.update_time = now
        room.empty_since, room.update_time = None, now
        return self._snapshot_v3(room, member)

    def patch_room_v3(self, room_id: UUID, email: str, data: PartyRoomPatchV3):
        if data.password is not None:
            self._limit_v3(email, "password-change", 5)
        room = self._room_v3(room_id)
        me = self._owner_v3(room.id, email)
        if data.max_members is not None and data.max_members < len(self._joined_v3(room.id)):
            raise HTTPException(409, "CAPACITY_BELOW_MEMBER_COUNT")
        for field in data.model_fields_set:
            if field == "password":
                room.password_hash = PartyPasswordV3.hash_v3(data.password.get_secret_value())
            else:
                setattr(room, field, getattr(data, field))
        room.update_time = datetime.now(timezone.utc)
        return self._snapshot_v3(room, me)

    def leave_room_v3(self, room_id: UUID, email: str):
        room = self._room_v3(room_id)
        me = self._member_v3(room.id, email)
        was_owner = me.role == "owner"
        now = datetime.now(timezone.utc)
        me.role, me.status, me.left_at, me.update_time = "member", "left", now, now
        self.session.flush()  # Release the partial unique owner/color indexes first.
        joined = self._joined_v3(room.id)
        if not joined:
            room.closed_at = room.empty_since = now
        elif was_owner:
            joined[0].role, joined[0].update_time = "owner", now
        room.update_time = now
        owner = next((m.id for m in joined if m.role == "owner"), None)
        return PartyLeaveResponseV3(room_id=room.id, closed=not joined, owner_member_id=owner)

    def close_room_v3(self, room_id: UUID, email: str):
        room = self._room_v3(room_id)
        self._owner_v3(room.id, email)
        now = datetime.now(timezone.utc)
        for member in self._joined_v3(room.id):
            member.role, member.status = "member", "left"
            member.left_at = member.update_time = now
        room.closed_at = room.empty_since = room.update_time = now
        return PartyDeletedV3(id=room.id)

    def kick_member_v3(self, room_id: UUID, email: str, member_id: UUID):
        room = self._room_v3(room_id)
        me = self._owner_v3(room.id, email)
        target = self.session.get(PartyMemberV3, member_id)
        if target is None or target.room_id != room.id or target.status != "joined":
            raise HTTPException(404, "MEMBER_NOT_FOUND")
        if target.id == me.id:
            raise HTTPException(409, "OWNER_MUST_LEAVE_OR_TRANSFER")
        now = datetime.now(timezone.utc)
        target.status, target.role = "kicked", "member"
        target.left_at = target.update_time = room.update_time = now
        return self._snapshot_v3(room, me)

    def transfer_owner_v3(self, room_id: UUID, email: str, member_id: UUID):
        room = self._room_v3(room_id)
        me = self._owner_v3(room.id, email)
        target = self.session.get(PartyMemberV3, member_id)
        if target is None or target.room_id != room.id or target.status != "joined":
            raise HTTPException(404, "MEMBER_NOT_FOUND")
        if me.id != target.id:
            now = datetime.now(timezone.utc)
            me.role, me.update_time = "member", now
            self.session.flush()
            target.role, target.update_time, room.update_time = "owner", now, now
        return self._snapshot_v3(room, me)

    def patch_member_v3(self, room_id: UUID, email: str, data: PartyMemberPatchV3):
        room = self._room_v3(room_id)
        me = self._member_v3(room.id, email)
        if data.color is not None and any(
            m.id != me.id and m.color == data.color for m in self._joined_v3(room.id)
        ):
            raise HTTPException(409, "MEMBER_COLOR_IN_USE")
        for field in data.model_fields_set:
            setattr(me, field, getattr(data, field))
        me.update_time = room.update_time = datetime.now(timezone.utc)
        return PartyMemberResponseV3.model_validate(me)

    def _validate_floor_v3(self, room: PartyRoomV3, floor_id: str):
        floor = self.session.scalar(select(LiveMapFloorV3.id).join(
            MapV3, MapV3.id == LiveMapFloorV3.map_id,
        ).where(LiveMapFloorV3.id == floor_id, or_(
            MapV3.id == room.map_id, MapV3.parent_map_id == room.map_id,
        )))
        if floor is None:
            raise HTTPException(422, "FLOOR_NOT_IN_ROOM_MAP")

    def list_markers_v3(self, room_id: UUID, email: str):
        room = self._room_v3(room_id)
        self._member_v3(room.id, email)
        return [PartyMarkerResponseV3.model_validate(marker) for marker in self.session.scalars(
            select(PartyMarkerV3).where(PartyMarkerV3.room_id == room.id)
            .order_by(PartyMarkerV3.create_time, PartyMarkerV3.id)
        )]

    def create_marker_v3(self, room_id: UUID, email: str, data: PartyMarkerCreateV3):
        room = self._room_v3(room_id)
        me = self._member_v3(room.id, email)
        self._validate_floor_v3(room, data.floor_id)
        count = self.session.scalar(select(func.count()).select_from(PartyMarkerV3).where(
            PartyMarkerV3.room_id == room.id,
        ))
        if count >= 200:
            raise HTTPException(409, "ROOM_MARKER_LIMIT")
        now = datetime.now(timezone.utc)
        marker = PartyMarkerV3(
            id=uuid4(), room_id=room.id, created_by_member_id=me.id,
            **data.model_dump(), version=1, create_time=now, update_time=now,
        )
        self.session.add(marker)
        room.update_time = now
        self.session.flush()
        return PartyMarkerResponseV3.model_validate(marker)

    def _editable_marker_v3(self, room_id: UUID, me: PartyMemberV3, marker_id: UUID, version: int):
        marker = self.session.get(PartyMarkerV3, marker_id)
        if marker is None or marker.room_id != room_id:
            raise HTTPException(404, "MARKER_NOT_FOUND")
        if me.role != "owner" and marker.created_by_member_id != me.id:
            raise HTTPException(403, "MARKER_OWNER_REQUIRED")
        if marker.version != version:
            raise HTTPException(409, "MARKER_VERSION_CONFLICT")
        return marker

    def update_marker_v3(self, room_id: UUID, email: str, marker_id: UUID, data: PartyMarkerUpdateV3):
        room = self._room_v3(room_id)
        me = self._member_v3(room.id, email)
        marker = self._editable_marker_v3(room.id, me, marker_id, data.version)
        self._validate_floor_v3(room, data.floor_id)
        for field, value in data.model_dump(exclude={"version"}).items():
            setattr(marker, field, value)
        marker.version += 1
        marker.update_time = room.update_time = datetime.now(timezone.utc)
        self.session.flush()
        return PartyMarkerResponseV3.model_validate(marker)

    def delete_marker_v3(self, room_id: UUID, email: str, marker_id: UUID, version: int):
        room = self._room_v3(room_id)
        me = self._member_v3(room.id, email)
        marker = self._editable_marker_v3(room.id, me, marker_id, version)
        self.session.delete(marker)
        room.update_time = datetime.now(timezone.utc)
        return PartyDeletedV3(id=marker.id)
