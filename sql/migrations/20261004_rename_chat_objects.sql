-- Existing installations: rename chat tables, constraints and indexes without rebuilding or deleting data.
BEGIN;
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '30s';

-- Preserve existing data when the earlier suffixed tables have already been created.
-- Refuse ambiguous installations instead of silently choosing one set of tables.
DO $$
DECLARE
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'live_map_chat_users', 'live_map_chat_messages', 'live_map_chat_blocks',
        'live_map_chat_reports', 'live_map_chat_restrictions', 'live_map_party_invitations'
    ] LOOP
        IF to_regclass(table_name || '_v3') IS NOT NULL THEN
            IF to_regclass(table_name) IS NOT NULL THEN
                RAISE EXCEPTION USING MESSAGE = 'Duplicate table names: ' || table_name || ' and ' || table_name || '_v3';
            END IF;
            EXECUTE 'ALTER TABLE ' || quote_ident(table_name || '_v3') || ' RENAME TO ' || quote_ident(table_name);
        END IF;
    END LOOP;
END $$;

-- Table renames do not rename indexes or auto-generated constraints.
-- Limit renaming to the six new chat/invitation tables.
DO $$
DECLARE
    table_name text;
    constraint_row record;
    index_row record;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'live_map_chat_users', 'live_map_chat_messages', 'live_map_chat_blocks',
        'live_map_chat_reports', 'live_map_chat_restrictions', 'live_map_party_invitations'
    ] LOOP
        FOR constraint_row IN
            SELECT conname FROM pg_constraint
            WHERE conrelid = to_regclass(table_name) AND strpos(conname, '_v3') > 0
        LOOP
            EXECUTE 'ALTER TABLE ' || to_regclass(table_name)::text || ' RENAME CONSTRAINT '
                || quote_ident(constraint_row.conname) || ' TO '
                || quote_ident(replace(constraint_row.conname, '_v3', ''));
        END LOOP;
        FOR index_row IN
            SELECT c.relname, n.nspname FROM pg_index i
            JOIN pg_class c ON c.oid = i.indexrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE i.indrelid = to_regclass(table_name) AND strpos(c.relname, '_v3') > 0
        LOOP
            EXECUTE 'ALTER INDEX ' || quote_ident(index_row.nspname) || '.'
                || quote_ident(index_row.relname) || ' RENAME TO '
                || quote_ident(replace(index_row.relname, '_v3', ''));
        END LOOP;
    END LOOP;
END $$;

COMMIT;
