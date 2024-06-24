from api.news.models import Youtube
from database import DataBaseConnector


class NewsService:
    @staticmethod
    def get_youtube():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                youtube = s.query(Youtube).one()
                return youtube
        except Exception as e:
            print("오류 발생:", e)
            return None
