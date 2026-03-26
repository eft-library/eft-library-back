-- quest 기본 정보
CREATE TABLE IF NOT EXISTS quests
(
    id text NOT NULL primary key,
    normalized_name text,
    trader_id text,
    kappa_require boolean,
    experience integer,
    delay_min integer,
    delay_max integer,
    min_player_level integer,
    name_en text,
    name_ko text,
    name_ja text,
    wiki_url text,
    guide_en text,
    guide_ko text,
    guide_ja text,
    sort_order integer,
    update_time timestamptz DEFAULT now()
);

-- quest 이전, 다음 정보
CREATE TABLE IF NOT EXISTS quest_relations (
    quest_id      text,
    related_quest_id text,
    relation_type text,  -- 'require', 'next'
    update_time timestamptz DEFAULT now(),
    primary key (quest_id, related_quest_id, relation_type)
);
CREATE INDEX ON quest_relations (quest_id);

-- 아이템 보상
CREATE TABLE quest_reward_items (
    id          text PRIMARY KEY,
    quest_id    text,
    item_id     text,  -- item_detail JOIN
    count       integer,
    sort_order  integer,
    update_time timestamptz DEFAULT now()
);

-- 트레이더 호감도
CREATE TABLE quest_reward_trader_standing (
    id          text PRIMARY KEY,
    quest_id    text,
    trader_id   text,  -- traders JOIN
    standing    numeric,
    sort_order  integer,
    update_time timestamptz DEFAULT now()
);

-- 거래 잠금해제
CREATE TABLE quest_reward_offer_unlocks (
    id          text PRIMARY KEY,
    quest_id    text,
    trader_id   text,  -- traders JOIN
    item_id     text,  -- item_detail JOIN
    level       integer,
    sort_order  integer,
    update_time timestamptz DEFAULT now()
);

-- 제작 잠금해제
CREATE TABLE quest_reward_craft_unlocks (
    id          text PRIMARY KEY,
    quest_id    text,
    station_id  text,  -- hideout_stations JOIN
    item_id     text,  -- item_detail JOIN (결과물)
    count       integer,
    level       integer,
    sort_order  integer,
    update_time timestamptz DEFAULT now()
);

-- 스킬 보상 (JOIN 없어서 jsonb도 되지만 통일성 위해)
CREATE TABLE quest_reward_skills (
    id          text PRIMARY KEY,
    quest_id    text,
    skill_name  text,
    level       integer,
    sort_order  integer,
    update_time timestamptz DEFAULT now()
);

-- quest 목표 정보
CREATE TABLE IF NOT EXISTS quest_objectives (
    id            text primary key,
    quest_id      text,
    objective_type text,
    sort_order    integer,
    desc_en       text,
    desc_ko       text,
    desc_ja       text,
    extra         jsonb,  -- type마다 다른 필드
    update_time timestamptz DEFAULT now()
);
CREATE INDEX ON quest_objectives (quest_id);

-- quest 목표 상세
create table if not exists quest_objectives_detail (
    id text primary key,
    objective_id text,
    x_coordinate integer,
    z_coordinate integer,
    desc_en text,
    desc_ko text,
    desc_ja text,
    image text,
    update_time timestamptz DEFAULT now()
);
CREATE INDEX ON quest_objectives_detail (objective_id);