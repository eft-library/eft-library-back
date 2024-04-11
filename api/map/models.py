from sqlalchemy import Column, String, JSON
from database import DataBaseConnector


class ThreeMap(DataBaseConnector.Base):
    """
    3D map
    """
    __tablename__ = "tkw_three_map"

    three_map_id = Column(String, primary_key=True)
    three_map_name_en = Column(String)
    three_map_name_kr = Column(String)
    three_map_path = Column(String)
    three_map_item_path = Column(JSON)


class JpgMap(DataBaseConnector.Base):
    """
    2D map
    """
    __tablename__ = "tkw_jpg_map"

    jpg_map_id = Column(String, primary_key=True)
    jpg_map_name_en = Column(String)
    jpg_map_name_kr = Column(String)
    jpg_map_path = Column(String)
    jpg_map_item_path = Column(JSON)
