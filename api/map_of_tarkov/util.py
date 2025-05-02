class MapOfTarkovUtil:

    @staticmethod
    def get_map_of_tarkov_detail_query():
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

    @staticmethod
    def get_map_of_tarkov_boss_query():
        return """
            SELECT
                b.id,
                b.name,
                b.faction,
                b.image,
                b.health_total,
                b.item_info,
                b.spawn_chance,
                b.spawn_map,
                b.health_image,
                b.location_guide,
                b."order",
                b.update_time,
                b.url_mapping,
                jsonb_agg(c.*) FILTER (WHERE c.id IS NOT NULL) AS children
            FROM boss_i18n b
            LEFT JOIN boss_i18n c
                ON c.parent_id = b.id
            WHERE b.is_boss = true
              AND :map_id = ANY (b.spawn_map)
            GROUP BY b.id
            order by b."order"
        """
