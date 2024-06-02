from sqlalchemy import Column, TEXT, TIMESTAMP

from database import DataBaseConnector


class Headset(DataBaseConnector.Base):
    """
    Headset
    """
    __tablename__ = "tkw_head_phone"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
    update_time = Column(TIMESTAMP)


