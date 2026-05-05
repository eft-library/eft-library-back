import json
import logging
from typing import Any

from psycopg2.extras import Json
from sqlalchemy import text

from database import DataBaseConnector, V3Database


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration.story")


SELECT_EXTRACTION_SQL = text(
    """
    select
        id,
        name,
        always_available,
        single_use,
        image,
        faction,
        map,
        requirements,
        tip,
        update_time
    from extraction_i18n
    order by id;
    """
)


SELECT_TRANSIT_SQL = text(
    """
    select
        id,
        name,
        always_available,
        single_use,
        image,
        faction,
        map,
        requirements,
        tip,
        update_time
    from transit_i18n
    order by id;
    """
)


SELECT_MAIN_CONTENTS_SQL = text(
    """
    select
        value,
        name,
        link,
        "order" as sort_order,
        image,
        update_time
    from main_i18n
    order by "order", value;
    """
)


SELECT_MENU_GROUPS_SQL = text(
    """
    select
        value,
        name,
        "order" as sort_order,
        update_time
    from menu_group_i18n
    order by "order", value;
    """
)


SELECT_MENU_SUB_GROUPS_SQL = text(
    """
    select
        value,
        name,
        parent_value,
        link,
        "order" as sort_order,
        update_time
    from menu_sub_group_i18n
    order by parent_value, "order", value;
    """
)


SELECT_ROADMAP_NODE_SQL = text(
    """
    select
        id,
        total_x_coordinate,
        total_y_coordinate,
        single_x_coordinate,
        single_y_coordinate,
        total_kappa_x_coordinate,
        total_kappa_y_coordinate,
        single_kappa_x_coordinate,
        single_kappa_y_coordinate,
        update_time
    from roadmap_node
    order by id;
    """
)


SELECT_ROADMAP_EDGE_SQL = text(
    """
    select
        id,
        source_id,
        target_id,
        update_time
    from roadmap_edge
    order by id;
    """
)


SELECT_PROGRESS_ITEM_SQL = text(
    """
    select
        id,
        progress_type,
        update_time
    from progress_item_i18n
    order by progress_type, id;
    """
)


SELECT_INFORMATION_SQL = text(
    """
    select
        id,
        type,
        name,
        description,
        update_time
    from information_i18n
    order by type, update_time desc, id;
    """
)


SELECT_WIPE_SQL = text(
    """
    select
        id,
        patch_version,
        season_start,
        season_end,
        create_time
    from wipe_i18n
    order by id;
    """
)


SELECT_QUEST_GUIDE_SQL = text(
    """
    select
        id,
        guide,
        "order" as sort_order,
        update_time
    from quest_i18n
    order by "order", id;
    """
)


SELECT_QUEST_OBJECTIVES_SQL = text(
    """
    select
        id,
        objectives
    from quest_i18n
    where objectives is not null
    order by id;
    """
)


SELECT_STORY_SQL = text(
    """
    select
        id,
        name,
        objectives,
        requirements,
        guide,
        "order" as sort_order,
        update_time
    from story_i18n
    order by "order", id;
    """
)


SELECT_STORY_ROADMAP_SQL = text(
    """
    select
        id,
        node_type,
        title,
        contents,
        image,
        x_coordinate,
        y_coordinate,
        edge,
        node_meta,
        update_time
    from story_roadmap_i18n
    order by id;
    """
)


UPSERT_STORY_SQL = text(
    """
    insert into story (
        id,
        title_en,
        title_ko,
        title_ja,
        objectives_en,
        objectives_ko,
        objectives_ja,
        requirements_en,
        requirements_ko,
        requirements_ja,
        guide_en,
        guide_ko,
        guide_ja,
        sort_order,
        update_time
    ) values (
        :id,
        :title_en,
        :title_ko,
        :title_ja,
        :objectives_en,
        :objectives_ko,
        :objectives_ja,
        :requirements_en,
        :requirements_ko,
        :requirements_ja,
        :guide_en,
        :guide_ko,
        :guide_ja,
        :sort_order,
        :update_time
    )
    on conflict (id) do update set
        title_en = excluded.title_en,
        title_ko = excluded.title_ko,
        title_ja = excluded.title_ja,
        objectives_en = excluded.objectives_en,
        objectives_ko = excluded.objectives_ko,
        objectives_ja = excluded.objectives_ja,
        requirements_en = excluded.requirements_en,
        requirements_ko = excluded.requirements_ko,
        requirements_ja = excluded.requirements_ja,
        guide_en = excluded.guide_en,
        guide_ko = excluded.guide_ko,
        guide_ja = excluded.guide_ja,
        sort_order = excluded.sort_order,
        update_time = excluded.update_time;
    """
)


