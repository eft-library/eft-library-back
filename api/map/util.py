class MapUtil:
    @staticmethod
    def get_map_query():
        return """
            SELECT parent_value,
                   jsonb_agg(child_json) AS children
            FROM (SELECT parent_value,
                         jsonb_build_object(
                                 'id', id,
                                 'name', name,
                                 'three_image', three_image,
                                 'three_item_path', three_item_path,
                                 'jpg_image', jpg_image,
                                 'jpg_item_path', jpg_item_path,
                                 'depth', depth,
                                 'order', "order",
                                 'link', link,
                                 'mot_image', mot_image,
                                 'map_json', map_json,
                                 'update_time', update_time
                         ) AS child_json
                  FROM map_group_i18n
                  ORDER BY parent_value, depth, "order") AS ordered_children
            GROUP BY parent_value
        """
