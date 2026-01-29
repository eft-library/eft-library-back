class NewsUtil:

    @staticmethod
    def get_information_group():
        return """
            WITH selected_info AS (
                SELECT id, type, name, description, update_time
                FROM information_i18n
                WHERE id = :id AND type = :type
            ),
            above_infos AS (
                SELECT id, type, name, description, update_time
                FROM information_i18n
                WHERE type = :type 
                  AND update_time > (SELECT update_time FROM selected_info)
                ORDER BY update_time
                LIMIT 2
            ),
            below_infos AS (
                SELECT id, type, name, description, update_time
                FROM information_i18n
                WHERE type = :type 
                  AND update_time < (SELECT update_time FROM selected_info)
                ORDER BY update_time DESC
                LIMIT 2
            )
            SELECT * FROM above_infos
            UNION ALL
            SELECT * FROM selected_info
            UNION ALL
            SELECT * FROM below_infos
            ORDER BY update_time DESC;
        """
