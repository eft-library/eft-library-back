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
    update_time timestamptz default now(),
    primary key (boss_id, map_id)
);
create index idx_boss_spawn_map_id on boss_spawn (map_id);

create table if not exists boss_item (
    boss_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    update_time timestamptz default now(),
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
    sort_order integer,
    image text,
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
    sort_order integer,
    mot_image_en text,
    mot_image_ko text,
    mot_image_ja text,
    three_image text,
    three_json jsonb,
    update_time timestamptz default now()
);

create table if not exists quests
(
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
    sort_order integer,
    wiki_url text,
    guide_en text,
    guide_ko text,
    guide_ja text,
    update_time timestamptz default now()
);

create table if not exists quest_objectives
(
    objective_id text primary key,
    quest_id text,
    sort_order integer,
    objective_type text,
    description_en text,
    description_ko text,
    description_ja text,
    location_in_map boolean,
    raw_data jsonb,
    update_time timestamptz default now()
);
create index idx_quest_objectives_quest_id on quest_objectives (quest_id);
create index idx_quest_objectives_quest_id_sort_order on quest_objectives (quest_id, sort_order);
create index idx_quest_objectives_objective_type on quest_objectives (objective_type);

create table if not exists quest_objective_items
(
    objective_id text,
    item_type text, -- all item / questItem / markerItem / requiredKey
    item_id text,
    sort_order integer,
    update_time timestamptz default now(),
    primary key (objective_id, item_type, item_id)
);
create index idx_quest_objective_items_item_id on quest_objective_items (item_id);
create index idx_quest_objective_items_item_type on quest_objective_items (item_type);
create index idx_quest_objective_items_objective_id_item_type on quest_objective_items (objective_id, item_type);

create table if not exists quest_objective_maps
(
    objective_id text,
    map_id text,
    sort_order integer,
    update_time timestamptz default now(),
    primary key (objective_id, map_id)
);
create index idx_quest_objective_maps_map_id on quest_objective_maps (map_id);

create table if not exists quest_relations
(
    quest_id text,
    related_quest_id text,
    relation_type text, -- require / next
    sort_order integer,
    update_time timestamptz default now(),
    primary key (quest_id, related_quest_id, relation_type)
);
create index idx_quest_relations_related_quest_id on quest_relations (related_quest_id);
create index idx_quest_relations_relation_type on quest_relations (relation_type);

create table if not exists quest_finish_rewards
(
    quest_id text,
    reward_type text, -- skill_level / offer_unlock / trader_standing
    target_id text,   -- trader_id, skill_name 등
    reward_value numeric,
    sort_order integer,
    raw_data jsonb,
    update_time timestamptz default now(),
    primary key (quest_id, reward_type, target_id, sort_order)
);
create index idx_quest_finish_rewards_quest_id on quest_finish_rewards (quest_id);
create index idx_quest_finish_rewards_reward_type on quest_finish_rewards (reward_type);
create index idx_quest_finish_rewards_target_id on quest_finish_rewards (target_id);

create table if not exists quest_finish_reward_items
(
    quest_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    update_time timestamptz default now(),
    primary key (quest_id, item_id, sort_order)
);
create index idx_quest_finish_reward_items_item_id on quest_finish_reward_items (item_id);

create table if not exists quest_finish_reward_craft_unlocks
(
    quest_id text,
    craft_id text,
    sation_level integer,
    sort_order integer,
    update_time timestamptz default now(),
    primary key (quest_id, craft_id)
);
create index idx_quest_finish_reward_craft_unlocks_craft_id on quest_finish_reward_craft_unlocks (craft_id);

create table if not exists traders
(
    id text primary key,
    name_en text,
    name_ko text,
    name_ja text,
    image text,
    sort_order integer,
    update_time timestamptz default now()
);

create table if not exists trader_barters
(
    id text primary key,
    trader_id text,
    level integer,
    update_time timestamptz default now()
);
create index idx_trader_barters_trader_id on trader_barters(trader_id);
create index idx_trader_barters_trader_id_level on trader_barters(trader_id, level);

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
    id serial primary key,
    autocomplete_text text,
    url text,
    lang text,
    category text,
    sort_order integer,
    update_time timestamptz default now()
);
create index idx_autocomplete_text on autocomplete_items using gin (autocomplete_text gin_trgm_ops);
create index idx_autocomplete_lang on autocomplete_items(lang);

