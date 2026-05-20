class LiveMapQueryV3:
    @staticmethod
    def map_selector_sql():
        return """
            select selector.id,
                   selector.normalized_name,
                   selector.name_en,
                   selector.name_ko,
                   selector.name_ja,
                   selector.sort_order
            from live_map_floors lmf
                     join maps m on lmf.map_id = m.id
                     join maps selector on selector.id = coalesce(m.parent_map_id, m.id)
            where m.is_use is true
              and selector.is_use is true
            group by selector.id,
                     selector.normalized_name,
                     selector.name_en,
                     selector.name_ko,
                     selector.name_ja,
                     selector.sort_order
            order by selector.sort_order, selector.name_en;
        """

    @staticmethod
    def quest_points_by_map_sql():
        return """
            select lmp.id,
                   lmp.quest_id,
                   lmp.objective_id,
                   lmp.map_id,
                   lmp.floor_id,
                   lmp.floor_no,
                   lmp.x,
                   lmp.z,
                   lmp.y,
                   q.normalized_name as quest_normalized_name,
                   q.name_en as quest_name_en,
                   q.name_ko as quest_name_ko,
                   q.name_ja as quest_name_ja,
                   q.min_player_level,
                   qo.type as objective_type,
                   qo.description_en as objective_description_en,
                   qo.description_ko as objective_description_ko,
                   qo.description_ja as objective_description_ja,
                   qo.count as objective_count,
                   qo.found_in_raid,
                   t.id as trader_id,
                   t.normalized_name as trader_normalized_name,
                   t.name_en as trader_name_en,
                   t.name_ko as trader_name_ko,
                   t.name_ja as trader_name_ja,
                   t.image as trader_image
            from live_map_points lmp
                     left join quests q on lmp.quest_id = q.id
                     left join quest_objectives qo
                               on lmp.objective_id = qo.objective_id
                              and (lmp.quest_id is null or lmp.quest_id = qo.quest_id)
                     left join traders t on q.trader_id = t.id
            where lmp.map_id = :map_id
            order by lmp.floor_no, lmp.sort_order, lmp.id;
        """

    @staticmethod
    def point_details_by_map_sql():
        return """
            select lmpd.id,
                   lmpd.point_id,
                   lmpd.description_en,
                   lmpd.description_ko,
                   lmpd.description_ja,
                   lmpd.image
            from live_map_point_details lmpd
                     join live_map_points lmp on lmpd.point_id = lmp.id
            where lmp.map_id = :map_id
            order by lmpd.point_id, lmpd.sort_order, lmpd.id;
        """
