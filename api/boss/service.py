from api.boss.models import Boss
from database import DataBaseConnector
import os
from dotenv import load_dotenv


load_dotenv()


class BossService:

    @staticmethod
    def get_boss_by_id(boss_id: str):
        """
        특정 boss id 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                boss = (
                    s.query(Boss)
                    .filter(Boss.id == boss_id)
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
                boss_list = s.query(Boss).order_by(Boss.order).all()

                return boss_list
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
