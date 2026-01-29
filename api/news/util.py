class NewsUtil:

    @staticmethod
    def get_event_group():
        return """
            WITH selected_event AS (
                SELECT id, name, description, update_time
                FROM event_i18n
                WHERE id = :id
            ),
            above_events AS (
                SELECT id, name, description, update_time
                FROM event_i18n
                WHERE update_time > (SELECT update_time FROM selected_event)
                ORDER BY update_time
                LIMIT 2
            ),
            below_events AS (
                SELECT id, name, description, update_time
                FROM event_i18n
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

    @staticmethod
    def get_notice_group():
        return """
            WITH selected_notice AS (SELECT id, name, description, update_time
                                     FROM notice_i18n
                                     WHERE id = :id),
                 above_notices AS (SELECT id, name, description, update_time
                                   FROM notice_i18n
                                   WHERE update_time > (SELECT update_time FROM selected_notice)
                                   ORDER BY update_time
                                   LIMIT 2),
                 below_notices AS (SELECT id, name, description, update_time
                                   FROM notice_i18n
                                   WHERE update_time < (SELECT update_time FROM selected_notice)
                                   ORDER BY update_time DESC
                                   LIMIT 2)
            SELECT *
            FROM above_notices
            UNION ALL
            SELECT *
            FROM selected_notice
            UNION ALL
            SELECT *
            FROM below_notices
            ORDER BY update_time DESC;
        """

    @staticmethod
    def get_patch_notes_group():
        return """
            WITH selected_patch_notes AS (SELECT id, name, description, update_time
                                          FROM patch_notes_i18n
                                          WHERE id = :id),
                 above_patch_notes AS (SELECT id, name, description, update_time
                                       FROM patch_notes_i18n
                                       WHERE update_time > (SELECT update_time FROM selected_patch_notes)
                                       ORDER BY update_time
                                       LIMIT 2),
                 below_patch_notes AS (SELECT id, name, description, update_time
                                       FROM patch_notes_i18n
                                       WHERE update_time < (SELECT update_time FROM selected_patch_notes)
                                       ORDER BY update_time DESC
                                       LIMIT 2)
            SELECT *
            FROM above_patch_notes
            UNION ALL
            SELECT *
            FROM selected_patch_notes
            UNION ALL
            SELECT *
            FROM below_patch_notes
            ORDER BY update_time DESC;
        """
