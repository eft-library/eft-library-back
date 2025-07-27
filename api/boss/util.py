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
                (
                    SELECT jsonb_agg(entry ORDER BY entry.is_boss DESC, entry.id)
                    FROM (
                             -- 자식들
                             SELECT c.*
                             FROM boss_i18n c
                             WHERE c.parent_id = b.id
            
                             UNION ALL
            
                             -- 자기 자신
                             SELECT b.*
                         ) AS entry
                ) AS children
            FROM boss_i18n b
            WHERE b.is_boss = true
              AND b.url_mapping = :url_mapping;
        """
