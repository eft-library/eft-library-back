from typing import Annotated, Literal

from pydantic import Field, SecretStr, TypeAdapter

from .schemas import CoordinateV3, IdV3, MarkerTypeV3, PartyRequestV3


class PartySocketAuthV3(PartyRequestV3):
    type: Literal["auth"]
    token: SecretStr = Field(min_length=1, max_length=4096)


class PartyHeartbeatV3(PartyRequestV3):
    type: Literal["heartbeat", "sync"]


class PartyPingV3(PartyRequestV3):
    type: Literal["ping"]
    map_id: IdV3 | None = None
    floor_id: IdV3
    x: CoordinateV3
    z: CoordinateV3
    marker_type: MarkerTypeV3 = "normal"
    label: str | None = Field(default=None, max_length=100)
    request_id: str | None = Field(default=None, max_length=64)


class PartyPositionV3(PartyRequestV3):
    type: Literal["position"]
    map_id: IdV3 | None = None
    persistent: bool = False
    floor_id: IdV3
    x: CoordinateV3
    z: CoordinateV3
    yaw: float | None = Field(default=None, ge=0, lt=360, allow_inf_nan=False)
    request_id: str | None = Field(default=None, max_length=64)


class PartyViewMapV3(PartyRequestV3):
    type: Literal["view_map"]
    map_id: IdV3
    floor_id: IdV3


PartySocketMessageV3 = Annotated[
    PartyHeartbeatV3 | PartyPingV3 | PartyPositionV3 | PartyViewMapV3, Field(discriminator="type"),
]
socket_message_adapter_v3 = TypeAdapter(PartySocketMessageV3)
