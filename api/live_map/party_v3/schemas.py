from datetime import datetime
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints, field_validator, model_validator


NameV3 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
NicknameV3 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
IdV3 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
ColorV3 = Annotated[str, StringConstraints(to_upper=True, pattern=r"^#[0-9a-fA-F]{6}$")]
PasswordV3 = Annotated[SecretStr, Field(min_length=4, max_length=128)]
CoordinateV3 = Annotated[float, Field(allow_inf_nan=False)]
MarkerTypeV3 = Literal["normal", "danger", "rally", "target"]
DataV3 = TypeVar("DataV3")


class PartyRequestV3(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("password", check_fields=False)
    @classmethod
    def validate_password_v3(cls, value: SecretStr | None):
        if value is not None and not value.get_secret_value().strip():
            raise ValueError("Password must not be blank")
        return value


class PartyCreateV3(PartyRequestV3):
    name: NameV3
    map_id: IdV3
    password: PasswordV3
    nickname: NicknameV3 | None = None
    max_members: int = Field(default=5, ge=1, le=10, strict=True)


class PartyJoinV3(PartyRequestV3):
    password: PasswordV3
    nickname: NicknameV3 | None = None


class PartyPatchBaseV3(PartyRequestV3):
    @model_validator(mode="after")
    def validate_changes_v3(self):
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Explicit null is not allowed")
        return self


class PartyRoomPatchV3(PartyPatchBaseV3):
    name: NameV3 | None = None
    password: PasswordV3 | None = None
    is_locked: bool | None = Field(default=None, strict=True)
    max_members: int | None = Field(default=None, ge=1, le=10, strict=True)


class PartyMemberPatchV3(PartyPatchBaseV3):
    nickname: NicknameV3 | None = None
    color: ColorV3 | None = None


class PartyOwnerTransferV3(PartyRequestV3):
    member_id: UUID


class PartyMarkerCreateV3(PartyRequestV3):
    map_id: IdV3 | None = None
    floor_id: IdV3
    x: CoordinateV3
    z: CoordinateV3
    marker_type: MarkerTypeV3 = "normal"
    label: str | None = Field(default=None, max_length=100)


class PartyMarkerUpdateV3(PartyMarkerCreateV3):
    version: int = Field(ge=1, le=2147483646, strict=True)


class PartyResponseV3(BaseModel, Generic[DataV3]):
    status: int = 200
    msg: str = "OK"
    data: DataV3


class PartyRoomResponseV3(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    map_id: str
    is_locked: bool
    max_members: int
    member_count: int
    create_time: datetime
    update_time: datetime


class PartyRoomListV3(BaseModel):
    rooms: list[PartyRoomResponseV3]
    total: int
    limit: int
    offset: int


class PartyMemberResponseV3(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nickname: str
    color: str
    role: Literal["owner", "member"]
    status: Literal["joined", "left", "kicked"]
    joined_at: datetime


class PartyMarkerResponseV3(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    created_by_member_id: UUID
    map_id: str
    floor_id: str
    x: float
    z: float
    marker_type: MarkerTypeV3
    label: str | None
    version: int
    create_time: datetime
    update_time: datetime


class PartySnapshotV3(BaseModel):
    room: PartyRoomResponseV3
    me: PartyMemberResponseV3
    # Includes former members so persistent marker authors can still be displayed.
    members: list[PartyMemberResponseV3]
    markers: list[PartyMarkerResponseV3]


class PartyLeaveResponseV3(BaseModel):
    room_id: UUID
    closed: bool
    owner_member_id: UUID | None


class PartyDeletedV3(BaseModel):
    id: UUID
