from api.news.models import News, Popup
from database import DataBaseConnector


class NewsService:
    @staticmethod
    def get_news():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                news = s.query(News).one()
                return news
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_popup():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                popup = s.query(Popup).one()
                return popup
        except Exception as e:
            print("오류 발생:", e)
            return None
