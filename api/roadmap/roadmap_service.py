from typing import List
from datetime import datetime
from api.roadmap.roadmap_res_models import UserRoadmap, RoadmapEdge
from database import DataBaseConnector
from api.roadmap.util import RoadmapUtil
from sqlalchemy import text
import pytz
import logging

logger = logging.getLogger("api.roadmap")


class RoadmapService:
    @staticmethod
    def get_roadmap(user_email: str or None):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_roadmap = {}

                node_query = text(RoadmapUtil.get_roadmap_node())
                node_result = s.execute(node_query)
                node_info = [dict(row) for row in node_result.mappings()]
                user_roadmap["node_info"] = node_info

                edge_info = s.query(RoadmapEdge).all()

                user_roadmap["edge_info"] = edge_info

                if user_email is not None:
                    user_quest_list = (
                        s.query(UserRoadmap)
                        .filter(UserRoadmap.user_email == user_email)
                        .first()
                    )
                    if user_quest_list is not None:
                        user_roadmap["quest_list"] = user_quest_list.quest_list
                    else:
                        user_roadmap["quest_list"] = []
                    return user_roadmap
                else:
                    user_roadmap["quest_list"] = []
                    return user_roadmap
        except Exception as e:
            logger.error(
                f"get_roadmap error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def save_roadmap(questList: List[str], user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_roadmap = (
                    s.query(UserRoadmap).filter_by(user_email=user_email).first()
                )
                utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
                kst = pytz.timezone("Asia/Seoul")
                kst_now = utc_now.astimezone(kst)

                if user_roadmap:
                    user_roadmap.quest_list = questList
                    user_roadmap.update_time = kst_now
                    s.commit()
                else:
                    new_user_roadmap = UserRoadmap(
                        user_email=user_email, quest_list=questList, update_time=kst_now
                    )
                    s.add(new_user_roadmap)
                    s.commit()
                return questList
        except Exception as e:
            logger.error(
                f"save_roadmap: {questList}, error: {e}",
                exc_info=True,
            )
            return None
