from sqlalchemy.orm import subqueryload
from api.quest.models import NPC
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


