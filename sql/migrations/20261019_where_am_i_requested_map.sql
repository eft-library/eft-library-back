-- Apply after 20261019_where_am_i_analytics.sql. Existing rows remain NULL.
BEGIN;
ALTER TABLE where_am_i_raid_state_events ADD COLUMN IF NOT EXISTS requested_map text;
ALTER TABLE where_am_i_api_failures ADD COLUMN IF NOT EXISTS requested_map text;
COMMIT;
