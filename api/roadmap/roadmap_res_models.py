from database import V3Database
from sqlalchemy import Column, TIMESTAMP, ARRAY, TEXT, NUMERIC


class UserRoadmapV3(V3Database.Base):
    __tablename__ = "user_roadmap"

    email = Column(TEXT, primary_key=True)
    quest_list = Column(ARRAY(TEXT))
    update_time = Column(TIMESTAMP)


class RoadmapNodeV3(V3Database.Base):
    __tablename__ = "roadmap_node"

    id = Column(TEXT, primary_key=True)
    total_x_coordinate = Column(NUMERIC)
    total_y_coordinate = Column(NUMERIC)
    single_x_coordinate = Column(NUMERIC)
    single_y_coordinate = Column(NUMERIC)
    total_kappa_x_coordinate = Column(NUMERIC)
    total_kappa_y_coordinate = Column(NUMERIC)
    single_kappa_x_coordinate = Column(NUMERIC)
    single_kappa_y_coordinate = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class RoadmapEdgeV3(V3Database.Base):
    __tablename__ = "roadmap_edge"

    id = Column(TEXT, primary_key=True)
    source_id = Column(TEXT)
    target_id = Column(TEXT)
    update_time = Column(TIMESTAMP)
