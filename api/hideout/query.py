class HideoutQueryV3:
    @staticmethod
    def hideout_master_list_sql():
        return """
            select id,
                   name_en,
                   name_ko,
                   name_ja,
                   normalized_name
            from hideout_master
            order by name_en nulls last, id;
        """

    @staticmethod
    def user_hideout_sql():
        return """
            select email,
                   complete_list,
                   item_list,
                   update_time
            from user_hideout
            where email = :email;
        """

    @staticmethod
    def upsert_user_hideout_complete_list_sql():
        return """
            insert into user_hideout (email, complete_list, item_list, update_time)
            values (:email, :complete_list, '[]'::jsonb, :update_time)
            on conflict (email) do update
            set complete_list = excluded.complete_list,
                update_time = excluded.update_time;
        """

    @staticmethod
    def upsert_user_hideout_item_list_sql():
        return """
            insert into user_hideout (email, complete_list, item_list, update_time)
            values (:email, ARRAY[]::text[], cast(:item_list as jsonb), :update_time)
            on conflict (email) do update
            set item_list = cast(excluded.item_list as jsonb),
                update_time = excluded.update_time;
        """

    @staticmethod
    def hideout_master_sql():
        return """
            select id,
                   name_en,
                   name_ko,
                   name_ja,
                   normalized_name
            from hideout_master
            where normalized_name = :normalized_name;
        """

    @staticmethod
    def hideout_levels_sql():
        return """
            select id,
                   master_id,
                   hideout_level,
                   construction_time
            from hideout_levels
            where master_id = :master_id
            order by hideout_level;
        """

    @staticmethod
    def hideout_trader_require_sql():
        return """
            select htr.id,
                   htr.hideout_level_id,
                   htr.trader_id,
                   htr.trader_level,
                   t.name_en,
                   t.name_ko,
                   t.name_ja,
                   t.image
            from hideout_trader_require htr
                     left join traders t on htr.trader_id = t.id
            where htr.hideout_level_id = any(:level_ids)
            order by htr.hideout_level_id, htr.trader_level, t.sort_order nulls last;
        """

    @staticmethod
    def hideout_item_require_sql():
        return """
            select hir.id,
                   hir.hideout_level_id,
                   hir.item_id,
                   hir.quantity,
                   hir.in_raid,
                   i.name_en,
                   i.name_ko,
                   i.name_ja,
                   i.image,
                   i.width,
                   i.height,
                   i.normalized_name
            from hideout_item_require hir
                     left join items i on hir.item_id = i.id
            where hir.hideout_level_id = any(:level_ids)
            order by hir.hideout_level_id, i.name_en nulls last, hir.id;
        """

    @staticmethod
    def hideout_station_require_sql():
        return """
            select hsr.id,
                   hsr.hideout_level_id,
                   hsr.require_master_id,
                   hsr.station_level,
                   hm.name_en,
                   hm.name_ko,
                   hm.name_ja
            from hideout_station_require hsr
                     left join hideout_master hm on hsr.require_master_id = hm.id
            where hsr.hideout_level_id = any(:level_ids)
            order by hsr.hideout_level_id, hsr.station_level, hm.name_en nulls last;
        """

    @staticmethod
    def hideout_bonus_sql():
        return """
            select id,
                   hideout_level_id,
                   bonus_type,
                   name_en,
                   name_ko,
                   name_ja,
                   skill_name_en,
                   skill_name_ko,
                   skill_name_ja,
                   bonus_value
            from hideout_bonus
            where hideout_level_id = any(:level_ids)
            order by hideout_level_id, id;
        """

    @staticmethod
    def hideout_skill_require_sql():
        return """
            select id,
                   hideout_level_id,
                   require_level,
                   name_en,
                   name_ko,
                   name_ja,
                   image
            from hideout_skill_require
            where hideout_level_id = any(:level_ids)
            order by hideout_level_id, require_level, name_en nulls last, id;
        """

    @staticmethod
    def hideout_crafts_sql():
        return """
            select hc.id,
                   hc.hideout_level_id,
                   hc.reward_item_id,
                   hc.duration,
                   hc.reward_quantity,
                   i.name_en,
                   i.name_ko,
                   i.name_ja,
                   i.image,
                   i.width,
                   i.height,
                   i.normalized_name
            from hideout_crafts hc
                     left join items i on hc.reward_item_id = i.id
            where hc.hideout_level_id = any(:level_ids)
            order by hc.hideout_level_id, i.name_en nulls last, hc.id;
        """

    @staticmethod
    def hideout_craft_require_items_sql():
        return """
            select hcri.id,
                   hcri.craft_id,
                   hcri.item_id,
                   hcri.quantity,
                   i.name_en,
                   i.name_ko,
                   i.name_ja,
                   i.image,
                   i.width,
                   i.height,
                   i.normalized_name
            from hideout_craft_require_items hcri
                     left join items i on hcri.item_id = i.id
            where hcri.craft_id = any(:craft_ids)
            order by hcri.craft_id, i.name_en nulls last, hcri.id;
        """
