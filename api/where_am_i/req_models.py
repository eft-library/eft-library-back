from pydantic import BaseModel, field_validator
from datetime import datetime
import re


class NormalizedEmailRequestV3(BaseModel):
    email: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_v3(cls, value):
        if isinstance(value, str):
            # Desktop input may include surrounding brackets or trailing punctuation.
            # Only remove known boundary artifacts; never extract an email from text.
            normalized_v3 = re.sub(r"^[\s\[\]]+|[\s.\[\]]+$", "", value.replace("\\", ""))
            # Repair observed desktop suffix artifacts only after the complete Gmail
            # domain. Preserve local-part tags and other domains such as .com.au.
            match_v3 = re.fullmatch(
                r"([A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@gmail\.com)[\s\[\].,'\"+0-9]+",
                normalized_v3, flags=re.IGNORECASE,
            )
            return match_v3.group(1) if match_v3 else normalized_v3
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
