class PatchNotesUtil:

    @staticmethod
    def get_patch_notes_group():
        return """
        WITH selected_patch_notes AS (
            SELECT id, name_en, name_kr, patch_notes_en, patch_notes_kr, update_time
            FROM tkl_patch_notes
            WHERE id = :id
        ),
        above_patch_notes AS (
            SELECT id, name_en, name_kr, patch_notes_en, patch_notes_kr, update_time
            FROM tkl_patch_notes
            WHERE update_time > (SELECT update_time FROM selected_patch_notes)
            ORDER BY update_time ASC
            LIMIT 2
        ),
        below_patch_notes AS (
            SELECT id, name_en, name_kr, patch_notes_en, patch_notes_kr, update_time
            FROM tkl_patch_notes
            WHERE update_time < (SELECT update_time FROM selected_patch_notes)
            ORDER BY update_time DESC
            LIMIT 2
        )
        SELECT * FROM above_patch_notes
        UNION ALL
        SELECT * FROM selected_patch_notes
        UNION ALL
        SELECT * FROM below_patch_notes
        ORDER BY update_time DESC;
        """
