import logging
from collections import defaultdict

from sqlalchemy import text

from api.battle_pass.query import BattlePassQueryV3
from database import V3Database

logger = logging.getLogger("api.battle_pass")


class BattlePassServiceV3:
    @staticmethod
    def _serialize_season_v3(season: dict):
        return {
            "id": season["id"],
            "code": season["code"],
            "title_en": season["title_en"],
            "title_ko": season["title_ko"],
            "title_ja": season["title_ja"],
            "description_en": season["description_en"],
            "description_ko": season["description_ko"],
            "description_ja": season["description_ja"],
            "page_count": season["page_count"],
            "start_time": season["start_time"],
            "end_time": season["end_time"],
            "is_active": season.get("is_active", True),
            "sort_order": season["sort_order"],
            "update_time": season["update_time"],
        }

    @staticmethod
    def _serialize_document_v3(document: dict):
        return {
            "id": document["id"],
            "name_en": document["name_en"],
            "name_ko": document["name_ko"],
            "name_ja": document["name_ja"],
            "image": document["image"],
            "document_role": document["document_role"],
            "sort_order": document["sort_order"],
        }

    @staticmethod
    def _build_detail_v3(session, season: dict):
        season_id = season["id"]
        documents = [
            dict(row)
            for row in session.execute(
                text(BattlePassQueryV3.documents_by_season_sql()),
                {"season_id": season_id},
            ).mappings()
        ]
        rewards = [
            dict(row)
            for row in session.execute(
                text(BattlePassQueryV3.rewards_by_season_sql()),
                {"season_id": season_id},
            ).mappings()
        ]
        requirements = session.execute(
            text(BattlePassQueryV3.requirements_by_season_sql()),
            {"season_id": season_id},
        ).mappings()

        requirements_by_reward_id = defaultdict(list)
        for requirement in requirements:
            requirements_by_reward_id[requirement["reward_id"]].append(
                {
                    "quantity": requirement["quantity"],
                    "sort_order": requirement["sort_order"],
                    "document": {
                        "id": requirement["document_id"],
                        "name_en": requirement["document_name_en"],
                        "name_ko": requirement["document_name_ko"],
                        "name_ja": requirement["document_name_ja"],
                        "image": requirement["document_image"],
                        "document_role": requirement["document_role"],
                    },
                }
            )

        rewards_by_page = defaultdict(list)
        for reward in rewards:
            rewards_by_page[reward["page_number"]].append(
                {
                    "id": reward["id"],
                    "reward_type": reward["reward_type"],
                    "name_en": reward["name_en"],
                    "name_ko": reward["name_ko"],
                    "name_ja": reward["name_ja"],
                    "image": reward["image"],
                    "reward_quantity": reward["reward_quantity"],
                    "document_price": reward["document_price"],
                    "sort_order": reward["sort_order"],
                    "requirements": requirements_by_reward_id.get(
                        reward["id"], []
                    ),
                }
            )

        highest_page = max(rewards_by_page, default=0)
        page_count = max(season["page_count"] or 0, highest_page)
        pages = [
            {
                "page_number": page_number,
                "rewards": rewards_by_page.get(page_number, []),
            }
            for page_number in range(1, page_count + 1)
        ]

        return {
            "season": BattlePassServiceV3._serialize_season_v3(season),
            "documents": [
                BattlePassServiceV3._serialize_document_v3(document)
                for document in documents
            ],
            "pages": pages,
        }

    @staticmethod
    def get_active_battle_pass_v3():
        try:
            with V3Database.SessionLocal() as session:
                season = session.execute(
                    text(BattlePassQueryV3.active_season_sql())
                ).mappings().first()
                if season is None:
                    return None
                return BattlePassServiceV3._build_detail_v3(
                    session, dict(season)
                )
        except Exception as error:
            logger.error(
                f"get_active_battle_pass_v3 error: {error}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_battle_pass_by_code_v3(season_code: str):
        try:
            with V3Database.SessionLocal() as session:
                season = session.execute(
                    text(BattlePassQueryV3.season_by_code_sql()),
                    {"season_code": season_code},
                ).mappings().first()
                if season is None:
                    return None
                return BattlePassServiceV3._build_detail_v3(
                    session, dict(season)
                )
        except Exception as error:
            logger.error(
                f"get_battle_pass_by_code_v3({season_code!r}) error: {error}",
                exc_info=True,
            )
            return None
