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

    __tablename__ = "tkl_user_quest"

    user_email = Column(TEXT, primary_key=True)
    quest_id = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)