UPSERT_MAP_POINTS_SQL = text(
    """
    insert into map_points (
        id,
        point_type,
        name_en,
        name_ko,
        name_ja,
        is_unlimited_use,
        is_one_time_use,
        image,
        faction,
        map_id,
        requirements_en,
        requirements_ko,
        requirements_ja,
        tip_en,
        tip_ko,
        tip_ja,
        sort_order,
        update_time
    ) values (
        :id,
        :point_type,
        :name_en,
        :name_ko,
        :name_ja,
        :is_unlimited_use,
        :is_one_time_use,
        :image,
        :faction,
        :map_id,
        :requirements_en,
        :requirements_ko,
        :requirements_ja,
        :tip_en,
        :tip_ko,
        :tip_ja,
        :sort_order,
        :update_time
    )
    on conflict (id) do update set
        point_type = excluded.point_type,
        name_en = excluded.name_en,
        name_ko = excluded.name_ko,
        name_ja = excluded.name_ja,
        is_unlimited_use = excluded.is_unlimited_use,
        is_one_time_use = excluded.is_one_time_use,
        image = excluded.image,
        faction = excluded.faction,
        map_id = excluded.map_id,
        requirements_en = excluded.requirements_en,
        requirements_ko = excluded.requirements_ko,
        requirements_ja = excluded.requirements_ja,
        tip_en = excluded.tip_en,
        tip_ko = excluded.tip_ko,
        tip_ja = excluded.tip_ja,
        sort_order = excluded.sort_order,
        update_time = excluded.update_time;
    """
)


UPSERT_MAIN_CONTENTS_SQL = text(
    """
    insert into main_contents (
        id,
        name_en,
        name_ko,
        name_ja,
        url,
        image,
        sort_order,
        update_time
    ) values (
        :id,
        :name_en,
        :name_ko,
        :name_ja,
        :url,
        :image,
        :sort_order,
        :update_time
    )
    on conflict (id) do update set
        name_en = excluded.name_en,
        name_ko = excluded.name_ko,
        name_ja = excluded.name_ja,
        url = excluded.url,
        image = excluded.image,
        sort_order = excluded.sort_order,
        update_time = excluded.update_time;
    """
)


UPSERT_MENU_GROUPS_SQL = text(
    """
    insert into menu_groups (
        id,
        name_en,
        name_ko,
        name_ja,
        sort_order,
        update_time
    ) values (
        :id,
        :name_en,
        :name_ko,
        :name_ja,
        :sort_order,
        :update_time
    )
    on conflict (id) do update set
        name_en = excluded.name_en,
        name_ko = excluded.name_ko,
        name_ja = excluded.name_ja,
        sort_order = excluded.sort_order,
        update_time = excluded.update_time;
    """
)


UPSERT_MENU_SUB_GROUPS_SQL = text(
    """
    insert into menu_sub_groups (
        id,
        name_en,
        name_ko,
        name_ja,
        parent_group_id,
        url,
        sort_order,
        update_time
    ) values (
        :id,
        :name_en,
        :name_ko,
        :name_ja,
        :parent_group_id,
        :url,
        :sort_order,
        :update_time
    )
    on conflict (id) do update set
        name_en = excluded.name_en,
        name_ko = excluded.name_ko,
        name_ja = excluded.name_ja,
        parent_group_id = excluded.parent_group_id,
        url = excluded.url,
        sort_order = excluded.sort_order,
        update_time = excluded.update_time;
    """
)


