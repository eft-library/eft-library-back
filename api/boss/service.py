from api.boss.models import Boss
from database import DataBaseConnector


class BossService:
    @staticmethod
    def get_all_boss():
        """
        boss 전체 조회
        """
        try:
            session = DataBaseConnector.create_session()
            boss_list = session.query(Boss).all()
            session.close()
            return boss_list
        except Exception as e:
            print("오류 발생:", e)
            return None
