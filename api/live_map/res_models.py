from pydantic import BaseModel


class BtrRoutePoint(BaseModel):
    id: str
    x: float
    z: float
    sort_order: int


class BtrRouteStop(BaseModel):
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


class BtrRoute(BaseModel):
    """Static BTR route geometry and timetable; no current position is calculated."""

    id: str
    name: str
    spawn_type: str | None
    raid_duration_seconds: int
    spawn_remaining_seconds: int | None
    stop_duration_seconds: int
    timing_variance_seconds: int
    points: list[BtrRoutePoint]
    stops: list[BtrRouteStop]


class BtrRouteMap(BaseModel):
    id: str
    normalized_name: str


class BtrRoutesResponse(BaseModel):
    map: BtrRouteMap
    routes: list[BtrRoute]
