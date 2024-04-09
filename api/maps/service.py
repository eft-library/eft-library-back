from api.maps.models import ThreeMap
from database import DataBaseConnector


class MapService:
    @staticmethod
    def get_three_map(map_id: str):
        session = DataBaseConnector.create_session()
        three_map = session.query(ThreeMap).filter(ThreeMap.three_map_id == map_id).all()
        print(three_map)
        session.close()
        return three_map
