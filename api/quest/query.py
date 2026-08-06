class QuestQueryV3:
    @staticmethod
    def completion_graph_sql():
        return """
            select q.id,
                   coalesce(require_rel.task_requirements, array[]::text[]) as task_requirements,
                   coalesce(next_rel.task_next, array[]::text[]) as task_next
            from quests q
                     left join lateral (
                         select array_agg(qr.related_quest_id order by qr.sort_order, qr.related_quest_id) as task_requirements
                         from quest_relations qr
                                  join quests related_q
                                       on related_q.id = qr.related_quest_id
                                      and related_q.is_use is true
                         where qr.quest_id = q.id
                           and qr.relation_type = 'require'
                     ) require_rel on true
                     left join lateral (
                         select array_agg(qr.related_quest_id order by qr.sort_order, qr.related_quest_id) as task_next
                         from quest_relations qr
                                  join quests related_q
                                       on related_q.id = qr.related_quest_id
                                      and related_q.is_use is true
                         where qr.quest_id = q.id
                           and qr.relation_type = 'next'
                     ) next_rel on true
            where q.is_use is true
            order by q.sort_order, q.id;
        """

    @staticmethod
    def quest_list_sql():
        return """
            select q.id,
                   q.normalized_name,
                   q.name_en,
                   q.name_ko,
                   q.name_ja,
                   q.trader_id,
                   q.kappa_required,
                   q.min_player_level,
                   t.name_en as trader_name_en,
                   t.name_ko as trader_name_ko,
                   t.name_ja as trader_name_ja,
                   t.image as trader_image
            from quests q
                     left join traders t on q.trader_id = t.id
            where q.is_use is true
            order by q.sort_order, q.name_en;
        """

    @staticmethod
    def quest_feed_sql():
        return """
            select q.id,
                   q.normalized_name,
                   q.name_en,
                   q.name_ko,
                   q.name_ja,
                   q.guide_en,
                   q.guide_ko,
                   q.guide_ja,
                   q.update_time
            from quests q
            where q.is_use is true
            order by q.sort_order, q.name_en;
        """

    @staticmethod
    def quest_detail_sql():
        return """
            select q.id,
                   q.normalized_name,
                   q.name_en,
                   q.name_ko,
                   q.name_ja,
                   q.trader_id,
                   q.experience,
                   q.delay_max,
                   q.delay_min,
                   q.kappa_required,
                   q.min_player_level,
                   q.wiki_url,
                   q.guide_en,
                   q.guide_ko,
                   q.guide_ja,
                   t.name_en as trader_name_en,
                   t.name_ko as trader_name_ko,
                   t.name_ja as trader_name_ja,
                   t.normalized_name as trader_normalized_name,
                   t.image as trader_image
            from quests q
                     left join traders t on q.trader_id = t.id
            where q.normalized_name = :normalized_name
              and q.is_use is true;
        """

    @staticmethod
    def trader_list_sql():
        return """
            select id,
                   name_en,
                   name_ko,
                   name_ja,
                   normalized_name,
                   image
            from traders
            where is_use is true
            order by sort_order, name_en;
        """

    @staticmethod
    def quest_list_by_trader_sql():
        return """
            select q.id,
                   q.normalized_name,
                   q.name_en,
                   q.name_ko,
                   q.name_ja,
                   q.kappa_required,
                   q.min_player_level
            from quests q
                     join traders t on q.trader_id = t.id
            where t.normalized_name = :trader_normalized_name
              and q.is_use is true
            order by q.sort_order, q.name_en;
        """

    @staticmethod
    def quest_list_by_trader_id_sql():
        return """
            select q.id,
                   q.normalized_name,
                   q.name_en,
                   q.name_ko,
                   q.name_ja,
                   q.kappa_required,
                   q.min_player_level
            from quests q
            where q.trader_id = :trader_id
              and q.is_use is true
            order by q.sort_order, q.name_en;
        """

    @staticmethod
    def quest_relations_sql():
        return """
            select qr.relation_type,
                   qr.sort_order,
                   rq.id as related_quest_id,
                   rq.normalized_name,
                   rq.name_en,
                   rq.name_ko,
                   rq.name_ja
            from quest_relations qr
                     join quests rq on qr.related_quest_id = rq.id
            where qr.quest_id = :quest_id
              and rq.is_use is true
            order by qr.relation_type, qr.sort_order, rq.name_en;
        """

    @staticmethod
    def quest_objectives_sql():
        return """
            select objective_id,
                   quest_id,
                   type,
                   description_en,
                   description_ko,
                   description_ja,
                   count,
                   found_in_raid,
                   sort_order
            from quest_objectives
            where quest_id = :quest_id
              and is_use is true
            order by sort_order, objective_id;
        """

    @staticmethod
    def quest_objective_items_sql():
        return """
            select qoi.objective_id,
                   qoi.item_type,
                   qoi.sort_order,
                   i.id as item_id,
                   i.normalized_name,
                   i.name_en,
                   i.name_ko,
                   i.name_ja,
                   i.image
            from quest_objective_items qoi
                     left join items i on qoi.item_id = i.id
            where qoi.objective_id in (
                select objective_id
                from quest_objectives
                where quest_id = :quest_id
                  and is_use is true
            )
            order by qoi.objective_id, qoi.sort_order, i.name_en;
        """

    @staticmethod
    def quest_objective_required_keys_sql():
        return """
            select qork.objective_id,
                   i.id as key_id,
                   i.normalized_name,
                   i.name_en,
                   i.name_ko,
                   i.name_ja,
                   i.image
            from quest_objective_required_keys qork
                     left join items i on qork.key_id = i.id
            where qork.objective_id in (
                select objective_id
                from quest_objectives
                where quest_id = :quest_id
                  and is_use is true
            )
            order by qork.objective_id, i.name_en;
        """

    @staticmethod
    def quest_objective_maps_sql():
        return """
            select qom.objective_id,
                   qom.sort_order,
                   m.id as map_id,
                   m.normalized_name,
                   m.name_en,
                   m.name_ko,
                   m.name_ja
            from quest_objective_maps qom
                     left join maps m on qom.map_id = m.id
            where qom.objective_id in (
                select objective_id
                from quest_objectives
                where quest_id = :quest_id
                  and is_use is true
            )
            order by qom.objective_id, qom.sort_order, m.name_en;
        """

    @staticmethod
    def quest_reward_skills_sql():
        return """
            select name_en,
                   name_ko,
                   name_ja,
                   skill_level,
                   sort_order
            from quest_finish_reward_skills
            where quest_id = :quest_id
            order by sort_order, name_en;
        """

    @staticmethod
    def quest_reward_trader_standing_sql():
        return """
            select qfrts.trader_id,
                   qfrts.standing,
                   qfrts.sort_order,
                   t.normalized_name,
                   t.name_en,
                   t.name_ko,
                   t.name_ja,
                   t.image
            from quest_finish_reward_trader_standing qfrts
                     left join traders t on qfrts.trader_id = t.id
            where qfrts.quest_id = :quest_id
            order by qfrts.sort_order, t.name_en;
        """

    @staticmethod
    def quest_reward_offer_unlock_sql():
        return """
            select qfrou.offer_id,
                   qfrou.trader_id,
                   qfrou.item_id,
                   qfrou.level,
                   qfrou.sort_order,
                   t.normalized_name as trader_normalized_name,
                   t.name_en as trader_name_en,
                   t.name_ko as trader_name_ko,
                   t.name_ja as trader_name_ja,
                   t.image as trader_image,
                   i.normalized_name as item_normalized_name,
                   i.name_en as item_name_en,
                   i.name_ko as item_name_ko,
                   i.name_ja as item_name_ja,
                   i.image as item_image
            from quest_finish_reward_offer_unlock qfrou
                     left join traders t on qfrou.trader_id = t.id
                     left join items i on qfrou.item_id = i.id
            where qfrou.quest_id = :quest_id
            order by qfrou.sort_order, qfrou.offer_id;
        """

    @staticmethod
    def quest_reward_items_sql():
        return """
            select qfri.item_id,
                   qfri.quantity,
                   qfri.sort_order,
                   i.normalized_name,
                   i.name_en,
                   i.name_ko,
                   i.name_ja,
                   i.image
            from quest_finish_reward_items qfri
                     left join items i on qfri.item_id = i.id
            where qfri.quest_id = :quest_id
            order by qfri.sort_order, i.name_en;
        """

    @staticmethod
    def quest_reward_craft_unlocks_sql():
        return """
            select qfrcu.craft_id,
                   qfrcu.station_level,
                   qfrcu.sort_order,
                   hc.reward_item_id,
                   i.normalized_name,
                   i.name_en,
                   i.name_ko,
                   i.name_ja,
                   i.image
            from quest_finish_reward_craft_unlocks qfrcu
                     left join hideout_crafts hc on qfrcu.craft_id = hc.id
                     left join items i on hc.reward_item_id = i.id
            where qfrcu.quest_id = :quest_id
            order by qfrcu.sort_order, qfrcu.craft_id;
        """
