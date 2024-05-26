from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, ARRAY, TEXT, BOOLEAN

from database import DataBaseConnector


class Extraction(DataBaseConnector.Base):
    """
    Extraction info
    """

    __tablename__ = "tkw_extraction_info"

    extraction_id = Column(String, primary_key=True)
    extraction_name = Column(TEXT)
    extraction_image = Column(TEXT)
    extraction_faction = Column(String)
    extraction_always_available = Column(BOOLEAN)
    extraction_single_use = Column(BOOLEAN)
    extraction_requirements = Column(JSON)
    extraction_tip = Column(ARRAY(TEXT))
    extraction_map = Column(String)
    extraction_update_time = Column(TIMESTAMP)
