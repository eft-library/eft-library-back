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
    notice_text_en = Column(ARRAY(TEXT))
    notice_text_kr = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)
