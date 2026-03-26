-- quest 기본 정보
CREATE TABLE IF NOT EXISTS quests
(
    id text NOT NULL primary key,
    url_mapping text,
    npc_id text,
    kappa_required boolean,
    name_en text,
    name_ko text,
    name_ja text,
    wiki_url text,
    min_player_level INTEGER,
    guide_en text,
    guide_ko text,
    guide_ja text,
    sort_order INTEGER,
    update_time timestamptz DEFAULT now()
);

-- quest 이전, 다음 정보
CREATE TABLE IF NOT EXISTS quest_relations (
    quest_id      text,
    related_quest_id text,
    relation_type text,  -- 'requires', 'next'
    update_time timestamptz DEFAULT now(),
    primary key (quest_id, related_quest_id, relation_type)
);
CREATE INDEX ON quest_relations (quest_id);

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

-- quest 보상 정보
CREATE TABLE quest_rewards (
    id         text primary key,
    quest_id   text,
    reward_type text,  -- 'item', 'traderStanding', 'skill' ...
    count      integer,
    sort_order integer,
    extra      jsonb
);
CREATE INDEX ON quest_rewards (quest_id);

-- quest 목표 정보 상세
create table if not exists quest_objectives_detail (
    id text primary key,
    objective_id text,
    x_coordinate integer,
    z_coordinate integer,
    sub_desc_en text,
    sub_desc_ko text,
    sub_desc_ja text,
    image text,
    update_time timestamptz DEFAULT now()
);
CREATE INDEX ON quest_objectives_detail (objective_id);