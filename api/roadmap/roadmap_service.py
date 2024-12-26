from api.quest.models import NPC, QuestPreview
from sqlalchemy.orm import subqueryload
from api.roadmap.roadmap_res_models import UserRoadmap
from database import DataBaseConnector


class RoadmapService:
    @staticmethod
    def get_roadmap(user_email: str):
        # 여기에서 퀘스트만 전체 조회
        # 밑의 조건에서 사용자 quest list 조회 후 반환
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_roadmap = {}
                quest_info = (
                    s.query(NPC)
                    .order_by(NPC.order)
                    .options(subqueryload(NPC.all_quest))
                    .all()
                )
                user_roadmap["quest_info"] = quest_info

                if user_email is not None:
                    user_quest_list = (
                        s.query(UserRoadmap)
                        .filter(UserRoadmap.user_email == user_email)
                        .first()
                    )
                    user_roadmap["quest_list"] = user_quest_list
                    return user_roadmap
                else:
                    user_roadmap["quest_list"] = []
                    return user_roadmap
        except Exception as e:
            print("오류 발생:", e)
            return None
