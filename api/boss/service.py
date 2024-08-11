from api.boss.models import Boss, Followers
from database import DataBaseConnector
import os
from dotenv import load_dotenv
from sqlalchemy.orm import subqueryload


load_dotenv()


class BossService:
    @staticmethod
    def get_all_boss():
        """
        boss 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                boss_list = (
                    s.query(Boss)
                    .options(
                        subqueryload(Boss.sub_followers).subqueryload(Followers.loot)
                    )
                    .order_by(Boss.order)
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

    @staticmethod
    def get_boss_by_id(boss_id: str):
        """
        특정 boss id 조회
        """
        try:
            priority = {
                "WEAPON": 1,
                "AMMO": 2,
                "HEAD_WEAR": 3,
                "HEADSET": 4,
                "FACE_COVER": 5,
                "GLASSES": 6,
                "ARMOR_VEST": 7,
                "RIG": 8,
                "BACKPACK": 9,
                "MEDICAL": 10,
                "PROVISIONS": 11,
                "KEY": 12,
                "LOOT": 13,
            }

            session = DataBaseConnector.create_session_factory()
            with session() as s:
                boss = (
                    s.query(Boss)
                    .options(
                        subqueryload(Boss.sub_followers).subqueryload(Followers.loot)
                    )
                    .filter(Boss.id == boss_id)
                    .order_by(Boss.order)
                    .first()
                )

                if boss.location_guide is not None:
                    boss.location_guide = boss.location_guide.replace(
                        "/tkl_quest", os.getenv("NAS_DATA") + "/tkl_quest"
                    )
                for follower in boss.sub_followers:
                    follower.loot = sorted(
                        follower.loot, key=lambda x: priority[x.item_type]
                    )

                return boss
        except Exception as e:
            print("오류 발생:", e)
            return None