create table if not exists news_items
(
    id text primary key,
    news_type text not null, -- event, patch, notice, recommend, next_update, tarkov_info
    title_en text,
    title_ko text,
    title_ja text,
    link text,
    is_new boolean default false,
    is_renewal boolean default false,
    sort_order integer,
    is_active boolean default true,
    update_time timestamptz default now()
);
create index idx_news_items_sort_order on news_items(sort_order);

create table if not exists hideout_master
(
    id text primary key,
    name_en text,
    name_ko text,
    name_ja text,
    update_time timestamptz default now()
);

create table if not exists hideout_levels
(
    id text primary key,
    master_id text,
    hideout_level integer,
    construction_time integer,
    update_time timestamptz default now()
);
create index idx_hideout_levels_hideout_id on hideout_levels(master_id);
create index idx_hideout_levels_hideout_id_level on hideout_levels(master_id, hideout_level);

create table if not exists hideout_item_require
(
    id text primary key,
    hideout_level_id text,
    item_id text,
    quantity integer,
    in_raid boolean,
    update_time timestamptz default now()
);
create index idx_hideout_item_require_level on hideout_item_require(hideout_level_id);
create index idx_hideout_item_require_item on hideout_item_require(item_id);

create table if not exists hideout_trader_require
(
    id text primary key,
    hideout_level_id text,
    trader_id text,
    trader_level integer,
    update_time timestamptz default now()
);
create index idx_hideout_trader_require_level on hideout_trader_require(hideout_level_id);
create index idx_hideout_trader_require_trader on hideout_trader_require(trader_id);

create table if not exists hideout_station_require
(
    id text primary key,
    hideout_level_id text,
    require_master_id text,
    station_level integer,
    update_time timestamptz default now()
);
create index idx_hideout_station_require_level on hideout_station_require(hideout_level_id);
create index idx_hideout_station_require_station on hideout_station_require(require_master_id);

create table if not exists hideout_crafts
(
    id text primary key,
    hideout_level_id text,
    reward_item_id text,
    duration numeric,
    reward_quantity numeric,
    update_time timestamptz default now()
);
create index idx_hideout_crafts_hideout_level_id on hideout_crafts(hideout_level_id);
create index idx_hideout_crafts_reward_item_id on hideout_crafts(reward_item_id);
create index idx_hideout_crafts_hideout_level_reward_item on hideout_crafts(hideout_level_id, reward_item_id);

