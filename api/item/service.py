from api.item.models import (
    AmmoEfficiencyV3,
    AmmoItemV3,
    ConsumableCureV3,
    ConsumableItemV3,
    ConsumableStimEffectV3,
    ItemPenaltyV3,
    ItemV3,
    MeleeItemV3,
    ProtectionItemV3,
    StorageGridV3,
    StorageItemV3,
    ThrowableItemV3,
    UsageItemV3,
    WeaponAllowedAmmoV3,
    WeaponItemV3,
)
from database import V3Database
from sqlalchemy import or_, not_, text
import logging

logger = logging.getLogger("api.item")


class ItemServiceV3:
    ITEM_TYPE_RULES_V3 = {
        "weapon": [
            ("Weapon", None),
            ("Item", "Throwable weapon"),
            ("Item", "Knife"),
        ],
        "ammo": [("Stackable item", "Ammo")],
        "headwear": [
            ("Armored equipment", "Headwear"),
            ("Equipment", "Armored equipment"),
        ],
        "headset": [("Equipment", "Headphones")],
        "rig": [("Searchable item", "Chest rig")],
        "armor-vest": [("Armored equipment", "Armor")],
        "backpack": [("Searchable item", "Backpack")],
        "loot": [
            ("Stackable item", "Money"),
            ("Special item", None),
            ("Quest Item", "Loot"),
            ("Lubricant", None),
            ("Item", "Special item"),
            ("Item", "Map"),
            ("Item", "Info"),
            ("Item", "Flyer"),
            ("Info", "Dialog Item"),
            ("Completable", None),
            ("Barter item", None),
        ],
        "medical": [("Meds", None)],
        "provisions": [("Food and drink", None)],
        "container": [
            ("Searchable item", "Port. container"),
            ("Compound item", None),
        ],
        "key": [("Key", None)],
        "glasses": [("Armored equipment", None)],
        "face-cover": [("Armored equipment", "Face Cover")],
        "arm-band": [("Equipment", "Arm Band")],
        "tactical-accessory": [
            ("Special scope", None),
            ("Sights", None),
            ("Muzzle device", None),
            ("Magazine", None),
            ("Gear mod", None),
            ("Functional mod", None),
            ("Essential mod", None),
            ("Cylinder Magazine", "Spring Driven Cylinder"),
            ("Armored equipment", "Armor Plate"),
        ],
    }

    ITEM_TYPE_EXCLUDED_RULES_V3 = [
        ("Searchable item", "Random Loot Container"),
        ("Ammo", "Rocket"),
        ("Stackable item", "Ammo container"),
    ]

    @staticmethod
    def _serialize_item_base_v3(item: ItemV3):
        return {
            "id": item.id,
            "parent_category": item.parent_category,
            "category": item.category,
            "name_en": item.name_en,
            "name_ko": item.name_ko,
            "name_ja": item.name_ja,
            "normalized_name": item.normalized_name,
            "weight": float(item.weight) if item.weight is not None else None,
            "width": item.width,
            "height": item.height,
            "image": item.image,
        }

    @staticmethod
    def _serialize_item_list_row_v3(item: ItemV3):
        return {
            "id": item.id,
            "normalized_name": item.normalized_name,
            "name_en": item.name_en,
            "name_ko": item.name_ko,
            "name_ja": item.name_ja,
            "image": item.image,
            "width": item.width,
            "height": item.height,
        }

    @staticmethod
    def _serialize_ammo_info_v3(
        ammo_info: AmmoItemV3 | None,
        ammo_efficiency: AmmoEfficiencyV3 | None = None,
    ):
        if ammo_info is None:
            return None

        result = {
            "damage": ammo_info.damage,
            "armor_damage": ammo_info.armor_damage,
            "penetration_power": ammo_info.penetration_power,
            "recoil_modifier": (
                float(ammo_info.recoil_modifier)
                if ammo_info.recoil_modifier is not None
                else None
            ),
            "accuracy_modifier": (
                float(ammo_info.accuracy_modifier)
                if ammo_info.accuracy_modifier is not None
                else None
            ),
            "heavy_bleed_modifier": (
                float(ammo_info.heavy_bleed_modifier)
                if ammo_info.heavy_bleed_modifier is not None
                else None
            ),
            "light_bleed_modifier": (
                float(ammo_info.light_bleed_modifier)
                if ammo_info.light_bleed_modifier is not None
                else None
            ),
        }

        if ammo_efficiency is not None:
            result["efficiency"] = {
                "value_1": ammo_efficiency.value_1,
                "value_2": ammo_efficiency.value_2,
                "value_3": ammo_efficiency.value_3,
                "value_4": ammo_efficiency.value_4,
                "value_5": ammo_efficiency.value_5,
                "value_6": ammo_efficiency.value_6,
            }

        return result

    @staticmethod
    def _serialize_related_item_v3(item: ItemV3 | None):
        if item is None:
            return None

        return {
            "id": item.id,
            "name_en": item.name_en,
            "name_ko": item.name_ko,
            "name_ja": item.name_ja,
            "normalized_name": item.normalized_name,
            "image": item.image,
        }

    @staticmethod
    def _to_float_v3(value):
        return float(value) if value is not None else None

    @staticmethod
    def _serialize_quest_ref_v3(row):
        return {
            "id": row["quest_id"],
            "normalized_name": row["quest_normalized_name"],
            "name_en": row["quest_name_en"],
            "name_ko": row["quest_name_ko"],
            "name_ja": row["quest_name_ja"],
        }

    @staticmethod
    def _serialize_trader_ref_v3(row):
        if row["trader_id"] is None:
            return None
        return {
            "id": row["trader_id"],
            "normalized_name": row["trader_normalized_name"],
            "name_en": row["trader_name_en"],
            "name_ko": row["trader_name_ko"],
            "name_ja": row["trader_name_ja"],
            "image": row["trader_image"],
        }

    @staticmethod
    def _serialize_hideout_ref_v3(row):
        return {
            "id": row["hideout_id"],
            "normalized_name": row["hideout_normalized_name"],
            "name_en": row["hideout_name_en"],
            "name_ko": row["hideout_name_ko"],
            "name_ja": row["hideout_name_ja"],
            "level": row["hideout_level"],
            "level_id": row["hideout_level_id"],
        }

    @staticmethod
    def _serialize_row_item_ref_v3(row):
        return {
            "id": row["item_id"],
            "normalized_name": row["item_normalized_name"],
            "name_en": row["item_name_en"],
            "name_ko": row["item_name_ko"],
            "name_ja": row["item_name_ja"],
            "image": row["item_image"],
            "width": row["item_width"],
            "height": row["item_height"],
        }

    @staticmethod
    def _serialize_weapon_ref_v3(row):
        return {
            "id": row["weapon_id"],
            "normalized_name": row["weapon_normalized_name"],
            "name_en": row["weapon_name_en"],
            "name_ko": row["weapon_name_ko"],
            "name_ja": row["weapon_name_ja"],
            "image": row["weapon_image"],
            "width": row["weapon_width"],
            "height": row["weapon_height"],
        }

    @staticmethod
    def _group_item_detail_rows_v3(rows, key):
        grouped = {}
        for row in rows:
            row_dict = dict(row)
            grouped.setdefault(row_dict[key], []).append(row_dict)
        return grouped

    @staticmethod
    def _get_item_detail_references_v3(s, item_id: str):
        quest_requirement_rows = (
            s.execute(
                text(
                    """
                    select q.id as quest_id,
                           q.normalized_name as quest_normalized_name,
                           q.name_en as quest_name_en,
                           q.name_ko as quest_name_ko,
                           q.name_ja as quest_name_ja,
                           qo.objective_id,
                           qo.type as objective_type,
                           qo.description_en,
                           qo.description_ko,
                           qo.description_ja,
                           qo.count,
                           qo.found_in_raid,
                           qoi.item_type,
                           qoi.sort_order,
                           t.id as trader_id,
                           t.normalized_name as trader_normalized_name,
                           t.name_en as trader_name_en,
                           t.name_ko as trader_name_ko,
                           t.name_ja as trader_name_ja,
                           t.image as trader_image
                    from quest_objective_items qoi
                             join quest_objectives qo
                                  on qoi.objective_id = qo.objective_id
                                 and qo.is_use is true
                             join quests q
                                  on qo.quest_id = q.id
                                 and q.is_use is true
                             left join traders t on q.trader_id = t.id
                    where qoi.item_id = :item_id
                    union all
                    select q.id as quest_id,
                           q.normalized_name as quest_normalized_name,
                           q.name_en as quest_name_en,
                           q.name_ko as quest_name_ko,
                           q.name_ja as quest_name_ja,
                           qo.objective_id,
                           qo.type as objective_type,
                           qo.description_en,
                           qo.description_ko,
                           qo.description_ja,
                           qo.count,
                           qo.found_in_raid,
                           'requiredKey' as item_type,
                           null as sort_order,
                           t.id as trader_id,
                           t.normalized_name as trader_normalized_name,
                           t.name_en as trader_name_en,
                           t.name_ko as trader_name_ko,
                           t.name_ja as trader_name_ja,
                           t.image as trader_image
                    from quest_objective_required_keys qork
                             join quest_objectives qo
                                  on qork.objective_id = qo.objective_id
                                 and qo.is_use is true
                             join quests q
                                  on qo.quest_id = q.id
                                 and q.is_use is true
                             left join traders t on q.trader_id = t.id
                    where qork.key_id = :item_id
                    order by quest_name_en nulls last, objective_id, sort_order nulls last;
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .all()
        )

        quest_reward_rows = (
            s.execute(
                text(
                    """
                    select q.id as quest_id,
                           q.normalized_name as quest_normalized_name,
                           q.name_en as quest_name_en,
                           q.name_ko as quest_name_ko,
                           q.name_ja as quest_name_ja,
                           qfri.quantity,
                           'item' as reward_type,
                           null as offer_id,
                           null as level,
                           qfri.sort_order,
                           t.id as trader_id,
                           t.normalized_name as trader_normalized_name,
                           t.name_en as trader_name_en,
                           t.name_ko as trader_name_ko,
                           t.name_ja as trader_name_ja,
                           t.image as trader_image
                    from quest_finish_reward_items qfri
                             join quests q
                                  on qfri.quest_id = q.id
                                 and q.is_use is true
                             left join traders t on q.trader_id = t.id
                    where qfri.item_id = :item_id
                    union all
                    select q.id as quest_id,
                           q.normalized_name as quest_normalized_name,
                           q.name_en as quest_name_en,
                           q.name_ko as quest_name_ko,
                           q.name_ja as quest_name_ja,
                           null as quantity,
                           'offer_unlock' as reward_type,
                           qfrou.offer_id,
                           qfrou.level,
                           qfrou.sort_order,
                           t.id as trader_id,
                           t.normalized_name as trader_normalized_name,
                           t.name_en as trader_name_en,
                           t.name_ko as trader_name_ko,
                           t.name_ja as trader_name_ja,
                           t.image as trader_image
                    from quest_finish_reward_offer_unlock qfrou
                             join quests q
                                  on qfrou.quest_id = q.id
                                 and q.is_use is true
                             left join traders t on qfrou.trader_id = t.id
                    where qfrou.item_id = :item_id
                    order by quest_name_en nulls last, reward_type, sort_order nulls last;
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .all()
        )

        barter_rows = (
            s.execute(
                text(
                    """
                    select tb.id as barter_id,
                           tb.trader_id,
                           tb.trader_level,
                           t.normalized_name as trader_normalized_name,
                           t.name_en as trader_name_en,
                           t.name_ko as trader_name_ko,
                           t.name_ja as trader_name_ja,
                           t.image as trader_image,
                           bri.quantity as reward_quantity,
                           req.id as require_id,
                           req.quantity as require_quantity,
                           i.id as item_id,
                           i.normalized_name as item_normalized_name,
                           i.name_en as item_name_en,
                           i.name_ko as item_name_ko,
                           i.name_ja as item_name_ja,
                           i.image as item_image,
                           i.width as item_width,
                           i.height as item_height
                    from barter_reward_items bri
                             join trader_barters tb on bri.barter_id = tb.id
                             left join traders t on tb.trader_id = t.id
                             left join barter_required_items req on tb.id = req.barter_id
                             left join items i on req.item_id = i.id
                    where bri.item_id = :item_id
                    order by t.sort_order nulls last, tb.trader_level, tb.id, i.name_en nulls last;
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .all()
        )

        used_in_barter_rows = (
            s.execute(
                text(
                    """
                    select tb.id as barter_id,
                           tb.trader_id,
                           tb.trader_level,
                           t.normalized_name as trader_normalized_name,
                           t.name_en as trader_name_en,
                           t.name_ko as trader_name_ko,
                           t.name_ja as trader_name_ja,
                           t.image as trader_image,
                           target_req.quantity as target_quantity,
                           reward.id as reward_id,
                           reward.quantity as reward_quantity,
                           i.id as item_id,
                           i.normalized_name as item_normalized_name,
                           i.name_en as item_name_en,
                           i.name_ko as item_name_ko,
                           i.name_ja as item_name_ja,
                           i.image as item_image,
                           i.width as item_width,
                           i.height as item_height
                    from barter_required_items target_req
                             join trader_barters tb on target_req.barter_id = tb.id
                             left join traders t on tb.trader_id = t.id
                             left join barter_reward_items reward on tb.id = reward.barter_id
                             left join items i on reward.item_id = i.id
                    where target_req.item_id = :item_id
                    order by t.sort_order nulls last, tb.trader_level, tb.id, i.name_en nulls last;
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .all()
        )

        hideout_construction_rows = (
            s.execute(
                text(
                    """
                    select hir.id as require_id,
                           hir.quantity,
                           hir.in_raid,
                           hl.id as hideout_level_id,
                           hl.hideout_level,
                           hl.construction_time,
                           hm.id as hideout_id,
                           hm.normalized_name as hideout_normalized_name,
                           hm.name_en as hideout_name_en,
                           hm.name_ko as hideout_name_ko,
                           hm.name_ja as hideout_name_ja
                    from hideout_item_require hir
                             join hideout_levels hl on hir.hideout_level_id = hl.id
                             join hideout_master hm on hl.master_id = hm.id
                    where hir.item_id = :item_id
                    order by hm.name_en nulls last, hl.hideout_level;
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .all()
        )

        hideout_craft_rows = (
            s.execute(
                text(
                    """
                    select hc.id as craft_id,
                           hc.reward_item_id as craft_reward_item_id,
                           hc.duration,
                           hc.reward_quantity,
                           hl.id as hideout_level_id,
                           hl.hideout_level,
                           hm.id as hideout_id,
                           hm.normalized_name as hideout_normalized_name,
                           hm.name_en as hideout_name_en,
                           hm.name_ko as hideout_name_ko,
                           hm.name_ja as hideout_name_ja,
                           req.id as require_id,
                           req.quantity as require_quantity,
                           i.id as item_id,
                           i.normalized_name as item_normalized_name,
                           i.name_en as item_name_en,
                           i.name_ko as item_name_ko,
                           i.name_ja as item_name_ja,
                           i.image as item_image,
                           i.width as item_width,
                           i.height as item_height
                    from hideout_crafts hc
                             join hideout_levels hl on hc.hideout_level_id = hl.id
                             join hideout_master hm on hl.master_id = hm.id
                             left join hideout_craft_require_items req on hc.id = req.craft_id
                             left join items i on req.item_id = i.id
                    where hc.reward_item_id = :item_id
                       or exists (
                           select 1
                           from hideout_craft_require_items target_req
                           where target_req.craft_id = hc.id
                             and target_req.item_id = :item_id
                       )
                    order by hm.name_en nulls last, hl.hideout_level, hc.id, i.name_en nulls last;
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .all()
        )

        quest_craft_unlock_rows = (
            s.execute(
                text(
                    """
                    select q.id as quest_id,
                           q.normalized_name as quest_normalized_name,
                           q.name_en as quest_name_en,
                           q.name_ko as quest_name_ko,
                           q.name_ja as quest_name_ja,
                           qfrcu.craft_id,
                           qfrcu.station_level,
                           qfrcu.sort_order,
                           hc.duration,
                           hc.reward_quantity,
                           hl.id as hideout_level_id,
                           hl.hideout_level,
                           hm.id as hideout_id,
                           hm.normalized_name as hideout_normalized_name,
                           hm.name_en as hideout_name_en,
                           hm.name_ko as hideout_name_ko,
                           hm.name_ja as hideout_name_ja
                    from quest_finish_reward_craft_unlocks qfrcu
                             join quests q
                                  on qfrcu.quest_id = q.id
                                 and q.is_use is true
                             join hideout_crafts hc on qfrcu.craft_id = hc.id
                             left join hideout_levels hl on hc.hideout_level_id = hl.id
                             left join hideout_master hm on hl.master_id = hm.id
                    where hc.reward_item_id = :item_id
                    order by q.name_en nulls last, qfrcu.sort_order nulls last;
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .all()
        )

        boss_drop_rows = (
            s.execute(
                text(
                    """
                    select b.id as boss_id,
                           b.normalized_name,
                           b.name_en,
                           b.name_ko,
                           b.name_ja,
                           b.image,
                           b.is_boss,
                           b.faction,
                           bi.quantity,
                           bi.sort_order
                    from boss_item bi
                             join bosses b on bi.boss_id = b.id
                    where bi.item_id = :item_id
                    order by b.sort_order nulls last, bi.sort_order nulls last, b.name_en;
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .all()
        )

        compatible_weapon_rows = (
            s.execute(
                text(
                    """
                    select i.id as weapon_id,
                           i.normalized_name as weapon_normalized_name,
                           i.name_en as weapon_name_en,
                           i.name_ko as weapon_name_ko,
                           i.name_ja as weapon_name_ja,
                           i.image as weapon_image,
                           i.width as weapon_width,
                           i.height as weapon_height
                    from weapon_allowed_ammo waa
                             join items i on waa.item_id = i.id
                    where waa.ammo_item_id = :item_id
                    order by i.name_en;
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .all()
        )

        default_weapon_rows = (
            s.execute(
                text(
                    """
                    select i.id as weapon_id,
                           i.normalized_name as weapon_normalized_name,
                           i.name_en as weapon_name_en,
                           i.name_ko as weapon_name_ko,
                           i.name_ja as weapon_name_ja,
                           i.image as weapon_image,
                           i.width as weapon_width,
                           i.height as weapon_height
                    from weapon_items wi
                             join items i on wi.item_id = i.id
                    where wi.default_ammo_item_id = :item_id
                    order by i.name_en;
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .all()
        )

        barters = []
        for barter_id, rows in ItemServiceV3._group_item_detail_rows_v3(
            barter_rows, "barter_id"
        ).items():
            first = rows[0]
            barters.append(
                {
                    "barter_id": barter_id,
                    "reward_quantity": first["reward_quantity"],
                    "trader_level": first["trader_level"],
                    "trader": ItemServiceV3._serialize_trader_ref_v3(first),
                    "require_items": [
                        {
                            "id": row["require_id"],
                            "quantity": row["require_quantity"],
                            "item": ItemServiceV3._serialize_row_item_ref_v3(row),
                        }
                        for row in rows
                        if row["item_id"] is not None
                    ],
                }
            )

        used_in_barters = []
        for barter_id, rows in ItemServiceV3._group_item_detail_rows_v3(
            used_in_barter_rows, "barter_id"
        ).items():
            first = rows[0]
            used_in_barters.append(
                {
                    "barter_id": barter_id,
                    "require_quantity": first["target_quantity"],
                    "trader_level": first["trader_level"],
                    "trader": ItemServiceV3._serialize_trader_ref_v3(first),
                    "reward_items": [
                        {
                            "id": row["reward_id"],
                            "quantity": row["reward_quantity"],
                            "item": ItemServiceV3._serialize_row_item_ref_v3(row),
                        }
                        for row in rows
                        if row["item_id"] is not None
                    ],
                }
            )

        hideout_crafts = []
        for craft_id, rows in ItemServiceV3._group_item_detail_rows_v3(
            hideout_craft_rows, "craft_id"
        ).items():
            first = rows[0]
            is_target_reward = first["craft_reward_item_id"] == item_id
            is_target_required = any(row["item_id"] == item_id for row in rows)
            role = "reward"
            if is_target_reward and is_target_required:
                role = "reward_and_require"
            elif is_target_required:
                role = "require"

            hideout_crafts.append(
                {
                    "craft_id": craft_id,
                    "duration": ItemServiceV3._to_float_v3(first["duration"]),
                    "reward_quantity": ItemServiceV3._to_float_v3(
                        first["reward_quantity"]
                    ),
                    "role": role,
                    "hideout": ItemServiceV3._serialize_hideout_ref_v3(first),
                    "require_items": [
                        {
                            "id": row["require_id"],
                            "quantity": row["require_quantity"],
                            "item": ItemServiceV3._serialize_row_item_ref_v3(row),
                        }
                        for row in rows
                        if row["item_id"] is not None
                    ],
                }
            )

        return {
            "quest_requirements": [
                {
                    "quest": ItemServiceV3._serialize_quest_ref_v3(row),
                    "trader": ItemServiceV3._serialize_trader_ref_v3(row),
                    "objective": {
                        "objective_id": row["objective_id"],
                        "type": row["objective_type"],
                        "description_en": row["description_en"],
                        "description_ko": row["description_ko"],
                        "description_ja": row["description_ja"],
                        "count": row["count"],
                        "found_in_raid": row["found_in_raid"],
                        "item_type": row["item_type"],
                    },
                }
                for row in quest_requirement_rows
            ],
            "trader_barters": barters,
            "used_in_trader_barters": used_in_barters,
            "hideout_crafts": hideout_crafts,
            "quest_rewards": [
                {
                    "quest": ItemServiceV3._serialize_quest_ref_v3(row),
                    "trader": ItemServiceV3._serialize_trader_ref_v3(row),
                    "reward_type": row["reward_type"],
                    "quantity": row["quantity"],
                    "offer_id": row["offer_id"],
                    "level": row["level"],
                }
                for row in quest_reward_rows
            ],
            "hideout_constructions": [
                {
                    "id": row["require_id"],
                    "quantity": row["quantity"],
                    "in_raid": row["in_raid"],
                    "construction_time": row["construction_time"],
                    "hideout": ItemServiceV3._serialize_hideout_ref_v3(row),
                }
                for row in hideout_construction_rows
            ],
            "quest_craft_unlock_rewards": [
                {
                    "quest": ItemServiceV3._serialize_quest_ref_v3(row),
                    "craft_id": row["craft_id"],
                    "station_level": row["station_level"],
                    "duration": ItemServiceV3._to_float_v3(row["duration"]),
                    "reward_quantity": ItemServiceV3._to_float_v3(
                        row["reward_quantity"]
                    ),
                    "hideout": ItemServiceV3._serialize_hideout_ref_v3(row),
                }
                for row in quest_craft_unlock_rows
            ],
            "boss_drops": [
                {
                    "boss": {
                        "id": row["boss_id"],
                        "normalized_name": row["normalized_name"],
                        "name_en": row["name_en"],
                        "name_ko": row["name_ko"],
                        "name_ja": row["name_ja"],
                        "image": row["image"],
                        "is_boss": row["is_boss"],
                        "faction": row["faction"],
                    },
                    "quantity": row["quantity"],
                }
                for row in boss_drop_rows
            ],
            "compatible_weapons": [
                ItemServiceV3._serialize_weapon_ref_v3(row)
                for row in compatible_weapon_rows
            ],
            "default_for_weapons": [
                ItemServiceV3._serialize_weapon_ref_v3(row)
                for row in default_weapon_rows
            ],
        }

    @staticmethod
    def get_item_detail_v3(normalized_name: str):
        """
        v3 item 상세 조회
        """
        try:
            with V3Database.SessionLocal() as s:
                item = (
                    s.query(ItemV3)
                    .filter(ItemV3.normalized_name == normalized_name)
                    .first()
                )

                if item is None:
                    return None

                result = ItemServiceV3._serialize_item_base_v3(item)

                penalties = (
                    s.query(ItemPenaltyV3)
                    .filter(ItemPenaltyV3.item_id == item.id)
                    .first()
                )
                if penalties is not None:
                    result["penalties"] = {
                        "ergonomics_penalty": (
                            float(penalties.ergonomics_penalty)
                            if penalties.ergonomics_penalty is not None
                            else None
                        ),
                        "turn_speed_penalty": (
                            float(penalties.turn_speed_penalty)
                            if penalties.turn_speed_penalty is not None
                            else None
                        ),
                        "movement_speed_penalty": (
                            float(penalties.movement_speed_penalty)
                            if penalties.movement_speed_penalty is not None
                            else None
                        ),
                        "distance_modifier": (
                            float(penalties.distance_modifier)
                            if penalties.distance_modifier is not None
                            else None
                        ),
                    }

                weapon_info = (
                    s.query(WeaponItemV3)
                    .filter(WeaponItemV3.item_id == item.id)
                    .first()
                )
                if weapon_info is not None:
                    default_ammo = None
                    if weapon_info.default_ammo_item_id:
                        default_ammo = (
                            s.query(ItemV3)
                            .filter(ItemV3.id == weapon_info.default_ammo_item_id)
                            .first()
                        )

                    allowed_ammo_rows = (
                        s.query(ItemV3)
                        .join(
                            WeaponAllowedAmmoV3,
                            WeaponAllowedAmmoV3.ammo_item_id == ItemV3.id,
                        )
                        .filter(WeaponAllowedAmmoV3.item_id == item.id)
                        .order_by(ItemV3.name_en)
                        .all()
                    )

                    result["weapon_info"] = {
                        "caliber": weapon_info.caliber,
                        "fire_rate": weapon_info.fire_rate,
                        "ergonomics": weapon_info.ergonomics,
                        "recoil_horizontal": weapon_info.recoil_horizontal,
                        "recoil_vertical": weapon_info.recoil_vertical,
                        "default_ammo": ItemServiceV3._serialize_related_item_v3(
                            default_ammo
                        ),
                        "fire_modes": {
                            "single_fire": weapon_info.is_single_fire,
                            "full_auto": weapon_info.is_full_auto,
                            "burst_fire": weapon_info.is_burst_fire,
                            "double_action": weapon_info.is_double_action,
                            "double_tap": weapon_info.is_double_tap,
                            "semi_auto": weapon_info.is_semi_auto,
                        },
                        "allowed_ammo": [
                            ItemServiceV3._serialize_related_item_v3(ammo)
                            for ammo in allowed_ammo_rows
                        ],
                    }

                ammo_info = (
                    s.query(AmmoItemV3).filter(AmmoItemV3.item_id == item.id).first()
                )
                if ammo_info is not None:
                    ammo_efficiency = (
                        s.query(AmmoEfficiencyV3)
                        .filter(AmmoEfficiencyV3.ammo_item_id == item.id)
                        .first()
                    )

                    result["ammo_info"] = ItemServiceV3._serialize_ammo_info_v3(
                        ammo_info,
                        ammo_efficiency,
                    )

                melee_info = (
                    s.query(MeleeItemV3).filter(MeleeItemV3.item_id == item.id).first()
                )
                if melee_info is not None:
                    result["melee_info"] = {
                        "hit_radius": (
                            float(melee_info.hit_radius)
                            if melee_info.hit_radius is not None
                            else None
                        ),
                        "slash_damage": melee_info.slash_damage,
                        "stab_damage": melee_info.stab_damage,
                    }

                throwable_info = (
                    s.query(ThrowableItemV3)
                    .filter(ThrowableItemV3.item_id == item.id)
                    .first()
                )
                if throwable_info is not None:
                    result["throwable_info"] = {
                        "throwable_type": throwable_info.throwable_type,
                        "fuse": (
                            float(throwable_info.fuse)
                            if throwable_info.fuse is not None
                            else None
                        ),
                        "fragments": throwable_info.fragments,
                        "contusion_radius": (
                            float(throwable_info.contusion_radius)
                            if throwable_info.contusion_radius is not None
                            else None
                        ),
                        "min_explosion_distance": (
                            float(throwable_info.min_explosion_distance)
                            if throwable_info.min_explosion_distance is not None
                            else None
                        ),
                        "max_explosion_distance": (
                            float(throwable_info.max_explosion_distance)
                            if throwable_info.max_explosion_distance is not None
                            else None
                        ),
                    }

                storage_info = (
                    s.query(StorageItemV3)
                    .filter(StorageItemV3.item_id == item.id)
                    .first()
                )
                if storage_info is not None:
                    grids = (
                        s.query(StorageGridV3)
                        .filter(StorageGridV3.item_id == item.id)
                        .order_by(StorageGridV3.grid_index)
                        .all()
                    )
                    result["storage_info"] = {
                        "storage_type": storage_info.storage_type,
                        "capacity": storage_info.capacity,
                        "grids": [
                            {
                                "grid_index": grid.grid_index,
                                "width": grid.width,
                                "height": grid.height,
                            }
                            for grid in grids
                        ],
                    }

                protection_info = (
                    s.query(ProtectionItemV3)
                    .filter(ProtectionItemV3.item_id == item.id)
                    .first()
                )
                if protection_info is not None:
                    result["protection_info"] = {
                        "protection_type": protection_info.protection_type,
                        "armor_class": protection_info.armor_class,
                        "durability": protection_info.durability,
                        "material": protection_info.material,
                        "ricochet_y": (
                            float(protection_info.ricochet_y)
                            if protection_info.ricochet_y is not None
                            else None
                        ),
                        "deafening": protection_info.deafening,
                        "blindness_protection": (
                            float(protection_info.blindness_protection)
                            if protection_info.blindness_protection is not None
                            else None
                        ),
                        "zones": {
                            "head_top": protection_info.is_head_top,
                            "head_nape": protection_info.is_head_nape,
                            "head_ears": protection_info.is_head_ears,
                            "head_face": protection_info.is_head_face,
                            "head_jaws": protection_info.is_head_jaws,
                            "head_eyes": protection_info.is_head_eyes,
                            "thorax_throat": protection_info.is_thorax_throat,
                            "thorax_neck": protection_info.is_thorax_neck,
                            "thorax": protection_info.is_thorax,
                            "upper_back": protection_info.is_upper_back,
                            "stomach": protection_info.is_stomach,
                            "left_side": protection_info.is_left_side,
                            "right_side": protection_info.is_right_side,
                            "lower_back": protection_info.is_lower_back,
                            "groin": protection_info.is_groin,
                            "buttocks": protection_info.is_buttocks,
                            "left_shoulder": protection_info.is_left_shoulder,
                            "right_shoulder": protection_info.is_right_shoulder,
                            "front_plate": protection_info.is_front_plate,
                            "back_plate": protection_info.is_back_plate,
                            "left_plate": protection_info.is_left_plate,
                            "right_plate": protection_info.is_right_plate,
                            "side_plate": protection_info.is_side_plate,
                        },
                    }

                consumable_info = (
                    s.query(ConsumableItemV3)
                    .filter(ConsumableItemV3.item_id == item.id)
                    .first()
                )
                if consumable_info is not None:
                    cures = (
                        s.query(ConsumableCureV3)
                        .filter(ConsumableCureV3.item_id == item.id)
                        .order_by(ConsumableCureV3.cure)
                        .all()
                    )
                    stim_effects = (
                        s.query(ConsumableStimEffectV3)
                        .filter(ConsumableStimEffectV3.item_id == item.id)
                        .order_by(ConsumableStimEffectV3.effect_index)
                        .all()
                    )

                    result["consumable_info"] = {
                        "consumable_type": consumable_info.consumable_type,
                        "energy": consumable_info.energy,
                        "hydration": consumable_info.hydration,
                        "units": consumable_info.units,
                        "use_time": (
                            float(consumable_info.use_time)
                            if consumable_info.use_time is not None
                            else None
                        ),
                        "hitpoints": consumable_info.hitpoints,
                        "painkiller_duration": consumable_info.painkiller_duration,
                        "energy_impact": consumable_info.energy_impact,
                        "hydration_impact": consumable_info.hydration_impact,
                        "cures": [row.cure for row in cures],
                        "stim_effects": [
                            {
                                "effect_index": effect.effect_index,
                                "effect_type": effect.effect_type,
                                "value": (
                                    float(effect.value)
                                    if effect.value is not None
                                    else None
                                ),
                                "delay": effect.delay,
                                "duration": effect.duration,
                                "skill_name": effect.skill_name,
                            }
                            for effect in stim_effects
                        ],
                    }

                usage_info = (
                    s.query(UsageItemV3).filter(UsageItemV3.item_id == item.id).first()
                )
                if usage_info is not None:
                    result["usage_info"] = {"max_uses": usage_info.max_uses}

                result.update(
                    ItemServiceV3._get_item_detail_references_v3(s, item.id)
                )

                return result
        except Exception as e:
            logger.error(
                f"get_item_detail_v3: {normalized_name}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_item_list_v3(item_type: str):
        """
        v3 item 목록 조회
        """
        try:
            rules = ItemServiceV3.ITEM_TYPE_RULES_V3.get(item_type)
            if rules is None:
                return None

            include_conditions = []
            for parent_category, category in rules:
                if category is None:
                    include_conditions.append(ItemV3.parent_category == parent_category)
                else:
                    include_conditions.append(
                        (ItemV3.parent_category == parent_category)
                        & (ItemV3.category == category)
                    )

            exclude_conditions = [
                (ItemV3.parent_category == parent_category)
                & (ItemV3.category == category)
                for parent_category, category in ItemServiceV3.ITEM_TYPE_EXCLUDED_RULES_V3
            ]

            with V3Database.SessionLocal() as s:
                query = (
                    s.query(
                        ItemV3.id,
                        ItemV3.normalized_name,
                        ItemV3.name_en,
                        ItemV3.name_ko,
                        ItemV3.name_ja,
                        ItemV3.image,
                        ItemV3.width,
                        ItemV3.height,
                    )
                    .filter(or_(*include_conditions))
                    .order_by(ItemV3.name_en)
                )

                if exclude_conditions:
                    query = query.filter(not_(or_(*exclude_conditions)))

                items = query.all()

                if item_type != "ammo":
                    return [
                        {
                            "id": item.id,
                            "normalized_name": item.normalized_name,
                            "name_en": item.name_en,
                            "name_ko": item.name_ko,
                            "name_ja": item.name_ja,
                            "image": item.image,
                            "width": item.width,
                            "height": item.height,
                        }
                        for item in items
                    ]

                item_ids = [item.id for item in items]
                ammo_info_by_item_id = {}
                ammo_efficiency_by_item_id = {}

                if item_ids:
                    ammo_infos = (
                        s.query(AmmoItemV3)
                        .filter(AmmoItemV3.item_id.in_(item_ids))
                        .all()
                    )
                    ammo_info_by_item_id = {
                        ammo_info.item_id: ammo_info for ammo_info in ammo_infos
                    }

                    ammo_efficiencies = (
                        s.query(AmmoEfficiencyV3)
                        .filter(AmmoEfficiencyV3.ammo_item_id.in_(item_ids))
                        .all()
                    )
                    ammo_efficiency_by_item_id = {
                        ammo_efficiency.ammo_item_id: ammo_efficiency
                        for ammo_efficiency in ammo_efficiencies
                    }

                result = []
                for item in items:
                    item_data = {
                        "id": item.id,
                        "normalized_name": item.normalized_name,
                        "name_en": item.name_en,
                        "name_ko": item.name_ko,
                        "name_ja": item.name_ja,
                        "image": item.image,
                        "width": item.width,
                        "height": item.height,
                    }
                    item_data["ammo_info"] = ItemServiceV3._serialize_ammo_info_v3(
                        ammo_info_by_item_id.get(item.id),
                        ammo_efficiency_by_item_id.get(item.id),
                    )
                    result.append(item_data)

                return result
        except Exception as e:
            logger.error(
                f"get_item_list_v3: {item_type}, error: {e}",
                exc_info=True,
            )
            return None
