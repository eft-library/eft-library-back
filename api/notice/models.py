from database import DataBaseConnector
from sqlalchemy import Column, String, ARRAY, TEXT, TIMESTAMP


class Notice(DataBaseConnector.Base):
    """
    Notice
    """

    __tablename__ = "tkl_notice"

    id = Column("id", TEXT, primary_key=True)
    name_en = Column(String)
    name_kr = Column(String)
    notes_en = Column(ARRAY(TEXT))
    notes_kr = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)
