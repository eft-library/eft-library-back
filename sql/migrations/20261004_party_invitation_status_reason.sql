-- Add detailed invitation terminal reasons without changing existing statuses.
BEGIN;
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '30s';

ALTER TABLE live_map_party_invitations
    ADD COLUMN IF NOT EXISTS status_reason text;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'live_map_party_invitations'::regclass
          AND conname = 'ck_party_invitations_status_reason'
    ) THEN
        ALTER TABLE live_map_party_invitations
            ADD CONSTRAINT ck_party_invitations_status_reason
            CHECK (status_reason IN (
                'cancelled', 'room_closed', 'room_full', 'already_joined', 'member_kicked'
            )) NOT VALID;
    END IF;
END $$;

ALTER TABLE live_map_party_invitations
    VALIDATE CONSTRAINT ck_party_invitations_status_reason;

COMMIT;
