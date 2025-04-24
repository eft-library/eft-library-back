from api.quest.models import NPC, Quest
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
                quest_list = s.query(Quest).order_by(Quest.order).all()
                return quest_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_quest_by_id(url_mapping):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                quest_npc = (
                    s.query(Quest, NPC)
                    .filter(Quest.npc_value == NPC.id)
                    .filter(Quest.url_mapping == url_mapping)
                    .first()
                )
            combined_info = {**quest_npc[0].__dict__, **quest_npc[1].__dict__}

            return combined_info
        except Exception as e:
            print("오류 발생:", e)
            return None
