-- Existing rows and user_progress_item are preserved.
-- NULL progress_type values, if any, must be reviewed before applying this migration.
BEGIN;
SET LOCAL lock_timeout = '10s';
SET LOCAL statement_timeout = '60s';
ALTER TABLE progress_item
    DROP CONSTRAINT progress_item_pkey,
    ALTER COLUMN progress_type SET NOT NULL,
    ADD CONSTRAINT progress_item_pkey PRIMARY KEY (id, progress_type);
COMMIT;
