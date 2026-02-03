from sqlalchemy import text
from api.quest.models import NPC
from api.quest.util import QuestUtil
from database import DataBaseConnector
import logging

logger = logging.getLogger("api.quest")


class QuestService:
    @staticmethod
    def get_npc_selector():
        try:

            with DataBaseConnector.SessionLocal() as s:
                npc_list = (
                    s.query(NPC.id, NPC.name, NPC.image)
                    .filter(NPC.order != None)
                    .order_by(NPC.order)
                    .all()
                )

                return [
                    {"id": id_, "name": name, "image": image}
                    for id_, name, image in npc_list
                ]
        except Exception as e:
            logger.error(
                f"get_npc_selector error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_all_quest():
        try:

            with DataBaseConnector.SessionLocal() as s:
                query = text(QuestUtil.get_all_quest_query())
                result = s.execute(query)
                quest_list = [dict(row) for row in result.mappings()]
                return quest_list
        except Exception as e:
            logger.error(
                f"get_all_quest  error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_all_quest_detail():
        try:

            with DataBaseConnector.SessionLocal() as s:
                query = text(QuestUtil.get_all_quest_detail_query())
                result = s.execute(query)
                quest_list = [dict(row) for row in result.mappings()]
                return quest_list
        except Exception as e:
            logger.error(
                f"get_all_quest_detail  error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_quest_by_id(url_mapping):
        try:

            with DataBaseConnector.SessionLocal() as s:
                query = text(QuestUtil.get_quest_detail_query())
                param = {"url_mapping": url_mapping}
                result = s.execute(query, param)
                quest = [dict(row) for row in result.mappings()]

            return quest[0]
        except Exception as e:
            logger.error(
                f"get_quest_by_id: {url_mapping}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_quest_by_npc(npc_id):
        try:

            with DataBaseConnector.SessionLocal() as s:
                query = text(QuestUtil.get_quest_by_npc())
                param = {"npc_id": npc_id}
                result = s.execute(query, param)
                quest_list = [dict(row) for row in result.mappings()]

            return quest_list
        except Exception as e:
            logger.error(
                f"get_quest_by_npc: {npc_id}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_quest_with_trader(trader_id):
        try:

            with DataBaseConnector.SessionLocal() as s:
                info = {}
                query = text(QuestUtil.get_quest_by_npc())
                param = {"npc_id": trader_id}
                quest_list = s.execute(query, param)
                npc_list = (
                    s.query(NPC.id, NPC.name, NPC.image)
                    .filter(NPC.order != None)
                    .order_by(NPC.order)
                    .all()
                )
                info["quest_list"] = [dict(row) for row in quest_list.mappings()]
                info["trader_list"] = [
                    {"id": id_, "name": name, "image": image}
                    for id_, name, image in npc_list
                ]

            return info
        except Exception as e:
            logger.error(
                f"get_quest_with_trader: {trader_id}, error: {e}",
                exc_info=True,
            )
            return None
