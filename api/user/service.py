from api.user.models import User, AddUserReq, UserQuest
from api.quest.models import QuestPreview, NPC
from database import DataBaseConnector
from dotenv import load_dotenv
import os
import uuid


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
                user_quests = (
                    s.query(
                        UserQuest.user_email,
                        UserQuest.quest_id,
                        QuestPreview.npc_value,
                        QuestPreview.title_en,
                        QuestPreview.title_kr,
                        NPC.name_kr,
                        NPC.name_en,
                        UserQuest.is_clear,
                    )
                    .join(QuestPreview, UserQuest.quest_id == QuestPreview.id)
                    .join(NPC, QuestPreview.npc_value == NPC.id)
                    .filter(UserQuest.user_email == user_email)
                    .all()
                )

                results = []
                for row in user_quests:
                    (
                        user_email,
                        quest_id,
                        npc_value,
                        title_en,
                        title_kr,
                        name_kr,
                        name_en,
                        is_clear,
                    ) = row
                    results.append(
                        {
                            "user_email": user_email,
                            "quest_id": quest_id,
                            "npc_value": npc_value,
                            "title_en": title_en,
                            "title_kr": title_kr,
                            "name_kr": name_kr,
                            "name_en": name_en,
                            "is_clear": is_clear,
                        }
                    )

                return results
        except Exception as e:
            print("오류 발생:", e)
            return None
