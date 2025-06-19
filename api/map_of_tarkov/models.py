from sqlalchemy import (
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

from database import DataBaseConnector


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
