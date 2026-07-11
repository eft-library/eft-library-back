import logging
import random
from collections import defaultdict
from datetime import datetime
from typing import Iterable

from sqlalchemy import delete, text
from sqlalchemy.dialects.postgresql import insert

from api.kord_breach.models import (
    KordBreachModifierConflictV3,
    KordBreachModifierV3,
    UserKordBreachPresetModifierV3,
    UserKordBreachPresetV3,
)
from api.kord_breach.req_models import (
    DeleteKordBreachPresetV3,
    SaveKordBreachPresetV3,
)
from database import V3Database

logger = logging.getLogger("api.kord_breach")


class KordBreachServiceV3:
    @staticmethod
    def _serialize_modifier_v3(modifier: KordBreachModifierV3):
        return {
            "id": modifier.id,
            "category": modifier.modifier_category,
            "nameEn": modifier.name_en,
            "nameKo": modifier.name_ko,
            "nameJa": modifier.name_ja,
            "effect": modifier.effect_ko or modifier.effect_en or modifier.effect_ja,
            "effectEn": modifier.effect_en,
            "effectKo": modifier.effect_ko,
            "effectJa": modifier.effect_ja,
            "score": modifier.score or 0,
            "iconUrl": modifier.icon_url,
            "sortOrder": modifier.sort_order,
            "isActive": modifier.is_active,
            "updateTime": modifier.update_time,
        }

    @staticmethod
    def _build_conflict_map_v3(conflicts: Iterable[KordBreachModifierConflictV3]):
        conflict_map: dict[str, list[str]] = defaultdict(list)
        for conflict in conflicts:
            conflict_map[conflict.modifier_id].append(conflict.conflict_modifier_id)
        return dict(conflict_map)

    @staticmethod
    def _slot_is_valid_v3(slot_no: int):
        return 1 <= slot_no <= 3

    @staticmethod
    def _dedupe_ids_v3(modifier_ids: list[str]):
        return list(dict.fromkeys(modifier_ids))

    @staticmethod
    def _modifier_groups_v3(modifiers: list[KordBreachModifierV3]):
        groups = {"global": [], "positive": [], "negative": []}
        for modifier in modifiers:
            groups.setdefault(modifier.modifier_category, []).append(
                KordBreachServiceV3._serialize_modifier_v3(modifier)
            )
        return groups

    @staticmethod
    def get_modifiers_v3():
        try:
            with V3Database.SessionLocal() as s:
                modifiers = (
                    s.query(KordBreachModifierV3)
                    .filter(KordBreachModifierV3.is_active.is_(True))
                    .order_by(
                        KordBreachModifierV3.modifier_category,
                        KordBreachModifierV3.sort_order,
                        KordBreachModifierV3.id,
                    )
                    .all()
                )
                conflicts = s.query(KordBreachModifierConflictV3).all()
                groups = KordBreachServiceV3._modifier_groups_v3(modifiers)
                return {
                    "globalModifiers": groups.get("global", []),
                    "positiveModifiers": groups.get("positive", []),
                    "negativeModifiers": groups.get("negative", []),
                    "conflictMap": KordBreachServiceV3._build_conflict_map_v3(
                        conflicts
                    ),
                }
        except Exception as e:
            logger.error(f"get_modifiers_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def _validate_selection_v3(s, modifier_ids: list[str]):
        modifier_ids = KordBreachServiceV3._dedupe_ids_v3(modifier_ids)
        if not modifier_ids:
            return False, "empty_selection", [], 0

        modifiers = (
            s.query(KordBreachModifierV3)
            .filter(
                KordBreachModifierV3.id.in_(modifier_ids),
                KordBreachModifierV3.is_active.is_(True),
            )
            .all()
        )
        modifier_by_id = {modifier.id: modifier for modifier in modifiers}
        missing_ids = [modifier_id for modifier_id in modifier_ids if modifier_id not in modifier_by_id]
        if missing_ids:
            return False, f"unknown_modifier:{','.join(missing_ids)}", [], 0

        global_ids = [
            modifier_id
            for modifier_id in modifier_ids
            if modifier_by_id[modifier_id].modifier_category == "global"
        ]
        if global_ids:
            return False, f"global_modifier_not_selectable:{','.join(global_ids)}", [], 0

        conflicts = (
            s.query(KordBreachModifierConflictV3)
            .filter(KordBreachModifierConflictV3.modifier_id.in_(modifier_ids))
            .all()
        )
        selected = set(modifier_ids)
        for conflict in conflicts:
            if conflict.conflict_modifier_id in selected:
                return (
                    False,
                    f"conflict:{conflict.modifier_id}:{conflict.conflict_modifier_id}",
                    [],
                    0,
                )

        ordered_modifiers = [modifier_by_id[modifier_id] for modifier_id in modifier_ids]
        total_score = sum(modifier.score or 0 for modifier in ordered_modifiers)
        if total_score < 0:
            return False, "fail_score", [], total_score

        return True, None, ordered_modifiers, total_score

    @staticmethod
    def _serialize_preset_v3(row: dict):
        modifier_ids = row.get("modifier_ids") or []
        positive_ids = row.get("positive_ids") or []
        negative_ids = row.get("negative_ids") or []
        total_score = row.get("total_score") or 0
        return {
            "id": f"preset-{row['slot_no']}",
            "slotNo": row["slot_no"],
            "name": row.get("name") or f"프리셋 {row['slot_no']}",
            "modifierIds": modifier_ids,
            "positiveIds": positive_ids,
            "negativeIds": negative_ids,
            "savedAt": row.get("update_time"),
            "totalScore": total_score,
            "isPassed": total_score >= 0,
        }

    @staticmethod
    def get_presets_v3(user_email: str | None):
        if not user_email:
            return []

        try:
            with V3Database.SessionLocal() as s:
                result = s.execute(
                    text(
                        """
                        SELECT p.email,
                               p.slot_no,
                               p.name,
                               p.total_score,
                               p.update_time,
                               COALESCE(
                                   array_agg(pm.modifier_id ORDER BY pm.sort_order, pm.modifier_id)
                                   FILTER (WHERE pm.modifier_id IS NOT NULL),
                                   ARRAY[]::text[]
                               ) AS modifier_ids,
                               COALESCE(
                                   array_agg(pm.modifier_id ORDER BY pm.sort_order, pm.modifier_id)
                                   FILTER (WHERE m.modifier_category = 'positive'),
                                   ARRAY[]::text[]
                               ) AS positive_ids,
                               COALESCE(
                                   array_agg(pm.modifier_id ORDER BY pm.sort_order, pm.modifier_id)
                                   FILTER (WHERE m.modifier_category = 'negative'),
                                   ARRAY[]::text[]
                               ) AS negative_ids
                        FROM user_kord_breach_preset p
                        LEFT JOIN user_kord_breach_preset_modifier pm
                               ON p.email = pm.email AND p.slot_no = pm.slot_no
                        LEFT JOIN kord_breach_modifier m ON pm.modifier_id = m.id
                        WHERE p.email = :email
                        GROUP BY p.email, p.slot_no, p.name, p.total_score, p.update_time
                        ORDER BY p.slot_no;
                        """
                    ),
                    {"email": user_email},
                )
                return [
                    KordBreachServiceV3._serialize_preset_v3(dict(row))
                    for row in result.mappings()
                ]
        except Exception as e:
            logger.error(f"get_presets_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def save_preset_v3(request_info: SaveKordBreachPresetV3, user_email: str):
        try:
            if not KordBreachServiceV3._slot_is_valid_v3(request_info.slotNo):
                return {"success": False, "reason": "invalid_slot"}

            with V3Database.SessionLocal() as s:
                is_valid, reason, modifiers, total_score = (
                    KordBreachServiceV3._validate_selection_v3(
                        s, request_info.modifierIds
                    )
                )
                if not is_valid:
                    return {
                        "success": False,
                        "reason": reason,
                        "totalScore": total_score,
                    }

                now = datetime.utcnow()
                preset_stmt = insert(UserKordBreachPresetV3).values(
                    email=user_email,
                    slot_no=request_info.slotNo,
                    name=request_info.name or f"프리셋 {request_info.slotNo}",
                    total_score=total_score,
                    create_time=now,
                    update_time=now,
                )
                preset_stmt = preset_stmt.on_conflict_do_update(
                    index_elements=[
                        UserKordBreachPresetV3.email,
                        UserKordBreachPresetV3.slot_no,
                    ],
                    set_={
                        "name": preset_stmt.excluded.name,
                        "total_score": preset_stmt.excluded.total_score,
                        "update_time": preset_stmt.excluded.update_time,
                    },
                )
                s.execute(preset_stmt)
                s.execute(
                    delete(UserKordBreachPresetModifierV3).where(
                        UserKordBreachPresetModifierV3.email == user_email,
                        UserKordBreachPresetModifierV3.slot_no
                        == request_info.slotNo,
                    )
                )
                for index, modifier in enumerate(modifiers):
                    s.add(
                        UserKordBreachPresetModifierV3(
                            email=user_email,
                            slot_no=request_info.slotNo,
                            modifier_id=modifier.id,
                            sort_order=index,
                            create_time=now,
                        )
                    )
                s.commit()

            presets = KordBreachServiceV3.get_presets_v3(user_email)
            saved_preset = next(
                (
                    preset
                    for preset in presets
                    if preset["slotNo"] == request_info.slotNo
                ),
                None,
            )
            return {"success": True, "preset": saved_preset}
        except Exception as e:
            logger.error(
                f"save_preset_v3: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def delete_preset_v3(request_info: DeleteKordBreachPresetV3, user_email: str):
        try:
            if not KordBreachServiceV3._slot_is_valid_v3(request_info.slotNo):
                return {"success": False, "reason": "invalid_slot"}

            with V3Database.SessionLocal() as s:
                s.execute(
                    delete(UserKordBreachPresetModifierV3).where(
                        UserKordBreachPresetModifierV3.email == user_email,
                        UserKordBreachPresetModifierV3.slot_no
                        == request_info.slotNo,
                    )
                )
                s.execute(
                    delete(UserKordBreachPresetV3).where(
                        UserKordBreachPresetV3.email == user_email,
                        UserKordBreachPresetV3.slot_no == request_info.slotNo,
                    )
                )
                s.commit()
                return {"success": True}
        except Exception as e:
            logger.error(
                f"delete_preset_v3: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def random_selection_v3():
        try:
            with V3Database.SessionLocal() as s:
                modifiers = (
                    s.query(KordBreachModifierV3)
                    .filter(KordBreachModifierV3.is_active.is_(True))
                    .all()
                )
                conflicts = s.query(KordBreachModifierConflictV3).all()

            positive = [m for m in modifiers if m.modifier_category == "positive"]
            negative = [m for m in modifiers if m.modifier_category == "negative"]
            conflict_map = KordBreachServiceV3._build_conflict_map_v3(conflicts)

            picked_ids: set[str] = set()
            random.shuffle(negative)
            target_negative_count = random.randint(1, min(3, len(negative))) if negative else 0
            for modifier in negative:
                if len(picked_ids) >= target_negative_count:
                    break
                blocked_ids = set()
                for picked_id in picked_ids:
                    blocked_ids.update(conflict_map.get(picked_id, []))
                if modifier.id in blocked_ids:
                    continue
                picked_ids.add(modifier.id)

            negative_score = sum(
                modifier.score or 0 for modifier in negative if modifier.id in picked_ids
            )
            used_positive_score = 0
            random.shuffle(positive)
            for modifier in positive:
                abs_score = abs(modifier.score or 0)
                if used_positive_score + abs_score > negative_score:
                    continue
                blocked_ids = set()
                for picked_id in picked_ids:
                    blocked_ids.update(conflict_map.get(picked_id, []))
                if modifier.id in blocked_ids:
                    continue
                picked_ids.add(modifier.id)
                used_positive_score += abs_score

            picked_modifiers = [m for m in modifiers if m.id in picked_ids]
            positive_ids = [
                m.id for m in picked_modifiers if m.modifier_category == "positive"
            ]
            negative_ids = [
                m.id for m in picked_modifiers if m.modifier_category == "negative"
            ]
            total_score = sum(modifier.score or 0 for modifier in picked_modifiers)
            return {
                "modifierIds": positive_ids + negative_ids,
                "positiveIds": positive_ids,
                "negativeIds": negative_ids,
                "totalScore": total_score,
                "isPassed": total_score >= 0,
            }
        except Exception as e:
            logger.error(f"random_selection_v3 error: {e}", exc_info=True)
            return None
