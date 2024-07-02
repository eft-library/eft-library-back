from sqlalchemy import Column, String, Integer, TEXT, NUMERIC
from sqlalchemy.dialects.postgresql import ARRAY
from database import DataBaseConnector


class HideoutMaster(DataBaseConnector.Base):
    __tablename__ = "tkl_hideout_master"
    id = Column(Integer, primary_key=True)
    name_en = Column(String)
    name_kr = Column(String)
    image = Column(String)
    level_ids = Column(ARRAY(TEXT))


class HideoutItemRequire(DataBaseConnector.Base):
    __tablename__ = "tkl_hideout_item_require"
    id = Column(Integer, primary_key=True)
    level_id = Column(Integer)
    name_en = Column(String)
    name_kr = Column(String)
    count = Column(Integer)
    quantity = Column(Integer)


class HideoutLevel(DataBaseConnector.Base):
    __tablename__ = "tkl_hideout_level"
    id = Column(Integer, primary_key=True)
    level = Column(Integer)
    construction_time = Column(Integer)


class HideoutTraderRequire(DataBaseConnector.Base):
    __tablename__ = "tkl_hideout_trader_require"
    id = Column(Integer, primary_key=True)
    level_id = Column(Integer)
    name_en = Column(String)
    name_kr = Column(String)
    compare = Column(String)
    require_type = Column(String)
    value = Column(Integer)


class HideoutStationRequire(DataBaseConnector.Base):
    __tablename__ = "tkl_hideout_station_require"
    id = Column(Integer, primary_key=True)
    level_id = Column(Integer)
    level = Column(Integer)
    name_en = Column(String)
    name_kr = Column(String)


class HideoutSkillRequire(DataBaseConnector.Base):
    __tablename__ = "tkl_hideout_skill_require"
    id = Column(Integer, primary_key=True)
    level_id = Column(Integer)
    level = Column(Integer)
    name_en = Column(String)
    name_kr = Column(String)


class HideoutBonus(DataBaseConnector.Base):
    __tablename__ = "tkl_hideout_bonus"
    level_id = Column(Integer, primary_key=True)
    type = Column(TEXT, primary_key=True)
    name_en = Column(String)
    name_kr = Column(String)
    value = Column(NUMERIC)
    skill_name_en = Column(String)
    skill_name_kr = Column(String)


class HideoutCrafts(DataBaseConnector.Base):
    __tablename__ = "tkl_hideout_crafts"
    id = Column(Integer, primary_key=True)
    level_id = Column(Integer)
    level = Column(Integer)
    name_en = Column(String)
    name_kr = Column(String)
