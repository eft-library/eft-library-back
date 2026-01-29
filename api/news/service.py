from api.news.models import Wipe
from database import DataBaseConnector
from sqlalchemy import desc

import logging

logger = logging.getLogger("api.wipe")


class NewsService:

    @staticmethod
    def get_wipe():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                wipe = s.query(Wipe).order_by(desc(Wipe.season_start)).all()
                return wipe
        except Exception as e:
            logger.error(
                f"get_wipe error: {e}",
                exc_info=True,
            )
            return None
