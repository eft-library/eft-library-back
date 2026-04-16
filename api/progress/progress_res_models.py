from database import V3Database
from sqlalchemy import Column, TIMESTAMP, ARRAY, TEXT


class UserProgressItemV3(V3Database.Base):
    __tablename__ = "user_progress_item"

    email = Column(TEXT, primary_key=True)
    progress_type = Column(TEXT, primary_key=True)
    item_list = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)


class ProgressItemV3(V3Database.Base):
    __tablename__ = "progress_item"

    id = Column(TEXT, primary_key=True)
    progress_type = Column(TEXT, primary_key=True)
    update_time = Column(TIMESTAMP)