UPSERT_ROADMAP_NODE_SQL = text(
    """
    insert into roadmap_node (
        id,
        total_x_coordinate,
        total_y_coordinate,
        single_x_coordinate,
        single_y_coordinate,
        total_kappa_x_coordinate,
        total_kappa_y_coordinate,
        single_kappa_x_coordinate,
        single_kappa_y_coordinate,
        update_time
    ) values (
        :id,
        :total_x_coordinate,
        :total_y_coordinate,
        :single_x_coordinate,
        :single_y_coordinate,
        :total_kappa_x_coordinate,
        :total_kappa_y_coordinate,
        :single_kappa_x_coordinate,
        :single_kappa_y_coordinate,
        :update_time
    )
    on conflict (id) do update set
        total_x_coordinate = excluded.total_x_coordinate,
        total_y_coordinate = excluded.total_y_coordinate,
        single_x_coordinate = excluded.single_x_coordinate,
        single_y_coordinate = excluded.single_y_coordinate,
        total_kappa_x_coordinate = excluded.total_kappa_x_coordinate,
        total_kappa_y_coordinate = excluded.total_kappa_y_coordinate,
        single_kappa_x_coordinate = excluded.single_kappa_x_coordinate,
        single_kappa_y_coordinate = excluded.single_kappa_y_coordinate,
        update_time = excluded.update_time;
    """
)


UPSERT_ROADMAP_EDGE_SQL = text(
    """
    insert into roadmap_edge (
        id,
        source_id,
        target_id,
        update_time
    ) values (
        :id,
        :source_id,
        :target_id,
        :update_time
    )
    on conflict (id) do update set
        source_id = excluded.source_id,
        target_id = excluded.target_id,
        update_time = excluded.update_time;
    """
)


UPSERT_PROGRESS_ITEM_SQL = text(
    """
    insert into progress_item (
        id,
        progress_type,
        update_time
    ) values (
        :id,
        :progress_type,
        :update_time
    )
    on conflict (id) do update set
        progress_type = excluded.progress_type,
        update_time = excluded.update_time;
    """
)


UPSERT_INFORMATION_SQL = text(
    """
    insert into information (
        id,
        information_type,
        title_en,
        title_ko,
        title_ja,
        content_en,
        content_ko,
        content_ja,
        update_time
    ) values (
        :id,
        :information_type,
        :title_en,
        :title_ko,
        :title_ja,
        :content_en,
        :content_ko,
        :content_ja,
        :update_time
    )
    on conflict (id) do update set
        information_type = excluded.information_type,
        title_en = excluded.title_en,
        title_ko = excluded.title_ko,
        title_ja = excluded.title_ja,
        content_en = excluded.content_en,
        content_ko = excluded.content_ko,
        content_ja = excluded.content_ja,
        update_time = excluded.update_time;
    """
)


UPSERT_WIPE_SQL = text(
    """
    insert into wipe (
        id,
        patch_version,
        season_start,
        season_end,
        create_time
    ) values (
        :id,
        :patch_version,
        :season_start,
        :season_end,
        :create_time
    )
    on conflict (id) do update set
        patch_version = excluded.patch_version,
        season_start = excluded.season_start,
        season_end = excluded.season_end,
        create_time = excluded.create_time;
    """
)


UPSERT_QUEST_GUIDE_SQL = text(
    """
    insert into quests (
        id,
        guide_en,
        guide_ko,
        guide_ja,
        sort_order,
        update_time
    ) values (
        :id,
        :guide_en,
        :guide_ko,
        :guide_ja,
        :sort_order,
        :update_time
    )
    on conflict (id) do update set
        guide_en = excluded.guide_en,
        guide_ko = excluded.guide_ko,
        guide_ja = excluded.guide_ja,
        sort_order = excluded.sort_order,
        update_time = excluded.update_time;
    """
)


