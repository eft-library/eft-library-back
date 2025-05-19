from sqlalchemy import text

from api.quest.models import NPC, Quest
from api.quest.util import QuestUtil
from database import DataBaseConnector


class QuestService:
    @staticmethod
    def get_npc_selector():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                npc_list = (
                    s.query(NPC.id, NPC.name, NPC.image).order_by(NPC.order).all()
                )

                return [
                    {"id": id_, "name": name, "image": image}
                    for id_, name, image in npc_list
                ]
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_quest():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(QuestUtil.get_all_quest_query())
                result = s.execute(query)
                quest_list = [dict(row) for row in result.mappings()]
                return quest_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_quest_detail():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(QuestUtil.get_all_quest_detail_query())
                result = s.execute(query)
                quest_list = [dict(row) for row in result.mappings()]
                return quest_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_quest_by_id(url_mapping):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(QuestUtil.get_quest_detail_query())
                param = {"url_mapping": url_mapping}
                result = s.execute(query, param)
                quest = [dict(row) for row in result.mappings()]

            return quest[0]
        except Exception as e:
            print("오류 발생:", e)
            return None
