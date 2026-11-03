from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictBool, Field, StringConstraints, model_validator


Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
Channel = Literal['lobby', 'party']
Status = Literal['pending', 'accepted', 'rejected', 'revoked', 'expired']
StatusReason = Literal['cancelled', 'room_closed', 'room_full', 'already_joined', 'member_kicked', 'receiver_unavailable']


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ChatSend(ChatRequest):
    type: Literal['send_message'] = 'send_message'
    channel: Channel
    room_id: UUID | None = None
    message: Text
    request_id: UUID

    @model_validator(mode='after')
    def validate_channel(self):
        if (self.channel == 'party') != (self.room_id is not None):
            raise ValueError('room_id is required only for party messages')
        return self


class InvitationCreate(ChatRequest):
    room_id: UUID
    invitee_user_id: UUID


class ChatReportCreate(ChatRequest):
    reason: Literal['spam', 'abuse', 'inappropriate', 'personal_info', 'other']
    detail: str | None = Field(default=None, max_length=1000)


class ChatRestrictionCreate(ChatRequest):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    expires_at: datetime | None = None

    @model_validator(mode='after')
    def validate_expiry(self):
        if self.expires_at is not None and (
            self.expires_at.tzinfo is None or self.expires_at <= datetime.now(timezone.utc)
        ):
            raise ValueError('expires_at must be a future timezone-aware timestamp or null (permanent)')
        return self


class ChatUserResponse(BaseModel):
    id: UUID
    nickname: str


class ChatMessageResponse(BaseModel):
    id: UUID
    channel: Channel
    room_id: UUID | None
    user: ChatUserResponse
    message: str
    create_time: datetime


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
    next_before: str | None


class InvitationPartyResponse(BaseModel):
    id: UUID
    name: str
    member_count: int
    max_members: int
    is_locked: bool
    closed: bool
    can_join: bool


class InvitationResponse(BaseModel):
    id: UUID
    invitation_id: UUID
    notification_tab: Literal['party'] = 'party'
    room_id: UUID
    inviter: ChatUserResponse
    invitee_user_id: UUID
    status: Status
    status_reason: StatusReason | None
    expires_at: datetime
    party: InvitationPartyResponse


class ChatBlockResponse(BaseModel):
    user_id: UUID
    blocked: bool


class ChatIdResponse(BaseModel):
    id: UUID


class ChatDeletedResponse(BaseModel):
    message_id: UUID


class ChatRestrictionResponse(BaseModel):
    user_id: UUID
    restricted: bool


class ChatReportResponse(BaseModel):
    id: UUID
    user_id: UUID
    message_id: UUID
    reason: str
    detail: str | None
    create_time: datetime
    message: ChatMessageResponse


class ChatRestrictionDetail(BaseModel):
    user: ChatUserResponse
    reason: str
    expires_at: datetime | None
    create_time: datetime


class ChatModerationState(BaseModel):
    is_admin: bool
    restricted: bool
    reason: str | None
    expires_at: datetime | None


class PartyNotifications(BaseModel):
    party_invitation_count: int
    notification_tab: Literal['party'] = 'party'


class ChatUserActions(BaseModel):
    user: ChatUserResponse
    blocked: bool
    can_block: bool
    can_restrict: bool
    can_invite: bool
    invite_disabled_reason: str | None
    retry_after: int | None = None
    member_id: UUID | None
    can_unkick: bool


class ChatConnectionResponse(BaseModel):
    id: UUID
    user: ChatUserResponse
    connected_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    disconnected_at: datetime | None
    disconnect_reason: Literal['closed', 'expired'] | None
    online: bool


class ChatInvitePreferencesUpdate(ChatRequest):
    allow_party_invites: StrictBool


class ChatInvitePreferencesResponse(BaseModel):
    allow_party_invites: bool