UPSERT_QUEST_OBJECTIVES_SQL = text(
    """
    insert into quest_objectives (
        objective_id,
        quest_id,
        type,
        description_en,
        description_ko,
        description_ja,
        count,
        found_in_raid,
        sort_order
    ) values (
        :objective_id,
        :quest_id,
        :type,
        :description_en,
        :description_ko,
        :description_ja,
        :count,
        :found_in_raid,
        :sort_order
    )
    on conflict (objective_id, quest_id) do update set
        description_en = excluded.description_en,
        description_ko = excluded.description_ko,
        description_ja = excluded.description_ja;
    """
)


UPSERT_STORY_ROADMAP_SQL = text(
    """
    insert into story_roadmap (
        id,
        node_type,
        title_en,
        title_ko,
        title_ja,
        contents_en,
        contents_ko,
        contents_ja,
        desc_en,
        desc_ko,
        desc_ja,
        value_text,
        image,
        x_coordinate,
        y_coordinate,
        edge,
        update_time
    ) values (
        :id,
        :node_type,
        :title_en,
        :title_ko,
        :title_ja,
        :contents_en,
        :contents_ko,
        :contents_ja,
        :desc_en,
        :desc_ko,
        :desc_ja,
        :value_text,
        :image,
        :x_coordinate,
        :y_coordinate,
        :edge,
        :update_time
    )
    on conflict (id) do update set
        node_type = excluded.node_type,
        title_en = excluded.title_en,
        title_ko = excluded.title_ko,
        title_ja = excluded.title_ja,
        contents_en = excluded.contents_en,
        contents_ko = excluded.contents_ko,
        contents_ja = excluded.contents_ja,
        desc_en = excluded.desc_en,
        desc_ko = excluded.desc_ko,
        desc_ja = excluded.desc_ja,
        value_text = excluded.value_text,
        image = excluded.image,
        x_coordinate = excluded.x_coordinate,
        y_coordinate = excluded.y_coordinate,
        edge = excluded.edge,
        update_time = excluded.update_time;
    """
)


def get_lang_value(value: Any, lang: str) -> str | None:
    if value is None:
        return None

    if isinstance(value, dict):
        return value.get(lang)

    return str(value)


def get_meta_lang_value(node_meta: Any, keys: list[str], lang: str) -> str | None:
    if not isinstance(node_meta, dict):
        return None

    for key in keys:
        value = node_meta.get(key)
        if value is None:
            continue

        if isinstance(value, dict):
            lang_value = value.get(lang)
            if lang_value is not None:
                return lang_value
        elif lang == "en":
            return str(value)

    return None


def get_value_text(node_meta: Any) -> str | None:
    if not isinstance(node_meta, dict):
        return None

    value = node_meta.get("value")
    if value is not None:
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    value_text = node_meta.get("value_text")
    if value_text is not None:
        if isinstance(value_text, (dict, list)):
            return json.dumps(value_text, ensure_ascii=False)
        return str(value_text)

    if node_meta:
        return json.dumps(node_meta, ensure_ascii=False)

    return None


def build_story_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title_en": get_lang_value(row["name"], "en"),
        "title_ko": get_lang_value(row["name"], "ko"),
        "title_ja": get_lang_value(row["name"], "ja"),
        "objectives_en": get_lang_value(row["objectives"], "en"),
        "objectives_ko": get_lang_value(row["objectives"], "ko"),
        "objectives_ja": get_lang_value(row["objectives"], "ja"),
        "requirements_en": get_lang_value(row["requirements"], "en"),
        "requirements_ko": get_lang_value(row["requirements"], "ko"),
        "requirements_ja": get_lang_value(row["requirements"], "ja"),
        "guide_en": get_lang_value(row["guide"], "en"),
        "guide_ko": get_lang_value(row["guide"], "ko"),
        "guide_ja": get_lang_value(row["guide"], "ja"),
        "sort_order": row["sort_order"],
        "update_time": row["update_time"],
    }


