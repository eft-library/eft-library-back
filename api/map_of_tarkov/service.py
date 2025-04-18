from sqlalchemy.orm import subqueryload

from api.boss.models import Boss
from api.map.models import ParentMap
from api.map_of_tarkov.models import Extraction, Transits, WhereAmI
from database import DataBaseConnector
import os
from dotenv import load_dotenv


class MapOfTarkovService:
    @staticmethod
    def get_map_of_tarkov(map_id):
        """
        map of tarkov 지도 조회
        """
        try:
            load_dotenv()
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                boss_list = (
                    s.query(Boss)
                    .filter(Boss.spawn.contains([map_id]))
                    .order_by(Boss.order)
                    .all()
                )
                map_info = (
                    s.query(ParentMap)
                    .options(subqueryload(ParentMap.sub))
                    .filter(ParentMap.id == map_id)
                ).first()
                extraction_info = (
                    s.query(Extraction)
                    .filter(Extraction.map == map_id)
                    .order_by(Extraction.faction, Extraction.name)
                    .all()
                )
                transits_info = (
                    s.query(Transits)
                    .filter(Transits.map == map_id)
                    .order_by(Transits.faction, Transits.name)
                    .all()
                )

            updated_boss_list = []
            for boss in boss_list:
                updated_boss_list.append(boss)

            # 각각의 Boss 객체를 딕셔너리로 변환
            combined_info = [boss.__dict__ for boss in updated_boss_list]

            map_of_tarkov = {
                "boss_list": combined_info,
                "map_info": map_info,
                "extraction_info": extraction_info,
                "transits_info": transits_info,
                "map_id": map_id,
            }

            return map_of_tarkov
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_map_of_tarkov():
        try:
            load_dotenv()
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 모든 지도 정보와 관련 데이터를 한번에 가져오기
                maps = s.query(ParentMap).options(subqueryload(ParentMap.sub)).all()
                bosses = s.query(Boss).all()
                extractions = s.query(Extraction).all()
                transits = s.query(Transits).all()
                finds = s.query(WhereAmI).all()

            # 지도 ID를 기준으로 데이터 분류
            boss_dict = {}
            for boss in bosses:
                for spawn_map_id in boss.spawn:  # Boss.spawn이 리스트라고 가정
                    boss_dict.setdefault(spawn_map_id, []).append(boss)

            extraction_dict = {}
            for extraction in extractions:
                extraction_dict.setdefault(extraction.map, []).append(extraction)

            transits_dict = {}
            for transit in transits:
                transits_dict.setdefault(transit.map, []).append(transit)

            find_dict = {}
            for find in finds:
                find_dict.setdefault(find.id, []).append(find)

            # 최종 결과 구성
            result = []
            for map_info in maps:
                map_id = map_info.id

                updated_boss_list = []
                for boss in boss_dict.get(map_id, []):
                    updated_boss_list.append(boss.__dict__)

                map_of_tarkov = {
                    "boss_list": updated_boss_list,
                    "map_info": map_info,
                    "extraction_info": extraction_dict.get(map_id, []),
                    "transits_info": transits_dict.get(map_id, []),
                    "map_id": map_id,
                    "find_info": find_dict.get(map_id, [])
                }

                result.append(map_of_tarkov)

            return result
        except Exception as e:
            print("오류 발생:", e)
            return None
