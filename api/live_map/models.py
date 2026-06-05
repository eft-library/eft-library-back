from sqlalchemy import Column, Integer, JSON, NUMERIC, String, TEXT, TIMESTAMP

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
    min_z = Column(NUMERIC)
    max_z = Column(NUMERIC)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapPointV3(V3Database.Base):
    __tablename__ = "live_map_points"

    id = Column(String, primary_key=True)
    quest_id = Column(String)
    objective_id = Column(String)
    map_id = Column(String)
    floor_id = Column(String)
    floor_no = Column(Integer)
    x = Column(NUMERIC)
    z = Column(NUMERIC)
    y = Column(NUMERIC)
    sort_order = Column(Integer)
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
    floor_no = Column(Integer)
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
    y = Column(NUMERIC)
    metadata_ = Column("metadata", JSON)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class LiveMapStoryPointV3(V3Database.Base):
    __tablename__ = "live_map_story_points"

    id = Column(String, primary_key=True)
    story_id = Column(String)
    objective_id = Column(String)
    map_id = Column(String)
    floor_id = Column(String)
    floor_no = Column(Integer)
    x = Column(NUMERIC)
    z = Column(NUMERIC)
    y = Column(NUMERIC)
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


class LiveMapEventPointV3(V3Database.Base):
    __tablename__ = "live_map_event_points"

    id = Column(String, primary_key=True)
    event_id = Column(String)
    objective_id = Column(String)
    map_id = Column(String)
    floor_id = Column(String)
    floor_no = Column(Integer)
    x = Column(NUMERIC)
    z = Column(NUMERIC)
    y = Column(NUMERIC)
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