def build_map_point_payload(row: dict[str, Any], point_type: str) -> dict[str, Any]:
    return {
        "id": row["id"],
        "point_type": point_type,
        "name_en": get_lang_value(row["name"], "en"),
        "name_ko": get_lang_value(row["name"], "ko"),
        "name_ja": get_lang_value(row["name"], "ja"),
        "is_unlimited_use": row["always_available"],
        "is_one_time_use": row["single_use"],
        "image": row["image"],
        "faction": row["faction"],
        "map_id": row["map"],
        "requirements_en": get_lang_value(row["requirements"], "en"),
        "requirements_ko": get_lang_value(row["requirements"], "ko"),
        "requirements_ja": get_lang_value(row["requirements"], "ja"),
        "tip_en": get_lang_value(row["tip"], "en"),
        "tip_ko": get_lang_value(row["tip"], "ko"),
        "tip_ja": get_lang_value(row["tip"], "ja"),
        "sort_order": None,
        "update_time": row["update_time"],
    }


def build_main_contents_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["value"],
        "name_en": get_lang_value(row["name"], "en"),
        "name_ko": get_lang_value(row["name"], "ko"),
        "name_ja": get_lang_value(row["name"], "ja"),
        "url": row["link"],
        "image": row["image"],
        "sort_order": row["sort_order"],
        "update_time": row["update_time"],
    }


def build_menu_group_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["value"],
        "name_en": get_lang_value(row["name"], "en"),
        "name_ko": get_lang_value(row["name"], "ko"),
        "name_ja": get_lang_value(row["name"], "ja"),
        "sort_order": row["sort_order"],
        "update_time": row["update_time"],
    }


def build_menu_sub_group_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["value"],
        "name_en": get_lang_value(row["name"], "en"),
        "name_ko": get_lang_value(row["name"], "ko"),
        "name_ja": get_lang_value(row["name"], "ja"),
        "parent_group_id": row["parent_value"],
        "url": row["link"],
        "sort_order": row["sort_order"],
        "update_time": row["update_time"],
    }


def build_roadmap_node_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "total_x_coordinate": row["total_x_coordinate"],
        "total_y_coordinate": row["total_y_coordinate"],
        "single_x_coordinate": row["single_x_coordinate"],
        "single_y_coordinate": row["single_y_coordinate"],
        "total_kappa_x_coordinate": row["total_kappa_x_coordinate"],
        "total_kappa_y_coordinate": row["total_kappa_y_coordinate"],
        "single_kappa_x_coordinate": row["single_kappa_x_coordinate"],
        "single_kappa_y_coordinate": row["single_kappa_y_coordinate"],
        "update_time": row["update_time"],
    }


def build_roadmap_edge_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "source_id": row["source_id"],
        "target_id": row["target_id"],
        "update_time": row["update_time"],
    }


def build_progress_item_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "progress_type": row["progress_type"],
        "update_time": row["update_time"],
    }


def build_information_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "information_type": row["type"],
        "title_en": get_lang_value(row["name"], "en"),
        "title_ko": get_lang_value(row["name"], "ko"),
        "title_ja": get_lang_value(row["name"], "ja"),
        "content_en": get_lang_value(row["description"], "en"),
        "content_ko": get_lang_value(row["description"], "ko"),
        "content_ja": get_lang_value(row["description"], "ja"),
        "update_time": row["update_time"],
    }


def build_wipe_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "patch_version": row["patch_version"],
        "season_start": row["season_start"],
        "season_end": row["season_end"],
        "create_time": row["create_time"],
    }


def build_quest_guide_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "guide_en": get_lang_value(row["guide"], "en"),
        "guide_ko": get_lang_value(row["guide"], "ko"),
        "guide_ja": get_lang_value(row["guide"], "ja"),
        "sort_order": row["sort_order"],
        "update_time": row["update_time"],
    }


def build_quest_objective_payload(
    quest_id: str, objective: dict[str, Any], sort_order: int
) -> dict[str, Any] | None:
    objective_id = objective.get("id")
    if objective_id is None:
        return None

    return {
        "objective_id": objective_id,
        "quest_id": quest_id,
        "type": objective.get("type"),
        "description_en": objective.get("description_en"),
        "description_ko": objective.get("description_ko"),
        "description_ja": objective.get("description_ja"),
        "count": objective.get("count"),
        "found_in_raid": objective.get("foundInRaid"),
        "sort_order": sort_order,
    }


