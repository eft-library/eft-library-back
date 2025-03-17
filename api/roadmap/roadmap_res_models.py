from database import DataBaseConnector
from sqlalchemy import (
    Column,
    TIMESTAMP,
    ARRAY,
    TEXT,
    ForeignKey,
    NUMERIC
)


class UserRoadmap(DataBaseConnector.Base):
    """
    user roadmap
    """

    __tablename__ = "tkl_user_roadmap"

    user_email = Column(TEXT, primary_key=True)
    quest_list = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)


class RoadmapNode(DataBaseConnector.Base):
    """
    roadmap node
    """

    __tablename__ = "tkl_roadmap_node"

    id = Column(TEXT, primary_key=True)
    prev_list = Column(ARRAY(TEXT))
    next_list = Column(ARRAY(TEXT))
    total_x_coordinate = Column(NUMERIC)
    total_y_coordinate = Column(NUMERIC)
    single_x_coordinate = Column(NUMERIC)
    single_y_coordinate = Column(NUMERIC)
    update_time = Column(TIMESTAMP)
    url_mapping = Column(TEXT)
    title_kr = Column(TEXT)
    title_en = Column(TEXT)
    is_kappa = Column(TEXT)
    npc_value = Column(TEXT, ForeignKey("tkl_npc.id"))
    node_color = Column(TEXT)


class RoadmapEdge(DataBaseConnector.Base):
    """
    roadmap edge
    """

    __tablename__ = "tkl_roadmap_edge"

    id = Column(TEXT, primary_key=True)
    source_id = Column(TEXT)
    target_id = Column(TEXT)
    update_time = Column(TIMESTAMP)
