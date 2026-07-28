from sqlalchemy import (
    Boolean,
    Column,
    String,
    Integer,
    TIMESTAMP,
    TEXT,
)

from database import V3Database


class MapPointV3(V3Database.Base):
    __tablename__ = "map_points"

    id = Column(String, primary_key=True)
    point_type = Column(String)
    name_en = Column(String)
    name_ko = Column(String)
    name_ja = Column(String)
    is_unlimited_use = Column(Boolean)
    is_one_time_use = Column(Boolean)
    image = Column(TEXT)
    faction = Column(String)
    map_id = Column(String)
    requirements_en = Column(TEXT)
    requirements_ko = Column(TEXT)
    requirements_ja = Column(TEXT)
    tip_en = Column(TEXT)
    tip_ko = Column(TEXT)
    tip_ja = Column(TEXT)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)
