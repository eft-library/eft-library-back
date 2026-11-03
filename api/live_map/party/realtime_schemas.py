from typing import Annotated, Literal

from pydantic import Field, SecretStr, TypeAdapter

from .schemas import Coordinate, Id, MarkerType, PartyRequest


class PartySocketAuth(PartyRequest):
    type: Literal["auth"]
    token: SecretStr = Field(min_length=1, max_length=4096)


class PartyHeartbeat(PartyRequest):
    type: Literal["heartbeat", "sync"]


class PartyPing(PartyRequest):
    type: Literal["ping"]
    map_id: Id | None = None
    floor_id: Id
    x: Coordinate
    z: Coordinate
    marker_type: MarkerType = "normal"
    label: str | None = Field(default=None, max_length=100)
    request_id: str | None = Field(default=None, max_length=64)


class PartyPosition(PartyRequest):
    type: Literal["position"]
    map_id: Id | None = None
    persistent: bool = False
    floor_id: Id
    x: Coordinate
    z: Coordinate
    yaw: float | None = Field(default=None, ge=0, lt=360, allow_inf_nan=False)
    request_id: str | None = Field(default=None, max_length=64)


class PartyViewMap(PartyRequest):
    type: Literal["view_map"]
    map_id: Id
    floor_id: Id


PartySocketMessage = Annotated[
    PartyHeartbeat | PartyPing | PartyPosition | PartyViewMap, Field(discriminator="type"),
]
socket_message_adapter = TypeAdapter(PartySocketMessage)
