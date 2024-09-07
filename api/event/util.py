class EventUtil:

    @staticmethod
    def get_event_group():
        return """
        WITH selected_event AS (
            SELECT id, name_en, name_kr, notes_en, notes_kr, update_time
            FROM tkl_event
            WHERE id = :id
        ),
        above_events AS (
            SELECT id, name_en, name_kr, notes_en, notes_kr, update_time
            FROM tkl_event
            WHERE update_time > (SELECT update_time FROM selected_event)
            ORDER BY update_time ASC
            LIMIT 2
        ),
        below_events AS (
            SELECT id, name_en, name_kr, notes_en, notes_kr, update_time
            FROM tkl_event
            WHERE update_time < (SELECT update_time FROM selected_event)
            ORDER BY update_time DESC
            LIMIT 2
        )
        SELECT * FROM above_events
        UNION ALL
        SELECT * FROM selected_event
        UNION ALL
        SELECT * FROM below_events
        ORDER BY update_time DESC;
        """
