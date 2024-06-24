from sqlalchemy.orm import subqueryload

from api.boss.models import Boss
from api.map.models import ParentMap
from api.map_of_tarkov.models import Extraction
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
                boss_list = s.query(Boss).filter(Boss.spawn.contains([map_id])).all()
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

            updated_boss_list = []
            for boss in boss_list:
                if boss.location_guide is not None:
                    boss.location_guide = boss.location_guide.replace(
                        "/tkw_quest", os.getenv("NAS_DATA") + "/tkw_quest"
                    )
                updated_boss_list.append(boss)

            # 각각의 Boss 객체를 딕셔너리로 변환
            combined_info = [boss.__dict__ for boss in updated_boss_list]

            map_of_tarkov = {
                "boss_list": combined_info,
                "map_info": map_info,
                "extraction_info": extraction_info,
            }

            return map_of_tarkov
        except Exception as e:
            print("오류 발생:", e)
            return None
