from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictBool, Field, StringConstraints, model_validator


TextV3 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
ChannelV3 = Literal['lobby', 'party']
StatusV3 = Literal['pending', 'accepted', 'rejected', 'revoked', 'expired']
StatusReasonV3 = Literal['cancelled', 'room_closed', 'room_full', 'already_joined', 'member_kicked', 'receiver_unavailable']


class ChatRequestV3(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ChatSendV3(ChatRequestV3):
    type: Literal['send_message'] = 'send_message'
    channel: ChannelV3
    room_id: UUID | None = None
    message: TextV3
    request_id: UUID

    @model_validator(mode='after')
    def validate_channel_v3(self):
        if (self.channel == 'party') != (self.room_id is not None):
            raise ValueError('room_id is required only for party messages')
        return self


class InvitationCreateV3(ChatRequestV3):
    room_id: UUID
    invitee_user_id: UUID


class ChatReportCreateV3(ChatRequestV3):
    reason: Literal['spam', 'abuse', 'inappropriate', 'personal_info', 'other']
    detail: str | None = Field(default=None, max_length=1000)


class ChatRestrictionCreateV3(ChatRequestV3):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    expires_at: datetime | None = None

    @model_validator(mode='after')
    def validate_expiry_v3(self):
        if self.expires_at is not None and (
            self.expires_at.tzinfo is None or self.expires_at <= datetime.now(timezone.utc)
        ):
            raise ValueError('expires_at must be a future timezone-aware timestamp or null (permanent)')
        return self


class ChatUserResponseV3(BaseModel):
    id: UUID
    nickname: str


class ChatMessageResponseV3(BaseModel):
    id: UUID
    channel: ChannelV3
    room_id: UUID | None
    user: ChatUserResponseV3
    message: str
    create_time: datetime


class ChatHistoryResponseV3(BaseModel):
    messages: list[ChatMessageResponseV3]
    next_before: str | None


class InvitationPartyResponseV3(BaseModel):
    id: UUID
    name: str
    member_count: int
    max_members: int
    is_locked: bool
    closed: bool
    can_join: bool


class InvitationResponseV3(BaseModel):
    id: UUID
    invitation_id: UUID
    notification_tab: Literal['party'] = 'party'
    room_id: UUID
    inviter: ChatUserResponseV3
    invitee_user_id: UUID
    status: StatusV3
    status_reason: StatusReasonV3 | None
    expires_at: datetime
    party: InvitationPartyResponseV3


class ChatBlockResponseV3(BaseModel):
    user_id: UUID
    blocked: bool


class ChatIdResponseV3(BaseModel):
    id: UUID


class ChatDeletedResponseV3(BaseModel):
    message_id: UUID


class ChatRestrictionResponseV3(BaseModel):
    user_id: UUID
    restricted: bool


class ChatReportResponseV3(BaseModel):
    id: UUID
    user_id: UUID
    message_id: UUID
    reason: str
    detail: str | None
    create_time: datetime
    message: ChatMessageResponseV3


class ChatRestrictionDetailV3(BaseModel):
    user: ChatUserResponseV3
    reason: str
    expires_at: datetime | None
    create_time: datetime


class ChatModerationStateV3(BaseModel):
    is_admin: bool
    restricted: bool
    reason: str | None
    expires_at: datetime | None


class PartyNotificationsV3(BaseModel):
    party_invitation_count: int
    notification_tab: Literal['party'] = 'party'


class ChatUserActionsV3(BaseModel):
    user: ChatUserResponseV3
    blocked: bool
    can_block: bool
    can_restrict: bool
    can_invite: bool
    invite_disabled_reason: str | None
    retry_after: int | None = None
    member_id: UUID | None
    can_unkick: bool


class ChatConnectionResponseV3(BaseModel):
    id: UUID
    user: ChatUserResponseV3
    connected_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    disconnected_at: datetime | None
    disconnect_reason: Literal['closed', 'expired'] | None
    online: bool


class ChatInvitePreferencesUpdateV3(ChatRequestV3):
    allow_party_invites: StrictBool


class ChatInvitePreferencesResponseV3(BaseModel):
    allow_party_invites: bool
