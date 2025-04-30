class MapUtil:

    @staticmethod
    def get_map_detail_query():
        return """
            SELECT
                a.id,
                a.name,
                a.three_image,
                a.parent_value,
                a.three_item_path,
                a.jpg_image,
                a.jpg_item_path,
                a.depth,
                a."order",
                a.link,
                a.mot_image,
                a.map_json,
                a.update_time,
                jsonb_agg(b.*) FILTER (WHERE b.id IS NOT NULL) AS children
            FROM map_group_i18n a
            LEFT JOIN map_group_i18n b
                ON b.parent_value = a.id
            WHERE a.depth = 1 
            and a.id = :map_id
            GROUP BY a.id;
        """
