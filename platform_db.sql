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
    count integer,
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
    name_en text,
    name_ko text,
    name_ja text,
    parent_map_id text,
    map_depth integer,
    sort_order integer,
    url text,
    mot_image_en text,
    mot_image_ko text,
    mot_image_ja text,
    three_image text,
    three_json jsonb,
    update_time timestamptz default now()
);

create table if not exists QUEST_I18N
(
    id text primary key,
    normalized_name text,
    name jsonb,
    npc_id text,
    lightkeeper_required boolean,
    kappa_required boolean,
    task_requirements jsonb,
    task_next jsonb,
    objectives jsonb,
    WIKI_URL text,
    finish_rewards jsonb,
    min_player_level integer,
    guide jsonb,
    sort_order integer,
    update_time timestamptz default now()
);
COMMENT ON COLUMN QUEST_I18N.id IS 'Quest ID';
COMMENT ON COLUMN QUEST_I18N.name IS 'Quest 이름';
COMMENT ON COLUMN QUEST_I18N.npc_id IS 'Quest npc id';
COMMENT ON COLUMN QUEST_I18N.lightkeeper_required IS 'Quest 라이트키퍼 여부';
COMMENT ON COLUMN QUEST_I18N.kappa_required IS 'Quest 카파 여부';
COMMENT ON COLUMN QUEST_I18N.task_requirements IS 'Quest 선행 퀘스트 목록';
COMMENT ON COLUMN QUEST_I18N.task_next IS 'Quest 후행 퀘스트 목록';
COMMENT ON COLUMN QUEST_I18N.objectives IS 'Quest 목표 목록';
COMMENT ON COLUMN QUEST_I18N.WIKI_URL IS 'Quest 위키 주소';
COMMENT ON COLUMN QUEST_I18N.GUIDE IS 'Quest 가이드';
COMMENT ON COLUMN QUEST_I18N.finish_rewards IS 'Quest 완료 보상 목록';
COMMENT ON COLUMN QUEST_I18N.min_player_level IS 'Quest 레벨 조건';
COMMENT ON COLUMN QUEST_I18N.normalized_name IS 'Quest url mapping';
COMMENT ON COLUMN QUEST_I18N.sort_order IS 'Quest 정렬';
COMMENT ON COLUMN QUEST_I18N.update_time IS 'Quest 업데이트 시간';

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

create table trader_barters
(
    id text primary key,
    trader_id text,
    level integer,
    update_time timestamptz default now()
);
create index idx_trader_barters_trader_id on trader_barters(trader_id);
create index idx_trader_barters_trader_id_level on trader_barters(trader_id, level);

create table barter_required_items
(
    id text primary key,
    barter_id text,
    item_id text,
    quantity integer
);
create index idx_barter_required_items_barter_id on barter_required_items(barter_id);
create index idx_barter_required_items_item_id on barter_required_items(item_id);

create table barter_reward_items
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
    hideout_id text,
    hideout_level integer,
    construction_time integer,
    update_time timestamptz default now()
);
create index idx_hideout_levels_hideout_id on hideout_levels(hideout_id);
create index idx_hideout_levels_hideout_id_level on hideout_levels(hideout_id, hideout_level);

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
    hideout_id text,
    hideout_level_id text,
    station_level integer,
    update_time timestamptz default now()
);
create index idx_hideout_station_require_level on hideout_station_require(hideout_level_id);
create index idx_hideout_station_require_station on hideout_station_require(hideout_id);

