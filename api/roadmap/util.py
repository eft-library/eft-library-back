class RoadmapUtil:
    @staticmethod
    def get_roadmap_node():
        return """
            WITH quest_based AS (
                SELECT
                    ni.id AS npc_id,
                    ni.name,
                    ni.image,
                    ni."order",
                    jsonb_build_object(
                            'id', qi.id,
                            'name', qi.name,
                            'kappa_required', qi.kappa_required,
                            'npc_id', qi.npc_id,
                            'url_mapping', qi.url_mapping,
                            'total_x_coordinate', rn.total_x_coordinate,
                            'total_y_coordinate', rn.total_y_coordinate,
                            'single_x_coordinate', rn.single_x_coordinate,
                            'single_y_coordinate', rn.single_y_coordinate,
                            'total_kappa_x_coordinate', rn.total_kappa_x_coordinate,
                            'total_kappa_y_coordinate', rn.total_kappa_y_coordinate,
                            'single_kappa_x_coordinate', rn.single_kappa_x_coordinate,
                            'single_kappa_y_coordinate', rn.single_kappa_y_coordinate,
                            'node_color', rn.node_color,
                            'task_next', COALESCE((SELECT jsonb_agg(elem -> 'task' -> 'id')
                                                   FROM jsonb_array_elements(COALESCE(qi.task_next, '[]'::jsonb)) AS elem), '[]'::jsonb),
                            'task_requirements', COALESCE((SELECT jsonb_agg(elem -> 'task' -> 'id')
                                                           FROM jsonb_array_elements(COALESCE(qi.task_requirements, '[]'::jsonb)) AS elem), '[]'::jsonb)
                    ) AS quest
                FROM npc_i18n ni
                         LEFT JOIN quest_i18n qi ON ni.id = qi.npc_id
                         LEFT JOIN roadmap_node rn ON qi.id = rn.id
                WHERE qi.id IS NOT NULL
            ),
                 node_only AS (
                     SELECT
                         ni.id AS npc_id,
                         ni.name,
                         ni.image,
                         ni."order",
                         jsonb_build_object(
                                 'id', ni.id,
                                 'name', ni.name,
                                 'kappa_required', false,
                                 'npc_id', ni.id,
                                 'url_mapping', '',
                                 'total_x_coordinate', rn.total_x_coordinate,
                                 'total_y_coordinate', rn.total_y_coordinate,
                                 'single_x_coordinate', rn.single_x_coordinate,
                                 'single_y_coordinate', rn.single_y_coordinate,
                                 'total_kappa_x_coordinate', rn.total_kappa_x_coordinate,
                                 'total_kappa_y_coordinate', rn.total_kappa_y_coordinate,
                                 'single_kappa_x_coordinate', rn.single_kappa_x_coordinate,
                                 'single_kappa_y_coordinate', rn.single_kappa_y_coordinate,
                                 'node_color', rn.node_color,
                                 'task_next', '[]'::jsonb,
                                 'task_requirements','[]'::jsonb
                         ) AS quest
                     FROM roadmap_node rn
                              JOIN npc_i18n ni ON ni.id = rn.id
                              LEFT JOIN quest_i18n qi ON qi.id = rn.id
                     WHERE qi.id IS NULL
                 )
            SELECT
                npc_id AS id,
                "order",
                name,
                image,
                json_agg(quest) AS quests
            FROM (
                     SELECT * FROM quest_based
                     UNION ALL
                     SELECT * FROM node_only
                 ) AS all_quests
            GROUP BY npc_id, name, image, "order"
            order by "order";
        """
