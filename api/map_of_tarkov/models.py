from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, ARRAY, TEXT

from database import DataBaseConnector


# class Boss(DataBaseConnector.Base):
#     """
#     Boss
#     """
#
#     __tablename__ = "tkw_boss_info"
#
#     boss_id = Column(Integer, primary_key=True)
#     boss_name_en = Column(String)
#     boss_name_kr = Column(String)
#     boss_faction = Column(String)
#     boss_location_spawn_chance_en = Column(JSON)
#     boss_location_spawn_chance_kr = Column(JSON)
#     boss_followers_en = Column(ARRAY(TEXT))
#     boss_followers_kr = Column(ARRAY(TEXT))
#     boss_img_path = Column(TEXT)
#     boss_health_img_path = Column(ARRAY(TEXT))
#     boss_health_total = Column(Integer)
#     boss_location_guide = Column(TEXT)
#     boss_loot = Column(ARRAY(TEXT))
#     boss_spawn = Column(ARRAY(TEXT))
#     boss_update_time = Column(TIMESTAMP)
#
#
# class Map(DataBaseConnector.Base):
#     """
#     map
#     """
#     __tablename__ = "tkw_map"
#
#     map_id = Column(String, primary_key=True)
#     map_name_en = Column(String)
#     map_name_kr = Column(String)
#     map_three_path = Column(String)
#     map_three_item_path = Column(JSON)
#     map_jpg_path = Column(String)
#     map_jpg_item_path = Column(JSON)
#     map_depth = Column(Integer)
#     map_order = Column(Integer)
#     map_link = Column(String)
#     map_parent_value = Column(String)
#     map_main_image = Column(String)
#     map_update_time = Column(TIMESTAMP)