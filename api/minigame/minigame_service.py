from api.minigame.res_models import ItemFleaSummary
from database import DataBaseConnector


class MinigameService:

    @staticmethod
    def get_rng_item_list():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                rng_item_list = s.query(ItemFleaSummary).all()
                return rng_item_list
        except Exception as e:
            print("오류 발생:", e)
            return None
