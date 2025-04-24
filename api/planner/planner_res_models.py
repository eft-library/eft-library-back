from database import DataBaseConnector
from sqlalchemy import (
    Column,
    TIMESTAMP,
    ARRAY,
    TEXT,
)


class UserQuest(DataBaseConnector.Base):
    """
    User quest
    """

    __tablename__ = "user_quest"

    user_email = Column(TEXT, primary_key=True)
    quest_list = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)
