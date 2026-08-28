class PrestigeQueryV3:
    @staticmethod
    def levels_sql():
        return """
            select id, prestige_level, name_key,
                   name_en, name_ko, name_ja,
                   icon_link, image_link, sort_order, update_time
            from prestige_levels
            where is_use is true
            order by prestige_level, sort_order nulls last, id;
        """

    @staticmethod
    def level_sql():
        return """
            select id, prestige_level, name_key,
                   name_en, name_ko, name_ja,
                   icon_link, image_link, sort_order, update_time
            from prestige_levels
            where prestige_level = :prestige_level
              and is_use is true
            limit 1;
        """

    @staticmethod
    def conditions_sql():
        return """
            select pc.*,
                   q.normalized_name as task_normalized_name,
                   q.name_en as task_name_en,
                   q.name_ko as task_name_ko,
                   q.name_ja as task_name_ja,
                   hm.normalized_name as station_normalized_name,
                   hm.name_en as station_name_en,
                   hm.name_ko as station_name_ko,
                   hm.name_ja as station_name_ja
            from prestige_conditions pc
                     left join quests q on pc.task_id = q.id
                     left join hideout_master hm on pc.station_id = hm.id
            where pc.prestige_id = any(:prestige_ids)
            order by pc.prestige_id, pc.sort_order nulls last, pc.id;
        """

    @staticmethod
    def condition_items_sql():
        return """
            select pci.condition_id, pci.item_id, pci.sort_order,
                   i.normalized_name, i.name_en, i.name_ko, i.name_ja, i.image
            from prestige_condition_items pci
                     join prestige_conditions pc on pci.condition_id = pc.id
                     left join items i on pci.item_id = i.id
            where pc.prestige_id = any(:prestige_ids)
            order by pci.condition_id, pci.sort_order nulls last, pci.item_id;
        """

    @staticmethod
    def condition_statuses_sql():
        return """
            select pcs.condition_id, pcs.status, pcs.sort_order
            from prestige_condition_statuses pcs
                     join prestige_conditions pc on pcs.condition_id = pc.id
            where pc.prestige_id = any(:prestige_ids)
            order by pcs.condition_id, pcs.sort_order nulls last, pcs.status;
        """

    @staticmethod
    def condition_maps_sql():
        return """
            select pcm.condition_id, pcm.map_id, pcm.sort_order,
                   m.normalized_name, m.name_en, m.name_ko, m.name_ja
            from prestige_condition_maps pcm
                     join prestige_conditions pc on pcm.condition_id = pc.id
                     left join maps m on pcm.map_id = m.id
            where pc.prestige_id = any(:prestige_ids)
            order by pcm.condition_id, pcm.sort_order nulls last, pcm.map_id;
        """

    @staticmethod
    def reward_items_sql():
        return """
            select pri.prestige_id, pri.item_id, pri.quantity,
                   pri.attributes, pri.sort_order,
                   i.normalized_name, i.name_en, i.name_ko, i.name_ja, i.image
            from prestige_reward_items pri
                     left join items i on pri.item_id = i.id
            where pri.prestige_id = any(:prestige_ids)
            order by pri.prestige_id, pri.sort_order nulls last, pri.item_id;
        """

    @staticmethod
    def reward_skills_sql():
        return """
            select prestige_id, skill_name, skill_level, sort_order
            from prestige_reward_skills
            where prestige_id = any(:prestige_ids)
            order by prestige_id, sort_order nulls last, skill_name;
        """

    @staticmethod
    def reward_customizations_sql():
        return """
            select customization_id, prestige_id, name_key,
                   name_en, name_ko, name_ja, image_link,
                   customization_type, customization_type_name_key,
                   customization_type_name_en, customization_type_name_ko,
                   customization_type_name_ja, sort_order
            from prestige_reward_customizations
            where prestige_id = any(:prestige_ids)
            order by prestige_id, sort_order nulls last, customization_id;
        """

    @staticmethod
    def reward_customization_items_sql():
        return """
            select prci.customization_id, prci.item_id, prci.sort_order,
                   i.normalized_name, i.name_en, i.name_ko, i.name_ja, i.image
            from prestige_reward_customization_items prci
                     join prestige_reward_customizations prc
                          on prci.customization_id = prc.customization_id
                     left join items i on prci.item_id = i.id
            where prc.prestige_id = any(:prestige_ids)
            order by prci.customization_id, prci.sort_order nulls last, prci.item_id;
        """

    @staticmethod
    def transfer_settings_sql():
        return """
            select id, prestige_id, setting_type, name_key,
                   name_en, name_ko, name_ja, skill_type,
                   transfer_rate, grid_width, grid_height, sort_order
            from prestige_transfer_settings
            where prestige_id = any(:prestige_ids)
            order by prestige_id, sort_order nulls last, id;
        """

    @staticmethod
    def transfer_filters_sql():
        return """
            select ptfv.transfer_setting_id, ptfv.filter_type,
                   ptfv.value_id, ptfv.sort_order
            from prestige_transfer_filter_values ptfv
                     join prestige_transfer_settings pts
                          on ptfv.transfer_setting_id = pts.id
            where pts.prestige_id = any(:prestige_ids)
            order by ptfv.transfer_setting_id, ptfv.filter_type,
                     ptfv.sort_order nulls last, ptfv.value_id;
        """
