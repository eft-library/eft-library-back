from api.user.models import (
    User,
    AddUserReq,
    UserQuest,
    UserQuestUpdate,
    UserQuestDelete,
)
from database import DataBaseConnector
from dotenv import load_dotenv
import os
import uuid
from sqlalchemy import text
from api.user.util import UserUtil
from datetime import datetime


load_dotenv()


class UserService:
    @staticmethod
    def add_new_user(addUserReq: AddUserReq):
        try:
            uuid_v5 = f"{os.getenv('UUID_NAME')}-{uuid.uuid5(uuid.NAMESPACE_DNS, addUserReq.email)}"
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 이미 존재하는 사용자인지 확인
                check_user = (
                    s.query(User).filter(User.email == addUserReq.email).first()
                )

                if check_user:
                    return True
                else:
                    new_user = User(
                        id=addUserReq.id,
                        name=addUserReq.name,
                        email=addUserReq.email,
                        image=addUserReq.image,
                        nick_name=uuid_v5,
                        point=0,
                        is_ban=False,
                        is_delete=False,
                        grade="뉴비",
                        create_time=datetime.now(),
                        update_time=None,
                        delete_time=None,
                    )
                    s.add(new_user)
                    new_user_quest = UserQuest(
                        user_email=addUserReq.email,
                        quest_id=[],
                    )
                    s.add(new_user_quest)
                    s.commit()
                    return True
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_user_quest(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(UserUtil.user_quest_query())
                result = s.execute(query, {"user_email": user_email})
                user_quests = []
                for row in result:
                    quest_dict = {
                        "npc_id": row[0],
                        "npc_name_kr": row[1],
                        "npc_name_en": row[2],
                        "npc_image": row[3],
                        "quest_info": row[4],
                    }
                    user_quests.append(quest_dict)

                return user_quests
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def update_user_quest(userQuestAdd: UserQuestUpdate, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_quest = s.query(UserQuest).filter_by(user_email=user_email).first()
                user_quest.quest_id = userQuestAdd.userQuestList
                s.commit()
                query = text(UserUtil.user_quest_query())

                result = s.execute(query, {"user_email": user_email})
                new_user_quests = []
                for row in result:
                    quest_dict = {
                        "npc_id": row[0],
                        "npc_name_kr": row[1],
                        "npc_name_en": row[2],
                        "npc_image": row[3],
                        "quest_info": row[4],
                    }
                    new_user_quests.append(quest_dict)

                return new_user_quests
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def delete_user_quest(userQuestDelete: UserQuestDelete, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_quest = s.query(UserQuest).filter_by(user_email=user_email).first()
                user_quest.quest_id = userQuestDelete.userQuestList
                s.commit()
                query = text(UserUtil.user_quest_query())
                result = s.execute(query, {"user_email": user_email})
                new_user_quests = []
                for row in result:
                    quest_dict = {
                        "npc_id": row[0],
                        "npc_name_kr": row[1],
                        "npc_name_en": row[2],
                        "npc_image": row[3],
                        "quest_info": row[4],
                    }
                    new_user_quests.append(quest_dict)

                return new_user_quests
        except Exception as e:
            print("오류 발생:", e)
            return None
