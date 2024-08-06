from api.user.user_res_models import (
    UserQuest,
)
from api.user.user_req_models import (
    UserQuestList,
)
from database import DataBaseConnector
from dotenv import load_dotenv
from sqlalchemy import text
from api.user.util import UserUtil

load_dotenv()


class UserQuestService:
    @staticmethod
    def get_user_quest(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(UserUtil.user_quest_query())
                result = s.execute(query, {"user_email": user_email})
                user_quests = [dict(row) for row in result.mappings()]
                return user_quests
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def update_user_quest(userQuestList: UserQuestList, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_quest = s.query(UserQuest).filter_by(user_email=user_email).first()
                user_quest.quest_id = userQuestList.userQuestList
                s.commit()
                query = text(UserUtil.user_quest_query())

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
                user_quest.quest_id = userQuestList.userQuestList
                s.commit()
                query = text(UserUtil.user_quest_query())
                result = s.execute(query, {"user_email": user_email})
                new_user_quests = [dict(row) for row in result.mappings()]
                return new_user_quests
        except Exception as e:
            print("오류 발생:", e)
            return None
