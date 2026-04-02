from sqlalchemy import text
from api.quest.models import NPC
from api.quest.query import QuestQuery
from api.quest.util import QuestUtil
from database import DataBaseConnector, V3Database
import logging

logger = logging.getLogger("api.quest")


class QuestService:
    @staticmethod
    def _serialize_objective_related_item(row, id_key: str):
        return {
            "id": row[id_key],
            "normalized_name": row["normalized_name"],
            "name_en": row["name_en"],
            "name_ko": row["name_ko"],
            "name_ja": row["name_ja"],
            "image": row.get("image"),
        }

    @staticmethod
    def get_all_quest_v3():
        try:
            with V3Database.SessionLocal() as s:
                result = s.execute(text(QuestQuery.quest_list_sql()))
                return [dict(row) for row in result.mappings()]
        except Exception as e:
            logger.error(
                f"get_all_quest_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_all_quest_detail_v3():
        try:
            with V3Database.SessionLocal() as s:
                result = s.execute(text(QuestQuery.quest_feed_sql()))
                return [dict(row) for row in result.mappings()]
        except Exception as e:
            logger.error(
                f"get_all_quest_detail_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_quest_by_normalized_name_v3(normalized_name: str):
        try:
            with V3Database.SessionLocal() as s:
                quest_result = s.execute(
                    text(QuestQuery.quest_detail_sql()),
                    {"normalized_name": normalized_name},
                )
                quest = quest_result.mappings().first()
                if quest is None:
                    return None

                quest_id = quest["id"]

                relations = [
                    dict(row)
                    for row in s.execute(
                        text(QuestQuery.quest_relations_sql()),
                        {"quest_id": quest_id},
                    ).mappings()
                ]
                objectives = [
                    dict(row)
                    for row in s.execute(
                        text(QuestQuery.quest_objectives_sql()),
                        {"quest_id": quest_id},
                    ).mappings()
                ]
                objective_items = [
                    dict(row)
                    for row in s.execute(
                        text(QuestQuery.quest_objective_items_sql()),
                        {"quest_id": quest_id},
                    ).mappings()
                ]
                objective_required_keys = [
                    dict(row)
                    for row in s.execute(
                        text(QuestQuery.quest_objective_required_keys_sql()),
                        {"quest_id": quest_id},
                    ).mappings()
                ]
                objective_maps = [
                    dict(row)
                    for row in s.execute(
                        text(QuestQuery.quest_objective_maps_sql()),
                        {"quest_id": quest_id},
                    ).mappings()
                ]

                reward_skills = [
                    dict(row)
                    for row in s.execute(
                        text(QuestQuery.quest_reward_skills_sql()),
                        {"quest_id": quest_id},
                    ).mappings()
                ]
                reward_trader_standing = [
                    dict(row)
                    for row in s.execute(
                        text(QuestQuery.quest_reward_trader_standing_sql()),
                        {"quest_id": quest_id},
                    ).mappings()
                ]
                reward_offer_unlocks = [
                    dict(row)
                    for row in s.execute(
                        text(QuestQuery.quest_reward_offer_unlock_sql()),
                        {"quest_id": quest_id},
                    ).mappings()
                ]
                reward_items = [
                    dict(row)
                    for row in s.execute(
                        text(QuestQuery.quest_reward_items_sql()),
                        {"quest_id": quest_id},
                    ).mappings()
                ]
                reward_craft_unlocks = [
                    dict(row)
                    for row in s.execute(
                        text(QuestQuery.quest_reward_craft_unlocks_sql()),
                        {"quest_id": quest_id},
                    ).mappings()
                ]

                require_quests = []
                next_quests = []
                for relation in relations:
                    relation_info = {
                        "id": relation["related_quest_id"],
                        "normalized_name": relation["normalized_name"],
                        "name_en": relation["name_en"],
                        "name_ko": relation["name_ko"],
                        "name_ja": relation["name_ja"],
                    }
                    if relation["relation_type"] == "require":
                        require_quests.append(relation_info)
                    elif relation["relation_type"] == "next":
                        next_quests.append(relation_info)

                objective_map = {}
                for objective in objectives:
                    objective_map[objective["objective_id"]] = {
                        "objective_id": objective["objective_id"],
                        "type": objective["type"],
                        "description_en": objective["description_en"],
                        "description_ko": objective["description_ko"],
                        "description_ja": objective["description_ja"],
                        "count": objective["count"],
                        "found_in_raid": objective["found_in_raid"],
                        "items": [],
                        "required_keys": [],
                        "maps": [],
                    }

                for item in objective_items:
                    objective = objective_map.get(item["objective_id"])
                    if objective is None:
                        continue
                    objective["items"].append(
                        {
                            "item_type": item["item_type"],
                            "item": {
                                "id": item["item_id"],
                                "normalized_name": item["normalized_name"],
                                "name_en": item["name_en"],
                                "name_ko": item["name_ko"],
                                "name_ja": item["name_ja"],
                                "image": item["image"],
                            },
                        }
                    )

                for required_key in objective_required_keys:
                    objective = objective_map.get(required_key["objective_id"])
                    if objective is None:
                        continue
                    objective["required_keys"].append(
                        {
                            "id": required_key["key_id"],
                            "normalized_name": required_key["normalized_name"],
                            "name_en": required_key["name_en"],
                            "name_ko": required_key["name_ko"],
                            "name_ja": required_key["name_ja"],
                            "image": required_key["image"],
                        }
                    )

                for map_row in objective_maps:
                    objective = objective_map.get(map_row["objective_id"])
                    if objective is None:
                        continue
                    objective["maps"].append(
                        {
                            "id": map_row["map_id"],
                            "normalized_name": map_row["normalized_name"],
                            "name_en": map_row["name_en"],
                            "name_ko": map_row["name_ko"],
                            "name_ja": map_row["name_ja"],
                        }
                    )

                result = {
                    "quest": {
                        "id": quest["id"],
                        "normalized_name": quest["normalized_name"],
                        "name_en": quest["name_en"],
                        "name_ko": quest["name_ko"],
                        "name_ja": quest["name_ja"],
                        "experience": quest["experience"],
                        "delay_max": quest["delay_max"],
                        "delay_min": quest["delay_min"],
                        "kappa_required": quest["kappa_required"],
                        "min_player_level": quest["min_player_level"],
                        "wiki_url": quest["wiki_url"],
                        "guide_en": quest["guide_en"],
                        "guide_ko": quest["guide_ko"],
                        "guide_ja": quest["guide_ja"],
                    },
                    "trader": (
                        {
                            "id": quest["trader_id"],
                            "normalized_name": quest["trader_normalized_name"],
                            "name_en": quest["trader_name_en"],
                            "name_ko": quest["trader_name_ko"],
                            "name_ja": quest["trader_name_ja"],
                            "image": quest["trader_image"],
                        }
                        if quest["trader_id"] is not None
                        else None
                    ),
                    "require_quests": require_quests,
                    "next_quests": next_quests,
                    "objectives": list(objective_map.values()),
                    "finish_rewards": {
                        "skill_level_reward": reward_skills,
                        "trader_standing": [
                            {
                                "standing": row["standing"],
                                "trader": {
                                    "id": row["trader_id"],
                                    "normalized_name": row["normalized_name"],
                                    "name_en": row["name_en"],
                                    "name_ko": row["name_ko"],
                                    "name_ja": row["name_ja"],
                                    "image": row["image"],
                                },
                            }
                            for row in reward_trader_standing
                        ],
                        "offer_unlock": [
                            {
                                "offer_id": row["offer_id"],
                                "level": row["level"],
                                "trader": (
                                    {
                                        "id": row["trader_id"],
                                        "normalized_name": row[
                                            "trader_normalized_name"
                                        ],
                                        "name_en": row["trader_name_en"],
                                        "name_ko": row["trader_name_ko"],
                                        "name_ja": row["trader_name_ja"],
                                        "image": row["trader_image"],
                                    }
                                    if row["trader_id"] is not None
                                    else None
                                ),
                                "item": (
                                    {
                                        "id": row["item_id"],
                                        "normalized_name": row["item_normalized_name"],
                                        "name_en": row["item_name_en"],
                                        "name_ko": row["item_name_ko"],
                                        "name_ja": row["item_name_ja"],
                                        "image": row["item_image"],
                                    }
                                    if row["item_id"] is not None
                                    else None
                                ),
                            }
                            for row in reward_offer_unlocks
                        ],
                        "items": [
                            {
                                "quantity": row["quantity"],
                                "item": {
                                    "id": row["item_id"],
                                    "normalized_name": row["normalized_name"],
                                    "name_en": row["name_en"],
                                    "name_ko": row["name_ko"],
                                    "name_ja": row["name_ja"],
                                    "image": row["image"],
                                },
                            }
                            for row in reward_items
                        ],
                        "craft_unlock": [
                            {
                                "craft_id": row["craft_id"],
                                "station_level": row["station_level"],
                                "reward_item": (
                                    {
                                        "id": row["reward_item_id"],
                                        "normalized_name": row["normalized_name"],
                                        "name_en": row["name_en"],
                                        "name_ko": row["name_ko"],
                                        "name_ja": row["name_ja"],
                                        "image": row["image"],
                                    }
                                    if row["reward_item_id"] is not None
                                    else None
                                ),
                            }
                            for row in reward_craft_unlocks
                        ],
                    },
                }

                return result
        except Exception as e:
            logger.error(
                f"get_quest_by_normalized_name_v3: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_quest_with_trader_v3(trader_normalized_name: str):
        try:
            with V3Database.SessionLocal() as s:
                quest_list = [
                    dict(row)
                    for row in s.execute(
                        text(QuestQuery.quest_list_by_trader_sql()),
                        {"trader_normalized_name": trader_normalized_name},
                    ).mappings()
                ]
                trader_list = [
                    dict(row)
                    for row in s.execute(text(QuestQuery.trader_list_sql())).mappings()
                ]

                return {
                    "quest_list": quest_list,
                    "trader_list": trader_list,
                }
        except Exception as e:
            logger.error(
                f"get_quest_with_trader_v3: {trader_normalized_name}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_all_quest():
        try:

            with DataBaseConnector.SessionLocal() as s:
                query = text(QuestUtil.get_all_quest_query())
                result = s.execute(query)
                quest_list = [dict(row) for row in result.mappings()]
                return quest_list
        except Exception as e:
            logger.error(
                f"get_all_quest  error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_all_quest_detail():
        try:

            with DataBaseConnector.SessionLocal() as s:
                query = text(QuestUtil.get_all_quest_detail_query())
                result = s.execute(query)
                quest_list = [dict(row) for row in result.mappings()]
                return quest_list
        except Exception as e:
            logger.error(
                f"get_all_quest_detail  error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_quest_by_id(url_mapping):
        try:

            with DataBaseConnector.SessionLocal() as s:
                query = text(QuestUtil.get_quest_detail_query())
                param = {"url_mapping": url_mapping}
                result = s.execute(query, param)
                quest = [dict(row) for row in result.mappings()]

            return quest[0]
        except Exception as e:
            logger.error(
                f"get_quest_by_id: {url_mapping}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_quest_with_trader(trader_id):
        try:

            with DataBaseConnector.SessionLocal() as s:
                info = {}
                query = text(QuestUtil.get_quest_by_npc())
                param = {"npc_id": trader_id}
                quest_list = s.execute(query, param)
                npc_list = (
                    s.query(NPC.id, NPC.name, NPC.image)
                    .filter(NPC.order != None)
                    .order_by(NPC.order)
                    .all()
                )
                info["quest_list"] = [dict(row) for row in quest_list.mappings()]
                info["trader_list"] = [
                    {"id": id_, "name": name, "image": image}
                    for id_, name, image in npc_list
                ]

            return info
        except Exception as e:
            logger.error(
                f"get_quest_with_trader: {trader_id}, error: {e}",
                exc_info=True,
            )
            return None
