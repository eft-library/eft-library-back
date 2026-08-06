from sqlalchemy import BOOLEAN, Column, Integer, JSON, NUMERIC, String, TEXT, TIMESTAMP

from database import V3Database


class LiveMapFloorV3(V3Database.Base):
    __tablename__ = "live_map_floors"

    id = Column(String, primary_key=True)
    map_id = Column(String)
    floor_no = Column(Integer)
    name_en = Column(String)
    name_ko = Column(String)
    name_ja = Column(String)
    image = Column(TEXT)
    map_bounds = Column(JSON)
    default_zoom_level = Column(NUMERIC)
    is_main = Column(BOOLEAN)
    min_y = Column(NUMERIC)
    max_y = Column(NUMERIC)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapFloorZoneV3(V3Database.Base):
    __tablename__ = "live_map_floor_zones"

    id = Column(String, primary_key=True)
    floor_id = Column(String)
    map_id = Column(String)
    area_x_min = Column(NUMERIC)
    area_x_max = Column(NUMERIC)
    area_z_min = Column(NUMERIC)
    area_z_max = Column(NUMERIC)
    override_min_y = Column(NUMERIC)
    override_max_y = Column(NUMERIC)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapPointV3(V3Database.Base):
    __tablename__ = "live_map_points"

    id = Column(String, primary_key=True)
    quest_id = Column(String)
    objective_id = Column(String)
    map_id = Column(String)
    floor_id = Column(String)
    x = Column(NUMERIC)
    z = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class LiveMapPointDetailV3(V3Database.Base):
    __tablename__ = "live_map_point_details"

    id = Column(String, primary_key=True)
    point_id = Column(String)
    description_en = Column(TEXT)
    description_ko = Column(TEXT)
    description_ja = Column(TEXT)
    image = Column(TEXT)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapStaticPointV3(V3Database.Base):
    __tablename__ = "live_map_static_points"

    id = Column(String, primary_key=True)
    map_id = Column(String)
    floor_id = Column(String)
    category = Column(String)
    name_en = Column(String)
    name_ko = Column(String)
    name_ja = Column(String)
    description_en = Column(TEXT)
    description_ko = Column(TEXT)
    description_ja = Column(TEXT)
    image = Column(TEXT)
    x = Column(NUMERIC)
    z = Column(NUMERIC)
    metadata_ = Column("metadata", JSON)
    is_use = Column(BOOLEAN)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapBtrRouteV3(V3Database.Base):
    __tablename__ = "live_map_btr_routes"

    id = Column(String, primary_key=True)
    map_id = Column(String)
    name = Column(String)
    spawn_type = Column(String)
    raid_duration_seconds = Column(Integer)
    spawn_remaining_seconds = Column(Integer)
    stop_duration_seconds = Column(Integer)
    timing_variance_seconds = Column(Integer)
    is_use = Column(BOOLEAN)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapBtrRoutePointV3(V3Database.Base):
    __tablename__ = "live_map_btr_route_points"

    id = Column(String, primary_key=True)
    route_id = Column(String)
    x = Column(NUMERIC)
    z = Column(NUMERIC)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapBtrRouteStopV3(V3Database.Base):
    __tablename__ = "live_map_btr_route_stops"

    id = Column(String, primary_key=True)
    route_id = Column(String)
    static_point_id = Column(String)
    route_point_id = Column(String)
    arrival_remaining_seconds = Column(Integer)
    departure_remaining_seconds = Column(Integer)
    visit_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapStoryPointV3(V3Database.Base):
    __tablename__ = "live_map_story_points"

    id = Column(String, primary_key=True)
    story_id = Column(String)
    objective_id = Column(String)
    map_id = Column(String)
    floor_id = Column(String)
    x = Column(NUMERIC)
    z = Column(NUMERIC)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapStoryPointDetailV3(V3Database.Base):
    __tablename__ = "live_map_story_point_details"

    id = Column(String, primary_key=True)
    point_id = Column(String)
    description_en = Column(TEXT)
    description_ko = Column(TEXT)
    description_ja = Column(TEXT)
    image = Column(TEXT)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapStoryRequirementPointV3(V3Database.Base):
    __tablename__ = "live_map_story_requirement_points"

    id = Column(String, primary_key=True)
    story_id = Column(String)
    requirement_id = Column(String)
    map_id = Column(String)
    floor_id = Column(String)
    x = Column(NUMERIC)
    z = Column(NUMERIC)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapStoryRequirementPointDetailV3(V3Database.Base):
    __tablename__ = "live_map_story_requirement_point_details"

    id = Column(String, primary_key=True)
    point_id = Column(String)
    description_en = Column(TEXT)
    description_ko = Column(TEXT)
    description_ja = Column(TEXT)
    image = Column(TEXT)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapEventPointV3(V3Database.Base):
    __tablename__ = "live_map_event_points"

    id = Column(String, primary_key=True)
    event_id = Column(String)
    objective_id = Column(String)
    map_id = Column(String)
    floor_id = Column(String)
    x = Column(NUMERIC)
    z = Column(NUMERIC)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapEventPointDetailV3(V3Database.Base):
    __tablename__ = "live_map_event_point_details"

    id = Column(String, primary_key=True)
    point_id = Column(String)
    description_en = Column(TEXT)
    description_ko = Column(TEXT)
    description_ja = Column(TEXT)
    image = Column(TEXT)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)
