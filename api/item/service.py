from api.item.models import Headset
from database import DataBaseConnector


class ItemService:

    @staticmethod
    def get_all_headset():
        """
        headset 전체 조회
        """
        try:
            session = DataBaseConnector.create_session()
            headset = (session.query(Headset).order_by(Headset.name).all())
            session.close()
            return headset
        except Exception as e:
            print("오류 발생:", e)
            return None