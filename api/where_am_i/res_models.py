from database import V3Database
from sqlalchemy import Column, TIMESTAMP, TEXT, func, INTEGER


class UserLocationRequestV3(V3Database.Base):
    __tablename__ = "user_location_request"

    id = Column(INTEGER, primary_key=True)
    email = Column(TEXT)
    location = Column(TEXT)
    request_time = Column(TIMESTAMP, server_default=func.now())
