from api.user.models import (
    User,
    AddUserReq,
    UserQuest,
    UserQuestUpdate,
    UserQuestSuccess,
)
from database import DataBaseConnector
from dotenv import load_dotenv
import os
import uuid
from sqlalchemy import text


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
                    )
                    s.add(new_user)
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
                query = text(
                    """
                    select tkl_npc.id                                             as npc_id,
                           tkl_npc.name_kr                                        as npc_name_kr,
                           tkl_npc.name_en                                        as npc_name_en,
                           tkl_npc.image                                          as npc_image,
                           jsonb_agg(jsonb_build_object('quest_id', rq, 'quest_name_en', tkl_quest.name_en, 'quest_name_kr',
                                                        tkl_quest.name_kr, 'objectives_kr', tkl_quest.objectives_kr, 'objectives_en',
                                                        tkl_quest.objectives_en, 'next', COALESCE(tkl_quest.next, jsonb '[]'::jsonb))) as quest_info
                    from tkl_user_quest
                             left join lateral unnest(tkl_user_quest.quest_id) AS rq ON true
                             left join tkl_quest on rq = tkl_quest.id
                             left join tkl_npc on tkl_quest.npc_value = tkl_npc.id
                    WHERE tkl_user_quest.user_email = :user_email
                    group by tkl_npc.id, tkl_npc.name_kr, tkl_npc.name_en
                    order by tkl_npc.id
                    """
                )
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
                if user_quest:
                    user_quest.quest_id = userQuestAdd.quest_list
                else:
                    new_data = UserQuest(
                        user_email=user_email, quest_id=userQuestAdd.quest_list
                    )
                    s.add(new_data)

                s.commit()
                return True
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def success_user_quest(userQuestSuccess: UserQuestSuccess, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_quest = s.query(UserQuest).filter_by(user_email=user_email).first()
                user_quest.quest_id = userQuestSuccess.userQuestList
                s.commit()
                query = text(
                    """
                    select tkl_npc.id                                             as npc_id,
                           tkl_npc.name_kr                                        as npc_name_kr,
                           tkl_npc.name_en                                        as npc_name_en,
                           tkl_npc.image                                          as npc_image,
                           jsonb_agg(jsonb_build_object('quest_id', rq, 'quest_name_en', tkl_quest.name_en, 'quest_name_kr',
                                                        tkl_quest.name_kr, 'objectives_kr', tkl_quest.objectives_kr, 'objectives_en',
                                                        tkl_quest.objectives_en, 'next', COALESCE(tkl_quest.next, jsonb '[]'::jsonb))) as quest_info
                    from tkl_user_quest
                             left join lateral unnest(tkl_user_quest.quest_id) AS rq ON true
                             left join tkl_quest on rq = tkl_quest.id
                             left join tkl_npc on tkl_quest.npc_value = tkl_npc.id
                    WHERE tkl_user_quest.user_email = :user_email
                    group by tkl_npc.id, tkl_npc.name_kr, tkl_npc.name_en
                    order by tkl_npc.id
                    """
                )
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
