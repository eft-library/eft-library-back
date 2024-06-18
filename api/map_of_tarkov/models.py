from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, ARRAY, TEXT, BOOLEAN

from database import DataBaseConnector


class Extraction(DataBaseConnector.Base):
    """
    Extraction info
    """

    __tablename__ = "tkw_extraction"

    id = Column(String, primary_key=True)
    name = Column(TEXT)
    image = Column(TEXT)
    faction = Column(String)
    always_available = Column(BOOLEAN)
    single_use = Column(BOOLEAN)
    requirements = Column(JSON)
    tip = Column(ARRAY(TEXT))
    map = Column(String)
    image_thumbnail = Column(TEXT)
    update_time = Column(TIMESTAMP)
