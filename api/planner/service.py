from api.planner.planner_res_models import UserQuest
from api.planner.planner_req_models import UserQuestList
from database import DataBaseConnector
from dotenv import load_dotenv
from sqlalchemy import text
from datetime import datetime
from api.planner.util import PlannerUtil
import pytz

load_dotenv()


class PlannerService:
    @staticmethod
    def get_user_quest(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(PlannerUtil.user_quest_query())
                result = s.execute(query, {"user_email": user_email})
                if result:
                    return [dict(row) for row in result.mappings()]
                else:
                    return []
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def update_user_quest(userQuestList: UserQuestList, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_quest = s.query(UserQuest).filter_by(user_email=user_email).first()
                user_quest.quest_list = userQuestList.userQuestList
                utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
                kst = pytz.timezone("Asia/Seoul")
                kst_now = utc_now.astimezone(kst)

                user_quest.update_time = kst_now
                s.commit()
                query = text(PlannerUtil.user_quest_query())

                result = s.execute(query, {"user_email": user_email})
                new_user_quests = [dict(row) for row in result.mappings()]
                return new_user_quests
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def delete_user_quest(userQuestList: UserQuestList, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_quest = s.query(UserQuest).filter_by(user_email=user_email).first()
                user_quest.quest_list = userQuestList.userQuestList
                s.commit()
                query = text(PlannerUtil.user_quest_query())
                result = s.execute(query, {"user_email": user_email})
                new_user_quests = [dict(row) for row in result.mappings()]
                return new_user_quests
        except Exception as e:
            print("오류 발생:", e)
            return None
