from sqlalchemy import Column, String, JSON
from database import DataBaseConnector


# 3D 사진 클래스
class ThreeMap(DataBaseConnector.Base):
    __tablename__ = "tkw_three_map"

    three_map_id = Column(String, primary_key=True)
    three_map_name_en = Column(String)
    three_map_name_kr = Column(String)
    three_map_path = Column(String)
    three_map_item_path = Column(JSON)


class JpgMap(DataBaseConnector.Base):
    __tablename__ = "tkw_jpg_map"

    jpg_map_id = Column(String, primary_key=True)
    jpg_map_name_en = Column(String)
    jpg_map_name_kr = Column(String)
    jpg_map_path = Column(String)
    jpg_map_item_path = Column(JSON)
