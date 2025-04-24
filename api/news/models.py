from sqlalchemy import Column, TIMESTAMP, TEXT
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
