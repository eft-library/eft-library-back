begin;

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

alter table item_prices add column if not exists season_id text;
alter table item_prices add column if not exists season_key text
    generated always as (coalesce(season_id, '')) stored;
alter table item_trader_prices add column if not exists season_id text;
alter table item_trader_prices add column if not exists season_key text
    generated always as (coalesce(season_id, '')) stored;
alter table item_price_history add column if not exists season_id text;
alter table item_price_history add column if not exists season_key text
    generated always as (coalesce(season_id, '')) stored;

-- Preserve pre-migration seasonal rows whose source season cannot be identified.
insert into price_seasons (id, name, is_current)
select 'legacy-unidentified', 'Legacy unidentified season', false
where exists (
    select 1 from item_prices where game_mode = 'pvp-season' and season_id is null
    union all
    select 1 from item_trader_prices where game_mode = 'pvp-season' and season_id is null
    union all
    select 1 from item_price_history where game_mode = 'pvp-season' and season_id is null
)
on conflict (id) do nothing;

update item_prices
set season_id = 'legacy-unidentified'
where game_mode = 'pvp-season' and season_id is null;
update item_trader_prices
set season_id = 'legacy-unidentified'
where game_mode = 'pvp-season' and season_id is null;
update item_price_history
set season_id = 'legacy-unidentified'
where game_mode = 'pvp-season' and season_id is null;

alter table item_prices drop constraint if exists item_prices_pkey;
alter table item_prices
    add constraint item_prices_pkey primary key (item_id, game_mode, season_key);
alter table item_trader_prices drop constraint if exists item_trader_prices_pkey;
alter table item_trader_prices
    add constraint item_trader_prices_pkey
        primary key (item_id, game_mode, season_key, trader_id);
alter table item_price_history drop constraint if exists item_price_history_pkey;
alter table item_price_history
    add constraint item_price_history_pkey
        primary key (item_id, game_mode, season_key, price_time);

alter table item_prices drop constraint if exists fk_item_prices_season;
alter table item_prices
    add constraint fk_item_prices_season foreign key (season_id)
        references price_seasons(id) on delete restrict;
alter table item_trader_prices drop constraint if exists fk_item_trader_prices_season;
alter table item_trader_prices
    add constraint fk_item_trader_prices_season foreign key (season_id)
        references price_seasons(id) on delete restrict;
alter table item_price_history drop constraint if exists fk_item_price_history_season;
alter table item_price_history
    add constraint fk_item_price_history_season foreign key (season_id)
        references price_seasons(id) on delete restrict;

alter table item_prices drop constraint if exists ck_item_prices_season_scope;
alter table item_prices add constraint ck_item_prices_season_scope check (
    (game_mode = 'pvp-season' and season_id is not null)
    or (game_mode <> 'pvp-season' and season_id is null)
);
alter table item_trader_prices drop constraint if exists ck_item_trader_prices_season_scope;
alter table item_trader_prices add constraint ck_item_trader_prices_season_scope check (
    (game_mode = 'pvp-season' and season_id is not null)
    or (game_mode <> 'pvp-season' and season_id is null)
);
alter table item_price_history drop constraint if exists ck_item_price_history_season_scope;
alter table item_price_history add constraint ck_item_price_history_season_scope check (
    (game_mode = 'pvp-season' and season_id is not null)
    or (game_mode <> 'pvp-season' and season_id is null)
);

drop index if exists idx_item_trader_prices_item_mode;
create index if not exists idx_item_prices_mode_season
    on item_prices(game_mode, season_id);
create index if not exists idx_item_trader_prices_item_mode
    on item_trader_prices(item_id, game_mode, season_id);
create index if not exists idx_item_price_history_item_mode_season_time
    on item_price_history(item_id, game_mode, season_id, price_time);

commit;
