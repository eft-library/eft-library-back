import logging
from collections import defaultdict

from sqlalchemy import text

from api.prestige.query import PrestigeQueryV3
from database import V3Database

logger = logging.getLogger("api.prestige")


class PrestigeServiceV3:
    @staticmethod
    def _item_v3(row: dict):
        return {
            "id": row["item_id"],
            "normalized_name": row["normalized_name"],
            "name_en": row["name_en"],
            "name_ko": row["name_ko"],
            "name_ja": row["name_ja"],
            "image": row["image"],
        }

    @staticmethod
    def _fetch_v3(session, query: str, prestige_ids: list[str]):
        return [
            dict(row)
            for row in session.execute(
                text(query), {"prestige_ids": prestige_ids}
            ).mappings()
        ]

    @staticmethod
    def _build_levels_v3(session, levels: list[dict]):
        if not levels:
            return []

        prestige_ids = [level["id"] for level in levels]
        conditions = PrestigeServiceV3._fetch_v3(
            session, PrestigeQueryV3.conditions_sql(), prestige_ids
        )
        condition_items = PrestigeServiceV3._fetch_v3(
            session, PrestigeQueryV3.condition_items_sql(), prestige_ids
        )
        condition_statuses = PrestigeServiceV3._fetch_v3(
            session, PrestigeQueryV3.condition_statuses_sql(), prestige_ids
        )
        condition_maps = PrestigeServiceV3._fetch_v3(
            session, PrestigeQueryV3.condition_maps_sql(), prestige_ids
        )
        reward_items = PrestigeServiceV3._fetch_v3(
            session, PrestigeQueryV3.reward_items_sql(), prestige_ids
        )
        reward_skills = PrestigeServiceV3._fetch_v3(
            session, PrestigeQueryV3.reward_skills_sql(), prestige_ids
        )
        customizations = PrestigeServiceV3._fetch_v3(
            session, PrestigeQueryV3.reward_customizations_sql(), prestige_ids
        )
        customization_items = PrestigeServiceV3._fetch_v3(
            session,
            PrestigeQueryV3.reward_customization_items_sql(),
            prestige_ids,
        )
        transfer_settings = PrestigeServiceV3._fetch_v3(
            session, PrestigeQueryV3.transfer_settings_sql(), prestige_ids
        )
        transfer_filters = PrestigeServiceV3._fetch_v3(
            session, PrestigeQueryV3.transfer_filters_sql(), prestige_ids
        )

        condition_items_by_id = defaultdict(list)
        for row in condition_items:
            condition_items_by_id[row["condition_id"]].append(
                PrestigeServiceV3._item_v3(row)
            )
        statuses_by_id = defaultdict(list)
        for row in condition_statuses:
            statuses_by_id[row["condition_id"]].append(row["status"])
        maps_by_id = defaultdict(list)
        for row in condition_maps:
            maps_by_id[row["condition_id"]].append(
                {
                    "id": row["map_id"],
                    "normalized_name": row["normalized_name"],
                    "name_en": row["name_en"],
                    "name_ko": row["name_ko"],
                    "name_ja": row["name_ja"],
                }
            )

        conditions_by_level = defaultdict(list)
        for row in conditions:
            conditions_by_level[row["prestige_id"]].append(
                {
                    "id": row["id"],
                    "type": row["condition_type"],
                    "description_key": row["description_key"],
                    "description_en": row["description_en"],
                    "description_ko": row["description_ko"],
                    "description_ja": row["description_ja"],
                    "count": row["count"],
                    "optional": row["is_optional"],
                    "player_level": row["player_level"],
                    "task": (
                        {
                            "id": row["task_id"],
                            "normalized_name": row["task_normalized_name"],
                            "name_en": row["task_name_en"],
                            "name_ko": row["task_name_ko"],
                            "name_ja": row["task_name_ja"],
                        }
                        if row["task_id"] is not None
                        else None
                    ),
                    "statuses": statuses_by_id.get(row["id"], []),
                    "station": (
                        {
                            "id": row["station_id"],
                            "level": row["station_level"],
                            "normalized_name": row["station_normalized_name"],
                            "name_en": row["station_name_en"],
                            "name_ko": row["station_name_ko"],
                            "name_ja": row["station_name_ja"],
                        }
                        if row["station_id"] is not None
                        else None
                    ),
                    "skill_name": row["skill_name"],
                    "skill_level": row["skill_level"],
                    "dog_tag_level": row["dog_tag_level"],
                    "max_durability": row["max_durability"],
                    "min_durability": row["min_durability"],
                    "found_in_raid": row["found_in_raid"],
                    "items": condition_items_by_id.get(row["id"], []),
                    "maps": maps_by_id.get(row["id"], []),
                    "sort_order": row["sort_order"],
                }
            )

        reward_items_by_level = defaultdict(list)
        for row in reward_items:
            reward_items_by_level[row["prestige_id"]].append(
                {
                    "quantity": row["quantity"],
                    "attributes": row["attributes"],
                    "sort_order": row["sort_order"],
                    "item": PrestigeServiceV3._item_v3(row),
                }
            )
        reward_skills_by_level = defaultdict(list)
        for row in reward_skills:
            reward_skills_by_level[row["prestige_id"]].append(
                {
                    "skill_name": row["skill_name"],
                    "skill_level": row["skill_level"],
                    "sort_order": row["sort_order"],
                }
            )

        customization_items_by_id = defaultdict(list)
        for row in customization_items:
            customization_items_by_id[row["customization_id"]].append(
                PrestigeServiceV3._item_v3(row)
            )
        customizations_by_level = defaultdict(list)
        for row in customizations:
            customizations_by_level[row["prestige_id"]].append(
                {
                    "id": row["customization_id"],
                    "name_key": row["name_key"],
                    "name_en": row["name_en"],
                    "name_ko": row["name_ko"],
                    "name_ja": row["name_ja"],
                    "image_link": row["image_link"],
                    "customization_type": row["customization_type"],
                    "customization_type_name_key": row[
                        "customization_type_name_key"
                    ],
                    "customization_type_name_en": row[
                        "customization_type_name_en"
                    ],
                    "customization_type_name_ko": row[
                        "customization_type_name_ko"
                    ],
                    "customization_type_name_ja": row[
                        "customization_type_name_ja"
                    ],
                    "items": customization_items_by_id.get(
                        row["customization_id"], []
                    ),
                    "sort_order": row["sort_order"],
                }
            )

        filters_by_setting = defaultdict(lambda: defaultdict(list))
        for row in transfer_filters:
            filters_by_setting[row["transfer_setting_id"]][
                row["filter_type"]
            ].append(row["value_id"])
        transfers_by_level = defaultdict(list)
        for row in transfer_settings:
            transfers_by_level[row["prestige_id"]].append(
                {
                    "id": row["id"],
                    "type": row["setting_type"],
                    "name_key": row["name_key"],
                    "name_en": row["name_en"],
                    "name_ko": row["name_ko"],
                    "name_ja": row["name_ja"],
                    "skill_type": row["skill_type"],
                    "transfer_rate": row["transfer_rate"],
                    "grid_width": row["grid_width"],
                    "grid_height": row["grid_height"],
                    "filters": dict(filters_by_setting.get(row["id"], {})),
                    "sort_order": row["sort_order"],
                }
            )

        return [
            {
                "id": level["id"],
                "prestige_level": level["prestige_level"],
                "name_key": level["name_key"],
                "name_en": level["name_en"],
                "name_ko": level["name_ko"],
                "name_ja": level["name_ja"],
                "icon_link": level["icon_link"],
                "image_link": level["image_link"],
                "conditions": conditions_by_level.get(level["id"], []),
                "rewards": {
                    "items": reward_items_by_level.get(level["id"], []),
                    "skills": reward_skills_by_level.get(level["id"], []),
                    "customizations": customizations_by_level.get(
                        level["id"], []
                    ),
                },
                "transfer_settings": transfers_by_level.get(level["id"], []),
                "sort_order": level["sort_order"],
                "update_time": level["update_time"],
            }
            for level in levels
        ]

    @staticmethod
    def get_all_prestige_v3():
        try:
            with V3Database.SessionLocal() as session:
                levels = [
                    dict(row)
                    for row in session.execute(
                        text(PrestigeQueryV3.levels_sql())
                    ).mappings()
                ]
                return PrestigeServiceV3._build_levels_v3(session, levels)
        except Exception as error:
            logger.error(f"get_all_prestige_v3 error: {error}", exc_info=True)
            return None

    @staticmethod
    def get_prestige_by_level_v3(prestige_level: int):
        try:
            with V3Database.SessionLocal() as session:
                level = session.execute(
                    text(PrestigeQueryV3.level_sql()),
                    {"prestige_level": prestige_level},
                ).mappings().first()
                if level is None:
                    return None
                return PrestigeServiceV3._build_levels_v3(
                    session, [dict(level)]
                )[0]
        except Exception as error:
            logger.error(
                f"get_prestige_by_level_v3({prestige_level}) error: {error}",
                exc_info=True,
            )
            return None
