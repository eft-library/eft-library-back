from database import DataBaseConnector
from sqlalchemy import Column, Integer, TIMESTAMP, ARRAY, TEXT


class Weapon(DataBaseConnector.Base):
    """
    Weapon
    """
    __tablename__ = "tkw_weapon_info"

    weapon_id = Column(TEXT, primary_key=True)
    weapon_name = Column(TEXT)
    weapon_short_name = Column(TEXT)
    weapon_img = Column(TEXT)
    weapon_category = Column(TEXT)
    weapon_carliber = Column(TEXT)
    weapon_default_ammo = Column(TEXT)
    weapon_modes_en = Column(ARRAY(TEXT))
    weapon_modes_kr = Column(ARRAY(TEXT))
    weapon_fire_rate = Column(Integer)
    weapon_ergonomics = Column(Integer)
    weapon_recoil_vertical = Column(Integer)
    weapon_recoil_horizontal = Column(Integer)
    weapon_update_time = Column(TIMESTAMP)



