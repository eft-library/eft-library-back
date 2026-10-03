from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from database import V3Database


class ChatUserV3(V3Database.Base):
    __tablename__ = "live_map_chat_users_v3"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_email: Mapped[str] = mapped_column(Text, unique=True)
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ChatMessageV3(V3Database.Base):
    __tablename__ = "live_map_chat_messages_v3"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(Uuid)
    channel: Mapped[str] = mapped_column(Text)
    room_id: Mapped[UUID | None] = mapped_column(Uuid)
    request_id: Mapped[UUID] = mapped_column(Uuid)
    message: Mapped[str] = mapped_column(String(300))
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChatBlockV3(V3Database.Base):
    __tablename__ = "live_map_chat_blocks_v3"
    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    target_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ChatReportV3(V3Database.Base):
    __tablename__ = "live_map_chat_reports_v3"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(Uuid)
    message_id: Mapped[UUID] = mapped_column(Uuid)
    reason: Mapped[str] = mapped_column(Text)
    detail: Mapped[str | None] = mapped_column(String(1000))
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ChatRestrictionV3(V3Database.Base):
    __tablename__ = "live_map_chat_restrictions_v3"
    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    moderator_id: Mapped[UUID | None] = mapped_column(Uuid)
    reason: Mapped[str] = mapped_column(String(1000))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PartyInvitationV3(V3Database.Base):
    __tablename__ = "live_map_party_invitations_v3"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    room_id: Mapped[UUID] = mapped_column(Uuid)
    inviter_id: Mapped[UUID] = mapped_column(Uuid)
    invitee_id: Mapped[UUID] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
