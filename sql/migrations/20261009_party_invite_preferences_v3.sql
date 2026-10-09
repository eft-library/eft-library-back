BEGIN;
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '30s';

-- V3 per-user party invitation preferences. Missing row means allow=true.
create table if not exists live_map_chat_invite_preferences (
    user_id uuid primary key references live_map_chat_users(id) on delete cascade,
    allow_party_invites boolean not null default true,
    update_time timestamptz not null default now()
);
create index if not exists idx_party_invitations_pair_history
    on live_map_party_invitations(inviter_id, invitee_id, update_time desc);

ALTER TABLE live_map_party_invitations
    DROP CONSTRAINT IF EXISTS ck_party_invitations_status_reason;
ALTER TABLE live_map_party_invitations
    ADD CONSTRAINT ck_party_invitations_status_reason CHECK (status_reason IN (
        'cancelled', 'room_closed', 'room_full', 'already_joined', 'member_kicked', 'receiver_unavailable'
    )) NOT VALID;
ALTER TABLE live_map_party_invitations VALIDATE CONSTRAINT ck_party_invitations_status_reason;
COMMIT;
