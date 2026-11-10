-- Additive user build schema. No source/Airflow table is changed.
BEGIN;
SET LOCAL lock_timeout = '10s';
SET LOCAL statement_timeout = '60s';

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

COMMIT;
