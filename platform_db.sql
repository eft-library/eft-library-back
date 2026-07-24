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
create index idx_boss_spawn_map_id on boss_spawn (map_id);

create table if not exists boss_item (
    boss_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    primary key (boss_id, item_id)
);
create index idx_boss_item_item_id on boss_item (item_id);

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
create index idx_map_points_map_id on map_points(map_id);

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
create index idx_menu_sub_group_parent_group_id on menu_sub_groups(parent_group_id);

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
    sort_order integer,
    update_time timestamptz default now()
);


-- 퀘스트 관계(Relations)
create table if not exists quest_relations (
    quest_id text,
    related_quest_id text,
    relation_type text, -- require(선행), next(후행)
    sort_order integer,
    primary key (quest_id, related_quest_id, relation_type)
);
create index idx_quest_relations_quest_id on quest_relations (quest_id);
create index idx_quest_relations_relation_type on quest_relations (relation_type);

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
    sort_order integer,
    primary key (objective_id, quest_id)
);
create index idx_quest_objectives_quest_id on quest_objectives (quest_id);
create index idx_quest_objectives_type on quest_objectives (type);
create index if not exists idx_quest_objectives_quest_sort on quest_objectives(quest_id, sort_order, objective_id);

-- 목표에 필요한 아이템
create table if not exists quest_objective_items (
    objective_id text,
    item_id text,
    item_type text, -- item/questItem/markerItem/requiredKey 등
    sort_order integer,
    primary key (objective_id, item_id, item_type)
);
create index idx_quest_objective_items_objective_id on quest_objective_items (objective_id);
create index idx_quest_objective_items_item_id on quest_objective_items (item_id);

-- 목표에 필요한 키(OR 그룹 지원)
create table if not exists quest_objective_required_keys (
    objective_id text,
    key_id text,
    primary key (objective_id, key_id)
);
create index idx_quest_objective_required_keys_objective_id on quest_objective_required_keys (objective_id);

-- 목표와 맵의 연관
create table if not exists quest_objective_maps (
    objective_id text,
    map_id text,
    sort_order integer,
    primary key (objective_id, map_id)
);
create index idx_quest_objective_maps_objective_id on quest_objective_maps (objective_id);
create index idx_quest_objective_maps_map_id on quest_objective_maps (map_id);


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
create index idx_quest_finish_reward_skills_quest_id on quest_finish_reward_skills (quest_id);

-- 퀘스트 완료 보상(트레이더 평판)
create table if not exists quest_finish_reward_trader_standing (
    quest_id text,
    trader_id text,
    standing numeric,
    sort_order integer,
    primary key (quest_id, trader_id)
);
create index idx_quest_finish_reward_trader_standing_quest_id on quest_finish_reward_trader_standing (quest_id);

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
create index idx_quest_finish_reward_offer_unlock_quest_id on quest_finish_reward_offer_unlock (quest_id);

-- 퀘스트 완료 보상(아이템)
create table if not exists quest_finish_reward_items (
    quest_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    primary key (quest_id, item_id)
);
create index idx_quest_finish_reward_items_quest_id on quest_finish_reward_items (quest_id);
create index idx_quest_finish_reward_items_item_id on quest_finish_reward_items (item_id);

-- 퀘스트 완료 보상(제작 해금)
create table if not exists quest_finish_reward_craft_unlocks (
    quest_id text,
    craft_id text,
    station_level integer,
    sort_order integer,
    primary key (quest_id, craft_id)
);
create index idx_quest_finish_reward_craft_unlocks_quest_id on quest_finish_reward_craft_unlocks (quest_id);
create index idx_quest_finish_reward_craft_unlocks_craft_id on quest_finish_reward_craft_unlocks (craft_id);

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

create index idx_trader_barters_trader_id on trader_barters(trader_id);
create index idx_trader_barters_trader_id_level on trader_barters(trader_id, trader_level);

create table if not exists barter_required_items
(
    id text primary key,
    barter_id text,
    item_id text,
    quantity integer
);
create index idx_barter_required_items_barter_id on barter_required_items(barter_id);
create index idx_barter_required_items_item_id on barter_required_items(item_id);

create table if not exists barter_reward_items
(
    id text primary key,
    barter_id text,
    item_id text,
    quantity integer
);
create index idx_barter_reward_items_barter_id on barter_reward_items(barter_id);
create index idx_barter_reward_items_item_id on barter_reward_items(item_id);

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
create index idx_news_items_sort_order on news_items(sort_order);

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
create index idx_hideout_levels_hideout_id on hideout_levels(master_id);
create index idx_hideout_levels_hideout_id_level on hideout_levels(master_id, hideout_level);

create table if not exists hideout_item_require
(
    id text primary key,
    hideout_level_id text,
    item_id text,
    quantity integer,
    in_raid boolean
);
create index idx_hideout_item_require_level on hideout_item_require(hideout_level_id);
create index idx_hideout_item_require_item on hideout_item_require(item_id);

create table if not exists hideout_trader_require
(
    id text primary key,
    hideout_level_id text,
    trader_id text,
    trader_level integer
);
create index idx_hideout_trader_require_level on hideout_trader_require(hideout_level_id);
create index idx_hideout_trader_require_trader on hideout_trader_require(trader_id);

