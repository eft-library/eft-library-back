from typing import List
from datetime import datetime
from api.quest.models import NPC
from sqlalchemy.orm import subqueryload
from api.roadmap.roadmap_res_models import UserRoadmap, RoadmapNode, RoadmapEdge
from database import DataBaseConnector


class RoadmapService:
    @staticmethod
    def get_roadmap(user_email: str or None):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_roadmap = {}
                node_info = (
                    s.query(NPC)
                    .order_by(NPC.order)
                    .options(subqueryload(NPC.all_quest))
                    .all()
                )
                user_roadmap["node_info"] = node_info

                edge_info = (
                    s.query(RoadmapEdge).all()
                )

                user_roadmap['edge_info'] = edge_info

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
            print("오류 발생:", e)
            return None

    @staticmethod
    def save_roadmap(questList: List[str], user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_roadmap = s.query(UserRoadmap).filter_by(user_email=user_email).first()
                if user_roadmap:
                    user_roadmap.quest_list = questList
                    user_roadmap.update_time = datetime.utcnow()
                    s.commit()
                else:
                    new_user_roadmap = UserRoadmap(
                        user_email=user_email,
                        quest_list=questList,
                        update_time=datetime.utcnow()
                    )
                    s.add(new_user_roadmap)
                return questList
        except Exception as e:
            print("오류 발생:", e)
            return None
