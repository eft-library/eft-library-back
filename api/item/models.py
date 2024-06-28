from sqlalchemy import Column, TEXT, TIMESTAMP, JSON, ARRAY, INTEGER, NUMERIC
from database import DataBaseConnector


class Headset(DataBaseConnector.Base):
    """
    Headset
    """

    __tablename__ = "tkl_headset"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    image = Column(TEXT)
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
    update_time = Column(TIMESTAMP)


class Container(DataBaseConnector.Base):
    """
    Container
    """

    __tablename__ = "tkl_container"

    id = Column(TEXT, primary_key=True)
    name = Column(TEXT)
    short_name = Column(TEXT)
    grids = Column(JSON)
    capacity = Column(INTEGER)
    image = Column(TEXT)
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
    category_en = Column(TEXT)
    category_kr = Column(TEXT)
    update_time = Column(TIMESTAMP)
