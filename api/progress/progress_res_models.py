from database import DataBaseConnector
from sqlalchemy import Column, TIMESTAMP, ARRAY, TEXT, JSON


class UserProgressItem(DataBaseConnector.Base):
    __tablename__ = "user_progress_item"

    user_email = Column(TEXT, primary_key=True)
    progress_type = Column(TEXT, primary_key=True)
    item_list = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)


class ProgressItem(DataBaseConnector.Base):
    __tablename__ = "progress_item_i18n"

    id = Column(TEXT, primary_key=True)
    name = Column(JSON)
    progress_type = Column(TEXT, primary_key=True)
    image = Column(TEXT)
    update_time = Column(TIMESTAMP)
