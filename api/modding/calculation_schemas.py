"""Calculation contracts reuse the saved build's exact node and structural validator."""
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator
from api.weapon_builds.schemas import BuildContent, BuildNodeInput


class CalculationRequest(BaseModel):
    weapon_item_id: str = Field(min_length=1, max_length=200)
    nodes: list[BuildNodeInput] = Field(min_length=1, max_length=200)
    ammo_item_id: str | None = Field(None, min_length=1, max_length=200)

    @model_validator(mode='after')
    def valid_tree(self):
        BuildContent.model_validate({'weapon_item_id': self.weapon_item_id,
                                     'nodes': self.nodes, 'title': 'calculation'})
        return self


class CalculationIssue(BaseModel):
    code: str
    node_id: str | None = None
    slot_id: str | None = None
    item_id: str | None = None


class CompatibilityResult(BaseModel):
    scope: Literal['stored_slot_constraints']
    status: Literal['valid', 'invalid', 'unknown']
    issues: list[CalculationIssue]
    excludes: list[str]


class UnavailableMetric(BaseModel):
    metric: str
    code: str
    item_ids: list[str] = Field(default_factory=list)


class WeaponStatistics(BaseModel):
    weight_kg: float | None
    ergonomics: float | None
    recoil_vertical: float | None
    recoil_horizontal: float | None
    accuracy_moa: float | None
    muzzle_velocity_mps: float | None
    fire_modes: list[str] | None
    caliber: str | None
    fire_rate_rpm: int | None


class CalculationResult(BaseModel):
    calculation_version: str
    source_revision: str
    ammo_item_id: str | None
    ammo_selection: Literal['requested', 'weapon_default', 'unavailable']
    assumptions: list[str]
    compatibility: CompatibilityResult
    statistics: WeaponStatistics
    unavailable: list[UnavailableMetric]


class CalculationError(BaseModel):
    detail: str | list[dict[str, Any]]
