from api.news.models import Youtube
from database import DataBaseConnector
import copy


class NewsService:
    @staticmethod
    def get_youtube():
        session = DataBaseConnector.create_session()
        youtube = session.query(Youtube).one()
        session.close()
        return copy.deepcopy(youtube)
        