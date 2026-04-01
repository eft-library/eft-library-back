from sqlalchemy import (
    Boolean,
    Column,
    String,
    JSON,
    Integer,
    TIMESTAMP,
    ARRAY,
    TEXT,
    BOOLEAN,
    NUMERIC,
)

from database import DataBaseConnector, V3Database


class Extraction(DataBaseConnector.Base):
    """
    Extraction info
    """

    __tablename__ = "extraction_i18n"

    id = Column(String, primary_key=True)
    name = Column(JSON)
    image = Column(TEXT)
    faction = Column(String)
    always_available = Column(BOOLEAN)
    single_use = Column(BOOLEAN)
    requirements = Column(JSON)
    tip = Column(JSON)
    map = Column(String)
    image_thumbnail = Column(TEXT)
    update_time = Column(TIMESTAMP)


class Transits(DataBaseConnector.Base):
    """
    Transits info
    """

    __tablename__ = "transit_i18n"

    id = Column(String, primary_key=True)
    name = Column(JSON)
    image = Column(TEXT)
    faction = Column(String)
    always_available = Column(BOOLEAN)
    single_use = Column(BOOLEAN)
    requirements = Column(JSON)
    tip = Column(JSON)
    map = Column(String)
    image_thumbnail = Column(TEXT)
    update_time = Column(TIMESTAMP)


class WhereAmI(DataBaseConnector.Base):
    """
    Where am i
    """

    __tablename__ = "where_am_i_i18n"

    id = Column(String, primary_key=True)
    image = Column(TEXT)
    map_bounds = Column(JSON)
    image_bounds = Column(JSON)
    default_zoom_level = Column(NUMERIC)
    quests = Column(JSON)


class WhereAmIV3(V3Database.Base):
    __tablename__ = "where_am_i"

    id = Column(String, primary_key=True)
    image = Column(TEXT)
    map_bounds = Column(JSON)
    image_bounds = Column(JSON)
    default_zoom_level = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class MapPointV3(V3Database.Base):
    __tablename__ = "map_points"

    id = Column(String, primary_key=True)
    point_type = Column(String)
    name_en = Column(String)
    name_ko = Column(String)
    name_ja = Column(String)
    is_unlimited_use = Column(Boolean)
    is_one_time_use = Column(Boolean)
    image = Column(TEXT)
    faction = Column(String)
    map_id = Column(String)
    requirements_en = Column(TEXT)
    requirements_ko = Column(TEXT)
    requirements_ja = Column(TEXT)
    tip_en = Column(TEXT)
    tip_ko = Column(TEXT)
    tip_ja = Column(TEXT)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)
