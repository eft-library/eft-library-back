from database import DataBaseConnector
from sqlalchemy import Column, Integer, TIMESTAMP, ARRAY, TEXT, NUMERIC


class Weapon(DataBaseConnector.Base):
    """
    Weapon Gun
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


class Knife(DataBaseConnector.Base):
    """
    Weapon Knife
    """

    __tablename__ = "tkw_knife_info"

    knife_id = Column(TEXT, primary_key=True)
    knife_name = Column(TEXT)
    knife_short_name = Column(TEXT)
    knife_image = Column(TEXT)
    knife_category = Column(TEXT)
    knife_slash_damage = Column(Integer)
    knife_stab_damage = Column(Integer)
    knife_hit_radius = Column(NUMERIC)
    knife_update_time = Column(TIMESTAMP)


class Throwable(DataBaseConnector.Base):
    """
    Weapon Throwable
    """

    __tablename__ = "tkw_throwable_info"

    throwable_id = Column(TEXT, primary_key=True)
    throwable_name = Column(TEXT)
    throwable_short_name = Column(TEXT)
    throwable_image = Column(TEXT)
    throwable_category = Column(TEXT)
    throwable_fuse = Column(NUMERIC)
    throwable_min_fuse = Column(NUMERIC)
    throwable_min_explosion_distance = Column(Integer)
    throwable_max_explosion_distance = Column(Integer)
    throwable_fragments = Column(Integer)
    throwable_update_time = Column(TIMESTAMP)
