from database import DataBaseConnector
from sqlalchemy import Column, Integer, TIMESTAMP, ARRAY, TEXT, NUMERIC


class Weapon(DataBaseConnector.Base):
    """
    Weapon Gun
    """

    __tablename__ = "tkl_weapon"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
    category = Column(TEXT)
    carliber = Column(TEXT)
    default_ammo = Column(TEXT)
    modes_en = Column(ARRAY(TEXT))
    modes_kr = Column(ARRAY(TEXT))
    fire_rate = Column(Integer)
    ergonomics = Column(Integer)
    recoil_vertical = Column(Integer)
    recoil_horizontal = Column(Integer)
    update_time = Column(TIMESTAMP)


class Knife(DataBaseConnector.Base):
    """
    Weapon Knife
    """

    __tablename__ = "tkl_knife"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
    category = Column(TEXT)
    slash_damage = Column(Integer)
    stab_damage = Column(Integer)
    hit_radius = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Throwable(DataBaseConnector.Base):
    """
    Weapon Throwable
    """

    __tablename__ = "tkl_throwable"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
    category = Column(TEXT)
    fuse = Column(NUMERIC)
    min_fuse = Column(NUMERIC)
    min_explosion_distance = Column(Integer)
    max_explosion_distance = Column(Integer)
    fragments = Column(Integer)
    update_time = Column(TIMESTAMP)
