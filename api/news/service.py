from database import DataBaseConnector
from sqlalchemy import desc

class NewsService:

    @staticmethod
    def get_wipe():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                wipe = s.query(Wipe).order_by(desc(Wipe.season_start)).all()
                return wipe
        except Exception as e:
            print("오류 발생:", e)
            return None
