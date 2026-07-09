from typing import List
from datetime import datetime
from api.roadmap.roadmap_res_models import (
    RoadmapEdgeV3,
    UserRoadmapV3,
)
from database import V3Database
from api.roadmap.query import RoadmapQueryV3
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
import pytz
import logging

logger = logging.getLogger("api.roadmap")


class RoadmapServiceV3:
    @staticmethod
    def _serialize_edge_v3(edge: RoadmapEdgeV3):
        return {
            "id": edge.id,
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "update_time": edge.update_time,
        }

    @staticmethod
    def get_roadmap_v3():
        try:
            with V3Database.SessionLocal() as s:
                roadmap = {}
                node_query = text(RoadmapQueryV3.get_roadmap_node_v3())
                node_result = s.execute(node_query)
                roadmap["node_info"] = [dict(row) for row in node_result.mappings()]

                edge_info = s.query(RoadmapEdgeV3).all()
                roadmap["edge_info"] = [
                    RoadmapServiceV3._serialize_edge_v3(edge) for edge in edge_info
                ]

                return roadmap
        except Exception as e:
            logger.error(
                f"get_roadmap_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_user_roadmap_v3(user_email: str | None):
        try:
            with V3Database.SessionLocal() as s:
                if user_email is not None:
                    user_roadmap = (
                        s.query(UserRoadmapV3)
                        .filter(UserRoadmapV3.email == user_email)
                        .first()
                    )
                    if user_roadmap is not None:
                        return user_roadmap.quest_list
                    return []
                return []
        except Exception as e:
            logger.error(
                f"get_user_roadmap_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def save_roadmap_v3(quest_list: List[str], user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
                kst = pytz.timezone("Asia/Seoul")
                kst_now = utc_now.astimezone(kst)

                stmt = insert(UserRoadmapV3).values(
                    email=user_email,
                    quest_list=quest_list,
                    update_time=kst_now,
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=[UserRoadmapV3.email],
                    set_={
                        "quest_list": stmt.excluded.quest_list,
                        "update_time": stmt.excluded.update_time,
                    },
                )
                s.execute(stmt)
                s.commit()
                return quest_list
        except Exception as e:
            logger.error(
                f"save_roadmap_v3: {quest_list}, error: {e}",
                exc_info=True,
            )
            return None
