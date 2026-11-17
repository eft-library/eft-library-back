-- 백엔드의 3D API/ORM 필드 제거 및 프론트 호출 제거 배포 후 실행.
-- 공유 maps 행과 2D/라이브 지도 데이터는 유지한다. CASCADE는 사용하지 않는다.
BEGIN;
SET LOCAL lock_timeout = '5s';
ALTER TABLE maps
    DROP COLUMN IF EXISTS three_image,
    DROP COLUMN IF EXISTS three_json;

-- /map-of-tarkov, /live-map, /roadmap은 제외. 상대/공식 절대 URL만 처리.
DELETE FROM autocomplete_items
WHERE url ~ '^(https?://(www\.)?eftlibrary\.com)?/map(/|[?#]|$)';
DELETE FROM sitemap
WHERE url ~ '^(https?://(www\.)?eftlibrary\.com)?/map(/|[?#]|$)';
DELETE FROM menu_sub_groups
WHERE url ~ '^(https?://(www\.)?eftlibrary\.com)?/map(/|[?#]|$)';
COMMIT;
