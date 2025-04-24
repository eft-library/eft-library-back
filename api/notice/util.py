class NoticeUtil:

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
