from api.news.models import Youtube
from api.session_scope import SessionManger
import copy


class NewsService:
    @staticmethod
    def get_youtube():
        with SessionManger.session_scope() as session:
            youtube = session.query(Youtube).one()
            return copy.deepcopy(youtube)
        