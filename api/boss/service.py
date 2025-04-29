from sqlalchemy import text

from api.boss.models import Boss
from api.boss.util import BossUtil
from database import DataBaseConnector


class BossService:

    @staticmethod
    def get_boss_by_id(url_mapping: str):
        """
        특정 boss id 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                boss = (
                    s.query(Boss)
                    .filter(Boss.url_mapping == url_mapping)
                    .order_by(Boss.order)
                    .first()
                )

                return boss
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_boss():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(BossUtil.get_boss_query())
                result = s.execute(query)
                bosses = [dict(row) for row in result.mappings()]

                return bosses
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_boss_selector():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                selector_list = s.query(Boss.id, Boss.name).order_by(Boss.order).all()

                return [{"id": id_, "name": name} for id_, name in selector_list]
        except Exception as e:
            print("오류 발생:", e)
            return None
