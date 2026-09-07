from pydantic import BaseModel, field_validator
from datetime import datetime


class NormalizedEmailRequestV3(BaseModel):
    email: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_v3(cls, value):
        if isinstance(value, str):
            return value.replace("\\", "").strip().rstrip(".")
        return value


class CheckWpfUser(NormalizedEmailRequestV3):
    pass


class ReqWhereAmI(NormalizedEmailRequestV3):
    location: str


class RaidStateRequestV3(NormalizedEmailRequestV3):
    map: str | None = None
    started_at: datetime | None = None
    is_active: bool
    transit_count: int = 0


class LogLocationRequestV3(NormalizedEmailRequestV3):
    map: str | None = None
    x: float
    y: float
    z: float
    observed_at: datetime
