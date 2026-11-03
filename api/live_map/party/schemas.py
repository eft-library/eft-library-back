from datetime import datetime
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints, field_validator, model_validator


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Nickname = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
Id = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Color = Annotated[str, StringConstraints(to_upper=True, pattern=r"^#[0-9a-fA-F]{6}$")]
Password = Annotated[SecretStr, Field(min_length=4, max_length=128)]
Coordinate = Annotated[float, Field(allow_inf_nan=False)]
MarkerType = Literal["normal", "danger", "rally", "target"]
Data = TypeVar("Data")


class PartyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("password", check_fields=False)
    @classmethod
    def validate_password(cls, value: SecretStr | None):
        if value is not None and not value.get_secret_value().strip():
            raise ValueError("Password must not be blank")
        return value


class PartyCreate(PartyRequest):
    name: Name
    map_id: Id
    password: Password
    nickname: Nickname | None = None
    max_members: int = Field(default=5, ge=1, le=10, strict=True)


class PartyJoin(PartyRequest):
    password: Password
    nickname: Nickname | None = None


class PartyPatchBase(PartyRequest):
    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Explicit null is not allowed")
        return self


class PartyRoomPatch(PartyPatchBase):
    name: Name | None = None
    password: Password | None = None
    is_locked: bool | None = Field(default=None, strict=True)
    max_members: int | None = Field(default=None, ge=1, le=10, strict=True)


class PartyMemberPatch(PartyPatchBase):
    nickname: Nickname | None = None
    color: Color | None = None


class PartyOwnerTransfer(PartyRequest):
    member_id: UUID


class PartyMarkerCreate(PartyRequest):
    map_id: Id | None = None
    floor_id: Id
    x: Coordinate
    z: Coordinate
    marker_type: MarkerType = "normal"
    label: str | None = Field(default=None, max_length=100)


class PartyMarkerUpdate(PartyMarkerCreate):
    version: int = Field(ge=1, le=2147483646, strict=True)


class PartyResponse(BaseModel, Generic[Data]):
    status: int = 200
    msg: str = "OK"
    data: Data


class PartyRoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    map_id: str
    is_locked: bool
    max_members: int
    member_count: int
    create_time: datetime
    update_time: datetime


class PartyRoomList(BaseModel):
    rooms: list[PartyRoomResponse]
    total: int
    limit: int
    offset: int


class PartyMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nickname: str
    color: str
    role: Literal["owner", "member"]
    status: Literal["joined", "left", "kicked"]
    joined_at: datetime


class PartyMarkerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    created_by_member_id: UUID
    map_id: str
    floor_id: str
    x: float
    z: float
    marker_type: MarkerType
    label: str | None
    version: int
    create_time: datetime
    update_time: datetime


class PartySnapshot(BaseModel):
    room: PartyRoomResponse
    me: PartyMemberResponse
    # Includes former members so persistent marker authors can still be displayed.
    members: list[PartyMemberResponse]
    markers: list[PartyMarkerResponse]


class PartyLeaveResponse(BaseModel):
    room_id: UUID
    closed: bool
    owner_member_id: UUID | None


class PartyDeleted(BaseModel):
    id: UUID
