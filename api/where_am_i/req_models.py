from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, timezone
import re


class NormalizedEmailRequest(BaseModel):
    email: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            # Desktop input may include surrounding brackets or trailing punctuation.
            # Only remove known boundary artifacts; never extract an email from text.
            normalized = re.sub(r"^[\s\[\]]+|[\s.\[\]]+$", "", value.replace("\\", ""))
            # Repair observed desktop suffix artifacts only after the complete Gmail
            # domain. Preserve local-part tags and other domains such as .com.au.
            match = re.fullmatch(
                r"([A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@gmail\.com)[\s\[\].,'\"+0-9]+",
                normalized, flags=re.IGNORECASE,
            )
            return match.group(1) if match else normalized
        return value


class CheckWpfUser(NormalizedEmailRequest):
    pass


class ReqWhereAmI(NormalizedEmailRequest):
    location: str


class RaidStateRequest(NormalizedEmailRequest):
    map: str | None = None
    started_at: datetime | None = None
    is_active: bool
    transit_count: int = 0
    session_id: str | None = Field(default=None, strict=True, min_length=64, max_length=64,
                                  pattern=r'^[a-f0-9]{64}$')
    timer_observed_at: datetime | None = None
    raid_ends_at: datetime | None = None

    @field_validator('started_at', 'timer_observed_at', 'raid_ends_at', mode='before')
    @classmethod
    def validate_raid_time_input(cls, value):
        if value is not None and not isinstance(value, (str, datetime)):
            raise ValueError('ISO 8601 timestamp required')
        return value

    @field_validator('started_at', 'timer_observed_at', 'raid_ends_at')
    @classmethod
    def normalize_raid_time(cls, value):
        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError('Timezone is required')
            return value.astimezone(timezone.utc)
        return value

    @model_validator(mode='after')
    def validate_timer(self):
        if (self.timer_observed_at is None) != (self.raid_ends_at is None):
            raise ValueError('Both timer timestamps must be supplied together')
        if self.raid_ends_at is not None:
            if self.raid_ends_at <= self.timer_observed_at:
                raise ValueError('Raid end must be after timer observation')
            if not self.is_active or not self.map or self.started_at is None or self.session_id is None:
                raise ValueError('Timer requires an active map, start time and session ID')
        return self


class LogLocationRequest(NormalizedEmailRequest):
    map: str | None = None
    x: float
    y: float
    z: float
    observed_at: datetime
