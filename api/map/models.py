from sqlalchemy import Boolean, Column, String, JSON, Integer, TIMESTAMP

from database import V3Database


class MapV3(V3Database.Base):
    __tablename__ = "maps"

    id = Column(String, primary_key=True)
    normalized_name = Column(String)
    is_use = Column(Boolean)
    name_en = Column(String)
    name_ko = Column(String)
    name_ja = Column(String)
    parent_map_id = Column(String)
    map_depth = Column(Integer)
    mot_image_en = Column(String)
    mot_image_ko = Column(String)
    mot_image_ja = Column(String)
    three_image = Column(String)
    three_json = Column(JSON)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)
