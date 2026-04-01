from sqlalchemy import BOOLEAN, Column, INTEGER, NUMERIC, TEXT, TIMESTAMP, JSON
from database import DataBaseConnector, V3Database


class Item(DataBaseConnector.Base):
    """
    Item
    """

    __tablename__ = "item_i18n"

    id = Column(TEXT, primary_key=True)
    name = Column(JSON)
    image_width = Column(NUMERIC)
    image_height = Column(NUMERIC)
    url_mapping = Column(TEXT)
    category = Column(TEXT)
    image = Column(TEXT)
    info = Column(JSON)
    update_time = Column(TIMESTAMP)


class ItemV3(V3Database.Base):
    __tablename__ = "items"

    id = Column(TEXT, primary_key=True)
    parent_category = Column(TEXT)
    category = Column(TEXT)
    name_en = Column(TEXT)
    name_ko = Column(TEXT)
    name_ja = Column(TEXT)
    normalized_name = Column(TEXT)
    weight = Column(NUMERIC)
    width = Column(INTEGER)
    height = Column(INTEGER)
    image = Column(TEXT)
    update_time = Column(TIMESTAMP)


class ItemPenaltyV3(V3Database.Base):
    __tablename__ = "item_penalties"

    item_id = Column(TEXT, primary_key=True)
    ergonomics_penalty = Column(NUMERIC)
    turn_speed_penalty = Column(NUMERIC)
    movement_speed_penalty = Column(NUMERIC)
    distance_modifier = Column(NUMERIC)


class WeaponItemV3(V3Database.Base):
    __tablename__ = "weapon_items"

    item_id = Column(TEXT, primary_key=True)
    caliber = Column(TEXT)
    fire_rate = Column(INTEGER)
    ergonomics = Column(INTEGER)
    recoil_horizontal = Column(INTEGER)
    recoil_vertical = Column(INTEGER)
    default_ammo_item_id = Column(TEXT)
    is_single_fire = Column(BOOLEAN)
    is_full_auto = Column(BOOLEAN)
    is_burst_fire = Column(BOOLEAN)
    is_double_action = Column(BOOLEAN)
    is_double_tap = Column(BOOLEAN)
    is_semi_auto = Column(BOOLEAN)


class WeaponAllowedAmmoV3(V3Database.Base):
    __tablename__ = "weapon_allowed_ammo"

    item_id = Column(TEXT, primary_key=True)
    ammo_item_id = Column(TEXT, primary_key=True)


class AmmoItemV3(V3Database.Base):
    __tablename__ = "ammo_items"

    item_id = Column(TEXT, primary_key=True)
    damage = Column(INTEGER)
    armor_damage = Column(INTEGER)
    penetration_power = Column(INTEGER)
    recoil_modifier = Column(NUMERIC)
    accuracy_modifier = Column(NUMERIC)
    heavy_bleed_modifier = Column(NUMERIC)
    light_bleed_modifier = Column(NUMERIC)


class AmmoEfficiencyV3(V3Database.Base):
    __tablename__ = "ammo_efficiency"

    ammo_item_id = Column(TEXT, primary_key=True)
    value_1 = Column(INTEGER)
    value_2 = Column(INTEGER)
    value_3 = Column(INTEGER)
    value_4 = Column(INTEGER)
    value_5 = Column(INTEGER)
    value_6 = Column(INTEGER)


class MeleeItemV3(V3Database.Base):
    __tablename__ = "melee_items"

    item_id = Column(TEXT, primary_key=True)
    hit_radius = Column(NUMERIC)
    slash_damage = Column(INTEGER)
    stab_damage = Column(INTEGER)


class ThrowableItemV3(V3Database.Base):
    __tablename__ = "throwable_items"

    item_id = Column(TEXT, primary_key=True)
    throwable_type = Column(TEXT)
    fuse = Column(NUMERIC)
    fragments = Column(INTEGER)
    contusion_radius = Column(NUMERIC)
    min_explosion_distance = Column(NUMERIC)
    max_explosion_distance = Column(NUMERIC)


class StorageItemV3(V3Database.Base):
    __tablename__ = "storage_items"

    item_id = Column(TEXT, primary_key=True)
    storage_type = Column(TEXT)
    capacity = Column(INTEGER)


class StorageGridV3(V3Database.Base):
    __tablename__ = "storage_grids"

    item_id = Column(TEXT, primary_key=True)
    grid_index = Column(INTEGER, primary_key=True)
    width = Column(INTEGER)
    height = Column(INTEGER)


class ProtectionItemV3(V3Database.Base):
    __tablename__ = "protection_items"

    item_id = Column(TEXT, primary_key=True)
    protection_type = Column(TEXT)
    armor_class = Column(INTEGER)
    durability = Column(INTEGER)
    material = Column(TEXT)
    ricochet_y = Column(NUMERIC)
    deafening = Column(TEXT)
    blindness_protection = Column(NUMERIC)
    is_head_top = Column(BOOLEAN)
    is_head_nape = Column(BOOLEAN)
    is_head_ears = Column(BOOLEAN)
    is_head_face = Column(BOOLEAN)
    is_head_jaws = Column(BOOLEAN)
    is_head_eyes = Column(BOOLEAN)
    is_thorax_throat = Column(BOOLEAN)
    is_thorax_neck = Column(BOOLEAN)
    is_thorax = Column(BOOLEAN)
    is_upper_back = Column(BOOLEAN)
    is_stomach = Column(BOOLEAN)
    is_left_side = Column(BOOLEAN)
    is_right_side = Column(BOOLEAN)
    is_lower_back = Column(BOOLEAN)
    is_groin = Column(BOOLEAN)
    is_buttocks = Column(BOOLEAN)
    is_left_shoulder = Column(BOOLEAN)
    is_right_shoulder = Column(BOOLEAN)
    is_front_plate = Column(BOOLEAN)
    is_back_plate = Column(BOOLEAN)
    is_left_plate = Column(BOOLEAN)
    is_right_plate = Column(BOOLEAN)
    is_side_plate = Column(BOOLEAN)


class ConsumableItemV3(V3Database.Base):
    __tablename__ = "consumable_items"

    item_id = Column(TEXT, primary_key=True)
    consumable_type = Column(TEXT)
    energy = Column(INTEGER)
    hydration = Column(INTEGER)
    units = Column(INTEGER)
    use_time = Column(NUMERIC)
    hitpoints = Column(INTEGER)
    painkiller_duration = Column(INTEGER)
    energy_impact = Column(INTEGER)
    hydration_impact = Column(INTEGER)


class ConsumableCureV3(V3Database.Base):
    __tablename__ = "consumable_cures"

    item_id = Column(TEXT, primary_key=True)
    cure = Column(TEXT, primary_key=True)


class ConsumableStimEffectV3(V3Database.Base):
    __tablename__ = "consumable_stim_effects"

    item_id = Column(TEXT, primary_key=True)
    effect_index = Column(INTEGER, primary_key=True)
    effect_type = Column(TEXT)
    value = Column(NUMERIC)
    delay = Column(INTEGER)
    duration = Column(INTEGER)
    skill_name = Column(TEXT)


class UsageItemV3(V3Database.Base):
    __tablename__ = "usage_items"

    item_id = Column(TEXT, primary_key=True)
    max_uses = Column(INTEGER)
