from sqlalchemy import Column, TEXT, TIMESTAMP, JSON, ARRAY, INTEGER, NUMERIC, Integer
from database import DataBaseConnector


class Item(DataBaseConnector.Base):
    """
    Item
    """

    __tablename__ = "tkl_item"

    id = Column(TEXT, primary_key=True)
    name_en = Column(TEXT)
    name_kr = Column(TEXT)
    category = Column(TEXT)
    image = Column(TEXT)
    info = Column(JSON)
    image_width = Column(NUMERIC)
    image_height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)

class Weapon(DataBaseConnector.Base):
    """
    Weapon Gun
    """

    __tablename__ = "tkl_weapon"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
    category = Column(TEXT)
    carliber = Column(TEXT)
    default_ammo = Column(TEXT)
    modes_en = Column(ARRAY(TEXT))
    modes_kr = Column(ARRAY(TEXT))
    fire_rate = Column(Integer)
    ergonomics = Column(Integer)
    recoil_vertical = Column(Integer)
    recoil_horizontal = Column(Integer)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Knife(DataBaseConnector.Base):
    """
    Weapon Knife
    """

    __tablename__ = "tkl_knife"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
    category = Column(TEXT)
    slash_damage = Column(Integer)
    stab_damage = Column(Integer)
    hit_radius = Column(NUMERIC)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Throwable(DataBaseConnector.Base):
    """
    Weapon Throwable
    """

    __tablename__ = "tkl_throwable"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
    category = Column(TEXT)
    fuse = Column(NUMERIC)
    min_fuse = Column(NUMERIC)
    min_explosion_distance = Column(Integer)
    max_explosion_distance = Column(Integer)
    fragments = Column(Integer)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Headset(DataBaseConnector.Base):
    """
    Headset
    """

    __tablename__ = "tkl_headset"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Headwear(DataBaseConnector.Base):
    """
    Headwear
    """

    __tablename__ = "tkl_headwear"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    class_value = Column(TEXT)
    areas_en = Column(ARRAY(TEXT))
    areas_kr = Column(ARRAY(TEXT))
    durability = Column(INTEGER)
    ricochet_chance = Column(NUMERIC)
    weight = Column(NUMERIC)
    image = Column(TEXT)
    ricochet_str_kr = Column(TEXT)
    ricochet_str_en = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class ArmorVest(DataBaseConnector.Base):
    """
    ArmorVest
    """

    __tablename__ = "tkl_armor_vest"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    class_value = Column(TEXT)
    areas_en = Column(ARRAY(TEXT))
    areas_kr = Column(ARRAY(TEXT))
    durability = Column(INTEGER)
    weight = Column(NUMERIC)
    image = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Rig(DataBaseConnector.Base):
    """
    Rig
    """

    __tablename__ = "tkl_rig"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    class_value = Column(TEXT)
    areas_en = Column(ARRAY(TEXT))
    areas_kr = Column(ARRAY(TEXT))
    durability = Column(INTEGER)
    capacity = Column(INTEGER)
    weight = Column(NUMERIC)
    image = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Provisions(DataBaseConnector.Base):
    """
    Provisions
    """

    __tablename__ = "tkl_provisions"

    id = Column(TEXT, primary_key=True)
    name_en = Column(TEXT)
    name_kr = Column(TEXT)
    short_name = Column(TEXT)
    category = Column(TEXT)
    energy = Column(INTEGER)
    hydration = Column(INTEGER)
    stim_effects = Column(JSON)
    image = Column(TEXT)
    notes = Column(JSON)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Backpack(DataBaseConnector.Base):
    """
    Backpack
    """

    __tablename__ = "tkl_backpack"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    grids = Column(JSON)
    capacity = Column(INTEGER)
    weight = Column(NUMERIC)
    image = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Container(DataBaseConnector.Base):
    """
    Container
    """

    __tablename__ = "tkl_container"

    id = Column(TEXT, primary_key=True)
    name_en = Column(TEXT)
    name_kr = Column(TEXT)
    short_name = Column(TEXT)
    grids = Column(JSON)
    capacity = Column(INTEGER)
    image = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Key(DataBaseConnector.Base):
    """
    Key
    """

    __tablename__ = "tkl_key"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    uses = Column(INTEGER)
    use_map_en = Column(ARRAY(TEXT))
    use_map_kr = Column(ARRAY(TEXT))
    map_value = Column(ARRAY(TEXT))
    image = Column(TEXT)
    notes = Column(JSON)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Medical(DataBaseConnector.Base):
    """
    Medical
    """

    __tablename__ = "tkl_medical"

    id = Column(TEXT, primary_key=True)
    name_en = Column(TEXT)
    name_kr = Column(TEXT)
    short_name = Column(TEXT)
    cures_en = Column(ARRAY(TEXT))
    cures_kr = Column(ARRAY(TEXT))
    category = Column(TEXT)
    buff = Column(JSON)
    debuff = Column(JSON)
    use_time = Column(INTEGER)
    uses = Column(INTEGER)
    energy_impact = Column(INTEGER)
    hydration_impact = Column(INTEGER)
    painkiller_duration = Column(INTEGER)
    hitpoints = Column(INTEGER)
    image = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Ammo(DataBaseConnector.Base):
    """
    Ammo
    """

    __tablename__ = "tkl_ammo"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    category = Column(TEXT)
    round = Column(TEXT)
    damage = Column(INTEGER)
    penetration_power = Column(INTEGER)
    armor_damage = Column(INTEGER)
    accuracy_modifier = Column(NUMERIC)
    recoil_modifier = Column(NUMERIC)
    light_bleed_modifier = Column(NUMERIC)
    heavy_bleed_modifier = Column(NUMERIC)
    efficiency = Column(ARRAY(INTEGER))
    image = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Loot(DataBaseConnector.Base):
    """
    Loot
    """

    __tablename__ = "tkl_loot"

    id = Column(TEXT, primary_key=True)
    name_en = Column(TEXT)
    name_kr = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
    notes = Column(JSON)
    category = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class FaceCover(DataBaseConnector.Base):
    """
    FaceCover
    """

    __tablename__ = "tkl_face_cover"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    class_value = Column(TEXT)
    areas_en = Column(ARRAY(TEXT))
    areas_kr = Column(ARRAY(TEXT))
    durability = Column(INTEGER)
    ricochet_chance = Column(NUMERIC)
    weight = Column(NUMERIC)
    image = Column(TEXT)
    ricochet_str_kr = Column(TEXT)
    ricochet_str_en = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class ArmBand(DataBaseConnector.Base):
    """
    Arm band
    """

    __tablename__ = "tkl_arm_band"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    weight = Column(NUMERIC)
    image = Column(TEXT)
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)


class Glasses(DataBaseConnector.Base):
    """
    Glasses
    """

    __tablename__ = "tkl_glasses"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    class_value = Column(INTEGER)
    durability = Column(INTEGER)
    blindness_protection = Column(NUMERIC)
    image = Column(TEXT)
    related_quests = Column(ARRAY(TEXT))
    width = Column(NUMERIC)
    height = Column(NUMERIC)
    update_time = Column(TIMESTAMP)
