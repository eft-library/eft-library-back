-- Run during the party backend deployment, before starting the new backend.
-- Pause marker writes until deployment completes: old code does not supply map_id.
BEGIN;
LOCK TABLE live_map_party_markers IN SHARE ROW EXCLUSIVE MODE;
ALTER TABLE live_map_party_markers
    ADD COLUMN IF NOT EXISTS map_id text REFERENCES maps(id) ON DELETE RESTRICT;

-- Existing markers were validated against the room map, including its child floors.
UPDATE live_map_party_markers AS marker
SET map_id = room.map_id
FROM live_map_party_rooms AS room
WHERE marker.room_id = room.id AND marker.map_id IS NULL;

ALTER TABLE live_map_party_markers ALTER COLUMN map_id SET NOT NULL;
COMMIT;
