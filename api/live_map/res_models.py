from pydantic import BaseModel


class BtrRoutePointV3(BaseModel):
    id: str
    x: float
    z: float
    sort_order: int


class BtrRouteStopV3(BaseModel):
    """BTR stop timing values use the in-raid remaining-time clock."""

    id: str
    static_point_id: str
    route_point_id: str | None
    name_en: str
    name_ko: str
    name_ja: str
    x: float
    z: float
    arrival_remaining_seconds: int
    departure_remaining_seconds: int | None
    visit_order: int
    route_point_order: int | None


class BtrRouteV3(BaseModel):
    """Static BTR route geometry and timetable; no current position is calculated."""

    id: str
    name: str
    spawn_type: str | None
    raid_duration_seconds: int
    spawn_remaining_seconds: int | None
    stop_duration_seconds: int
    timing_variance_seconds: int
    points: list[BtrRoutePointV3]
    stops: list[BtrRouteStopV3]


class BtrRouteMapV3(BaseModel):
    id: str
    normalized_name: str


class BtrRoutesResponseV3(BaseModel):
    map: BtrRouteMapV3
    routes: list[BtrRouteV3]
