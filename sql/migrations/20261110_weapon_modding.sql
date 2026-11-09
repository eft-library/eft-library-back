-- Additive schema for weapon modding source data; no existing data is rewritten.
BEGIN;
SET LOCAL lock_timeout = '10s';
SET LOCAL statement_timeout = '60s';

-- 총기 모딩 원천 관계. 기존 items / weapon_items / weapon_allowed_ammo는 재사용한다.
-- 이름 문자열 기반 items.category와 달리 아래 카테고리는 원천 ID를 보존한다.
create table if not exists item_categories (
    id text primary key,
    parent_id text references item_categories(id) on delete restrict
        deferrable initially deferred,
    name_key text,
    name_en text,
    name_ko text,
    name_ja text,
    normalized_name text,
    collected_at timestamptz not null default now(),
    update_time timestamptz not null default now()
);
create index if not exists idx_item_categories_parent_id on item_categories(parent_id);

create table if not exists item_category_memberships (
    item_id text not null references items(id) on delete cascade,
    category_id text not null references item_categories(id) on delete restrict,
    sort_order integer not null check (sort_order >= 0),
    primary key (item_id, category_id)
);
create index if not exists idx_item_category_memberships_category_id
    on item_category_memberships(category_id, item_id);

-- 슬롯 소유자는 총기 또는 파츠 등 임의의 items 행일 수 있다.
-- 슬롯 ID를 전역 유니크로 가정하지 않고 소유 아이템과 함께 식별한다.
create table if not exists item_slots (
    item_id text not null references items(id) on delete cascade,
    slot_id text not null,
    name_id text not null,
    name_key text,
    name_en text,
    name_ko text,
    name_ja text,
    required boolean not null,
    sort_order integer not null check (sort_order >= 0),
    collected_at timestamptz not null default now(),
    update_time timestamptz not null default now(),
    primary key (item_id, slot_id),
    unique (item_id, sort_order)
);
create index if not exists idx_item_slots_slot_id on item_slots(slot_id, item_id);
create index if not exists idx_item_slots_name_id on item_slots(name_id, item_id);

-- 필터 배열 순번을 PK에 포함하여 원천의 동일 ID 반복도 보존한다.
-- allow/exclude를 서로 다른 행으로 보존한다. 우선순위와 장착 가능 여부는 계산하지 않는다.
create table if not exists item_slot_item_filters (
    item_id text not null,
    slot_id text not null,
    filter_type text not null check (filter_type in ('allowed', 'excluded')),
    target_item_id text not null references items(id) on delete restrict,
    sort_order integer not null check (sort_order >= 0),
    primary key (item_id, slot_id, filter_type, sort_order),
    foreign key (item_id, slot_id) references item_slots(item_id, slot_id) on delete cascade
);
create index if not exists idx_item_slot_item_filters_target
    on item_slot_item_filters(target_item_id, filter_type, item_id, slot_id);

create table if not exists item_slot_category_filters (
    item_id text not null,
    slot_id text not null,
    filter_type text not null check (filter_type in ('allowed', 'excluded')),
    category_id text not null references item_categories(id) on delete restrict,
    sort_order integer not null check (sort_order >= 0),
    primary key (item_id, slot_id, filter_type, sort_order),
    foreign key (item_id, slot_id) references item_slots(item_id, slot_id) on delete cascade
);
create index if not exists idx_item_slot_category_filters_category
    on item_slot_category_filters(category_id, filter_type, item_id, slot_id);

-- 충돌 배열은 동일 대상 ID가 반복될 수 있으므로 원본 순번으로 식별한다.
-- 충돌은 원천의 방향대로 저장한다. 역방향 관계를 자동 생성하지 않는다.
create table if not exists item_conflicting_items (
    item_id text not null references items(id) on delete cascade,
    conflicting_item_id text not null references items(id) on delete restrict,
    sort_order integer not null check (sort_order >= 0),
    primary key (item_id, sort_order)
);
create index if not exists idx_item_conflicting_items_reverse
    on item_conflicting_items(conflicting_item_id, item_id);

create table if not exists item_conflicting_slots (
    item_id text not null references items(id) on delete cascade,
    conflicting_slot_id text not null,
    sort_order integer not null check (sort_order >= 0),
    primary key (item_id, sort_order)
);
create index if not exists idx_item_conflicting_slots_reverse
    on item_conflicting_slots(conflicting_slot_id, item_id);
comment on column item_conflicting_slots.conflicting_slot_id is
    '원본 conflictingSlotIds 값. 원천 슬롯 목록에 없는 ID도 있어 대상 슬롯 FK를 두지 않는다. 소유 슬롯을 추정하지 않는다.';

create table if not exists item_conflicting_categories (
    item_id text not null references items(id) on delete cascade,
    category_id text not null references item_categories(id) on delete restrict,
    sort_order integer not null check (sort_order >= 0),
    primary key (item_id, sort_order)
);
create index if not exists idx_item_conflicting_categories_reverse
    on item_conflicting_categories(category_id, item_id);

