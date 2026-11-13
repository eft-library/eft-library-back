create extension if not exists pg_trgm;
CREATE EXTENSION IF NOT EXISTS ltree;

create table if not exists bosses (
    id text primary key,
    name_en text,
    name_ko text,
    name_ja text,
    is_boss boolean,
    parent_boss_id text,
    faction text,
    image text,
    normalized_name text,
    health_total integer,
    health_image text,
    head_hp integer,
    thorax_hp integer,
    stomach_hp integer,
    left_arm_hp integer,
    right_arm_hp integer,
    left_leg_hp integer,
    right_leg_hp integer,
    guide_en text,
    guide_ko text,
    guide_ja text,
    sort_order integer,
    update_time timestamptz default now()
);

create table if not exists boss_spawn (
    boss_id text,
    map_id text,
    spawn_chance numeric,
    primary key (boss_id, map_id)
);
create index if not exists idx_boss_spawn_map_id on boss_spawn (map_id);

create table if not exists boss_item (
    boss_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    primary key (boss_id, item_id)
);
create index if not exists idx_boss_item_item_id on boss_item (item_id);

create table if not exists map_points
(
    id text primary key,
    point_type text,
    name_en text,
    name_ko text,
    name_ja text,
    is_unlimited_use boolean,
    is_one_time_use boolean,
    image text,
    faction text,
    map_id text,
    requirements_en text,
    requirements_ko text,
    requirements_ja text,
    tip_en text,
    tip_ko text,
    tip_ja text,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_map_points_map_id on map_points(map_id);

create table if not exists main_contents
(
    id text primary key,
    name_en text,
    name_ko text,
    name_ja text,
    url text,
    image text,
    sort_order integer,
    update_time timestamptz default now()
);

create table if not exists menu_groups
(
    id text primary key,
    name_en text,
    name_ko text,
    name_ja text,
    sort_order integer,
    update_time timestamptz default now()
);

create table if not exists menu_sub_groups
(
    id text primary key,
    name_en text,
    name_ko text,
    name_ja text,
    parent_group_id text,
    url text,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_menu_sub_group_parent_group_id on menu_sub_groups(parent_group_id);

create table if not exists maps
(
    id text primary key,
    normalized_name text,
    is_use boolean,
    name_en text,
    name_ko text,
    name_ja text,
    parent_map_id text,
    map_depth integer,
    mot_image_en text,
    mot_image_ko text,
    mot_image_ja text,
    three_image text,
    three_json jsonb,
    sort_order integer,
    update_time timestamptz default now()
);

-- 퀘스트 기본 정보
create table if not exists quests (
    id text primary key,
    normalized_name text,
    name_en text,
    name_ko text,
    name_ja text,
    trader_id text,
    experience integer,
    delay_max integer,
    delay_min integer,
    kappa_required boolean,
    min_player_level integer,
    wiki_url text,
    guide_en text,
    guide_ko text,
    guide_ja text,
    affinity_type text constraint quests_affinity_type_check
        check (affinity_type in ('level_1', 'level_2', 'level_3', 'level_4', 'main_quest')),
    is_use boolean not null default true,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_quests_is_use on quests(is_use);


-- 퀘스트 관계(Relations)
create table if not exists quest_relations (
    quest_id text,
    related_quest_id text,
    relation_type text, -- require(선행), next(후행)
    sort_order integer,
    primary key (quest_id, related_quest_id, relation_type)
);
create index if not exists idx_quest_relations_quest_id on quest_relations (quest_id);
create index if not exists idx_quest_relations_relation_type on quest_relations (relation_type);

-- 퀘스트 목표(Objectives)
create table if not exists quest_objectives (
    objective_id text,
    quest_id text,
    type text,
    description_en text,
    description_ko text,
    description_ja text,
    count integer,
    found_in_raid boolean,
    optional boolean not null default false,
    sort_order integer,
    is_use boolean not null default true,
    update_time timestamptz default now(),
    primary key (objective_id, quest_id)
);
create index if not exists idx_quest_objectives_quest_id on quest_objectives (quest_id);
create index if not exists idx_quest_objectives_type on quest_objectives (type);
create index if not exists idx_quest_objectives_quest_sort on quest_objectives(quest_id, sort_order, objective_id);

-- 목표에 필요한 아이템
create table if not exists quest_objective_items (
    objective_id text,
    item_id text,
    item_type text, -- item/questItem/markerItem/requiredKey 등
    sort_order integer,
    primary key (objective_id, item_id, item_type)
);
create index if not exists idx_quest_objective_items_objective_id on quest_objective_items (objective_id);
create index if not exists idx_quest_objective_items_item_id on quest_objective_items (item_id);

-- 목표에 필요한 키(OR 그룹 지원)
create table if not exists quest_objective_required_keys (
    objective_id text,
    key_id text,
    primary key (objective_id, key_id)
);
create index if not exists idx_quest_objective_required_keys_objective_id on quest_objective_required_keys (objective_id);

-- 목표와 맵의 연관
create table if not exists quest_objective_maps (
    objective_id text,
    map_id text,
    sort_order integer,
    primary key (objective_id, map_id)
);
create index if not exists idx_quest_objective_maps_objective_id on quest_objective_maps (objective_id);
create index if not exists idx_quest_objective_maps_map_id on quest_objective_maps (map_id);


-- 퀘스트 완료 보상(스킬)
create table if not exists quest_finish_reward_skills (
    quest_id text,
    name_en text,
    name_ko text,
    name_ja text,
    skill_level numeric,
    sort_order integer,
    primary key (quest_id, name_en, name_ko, name_ja)
);
create index if not exists idx_quest_finish_reward_skills_quest_id on quest_finish_reward_skills (quest_id);

-- 퀘스트 완료 보상(트레이더 평판)
create table if not exists quest_finish_reward_trader_standing (
    quest_id text,
    trader_id text,
    standing numeric,
    sort_order integer,
    primary key (quest_id, trader_id)
);
create index if not exists idx_quest_finish_reward_trader_standing_quest_id on quest_finish_reward_trader_standing (quest_id);

-- 퀘스트 완료 보상(오퍼 해금)
create table if not exists quest_finish_reward_offer_unlock (
    quest_id text,
    offer_id text,
    trader_id text,
    item_id text,
    level integer,
    sort_order integer,
    primary key (quest_id, offer_id, item_id)
);
create index if not exists idx_quest_finish_reward_offer_unlock_quest_id on quest_finish_reward_offer_unlock (quest_id);

-- 퀘스트 완료 보상(아이템)
create table if not exists quest_finish_reward_items (
    quest_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    primary key (quest_id, item_id)
);
create index if not exists idx_quest_finish_reward_items_quest_id on quest_finish_reward_items (quest_id);
create index if not exists idx_quest_finish_reward_items_item_id on quest_finish_reward_items (item_id);

-- 퀘스트 완료 보상(제작 해금)
create table if not exists quest_finish_reward_craft_unlocks (
    quest_id text,
    craft_id text,
    station_level integer,
    sort_order integer,
    primary key (quest_id, craft_id)
);
create index if not exists idx_quest_finish_reward_craft_unlocks_quest_id on quest_finish_reward_craft_unlocks (quest_id);
create index if not exists idx_quest_finish_reward_craft_unlocks_craft_id on quest_finish_reward_craft_unlocks (craft_id);

create table if not exists traders
(
    id text primary key,
    name_en text,
    name_ko text,
    name_ja text,
    normalized_name text,
    image text,
    is_use boolean,
    sort_order integer,
    update_time timestamptz default now()
);

create table if not exists trader_barters
(
    id text primary key,
    trader_id text,
    trader_level integer
);

create index if not exists idx_trader_barters_trader_id on trader_barters(trader_id);
create index if not exists idx_trader_barters_trader_id_level on trader_barters(trader_id, trader_level);

create table if not exists barter_required_items
(
    id text primary key,
    barter_id text,
    item_id text,
    quantity integer
);
create index if not exists idx_barter_required_items_barter_id on barter_required_items(barter_id);
create index if not exists idx_barter_required_items_item_id on barter_required_items(item_id);

create table if not exists barter_reward_items
(
    id text primary key,
    barter_id text,
    item_id text,
    quantity integer
);
create index if not exists idx_barter_reward_items_barter_id on barter_reward_items(barter_id);
create index if not exists idx_barter_reward_items_item_id on barter_reward_items(item_id);

create table if not exists autocomplete_items
(
    url text primary key,
    autocomplete_text_en text,
    autocomplete_text_ko text,
    autocomplete_text_ja text,
    category text,
    sort_order integer,
    update_time timestamptz default now()
);

create table if not exists news_items
(
    id serial primary key,
    news_type text not null, -- event, patch, notice, recommend, next_update, tarkov_info
    title_en text,
    title_ko text,
    title_ja text,
    link text,
    is_new boolean default false,
    is_renewal boolean default false,
    is_active boolean default true,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_news_items_sort_order on news_items(sort_order);

create table if not exists hideout_master
(
    id text primary key,
    name_en text,
    name_ko text,
    name_ja text,
    normalized_name text,
    update_time timestamptz default now()
);

create table if not exists hideout_levels
(
    id text primary key,
    master_id text,
    hideout_level integer,
    construction_time integer
);
create index if not exists idx_hideout_levels_hideout_id on hideout_levels(master_id);
create index if not exists idx_hideout_levels_hideout_id_level on hideout_levels(master_id, hideout_level);

create table if not exists hideout_item_require
(
    id text primary key,
    hideout_level_id text,
    item_id text,
    quantity integer,
    in_raid boolean
);
create index if not exists idx_hideout_item_require_level on hideout_item_require(hideout_level_id);
create index if not exists idx_hideout_item_require_item on hideout_item_require(item_id);

create table if not exists hideout_trader_require
(
    id text primary key,
    hideout_level_id text,
    trader_id text,
    trader_level integer
);
create index if not exists idx_hideout_trader_require_level on hideout_trader_require(hideout_level_id);
create index if not exists idx_hideout_trader_require_trader on hideout_trader_require(trader_id);

create table if not exists hideout_station_require
(
    id text primary key,
    hideout_level_id text,
    require_master_id text,
    station_level integer
);
create index if not exists idx_hideout_station_require_level on hideout_station_require(hideout_level_id);
create index if not exists idx_hideout_station_require_station on hideout_station_require(require_master_id);

create table if not exists hideout_crafts
(
    id text primary key,
    hideout_level_id text,
    reward_item_id text,
    duration numeric,
    reward_quantity numeric
);
create index if not exists idx_hideout_crafts_hideout_level_id on hideout_crafts(hideout_level_id);
create index if not exists idx_hideout_crafts_reward_item_id on hideout_crafts(reward_item_id);
create index if not exists idx_hideout_crafts_hideout_level_reward_item on hideout_crafts(hideout_level_id, reward_item_id);

create table if not exists hideout_craft_require_items
(
    id text primary key,
    craft_id text,
    item_id text,
    quantity numeric
);
create index if not exists idx_craft_require_items_craft on hideout_craft_require_items(craft_id);
create index if not exists idx_craft_require_items_item on hideout_craft_require_items(item_id);
create index if not exists idx_craft_require_items_craft_item on hideout_craft_require_items(craft_id, item_id);

create table if not exists hideout_skill_require
(
    id text primary key,
    hideout_level_id text,
    require_level integer,
    name_en text,
    name_ko text,
    name_ja text,
    image text
);
create index if not exists idx_hideout_skill_require_level on hideout_skill_require(hideout_level_id);

create table if not exists hideout_bonus
(
    id text primary key,
    hideout_level_id text,
    bonus_type text,
    name_en text,
    name_ko text,
    name_ja text,
    skill_name_en text,
    skill_name_ko text,
    skill_name_ja text,
    bonus_value numeric(10, 4)
);
create index if not exists idx_hideout_bonus_level on hideout_bonus(hideout_level_id);

-- 여기서 부터 인덱스 걸기
create table if not exists user_info
(
  email text primary key,
  name text,
  nickname text,
  is_admin boolean,
  attendance_count integer,
  attendance_time timestamptz default now(),
  last_update_nickname timestamptz default now(),
  create_time timestamptz default now()
);

create table if not exists information
(
    id text primary key,
    information_type text,
    title_en text,
    title_ko text,
    title_ja text,
    content_en text,
    content_ko text,
    content_ja text,
    update_time timestamptz default now()
);

create table if not exists user_roadmap
(
    email text primary key,
    quest_list text[],
    update_time timestamptz default now()
);

create table if not exists ROADMAP_NODE
(
    id text primary key,
    total_x_coordinate numeric,
    total_y_coordinate numeric,
    single_x_coordinate numeric,
    single_y_coordinate numeric,
    total_kappa_x_coordinate numeric,
    total_kappa_y_coordinate numeric,
    single_kappa_x_coordinate numeric,
    single_kappa_y_coordinate numeric,
    update_time timestamptz default now()
);

create table if not exists ROADMAP_EDGE
(
    id text primary key,
    source_id text,
    target_id text,
    update_time timestamptz default now()
);

create table if not exists price_seasons
(
    id text primary key,
    name text,
    starts_at timestamptz,
    ends_at timestamptz,
    is_current boolean not null default false,
    collected_at timestamptz not null default now(),
    update_time timestamptz not null default now(),
    check (ends_at is null or starts_at is null or ends_at > starts_at)
);
create unique index if not exists uq_price_seasons_current
    on price_seasons(is_current) where is_current;
create index if not exists idx_price_seasons_start
    on price_seasons(starts_at desc, id);

create table if not exists item_prices
(
    item_id text,
    game_mode text,
    season_id text references price_seasons(id) on delete restrict,
    season_key text generated always as (coalesce(season_id, '')) stored,
    highest_trader_price numeric,
    highest_trader_id text,
    flea_market_price numeric,
    trader_count integer,
    has_flea boolean,
    update_time timestamptz default now(),
    primary key (item_id, game_mode, season_key),
    check (
        (game_mode = 'pvp-season' and season_id is not null)
        or (game_mode <> 'pvp-season' and season_id is null)
    )
);
create index if not exists idx_item_prices_mode_season
    on item_prices(game_mode, season_id);

create table if not exists item_trader_prices
(
    id text not null,
    item_id text,
    game_mode text, -- 'pve' | 'pvp' | 'pvp-season'
    season_id text references price_seasons(id) on delete restrict,
    season_key text generated always as (coalesce(season_id, '')) stored,
    trader_id text,
    price numeric,
    primary key (item_id, game_mode, season_key, trader_id),
    check (
        (game_mode = 'pvp-season' and season_id is not null)
        or (game_mode <> 'pvp-season' and season_id is null)
    )
);
create index if not exists idx_item_trader_prices_item_id on item_trader_prices(item_id);
create index if not exists idx_item_trader_prices_trader_id on item_trader_prices(trader_id);
create index if not exists idx_item_trader_prices_item_mode on item_trader_prices(item_id, game_mode, season_id);

-- 아이템 시세 조회 별도 테이블 말고 조회 쿼리로 수정
select
    itp.item_id,
    max(itp.price) as flea_market_price
from item_trader_prices itp
where itp.game_mode = 'pve'
  and itp.trader_id = 'FLEA_MARKET'
group by itp.item_id;

create table if not exists item_price_history
(
    item_id text,
    price integer,
    game_mode text,
    season_id text references price_seasons(id) on delete restrict,
    season_key text generated always as (coalesce(season_id, '')) stored,
    price_time timestamptz default now(),
    PRIMARY KEY (item_id, game_mode, season_key, price_time),
    check (
        (game_mode = 'pvp-season' and season_id is not null)
        or (game_mode <> 'pvp-season' and season_id is null)
    )
);
create index if not exists idx_item_price_history_time on item_price_history(price_time desc);
create index if not exists idx_item_price_history_item_mode_season_time
    on item_price_history(item_id, game_mode, season_id, price_time);

create table if not exists wipe
(
    id integer primary key ,
    patch_version text,
    season_start text,
    season_end text,
    create_time timestamptz default now()
);

create table if not exists USER_HIDEOUT
(
    email text primary key,
    complete_list text[],
    item_list jsonb,
    update_time timestamptz default now()
);

create table if not exists items (
    id text primary key,
    parent_category text,
    category text,
    name_en text,
    name_ko text,
    name_ja text,
    normalized_name text,
    weight numeric,
    width integer,
    height integer,
    image text,
    update_time timestamptz default now()
);
create index if not exists idx_items_parent_category on items(parent_category);
create index if not exists idx_items_category on items(category);
create index if not exists idx_items_normalized_name on items(normalized_name);
create index if not exists idx_items_update_time on items(update_time desc);

-- 상인 판매 상품: id는 내부 식별자, source_offer_id는 수집 원천의 상품 식별자이다.
-- 같은 원천 상품도 게임 모드 및 시즌별로 별도의 내부 id를 사용한다.
-- source_offer_id: 교환은 barter:원천ID, 구매는 purchase:안정적식별값을 사용한다.
-- 구매 식별값은 상인/결과 아이템/화폐/우호도/정렬된 해금 조건으로 생성하고
-- 가격, 구매 제한, 초기화 시각은 제외한다. API regular 모드는 pvp로 매핑한다.
create table if not exists trader_offers
(
    id text primary key,
    source_offer_id text not null,
    trader_id text not null references traders(id) on delete restrict,
    trader_level integer not null check (trader_level between 1 and 4),
    offer_type text not null check (offer_type in ('purchase', 'barter')),
    game_mode text not null check (game_mode in ('pve', 'pvp', 'pvp-season')),
    season_id text references price_seasons(id) on delete restrict,
    season_key text generated always as (coalesce(season_id, '')) stored,
    -- 의미가 확인된 초기화 주기당 구매 가능 수량만 저장한다. NULL은 미확인이다.
    buy_limit integer check (buy_limit >= 0),
    -- 원천 buyLimit 값을 보존한다. 특수 값의 의미를 추정하지 않는다.
    raw_buy_limit integer,
    -- NULL: 미확인, true: 무제한 확인, false: 제한 있음 확인.
    is_unlimited boolean,
    is_use boolean not null default true,
    sort_order integer,
    collected_at timestamptz not null default now(),
    update_time timestamptz not null default now(),
    unique (source_offer_id, game_mode, season_key),
    check (not is_unlimited or buy_limit is null),
    check (
        (game_mode = 'pvp-season' and season_id is not null)
        or (game_mode <> 'pvp-season' and season_id is null)
    )
);
create index if not exists idx_trader_offers_trader_mode_season_level
    on trader_offers(trader_id, game_mode, season_id, trader_level)
    where is_use;
create index if not exists idx_trader_offers_season_id on trader_offers(season_id);

-- 화폐 구매와 아이템 교환 모두 비용을 행 단위로 저장한다.
-- 화폐 비용은 currencyItem의 원천 아이템 ID를 사용한다.
-- 비용/보상 아이템을 items에 먼저 적재한 뒤 상품의 하위 행을 적재한다.
create table if not exists trader_offer_costs
(
    offer_id text not null references trader_offers(id) on delete cascade,
    item_id text not null references items(id) on delete restrict,
    quantity numeric not null check (quantity > 0),
    sort_order integer,
    primary key (offer_id, item_id)
);
create index if not exists idx_trader_offer_costs_item_id on trader_offer_costs(item_id);

-- 한 상품에서 여러 결과 아이템을 제공하는 경우도 지원한다.
create table if not exists trader_offer_rewards
(
    offer_id text not null references trader_offers(id) on delete cascade,
    item_id text not null references items(id) on delete restrict,
    quantity integer not null check (quantity > 0),
    sort_order integer,
    primary key (offer_id, item_id)
);
create index if not exists idx_trader_offer_rewards_item_id on trader_offer_rewards(item_id);

-- 상품 구매에 필요한 퀘스트 해금 조건. 행이 없으면 퀘스트 조건이 없다.
-- 원천 퀘스트가 quests에 아직 없어도 조건을 보존하기 위해 quest_id FK는 두지 않는다.
-- TODO: taskUnlock의 다중 조건 및 완료 상태 의미를 확인한 뒤 수집 로직에 반영한다.
create table if not exists trader_offer_task_unlocks
(
    offer_id text not null references trader_offers(id) on delete cascade,
    quest_id text not null,
    primary key (offer_id, quest_id)
);
create index if not exists idx_trader_offer_task_unlocks_quest_id
    on trader_offer_task_unlocks(quest_id);

-- 남은 초가 아닌 원천에서 확인한 다음 초기화 시각을 저장한다.
create table if not exists trader_restock_state
(
    trader_id text not null references traders(id) on delete restrict,
    game_mode text not null check (game_mode in ('pve', 'pvp', 'pvp-season')),
    season_id text references price_seasons(id) on delete restrict,
    season_key text generated always as (coalesce(season_id, '')) stored,
    next_restock_at timestamptz,
    collected_at timestamptz not null default now(),
    update_time timestamptz not null default now(),
    primary key (trader_id, game_mode, season_key),
    check (
        (game_mode = 'pvp-season' and season_id is not null)
        or (game_mode <> 'pvp-season' and season_id is null)
    )
);
create index if not exists idx_trader_restock_state_season_id on trader_restock_state(season_id);

create table if not exists item_penalties (
    item_id text primary key,
    ergonomics_penalty numeric,
    turn_speed_penalty numeric,
    movement_speed_penalty numeric,
    distance_modifier numeric
);

create table if not exists weapon_items (
    item_id text primary key,
    caliber text,
    fire_rate integer,
    ergonomics integer,
    recoil_horizontal integer,
    recoil_vertical integer,
    default_ammo_item_id text,
    is_single_fire boolean default false,
    is_full_auto boolean default false,
    is_burst_fire boolean default false,
    is_double_action boolean default false,
    is_double_tap boolean default false,
    is_semi_auto boolean default false
);

create table if not exists weapon_allowed_ammo (
    item_id text,
    ammo_item_id text,
    primary key (item_id, ammo_item_id)
);
create index if not exists idx_weapon_allowed_ammo_ammo_item_id
    on weapon_allowed_ammo(ammo_item_id);

-- 사용자 모딩 빌드는 원천/Airflow 테이블과 분리한다.
-- 원천 아이템/슬롯이 사라져도 사용자 저장본을 유지하도록 해당 원천 FK는 두지 않는다.
create table if not exists user_weapon_builds (
    id uuid primary key,
    owner_email text not null references user_info(email) on delete cascade,
    request_id uuid not null,
    request_fingerprint text not null,
    weapon_item_id text not null,
    title text not null check (char_length(btrim(title)) between 1 and 120),
    description text not null default '' check (char_length(description) <= 5000),
    version integer not null default 1 check (version > 0),
    is_public boolean not null default false,
    published_revision integer,
    copied_from_build_id uuid references user_weapon_builds(id) on delete set null,
    copied_from_revision integer,
    source_title text,
    source_author_nickname text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (owner_email, request_id),
    check (not is_public or published_revision is not null),
    check (published_revision is null or (published_revision > 0 and published_revision <= version))
);
create index if not exists idx_user_weapon_builds_owner_updated
    on user_weapon_builds(owner_email, updated_at desc, id);
create index if not exists idx_user_weapon_builds_publication
    on user_weapon_builds(id, published_revision) where is_public;
create index if not exists idx_user_weapon_builds_copy_source on user_weapon_builds(copied_from_build_id);

create table if not exists user_weapon_build_nodes (
    build_id uuid not null references user_weapon_builds(id) on delete cascade,
    node_id text not null check (node_id ~ '^[A-Za-z0-9_-]{1,80}$'),
    parent_node_id text,
    slot_id text,
    item_id text not null,
    item_snapshot jsonb not null check (jsonb_typeof(item_snapshot) = 'object'),
    attributes jsonb check (jsonb_typeof(attributes) = 'object'),
    sort_order integer not null check (sort_order >= 0),
    primary key (build_id, node_id),
    unique (build_id, sort_order),
    foreign key (build_id, parent_node_id) references user_weapon_build_nodes(build_id, node_id)
        on delete cascade deferrable initially deferred,
    check ((parent_node_id is null and slot_id is null)
        or (parent_node_id is not null and slot_id is not null)),
    check (parent_node_id is null or parent_node_id <> node_id)
);
create unique index if not exists uq_user_weapon_build_nodes_root
    on user_weapon_build_nodes(build_id) where parent_node_id is null;
create unique index if not exists uq_user_weapon_build_nodes_parent_slot
    on user_weapon_build_nodes(build_id, parent_node_id, slot_id) where parent_node_id is not null;
create index if not exists idx_user_weapon_build_nodes_item on user_weapon_build_nodes(item_id, build_id);

-- 공개 버전의 불변 스냅샷. 작업본 변경은 이 행을 갱신하지 않는다.
create table if not exists user_weapon_build_publications (
    build_id uuid not null references user_weapon_builds(id) on delete cascade,
    revision integer not null check (revision > 0),
    snapshot jsonb not null check (jsonb_typeof(snapshot) = 'object'),
    published_at timestamptz not null default now(),
    primary key (build_id, revision)
);
create index if not exists idx_user_weapon_build_publications_recent
    on user_weapon_build_publications(published_at desc, build_id, revision);
create index if not exists idx_user_weapon_build_publications_weapon
    on user_weapon_build_publications ((snapshot->>'weapon_item_id'), build_id, revision);
-- 순환 의존성은 양쪽 테이블 생성 후 지연 검사 FK로 연결한다.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'user_weapon_builds'::regclass
          AND conname = 'fk_user_weapon_builds_publication'
    ) THEN
        ALTER TABLE user_weapon_builds
            ADD CONSTRAINT fk_user_weapon_builds_publication
            FOREIGN KEY (id, published_revision)
            REFERENCES user_weapon_build_publications(build_id, revision)
            DEFERRABLE INITIALLY DEFERRED;
    END IF;
END;
$$;

create table if not exists user_weapon_build_votes (
    build_id uuid not null,
    revision integer not null,
    user_email text not null references user_info(email) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (build_id, revision, user_email),
    foreign key (build_id, revision) references user_weapon_build_publications(build_id, revision) on delete cascade
);
create index if not exists idx_user_weapon_build_votes_user on user_weapon_build_votes(user_email, build_id, revision);
create index if not exists idx_user_weapon_build_votes_ranking
    on user_weapon_build_votes(build_id, revision, created_at desc);

create table if not exists user_weapon_build_comments (
    id uuid primary key,
    build_id uuid not null,
    revision integer not null,
    author_email text not null references user_info(email) on delete cascade,
    request_id uuid not null,
    content text not null check (char_length(btrim(content)) between 1 and 2000),
    version integer not null default 1 check (version > 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (author_email, request_id),
    foreign key (build_id, revision) references user_weapon_build_publications(build_id, revision) on delete cascade
);
create index if not exists idx_user_weapon_build_comments_page
    on user_weapon_build_comments(build_id, revision, created_at, id);
create index if not exists idx_user_weapon_build_comments_author
    on user_weapon_build_comments(author_email, created_at desc);

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

create table if not exists ammo_items (
    item_id text primary key,
    damage integer,
    armor_damage integer,
    penetration_power integer,
    recoil_modifier numeric,
    accuracy_modifier numeric,
    heavy_bleed_modifier numeric,
    light_bleed_modifier numeric
);

create table if not exists ammo_efficiency (
    ammo_item_id text primary key,
    value_1 integer,
    value_2 integer,
    value_3 integer,
    value_4 integer,
    value_5 integer,
    value_6 integer
);

create table if not exists melee_items (
    item_id text primary key,
    hit_radius numeric,
    slash_damage integer,
    stab_damage integer
);

create table if not exists throwable_items (
    item_id text primary key,
    throwable_type text,
    fuse numeric,
    fragments integer,
    contusion_radius numeric,
    min_explosion_distance numeric,
    max_explosion_distance numeric
);

create table if not exists storage_items (
    item_id text primary key,
    storage_type text,
    capacity integer
);
create index if not exists idx_storage_items_storage_type
    on storage_items(storage_type);

create table if not exists storage_grids (
    item_id text,
    grid_index integer,
    width integer,
    height integer,
    primary key (item_id, grid_index)
);

create table if not exists protection_items (
    item_id text primary key,
    protection_type text,
    armor_class integer,
    durability integer,
    material text,
    ricochet_y numeric,
    deafening text,
    blindness_protection numeric,
    is_head_top boolean default false,
    is_head_nape boolean default false,
    is_head_ears boolean default false,
    is_head_face boolean default false,
    is_head_jaws boolean default false,
    is_head_eyes boolean default false,
    is_thorax_throat boolean default false,
    is_thorax_neck boolean default false,
    is_thorax boolean default false,
    is_upper_back boolean default false,
    is_stomach boolean default false,
    is_left_side boolean default false,
    is_right_side boolean default false,
    is_lower_back boolean default false,
    is_groin boolean default false,
    is_buttocks boolean default false,
    is_left_shoulder boolean default false,
    is_right_shoulder boolean default false,
    is_front_plate boolean default false,
    is_back_plate boolean default false,
    is_left_plate boolean default false,
    is_right_plate boolean default false,
    is_side_plate boolean default false
);
create index if not exists idx_protection_items_protection_type
    on protection_items(protection_type);

create table if not exists consumable_items (
    item_id text primary key,
    consumable_type text,
    energy integer,
    hydration integer,
    units integer,
    use_time numeric,
    hitpoints integer,
    painkiller_duration integer,
    energy_impact integer,
    hydration_impact integer
);
create index if not exists idx_consumable_items_consumable_type
    on consumable_items(consumable_type);

create table if not exists consumable_cures
(
    item_id text,
    cure text,
    primary key (item_id, cure)
);
create index if not exists idx_consumable_cures_cure
    on consumable_cures(cure);

create table if not exists consumable_stim_effects (
    item_id text,
    effect_index integer,
    effect_type text,
    value numeric,
    delay integer,
    duration integer,
    skill_name text,
    primary key (item_id, effect_index)
);
create index if not exists idx_consumable_stim_effects_effect_type
    on consumable_stim_effects(effect_type);

create table if not exists usage_items
 (
    item_id text primary key,
    max_uses integer
);

create table if not exists user_footprint
(
  id serial primary key,
  url text,
  request_type text,
  request_time timestamptz default now(),
  execute_time timestamptz default now()
);
create index if not exists idx_user_footprint_request_time on user_footprint (request_time desc);

create table if not exists sitemap
(
    id serial primary key,
    url text,
    priority numeric,
    change_freq text,
    sitemap_value text,
    create_time timestamptz default now(),
    update_time timestamptz default now()
);

create table if not exists health_check (
    id serial primary key,
    service_name text,
    status text,
    checked_time timestamptz default now()
);
create index if not exists idx_health_check_checked_time on health_check(checked_time desc);

create table if not exists response_time (
    id serial primary key,
    service_name text,
    response_ms numeric,
    checked_time timestamptz default now()
);
create index if not exists idx_response_time_checked_time on response_time(checked_time desc);

create table if not exists deployment_notice (
    id text primary key,
    is_active boolean not null default false,
    message_ko text,
    message_en text,
    message_ja text,
    start_time timestamptz,
    end_time timestamptz,
    updated_by text,
    update_time timestamptz default now()
);
create index if not exists idx_deployment_notice_active
    on deployment_notice(is_active);
create index if not exists idx_deployment_notice_time
    on deployment_notice(start_time, end_time);

create table if not exists user_location_request (
    id serial primary key,
    email text,
    location text,
    request_time timestamptz default now()
);

-- Anonymous desktop path observations; one row per successful local selection.
create table if not exists where_am_i_path_reports (
    id bigint generated by default as identity primary key,
    path_type varchar(16) not null,
    path text not null,
    app_version varchar(64) not null,
    created_at timestamptz not null default now(),
    constraint ck_path_reports_type check (path_type in ('screenshot', 'log')),
    constraint ck_path_reports_path check (char_length(btrim(path)) > 0 and char_length(path) <= 4096),
    constraint ck_path_reports_version check (char_length(btrim(app_version)) > 0 and char_length(app_version) <= 64)
);

-- Public desktop release metadata. No sample release is published automatically.
create table if not exists where_am_i_releases (
    id bigint generated by default as identity primary key,
    product varchar(32) not null,
    version varchar(64) not null,
    platform varchar(32) not null,
    architecture varchar(32) not null,
    channel varchar(32) not null,
    min_supported_version varchar(64) not null,
    download_url text,
    release_notes text,
    published_at timestamptz not null default now(),
    is_active boolean not null default false,
    constraint uq_where_am_i_release unique (product, version, platform, architecture, channel),
    constraint ck_where_am_i_release_version check (version ~ '^[0-9]+(\.[0-9]+){1,3}$'),
    constraint ck_where_am_i_release_min_version check (min_supported_version ~ '^[0-9]+(\.[0-9]+){1,3}$'),
    constraint ck_where_am_i_release_notes check (char_length(release_notes) <= 4000),
    constraint ck_where_am_i_release_url check (char_length(download_url) <= 4096)
);
create index if not exists idx_where_am_i_releases_lookup
    on where_am_i_releases (product, platform, architecture, channel, published_at)
    where is_active;

-- Client-supported slugs are a separate vocabulary from maps.id; normalized_name
-- is not unique in maps, so it cannot be a reliable foreign-key target.
create table if not exists where_am_i_map_aliases (
    alias varchar(256) primary key,
    map_slug varchar(32) not null,
    is_active boolean not null default true,
    updated_at timestamptz not null default now(),
    constraint ck_where_am_i_alias_name check (
        char_length(replace(lower(btrim(alias)), '_preset', '')) between 1 and 128
        and replace(lower(btrim(alias)), '_preset', '') ~ '^[a-z0-9 _-]+$')
);
create unique index if not exists uq_where_am_i_alias_normalized
    on where_am_i_map_aliases ((replace(lower(btrim(alias)), '_preset', '')));

-- Post-response, best-effort analysis; no raw IP or request body storage; raid events include normalized email.
create table if not exists where_am_i_raid_state_events (
    id bigint generated by default as identity primary key,
    user_key varchar(64) not null,
    email text,
    session_id varchar(64),
    map_slug text,
    requested_map text,
    started_at timestamptz,
    timer_observed_at timestamptz,
    raid_ends_at timestamptz,
    is_active boolean not null,
    transit_count integer not null,
    state_hash varchar(64) not null,
    event_id uuid,
    http_status integer not null,
    result_code varchar(80) not null,
    is_success boolean not null,
    elapsed_ms integer not null,
    received_at timestamptz not null,
    created_at timestamptz not null default now()
);
create index if not exists idx_where_am_i_raid_events_received
    on where_am_i_raid_state_events (received_at desc);
create index if not exists idx_where_am_i_raid_events_session
    on where_am_i_raid_state_events (session_id, received_at) where session_id is not null;

create table if not exists where_am_i_version_checks (
    id bigint generated by default as identity primary key,
    product varchar(32) not null,
    current_version varchar(64) not null,
    platform varchar(32) not null,
    architecture varchar(32) not null,
    channel varchar(32) not null,
    latest_version varchar(64),
    min_supported_version varchar(64),
    update_available boolean,
    update_required boolean,
    http_status integer not null,
    result_code varchar(80) not null,
    is_success boolean not null,
    elapsed_ms integer not null,
    received_at timestamptz not null,
    created_at timestamptz not null default now()
);
create index if not exists idx_where_am_i_version_checks_received
    on where_am_i_version_checks (received_at desc);

create table if not exists where_am_i_api_failures (
    id bigint generated by default as identity primary key,
    endpoint varchar(80) not null,
    http_status integer not null,
    result_code varchar(80) not null,
    app_version varchar(64),
    user_key varchar(64),
    requested_map text,
    error_fields jsonb not null,
    elapsed_ms integer not null,
    received_at timestamptz not null,
    created_at timestamptz not null default now()
);
create index if not exists idx_where_am_i_api_failures_received
    on where_am_i_api_failures (received_at desc);

create table if not exists USER_PROGRESS_ITEM
(
  email text,
  progress_type text,
  item_list text[],
  update_time timestamptz default now(),
  PRIMARY KEY (email, progress_type)
);

create table if not exists progress_item (
    id text not null,
    progress_type text not null,
    update_time timestamptz default now(),
    primary key (id, progress_type)
);
CREATE INDEX if not exists idx_progress_item_type ON progress_item (progress_type);

-- 원천 성능 값: 비율 변환 없이 저장한다. 기존 아이템/파츠 성능은 재사용한다.
create table if not exists item_ballistics (
    item_id text primary key references items(id) on delete cascade,
    properties_type text not null,
    center_of_impact numeric,
    deviation_curve numeric,
    deviation_max numeric,
    velocity_raw numeric,
    initial_speed_mps numeric check (initial_speed_mps >= 0),
    collected_at timestamptz not null default now(),
    update_time timestamptz not null default now()
);
comment on column item_ballistics.velocity_raw is '아이템 루트 velocity 원본. 단위/적용식 검증 전 변환하지 않는다. 탄약 properties.initialSpeed(m/s)와 구분.';
comment on column item_ballistics.center_of_impact is 'properties.centerOfImpact 원본. 단독 MOA가 아니며 검증된 기준식으로 변환한다.';

-- 전체 목록의 수집 여부를 빈 보상 목록과 구분한다. 원천 확인 전에는 행을 만들지 않는다.
create table if not exists kord_breach_reward_snapshots (
    season_id text primary key,
    source_url text not null check (length(btrim(source_url)) > 0),
    source_revision text not null check (length(btrim(source_revision)) > 0),
    collected_at timestamptz not null
);
create table if not exists kord_breach_rewards (
    season_id text not null references kord_breach_reward_snapshots(season_id) on delete cascade,
    id text not null,
    item_id text not null references items(id) on delete restrict,
    sort_order integer not null check (sort_order >= 0),
    unlock_conditions_known boolean not null,
    primary key (season_id, id),
    unique (season_id, sort_order)
);
create index if not exists idx_kord_breach_rewards_item on kord_breach_rewards(item_id);
-- 같은 group_no 내 AND, 그룹 간 OR. 조건이 확인된 무조건 보상은 조건 행이 없다.
-- quests는 기존 수집에서 전체 교체된다. quest_id는 논리 참조로 보존하고 조회시 LEFT JOIN한다.
create table if not exists kord_breach_reward_conditions (
    season_id text not null,
    reward_id text not null,
    group_no integer not null check (group_no >= 0),
    sort_order integer not null check (sort_order >= 0),
    condition_type text not null check (condition_type in ('player_level', 'quest_completed')),
    required_level integer check (required_level > 0),
    quest_id text,
    primary key (season_id, reward_id, group_no, sort_order),
    foreign key (season_id, reward_id) references kord_breach_rewards(season_id, id) on delete cascade,
    check ((condition_type='player_level' and required_level is not null and quest_id is null)
        or (condition_type='quest_completed' and required_level is null and quest_id is not null and length(btrim(quest_id)) > 0))
);
create index if not exists idx_kord_breach_reward_conditions_quest on kord_breach_reward_conditions(quest_id) where quest_id is not null;

create table if not exists kord_breach_modifier (
    id text primary key,
    modifier_category text not null,
    name_en text not null,
    name_ko text,
    name_ja text,
    effect_en text,
    effect_ko text,
    effect_ja text,
    score integer not null default 0,
    icon_url text,
    sort_order integer,
    is_active boolean default true,
    update_time timestamptz default now()
);
create index if not exists idx_kord_breach_modifier_category_sort
    on kord_breach_modifier(modifier_category, sort_order, id);
create index if not exists idx_kord_breach_modifier_active
    on kord_breach_modifier(is_active);

create table if not exists kord_breach_modifier_conflict (
    modifier_id text not null,
    conflict_modifier_id text not null,
    reason text,
    update_time timestamptz default now(),
    primary key (modifier_id, conflict_modifier_id)
);
create index if not exists idx_kord_breach_modifier_conflict_reverse
    on kord_breach_modifier_conflict(conflict_modifier_id, modifier_id);

create table if not exists user_kord_breach_preset (
    email text not null,
    slot_no integer not null check (slot_no between 1 and 3),
    name text,
    total_score integer not null default 0,
    create_time timestamptz default now(),
    update_time timestamptz default now(),
    primary key (email, slot_no)
);
create index if not exists idx_user_kord_breach_preset_email_update
    on user_kord_breach_preset(email, update_time desc);

create table if not exists user_kord_breach_preset_modifier (
    email text not null,
    slot_no integer not null check (slot_no between 1 and 3),
    modifier_id text not null,
    sort_order integer,
    create_time timestamptz default now(),
    primary key (email, slot_no, modifier_id)
);
create index if not exists idx_user_kord_breach_preset_modifier_slot
    on user_kord_breach_preset_modifier(email, slot_no, sort_order, modifier_id);
create index if not exists idx_user_kord_breach_preset_modifier_modifier
    on user_kord_breach_preset_modifier(modifier_id);

create table if not exists story (
    id text primary key,
    title_en text,
    title_ko text,
    title_ja text,
    objectives_en text,
    objectives_ko text,
    objectives_ja text,
    requirements_en text,
    requirements_ko text,
    requirements_ja text,
    guide_en text,
    guide_ja text,
    guide_ko text,
    sort_order integer,
    update_time timestamptz default now()
);

create table if not exists story_objectives
(
    objective_id text primary key,
    story_id text,
    parent_objective_id text,
    objective_type text, -- talk/handover/extract/visit/locate/kill/access/note/etc
    description_en text,
    description_ko text,
    description_ja text,
    count integer,
    is_optional boolean default false,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_story_objectives_story_id on story_objectives(story_id);
create index if not exists idx_story_objectives_parent_id on story_objectives(parent_objective_id);
create index if not exists idx_story_objectives_type on story_objectives(objective_type);
create index if not exists idx_story_objectives_story_sort on story_objectives(story_id, sort_order, objective_id);

create table if not exists story_requirements
(
    id text primary key,
    story_id text,
    requirement_type text, -- auto_added/level/quest/item/access/note/etc
    description_en text,
    description_ko text,
    description_ja text,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_story_requirements_story_id on story_requirements(story_id);
create index if not exists idx_story_requirements_type on story_requirements(requirement_type);
create index if not exists idx_story_requirements_story_sort on story_requirements(story_id, sort_order, id);

create table if not exists story_requirement_items
(
    requirement_id text,
    item_id text,
    quantity integer,
    found_in_raid boolean,
    item_role text,
    sort_order integer,
    primary key (requirement_id, item_id, item_role)
);
create index if not exists idx_story_requirement_items_requirement_id on story_requirement_items(requirement_id);
create index if not exists idx_story_requirement_items_item_id on story_requirement_items(item_id);
create index if not exists idx_story_requirement_items_requirement_sort on story_requirement_items(requirement_id, sort_order, item_id);

create table if not exists story_objective_items
(
    objective_id text,
    item_id text,
    quantity integer,
    found_in_raid boolean,
    item_role text, -- required/handover/optional/reward/etc
    sort_order integer,
    primary key (objective_id, item_id, item_role)
);
create index if not exists idx_story_objective_items_objective_id on story_objective_items(objective_id);
create index if not exists idx_story_objective_items_item_id on story_objective_items(item_id);

create table if not exists story_objective_reward_items
(
    objective_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    primary key (objective_id, item_id)
);
create index if not exists idx_story_objective_reward_items_objective_id on story_objective_reward_items(objective_id);
create index if not exists idx_story_objective_reward_items_item_id on story_objective_reward_items(item_id);

create table if not exists story_objective_reward_texts
(
    id text primary key,
    objective_id text,
    reward_type text,
    description_en text,
    description_ko text,
    description_ja text,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_story_objective_reward_texts_objective_id on story_objective_reward_texts(objective_id);
create index if not exists idx_story_objective_reward_texts_type on story_objective_reward_texts(reward_type);

create table if not exists story_reward_trader_standing
(
    story_id text,
    trader_id text,
    standing numeric,
    sort_order integer,
    primary key (story_id, trader_id)
);
create index if not exists idx_story_reward_trader_standing_story_id on story_reward_trader_standing(story_id);

create table if not exists story_reward_items
(
    story_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    primary key (story_id, item_id)
);
create index if not exists idx_story_reward_items_story_id on story_reward_items(story_id);
create index if not exists idx_story_reward_items_item_id on story_reward_items(item_id);

create table if not exists story_roadmap (
    id text primary key,
    node_type text,
    title_en text,
    title_ko text,
    title_ja text,
    contents_en text,
    contents_ko text,
    contents_ja text,
    desc_en text,
    desc_ko text,
    desc_ja text,
    value_text text,
    image text,
    popup_image text,
    popup_text text,
    x_coordinate numeric,
    y_coordinate numeric,
    edge jsonb,
    update_time timestamptz default now()
);

create table if not exists COMMUNITY_POSTS (
    id bigint PRIMARY KEY,
    slug text,
    user_email text,
    category text,
    title text,
    contents text,
    thumbnail text,
    delete_by_user boolean DEFAULT FALSE,
    delete_by_admin boolean DEFAULT FALSE,
    create_time timestamptz default now(),
    update_time timestamptz default now()
);
COMMENT ON COLUMN COMMUNITY_POSTS.ID IS '게시글 snoflake 아이디';
COMMENT ON COLUMN COMMUNITY_POSTS.SLUG IS '게시글 slug';
COMMENT ON COLUMN COMMUNITY_POSTS.user_email IS '게시글 사용자 이메일';
COMMENT ON COLUMN COMMUNITY_POSTS.CATEGORY IS '게시글 카테고리';
COMMENT ON COLUMN COMMUNITY_POSTS.TITLE IS '게시글 제목';
COMMENT ON COLUMN COMMUNITY_POSTS.CONTENTS IS '게시글 내용';
COMMENT ON COLUMN COMMUNITY_POSTS.THUMBNAIL IS '게시글 미리보기 사진';
COMMENT ON COLUMN COMMUNITY_POSTS.DELETE_BY_USER IS '게시글 유저 삭제 여부';
COMMENT ON COLUMN COMMUNITY_POSTS.DELETE_BY_ADMIN IS '게시글 관리자 삭제 여부';
COMMENT ON COLUMN COMMUNITY_POSTS.CREATE_TIME IS '게시글 생성 시간';
COMMENT ON COLUMN COMMUNITY_POSTS.UPDATE_TIME IS '게시글 업데이트 시간';
create index if not exists idx_community_posts_active_created
    on community_posts(create_time desc)
    where delete_by_user = false and delete_by_admin = false;
create index if not exists idx_community_posts_active_category_created
    on community_posts(category, create_time desc)
    where delete_by_user = false and delete_by_admin = false;
create index if not exists idx_community_posts_user_created
    on community_posts(user_email, create_time desc)
    where delete_by_user = false and delete_by_admin = false;

create table if not exists community_posts_views (
    post_id bigint PRIMARY KEY,
    view_count bigint DEFAULT 0
);
COMMENT ON COLUMN community_posts_views.post_id IS '게시글 snoflake 아이디';
COMMENT ON COLUMN community_posts_views.view_count IS '게시글 조회수';

create table if not exists community_posts_reactions (
    post_id bigint,
    user_email text,
    reaction_type SMALLINT,
    update_time timestamptz default now(),
    PRIMARY KEY (post_id, user_email)
);
COMMENT ON COLUMN community_posts_reactions.post_id IS '게시글 snoflake 아이디';
COMMENT ON COLUMN community_posts_reactions.user_email IS '리액션 누른 사용자 이메일';
COMMENT ON COLUMN community_posts_reactions.reaction_type IS '리액션 종류 (1: 좋아요, 2: 싫어요)';
COMMENT ON COLUMN community_posts_reactions.update_time IS '리액션 갱신 시간';

-- 조회 성능을 위한 인덱스
CREATE INDEX if not exists idx_post_reactions_post ON community_posts_reactions(post_id);

create table if not exists COMMUNITY_POSTS_HOT_ISSUE (
    post_id bigint PRIMARY KEY,
    issue_time timestamptz default now()
);
COMMENT ON COLUMN COMMUNITY_POSTS_HOT_ISSUE.post_id IS '게시글 snoflake 아이디';
COMMENT ON COLUMN COMMUNITY_POSTS_HOT_ISSUE.issue_time IS '게시글 핫이슈 시간';
create index if not exists idx_community_posts_hot_issue_time
    on community_posts_hot_issue(issue_time desc);

create table if not exists USER_FOLLOWS (
    follower_email text,
    following_email text,
    create_time timestamptz default now(),
    PRIMARY KEY (follower_email, following_email)
);
COMMENT ON COLUMN USER_FOLLOWS.follower_email IS '팔로잉 대상';
COMMENT ON COLUMN USER_FOLLOWS.following_email IS '팔로잉 한 유저';
COMMENT ON COLUMN USER_FOLLOWS.create_time IS '팔로잉 시작 날짜';

create table if not exists community_posts_bookmark (
    email text,
    post_id bigint,
    create_time timestamptz default now(),
    PRIMARY KEY (email, post_id)
);

-- 댓글

create table if not exists community_comments (
    id text PRIMARY KEY,                  -- nanoid
    parent_id text,
    post_id bigint,
    path LTREE,
    user_email text,
    contents text,
    delete_by_user boolean DEFAULT FALSE,
    delete_by_admin boolean DEFAULT FALSE,
    create_time timestamptz default now(),
    update_time timestamptz default now()
);

-- 성능 인덱스
CREATE INDEX if not exists idx_comments_path ON community_comments USING GIST (path);
CREATE INDEX if not exists idx_comments_post_id ON community_comments (post_id);

-- ilike 검색 인덱스
create index if not exists idx_posts_title_trgm on community_posts using gin (title gin_trgm_ops);
create index if not exists idx_posts_contents_trgm on community_posts using gin (contents gin_trgm_ops);
create index if not exists idx_comments_contents_trgm on community_comments using gin (contents gin_trgm_ops);

create table if not exists community_comments_reactions (
    comment_id text,
    email text,
    reaction_type SMALLINT, -- (1: 좋아요, 0: 싫어요, -1:무반응)
    reaction_time timestamptz default now(),
    PRIMARY KEY (comment_id, email)
);

create table if not exists user_block (
    id serial primary key,
    request_email text,
    target_email text,
    reason text,
    create_time timestamptz default now()
);
create index if not exists idx_user_block_request_target on user_block(request_email, target_email);

create table if not exists user_penalty (
    id serial primary key,
    email text,
    reason text,
    start_time timestamptz default now(),
    end_time timestamptz default now()
);

create table if not exists comment_report (
    id serial primary key,
    target_comment_id text,
    request_email text,
    target_email text,
    reason_type text,
    reason text,
    create_time timestamptz default now()
);

create table if not exists post_report (
    id serial primary key,
    target_post_id bigint,
    request_email text,
    target_email text,
    reason_type text,
    reason text,
    create_time timestamptz default now()
);

create table if not exists user_report (
    id serial primary key,
    request_email text,
    target_email text,
    reason_type text,
    reason text,
    request_time timestamptz default now()
);

create table if not exists user_notifications (
    id serial primary key,
    email text,
    noti_type text,
    payload jsonb,
    is_read boolean DEFAULT FALSE,
    create_time timestamptz default now()
);

create table if not exists live_map_floors
(
    id text primary key,
    map_id text,
    floor_no integer,
    name_en text,
    name_ko text,
    name_ja text,
    image text,
    map_bounds jsonb,
    default_zoom_level numeric,
    is_main boolean default false,
    min_y numeric,
    max_y numeric,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_floors_map_id on live_map_floors(map_id);
create unique index if not exists idx_live_map_floors_map_floor on live_map_floors(map_id, floor_no);

create table if not exists live_map_floor_zones
(
    id text primary key,
    floor_id text,
    map_id text,
    area_x_min numeric,
    area_x_max numeric,
    area_z_min numeric,
    area_z_max numeric,
    override_min_y numeric,
    override_max_y numeric,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_floor_zones_floor_id on live_map_floor_zones(floor_id);
create index if not exists idx_live_map_floor_zones_map_id on live_map_floor_zones(map_id);
create index if not exists idx_live_map_floor_zones_floor_sort on live_map_floor_zones(floor_id, sort_order, id);

create table if not exists live_map_points
(
    id text primary key,
    quest_id text,
    objective_id text,
    map_id text,
    floor_id text,
    x numeric,
    z numeric,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_points_objective_id
    on live_map_points(objective_id)
    where objective_id is not null;
create index if not exists idx_live_map_points_map_id on live_map_points(map_id);
create index if not exists idx_live_map_points_quest_id on live_map_points(quest_id);
create index if not exists idx_live_map_points_floor_id on live_map_points(floor_id);
create index if not exists idx_live_map_points_map_floor on live_map_points(map_id, floor_id);
create index if not exists idx_live_map_points_map_floor_id on live_map_points(map_id, floor_id, id);
create index if not exists idx_live_map_points_quest_floor_id on live_map_points(quest_id, floor_id, id);

create table if not exists live_map_point_details
(
    id text primary key,
    point_id text,
    description_en text,
    description_ko text,
    description_ja text,
    image text,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_point_details_point_id on live_map_point_details(point_id);

create table if not exists live_map_static_points
(
    id text primary key,
    map_id text,
    floor_id text,
    category text,
    name_en text,
    name_ko text,
    name_ja text,
    description_en text,
    description_ko text,
    description_ja text,
    image text,
    x numeric,
    z numeric,
    metadata jsonb,
    is_use boolean default false,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_static_points_map_id on live_map_static_points(map_id);
create index if not exists idx_live_map_static_points_category on live_map_static_points(category);
create index if not exists idx_live_map_static_points_map_category on live_map_static_points(map_id, category);
create index if not exists idx_live_map_static_points_floor_id on live_map_static_points(floor_id);
create index if not exists idx_live_map_static_points_is_use on live_map_static_points(is_use);
create index if not exists idx_live_map_static_points_map_sort on live_map_static_points(map_id, floor_id, category, sort_order, name_en);

create table if not exists live_map_btr_routes
(
    id text primary key,
    map_id text not null,
    name text not null,
    spawn_type text,
    raid_duration_seconds integer not null,
    spawn_remaining_seconds integer,
    stop_duration_seconds integer default 120,
    timing_variance_seconds integer default 120,
    is_use boolean default true,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_btr_routes_map_id on live_map_btr_routes(map_id);
create index if not exists idx_live_map_btr_routes_map_use_sort on live_map_btr_routes(map_id, is_use, sort_order);

create table if not exists live_map_btr_route_points
(
    id text primary key,
    route_id text not null,
    x numeric not null,
    z numeric not null,
    sort_order integer not null,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_btr_route_points_route_id on live_map_btr_route_points(route_id);
create unique index if not exists idx_live_map_btr_route_points_route_sort on live_map_btr_route_points(route_id, sort_order);

create table if not exists live_map_btr_route_stops
(
    id text primary key,
    route_id text not null,
    static_point_id text not null,
    route_point_id text,
    arrival_remaining_seconds integer not null,
    departure_remaining_seconds integer,
    visit_order integer not null,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_btr_route_stops_route_id on live_map_btr_route_stops(route_id);
create index if not exists idx_live_map_btr_route_stops_static_point on live_map_btr_route_stops(static_point_id);
create unique index if not exists idx_live_map_btr_route_stops_route_visit on live_map_btr_route_stops(route_id, visit_order);

create table if not exists live_map_story_points
(
    id text primary key,
    story_id text,
    objective_id text,
    map_id text,
    floor_id text,
    x numeric,
    z numeric,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_story_points_map_id on live_map_story_points(map_id);
create index if not exists idx_live_map_story_points_story_id on live_map_story_points(story_id);
create index if not exists idx_live_map_story_points_objective_id on live_map_story_points(objective_id);
create index if not exists idx_live_map_story_points_floor_id on live_map_story_points(floor_id);
create index if not exists idx_live_map_story_points_map_floor on live_map_story_points(map_id, floor_id);
create index if not exists idx_live_map_story_points_map_sort on live_map_story_points(map_id, sort_order, floor_id, id);

create table if not exists live_map_story_point_details
(
    id text primary key,
    point_id text,
    description_en text,
    description_ko text,
    description_ja text,
    image text,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_story_point_details_point_id on live_map_story_point_details(point_id);

create table if not exists live_map_story_requirement_points
(
    id text primary key,
    story_id text,
    requirement_id text,
    map_id text,
    floor_id text,
    x numeric,
    z numeric,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_story_requirement_points_story_id on live_map_story_requirement_points(story_id);
create index if not exists idx_live_map_story_requirement_points_requirement_id on live_map_story_requirement_points(requirement_id);
create index if not exists idx_live_map_story_requirement_points_map_id on live_map_story_requirement_points(map_id);
create index if not exists idx_live_map_story_requirement_points_floor_id on live_map_story_requirement_points(floor_id);
create index if not exists idx_live_map_story_requirement_points_map_floor on live_map_story_requirement_points(map_id, floor_id);
create index if not exists idx_live_map_story_requirement_points_map_sort on live_map_story_requirement_points(map_id, sort_order, floor_id, id);

create table if not exists live_map_story_requirement_point_details
(
    id text primary key,
    point_id text,
    description_en text,
    description_ko text,
    description_ja text,
    image text,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_story_requirement_point_details_point_id on live_map_story_requirement_point_details(point_id);
create index if not exists idx_live_map_story_requirement_point_details_point_sort on live_map_story_requirement_point_details(point_id, sort_order, id);

create table if not exists live_map_events
(
    id text primary key,
    trader_id text,
    title_en text,
    title_ko text,
    title_ja text,
    is_active boolean default true,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_events_trader_id on live_map_events(trader_id);
create index if not exists idx_live_map_events_active on live_map_events(is_active);

create table if not exists live_map_event_objectives
(
    objective_id text primary key,
    event_id text,
    parent_objective_id text,
    objective_type text,
    description_en text,
    description_ko text,
    description_ja text,
    count integer,
    is_optional boolean default false,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_event_objectives_event_id on live_map_event_objectives(event_id);
create index if not exists idx_live_map_event_objectives_parent_id on live_map_event_objectives(parent_objective_id);
create index if not exists idx_live_map_event_objectives_type on live_map_event_objectives(objective_type);
create index if not exists idx_live_map_event_objectives_event_sort on live_map_event_objectives(event_id, sort_order, objective_id);

create table if not exists live_map_event_objective_items
(
    objective_id text,
    item_id text,
    quantity integer,
    found_in_raid boolean,
    item_role text,
    sort_order integer,
    primary key (objective_id, item_id, item_role)
);
create index if not exists idx_live_map_event_objective_items_objective_id on live_map_event_objective_items(objective_id);
create index if not exists idx_live_map_event_objective_items_item_id on live_map_event_objective_items(item_id);

create table if not exists live_map_event_reward_trader_standing
(
    event_id text,
    trader_id text,
    standing numeric,
    sort_order integer,
    primary key (event_id, trader_id)
);
create index if not exists idx_live_map_event_reward_trader_standing_event_id on live_map_event_reward_trader_standing(event_id);

create table if not exists live_map_event_reward_items
(
    event_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    primary key (event_id, item_id)
);
create index if not exists idx_live_map_event_reward_items_event_id on live_map_event_reward_items(event_id);
create index if not exists idx_live_map_event_reward_items_item_id on live_map_event_reward_items(item_id);

create table if not exists live_map_event_reward_texts
(
    id text primary key,
    event_id text,
    reward_type text,
    description_en text,
    description_ko text,
    description_ja text,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_event_reward_texts_event_id on live_map_event_reward_texts(event_id);
create index if not exists idx_live_map_event_reward_texts_type on live_map_event_reward_texts(reward_type);
create index if not exists idx_live_map_event_reward_texts_event_sort on live_map_event_reward_texts(event_id, sort_order, id);

create table if not exists live_map_event_points
(
    id text primary key,
    event_id text,
    objective_id text,
    map_id text,
    floor_id text,
    x numeric,
    z numeric,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_event_points_event_id on live_map_event_points(event_id);
create index if not exists idx_live_map_event_points_objective_id on live_map_event_points(objective_id);
create index if not exists idx_live_map_event_points_map_id on live_map_event_points(map_id);
create index if not exists idx_live_map_event_points_floor_id on live_map_event_points(floor_id);
create index if not exists idx_live_map_event_points_map_floor on live_map_event_points(map_id, floor_id);
create index if not exists idx_live_map_event_points_map_sort on live_map_event_points(map_id, sort_order, floor_id, id);

create table if not exists live_map_event_point_details
(
    id text primary key,
    point_id text,
    description_en text,
    description_ko text,
    description_ja text,
    image text,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_live_map_event_point_details_point_id on live_map_event_point_details(point_id);

-- 배틀패스 시즌
create table if not exists battle_pass_seasons
(
    id text primary key,
    code text not null unique,
    title_en text,
    title_ko text,
    title_ja text,
    description_en text,
    description_ko text,
    description_ja text,
    page_count integer not null default 0 check (page_count >= 0),
    start_time timestamptz,
    end_time timestamptz,
    is_active boolean not null default true,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_battle_pass_seasons_active on battle_pass_seasons(is_active);

-- 시즌별 페이지와 이전 페이지 보상 획득 해금 조건
create table if not exists battle_pass_pages
(
    season_id text not null,
    page_number integer not null check (page_number > 0),
    required_previous_page_reward_count integer not null default 0
        check (required_previous_page_reward_count >= 0),
    sort_order integer,
    update_time timestamptz default now(),
    primary key (season_id, page_number),
    constraint fk_battle_pass_pages_season
        foreign key (season_id) references battle_pass_seasons(id) on delete cascade
);
create index if not exists idx_battle_pass_pages_season on battle_pass_pages(season_id, page_number);

-- 시즌에서 사용하는 교환 문서 및 유료 문서
create table if not exists battle_pass_documents
(
    id text primary key,
    season_id text not null,
    name_en text not null,
    name_ko text,
    name_ja text,
    image text,
    document_role text not null default 'exchange'
        check (document_role in ('exchange', 'classified')),
    is_use boolean not null default true,
    sort_order integer,
    update_time timestamptz default now(),
    constraint fk_battle_pass_documents_season
        foreign key (season_id) references battle_pass_seasons(id) on delete cascade
);
create index if not exists idx_battle_pass_documents_season on battle_pass_documents(season_id, sort_order);

-- 페이지에 표시되는 보상
create table if not exists battle_pass_rewards
(
    id text primary key,
    season_id text not null,
    page_number integer not null check (page_number > 0),
    reward_type text not null,
    name_en text not null,
    name_ko text,
    name_ja text,
    image text,
    reward_quantity integer not null default 1 check (reward_quantity > 0),
    document_price integer not null default 0 check (document_price >= 0),
    is_use boolean not null default true,
    sort_order integer not null default 0,
    update_time timestamptz default now(),
    constraint uq_battle_pass_rewards_page_sort
        unique (season_id, page_number, sort_order),
    constraint fk_battle_pass_rewards_season
        foreign key (season_id) references battle_pass_seasons(id) on delete cascade
);
create index if not exists idx_battle_pass_rewards_page on battle_pass_rewards(season_id, page_number, sort_order);
create index if not exists idx_battle_pass_rewards_type on battle_pass_rewards(reward_type);

-- 보상을 교환할 때 필요한 문서
create table if not exists battle_pass_reward_requirements
(
    reward_id text not null,
    document_id text not null,
    quantity integer not null check (quantity > 0),
    sort_order integer,
    primary key (reward_id, document_id),
    constraint fk_battle_pass_reward_requirements_reward
        foreign key (reward_id) references battle_pass_rewards(id) on delete cascade,
    constraint fk_battle_pass_reward_requirements_document
        foreign key (document_id) references battle_pass_documents(id) on delete cascade
);
create index if not exists idx_battle_pass_requirements_reward on battle_pass_reward_requirements(reward_id, sort_order);
create index if not exists idx_battle_pass_requirements_document on battle_pass_reward_requirements(document_id);

-- 프레스티지 단계
create table if not exists prestige_levels
(
    id text primary key,
    prestige_level integer not null unique check (prestige_level > 0),
    name_key text,
    name_en text,
    name_ko text,
    name_ja text,
    icon_link text,
    image_link text,
    is_use boolean not null default true,
    sort_order integer,
    update_time timestamptz default now()
);
create index if not exists idx_prestige_levels_use on prestige_levels(is_use, prestige_level);

-- 프레스티지 달성 조건
create table if not exists prestige_conditions
(
    id text primary key,
    prestige_id text not null,
    condition_type text not null,
    description_key text,
    description_en text,
    description_ko text,
    description_ja text,
    count integer,
    is_optional boolean not null default false,
    player_level integer,
    task_id text,
    station_id text,
    station_level integer,
    skill_name text,
    skill_level integer,
    dog_tag_level integer,
    max_durability numeric,
    min_durability numeric,
    found_in_raid boolean,
    sort_order integer,
    update_time timestamptz default now(),
    constraint fk_prestige_conditions_level
        foreign key (prestige_id) references prestige_levels(id) on delete cascade
);
create index if not exists idx_prestige_conditions_level on prestige_conditions(prestige_id, sort_order, id);
create index if not exists idx_prestige_conditions_type on prestige_conditions(condition_type);
create index if not exists idx_prestige_conditions_task on prestige_conditions(task_id);
create index if not exists idx_prestige_conditions_station on prestige_conditions(station_id);

create table if not exists prestige_condition_items
(
    condition_id text not null,
    item_id text not null,
    sort_order integer,
    primary key (condition_id, item_id),
    constraint fk_prestige_condition_items_condition
        foreign key (condition_id) references prestige_conditions(id) on delete cascade
);
create index if not exists idx_prestige_condition_items_item on prestige_condition_items(item_id);

create table if not exists prestige_condition_statuses
(
    condition_id text not null,
    status text not null,
    sort_order integer,
    primary key (condition_id, status),
    constraint fk_prestige_condition_statuses_condition
        foreign key (condition_id) references prestige_conditions(id) on delete cascade
);

create table if not exists prestige_condition_maps
(
    condition_id text not null,
    map_id text not null,
    sort_order integer,
    primary key (condition_id, map_id),
    constraint fk_prestige_condition_maps_condition
        foreign key (condition_id) references prestige_conditions(id) on delete cascade
);
create index if not exists idx_prestige_condition_maps_map on prestige_condition_maps(map_id);

-- 프레스티지 보상
create table if not exists prestige_reward_items
(
    prestige_id text not null,
    item_id text not null,
    quantity integer not null check (quantity > 0),
    attributes jsonb not null default '{}'::jsonb,
    sort_order integer,
    primary key (prestige_id, item_id),
    constraint fk_prestige_reward_items_level
        foreign key (prestige_id) references prestige_levels(id) on delete cascade
);
create index if not exists idx_prestige_reward_items_item on prestige_reward_items(item_id);

create table if not exists prestige_reward_skills
(
    prestige_id text not null,
    skill_name text not null,
    skill_level integer not null,
    sort_order integer,
    primary key (prestige_id, skill_name),
    constraint fk_prestige_reward_skills_level
        foreign key (prestige_id) references prestige_levels(id) on delete cascade
);

-- 퀘스트와 프레스티지에서 공통으로 사용하는 커스터마이징 본체
create table if not exists customizations
(
    id text primary key,
    name_key text,
    name_en text,
    name_ko text,
    name_ja text,
    image_link text,
    customization_type text,
    customization_type_name_key text,
    customization_type_name_en text,
    customization_type_name_ko text,
    customization_type_name_ja text,
    update_time timestamptz default now()
);
create index if not exists idx_customizations_type on customizations(customization_type);

create table if not exists customization_items
(
    customization_id text not null,
    item_id text not null,
    sort_order integer,
    primary key (customization_id, item_id),
    constraint fk_customization_items_customization
        foreign key (customization_id)
            references customizations(id)
            on delete cascade
);
create index if not exists idx_customization_items_item on customization_items(item_id);

-- 프레스티지와 커스터마이징 보상의 연결
create table if not exists prestige_reward_customizations
(
    prestige_id text not null,
    customization_id text not null,
    sort_order integer,
    primary key (prestige_id, customization_id),
    constraint fk_prestige_reward_customizations_level
        foreign key (prestige_id) references prestige_levels(id) on delete cascade,
    constraint fk_prestige_reward_customizations_customization
        foreign key (customization_id) references customizations(id) on delete cascade
);
create index if not exists idx_prestige_reward_customizations_level on prestige_reward_customizations(prestige_id, sort_order, customization_id);

-- 퀘스트의 시작/완료/실패 커스터마이징 보상
create table if not exists quest_reward_customizations
(
    quest_id text not null,
    customization_id text not null,
    reward_type text not null
        check (reward_type in ('start', 'finish', 'failure')),
    sort_order integer,
    update_time timestamptz default now(),
    primary key (quest_id, customization_id, reward_type),
    constraint fk_quest_reward_customizations_quest
        foreign key (quest_id) references quests(id) on delete cascade,
    constraint fk_quest_reward_customizations_customization
        foreign key (customization_id) references customizations(id) on delete cascade
);
create index if not exists idx_quest_reward_customizations_customization on quest_reward_customizations(customization_id);
create index if not exists idx_quest_reward_customizations_type on quest_reward_customizations(reward_type, customization_id);

-- 프레스티지 이후 이전 가능한 아이템 및 스킬 설정
create table if not exists prestige_transfer_settings
(
    id text primary key,
    prestige_id text not null,
    setting_type text not null check (setting_type in ('item_grid', 'skill')),
    name_key text,
    name_en text,
    name_ko text,
    name_ja text,
    skill_type text,
    transfer_rate numeric,
    grid_width integer,
    grid_height integer,
    sort_order integer,
    update_time timestamptz default now(),
    constraint fk_prestige_transfer_settings_level
        foreign key (prestige_id) references prestige_levels(id) on delete cascade
);
create index if not exists idx_prestige_transfer_settings_level on prestige_transfer_settings(prestige_id, sort_order, id);
create index if not exists idx_prestige_transfer_settings_type on prestige_transfer_settings(setting_type);

create table if not exists prestige_transfer_filter_values
(
    transfer_setting_id text not null,
    filter_type text not null
        check (filter_type in (
            'allowed_category',
            'allowed_item',
            'excluded_category',
            'excluded_item'
        )),
    value_id text not null,
    sort_order integer,
    primary key (transfer_setting_id, filter_type, value_id),
    constraint fk_prestige_transfer_filters_setting
        foreign key (transfer_setting_id)
            references prestige_transfer_settings(id)
            on delete cascade
);
create index if not exists idx_prestige_transfer_filters_value on prestige_transfer_filter_values(filter_type, value_id);

-- Live Map 파티 V3: 목록 공개, 비밀번호 입장, 생성/참여 모두 로그인 필수.
-- UUID는 애플리케이션에서 생성하고 update_time은 V3 서비스에서 갱신한다.
-- 기본 정원은 서비스 설정으로 전달한다. 순간 핑/접속 상태는 이 테이블에 저장하지 않는다.
create table if not exists live_map_party_rooms
(
    id uuid primary key,
    name varchar(60) not null check (name ~ '[^[:space:]]'),
    map_id text not null,
    password_hash text not null check (password_hash ~ '[^[:space:]]'),
    is_locked boolean not null default false,
    max_members smallint not null check (max_members > 0),
    empty_since timestamptz,
    closed_at timestamptz,
    create_time timestamptz not null default now(),
    update_time timestamptz not null default now(),
    constraint fk_live_map_party_rooms_v3_map
        foreign key (map_id) references maps(id) on delete restrict
);
create index if not exists idx_live_map_party_rooms_v3_open
    on live_map_party_rooms(create_time desc, id) where closed_at is null;
create index if not exists idx_live_map_party_rooms_v3_open_map
    on live_map_party_rooms(map_id, create_time desc, id) where closed_at is null;
-- 종료된 방도 맵 FK 확인 대상이므로 전체 map_id 인덱스를 둔다.
create index if not exists idx_live_map_party_rooms_v3_map
    on live_map_party_rooms(map_id);
create index if not exists idx_live_map_party_rooms_v3_empty
    on live_map_party_rooms(empty_since)
    where closed_at is null and empty_since is not null;
create index if not exists idx_live_map_party_rooms_v3_name
    on live_map_party_rooms using gin(name gin_trgm_ops) where closed_at is null;

-- joined는 입장 자격이며 현재 WebSocket 연결 여부와 다르다.
-- 퇴장/강퇴 시 행을 유지하고, 재입장 시 같은 계정의 기존 행을 갱신한다.
create table if not exists live_map_party_members
(
    id uuid primary key,
    room_id uuid not null,
    user_email text not null,
    nickname varchar(30) not null check (nickname ~ '[^[:space:]]'),
    color varchar(7) not null check (color ~ '^#[0-9A-F]{6}$'),
    role text not null default 'member' check (role in ('owner', 'member')),
    status text not null default 'joined' check (status in ('joined', 'left', 'kicked')),
    joined_at timestamptz not null default now(),
    left_at timestamptz,
    create_time timestamptz not null default now(),
    update_time timestamptz not null default now(),
    constraint uq_live_map_party_members_v3_room_member unique (room_id, id),
    constraint uq_live_map_party_members_v3_room_user unique (room_id, user_email),
    constraint ck_live_map_party_members_v3_left_at check (
        (status = 'joined' and left_at is null)
        or (status in ('left', 'kicked') and left_at is not null and left_at >= joined_at)
    ),
    constraint fk_live_map_party_members_v3_room
        foreign key (room_id) references live_map_party_rooms(id) on delete cascade,
    constraint fk_live_map_party_members_v3_user
        foreign key (user_email) references user_info(email) on delete restrict
);
-- 최대 한 명만 보장한다. 방 생성/방장 양도 트랜잭션에서 방장 존재를 보장한다.
create unique index if not exists uq_live_map_party_members_v3_owner
    on live_map_party_members(room_id) where role = 'owner' and status = 'joined';
create unique index if not exists uq_live_map_party_members_v3_color
    on live_map_party_members(room_id, color) where status = 'joined';
create index if not exists idx_live_map_party_members_v3_status
    on live_map_party_members(room_id, status);
create index if not exists idx_live_map_party_members_v3_user
    on live_map_party_members(user_email);

-- 지속 마커: 기존 live map과 동일한 floor_id 및 x/z 좌표계를 사용한다.
-- 방 맵과 층 맵의 동일/부모 관계, 참여 권한, 정원은 V3 서비스에서 검증한다.
-- 방 맵은 생성 이후 고정한다. version은 수정 시 일치 조건으로 검사하고 증가시킨다.
create table if not exists live_map_party_markers
(
    id uuid primary key,
    room_id uuid not null,
    created_by_member_id uuid not null,
    map_id text not null references maps(id) on delete restrict,
    floor_id text not null,
    x numeric not null check (x::text not in ('NaN', 'Infinity', '-Infinity')),
    z numeric not null check (z::text not in ('NaN', 'Infinity', '-Infinity')),
    marker_type text not null default 'normal'
        check (marker_type in ('normal', 'danger', 'rally', 'target')),
    label varchar(100),
    version integer not null default 1 check (version > 0),
    create_time timestamptz not null default now(),
    update_time timestamptz not null default now(),
    constraint fk_live_map_party_markers_v3_room
        foreign key (room_id) references live_map_party_rooms(id) on delete cascade,
    constraint fk_live_map_party_markers_v3_member
        foreign key (room_id, created_by_member_id)
            references live_map_party_members(room_id, id) on delete no action,
    constraint fk_live_map_party_markers_v3_floor
        foreign key (floor_id) references live_map_floors(id) on delete restrict
);
create index if not exists idx_live_map_party_markers_v3_room_floor
    on live_map_party_markers(room_id, floor_id, id);
create index if not exists idx_live_map_party_markers_v3_member
    on live_map_party_markers(room_id, created_by_member_id);
create index if not exists idx_live_map_party_markers_v3_floor
    on live_map_party_markers(floor_id);

-- Live Map 채팅 V3: additive only; no changes to existing party/account rows.
create table if not exists live_map_chat_users (
    id uuid primary key,
    user_email text not null unique references user_info(email) on delete cascade,
    create_time timestamptz not null default now()
);
create table if not exists live_map_chat_messages (
    id uuid primary key,
    user_id uuid not null references live_map_chat_users(id) on delete cascade,
    channel text not null check (channel in ('lobby', 'party')),
    room_id uuid references live_map_party_rooms(id) on delete cascade,
    request_id uuid not null,
    message varchar(300) not null,
    create_time timestamptz not null default now(),
    deleted_at timestamptz,
    unique (user_id, request_id),
    check ((channel = 'lobby' and room_id is null) or (channel = 'party' and room_id is not null)),
    check (deleted_at is not null or message ~ '[^[:space:]]')
);
create index if not exists idx_chat_messages_history
    on live_map_chat_messages(channel, room_id, create_time desc, id desc);
create index if not exists idx_chat_messages_user on live_map_chat_messages(user_id, create_time desc);
create index if not exists idx_chat_messages_retention on live_map_chat_messages(create_time);
create index if not exists idx_chat_messages_room on live_map_chat_messages(room_id);
create table if not exists live_map_chat_blocks (
    user_id uuid not null references live_map_chat_users(id) on delete cascade,
    target_id uuid not null references live_map_chat_users(id) on delete cascade,
    create_time timestamptz not null default now(),
    primary key (user_id, target_id),
    check (user_id <> target_id)
);
create index if not exists idx_chat_blocks_target on live_map_chat_blocks(target_id);
create table if not exists live_map_chat_reports (
    id uuid primary key,
    user_id uuid not null references live_map_chat_users(id) on delete cascade,
    message_id uuid not null references live_map_chat_messages(id) on delete cascade,
    reason text not null check (reason in ('spam', 'abuse', 'inappropriate', 'personal_info', 'other')),
    detail varchar(1000),
    create_time timestamptz not null default now(),
    unique (user_id, message_id)
);
create index if not exists idx_chat_reports_message on live_map_chat_reports(message_id);
create index if not exists idx_chat_reports_time on live_map_chat_reports(create_time desc, id desc);
create table if not exists live_map_chat_restrictions (
    user_id uuid primary key references live_map_chat_users(id) on delete cascade,
    moderator_id uuid references live_map_chat_users(id) on delete set null,
    reason varchar(1000) not null,
    expires_at timestamptz,
    create_time timestamptz not null default now()
);
create index if not exists idx_chat_restrictions_moderator on live_map_chat_restrictions(moderator_id);
create table if not exists live_map_party_invitations (
    id uuid primary key,
    room_id uuid not null references live_map_party_rooms(id) on delete cascade,
    inviter_id uuid not null references live_map_chat_users(id) on delete cascade,
    invitee_id uuid not null references live_map_chat_users(id) on delete cascade,
    status text not null check (status in ('pending', 'accepted', 'rejected', 'revoked', 'expired')),
    status_reason text constraint ck_party_invitations_status_reason check (status_reason in (
        'cancelled', 'room_closed', 'room_full', 'already_joined', 'member_kicked', 'receiver_unavailable'
    )),
    expires_at timestamptz not null,
    create_time timestamptz not null default now(),
    update_time timestamptz not null default now(),
    check (inviter_id <> invitee_id)
);
create unique index if not exists uq_party_invitations_pending
    on live_map_party_invitations(room_id, invitee_id) where status = 'pending';
create index if not exists idx_party_invitations_invitee on live_map_party_invitations(invitee_id, status, create_time desc);
create index if not exists idx_party_invitations_inviter on live_map_party_invitations(inviter_id, create_time desc);
create index if not exists idx_party_invitations_expiry on live_map_party_invitations(status, expires_at);

-- Authenticated recruitment-chat connections; each tab/reconnect has its own row.
create table if not exists live_map_chat_connections (
    id uuid primary key,
    user_id uuid not null references live_map_chat_users(id) on delete cascade,
    connected_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    expires_at timestamptz not null,
    disconnected_at timestamptz,
    disconnect_reason text check (disconnect_reason in ('closed', 'expired')),
    check (last_seen_at >= connected_at and expires_at > last_seen_at),
    check ((disconnected_at is null and disconnect_reason is null)
        or (disconnected_at is not null and disconnected_at >= connected_at and disconnect_reason is not null))
);
create index if not exists idx_chat_connections_user_history
    on live_map_chat_connections(user_id, connected_at desc, id desc);
create index if not exists idx_chat_connections_history
    on live_map_chat_connections(connected_at desc, id desc);
create index if not exists idx_chat_connections_active
    on live_map_chat_connections(expires_at, user_id) where disconnected_at is null;

-- V3 per-user party invitation preferences. Missing row means allow=true.
create table if not exists live_map_chat_invite_preferences (
    user_id uuid primary key references live_map_chat_users(id) on delete cascade,
    allow_party_invites boolean not null default true,
    update_time timestamptz not null default now()
);
create index if not exists idx_party_invitations_pair_history
    on live_map_party_invitations(inviter_id, invitee_id, update_time desc);
