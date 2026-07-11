from sqlalchemy import BOOLEAN, INTEGER, TEXT, TIMESTAMP, Column

from database import V3Database


class KordBreachModifierV3(V3Database.Base):
    __tablename__ = "kord_breach_modifier"

    id = Column(TEXT, primary_key=True)
    modifier_category = Column(TEXT)
    name_en = Column(TEXT)
    name_ko = Column(TEXT)
    name_ja = Column(TEXT)
    effect_en = Column(TEXT)
    effect_ko = Column(TEXT)
    effect_ja = Column(TEXT)
    score = Column(INTEGER)
    icon_url = Column(TEXT)
    sort_order = Column(INTEGER)
    is_active = Column(BOOLEAN)
    update_time = Column(TIMESTAMP)


class KordBreachModifierConflictV3(V3Database.Base):
    __tablename__ = "kord_breach_modifier_conflict"

    modifier_id = Column(TEXT, primary_key=True)
    conflict_modifier_id = Column(TEXT, primary_key=True)
    reason = Column(TEXT)
    update_time = Column(TIMESTAMP)


class UserKordBreachPresetV3(V3Database.Base):
    __tablename__ = "user_kord_breach_preset"

    email = Column(TEXT, primary_key=True)
    slot_no = Column(INTEGER, primary_key=True)
    name = Column(TEXT)
    total_score = Column(INTEGER)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)


class UserKordBreachPresetModifierV3(V3Database.Base):
    __tablename__ = "user_kord_breach_preset_modifier"

    email = Column(TEXT, primary_key=True)
    slot_no = Column(INTEGER, primary_key=True)
    modifier_id = Column(TEXT, primary_key=True)
    sort_order = Column(INTEGER)
    create_time = Column(TIMESTAMP)
