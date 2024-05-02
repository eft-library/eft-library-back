from api.quest.models import NPC, QuestPreview
from database import DataBaseConnector


class QuestService:
    @staticmethod
    def get_all_npc():
        session = DataBaseConnector.create_session()
        npc_list = (session
                    .query(NPC)
                    .order_by(NPC.npc_order).all())
        session.close()
        return npc_list

    @staticmethod
    def get_all_quest_preview():
        session = DataBaseConnector.create_session()
        quest_list = (session
                      .query(QuestPreview)
                      .order_by(QuestPreview.quest_order).all())
        session.close()
        return quest_list

    @staticmethod
    def get_quest_by_id(quest_id):
        session = DataBaseConnector.create_session()
        quest_npc_info = (session
                 .query(QuestPreview, NPC)
                 .filter(QuestPreview.quest_npc_value == NPC.npc_id)
                 .filter(QuestPreview.quest_id == quest_id)
                 .first())
        combined_info = {**quest_npc_info[0].__dict__, **quest_npc_info[1].__dict__}
        session.close()
        return combined_info