def build_story_roadmap_payload(row: dict[str, Any]) -> dict[str, Any]:
    node_meta = row["node_meta"]

    return {
        "id": row["id"],
        "node_type": row["node_type"],
        "title_en": get_lang_value(row["title"], "en"),
        "title_ko": get_lang_value(row["title"], "ko"),
        "title_ja": get_lang_value(row["title"], "ja"),
        "contents_en": get_lang_value(row["contents"], "en"),
        "contents_ko": get_lang_value(row["contents"], "ko"),
        "contents_ja": get_lang_value(row["contents"], "ja"),
        "desc_en": get_meta_lang_value(node_meta, ["desc", "description"], "en"),
        "desc_ko": get_meta_lang_value(node_meta, ["desc", "description"], "ko"),
        "desc_ja": get_meta_lang_value(node_meta, ["desc", "description"], "ja"),
        "value_text": get_value_text(node_meta),
        "image": row["image"],
        "x_coordinate": row["x_coordinate"],
        "y_coordinate": row["y_coordinate"],
        "edge": Json(row["edge"]) if row["edge"] is not None else None,
        "update_time": row["update_time"],
    }


def migrate_map_points() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        extraction_rows = source_session.execute(SELECT_EXTRACTION_SQL).mappings().all()
        transit_rows = source_session.execute(SELECT_TRANSIT_SQL).mappings().all()

    payloads = [
        *[build_map_point_payload(dict(row), "extraction") for row in extraction_rows],
        *[build_map_point_payload(dict(row), "transit") for row in transit_rows],
    ]

    if not payloads:
        logger.info("map_points migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_MAP_POINTS_SQL, payloads)
        target_session.commit()

    logger.info("map_points migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_main_contents() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = source_session.execute(SELECT_MAIN_CONTENTS_SQL).mappings().all()

    payloads = [build_main_contents_payload(dict(row)) for row in source_rows]

    if not payloads:
        logger.info("main_contents migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_MAIN_CONTENTS_SQL, payloads)
        target_session.commit()

    logger.info("main_contents migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_menu_groups() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = source_session.execute(SELECT_MENU_GROUPS_SQL).mappings().all()

    payloads = [build_menu_group_payload(dict(row)) for row in source_rows]

    if not payloads:
        logger.info("menu_groups migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_MENU_GROUPS_SQL, payloads)
        target_session.commit()

    logger.info("menu_groups migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_menu_sub_groups() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = (
            source_session.execute(SELECT_MENU_SUB_GROUPS_SQL).mappings().all()
        )

    payloads = [build_menu_sub_group_payload(dict(row)) for row in source_rows]

    if not payloads:
        logger.info("menu_sub_groups migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_MENU_SUB_GROUPS_SQL, payloads)
        target_session.commit()

    logger.info("menu_sub_groups migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_roadmap_node() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = source_session.execute(SELECT_ROADMAP_NODE_SQL).mappings().all()

    payloads = [build_roadmap_node_payload(dict(row)) for row in source_rows]

    if not payloads:
        logger.info("roadmap_node migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_ROADMAP_NODE_SQL, payloads)
        target_session.commit()

    logger.info("roadmap_node migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_roadmap_edge() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = source_session.execute(SELECT_ROADMAP_EDGE_SQL).mappings().all()

    payloads = [build_roadmap_edge_payload(dict(row)) for row in source_rows]

    if not payloads:
        logger.info("roadmap_edge migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_ROADMAP_EDGE_SQL, payloads)
        target_session.commit()

    logger.info("roadmap_edge migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_progress_item() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = source_session.execute(SELECT_PROGRESS_ITEM_SQL).mappings().all()

    payloads = [build_progress_item_payload(dict(row)) for row in source_rows]

    if not payloads:
        logger.info("progress_item migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_PROGRESS_ITEM_SQL, payloads)
        target_session.commit()

    logger.info("progress_item migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_information() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = source_session.execute(SELECT_INFORMATION_SQL).mappings().all()

    payloads = [build_information_payload(dict(row)) for row in source_rows]

    if not payloads:
        logger.info("information migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_INFORMATION_SQL, payloads)
        target_session.commit()

    logger.info("information migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_wipe() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = source_session.execute(SELECT_WIPE_SQL).mappings().all()

    payloads = [build_wipe_payload(dict(row)) for row in source_rows]

    if not payloads:
        logger.info("wipe migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_WIPE_SQL, payloads)
        target_session.commit()

    logger.info("wipe migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_quest_guide() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = source_session.execute(SELECT_QUEST_GUIDE_SQL).mappings().all()

    payloads = [build_quest_guide_payload(dict(row)) for row in source_rows]

    if not payloads:
        logger.info("quest guide migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_QUEST_GUIDE_SQL, payloads)
        target_session.commit()

    logger.info("quest guide migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_quest_objectives_i18n() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = (
            source_session.execute(SELECT_QUEST_OBJECTIVES_SQL).mappings().all()
        )

    payloads = []
    for row in source_rows:
        quest_id = row["id"]
        objectives = row["objectives"] or []

        if not isinstance(objectives, list):
            continue

        for sort_order, objective in enumerate(objectives, start=1):
            if not isinstance(objective, dict):
                continue

            payload = build_quest_objective_payload(quest_id, objective, sort_order)
            if payload is not None:
                payloads.append(payload)

    if not payloads:
        logger.info("quest objectives i18n migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_QUEST_OBJECTIVES_SQL, payloads)
        target_session.commit()

    logger.info("quest objectives i18n migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_story() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = source_session.execute(SELECT_STORY_SQL).mappings().all()

    payloads = [build_story_payload(dict(row)) for row in source_rows]

    if not payloads:
        logger.info("story migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_STORY_SQL, payloads)
        target_session.commit()

    logger.info("story migration completed: %s rows", len(payloads))
    return len(payloads)


def migrate_story_roadmap() -> int:
    with DataBaseConnector.SessionLocal() as source_session:
        source_rows = source_session.execute(SELECT_STORY_ROADMAP_SQL).mappings().all()

    payloads = [build_story_roadmap_payload(dict(row)) for row in source_rows]

    if not payloads:
        logger.info("story_roadmap migration skipped: no source rows")
        return 0

    with V3Database.SessionLocal() as target_session:
        target_session.execute(UPSERT_STORY_ROADMAP_SQL, payloads)
        target_session.commit()

    logger.info("story_roadmap migration completed: %s rows", len(payloads))
    return len(payloads)


def main() -> None:
    map_points_count = migrate_map_points()
    main_contents_count = migrate_main_contents()
    menu_groups_count = migrate_menu_groups()
    menu_sub_groups_count = migrate_menu_sub_groups()
    roadmap_node_count = migrate_roadmap_node()
    roadmap_edge_count = migrate_roadmap_edge()
    progress_item_count = migrate_progress_item()
    information_count = migrate_information()
    wipe_count = migrate_wipe()
    quest_guide_count = migrate_quest_guide()
    quest_objectives_i18n_count = migrate_quest_objectives_i18n()
    story_count = migrate_story()
    roadmap_count = migrate_story_roadmap()
    logger.info(
        "migration finished: map_points=%s, main_contents=%s, menu_groups=%s, menu_sub_groups=%s, roadmap_node=%s, roadmap_edge=%s, progress_item=%s, information=%s, wipe=%s, quest_guide=%s, quest_objectives_i18n=%s, story=%s, story_roadmap=%s",
        map_points_count,
        main_contents_count,
        menu_groups_count,
        menu_sub_groups_count,
        roadmap_node_count,
        roadmap_edge_count,
        progress_item_count,
        information_count,
        wipe_count,
        quest_guide_count,
        quest_objectives_i18n_count,
        story_count,
        roadmap_count,
    )


if __name__ == "__main__":
    main()
