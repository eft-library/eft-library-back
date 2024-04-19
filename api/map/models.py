from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship

from database import DataBaseConnector


class ParentMap(DataBaseConnector.Base):
    """
    parent map
    """
    __tablename__ = "tkw_map_parent"

    map_id = Column(String, primary_key=True)
    map_name_en = Column(String)
    map_name_kr = Column(String)
    map_three_path = Column(String)
    map_three_item_path = Column(JSON)
    map_jpg_path = Column(String)
    map_jpg_item_path = Column(JSON)
    map_depth = Column(Integer)
    map_link = Column(String)
    map_main_image = Column(String)
    map_update_time = Column(TIMESTAMP)
    map_sub = relationship("Map", backref="parent_map")


class Map(DataBaseConnector.Base):
    """
    map
    """
    __tablename__ = "tkw_map"

    map_id = Column(String, primary_key=True)
    map_name_en = Column(String)
    map_name_kr = Column(String)
    map_three_path = Column(String)
    map_three_item_path = Column(JSON)
    map_jpg_path = Column(String)
    map_jpg_item_path = Column(JSON)
    map_depth = Column(Integer)
    map_link = Column(String)
    map_parent_value = Column(String, ForeignKey('tkw_map_parent.map_id'))
    map_main_image = Column(String)
    map_update_time = Column(TIMESTAMP)

