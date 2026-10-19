-- Confirmed aliases from the desktop parser. Preserve operator edits/disabled rows.
BEGIN;
INSERT INTO where_am_i_map_aliases (alias, map_slug) VALUES
    ('bigmap', 'customs'),
    ('factory4_day', 'factory'),
    ('factory4_night', 'factory'),
    ('factory_day', 'factory'),
    ('factory_night', 'factory'),
    ('interchange', 'interchange'),
    ('shopping_mall', 'interchange'),
    ('laboratory', 'the-lab'),
    ('labyrinth', 'the-labyrinth'),
    ('lighthouse', 'lighthouse'),
    ('rezervbase', 'reserve'),
    ('shoreline', 'shoreline'),
    ('city', 'streets-of-tarkov'),
    ('tarkovstreets', 'streets-of-tarkov'),
    ('tarkov streets', 'streets-of-tarkov'),
    ('terminal', 'terminal'),
    ('woods', 'woods'),
    ('sandbox', 'ground-zero'),
    ('sandbox_high', 'ground-zero'),
    ('sandbox_start', 'ground-zero'),
    ('sandbox_sl', 'ground-zero')
ON CONFLICT DO NOTHING;
COMMIT;
