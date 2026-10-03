-- Run against V3 database before deploying the chat V3 backend.
BEGIN;
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '30s';

-- Live Map 채팅 V3: additive only; no changes to existing party/account rows.
create table if not exists live_map_chat_users_v3 (
    id uuid primary key,
    user_email text not null unique references user_info(email) on delete cascade,
    create_time timestamptz not null default now()
);
create table if not exists live_map_chat_messages_v3 (
    id uuid primary key,
    user_id uuid not null references live_map_chat_users_v3(id) on delete cascade,
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
create index if not exists idx_chat_messages_v3_history
    on live_map_chat_messages_v3(channel, room_id, create_time desc, id desc);
create index if not exists idx_chat_messages_v3_user on live_map_chat_messages_v3(user_id, create_time desc);
create index if not exists idx_chat_messages_v3_retention on live_map_chat_messages_v3(create_time);
create index if not exists idx_chat_messages_v3_room on live_map_chat_messages_v3(room_id);
create table if not exists live_map_chat_blocks_v3 (
    user_id uuid not null references live_map_chat_users_v3(id) on delete cascade,
    target_id uuid not null references live_map_chat_users_v3(id) on delete cascade,
    create_time timestamptz not null default now(),
    primary key (user_id, target_id),
    check (user_id <> target_id)
);
create index if not exists idx_chat_blocks_v3_target on live_map_chat_blocks_v3(target_id);
create table if not exists live_map_chat_reports_v3 (
    id uuid primary key,
    user_id uuid not null references live_map_chat_users_v3(id) on delete cascade,
    message_id uuid not null references live_map_chat_messages_v3(id) on delete cascade,
    reason text not null check (reason in ('spam', 'abuse', 'inappropriate', 'personal_info', 'other')),
    detail varchar(1000),
    create_time timestamptz not null default now(),
    unique (user_id, message_id)
);
create index if not exists idx_chat_reports_v3_message on live_map_chat_reports_v3(message_id);
create index if not exists idx_chat_reports_v3_time on live_map_chat_reports_v3(create_time desc, id desc);
create table if not exists live_map_chat_restrictions_v3 (
    user_id uuid primary key references live_map_chat_users_v3(id) on delete cascade,
    moderator_id uuid references live_map_chat_users_v3(id) on delete set null,
    reason varchar(1000) not null,
    expires_at timestamptz,
    create_time timestamptz not null default now()
);
create index if not exists idx_chat_restrictions_v3_moderator on live_map_chat_restrictions_v3(moderator_id);
create table if not exists live_map_party_invitations_v3 (
    id uuid primary key,
    room_id uuid not null references live_map_party_rooms(id) on delete cascade,
    inviter_id uuid not null references live_map_chat_users_v3(id) on delete cascade,
    invitee_id uuid not null references live_map_chat_users_v3(id) on delete cascade,
    status text not null check (status in ('pending', 'accepted', 'rejected', 'revoked', 'expired')),
    expires_at timestamptz not null,
    create_time timestamptz not null default now(),
    update_time timestamptz not null default now(),
    check (inviter_id <> invitee_id)
);
create unique index if not exists uq_party_invitations_v3_pending
    on live_map_party_invitations_v3(room_id, invitee_id) where status = 'pending';
create index if not exists idx_party_invitations_v3_invitee on live_map_party_invitations_v3(invitee_id, status, create_time desc);
create index if not exists idx_party_invitations_v3_inviter on live_map_party_invitations_v3(inviter_id, create_time desc);
create index if not exists idx_party_invitations_v3_expiry on live_map_party_invitations_v3(status, expires_at);
COMMIT;