create table if not exists hideout_crafts
(
    id text primary key,
    hideout_level_id text,
    station_level integer,
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

create table if not exists USER_INFO
(
  EMAIL text  primary key,
  NAME text,
  NICKNAME text,
  IS_ADMIN boolean,
  ATTENDANCE_COUNT integer,
  LAST_UPDATE_NICKNAME timestamptz default now(),
  CREATE_TIME timestamptz default now(),
  ATTENDANCE_TIME timestamp with time zone
);
COMMENT ON COLUMN USER_INFO.NAME IS '사용자 이름';
COMMENT ON COLUMN USER_INFO.EMAIL IS '사용자 이메일';
COMMENT ON COLUMN USER_INFO.NICKNAME IS '사용자 별명';
COMMENT ON COLUMN USER_INFO.IS_ADMIN IS '사용자 운영자 여부';
COMMENT ON COLUMN USER_INFO.ATTENDANCE_COUNT IS '사용자 출석일 수';
COMMENT ON COLUMN USER_INFO.LAST_UPDATE_NICKNAME IS '사용자 닉네임 마지막 수정 일자';
COMMENT ON COLUMN USER_INFO.CREATE_TIME IS '사용자 생성일';
COMMENT ON COLUMN USER_INFO.ATTENDANCE_TIME IS '사용자 최근 출석 날짜';

create table if not exists USER_QUEST
(
  user_email text,
  QUEST_LIST text[],
  update_time timestamptz default now(),
  PRIMARY KEY (user_email)
);
COMMENT ON COLUMN USER_QUEST.user_email IS '사용자 이메일';
COMMENT ON COLUMN USER_QUEST.QUEST_LIST IS '사용자 퀘스트 리스트';
COMMENT ON COLUMN USER_QUEST.UPDATE_TIME IS '사용자 퀘스트 업데이트 시간';

create table if not exists INFORMATION_I18N
(
    ID text primary key,
    TYPE text,
    NAME jsonb,
    DESCRIPTION jsonb,
    update_time timestamptz default now()
);
COMMENT ON COLUMN INFORMATION_I18N.ID IS '패치 노트 ID';
COMMENT ON COLUMN INFORMATION_I18N.NAME IS '패치 노트 이름';
COMMENT ON COLUMN INFORMATION_I18N.DESCRIPTION IS '패치 노트 내용';
COMMENT ON COLUMN INFORMATION_I18N.UPDATE_TIME IS '패치 노트 업데이트 시간';

CREATE INDEX idx_information_i18n_type ON INFORMATION_I18N(TYPE);
CREATE INDEX idx_information_i18n_type_update_time ON INFORMATION_I18N(TYPE, UPDATE_TIME DESC);

create table if not exists USER_ROADMAP
(
    user_email text primary key,
    QUEST_LIST text[],
    update_time timestamptz default now()
);
COMMENT ON COLUMN USER_ROADMAP.user_email IS '로드맵 사용자 이메일';
COMMENT ON COLUMN USER_ROADMAP.QUEST_LIST IS '로드맵 완료한 퀘스트 정보';
COMMENT ON COLUMN USER_ROADMAP.UPDATE_TIME IS '로드맵 업데이트 날짜';

create table if not exists ROADMAP_NODE
(
    ID text primary key,
    TOTAL_X_COORDINATE numeric,
    TOTAL_Y_COORDINATE numeric,
    SINGLE_X_COORDINATE numeric,
    SINGLE_Y_COORDINATE numeric,
    TOTAL_KAPPA_X_COORDINATE numeric,
    TOTAL_KAPPA_Y_COORDINATE numeric,
    SINGLE_KAPPA_X_COORDINATE numeric,
    SINGLE_KAPPA_Y_COORDINATE numeric,
    NODE_COLOR text,
    update_time timestamptz default now()
);
COMMENT ON COLUMN ROADMAP_NODE.ID IS '로드맵 퀘스트 아이디';
COMMENT ON COLUMN ROADMAP_NODE.TOTAL_X_COORDINATE IS '로드맵 전체 X 좌표';
COMMENT ON COLUMN ROADMAP_NODE.TOTAL_Y_COORDINATE IS '로드맵 전체 Y 좌표';
COMMENT ON COLUMN ROADMAP_NODE.SINGLE_X_COORDINATE IS '로드맵 싱글 X 좌표';
COMMENT ON COLUMN ROADMAP_NODE.SINGLE_Y_COORDINATE IS '로드맵 싱글 Y 좌표';
COMMENT ON COLUMN ROADMAP_NODE.TOTAL_X_COORDINATE IS '로드맵 카파 전체 X 좌표';
COMMENT ON COLUMN ROADMAP_NODE.TOTAL_Y_COORDINATE IS '로드맵 카파 전체 Y 좌표';
COMMENT ON COLUMN ROADMAP_NODE.SINGLE_X_COORDINATE IS '로드맵 카파 싱글 X 좌표';
COMMENT ON COLUMN ROADMAP_NODE.SINGLE_Y_COORDINATE IS '로드맵 카파 싱글 Y 좌표';
COMMENT ON COLUMN ROADMAP_NODE.NODE_COLOR IS '로드맵 노드 색상';
COMMENT ON COLUMN ROADMAP_NODE.UPDATE_TIME IS '로드맵 업데이트 날짜';

create table if not exists ROADMAP_EDGE
(
    ID text primary key,
    SOURCE_ID text,
    TARGET_ID text,
    update_time timestamptz default now()
);
COMMENT ON COLUMN ROADMAP_EDGE.ID IS '로드맵 엣지 아이디';
COMMENT ON COLUMN ROADMAP_EDGE.SOURCE_ID IS '로드맵 엣지 연결 시작 노드 아이디';
COMMENT ON COLUMN ROADMAP_EDGE.TARGET_ID IS '로드맵 엣지 연결 끝 노드 아이디';
COMMENT ON COLUMN ROADMAP_EDGE.UPDATE_TIME IS '로드맵 엣지 업데이트 날짜';

create table if not exists ITEM_PRICE_I18N
(
    ID text primary key ,
    NAME jsonb,
    WIDTH numeric,
    HEIGHT numeric,
    CATEGORY text,
    TRADER jsonb,
    IMAGE text,
    update_time timestamptz default now()
);
COMMENT ON COLUMN ITEM_PRICE_I18N.ID IS '아이템 아이디';
COMMENT ON COLUMN ITEM_PRICE_I18N.NAME IS '아이템 이름';
COMMENT ON COLUMN ITEM_PRICE_I18N.IMAGE IS '아이템 사진';
COMMENT ON COLUMN ITEM_PRICE_I18N.WIDTH IS '아이템 가로 크기';
COMMENT ON COLUMN ITEM_PRICE_I18N.HEIGHT IS '아이템 세로 크기';
COMMENT ON COLUMN ITEM_PRICE_I18N.CATEGORY IS '아이템 카테고리';
COMMENT ON COLUMN ITEM_PRICE_I18N.TRADER IS '트레이더 정보';
COMMENT ON COLUMN ITEM_PRICE_I18N.UPDATE_TIME IS '업데이트 날짜';

-- 미니게임 전용 테이블
CREATE MATERIALIZED VIEW item_flea_summary AS
WITH pve_prices AS (SELECT id,
                           name,
                           image,
                           width,
                           height,
                           category,
                           jsonb_array_elements(trader -> 'pve_trader') AS trade_info,
                           update_time
                    FROM item_price_i18n
                    WHERE jsonb_typeof(trader -> 'pve_trader') = 'array')
SELECT id,
       name,
       image,
       width,
       height,
       category,
       MAX((trade_info ->> 'price')::INT)                                   AS flea_market_price,
       update_time
FROM pve_prices
WHERE trade_info -> 'trader' ->> 'npc_id' = 'FLEA_MARKET'
  AND category != 'Etc'
GROUP BY id, name, image, width, height, category, update_time
ORDER BY category, flea_market_price DESC;

CREATE UNIQUE INDEX idx_item_flea_summary_id
ON item_flea_summary (id);

create table if not exists ITEM_PRICE_HISTORY_I18N
(
    ID text,
    PRICE integer,
    PRICE_TYPE text,
    PRICE_TIME timestamptz default now(),
    EXECUTE_TIME timestamptz default now(),
    PRIMARY KEY (ID, PRICE_TYPE, PRICE_TIME)
);
COMMENT ON COLUMN ITEM_PRICE_HISTORY_I18N.ID IS '아이템 아이디';
COMMENT ON COLUMN ITEM_PRICE_HISTORY_I18N.PRICE IS '해당 시간대 금액';
COMMENT ON COLUMN ITEM_PRICE_HISTORY_I18N.PRICE_TYPE IS '시세 종류 (pvp, pve)';
COMMENT ON COLUMN ITEM_PRICE_HISTORY_I18N.PRICE_TIME IS '아이템 시세 시간대';
COMMENT ON COLUMN ITEM_PRICE_HISTORY_I18N.EXECUTE_TIME IS '적재 날짜';

create table if not exists WIPE_I18N
(
    ID integer primary key ,
    PATCH_VERSION text,
    SEASON_START text,
    SEASON_END text,
    CREATE_TIME timestamptz default now()
);
COMMENT ON COLUMN WIPE_I18N.ID IS '아이디';
COMMENT ON COLUMN WIPE_I18N.PATCH_VERSION IS '패치 버전';
COMMENT ON COLUMN WIPE_I18N.SEASON_START IS '시즌 시작 날짜';
COMMENT ON COLUMN WIPE_I18N.SEASON_END IS '시즌 종료 날짜';
COMMENT ON COLUMN WIPE_I18N.CREATE_TIME IS '생성 날짜';

create table if not exists USER_HIDEOUT
(
    user_email text primary key,
    COMPLETE_LIST text[],
    ITEM_LIST jsonb,
    update_time timestamptz default now()
);
COMMENT ON COLUMN USER_HIDEOUT.user_email IS '하이드아웃 사용자 이메일';
COMMENT ON COLUMN USER_HIDEOUT.COMPLETE_LIST IS '하이드아웃 완료 정보';
COMMENT ON COLUMN USER_HIDEOUT.ITEM_LIST IS '하이드아웃 사용자 아이템 저장 정보';
COMMENT ON COLUMN USER_HIDEOUT.UPDATE_TIME IS '하이드아웃 업데이트 날짜';

create table if not exists ITEM_I18N
(
    ID text primary key,
    NAME jsonb,
    CATEGORY text,
    IMAGE_WIDTH numeric,
    IMAGE_HEIGHT numeric,
    normalized_name text,
    IMAGE text,
    INFO jsonb,
    update_time timestamptz default now()
);
COMMENT ON COLUMN ITEM_I18N.ID IS '아이템 아이디';
COMMENT ON COLUMN ITEM_I18N.NAME IS '아이템 이름';
COMMENT ON COLUMN ITEM_I18N.CATEGORY IS '아이템 카테고리';
COMMENT ON COLUMN ITEM_I18N.IMAGE IS '아이템 사진';
COMMENT ON COLUMN ITEM_I18N.IMAGE_WIDTH IS '아이템 사진 가로 크기';
COMMENT ON COLUMN ITEM_I18N.IMAGE_HEIGHT IS '아이템 사진 세로 크기';
COMMENT ON COLUMN ITEM_I18N.normalized_name IS '아이템 주소';
COMMENT ON COLUMN ITEM_I18N.INFO IS '아이템 상세 정보';
COMMENT ON COLUMN ITEM_I18N.UPDATE_TIME IS '아이템 업데이트 날짜';

create table if not exists ITEM_DETAIL_I18N
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

create table if not exists WHERE_AM_I_I18N
(
    ID text primary key,
    IMAGE text,
    MAP_BOUNDS jsonb,
    IMAGE_BOUNDS jsonb,
    DEFAULT_ZOOM_LEVEL numeric,
    QUESTS jsonb,
    update_time timestamptz default now()
);
COMMENT ON COLUMN WHERE_AM_I_I18N.ID IS 'where am i 아이디';
COMMENT ON COLUMN WHERE_AM_I_I18N.IMAGE IS 'where am i 이미지';
COMMENT ON COLUMN WHERE_AM_I_I18N.MAP_BOUNDS IS 'where am i Map bounds';
COMMENT ON COLUMN WHERE_AM_I_I18N.IMAGE_BOUNDS IS 'where am i image bounds';
COMMENT ON COLUMN WHERE_AM_I_I18N.DEFAULT_ZOOM_LEVEL IS 'where am i default zoom level';
COMMENT ON COLUMN WHERE_AM_I_I18N.QUESTS IS 'where am i 퀘스트 정보';
COMMENT ON COLUMN WHERE_AM_I_I18N.UPDATE_TIME IS 'where am i 업데이트 날짜';

create table if not exists USER_FOOTPRINT
(
  ID serial primary key,
  LINK text,
  REQUEST text,
  FOOTPRINT_TIME timestamp with time zone,
  EXECUTE_TIME timestamptz default now()
);
COMMENT ON COLUMN USER_FOOTPRINT.ID IS '사용자 기록 아이디';
COMMENT ON COLUMN USER_FOOTPRINT.REQUEST IS '사용자 기록 요청 타입';
COMMENT ON COLUMN USER_FOOTPRINT.LINK IS '사용자 기록 주소';
COMMENT ON COLUMN USER_FOOTPRINT.FOOTPRINT_TIME IS '사용자 기록 전송 시간';
COMMENT ON COLUMN USER_FOOTPRINT.EXECUTE_TIME IS '사용자 기록 적재 시간';

create table if not exists SITEMAP
(
    ID serial primary key,
    LINK text,
    PRIORITY numeric,
    CHANGE_FREQ text,
    VALUE text,
    CREATE_DATE timestamptz default now(),
    update_time timestamptz default now()
);
COMMENT ON COLUMN SITEMAP.ID IS 'sitemap 아이디';
COMMENT ON COLUMN SITEMAP.LINK IS 'sitemap 주소';
COMMENT ON COLUMN SITEMAP.PRIORITY IS 'sitemap 우선순위';
COMMENT ON COLUMN SITEMAP.CHANGE_FREQ IS 'sitemap 업데이트 주기';
COMMENT ON COLUMN SITEMAP.VALUE IS 'sitemap 분리 값';
COMMENT ON COLUMN SITEMAP.CREATE_DATE IS 'sitemap 생성일';
COMMENT ON COLUMN SITEMAP.UPDATE_TIME IS 'sitemap 업데이트 날짜';

create table if not exists HEALTH_CHECK (
    id serial primary key,
    service_name text,
    status text,
    checked_time timestamptz default now()
);
COMMENT ON COLUMN HEALTH_CHECK.ID IS 'health check 아이디';
COMMENT ON COLUMN HEALTH_CHECK.service_name IS 'health check 서비스 이름';
COMMENT ON COLUMN HEALTH_CHECK.status IS 'health check 상태';
COMMENT ON COLUMN HEALTH_CHECK.checked_time IS 'health check 점검 시간';

create table if not exists RESPONSE_TIME (
    id serial primary key,
    service_name text,
    response_ms numeric,
    checked_time timestamptz default now()
);
COMMENT ON COLUMN RESPONSE_TIME.ID IS '응답 시간 아이디';
COMMENT ON COLUMN RESPONSE_TIME.service_name IS '응답 시간 서비스 이름';
COMMENT ON COLUMN RESPONSE_TIME.response_ms IS '응답 시간';
COMMENT ON COLUMN RESPONSE_TIME.checked_time IS '응답 시간 점검 시간';

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
CREATE INDEX idx_progress_item_type
ON progress_item (progress_type);

create table if not exists user_minigame_score (
  ID serial primary key,
  NICKNAME text,
  GAME_TYPE text,
  SCORE bigint,
  CREATE_TIME timestamptz default now()
);
CREATE INDEX idx_minigame_score_rank
ON user_minigame_score (game_type, score DESC, create_time ASC);

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