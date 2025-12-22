from database import DataBaseConnector
from sqlalchemy import (
    Column,
    TIMESTAMP,
    TEXT,
    func,
)


class UserLocationRequest(DataBaseConnector.Base):

    __tablename__ = "user_location_request"

    id = Column(TEXT, primary_key=True)
    user_email = Column(TEXT)
    location = Column(TEXT)
    create_time = Column(TIMESTAMP, server_default=func.now())
