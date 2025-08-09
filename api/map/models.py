from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP

from database import DataBaseConnector


class Map(DataBaseConnector.Base):
    """
    parent map
    """

    __tablename__ = "map_group_i18n"

    id = Column(String, primary_key=True)
    name = Column(JSON)
    three_image = Column(String)
    three_item_path = Column(JSON)
    jpg_image = Column(String)
    jpg_item_path = Column(JSON)
    depth = Column(Integer)
    order = Column(Integer)
    link = Column(String)
    parent_value = Column(String)
    mot_image = Column(JSON)
    map_json = Column(JSON)
    update_time = Column(TIMESTAMP)
