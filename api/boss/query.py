class BossQueryV3:
    @staticmethod
    def boss_selector_sql():
        return """
            select id,
                name_en,
                name_ko,
                name_ja,
                parent_boss_id,
                normalized_name
            from bosses b
            where b.is_boss = true
            order by b.sort_order;
        """

    @staticmethod
    def boss_id_sql():
        return """
            select id
            from bosses
            where normalized_name = :normalized_name;
        """

    @staticmethod
    def boss_info_sql():
        return """
            select id,
                name_en,
                name_ko,
                name_ja,
                is_boss,
                parent_boss_id,
                faction,
                image,
                normalized_name,
                health_total,
                health_image,
                head_hp,
                thorax_hp,
                stomach_hp,
                left_arm_hp,
                right_arm_hp,
                left_leg_hp,
                right_leg_hp,
                guide_en,
                guide_ko,
                guide_ja
            from bosses
            where normalized_name = :normalized_name;
        """

    @staticmethod
    def boss_map_sql():
        return """
            select bs.spawn_chance, m.name_en, m.name_ko, m.name_ja
            from boss_spawn bs
                    left join maps m on bs.map_id = m.id
            where bs.boss_id = :boss_id;
        """

    @staticmethod
    def boss_item_sql():
        return """
            select bi.quantity,
                i.name_en,
                i.name_ko,
                i.name_ja,
                i.normalized_name,
                i.width,
                i.height,
                i.image
            from boss_item bi
                    left join items i on bi.item_id = i.id
            where bi.boss_id = :boss_id
            order by sort_order;
            """

    @staticmethod
    def boss_follower_sql():
        return """
            select id
            from bosses
            where parent_boss_id = :boss_id;
            """

    @staticmethod
    def boss_follower_info_sql():
        return """
            select id,
                name_en,
                name_ko,
                name_ja,
                is_boss,
                parent_boss_id,
                faction,
                image,
                normalized_name,
                health_total,
                health_image,
                head_hp,
                thorax_hp,
                stomach_hp,
                left_arm_hp,
                right_arm_hp,
                left_leg_hp,
                right_leg_hp,
                guide_en,
                guide_ko,
                guide_ja
            from bosses
            where id = any(:boss_ids)
            order by sort_order;
            """

    @staticmethod
    def boss_follower_item_sql():
        return """
            select bi.boss_id,
                bi.quantity,
                i.name_en,
                i.name_ko,
                i.name_ja,
                i.normalized_name,
                i.width,
                i.height,
                i.image
            from boss_item bi
                     left join items i on bi.item_id = i.id
            where bi.boss_id = any(:boss_ids)
            order by bi.boss_id, sort_order;
            """
