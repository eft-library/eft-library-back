from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# 3D 사진 클래스
class ThreeMap(Base):
    __tablename__ = 'tkw_three_map'

    id = Column(Integer, primary_key=True)
    three_map_id = Column(String)
    three_map_name_en = Column(String)
    three_map_name_kr = Column(String)
    three_map_path = Column(String)
    three_map_item_path = Column(JSON)
