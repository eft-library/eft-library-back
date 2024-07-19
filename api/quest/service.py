from api.quest.models import NPC, QuestPreview
from database import DataBaseConnector
import os
from dotenv import load_dotenv
from sqlalchemy.orm import subqueryload


class QuestService:
    @staticmethod
    def get_all_npc():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                npc_list = s.query(NPC).order_by(NPC.order).all()
                return npc_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_quest_preview():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                quest_list = (
                    s.query(QuestPreview)
                    .order_by(QuestPreview.order)
                    .filter(QuestPreview.is_event == False)
                    .all()
                )
                return quest_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_quest_by_id(quest_id):
        try:
            load_dotenv()
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                quest_npc = (
                    s.query(QuestPreview, NPC)
                    .options(subqueryload(QuestPreview.sub))
                    .filter(QuestPreview.npc_value == NPC.id)
                    .filter(QuestPreview.id == quest_id)
                    .first()
                )

            if quest_npc[0].guide is not None:
                quest_npc[0].guide = quest_npc[0].guide.replace(
                    "/tkl_quest", os.getenv("NAS_DATA") + "/tkl_quest"
                )
            combined_info = {**quest_npc[0].__dict__, **quest_npc[1].__dict__}

            return combined_info
        except Exception as e:
            print("오류 발생:", e)
            return None
