class ItemUtil:

    @staticmethod
    def get_rig_query():
        return """
            SELECT *
            FROM item_i18n
            where category = 'Rig'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_head_wear_query():
        return """
            SELECT *
            FROM item_i18n
            where category = 'Headwear'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_armor_vest_query():
        return """
            SELECT *
            FROM item_i18n
            where category = 'ArmorVest'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_glasses_query():
        return """
            SELECT *
            FROM item_i18n
            where category = 'Glasses'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'blindness_protection')::NUMERIC
        """

    @staticmethod
    def get_face_cover_query():
        return """
            SELECT *
            FROM item_i18n
            where category = 'FaceCover'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_item_detail_query():
        return """
            select ii.id,
                   ii.name,
                   ii.category,
                   ii.id,
                   ii.name,
                   ii.category,
                   ii.image_width,
                   ii.image_height,
                   ii.url_mapping,
                   image,
                   info,
                   idi.hideout_items,
                   idi.used_in_crafts,
                   idi.rewarded_by_npcs,
                   idi.rewarded_by_quests,
                   idi.required_by_quest_item,
                   idi.required_by_quest_item_array,
                   idi.rewarded_by_quests_craft_unlock,
                   idi.rewarded_by_quests_offer_unlock
            from item_i18n ii
                     LEFT JOIN item_detail_i18n idi on ii.id = idi.id
            WHERE ii.url_mapping = :url_mapping
        """
