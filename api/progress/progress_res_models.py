from database import DataBaseConnector
from sqlalchemy import (
    Column,
    TIMESTAMP,
    ARRAY,
    TEXT,
)


class UserProgressItem(DataBaseConnector.Base):
    __tablename__ = "user_progress_item"

    user_email = Column(TEXT, primary_key=True)
    progress_type = Column(TEXT, primary_key=True)
    item_list = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)
