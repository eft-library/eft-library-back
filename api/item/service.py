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
from sqlalchemy import or_, not_
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

                    result["ammo_info"] = {
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
                        result["ammo_info"]["efficiency"] = {
                            "value_1": ammo_efficiency.value_1,
                            "value_2": ammo_efficiency.value_2,
                            "value_3": ammo_efficiency.value_3,
                            "value_4": ammo_efficiency.value_4,
                            "value_5": ammo_efficiency.value_5,
                            "value_6": ammo_efficiency.value_6,
                        }

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
        except Exception as e:
            logger.error(
                f"get_item_list_v3: {item_type}, error: {e}",
                exc_info=True,
            )
            return None
