class BossUtil:
    @staticmethod
    def get_boss_query():
        return """
            SELECT parent_id,
                   jsonb_agg(child_json) AS children,
                   string_agg(url_mapping, ', ') FILTER (WHERE is_boss = true) AS boss_url_mappings
            FROM (
                SELECT parent_id,
                       id,
                       name,
                       is_boss,
                       faction,
                       image,
                       health_total,
                       item_info,
                       spawn_chance,
                       location_guide,
                       "order",
                       update_time,
                       url_mapping,
                       jsonb_build_object(
                           'id', id,
                           'name', name,
                           'is_boss', is_boss,
                           'faction', faction,
                           'image', image,
                           'health_total', health_total,
                           'item_info', item_info,
                           'spawn_chance', spawn_chance,
                           'location_guide', location_guide,
                           'order', "order",
                           'update_time', update_time,
                           'url_mapping', url_mapping
                       ) AS child_json
                FROM boss_i18n
                ORDER BY parent_id, "order"
            ) AS ordered_children
            GROUP BY parent_id;
        """
