from sqlalchemy import text
from api.boss.query import BossQueryV3
from database import V3Database
import logging

logger = logging.getLogger("api.boss")


class BossServiceV3:
    @staticmethod
    def get_boss_by_normalized_name_v3(normalized_name: str):
        try:
            with V3Database.SessionLocal() as s:
                boss_id_sql = text(BossQueryV3.boss_id_sql())
                boss_info_sql = text(BossQueryV3.boss_info_sql())
                boss_map_sql = text(BossQueryV3.boss_map_sql())
                boss_item_sql = text(BossQueryV3.boss_item_sql())
                boss_follower_sql = text(BossQueryV3.boss_follower_sql())
                boss_follower_info_sql = text(BossQueryV3.boss_follower_info_sql())
                boss_selector_sql = text(BossQueryV3.boss_selector_sql())

                param = {"normalized_name": normalized_name}
                boss_id = s.execute(boss_id_sql, param).scalar()

                if boss_id is None:
                    return None

                boss_info = s.execute(boss_info_sql, param).mappings().fetchone()
                boss_map = (
                    s.execute(boss_map_sql, {"boss_id": boss_id}).mappings().all()
                )
                boss_item = (
                    s.execute(boss_item_sql, {"boss_id": boss_id}).mappings().all()
                )
                boss_follower = (
                    s.execute(boss_follower_sql, {"boss_id": boss_id}).scalars().all()
                )

                boss_selector = s.execute(boss_selector_sql).mappings().all()

                follower_info = []
                follower_items_by_boss = {}

                if boss_follower:
                    follower_info = (
                        s.execute(boss_follower_info_sql, {"boss_ids": boss_follower})
                        .mappings()
                        .all()
                    )

                    boss_follower_item_sql = text(BossQueryV3.boss_follower_item_sql())
                    boss_follower_items = (
                        s.execute(boss_follower_item_sql, {"boss_ids": boss_follower})
                        .mappings()
                        .all()
                    )

                    for row in boss_follower_items:
                        boss_id_key = row["boss_id"]
                        follower_items_by_boss.setdefault(boss_id_key, []).append(
                            dict(row)
                        )

                followers_item = [
                    {"boss_id": boss_id, "items": items}
                    for boss_id, items in follower_items_by_boss.items()
                ]

                return {
                    "boss": dict(boss_info) if boss_info is not None else None,
                    "spawn": [dict(row) for row in boss_map],
                    "items": [dict(row) for row in boss_item],
                    "followers": [dict(row) for row in follower_info],
                    "followers_item": followers_item,
                    "boss_selector": [dict(row) for row in boss_selector],
                }

        except Exception as e:
            logger.error(
                f"get_boss_by_normalized_name_v3: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None
