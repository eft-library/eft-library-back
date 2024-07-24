from api.user.user_res_models import (
    User,
    UserQuest,
)
from api.user.user_req_models import (
    AddUserReq,
    UserQuestUpdate,
    UserQuestDelete,
)
from database import DataBaseConnector
from dotenv import load_dotenv
import os
import uuid
from sqlalchemy import text
from api.user.util import UserUtil
from datetime import datetime, timedelta
import pytz

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
                        image="/tkl_user/icon/newbie.gif",
                        image_list=["/tkl_user/icon/newbie.gif"],
                        nick_name=uuid_v5[:10],
                        point=0,
                        is_ban=False,
                        is_delete=False,
                        grade="뉴비",
                        create_time=datetime.now(),
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

    @staticmethod
    def get_user(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = s.query(User).filter(User.email == user_email).first()
                return user
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def change_user_nickname(new_nickname: str, user_email: str):
        """
        요건 적합 : return user
        30일 안지남 : return 2
        중복 : return 3
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = s.query(User).filter(User.email == user_email).first()

                # 수정 시간이 30일이 지났는지 확인
                thirty_days_ago = datetime.now(pytz.UTC) - timedelta(days=30)

                if (
                    user.update_time is None
                    or user.update_time.replace(tzinfo=pytz.UTC) < thirty_days_ago
                ):
                    # 30일 지났거나 변경한 적 없음
                    nickname_duplicate = (
                        s.query(User).filter(User.nick_name == new_nickname).first()
                    )
                    if nickname_duplicate:
                        # 중복
                        return 3
                    else:
                        user.nick_name = new_nickname
                        user.update_time = datetime.now()
                        s.commit()

                        change_user = (
                            s.query(User).filter(User.email == user_email).first()
                        )
                        return change_user
                else:
                    # 30일 안 되었음
                    return 2
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def change_user_icon(new_icon: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = s.query(User).filter(User.email == user_email).first()
                user.image = new_icon
                s.commit()

                new_user = s.query(User).filter(User.email == user_email).first()
                return new_user
        except Exception as e:
            print("오류 발생:", e)
            return None
