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