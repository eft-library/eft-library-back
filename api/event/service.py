from api.quest.models import NPC, QuestPreview
from api.event.models import Event
from database import DataBaseConnector
import os
from dotenv import load_dotenv
from sqlalchemy.orm import subqueryload


class EventService:
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
    def get_all_event():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                event_list = s.query(Event).order_by(Event.update_time).all()
                return event_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_event_by_id(event_id):
        try:
            load_dotenv()
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                quest_npc = (
                    s.query(Event, NPC)
                    .filter(Event.npc_value == NPC.id)
                    .filter(Event.id == event_id)
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
