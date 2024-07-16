from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship

from database import DataBaseConnector


class ParentMap(DataBaseConnector.Base):
    """
    parent map
    """

    __tablename__ = "tkl_map_parent"

    id = Column(String, primary_key=True)
    name_en = Column(String)
    name_kr = Column(String)
    three_image = Column(String)
    three_item_path = Column(JSON)
    jpg_image = Column(String)
    jpg_item_path = Column(JSON)
    depth = Column(Integer)
    order = Column(Integer)
    link = Column(String)
    main_image = Column(String)
    mot_image = Column(String)
    map_json = Column(JSON)
    update_time = Column(TIMESTAMP)
    sub = relationship("Map", backref="parent_map")


class Map(DataBaseConnector.Base):
    """
    map
    """

    __tablename__ = "tkl_map"

    id = Column(String, primary_key=True)
    name_en = Column(String)
    name_kr = Column(String)
    three_image = Column(String)
    three_item_path = Column(JSON)
    jpg_image = Column(String)
    jpg_item_path = Column(JSON)
    depth = Column(Integer)
    order = Column(Integer)
    link = Column(String)
    parent_value = Column(String, ForeignKey("tkl_map_parent.id"))
    main_image = Column(String)
    mot_image = Column(String)
    map_json = Column(JSON)
    update_time = Column(TIMESTAMP)
