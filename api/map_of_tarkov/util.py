class MapOfTarkovUtil:

    @staticmethod
    def get_map_of_tarkov_detail_query():
        return """
            SELECT a.id,
                   a.name,
                   a.mot_image,
                   (SELECT jsonb_agg(
                                   jsonb_build_object(
                                           'id', b.id,
                                           'name', b.name,
                                           'mot_image', b.mot_image
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
                b.spawn_chance,
                b.spawn_map,
                jsonb_agg(c.*) FILTER (WHERE c.id IS NOT NULL) AS children
            FROM boss_i18n b
            LEFT JOIN boss_i18n c
                ON c.parent_id = b.id
            WHERE b.is_boss = true
              AND :map_id = ANY (b.spawn_map)
            GROUP BY b.id
            order by b."order"
        """
