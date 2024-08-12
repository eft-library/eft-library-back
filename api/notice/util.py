class NoticeUtil:

    @staticmethod
    def get_notice_group():
        return """
        WITH selected_notice AS (
            SELECT id, name_en, name_kr, notice_en, notice_kr, update_time
            FROM tkl_notice
            WHERE id = :id
        ),
        above_notices AS (
            SELECT id, name_en, name_kr, notice_en, notice_kr, update_time
            FROM tkl_notice
            WHERE update_time > (SELECT update_time FROM selected_notice)
            ORDER BY update_time ASC
            LIMIT 2
        ),
        below_notices AS (
            SELECT id, name_en, name_kr, notice_en, notice_kr, update_time
            FROM tkl_notice
            WHERE update_time < (SELECT update_time FROM selected_notice)
            ORDER BY update_time DESC
            LIMIT 2
        )
        SELECT * FROM above_notices
        UNION ALL
        SELECT * FROM selected_notice
        UNION ALL
        SELECT * FROM below_notices
        ORDER BY update_time DESC;
        """