-- 파츠 원천 성능. 총기 기본 제원은 weapon_items, 프리셋 완성 제원은 item_presets에 둔다.
-- 계산식/단위 변환/누적 결과를 저장하지 않는다. NULL을 0으로 바꾸지 않는다.
create table if not exists item_mod_properties (
    item_id text primary key references items(id) on delete cascade,
    properties_type text not null,
    ergonomics numeric,
    recoil_modifier numeric,
    accuracy_modifier numeric,
    zoom_levels jsonb check (jsonb_typeof(zoom_levels) = 'array'),
    ergonomics_modifier numeric,
    item_recoil_modifier numeric,
    item_accuracy_modifier numeric,
    collected_at timestamptz not null default now(),
    update_time timestamptz not null default now()
);
create index if not exists idx_item_mod_properties_properties_type
    on item_mod_properties(properties_type, item_id);
comment on column item_mod_properties.recoil_modifier is
    'properties.recoilModifier 원본 값. 루트 recoilModifier와 스케일이 다를 수 있으므로 합치거나 변환하지 않는다.';
comment on column item_mod_properties.item_recoil_modifier is '아이템 루트 recoilModifier 원본 값.';
comment on column item_mod_properties.accuracy_modifier is 'properties.accuracyModifier 원본 값.';
comment on column item_mod_properties.item_accuracy_modifier is '아이템 루트 accuracyModifier 원본 값.';
comment on column item_mod_properties.ergonomics is 'properties.ergonomics 원본 값.';
comment on column item_mod_properties.ergonomics_modifier is '아이템 루트 ergonomicsModifier 원본 값.';
comment on column item_mod_properties.zoom_levels is
    'properties.zoomLevels의 중첩 배열을 JSONB로 보존한다. 예: [[1,4],[2.5]]. 배열을 평탄화하지 않는다.';

-- 프리셋도 원천 items의 아이템이다. 이름/이미지/무게는 items에서 재사용한다.
-- 원천에는 방어구 프리셋도 있어 마스터는 item_presets로 명명한다.
create table if not exists item_presets (
    preset_item_id text primary key references items(id) on delete cascade,
    base_item_id text not null references items(id) on delete restrict,
    is_default boolean,
    ergonomics numeric,
    recoil_vertical numeric,
    recoil_horizontal numeric,
    moa numeric,
    collected_at timestamptz not null default now(),
    update_time timestamptz not null default now()
);
create index if not exists idx_item_presets_base_item_id
    on item_presets(base_item_id, preset_item_id);
comment on column item_presets.is_default is
    '프리셋 properties.default 원본 값. 총기 properties.defaultPreset 참조와 별개로 보존한다.';

-- 총기 properties.presets와 properties.defaultPreset 두 원천 관계를 따로 표시한다.
-- defaultPreset만 있고 presets에는 없는 참조도 표현할 수 있다.
create table if not exists weapon_preset_links (
    weapon_item_id text not null references weapon_items(item_id) on delete cascade,
    preset_item_id text not null references item_presets(preset_item_id) on delete restrict,
    is_listed boolean not null,
    is_default_reference boolean not null,
    sort_order integer check (sort_order >= 0),
    primary key (weapon_item_id, preset_item_id),
    check (is_listed or is_default_reference),
    check ((is_listed and sort_order is not null) or (not is_listed and sort_order is null))
);
create unique index if not exists uq_weapon_preset_links_default
    on weapon_preset_links(weapon_item_id) where is_default_reference;
create index if not exists idx_weapon_preset_links_preset
    on weapon_preset_links(preset_item_id, weapon_item_id);
create index if not exists idx_weapon_preset_links_sort
    on weapon_preset_links(weapon_item_id, sort_order, preset_item_id) where is_listed;

-- containsItems는 구성품 목록일 뿐 장착 트리가 아니다. 부모/슬롯을 추정하지 않는다.
-- 배열 순번으로 식별하여 동일 아이템의 반복과 서로 다른 attributes를 보존한다.
create table if not exists item_preset_components (
    preset_item_id text not null references item_presets(preset_item_id) on delete cascade,
    component_index integer not null check (component_index >= 0),
    item_id text not null references items(id) on delete restrict,
    quantity integer not null check (quantity > 0),
    attributes jsonb check (jsonb_typeof(attributes) = 'object'),
    primary key (preset_item_id, component_index)
);
create index if not exists idx_item_preset_components_item_id
    on item_preset_components(item_id, preset_item_id);
comment on column item_preset_components.attributes is
    'containsItems[].attributes 원본 객체. SQL NULL과 빈 객체 {}를 구분하고 임의의 장착 위치를 추가하지 않는다.';

COMMIT;
