class ItemUtil:

    @staticmethod
    def get_rig_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'Rig'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_head_wear_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'Headwear'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_glasses_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'Glasses'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'blindness_protection')::NUMERIC
        """

    @staticmethod
    def get_face_cover_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'FaceCover'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_item_detail_query():
        return """
            SELECT
              ti.id,
              ti.name_en,
              ti.name_kr,
              ti.category,
              ti.image,
              ti.image_width,
              ti.image_height,
              ti.info,
              ti.update_time,
              ti.url_mapping,
              COALESCE(
                json_agg(
                  json_build_object(
                    'id', thir.id,
                    'level_id', thir.level_id,
                    'name_en', thir.name_en,
                    'name_kr', thir.name_kr,
                    'quantity', thir.quantity,
                    'count', thir.count,
                    'image', thir.image,
                    'update_time', thir.update_time,
                    'item_id', thir.item_id
                  )
                ) FILTER (WHERE thir.id IS NOT NULL),
                '[]'
              ) AS hideout_items,
              COALESCE(
                json_agg(
                  DISTINCT jsonb_build_object(
                    'id', thc.id,
                    'name_en', thc.name_en,
                    'name_kr', thc.name_kr,
                    'level_id', thc.level_id,
                    'level', thc.level,
                    'duration', thc.duration,
                    'reward_item_id', thc.reward_item_id,
                    'image', thc.image,
                    'quantity', thc.quantity,
                    'update_time', thc.update_time
                  )
                ) FILTER (WHERE thc.id IS NOT NULL),
                '[]'
              ) AS used_in_crafts
            FROM TKL_ITEM ti
            LEFT JOIN tkl_hideout_item_require thir ON ti.id = thir.item_id
            LEFT JOIN tkl_hideout_crafts thc ON EXISTS (
              SELECT 1
              FROM jsonb_array_elements(thc.req_item) AS elem
              WHERE elem->'item'->>'id' = ti.id
            )
            WHERE ti.url_mapping = :url_mapping
            GROUP BY
              ti.id, ti.name_en, ti.name_kr, ti.category, ti.image,
              ti.image_width, ti.image_height, ti.info, ti.update_time, ti.url_mapping
        """