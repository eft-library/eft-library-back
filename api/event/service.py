from api.event.models import Event
from database import DataBaseConnector
from sqlalchemy.orm import subqueryload


class EventService:

    @staticmethod
    def get_all_event_quest():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                quest_list = (
                    s.query(Event)
                    .all()
                )
                return quest_list
        except Exception as e:
            print("오류 발생:", e)
            return None
