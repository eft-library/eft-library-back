-- 직접 실행용. 기존 데이터 삭제/기존 컬럼 변경 없음.
BEGIN;
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

COMMIT;
