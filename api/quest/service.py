from api.quest.models import NPC, QuestPreview
from database import DataBaseConnector
import os
from dotenv import load_dotenv


class QuestService:
    @staticmethod
    def get_all_npc():
        session = DataBaseConnector.create_session()
        npc_list = (session
                    .query(NPC)
                    .order_by(NPC.order).all())
        session.close()
        return npc_list

    @staticmethod
    def get_all_quest_preview():
        session = DataBaseConnector.create_session()
        quest_list = (session
                      .query(QuestPreview)
                      .order_by(QuestPreview.order).all())
        session.close()
        return quest_list

    @staticmethod
    def get_quest_by_id(quest_id):
        load_dotenv()
        session = DataBaseConnector.create_session()
        quest_npc = (session
                          .query(QuestPreview, NPC)
                          .filter(QuestPreview.npc_value == NPC.id)
                          .filter(QuestPreview.id == quest_id)
                          .first())

        if quest_npc[0].guide != None:
            quest_npc[0].guide = quest_npc[0].guide.replace("/tkw_quest", os.getenv("NAS_DATA") + "/tkw_quest")
        combined_info = {**quest_npc[0].__dict__, **quest_npc[1].__dict__}
        session.close()
        return combined_info
