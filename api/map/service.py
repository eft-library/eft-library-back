from api.map.models import ThreeMap, JpgMap
from api.session_scope import SessionManger
import copy


class MapService:
    @staticmethod
    def get_three_map(map_id: str):
        """
        ID를 통한 3d map 조회
        """
        with SessionManger.session_scope() as session:
            three_map = session.query(ThreeMap).filter(ThreeMap.three_map_id == map_id).first()
            return copy.deepcopy(three_map)

    @staticmethod
    def get_all_three_map():
        """
        3d map 전체 조회
        """
        with SessionManger.session_scope() as session:
            three_maps = session.query(ThreeMap).all()
            return copy.deepcopy(three_maps)

    @staticmethod
    def get_jpg_map(map_id: str):
        """
        ID를 통한 2d map 조회
        """
        with SessionManger.session_scope() as session:
            jpg_map = session.query(JpgMap).filter(JpgMap.jpg_map_id == map_id).first()
            return copy.deepcopy(jpg_map)

    @staticmethod
    def get_all_jpg_map():
        """
        2d map 전체 조회
        """
        with SessionManger.session_scope() as session:
            jpg_maps = session.query(JpgMap).all()
            return copy.deepcopy(jpg_maps)
