from api.boss.models import Boss, Followers
from database import DataBaseConnector
import os
from dotenv import load_dotenv
from sqlalchemy.orm import subqueryload


class BossService:
    @staticmethod
    def get_all_boss():
        """
        boss 전체 조회
        """
        try:
            load_dotenv()
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                boss_list = (
                    s.query(Boss)
                    .options(
                        subqueryload(Boss.sub_followers).subqueryload(Followers.loot)
                    )
                    .all()
                )

            updated_boss_list = []
            for boss in boss_list:
                if boss.location_guide is not None:
                    boss.location_guide = boss.location_guide.replace(
                        "/tkl_quest", os.getenv("NAS_DATA") + "/tkl_quest"
                    )
                updated_boss_list.append(boss)

            # 각각의 Boss 객체를 딕셔너리로 변환
            combined_info = [boss.__dict__ for boss in updated_boss_list]

            return combined_info
        except Exception as e:
            print("오류 발생:", e)
            return None
