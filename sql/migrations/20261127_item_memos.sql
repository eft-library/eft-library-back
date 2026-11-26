BEGIN;

ALTER TABLE items
    ADD COLUMN IF NOT EXISTS memo_ko text,
    ADD COLUMN IF NOT EXISTS memo_en text,
    ADD COLUMN IF NOT EXISTS memo_ja text;

COMMIT;
