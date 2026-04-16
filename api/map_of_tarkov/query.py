class MapOfTarkovQueryV3:
    @staticmethod
    def boss_info_by_map_sql():
        return """
            select b.id,
                b.name_en,
                b.name_ko,
                b.name_ja,
                b.faction,
                b.image,
                b.normalized_name,
                b.health_total,
                b.health_image,
                b.head_hp,
                b.thorax_hp,
                b.stomach_hp,
                b.left_arm_hp,
                b.right_arm_hp,
                b.left_leg_hp,
                b.right_leg_hp,
                bs.spawn_chance
            from bosses b
                     join boss_spawn bs on b.id = bs.boss_id
            where bs.map_id = :map_id
              and b.is_boss = true
            order by b.sort_order;
        """

    @staticmethod
    def boss_followers_by_parent_ids_sql():
        return """
            select id,
                name_en,
                name_ko,
                name_ja,
                normalized_name,
                parent_boss_id
            from bosses
            where parent_boss_id = any(:boss_ids)
            order by sort_order;
        """
