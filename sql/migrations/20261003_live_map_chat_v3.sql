-- Run against V3 database before deploying the chat V3 backend.
BEGIN;
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '30s';

-- Preserve existing data when the earlier suffixed tables have already been created.
-- Refuse ambiguous installations instead of silently choosing one set of tables.
DO $$
DECLARE
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'live_map_chat_users', 'live_map_chat_messages', 'live_map_chat_blocks',
        'live_map_chat_reports', 'live_map_chat_restrictions', 'live_map_party_invitations'
    ] LOOP
        IF to_regclass(table_name || '_v3') IS NOT NULL THEN
            IF to_regclass(table_name) IS NOT NULL THEN
                RAISE EXCEPTION USING MESSAGE = 'Duplicate table names: ' || table_name || ' and ' || table_name || '_v3';
            END IF;
            EXECUTE 'ALTER TABLE ' || quote_ident(table_name || '_v3') || ' RENAME TO ' || quote_ident(table_name);
        END IF;
    END LOOP;
END $$;

-- Table renames do not rename indexes or auto-generated constraints.
-- Limit renaming to the six new chat/invitation tables.
DO $$
DECLARE
    table_name text;
    constraint_row record;
    index_row record;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'live_map_chat_users', 'live_map_chat_messages', 'live_map_chat_blocks',
        'live_map_chat_reports', 'live_map_chat_restrictions', 'live_map_party_invitations'
    ] LOOP
        FOR constraint_row IN
            SELECT conname FROM pg_constraint
            WHERE conrelid = to_regclass(table_name) AND strpos(conname, '_v3') > 0
        LOOP
            EXECUTE 'ALTER TABLE ' || to_regclass(table_name)::text || ' RENAME CONSTRAINT '
                || quote_ident(constraint_row.conname) || ' TO '
                || quote_ident(replace(constraint_row.conname, '_v3', ''));
        END LOOP;
        FOR index_row IN
            SELECT c.relname, n.nspname FROM pg_index i
            JOIN pg_class c ON c.oid = i.indexrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE i.indrelid = to_regclass(table_name) AND strpos(c.relname, '_v3') > 0
        LOOP
            EXECUTE 'ALTER INDEX ' || quote_ident(index_row.nspname) || '.'
                || quote_ident(index_row.relname) || ' RENAME TO '
                || quote_ident(replace(index_row.relname, '_v3', ''));
        END LOOP;
    END LOOP;
END $$;

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
COMMIT;