create table if not exists hideout_station_require
(
    id text primary key,
    hideout_level_id text,
    require_master_id text,
    station_level integer
);
create index idx_hideout_station_require_level on hideout_station_require(hideout_level_id);
create index idx_hideout_station_require_station on hideout_station_require(require_master_id);

create table if not exists hideout_crafts
(
    id text primary key,
    hideout_level_id text,
    reward_item_id text,
    duration numeric,
    reward_quantity numeric
);
create index idx_hideout_crafts_hideout_level_id on hideout_crafts(hideout_level_id);
create index idx_hideout_crafts_reward_item_id on hideout_crafts(reward_item_id);
create index idx_hideout_crafts_hideout_level_reward_item on hideout_crafts(hideout_level_id, reward_item_id);

create table if not exists hideout_craft_require_items
(
    id text primary key,
    craft_id text,
    item_id text,
    quantity numeric
);
create index idx_craft_require_items_craft on hideout_craft_require_items(craft_id);
create index idx_craft_require_items_item on hideout_craft_require_items(item_id);
create index idx_craft_require_items_craft_item on hideout_craft_require_items(craft_id, item_id);

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
create index idx_hideout_skill_require_level on hideout_skill_require(hideout_level_id);

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
create index idx_hideout_bonus_level on hideout_bonus(hideout_level_id);

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

create table if not exists item_prices
(
    item_id text,
    game_mode text,
    highest_trader_price numeric,
    highest_trader_id text,
    flea_market_price numeric,
    trader_count integer,
    has_flea boolean,
    update_time timestamptz default now(),
    primary key (item_id, game_mode)
);

create table if not exists item_trader_prices
(
    id text primary key,
    item_id text,
    game_mode text, -- 'pve' | 'pvp'
    trader_id text,
    price numeric
);
create index idx_item_trader_prices_item_id on item_trader_prices(item_id);
create index idx_item_trader_prices_trader_id on item_trader_prices(trader_id);
create index idx_item_trader_prices_item_mode on item_trader_prices(item_id, game_mode);

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
    price_time timestamptz default now(),
    PRIMARY KEY (item_id, game_mode, price_time)
);
create index idx_item_price_history_time on item_price_history(price_time desc);

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

create table if not exists 
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
create index idx_user_footprint_request_time on user_footprint (request_time desc);

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

create table if not exists USER_PROGRESS_ITEM
(
  email text,
  progress_type text,
  item_list text[],
  update_time timestamptz default now(),
  PRIMARY KEY (email, progress_type)
);

create table if not exists progress_item (
    id text primary key,
    progress_type text,
    update_time timestamptz default now()
);
CREATE INDEX idx_progress_item_type ON progress_item (progress_type);

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

create table if not exists user_minigame_score (
  id serial primary key,
  nickname text,
  game_type text,
  score bigint,
  create_time timestamptz default now()
);
CREATE INDEX idx_minigame_score_rank ON user_minigame_score (game_type, score DESC, create_time ASC);

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
COMMENT ON COLUMN community_posts_reactions.update_time IS '게시글 snoflake 아이디';

-- 조회 성능을 위한 인덱스
CREATE INDEX idx_post_reactions_post ON community_posts_reactions(post_id);

create table if not exists COMMUNITY_POSTS_HOT_ISSUE (
    post_id bigint PRIMARY KEY,
    issue_time timestamptz default now()
);
COMMENT ON COLUMN COMMUNITY_POSTS_HOT_ISSUE.post_id IS '게시글 snoflake 아이디';
COMMENT ON COLUMN COMMUNITY_POSTS_HOT_ISSUE.post_id IS '게시글 핫이슈 시간';
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
CREATE EXTENSION IF NOT EXISTS ltree;

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
CREATE INDEX idx_comments_path ON community_comments USING GIST (path);
CREATE INDEX idx_comments_post_id ON community_comments (post_id);

-- ilike 검색 인덱스
create extension if not exists pg_trgm;
create index idx_posts_title_trgm on community_posts using gin (title gin_trgm_ops);
create index idx_posts_contents_trgm on community_posts using gin (contents gin_trgm_ops);
create index idx_comments_contents_trgm on community_comments using gin (contents gin_trgm_ops);

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
create index idx_live_map_floors_map_id on live_map_floors(map_id);
create unique index idx_live_map_floors_map_floor on live_map_floors(map_id, floor_no);

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
create index idx_live_map_points_objective_id
    on live_map_points(objective_id)
    where objective_id is not null;
create index idx_live_map_points_map_id on live_map_points(map_id);
create index idx_live_map_points_quest_id on live_map_points(quest_id);
create index idx_live_map_points_floor_id on live_map_points(floor_id);
create index idx_live_map_points_map_floor on live_map_points(map_id, floor_id);
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
create index idx_live_map_point_details_point_id on live_map_point_details(point_id);

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
    sort_order integer,
    update_time timestamptz default now()
);
create index idx_live_map_static_points_map_id on live_map_static_points(map_id);
create index idx_live_map_static_points_category on live_map_static_points(category);
create index idx_live_map_static_points_map_category on live_map_static_points(map_id, category);
create index idx_live_map_static_points_floor_id on live_map_static_points(floor_id);
create index if not exists idx_live_map_static_points_map_sort on live_map_static_points(map_id, floor_id, category, sort_order, name_en);

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
