from sqlalchemy import text
from api.boss.models import Boss
from api.boss.util import BossUtil
from api.boss.query import BossQuery
from database import DataBaseConnector, V3Database
import logging

logger = logging.getLogger("api.boss")


class BossService:
    # TODO: 삭제 예정
    @staticmethod
    def get_boss_by_id(url_mapping: str):
        """
        특정 boss id 조회
        """
        try:
            with DataBaseConnector.SessionLocal() as s:
                query = text(BossUtil.get_boss_query())
                param = {"url_mapping": url_mapping}
                result = s.execute(query, param)
                boss_data = [dict(row) for row in result.mappings()]

                boss_selector = (
                    s.query(Boss.url_mapping, Boss.name)
                    .filter(Boss.is_boss.is_(True))
                    .order_by(Boss.order)
                    .all()
                )

                boss_selector_list = [
                    {"url_mapping": url_mapping, "name": name}
                    for url_mapping, name in boss_selector
                ]

                return {"boss": boss_data[0], "boss_selector": boss_selector_list}

        except Exception as e:
            logger.error(
                f"get_boss_by_id: {url_mapping}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_boss_by_normalized_name(normalized_name: str):
        try:
            with V3Database.SessionLocal() as s:
                boss_id_sql = text(BossQuery.boss_id_sql())
                boss_info_sql = text(BossQuery.boss_info_sql())
                boss_map_sql = text(BossQuery.boss_map_sql())
                boss_item_sql = text(BossQuery.boss_item_sql())
                boss_follower_sql = text(BossQuery.boss_follower_sql())
                boss_follower_info_sql = text(BossQuery.boss_follower_info_sql())
                boss_selector_sql = text(BossQuery.boss_selector_sql())

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

                    boss_follower_item_sql = text(BossQuery.boss_follower_item_sql())
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
                f"get_boss_by_normalized_name: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None
