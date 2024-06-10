from sqlalchemy import Column, TEXT, TIMESTAMP, ARRAY, INTEGER, NUMERIC, JSON

from database import DataBaseConnector


class Headset(DataBaseConnector.Base):
    """
    Headset
    """

    __tablename__ = "tkw_head_phone"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
    update_time = Column(TIMESTAMP)


class HeadWear(DataBaseConnector.Base):
    """
    HeadWear
    """

    __tablename__ = "tkw_head_wear"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    class_value = Column(TEXT)
    areas_en = Column(ARRAY(TEXT))
    areas_kr = Column(ARRAY(TEXT))
    durability = Column(INTEGER)
    ricochet_chance = Column(NUMERIC)
    weight = Column(NUMERIC)
    image = Column(TEXT)
    ricochet_str_kr = Column(TEXT)
    ricochet_str_en = Column(TEXT)
    update_time = Column(TIMESTAMP)


class ArmorVest(DataBaseConnector.Base):
    """
    ArmorVest
    """

    __tablename__ = "tkw_armor_vest"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    class_value = Column(TEXT)
    areas_en = Column(ARRAY(TEXT))
    areas_kr = Column(ARRAY(TEXT))
    durability = Column(INTEGER)
    weight = Column(NUMERIC)
    image = Column(TEXT)
    update_time = Column(TIMESTAMP)


class Rig(DataBaseConnector.Base):
    """
    Rig
    """

    __tablename__ = "tkw_rig"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    class_value = Column(TEXT)
    areas_en = Column(ARRAY(TEXT))
    areas_kr = Column(ARRAY(TEXT))
    durability = Column(INTEGER)
    capacity = Column(INTEGER)
    weight = Column(NUMERIC)
    image = Column(TEXT)
    update_time = Column(TIMESTAMP)


class Backpack(DataBaseConnector.Base):
    """
    Backpack
    """

    __tablename__ = "tkw_backpack"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    grids = Column(JSON)
    capacity = Column(INTEGER)
    weight = Column(NUMERIC)
    image = Column(TEXT)
    update_time = Column(TIMESTAMP)
