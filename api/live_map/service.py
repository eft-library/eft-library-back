from copy import deepcopy
from datetime import datetime, timedelta, timezone

import requests
from sqlalchemy import inspect, nullslast, text

from api.live_map.models import (
    LiveMapFloorV3,
    LiveMapFloorZoneV3,
    LiveMapStaticPointV3,
)
from api.live_map.query import LiveMapQueryV3
from api.live_map.res_models import (
    BtrRouteMapV3,
    BtrRoutePointV3,
    BtrRouteStopV3,
    BtrRouteV3,
    BtrRoutesResponseV3,
)
from api.map.models import MapV3
from api.quest.service import QuestServiceV3
from database import V3Database
import logging

logger = logging.getLogger("api.live_map")


class LiveMapServiceV3:
    _BTR_TABLES_V3 = (
        "live_map_btr_routes",
        "live_map_btr_route_points",
        "live_map_btr_route_stops",
    )
    _raid_durations_v3: dict[str, int] = {}
    _raid_durations_fetched_at_v3: datetime | None = None

    @staticmethod
    def get_raid_duration_v3(normalized_name: str):
        now = datetime.now(timezone.utc)
        fetched_at = LiveMapServiceV3._raid_durations_fetched_at_v3
        if fetched_at is None or now - fetched_at > timedelta(minutes=15):
            try:
                response = requests.post(
                    "https://api.tarkov.dev/graphql",
                    json={"query": "{ maps { normalizedName raidDuration } }"},
                    timeout=8,
                )
                response.raise_for_status()
                maps = response.json().get("data", {}).get("maps", [])
                LiveMapServiceV3._raid_durations_v3 = {
                    row["normalizedName"]: row["raidDuration"]
                    for row in maps
                    if row.get("normalizedName") and row.get("raidDuration")
                }
                LiveMapServiceV3._raid_durations_fetched_at_v3 = now
            except (requests.RequestException, ValueError, TypeError) as e:
                logger.warning(f"get_raid_duration_v3 refresh failed: {e}")

        duration = LiveMapServiceV3._raid_durations_v3.get(normalized_name)
        return {"normalized_name": normalized_name, "minutes": duration} if duration else None

    @staticmethod
    def _starts_with_hangul_v3(value: str | None):
        if not value:
            return False
        stripped_value = value.strip()
        if not stripped_value:
            return False
        first_char = stripped_value[0]
        return (
            "\uac00" <= first_char <= "\ud7a3"
            or "\u3131" <= first_char <= "\u318e"
        )

    @staticmethod
    def _quest_name_sort_key_v3(row: dict):
        name_ko = row.get("quest_name_ko") or ""
        starts_with_hangul = LiveMapServiceV3._starts_with_hangul_v3(name_ko)
        name = name_ko or row.get("quest_name_en") or ""
        return (
            not starts_with_hangul,
            name == "",
            name.casefold(),
            row.get("quest_name_en") or "",
            row.get("objective_sort_order") is None,
            row.get("objective_sort_order") or 0,
            row.get("floor_id") or "",
            row.get("id") or "",
        )

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
    def _serialize_floor_zone_v3(zone: LiveMapFloorZoneV3):
        return {
            "id": zone.id,
            "floor_id": zone.floor_id,
            "map_id": zone.map_id,
            "area_x_min": zone.area_x_min,
            "area_x_max": zone.area_x_max,
            "area_z_min": zone.area_z_min,
            "area_z_max": zone.area_z_max,
            "override_min_y": zone.override_min_y,
            "override_max_y": zone.override_max_y,
        }

    @staticmethod
    def _serialize_floor_v3(floor: LiveMapFloorV3, zones: list[dict] | None = None):
        return {
            "id": floor.id,
            "map_id": floor.map_id,
            "floor_no": floor.floor_no,
            "name_en": floor.name_en,
            "name_ko": floor.name_ko,
            "name_ja": floor.name_ja,
            "image": floor.image,
            "map_bounds": floor.map_bounds,
            "default_zoom_level": floor.default_zoom_level,
            "is_main": floor.is_main,
            "min_y": floor.min_y,
            "max_y": floor.max_y,
            "zones": zones or [],
        }

    @staticmethod
    def _serialize_static_point_v3(point: LiveMapStaticPointV3):
        return {
            "id": point.id,
            "map_id": point.map_id,
            "floor_id": point.floor_id,
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
            "metadata": point.metadata_,
            "is_use": point.is_use,
        }

    @staticmethod
    def _serialize_live_map_point_v3(row: dict, details: list[dict]):
        live_map_point = {
            "id": row["id"],
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "x": row["x"],
            "z": row["z"],
            "details": details,
        }
        if row.get("map_normalized_name") is not None:
            live_map_point["map"] = {
                "id": row["map_id"],
                "normalized_name": row["map_normalized_name"],
                "name_en": row["map_name_en"],
                "name_ko": row["map_name_ko"],
                "name_ja": row["map_name_ja"],
            }
        return live_map_point

    @staticmethod
    def _build_story_info_by_id_v3(
        story_rows: list[dict],
        story_live_map_point_rows: list[dict],
        story_details_by_point_id: dict[str, list[dict]],
        requirements: list[dict],
        requirement_items: list[dict],
        requirement_live_map_point_rows: list[dict],
        requirement_point_details_by_point_id: dict[str, list[dict]],
        objectives: list[dict],
        objective_items: list[dict],
        objective_reward_items: list[dict],
        objective_reward_texts: list[dict],
        reward_trader_standing: list[dict],
        reward_items: list[dict],
    ):
        story_info_by_id = {}
        for row in story_rows:
            story_id = row["id"]
            if story_id is None:
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

        requirement_by_id = {}
        for requirement in requirements:
            story_info = story_info_by_id.get(requirement["story_id"])
            if story_info is None:
                continue
            requirement_info = {
                "id": requirement["id"],
                "requirement_type": requirement["requirement_type"],
                "description_en": requirement["description_en"],
                "description_ko": requirement["description_ko"],
                "description_ja": requirement["description_ja"],
                "items": [],
                "live_map_points": [],
            }
            requirement_by_id[requirement["id"]] = requirement_info
            story_info["requirements"].append(requirement_info)

        for item in requirement_items:
            requirement = requirement_by_id.get(item["requirement_id"])
            if requirement is None:
                continue
            requirement["items"].append(
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

        for row in requirement_live_map_point_rows:
            requirement = requirement_by_id.get(row["requirement_id"])
            if requirement is None:
                continue
            requirement["live_map_points"].append(
                LiveMapServiceV3._serialize_live_map_point_v3(
                    row, requirement_point_details_by_point_id.get(row["id"], [])
                )
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

        for row in story_live_map_point_rows:
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
            "requirement_id": row.get("requirement_id"),
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "x": row["x"],
            "z": row["z"],
            "story_info": story_info,
        }

    @staticmethod
    def _build_event_info_by_id_v3(
        event_point_rows: list[dict],
        event_live_map_point_rows: list[dict],
        event_details_by_point_id: dict[str, list[dict]],
        objectives: list[dict],
        objective_items: list[dict],
        reward_trader_standing: list[dict],
        reward_items: list[dict],
        reward_texts: list[dict],
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
                    "texts": [],
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

        for row in event_live_map_point_rows:
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

        for row in reward_texts:
            event_info = event_info_by_id.get(row["event_id"])
            if event_info is None:
                continue
            event_info["finish_rewards"]["texts"].append(
                {
                    "id": row["id"],
                    "reward_type": row["reward_type"],
                    "description_en": row["description_en"],
                    "description_ko": row["description_ko"],
                    "description_ja": row["description_ja"],
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
            "map": (
                {
                    "id": row["map_id"],
                    "normalized_name": row["map_normalized_name"],
                    "name_en": row["map_name_en"],
                    "name_ko": row["map_name_ko"],
                    "name_ja": row["map_name_ja"],
                }
                if row.get("map_normalized_name") is not None
                else None
            ),
            "floor_id": row["floor_id"],
            "x": row["x"],
            "z": row["z"],
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
        row: dict,
        details: list[dict],
        quest_detail: dict | None,
        quest_live_map_points_by_objective_id: dict[str, list[dict]] | None = None,
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
            "x": row["x"],
            "z": row["z"],
            "details": details,
        }

        for objective in quest_info.get("objectives", []):
            current_objective_id = objective.get("objective_id")
            if quest_live_map_points_by_objective_id is not None:
                live_map_points = quest_live_map_points_by_objective_id.get(
                    current_objective_id
                )
                if live_map_points:
                    objective["live_map_points"] = deepcopy(live_map_points)

            if current_objective_id == objective_id:
                objective["live_map_point"] = live_map_point

        return quest_info

    @staticmethod
    def _build_quest_live_map_points_by_quest_id_v3(
        quest_point_rows: list[dict],
        details_by_point_id: dict[str, list[dict]],
    ):
        quest_live_map_points_by_quest_id = {}
        for row in quest_point_rows:
            quest_id = row["quest_id"]
            objective_id = row["objective_id"]
            if quest_id is None or objective_id is None:
                continue

            live_map_point = {
                "id": row["id"],
                "map_id": row["map_id"],
                "floor_id": row["floor_id"],
                "x": row["x"],
                "z": row["z"],
                "details": details_by_point_id.get(row["id"], []),
            }
            if row.get("map_normalized_name") is not None:
                live_map_point["map"] = {
                    "id": row["map_id"],
                    "normalized_name": row["map_normalized_name"],
                    "name_en": row["map_name_en"],
                    "name_ko": row["map_name_ko"],
                    "name_ja": row["map_name_ja"],
                }
            quest_live_map_points_by_quest_id.setdefault(quest_id, {}).setdefault(
                objective_id, []
            ).append(live_map_point)

        return quest_live_map_points_by_quest_id

    @staticmethod
    def _serialize_quest_point_v3(row: dict, quest_info: dict | None):
        return {
            "id": row["id"],
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "x": row["x"],
            "z": row["z"],
            "quest_info": quest_info,
        }

    @staticmethod
    def _serialize_quest_point_summary_v3(row: dict, details: list[dict]):
        return {
            "id": row["id"],
            "quest_id": row["quest_id"],
            "objective_id": row["objective_id"],
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "x": row["x"],
            "z": row["z"],
            "details": details,
            "quest_info": {
                "quest": (
                    {
                        "id": row["quest_id"],
                        "normalized_name": row["quest_normalized_name"],
                        "name_en": row["quest_name_en"],
                        "name_ko": row["quest_name_ko"],
                        "name_ja": row["quest_name_ja"],
                        "min_player_level": row["min_player_level"],
                    }
                    if row["quest_id"] is not None
                    else None
                ),
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
                "objective": (
                    {
                        "objective_id": row["objective_id"],
                        "type": row["objective_type"],
                        "description_en": row["objective_description_en"],
                        "description_ko": row["objective_description_ko"],
                        "description_ja": row["objective_description_ja"],
                        "count": row["objective_count"],
                        "found_in_raid": row["found_in_raid"],
                        "optional": row["objective_optional"],
                    }
                    if row["objective_id"] is not None
                    else None
                ),
                "requirement": (
                    {
                        "id": row["requirement_id"],
                        "requirement_type": row["requirement_type"],
                        "description_en": row["requirement_description_en"],
                        "description_ko": row["requirement_description_ko"],
                        "description_ja": row["requirement_description_ja"],
                    }
                    if row.get("requirement_id") is not None
                    else None
                ),
            },
        }

    @staticmethod
    def _serialize_story_point_summary_v3(row: dict):
        return {
            "id": row["id"],
            "story_id": row["story_id"],
            "objective_id": row["objective_id"],
            "requirement_id": row.get("requirement_id"),
            "map_id": row["map_id"],
            "floor_id": row["floor_id"],
            "x": row["x"],
            "z": row["z"],
            "story_info": {
                "story": (
                    {
                        "id": row["story_id"],
                        "title_en": row["title_en"],
                        "title_ko": row["title_ko"],
                        "title_ja": row["title_ja"],
                    }
                    if row["story_id"] is not None
                    else None
                ),
                "objective": (
                    {
                        "objective_id": row["objective_id"],
                        "description_en": row["objective_description_en"],
                        "description_ko": row["objective_description_ko"],
                        "description_ja": row["objective_description_ja"],
                    }
                    if row["objective_id"] is not None
                    else None
                ),
                "requirement": (
                    {
                        "id": row["requirement_id"],
                        "requirement_type": row["requirement_type"],
                        "description_en": row["requirement_description_en"],
                        "description_ko": row["requirement_description_ko"],
                        "description_ja": row["requirement_description_ja"],
                    }
                    if row.get("requirement_id") is not None
                    else None
                ),
            },
        }

    @staticmethod
    def _serialize_event_point_summary_v3(row: dict):
        return {
            "id": row["id"],
            "event_id": row["event_id"],
            "objective_id": row["objective_id"],
            "map_id": row["map_id"],
            "map": (
                {
                    "id": row["map_id"],
                    "normalized_name": row["map_normalized_name"],
                    "name_en": row["map_name_en"],
                    "name_ko": row["map_name_ko"],
                    "name_ja": row["map_name_ja"],
                }
                if row.get("map_normalized_name") is not None
                else None
            ),
            "floor_id": row["floor_id"],
            "x": row["x"],
            "z": row["z"],
            "event_info": {
                "event": (
                    {
                        "id": row["event_id"],
                        "title_en": row["title_en"],
                        "title_ko": row["title_ko"],
                        "title_ja": row["title_ja"],
                        "is_active": row["is_active"],
                    }
                    if row["event_id"] is not None
                    else None
                ),
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
                "objective": (
                    {
                        "objective_id": row["objective_id"],
                        "description_en": row["objective_description_en"],
                        "description_ko": row["objective_description_ko"],
                        "description_ja": row["objective_description_ja"],
                    }
                    if row["objective_id"] is not None
                    else None
                ),
            },
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
    def _can_query_btr_routes_v3(s):
        inspector = inspect(s.bind)
        return all(
            inspector.has_table(table_name)
            for table_name in LiveMapServiceV3._BTR_TABLES_V3
        )

    @staticmethod
    def _get_btr_routes_by_map_id_v3(s, map_id: str):
        if not LiveMapServiceV3._can_query_btr_routes_v3(s):
            return []

        route_rows = list(
            s.execute(
                text(LiveMapQueryV3.btr_routes_by_map_sql()),
                {"map_id": map_id},
            ).mappings()
        )
        if not route_rows:
            return []

        route_ids = [row["id"] for row in route_rows]
        point_rows = list(
            s.execute(
                text(LiveMapQueryV3.btr_route_points_by_route_ids_sql()),
                {"route_ids": route_ids},
            ).mappings()
        )
        stop_rows = list(
            s.execute(
                text(LiveMapQueryV3.btr_route_stops_by_route_ids_sql()),
                {"route_ids": route_ids},
            ).mappings()
        )

        points_by_route_id: dict[str, list[BtrRoutePointV3]] = {}
        for row in point_rows:
            points_by_route_id.setdefault(row["route_id"], []).append(
                BtrRoutePointV3(
                    id=row["id"],
                    x=float(row["x"]),
                    z=float(row["z"]),
                    sort_order=row["sort_order"],
                )
            )

        stops_by_route_id: dict[str, list[BtrRouteStopV3]] = {}
        for row in stop_rows:
            stops_by_route_id.setdefault(row["route_id"], []).append(
                BtrRouteStopV3(
                    id=row["id"],
                    static_point_id=row["static_point_id"],
                    route_point_id=row["route_point_id"],
                    name_en=row["name_en"] or "",
                    name_ko=row["name_ko"] or "",
                    name_ja=row["name_ja"] or "",
                    x=float(row["x"]),
                    z=float(row["z"]),
                    arrival_remaining_seconds=row["arrival_remaining_seconds"],
                    departure_remaining_seconds=row[
                        "departure_remaining_seconds"
                    ],
                    visit_order=row["visit_order"],
                    route_point_order=row["route_point_order"],
                )
            )

        return [
            BtrRouteV3(
                id=row["id"],
                name=row["name"],
                spawn_type=row["spawn_type"],
                raid_duration_seconds=row["raid_duration_seconds"],
                spawn_remaining_seconds=row["spawn_remaining_seconds"],
                stop_duration_seconds=row["stop_duration_seconds"],
                timing_variance_seconds=row["timing_variance_seconds"],
                points=points_by_route_id.get(row["id"], []),
                stops=stops_by_route_id.get(row["id"], []),
            )
            for row in route_rows
        ]

    @staticmethod
    def get_btr_routes_v3(normalized_name: str):
        try:
            with V3Database.SessionLocal() as s:
                map_data = (
                    s.query(MapV3)
                    .filter(MapV3.normalized_name == normalized_name)
                    .order_by(
                        nullslast(MapV3.is_use.desc()),
                        nullslast(MapV3.sort_order),
                        MapV3.name_en,
                    )
                    .first()
                )
                if map_data is None:
                    return None

                response = BtrRoutesResponseV3(
                    map=BtrRouteMapV3(
                        id=map_data.id,
                        normalized_name=map_data.normalized_name,
                    ),
                    routes=LiveMapServiceV3._get_btr_routes_by_map_id_v3(
                        s, map_data.id
                    ),
                )
                return response.model_dump()
        except Exception as e:
            logger.error(
                f"get_btr_routes_v3: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def _build_details_by_point_id_v3(detail_rows: list[dict]):
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
        return details_by_point_id

    @staticmethod
    def get_quest_detail_v3(quest_id_or_normalized_name: str):
        try:
            with V3Database.SessionLocal() as s:
                quest_row = s.execute(
                    text(
                        """
                        select id, normalized_name
                        from quests
                        where (id = :identifier
                            or normalized_name = :identifier)
                          and is_use is true
                        limit 1;
                        """
                    ),
                    {"identifier": quest_id_or_normalized_name},
                ).mappings().first()
                if quest_row is None:
                    return None

                quest_detail = LiveMapServiceV3._strip_quest_html_text_v3(
                    QuestServiceV3.get_quest_by_normalized_name_v3(
                        quest_row["normalized_name"]
                    )
                )
                if quest_detail is None:
                    return None

                quest_point_rows = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.quest_points_by_quest_ids_sql()),
                        {"quest_ids": [quest_row["id"]]},
                    ).mappings()
                ]
                detail_rows = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.point_details_by_quest_ids_sql()),
                        {"quest_ids": [quest_row["id"]]},
                    ).mappings()
                ]
                details_by_point_id = LiveMapServiceV3._build_details_by_point_id_v3(
                    detail_rows
                )
                points_by_quest_id = (
                    LiveMapServiceV3._build_quest_live_map_points_by_quest_id_v3(
                        quest_point_rows, details_by_point_id
                    )
                )
                points_by_objective_id = points_by_quest_id.get(quest_row["id"], {})
                for objective in quest_detail.get("objectives", []):
                    live_map_points = points_by_objective_id.get(
                        objective["objective_id"]
                    )
                    if live_map_points:
                        objective["live_map_points"] = live_map_points

                return quest_detail
        except Exception as e:
            logger.error(
                f"get_quest_detail_v3: {quest_id_or_normalized_name}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_story_detail_v3(story_id: str):
        try:
            with V3Database.SessionLocal() as s:
                story_ids = [story_id]
                story_rows = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.stories_by_story_ids_sql()),
                        {"story_ids": story_ids},
                    ).mappings()
                ]
                if not story_rows:
                    return None

                story_point_rows = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.story_points_by_story_ids_sql()),
                        {"story_ids": story_ids},
                    ).mappings()
                ]

                detail_rows = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.story_point_details_by_story_ids_sql()),
                        {"story_ids": story_ids},
                    ).mappings()
                ]
                details_by_point_id = LiveMapServiceV3._build_details_by_point_id_v3(
                    detail_rows
                )
                requirements = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.story_requirements_by_story_ids_sql()),
                        {"story_ids": story_ids},
                    ).mappings()
                ]
                requirement_items = []
                requirement_point_rows = []
                requirement_point_detail_rows = []
                if LiveMapServiceV3._has_table_v3(s, "story_requirement_items"):
                    requirement_items = [
                        dict(row)
                        for row in s.execute(
                            text(
                                LiveMapQueryV3.story_requirement_items_by_story_ids_sql()
                            ),
                            {"story_ids": story_ids},
                        ).mappings()
                    ]
                if LiveMapServiceV3._has_table_v3(
                    s, "live_map_story_requirement_points"
                ):
                    requirement_point_rows = [
                        dict(row)
                        for row in s.execute(
                            text(
                                LiveMapQueryV3.story_requirement_points_by_story_ids_sql()
                            ),
                            {"story_ids": story_ids},
                        ).mappings()
                    ]
                if LiveMapServiceV3._has_table_v3(
                    s, "live_map_story_requirement_point_details"
                ):
                    requirement_point_detail_rows = [
                        dict(row)
                        for row in s.execute(
                            text(
                                LiveMapQueryV3.story_requirement_point_details_by_story_ids_sql()
                            ),
                            {"story_ids": story_ids},
                        ).mappings()
                    ]
                requirement_point_details_by_point_id = (
                    LiveMapServiceV3._build_details_by_point_id_v3(
                        requirement_point_detail_rows
                    )
                )
                objectives = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.story_objectives_by_story_ids_sql()),
                        {"story_ids": story_ids},
                    ).mappings()
                ]
                objective_items = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.story_objective_items_by_story_ids_sql()),
                        {"story_ids": story_ids},
                    ).mappings()
                ]
                objective_reward_items = []
                objective_reward_texts = []
                reward_trader_standing = []
                reward_items = []
                if LiveMapServiceV3._has_table_v3(s, "story_objective_reward_items"):
                    objective_reward_items = [
                        dict(row)
                        for row in s.execute(
                            text(
                                LiveMapQueryV3.story_objective_reward_items_by_story_ids_sql()
                            ),
                            {"story_ids": story_ids},
                        ).mappings()
                    ]
                if LiveMapServiceV3._has_table_v3(s, "story_objective_reward_texts"):
                    objective_reward_texts = [
                        dict(row)
                        for row in s.execute(
                            text(
                                LiveMapQueryV3.story_objective_reward_texts_by_story_ids_sql()
                            ),
                            {"story_ids": story_ids},
                        ).mappings()
                    ]
                if LiveMapServiceV3._has_table_v3(s, "story_reward_trader_standing"):
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
                            text(LiveMapQueryV3.story_reward_items_by_story_ids_sql()),
                            {"story_ids": story_ids},
                        ).mappings()
                    ]

                story_info_by_id = LiveMapServiceV3._build_story_info_by_id_v3(
                    story_rows,
                    story_point_rows,
                    details_by_point_id,
                    requirements,
                    requirement_items,
                    requirement_point_rows,
                    requirement_point_details_by_point_id,
                    objectives,
                    objective_items,
                    objective_reward_items,
                    objective_reward_texts,
                    reward_trader_standing,
                    reward_items,
                )
                return story_info_by_id.get(story_id)
        except Exception as e:
            logger.error(
                f"get_story_detail_v3: {story_id}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_event_detail_v3(event_id: str):
        try:
            with V3Database.SessionLocal() as s:
                event_ids = [event_id]
                event_point_rows = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.event_points_by_event_ids_sql()),
                        {"event_ids": event_ids},
                    ).mappings()
                ]
                if not event_point_rows:
                    return None

                detail_rows = [
                    dict(row)
                    for row in s.execute(
                        text(LiveMapQueryV3.event_point_details_by_event_ids_sql()),
                        {"event_ids": event_ids},
                    ).mappings()
                ]
                details_by_point_id = LiveMapServiceV3._build_details_by_point_id_v3(
                    detail_rows
                )
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
                        text(LiveMapQueryV3.event_objective_items_by_event_ids_sql()),
                        {"event_ids": event_ids},
                    ).mappings()
                ]
                event_reward_trader_standing = []
                event_reward_items = []
                event_reward_texts = []
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
                if LiveMapServiceV3._has_table_v3(s, "live_map_event_reward_items"):
                    event_reward_items = [
                        dict(row)
                        for row in s.execute(
                            text(LiveMapQueryV3.event_reward_items_by_event_ids_sql()),
                            {"event_ids": event_ids},
                        ).mappings()
                    ]
                if LiveMapServiceV3._has_table_v3(s, "live_map_event_reward_texts"):
                    event_reward_texts = [
                        dict(row)
                        for row in s.execute(
                            text(LiveMapQueryV3.event_reward_texts_by_event_ids_sql()),
                            {"event_ids": event_ids},
                        ).mappings()
                    ]

                event_info_by_id = LiveMapServiceV3._build_event_info_by_id_v3(
                    event_point_rows,
                    event_point_rows,
                    details_by_point_id,
                    event_objectives,
                    event_objective_items,
                    event_reward_trader_standing,
                    event_reward_items,
                    event_reward_texts,
                )
                return event_info_by_id.get(event_id)
        except Exception as e:
            logger.error(
                f"get_event_detail_v3: {event_id}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_live_map_v3(normalized_name: str):
        try:
            with V3Database.SessionLocal() as s:
                map_data = (
                    s.query(MapV3)
                    .join(LiveMapFloorV3, LiveMapFloorV3.map_id == MapV3.id)
                    .filter(
                        MapV3.normalized_name == normalized_name,
                    )
                    .order_by(
                        nullslast(MapV3.is_use.desc()),
                        nullslast(MapV3.sort_order),
                        MapV3.name_en,
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
                zones_by_floor_id = {}
                if LiveMapServiceV3._has_table_v3(s, "live_map_floor_zones"):
                    floor_zones = (
                        s.query(LiveMapFloorZoneV3)
                        .filter(LiveMapFloorZoneV3.map_id == map_data.id)
                        .order_by(
                            LiveMapFloorZoneV3.floor_id,
                            nullslast(LiveMapFloorZoneV3.sort_order),
                            LiveMapFloorZoneV3.id,
                        )
                        .all()
                    )
                    for zone in floor_zones:
                        zones_by_floor_id.setdefault(zone.floor_id, []).append(
                            LiveMapServiceV3._serialize_floor_zone_v3(zone)
                        )

                static_points = (
                    s.query(LiveMapStaticPointV3)
                    .filter(
                        LiveMapStaticPointV3.map_id == map_data.id,
                        LiveMapStaticPointV3.is_use.is_(True),
                    )
                    .order_by(
                        LiveMapStaticPointV3.floor_id,
                        LiveMapStaticPointV3.category,
                        LiveMapStaticPointV3.sort_order,
                        LiveMapStaticPointV3.name_en,
                    )
                    .all()
                )
                btr_routes = LiveMapServiceV3._get_btr_routes_by_map_id_v3(
                    s, map_data.id
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
                quest_point_rows.sort(key=LiveMapServiceV3._quest_name_sort_key_v3)

                quest_points = [
                    LiveMapServiceV3._serialize_quest_point_summary_v3(
                        row, details_by_point_id.get(row["id"], [])
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

                if LiveMapServiceV3._has_table_v3(
                    s, "live_map_story_requirement_points"
                ):
                    story_point_rows.extend(
                        [
                            dict(row)
                            for row in s.execute(
                                text(
                                    LiveMapQueryV3.story_requirement_points_by_map_sql()
                                ),
                                {"map_id": map_data.id},
                            ).mappings()
                        ]
                    )
                    story_point_rows.sort(
                        key=lambda row: (
                            row["sort_order"] is None,
                            row["sort_order"] or 0,
                            row["floor_id"] is None,
                            row["floor_id"] or "",
                            row["id"] or "",
                        )
                    )

                story_points = [
                    LiveMapServiceV3._serialize_story_point_summary_v3(row)
                    for row in story_point_rows
                ]

                event_points = []
                if LiveMapServiceV3._can_query_event_points_v3(s):
                    event_point_rows = [
                        dict(row)
                        for row in s.execute(
                            text(LiveMapQueryV3.event_points_all_active_sql()),
                        ).mappings()
                    ]
                else:
                    event_point_rows = []

                event_points = [
                    LiveMapServiceV3._serialize_event_point_summary_v3(row)
                    for row in event_point_rows
                ]

                return {
                    "map_selector": LiveMapServiceV3._get_map_selector_v3(s),
                    "floors": [
                        LiveMapServiceV3._serialize_floor_v3(
                            row, zones_by_floor_id.get(row.id, [])
                        )
                        for row in floors
                    ],
                    "quest_points": quest_points,
                    "story_points": story_points,
                    "event_points": event_points,
                    "static_points": [
                        LiveMapServiceV3._serialize_static_point_v3(row)
                        for row in static_points
                    ],
                    "btr_routes": [route.model_dump() for route in btr_routes],
                }
        except Exception as e:
            logger.error(
                f"get_live_map_v3: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None
