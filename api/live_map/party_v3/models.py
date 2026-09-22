from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, Numeric, SmallInteger, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from database import V3Database


# Constraints/indexes are maintained in platform_db.sql; these mappings never create tables.
class PartyRoomV3(V3Database.Base):
    __tablename__ = "live_map_party_rooms"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    map_id: Mapped[str] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text)
    is_locked: Mapped[bool] = mapped_column(Boolean)
    max_members: Mapped[int] = mapped_column(SmallInteger)
    empty_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PartyMemberV3(V3Database.Base):
    __tablename__ = "live_map_party_members"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    room_id: Mapped[UUID] = mapped_column(Uuid)
    user_email: Mapped[str] = mapped_column(Text)
    nickname: Mapped[str] = mapped_column(String(30))
    color: Mapped[str] = mapped_column(String(7))
    role: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PartyMarkerV3(V3Database.Base):
    __tablename__ = "live_map_party_markers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    room_id: Mapped[UUID] = mapped_column(Uuid)
    created_by_member_id: Mapped[UUID] = mapped_column(Uuid)
    map_id: Mapped[str] = mapped_column(Text)
    floor_id: Mapped[str] = mapped_column(Text)
    x: Mapped[Decimal] = mapped_column(Numeric)
    z: Mapped[Decimal] = mapped_column(Numeric)
    marker_type: Mapped[str] = mapped_column(Text)
    label: Mapped[str | None] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer)
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
