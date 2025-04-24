from database import DataBaseConnector
from sqlalchemy import (
    Column,
    TIMESTAMP,
    ARRAY,
    TEXT,
)


class UserHideOut(DataBaseConnector.Base):
    """
    roadmap edge
    """

    __tablename__ = "user_hideout"

    user_email = Column(TEXT, primary_key=True)
    complete_list = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)
