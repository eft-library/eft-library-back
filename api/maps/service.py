from .models import ThreeMap, JpgMap
from database import DataBaseConnector
from contextlib import contextmanager
import copy


class MapService:
    @staticmethod
    @contextmanager
    def session_scope():
        session = DataBaseConnector.create_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def get_three_map(map_id: str):
        with MapService.session_scope() as session:
            three_map = session.query(ThreeMap).filter(ThreeMap.three_map_id == map_id).first()
            return copy.deepcopy(three_map)

    @staticmethod
    def get_all_three_map():
        with MapService.session_scope() as session:
            three_maps = session.query(ThreeMap).all()
            return copy.deepcopy(three_maps)

    @staticmethod
    def get_jpg_map(map_id: str):
        with MapService.session_scope() as session:
            jpg_map = session.query(JpgMap).filter(JpgMap.jpg_map_id == map_id).first()
            return copy.deepcopy(jpg_map)

    @staticmethod
    def get_all_jpg_map():
        with MapService.session_scope() as session:
            jpg_maps = session.query(JpgMap).all()
            return copy.deepcopy(jpg_maps)
