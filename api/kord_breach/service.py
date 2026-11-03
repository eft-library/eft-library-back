import logging
import random
from collections import defaultdict
from datetime import datetime
from typing import Iterable

from sqlalchemy import delete, text
from sqlalchemy.dialects.postgresql import insert

from api.kord_breach.models import (
    KordBreachModifierConflict,
    KordBreachModifier,
    UserKordBreachPresetModifier,
    UserKordBreachPreset,
)
from api.kord_breach.req_models import (
    DeleteKordBreachPreset,
    SaveKordBreachPreset,
)
from database import Database

logger = logging.getLogger("api.kord_breach")


class KordBreachService:
    @staticmethod
    def _serialize_modifier(modifier: KordBreachModifier):
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
    def _build_conflict_map(conflicts: Iterable[KordBreachModifierConflict]):
        conflict_map: dict[str, list[str]] = defaultdict(list)
        for conflict in conflicts:
            conflict_map[conflict.modifier_id].append(conflict.conflict_modifier_id)
        return dict(conflict_map)

    @staticmethod
    def _slot_is_valid(slot_no: int):
        return 1 <= slot_no <= 3

    @staticmethod
    def _dedupe_ids(modifier_ids: list[str]):
        return list(dict.fromkeys(modifier_ids))

    @staticmethod
    def _modifier_groups(modifiers: list[KordBreachModifier]):
        groups = {"global": [], "positive": [], "negative": []}
        for modifier in modifiers:
            groups.setdefault(modifier.modifier_category, []).append(
                KordBreachService._serialize_modifier(modifier)
            )
        return groups

    @staticmethod
    def get_modifiers():
        try:
            with Database.SessionLocal() as s:
                modifiers = (
                    s.query(KordBreachModifier)
                    .filter(KordBreachModifier.is_active.is_(True))
                    .order_by(
                        KordBreachModifier.modifier_category,
                        KordBreachModifier.sort_order,
                        KordBreachModifier.id,
                    )
                    .all()
                )
                conflicts = s.query(KordBreachModifierConflict).all()
                groups = KordBreachService._modifier_groups(modifiers)
                return {
                    "globalModifiers": groups.get("global", []),
                    "positiveModifiers": groups.get("positive", []),
                    "negativeModifiers": groups.get("negative", []),
                    "conflictMap": KordBreachService._build_conflict_map(
                        conflicts
                    ),
                }
        except Exception as e:
            logger.error(f"get_modifiers_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def _validate_selection(s, modifier_ids: list[str]):
        modifier_ids = KordBreachService._dedupe_ids(modifier_ids)
        if not modifier_ids:
            return False, "empty_selection", [], 0

        modifiers = (
            s.query(KordBreachModifier)
            .filter(
                KordBreachModifier.id.in_(modifier_ids),
                KordBreachModifier.is_active.is_(True),
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
            s.query(KordBreachModifierConflict)
            .filter(KordBreachModifierConflict.modifier_id.in_(modifier_ids))
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
    def _serialize_preset(row: dict):
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
    def get_presets(user_email: str | None):
        if not user_email:
            return []

        try:
            with Database.SessionLocal() as s:
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
                    KordBreachService._serialize_preset(dict(row))
                    for row in result.mappings()
                ]
        except Exception as e:
            logger.error(f"get_presets_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def save_preset(request_info: SaveKordBreachPreset, user_email: str):
        try:
            if not KordBreachService._slot_is_valid(request_info.slotNo):
                return {"success": False, "reason": "invalid_slot"}

            with Database.SessionLocal() as s:
                is_valid, reason, modifiers, total_score = (
                    KordBreachService._validate_selection(
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
                preset_stmt = insert(UserKordBreachPreset).values(
                    email=user_email,
                    slot_no=request_info.slotNo,
                    name=request_info.name or f"프리셋 {request_info.slotNo}",
                    total_score=total_score,
                    create_time=now,
                    update_time=now,
                )
                preset_stmt = preset_stmt.on_conflict_do_update(
                    index_elements=[
                        UserKordBreachPreset.email,
                        UserKordBreachPreset.slot_no,
                    ],
                    set_={
                        "name": preset_stmt.excluded.name,
                        "total_score": preset_stmt.excluded.total_score,
                        "update_time": preset_stmt.excluded.update_time,
                    },
                )
                s.execute(preset_stmt)
                s.execute(
                    delete(UserKordBreachPresetModifier).where(
                        UserKordBreachPresetModifier.email == user_email,
                        UserKordBreachPresetModifier.slot_no
                        == request_info.slotNo,
                    )
                )
                for index, modifier in enumerate(modifiers):
                    s.add(
                        UserKordBreachPresetModifier(
                            email=user_email,
                            slot_no=request_info.slotNo,
                            modifier_id=modifier.id,
                            sort_order=index,
                            create_time=now,
                        )
                    )
                s.commit()

            presets = KordBreachService.get_presets(user_email)
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
    def delete_preset(request_info: DeleteKordBreachPreset, user_email: str):
        try:
            if not KordBreachService._slot_is_valid(request_info.slotNo):
                return {"success": False, "reason": "invalid_slot"}

            with Database.SessionLocal() as s:
                s.execute(
                    delete(UserKordBreachPresetModifier).where(
                        UserKordBreachPresetModifier.email == user_email,
                        UserKordBreachPresetModifier.slot_no
                        == request_info.slotNo,
                    )
                )
                s.execute(
                    delete(UserKordBreachPreset).where(
                        UserKordBreachPreset.email == user_email,
                        UserKordBreachPreset.slot_no == request_info.slotNo,
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
    def random_selection():
        try:
            with Database.SessionLocal() as s:
                modifiers = (
                    s.query(KordBreachModifier)
                    .filter(KordBreachModifier.is_active.is_(True))
                    .all()
                )
                conflicts = s.query(KordBreachModifierConflict).all()

            positive = [m for m in modifiers if m.modifier_category == "positive"]
            negative = [m for m in modifiers if m.modifier_category == "negative"]
            conflict_map = KordBreachService._build_conflict_map(conflicts)

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
