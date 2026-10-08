BEGIN;
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '30s';

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

COMMIT;
