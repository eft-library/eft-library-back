from sqlalchemy import Column, TIMESTAMP, TEXT, JSON
from database import DataBaseConnector


class Wipe(DataBaseConnector.Base):
    """
    wipe
    """

    __tablename__ = "wipe_i18n"

    id = Column("id", TEXT, primary_key=True)
    patch_version = Column(TEXT)
    season_start = Column(TEXT)
    season_end = Column(TEXT)
    create_time = Column(TIMESTAMP)


class Information(DataBaseConnector.Base):
    """
    Information
    """

    __tablename__ = "information_i18n"

    id = Column(TEXT, primary_key=True)
    type = Column(TEXT)
    name = Column(JSON)
    description = Column(TEXT)
    update_time = Column(TIMESTAMP)
