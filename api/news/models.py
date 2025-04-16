from sqlalchemy import Column, JSON, TIMESTAMP, TEXT, Boolean
from database import DataBaseConnector


class Wipe(DataBaseConnector.Base):
    """
    wipe
    """

    __tablename__ = "tkl_wipe"

    id = Column("id", TEXT, primary_key=True)
    patch_version = Column(TEXT)
    season_start = Column(TEXT)
    season_end = Column(TEXT)
    create_time = Column(TIMESTAMP)

