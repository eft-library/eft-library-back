BEGIN;

ALTER TABLE user_info ADD COLUMN IF NOT EXISTS google_sub text;
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_info_google_sub ON user_info(google_sub);

COMMIT;
