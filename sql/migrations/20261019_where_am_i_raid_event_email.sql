-- Additive upgrade; existing history remains NULL. No FK or backfill.
BEGIN;
ALTER TABLE where_am_i_raid_state_events ADD COLUMN IF NOT EXISTS email text;
COMMIT;
