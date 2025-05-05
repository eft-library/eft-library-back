class RoadmapUtil:
    @staticmethod
    def get_roadmap_node():
        return """
            SELECT ni.id,
                   ni.name,
                   ni.image,
                   COALESCE(
                                   json_agg(
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
                                           'node_color', rn.node_color,
                                           'task_next', COALESCE((SELECT jsonb_agg(elem -> 'task' -> 'id')
                                                                  FROM jsonb_array_elements(COALESCE(qi.task_next, '[]'::jsonb)) AS elem),
                                                                 '[]'::jsonb),
                                           'task_requirements', COALESCE((SELECT jsonb_agg(elem -> 'task' -> 'id')
                                                                          FROM jsonb_array_elements(COALESCE(qi.task_requirements, '[]'::jsonb)) AS elem),
                                                                         '[]'::jsonb)
                                   )
                                           ) FILTER (WHERE qi.id IS NOT NULL),
                                   '[]'
                   ) AS quests
            FROM npc_i18n ni
                     LEFT JOIN quest_i18n qi ON ni.id = qi.npc_id
                     LEFT JOIN roadmap_node rn ON qi.id = rn.id
            GROUP BY ni.id, ni.name, ni.image;
        """
