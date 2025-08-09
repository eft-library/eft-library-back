from database import DataBaseConnector
from sqlalchemy import Column, TIMESTAMP, ARRAY, TEXT, NUMERIC


class UserRoadmap(DataBaseConnector.Base):
    """
    user roadmap
    """

    __tablename__ = "user_roadmap"

    user_email = Column(TEXT, primary_key=True)
    quest_list = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)


class RoadmapNode(DataBaseConnector.Base):
    """
    roadmap node
    """

    __tablename__ = "roadmap_node"

    id = Column(TEXT, primary_key=True)
    prev_list = Column(ARRAY(TEXT))
    next_list = Column(ARRAY(TEXT))
    total_x_coordinate = Column(NUMERIC)
    total_y_coordinate = Column(NUMERIC)
    single_x_coordinate = Column(NUMERIC)
    single_y_coordinate = Column(NUMERIC)
    total_kappa_x_coordinate = Column(NUMERIC)
    total_kappa_y_coordinate = Column(NUMERIC)
    single_kappa_x_coordinate = Column(NUMERIC)
    single_kappa_y_coordinate = Column(NUMERIC)
    node_color = Column(TEXT)


class RoadmapEdge(DataBaseConnector.Base):
    """
    roadmap edge
    """

    __tablename__ = "roadmap_edge"

    id = Column(TEXT, primary_key=True)
    source_id = Column(TEXT)
    target_id = Column(TEXT)
