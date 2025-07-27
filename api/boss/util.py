class BossUtil:
    @staticmethod
    def get_boss_query():
        return """
            SELECT
                b.id,
                b.name,
                b.faction,
                b.image,
                b.health_total,
                b.item_info,
                b.health_detail,
                b.spawn_chance,
                b.spawn_map,
                b.health_image,
                b.location_guide,
                b."order",
                b.update_time,
                b.url_mapping,
                jsonb_agg(c.* ORDER BY c.is_boss DESC, c.id) FILTER (WHERE c.id IS NOT NULL) AS children
            FROM boss_i18n b
                     LEFT JOIN boss_i18n c
                               ON c.parent_id = b.id
            WHERE b.is_boss = true
              and b.url_mapping = :url_mapping
            GROUP BY b.id
        """
