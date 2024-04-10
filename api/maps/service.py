from .models import ThreeMapModel
from database import DataBaseConnector


class MapService:
    @staticmethod
    def get_three_map(map_id: str):
        session = DataBaseConnector.create_session()
        three_map = session.query(ThreeMapModel).filter(ThreeMapModel.three_map_id == map_id).first()
        print(three_map)
        session.close()
        return three_map