create table if not exists hideout_craft_require_items
(
    id text primary key,
    craft_id text,
    item_id text,
    quantity integer,
    update_time timestamptz default now()
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
    image text,
    update_time timestamptz default now()
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
    bonus_value numeric(10, 4),
    update_time timestamptz default now()
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

create table if not exists user_quest
(
  email text primary key,
  quest_list text[],
  update_time timestamptz default now()
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
    id text primary key,
    TRADER jsonb,
    update_time timestamptz default now()
);

create table if not exists item_trader_prices
(
    id text primary key,
    item_id text,
    game_mode text, -- 'pve' | 'pvp'
    trader_id text,
    price numeric,
    update_time timestamptz default now()
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
    execute_time timestamptz default now(),
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
    category text,
    name_en text,
    name_ko text,
    name_ja text,
    weight numeric,
    width integer,
    height integer,
    normalized_name text,
    image text,
    update_time timestamptz default now()
);
create index idx_items_category on items(category);
create index idx_items_normalized_name on items(normalized_name);
create index idx_items_update_time on items(update_time desc);

create table if not exists ammo_items (
    item_id text primary key,
    damage integer,
    armor_damage integer,
    penetration_power integer,
    recoil_modifier numeric,
    accuracy_modifier numeric,
    heavy_bleed_modifier numeric,
    light_bleed_modifier numeric,
    efficiency jsonb
);

create table if not exists armor_items (
    item_id text primary key,
    armor_type text, -- ArmorVest, Headwear, FaceCover, Rig ...
    class_value integer,
    durability integer,
    material_name text,
    ergo_penalty numeric,
    turn_penalty numeric,
    speed_penalty numeric,
    ricochet_chance_en text,
    ricochet_chance_ko text,
    ricochet_chance_ja text,
    deafening text,
    blindness_protection numeric,
    zones jsonb
);
create index idx_armor_items_armor_type on armor_items(armor_type);
create index idx_armor_items_class_value on armor_items(class_value);

create table if not exists storage_items (
    item_id text primary key,
    storage_type text, -- Backpack, Container, Rig
    capacity integer,
    grids jsonb
);
create index idx_storage_items_storage_type on storage_items(storage_type);

create table if not exists gun_items (
    item_id text primary key,
    gun_category text,
    caliber text,
    fire_rate integer,
    ergonomics numeric,
    recoil_vertical numeric,
    recoil_horizontal numeric,
    default_ammo text,
    modes jsonb
);
create index idx_gun_items_gun_category on gun_items(gun_category);

create table if not exists gun_allowed_ammo (
    item_id text,
    ammo_id text,
    primary key (item_id, ammo_id)
);

create table if not exists consumable_items (
    item_id text primary key,
    consumable_type text, -- Medical / Provisions
    medical_category text,
    uses integer,
    use_time numeric,
    hitpoints integer,
    energy integer,
    hydration integer,
    painkiller_duration integer,
    energy_impact integer,
    hydration_impact integer,
    units integer,
    cures jsonb,
    buff jsonb,
    malus jsonb,
    de_buff jsonb,
    advantage jsonb,
    stim_effects jsonb
);
create index idx_consumable_items_consumable_type on consumable_items(consumable_type);
create index idx_consumable_items_medical_category on consumable_items(medical_category);

create table if not exists where_am_i
(
    id text primary key,
    image text,
    map_bounds jsonb,
    image_bounds jsonb,
    default_zoom_level numeric,
    update_time timestamptz default now()
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

create table if not exists response_time (
    id serial primary key,
    service_name text,
    response_ms numeric,
    checked_time timestamptz default now()
);

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

create table if not exists item_details
(
    ID text primary key,
    normalized_name text,
    HIDEOUT_ITEMS jsonb,
    USED_IN_CRAFTS jsonb,
    REWARDED_BY_NPCS jsonb,
    REWARDED_BY_QUESTS jsonb,
    REQUIRED_BY_QUEST_ITEM jsonb,
    REQUIRED_BY_QUEST_ITEM_ARRAY jsonb,
    REWARDED_BY_QUESTS_CRAFT_UNLOCK jsonb,
    REWARDED_BY_QUESTS_OFFER_UNLOCK jsonb,
    update_time timestamptz default now()
);
COMMENT ON COLUMN ITEM_DETAIL_I18N.ID IS '아이템 상세 아이디';
COMMENT ON COLUMN ITEM_DETAIL_I18N.normalized_name IS '아이템 상세 주소';
COMMENT ON COLUMN ITEM_DETAIL_I18N.HIDEOUT_ITEMS IS '아이템 상세 건설 필요';
COMMENT ON COLUMN ITEM_DETAIL_I18N.USED_IN_CRAFTS IS '아이템 상세 제작 필요';
COMMENT ON COLUMN ITEM_DETAIL_I18N.REWARDED_BY_NPCS IS '아이템 상세 상인 교환';
COMMENT ON COLUMN ITEM_DETAIL_I18N.REWARDED_BY_QUESTS IS '아이템 상세 퀘스트 보상';
COMMENT ON COLUMN ITEM_DETAIL_I18N.REQUIRED_BY_QUEST_ITEM IS '아이템 상세 퀘스트 아이템';
COMMENT ON COLUMN ITEM_DETAIL_I18N.REQUIRED_BY_QUEST_ITEM_ARRAY IS '아이템 상세 퀘스트 아이템 배열';
COMMENT ON COLUMN ITEM_DETAIL_I18N.REWARDED_BY_QUESTS_CRAFT_UNLOCK IS '아이템 상세 제작 잠금 해제';
COMMENT ON COLUMN ITEM_DETAIL_I18N.REWARDED_BY_QUESTS_OFFER_UNLOCK IS '아이템 상세 구매 잠금 해제';
COMMENT ON COLUMN ITEM_DETAIL_I18N.UPDATE_TIME IS '아이템 상세 업데이트 날짜';

create table if not exists RAG_SEARCH_I18N
(
  VALUE text,
  LANG text,
  update_time timestamptz default now(),
  primary key (VALUE, LANG)
);
COMMENT ON COLUMN RAG_SEARCH_I18N.VALUE IS '검색 드롭다운 값';
COMMENT ON COLUMN RAG_SEARCH_I18N.LANG IS '언어';
COMMENT ON COLUMN RAG_SEARCH_I18N.UPDATE_TIME IS '검색 업데이트 시간';

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
    PRIMARY KEY (user_email, post_id)
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
