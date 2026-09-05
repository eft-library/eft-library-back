class RoadmapQueryV3:
    @staticmethod
    def get_roadmap_node_v3():
        return """
            WITH quest_based AS (
                SELECT
                    t.id AS trader_id,
                    t.normalized_name AS trader_normalized_name,
                    t.name_en AS trader_name_en,
                    t.name_ko AS trader_name_ko,
                    t.name_ja AS trader_name_ja,
                    t.image AS trader_image,
                    t.sort_order AS trader_sort_order,
                    jsonb_build_object(
                        'id', q.id,
                        'normalized_name', q.normalized_name,
                        'name_en', q.name_en,
                        'name_ko', q.name_ko,
                        'name_ja', q.name_ja,
                        'kappa_required', q.kappa_required,
                        'is_use', q.is_use,
                        'trader_id', q.trader_id,
                        'min_player_level', q.min_player_level,
                        'affinity_type', q.affinity_type,
                        'total_x_coordinate', rn.total_x_coordinate,
                        'total_y_coordinate', rn.total_y_coordinate,
                        'single_x_coordinate', rn.single_x_coordinate,
                        'single_y_coordinate', rn.single_y_coordinate,
                        'total_kappa_x_coordinate', rn.total_kappa_x_coordinate,
                        'total_kappa_y_coordinate', rn.total_kappa_y_coordinate,
                        'single_kappa_x_coordinate', rn.single_kappa_x_coordinate,
                        'single_kappa_y_coordinate', rn.single_kappa_y_coordinate,
                        'task_next', COALESCE(next_rel.next_ids, '[]'::jsonb),
                        'task_requirements', COALESCE(require_rel.require_ids, '[]'::jsonb)
                    ) AS quest
                FROM quests q
                         LEFT JOIN traders t ON q.trader_id = t.id
                         LEFT JOIN roadmap_node rn ON q.id = rn.id
                         LEFT JOIN LATERAL (
                             SELECT jsonb_agg(qr.related_quest_id ORDER BY qr.sort_order) AS next_ids
                             FROM quest_relations qr
                             WHERE qr.quest_id = q.id
                               AND qr.relation_type = 'next'
                         ) next_rel ON true
                         LEFT JOIN LATERAL (
                             SELECT jsonb_agg(qr.related_quest_id ORDER BY qr.sort_order) AS require_ids
                             FROM quest_relations qr
                             WHERE qr.quest_id = q.id
                               AND qr.relation_type = 'require'
                         ) require_rel ON true
                WHERE q.id IS NOT NULL
            ),
            node_only AS (
                SELECT
                    t.id AS trader_id,
                    t.normalized_name AS trader_normalized_name,
                    t.name_en AS trader_name_en,
                    t.name_ko AS trader_name_ko,
                    t.name_ja AS trader_name_ja,
                    t.image AS trader_image,
                    t.sort_order AS trader_sort_order,
                    jsonb_build_object(
                        'id', t.id,
                        'normalized_name', t.normalized_name,
                        'name_en', t.name_en,
                        'name_ko', t.name_ko,
                        'name_ja', t.name_ja,
                        'kappa_required', false,
                        'is_use', true,
                        'trader_id', t.id,
                        'min_player_level', null,
                        'affinity_type', null,
                        'total_x_coordinate', rn.total_x_coordinate,
                        'total_y_coordinate', rn.total_y_coordinate,
                        'single_x_coordinate', rn.single_x_coordinate,
                        'single_y_coordinate', rn.single_y_coordinate,
                        'total_kappa_x_coordinate', rn.total_kappa_x_coordinate,
                        'total_kappa_y_coordinate', rn.total_kappa_y_coordinate,
                        'single_kappa_x_coordinate', rn.single_kappa_x_coordinate,
                        'single_kappa_y_coordinate', rn.single_kappa_y_coordinate,
                        'task_next', '[]'::jsonb,
                        'task_requirements', '[]'::jsonb
                    ) AS quest
                FROM roadmap_node rn
                         JOIN traders t ON t.id = rn.id
                         LEFT JOIN quests q ON q.id = rn.id
                WHERE q.id IS NULL
            )
            SELECT
                trader_id AS id,
                trader_normalized_name AS normalized_name,
                trader_name_en AS name_en,
                trader_name_ko AS name_ko,
                trader_name_ja AS name_ja,
                trader_image AS image,
                trader_sort_order AS sort_order,
                json_agg(quest ORDER BY quest ->> 'name_en') AS quests
            FROM (
                SELECT * FROM quest_based
                UNION ALL
                SELECT * FROM node_only
            ) AS all_quests
            GROUP BY trader_id,
                     trader_normalized_name,
                     trader_name_en,
                     trader_name_ko,
                     trader_name_ja,
                     trader_image,
                     trader_sort_order
            ORDER BY trader_sort_order, trader_name_en;
        """
