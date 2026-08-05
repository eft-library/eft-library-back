from pydantic import BaseModel
from datetime import datetime


class CheckWpfUser(BaseModel):
    email: str


class ReqWhereAmI(BaseModel):
    email: str
    location: str


class RaidStateRequestV3(BaseModel):
    email: str
    map: str | None = None
    started_at: datetime | None = None
    is_active: bool
    transit_count: int = 0


class LogLocationRequestV3(BaseModel):
    email: str
    map: str | None = None
    x: float
    y: float
    z: float
    observed_at: datetime
