class MapOfTarkovUtil:

    @staticmethod
    def get_map_of_tarkov_detail_query():
        return """
            SELECT a.id,
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
                   (SELECT jsonb_agg(
                                   jsonb_build_object(
                                           'id', b.id,
                                           'name', b.name,
                                           'three_image', b.three_image,
                                           'parent_value', b.parent_value,
                                           'three_item_path', b.three_item_path,
                                           'jpg_image', b.jpg_image,
                                           'jpg_item_path', b.jpg_item_path,
                                           'depth', b.depth,
                                           'order', b."order",
                                           'link', b.link,
                                           'mot_image', b.mot_image,
                                           'map_json', b.map_json,
                                           'update_time', b.update_time
                                   )
                                   ORDER BY b."order"
                           )
                    FROM map_group_i18n b
                    WHERE b.parent_value = a.id) AS children
            FROM map_group_i18n a
            WHERE a.depth = 1
              AND a.id = :map_id
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
