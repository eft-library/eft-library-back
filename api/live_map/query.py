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

    @staticmethod
    def story_points_by_map_sql():
        return """
            select lmsp.id,
                   lmsp.story_id,
                   lmsp.objective_id,
                   lmsp.map_id,
                   lmsp.floor_id,
                   lmsp.floor_no,
                   lmsp.x,
                   lmsp.z,
                   lmsp.y,
                   s.title_en,
                   s.title_ko,
                   s.title_ja
            from live_map_story_points lmsp
                     left join story s on lmsp.story_id = s.id
            where lmsp.map_id = :map_id
            order by lmsp.floor_no, lmsp.sort_order, lmsp.id;
        """

    @staticmethod
    def story_point_details_by_map_sql():
        return """
            select lmspd.id,
                   lmspd.point_id,
                   lmspd.description_en,
                   lmspd.description_ko,
                   lmspd.description_ja,
                   lmspd.image
            from live_map_story_point_details lmspd
                     join live_map_story_points lmsp on lmspd.point_id = lmsp.id
            where lmsp.map_id = :map_id
            order by lmspd.point_id, lmspd.sort_order, lmspd.id;
        """

    @staticmethod
    def story_requirements_by_story_ids_sql():
        return """
            select id,
                   story_id,
                   requirement_type,
                   description_en,
                   description_ko,
                   description_ja,
                   sort_order
            from story_requirements
            where story_id = any(:story_ids)
            order by story_id, sort_order, id;
        """

    @staticmethod
    def story_objectives_by_story_ids_sql():
        return """
            select objective_id,
                   story_id,
                   parent_objective_id,
                   objective_type,
                   description_en,
                   description_ko,
                   description_ja,
                   count,
                   is_optional,
                   sort_order
            from story_objectives
            where story_id = any(:story_ids)
            order by story_id, sort_order, objective_id;
        """

    @staticmethod
    def story_objective_items_by_story_ids_sql():
        return """
            select soi.objective_id,
                   soi.item_id,
                   soi.quantity,
                   soi.found_in_raid,
                   soi.item_role,
                   soi.sort_order,
                   i.normalized_name,
                   i.name_en,
                   i.name_ko,
                   i.name_ja,
                   i.image
            from story_objective_items soi
                     join story_objectives so on soi.objective_id = so.objective_id
                     left join items i on soi.item_id = i.id
            where so.story_id = any(:story_ids)
            order by soi.objective_id, soi.sort_order, i.name_en;
        """

    @staticmethod
    def story_objective_maps_by_story_ids_sql():
        return """
            select som.objective_id,
                   som.map_id,
                   som.sort_order,
                   m.normalized_name,
                   m.name_en,
                   m.name_ko,
                   m.name_ja
            from story_objective_maps som
                     join story_objectives so on som.objective_id = so.objective_id
                     left join maps m on som.map_id = m.id
            where so.story_id = any(:story_ids)
            order by som.objective_id, som.sort_order, m.name_en;
        """

    @staticmethod
    def event_points_by_map_sql():
        return """
            select lmep.id,
                   lmep.event_id,
                   lmep.objective_id,
                   lmep.map_id,
                   lmep.floor_id,
                   lmep.floor_no,
                   lmep.x,
                   lmep.z,
                   lmep.y,
                   e.title_en,
                   e.title_ko,
                   e.title_ja,
                   e.is_active,
                   t.id as trader_id,
                   t.normalized_name as trader_normalized_name,
                   t.name_en as trader_name_en,
                   t.name_ko as trader_name_ko,
                   t.name_ja as trader_name_ja,
                   t.image as trader_image
            from live_map_event_points lmep
                     join live_map_events e on lmep.event_id = e.id
                     left join traders t on e.trader_id = t.id
            where lmep.map_id = :map_id
              and e.is_active is true
            order by lmep.floor_no, lmep.sort_order, lmep.id;
        """

    @staticmethod
    def event_point_details_by_map_sql():
        return """
            select lmepd.id,
                   lmepd.point_id,
                   lmepd.description_en,
                   lmepd.description_ko,
                   lmepd.description_ja,
                   lmepd.image
            from live_map_event_point_details lmepd
                     join live_map_event_points lmep on lmepd.point_id = lmep.id
            where lmep.map_id = :map_id
            order by lmepd.point_id, lmepd.sort_order, lmepd.id;
        """

    @staticmethod
    def event_objectives_by_event_ids_sql():
        return """
            select objective_id,
                   event_id,
                   parent_objective_id,
                   objective_type,
                   description_en,
                   description_ko,
                   description_ja,
                   count,
                   is_optional,
                   sort_order
            from live_map_event_objectives
            where event_id = any(:event_ids)
            order by event_id, sort_order, objective_id;
        """

    @staticmethod
    def event_objective_items_by_event_ids_sql():
        return """
            select lmeoi.objective_id,
                   lmeoi.item_id,
                   lmeoi.quantity,
                   lmeoi.found_in_raid,
                   lmeoi.item_role,
                   lmeoi.sort_order,
                   i.normalized_name,
                   i.name_en,
                   i.name_ko,
                   i.name_ja,
                   i.image
            from live_map_event_objective_items lmeoi
                     join live_map_event_objectives lmeo
                          on lmeoi.objective_id = lmeo.objective_id
                     left join items i on lmeoi.item_id = i.id
            where lmeo.event_id = any(:event_ids)
            order by lmeoi.objective_id, lmeoi.sort_order, i.name_en;
        """
