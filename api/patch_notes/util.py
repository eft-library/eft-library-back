class PatchNotesUtil:

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
