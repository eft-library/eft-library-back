from database import DataBaseConnector
from sqlalchemy import (
    Column,
    Integer,
    TIMESTAMP,
    ARRAY,
    TEXT,
    Boolean,
    BIGINT,
)


class User(DataBaseConnector.Base):
    """
    User
    """

    __tablename__ = "tkl_user"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    email = Column(TEXT)
    is_admin = Column(Boolean)
    attendance_count = Column(Integer)
    create_time = Column(TIMESTAMP)
    attendance_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
