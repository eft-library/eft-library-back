from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel


class ModProperties(BaseModel):
    properties_type: str
    ergonomics: float | None
    recoil_modifier: float | None
    accuracy_modifier: float | None
    zoom_levels: list[list[float]] | None
    ergonomics_modifier: float | None
    item_recoil_modifier: float | None
    item_accuracy_modifier: float | None
    collected_at: datetime
    update_time: datetime


class ItemSummary(BaseModel):
    id: str
    name_en: str | None
    name_ko: str | None
    name_ja: str | None
    normalized_name: str | None
    image: str | None
    weight: float | None
    width: int | None
    height: int | None
    slot_count: int
    mod_properties: ModProperties | None


class CategorySummary(BaseModel):
    id: str
    parent_id: str | None
    name_key: str | None
    name_en: str | None
    name_ko: str | None
    name_ja: str | None
    normalized_name: str | None


class CategoryEntry(BaseModel):
    category: CategorySummary
    sort_order: int


class ItemEntry(BaseModel):
    item: ItemSummary
    sort_order: int


class SlotFilters(BaseModel):
    allowed_items: list[ItemEntry]
    excluded_items: list[ItemEntry]
    allowed_categories: list[CategoryEntry]
    excluded_categories: list[CategoryEntry]


class SlotDefinition(BaseModel):
    item_id: str
    slot_id: str
    name_id: str
    name_key: str | None
    name_en: str | None
    name_ko: str | None
    name_ja: str | None


class Slot(SlotDefinition):
    required: bool
    sort_order: int
    collected_at: datetime
    update_time: datetime
    filters: SlotFilters


class SlotConflict(BaseModel):
    sort_order: int
    slot_id: str
    definitions: list[SlotDefinition]


class Conflicts(BaseModel):
    items: list[ItemEntry]
    slots: list[SlotConflict]
    categories: list[CategoryEntry]


class WeaponProperties(BaseModel):
    caliber: str | None
    fire_rate: int | None
    ergonomics: int | None
    recoil_horizontal: int | None
    recoil_vertical: int | None
    default_ammo_item_id: str | None
    is_single_fire: bool | None
    is_full_auto: bool | None
    is_burst_fire: bool | None
    is_double_action: bool | None
    is_double_tap: bool | None
    is_semi_auto: bool | None


class DefaultPresetSummary(BaseModel):
    id: str
    name_en: str | None
    name_ko: str | None
    name_ja: str | None
    image: str | None


class WeaponSummary(BaseModel):
    item: ItemSummary
    weapon_properties: WeaponProperties
    preset_count: int
    default_preset: DefaultPresetSummary | None


class Page(BaseModel):
    total: int
    page: int
    page_size: int


class WeaponPage(Page):
    weapons: list[WeaponSummary]


class BallisticsProperties(BaseModel):
    properties_type: str
    center_of_impact: float | None
    deviation_curve: float | None
    deviation_max: float | None
    velocity_raw: float | None
    initial_speed_mps: float | None
    collected_at: datetime
    update_time: datetime


class ItemDetail(BaseModel):
    ballistics: BallisticsProperties | None
    item: ItemSummary
    categories: list[CategoryEntry]
    weapon_properties: WeaponProperties | None
    allowed_ammo: list[ItemSummary]
    slots: list[Slot]
    conflicts: Conflicts


class Candidate(BaseModel):
    item: ItemSummary


class CandidatePage(Page):
    item_id: str
    slot_id: str
    validation_scope: Literal['slot_filters_only']
    candidates: list[Candidate]


class PresetLink(BaseModel):
    is_listed: bool
    is_default_reference: bool
    sort_order: int | None


class WeaponPresetLink(PresetLink):
    weapon_item_id: str


class PresetSummary(BaseModel):
    item: ItemSummary
    base_item_id: str
    is_default: bool | None
    ergonomics: float | None
    recoil_vertical: float | None
    recoil_horizontal: float | None
    moa: float | None
    collected_at: datetime
    update_time: datetime


class LinkedPreset(PresetSummary):
    link: PresetLink


class PresetPage(Page):
    weapon_item_id: str
    presets: list[LinkedPreset]


class PresetComponent(BaseModel):
    component_index: int
    quantity: int
    attributes: dict[str, Any] | None
    item: ItemSummary


class ReconstructedNode(BaseModel):
    node_id: str
    item_id: str
    parent_node_id: str | None
    slot_id: str | None
    attributes: dict[str, Any] | None
    source_component_index: int
    source_unit_index: int


class ReconstructedTree(BaseModel):
    nodes: list[ReconstructedNode]


class ReconstructionIssue(BaseModel):
    code: Literal[
        'UNSUPPORTED_BASE_ITEM','INVALID_COMPONENTS','NODE_LIMIT','ROOT_COMPONENT_COUNT',
        'MISSING_ITEM_DEFINITION','UNRESOLVED_CONFLICT_SLOT','ITEM_CONFLICT','CATEGORY_CONFLICT',
        'SLOT_UNREACHABLE','AMMUNITION_WITHOUT_SLOT','MULTIPLE_SOLUTIONS','SEARCH_LIMIT','SOLUTION_LIMIT',
        'REQUIRED_SLOT_UNFILLED','NO_COMPLETE_TREE',
    ]
    node_id: str | None = None
    other_node_id: str | None = None
    item_id: str | None = None
    slot_id: str | None = None


class UnplacedComponent(BaseModel):
    component_index: int
    item_id: str
    quantity: int
    attributes: dict[str, Any] | None


class PresetReconstruction(BaseModel):
    method: Literal['inferred']
    algorithm_version: Literal[1]
    is_source_tree: Literal[False]
    validation_scope: Literal['stored_slot_constraints']
    status: Literal['unique','ambiguous','incomplete','unavailable','search_limited']
    can_import: bool
    requires_confirmation: Literal[True]
    is_unique: bool | None
    search_complete: bool
    solution_count_lower_bound: int
    states_examined: int
    candidate_trees: list[ReconstructedTree]
    partial_tree: ReconstructedTree | None
    unplaced_components: list[UnplacedComponent]
    issues: list[ReconstructionIssue]
    issues_truncated: bool


class PresetDetail(BaseModel):
    preset: PresetSummary
    components: list[PresetComponent]
    weapon_links: list[WeaponPresetLink]
    composition_type: Literal['flat_source_list']
    reconstruction: PresetReconstruction


Data = TypeVar('Data')


class ModdingResponse(BaseModel, Generic[Data]):
    status: Literal[200]
    msg: Literal['OK']
    data: Data
