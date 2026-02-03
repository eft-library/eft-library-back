from sqlalchemy import text
from api.boss.models import Boss
from api.boss.util import BossUtil
from database import DataBaseConnector
import logging

logger = logging.getLogger("api.boss")


class BossService:

    @staticmethod
    def get_boss_by_id(url_mapping: str):
        """
        특정 boss id 조회
        """
        try:
            with DataBaseConnector.SessionLocal() as s:
                query = text(BossUtil.get_boss_query())
                param = {"url_mapping": url_mapping}
                result = s.execute(query, param)
                boss_data = [dict(row) for row in result.mappings()]

                boss_selector = (
                    s.query(Boss.url_mapping, Boss.name)
                    .filter(Boss.is_boss.is_(True))
                    .order_by(Boss.order)
                    .all()
                )

                boss_selector_list = [
                    {"url_mapping": url_mapping, "name": name}
                    for url_mapping, name in boss_selector
                ]

                return {"boss": boss_data[0], "boss_selector": boss_selector_list}

        except Exception as e:
            logger.error(
                f"get_boss_by_id: {url_mapping}, error: {e}",
                exc_info=True,
            )
            return None
