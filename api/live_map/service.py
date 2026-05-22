from copy import deepcopy

from sqlalchemy import inspect, nullslast, text

from api.live_map.models import LiveMapFloorV3, LiveMapStaticPointV3
from api.live_map.query import LiveMapQueryV3
from api.map.models import MapV3
from api.quest.service import QuestServiceV3
from database import V3Database
import logging

logger = logging.getLogger("api.live_map")


class LiveMapServiceV3:
    @staticmethod
    def _serialize_map_selector_v3(row: dict):
        return {
            "id": row["id"],
            "normalized_name": row["normalized_name"],
            "name_en": row["name_en"],
            "name_ko": row["name_ko"],
            "name_ja": row["name_ja"],
        }

    @staticmethod
    def _serialize_floor_v3(floor: LiveMapFloorV3):
        return {
            "id": floor.id,
            "map_id": floor.map_id,
            "floor_no": floor.floor_no,
            "name_en": floor.name_en,
            "name_ko": floor.name_ko,
            "name_ja": floor.name_ja,
            "image": floor.image,
            "min_z": floor.min_z,
            "max_z": floor.max_z,
        }

    @staticmethod
    def _serialize_static_point_v3(point: LiveMapStaticPointV3):
        return {
            "id": point.id,
            "map_id": point.map_id,
            "floor_id": point.floor_id,
            "floor_no": point.floor_no,
            "category": point.category,
            "name_en": point.name_en,
            "name_ko": point.name_ko,
            "name_ja": point.name_ja,
            "description_en": point.description_en,
            "description_ko": point.description_ko,
            "description_ja": point.description_ja,
            "image": point.image,
            "x": point.x,
            "z": point.z,
            "y": point.y,
            "metadata": point.metadata_,
        }

    @staticmethod
    def _serialize_live_map_point_v3(row: dict, details: list[dict]):
        return {
            "id": row["id"],
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "floor_no": row["floor_no"],
            "x": row["x"],
            "z": row["z"],
            "y": row["y"],
            "details": details,
        }

    @staticmethod
    def _build_story_info_by_id_v3(
        story_point_rows: list[dict],
        story_details_by_point_id: dict[str, list[dict]],
        requirements: list[dict],
        objectives: list[dict],
        objective_items: list[dict],
        objective_maps: list[dict],
        objective_reward_items: list[dict],
        objective_reward_texts: list[dict],
        reward_trader_standing: list[dict],
        reward_items: list[dict],
    ):
        story_info_by_id = {}
        for row in story_point_rows:
            story_id = row["story_id"]
            if story_id is None or story_id in story_info_by_id:
                continue
            story_info_by_id[story_id] = {
                "story": {
                    "id": story_id,
                    "title_en": row["title_en"],
                    "title_ko": row["title_ko"],
                    "title_ja": row["title_ja"],
                },
                "requirements": [],
                "objectives": [],
                "finish_rewards": {
                    "trader_standing": [],
                    "items": [],
                },
            }

        for requirement in requirements:
            story_info = story_info_by_id.get(requirement["story_id"])
            if story_info is None:
                continue
            story_info["requirements"].append(
                {
                    "id": requirement["id"],
                    "requirement_type": requirement["requirement_type"],
                    "description_en": requirement["description_en"],
                    "description_ko": requirement["description_ko"],
                    "description_ja": requirement["description_ja"],
                }
            )

        objective_by_id = {}
        children_by_parent_id = {}
        for objective in objectives:
            objective_info = {
                "objective_id": objective["objective_id"],
                "parent_objective_id": objective["parent_objective_id"],
                "objective_type": objective["objective_type"],
                "description_en": objective["description_en"],
                "description_ko": objective["description_ko"],
                "description_ja": objective["description_ja"],
                "count": objective["count"],
                "is_optional": objective["is_optional"],
                "items": [],
                "maps": [],
                "live_map_points": [],
                "rewards": {
                    "items": [],
                    "texts": [],
                },
                "children": [],
            }
            objective_by_id[objective["objective_id"]] = objective_info
            children_by_parent_id.setdefault(objective["parent_objective_id"], []).append(
                objective_info
            )

        for item in objective_items:
            objective = objective_by_id.get(item["objective_id"])
            if objective is None:
                continue
            objective["items"].append(
                {
                    "quantity": item["quantity"],
                    "found_in_raid": item["found_in_raid"],
                    "item_role": item["item_role"],
                    "item": (
                        {
                            "id": item["item_id"],
                            "normalized_name": item["normalized_name"],
                            "name_en": item["name_en"],
                            "name_ko": item["name_ko"],
                            "name_ja": item["name_ja"],
                            "image": item["image"],
                        }
                        if item["item_id"] is not None
                        else None
                    ),
                }
            )

        for map_row in objective_maps:
            objective = objective_by_id.get(map_row["objective_id"])
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

        for row in objective_reward_items:
            objective = objective_by_id.get(row["objective_id"])
            if objective is None:
                continue
            objective["rewards"]["items"].append(
                {
                    "quantity": row["quantity"],
                    "item": (
                        {
                            "id": row["item_id"],
                            "normalized_name": row["normalized_name"],
                            "name_en": row["name_en"],
                            "name_ko": row["name_ko"],
                            "name_ja": row["name_ja"],
                            "image": row["image"],
                        }
                        if row["item_id"] is not None
                        else None
                    ),
                }
            )

        for row in objective_reward_texts:
            objective = objective_by_id.get(row["objective_id"])
            if objective is None:
                continue
            objective["rewards"]["texts"].append(
                {
                    "id": row["id"],
                    "reward_type": row["reward_type"],
                    "description_en": row["description_en"],
                    "description_ko": row["description_ko"],
                    "description_ja": row["description_ja"],
                }
            )

        for row in story_point_rows:
            objective = objective_by_id.get(row["objective_id"])
            if objective is None:
                continue
            objective["live_map_points"].append(
                LiveMapServiceV3._serialize_live_map_point_v3(
                    row, story_details_by_point_id.get(row["id"], [])
                )
            )

        for objective_id, objective in objective_by_id.items():
            objective["children"] = children_by_parent_id.get(objective_id, [])

        for objective in objectives:
            if objective["parent_objective_id"] is not None:
                continue
            story_info = story_info_by_id.get(objective["story_id"])
            if story_info is not None:
                story_info["objectives"].append(objective_by_id[objective["objective_id"]])

        for row in reward_trader_standing:
            story_info = story_info_by_id.get(row["story_id"])
            if story_info is None:
                continue
            story_info["finish_rewards"]["trader_standing"].append(
                {
                    "standing": row["standing"],
                    "trader": (
                        {
                            "id": row["trader_id"],
                            "normalized_name": row["normalized_name"],
                            "name_en": row["name_en"],
                            "name_ko": row["name_ko"],
                            "name_ja": row["name_ja"],
                            "image": row["image"],
                        }
                        if row["trader_id"] is not None
                        else None
                    ),
                }
            )

        for row in reward_items:
            story_info = story_info_by_id.get(row["story_id"])
            if story_info is None:
                continue
            story_info["finish_rewards"]["items"].append(
                {
                    "quantity": row["quantity"],
                    "item": (
                        {
                            "id": row["item_id"],
                            "normalized_name": row["normalized_name"],
                            "name_en": row["name_en"],
                            "name_ko": row["name_ko"],
                            "name_ja": row["name_ja"],
                            "image": row["image"],
                        }
                        if row["item_id"] is not None
                        else None
                    ),
                }
            )

        return story_info_by_id

    @staticmethod
    def _serialize_story_point_v3(row: dict, story_info: dict | None):
        return {
            "id": row["id"],
            "story_id": row["story_id"],
            "objective_id": row["objective_id"],
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "floor_no": row["floor_no"],
            "x": row["x"],
            "z": row["z"],
            "y": row["y"],
            "story_info": story_info,
        }

    @staticmethod
    def _build_event_info_by_id_v3(
        event_point_rows: list[dict],
        event_details_by_point_id: dict[str, list[dict]],
        objectives: list[dict],
        objective_items: list[dict],
        reward_trader_standing: list[dict],
        reward_items: list[dict],
    ):
        event_info_by_id = {}
        for row in event_point_rows:
            event_id = row["event_id"]
            if event_id is None or event_id in event_info_by_id:
                continue
            event_info_by_id[event_id] = {
                "event": {
                    "id": event_id,
                    "title_en": row["title_en"],
                    "title_ko": row["title_ko"],
                    "title_ja": row["title_ja"],
                    "is_active": row["is_active"],
                },
                "trader": (
                    {
                        "id": row["trader_id"],
                        "normalized_name": row["trader_normalized_name"],
                        "name_en": row["trader_name_en"],
                        "name_ko": row["trader_name_ko"],
                        "name_ja": row["trader_name_ja"],
                        "image": row["trader_image"],
                    }
                    if row["trader_id"] is not None
                    else None
                ),
                "objectives": [],
                "finish_rewards": {
                    "trader_standing": [],
                    "items": [],
                },
            }

        objective_by_id = {}
        children_by_parent_id = {}
        for objective in objectives:
            objective_info = {
                "objective_id": objective["objective_id"],
                "parent_objective_id": objective["parent_objective_id"],
                "objective_type": objective["objective_type"],
                "description_en": objective["description_en"],
                "description_ko": objective["description_ko"],
                "description_ja": objective["description_ja"],
                "count": objective["count"],
                "is_optional": objective["is_optional"],
                "items": [],
                "live_map_points": [],
                "children": [],
            }
            objective_by_id[objective["objective_id"]] = objective_info
            children_by_parent_id.setdefault(objective["parent_objective_id"], []).append(
                objective_info
            )

        for item in objective_items:
            objective = objective_by_id.get(item["objective_id"])
            if objective is None:
                continue
            objective["items"].append(
                {
                    "quantity": item["quantity"],
                    "found_in_raid": item["found_in_raid"],
                    "item_role": item["item_role"],
                    "item": (
                        {
                            "id": item["item_id"],
                            "normalized_name": item["normalized_name"],
                            "name_en": item["name_en"],
                            "name_ko": item["name_ko"],
                            "name_ja": item["name_ja"],
                            "image": item["image"],
                        }
                        if item["item_id"] is not None
                        else None
                    ),
                }
            )

        for row in event_point_rows:
            objective = objective_by_id.get(row["objective_id"])
            if objective is None:
                continue
            objective["live_map_points"].append(
                LiveMapServiceV3._serialize_live_map_point_v3(
                    row, event_details_by_point_id.get(row["id"], [])
                )
            )

        for objective_id, objective in objective_by_id.items():
            objective["children"] = children_by_parent_id.get(objective_id, [])

        for objective in objectives:
            if objective["parent_objective_id"] is not None:
                continue
            event_info = event_info_by_id.get(objective["event_id"])
            if event_info is not None:
                event_info["objectives"].append(objective_by_id[objective["objective_id"]])

        for row in reward_trader_standing:
            event_info = event_info_by_id.get(row["event_id"])
            if event_info is None:
                continue
            event_info["finish_rewards"]["trader_standing"].append(
                {
                    "standing": row["standing"],
                    "trader": (
                        {
                            "id": row["trader_id"],
                            "normalized_name": row["normalized_name"],
                            "name_en": row["name_en"],
                            "name_ko": row["name_ko"],
                            "name_ja": row["name_ja"],
                            "image": row["image"],
                        }
                        if row["trader_id"] is not None
                        else None
                    ),
                }
            )

        for row in reward_items:
            event_info = event_info_by_id.get(row["event_id"])
            if event_info is None:
                continue
            event_info["finish_rewards"]["items"].append(
                {
                    "quantity": row["quantity"],
                    "item": (
                        {
                            "id": row["item_id"],
                            "normalized_name": row["normalized_name"],
                            "name_en": row["name_en"],
                            "name_ko": row["name_ko"],
                            "name_ja": row["name_ja"],
                            "image": row["image"],
                        }
                        if row["item_id"] is not None
                        else None
                    ),
                }
            )

        return event_info_by_id

    @staticmethod
    def _serialize_event_point_v3(row: dict, event_info: dict | None):
        return {
            "id": row["id"],
            "event_id": row["event_id"],
            "objective_id": row["objective_id"],
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "floor_no": row["floor_no"],
            "x": row["x"],
            "z": row["z"],
            "y": row["y"],
            "event_info": event_info,
        }

    @staticmethod
    def _strip_quest_html_text_v3(quest_detail: dict | None):
        if quest_detail is None:
            return None

        quest = quest_detail.get("quest")
        if quest is not None:
            quest.pop("guide_en", None)
            quest.pop("guide_ko", None)
            quest.pop("guide_ja", None)
        return quest_detail

    @staticmethod
    def _attach_live_map_point_to_objective_v3(
        row: dict, details: list[dict], quest_detail: dict | None
    ):
        if quest_detail is None:
            return None

        quest_info = deepcopy(quest_detail)
        objective_id = row["objective_id"]
        if objective_id is None:
            return quest_info

        live_map_point = {
            "id": row["id"],
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "floor_no": row["floor_no"],
            "x": row["x"],
            "z": row["z"],
            "y": row["y"],
            "details": details,
        }

        for objective in quest_info.get("objectives", []):
            if objective.get("objective_id") == objective_id:
                objective["live_map_point"] = live_map_point
                break

        return quest_info

    @staticmethod
    def _serialize_quest_point_v3(row: dict, quest_info: dict | None):
        return {
            "id": row["id"],
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "floor_no": row["floor_no"],
            "x": row["x"],
            "z": row["z"],
            "y": row["y"],
            "quest_info": quest_info,
        }

    @staticmethod
    def _get_map_selector_v3(s):
        return [
            LiveMapServiceV3._serialize_map_selector_v3(dict(row))
            for row in s.execute(text(LiveMapQueryV3.map_selector_sql())).mappings()
        ]

    @staticmethod
    def _can_query_story_points_v3(s):
        inspector = inspect(s.bind)
        return inspector.has_table("live_map_story_points")

    @staticmethod
    def _can_query_event_points_v3(s):
        inspector = inspect(s.bind)
        return inspector.has_table("live_map_event_points")

    @staticmethod
    def _has_table_v3(s, table_name: str):
        inspector = inspect(s.bind)
        return inspector.has_table(table_name)

    @staticmethod
    def get_live_map_v3(normalized_name: str):
        try:
            with V3Database.SessionLocal() as s:
                map_data = (
                    s.query(MapV3)
                    .filter(
                        MapV3.normalized_name == normalized_name,
                        MapV3.is_use.is_(True),
                    )
                    .first()
                )
                if map_data is None:
                    return None

                floors = (
                    s.query(LiveMapFloorV3)
                    .filter(LiveMapFloorV3.map_id == map_data.id)
                    .order_by(
                        nullslast(LiveMapFloorV3.sort_order),
                        LiveMapFloorV3.floor_no,
                    )
                    .all()
                )

                static_points = (
                    s.query(LiveMapStaticPointV3)
                    .filter(LiveMapStaticPointV3.map_id == map_data.id)
                    .order_by(
                        LiveMapStaticPointV3.floor_no,
                        LiveMapStaticPointV3.category,
                        LiveMapStaticPointV3.sort_order,
                        LiveMapStaticPointV3.name_en,
                    )
                    .all()
                )

                detail_rows = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.point_details_by_map_sql()),
                        {"map_id": map_data.id},
                    ).mappings()
                ]
                details_by_point_id = {}
                for detail in detail_rows:
                    details_by_point_id.setdefault(detail["point_id"], []).append(
                        {
                            "id": detail["id"],
                            "description_en": detail["description_en"],
                            "description_ko": detail["description_ko"],
                            "description_ja": detail["description_ja"],
                            "image": detail["image"],
                        }
                    )

                quest_point_rows = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.quest_points_by_map_sql()),
                        {"map_id": map_data.id},
                    ).mappings()
                ]

                quest_detail_by_normalized_name = {}
                for row in quest_point_rows:
                    quest_normalized_name = row["quest_normalized_name"]
                    if (
                        quest_normalized_name is not None
                        and quest_normalized_name not in quest_detail_by_normalized_name
                    ):
                        quest_detail_by_normalized_name[quest_normalized_name] = (
                            LiveMapServiceV3._strip_quest_html_text_v3(
                                QuestServiceV3.get_quest_by_normalized_name_v3(
                                    quest_normalized_name
                                )
                            )
                        )

                quest_points = [
                    LiveMapServiceV3._serialize_quest_point_v3(
                        row,
                        LiveMapServiceV3._attach_live_map_point_to_objective_v3(
                            row,
                            details_by_point_id.get(row["id"], []),
                            quest_detail_by_normalized_name.get(
                                row["quest_normalized_name"]
                            ),
                        ),
                    )
                    for row in quest_point_rows
                ]

                story_points = []
                if LiveMapServiceV3._can_query_story_points_v3(s):
                    story_point_rows = [
                        dict(row)
                        for row in s.execute(
                            text(LiveMapQueryV3.story_points_by_map_sql()),
                            {"map_id": map_data.id},
                        ).mappings()
                    ]
                else:
                    story_point_rows = []

                if story_point_rows:
                    story_detail_rows = [
                        dict(row)
                        for row in s.execute(
                            text(LiveMapQueryV3.story_point_details_by_map_sql()),
                            {"map_id": map_data.id},
                        ).mappings()
                    ]
                    story_details_by_point_id = {}
                    for detail in story_detail_rows:
                        story_details_by_point_id.setdefault(
                            detail["point_id"], []
                        ).append(
                            {
                                "id": detail["id"],
                                "description_en": detail["description_en"],
                                "description_ko": detail["description_ko"],
                                "description_ja": detail["description_ja"],
                                "image": detail["image"],
                            }
                        )

                    story_ids = sorted(
                        {row["story_id"] for row in story_point_rows if row["story_id"]}
                    )
                    requirements = []
                    objectives = []
                    objective_items = []
                    objective_maps = []
                    objective_reward_items = []
                    objective_reward_texts = []
                    reward_trader_standing = []
                    reward_items = []
                    if story_ids:
                        requirements = [
                            dict(row)
                            for row in s.execute(
                                text(
                                    LiveMapQueryV3.story_requirements_by_story_ids_sql()
                                ),
                                {"story_ids": story_ids},
                            ).mappings()
                        ]
                        objectives = [
                            dict(row)
                            for row in s.execute(
                                text(
                                    LiveMapQueryV3.story_objectives_by_story_ids_sql()
                                ),
                                {"story_ids": story_ids},
                            ).mappings()
                        ]
                        objective_items = [
                            dict(row)
                            for row in s.execute(
                                text(
                                    LiveMapQueryV3.story_objective_items_by_story_ids_sql()
                                ),
                                {"story_ids": story_ids},
                            ).mappings()
                        ]
                        objective_maps = [
                            dict(row)
                            for row in s.execute(
                                text(
                                    LiveMapQueryV3.story_objective_maps_by_story_ids_sql()
                                ),
                                {"story_ids": story_ids},
                            ).mappings()
                        ]
                        if LiveMapServiceV3._has_table_v3(
                            s, "story_objective_reward_items"
                        ):
                            objective_reward_items = [
                                dict(row)
                                for row in s.execute(
                                    text(
                                        LiveMapQueryV3.story_objective_reward_items_by_story_ids_sql()
                                    ),
                                    {"story_ids": story_ids},
                                ).mappings()
                            ]
                        if LiveMapServiceV3._has_table_v3(
                            s, "story_objective_reward_texts"
                        ):
                            objective_reward_texts = [
                                dict(row)
                                for row in s.execute(
                                    text(
                                        LiveMapQueryV3.story_objective_reward_texts_by_story_ids_sql()
                                    ),
                                    {"story_ids": story_ids},
                                ).mappings()
                            ]
                        if LiveMapServiceV3._has_table_v3(
                            s, "story_reward_trader_standing"
                        ):
                            reward_trader_standing = [
                                dict(row)
                                for row in s.execute(
                                    text(
                                        LiveMapQueryV3.story_reward_trader_standing_by_story_ids_sql()
                                    ),
                                    {"story_ids": story_ids},
                                ).mappings()
                            ]
                        if LiveMapServiceV3._has_table_v3(s, "story_reward_items"):
                            reward_items = [
                                dict(row)
                                for row in s.execute(
                                    text(
                                        LiveMapQueryV3.story_reward_items_by_story_ids_sql()
                                    ),
                                    {"story_ids": story_ids},
                                ).mappings()
                            ]

                    story_info_by_id = LiveMapServiceV3._build_story_info_by_id_v3(
                        story_point_rows,
                        story_details_by_point_id,
                        requirements,
                        objectives,
                        objective_items,
                        objective_maps,
                        objective_reward_items,
                        objective_reward_texts,
                        reward_trader_standing,
                        reward_items,
                    )
                    story_points = [
                        LiveMapServiceV3._serialize_story_point_v3(
                            row, story_info_by_id.get(row["story_id"])
                        )
                        for row in story_point_rows
                    ]

                event_points = []
                if LiveMapServiceV3._can_query_event_points_v3(s):
                    event_point_rows = [
                        dict(row)
                        for row in s.execute(
                            text(LiveMapQueryV3.event_points_by_map_sql()),
                            {"map_id": map_data.id},
                        ).mappings()
                    ]
                else:
                    event_point_rows = []

                if event_point_rows:
                    event_detail_rows = [
                        dict(row)
                        for row in s.execute(
                            text(LiveMapQueryV3.event_point_details_by_map_sql()),
                            {"map_id": map_data.id},
                        ).mappings()
                    ]
                    event_details_by_point_id = {}
                    for detail in event_detail_rows:
                        event_details_by_point_id.setdefault(
                            detail["point_id"], []
                        ).append(
                            {
                                "id": detail["id"],
                                "description_en": detail["description_en"],
                                "description_ko": detail["description_ko"],
                                "description_ja": detail["description_ja"],
                                "image": detail["image"],
                            }
                        )

                    event_ids = sorted(
                        {row["event_id"] for row in event_point_rows if row["event_id"]}
                    )
                    event_objectives = []
                    event_objective_items = []
                    event_reward_trader_standing = []
                    event_reward_items = []
                    if event_ids:
                        event_objectives = [
                            dict(row)
                            for row in s.execute(
                                text(LiveMapQueryV3.event_objectives_by_event_ids_sql()),
                                {"event_ids": event_ids},
                            ).mappings()
                        ]
                        event_objective_items = [
                            dict(row)
                            for row in s.execute(
                                text(
                                    LiveMapQueryV3.event_objective_items_by_event_ids_sql()
                                ),
                                {"event_ids": event_ids},
                            ).mappings()
                        ]
                        if LiveMapServiceV3._has_table_v3(
                            s, "live_map_event_reward_trader_standing"
                        ):
                            event_reward_trader_standing = [
                                dict(row)
                                for row in s.execute(
                                    text(
                                        LiveMapQueryV3.event_reward_trader_standing_by_event_ids_sql()
                                    ),
                                    {"event_ids": event_ids},
                                ).mappings()
                            ]
                        if LiveMapServiceV3._has_table_v3(
                            s, "live_map_event_reward_items"
                        ):
                            event_reward_items = [
                                dict(row)
                                for row in s.execute(
                                    text(
                                        LiveMapQueryV3.event_reward_items_by_event_ids_sql()
                                    ),
                                    {"event_ids": event_ids},
                                ).mappings()
                            ]

                    event_info_by_id = LiveMapServiceV3._build_event_info_by_id_v3(
                        event_point_rows,
                        event_details_by_point_id,
                        event_objectives,
                        event_objective_items,
                        event_reward_trader_standing,
                        event_reward_items,
                    )
                    event_points = [
                        LiveMapServiceV3._serialize_event_point_v3(
                            row, event_info_by_id.get(row["event_id"])
                        )
                        for row in event_point_rows
                    ]

                return {
                    "map_selector": LiveMapServiceV3._get_map_selector_v3(s),
                    "floors": [
                        LiveMapServiceV3._serialize_floor_v3(row) for row in floors
                    ],
                    "quest_points": quest_points,
                    "story_points": story_points,
                    "event_points": event_points,
                    "static_points": [
                        LiveMapServiceV3._serialize_static_point_v3(row)
                        for row in static_points
                    ],
                }
        except Exception as e:
            logger.error(
                f"get_live_map_v3: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None
