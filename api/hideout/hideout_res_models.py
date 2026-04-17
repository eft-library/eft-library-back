from sqlalchemy import ARRAY, JSON, TEXT, TIMESTAMP, Column

from database import V3Database


class UserHideoutV3(V3Database.Base):
    __tablename__ = "user_hideout"

    email = Column(TEXT, primary_key=True)
    complete_list = Column(ARRAY(TEXT))
    item_list = Column(JSON)
    update_time = Column(TIMESTAMP)
