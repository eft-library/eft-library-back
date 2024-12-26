from database import DataBaseConnector
from sqlalchemy import (
    Column,
    TIMESTAMP,
    ARRAY,
    TEXT,
)


class UserRoadmap(DataBaseConnector.Base):
    """
    user roadmap
    """

    __tablename__ = "tkl_user_roadmap"

    user_email = Column(TEXT, primary_key=True)
    quest_list = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)
