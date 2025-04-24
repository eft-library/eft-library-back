class PlannerUtil:

    @staticmethod
    def user_quest_query():
        """
        사용자 퀘스트 조회 쿼리
        """

        return """
            select npc_i18n.id                                                                 as npc_id,
                   npc_i18n.name                                                               as npc_name,
                   npc_i18n.image                                                              as npc_image,
                   jsonb_agg(jsonb_build_object('quest_id', rq, 'quest_name', quest_i18n.name, 'requirements_kr',
                                                quest_i18n.requirements, 'requirements', 'objectives', quest_i18n.objectives,
                                                'url_mapping', quest_i18n.url_mapping, 'next',
                                                COALESCE(quest_i18n.next, jsonb '[]'::jsonb))) as quest_info
            from user_quest
                     left join lateral unnest(user_quest.quest_list) AS rq ON true
                     left join quest_i18n on rq = quest_i18n.id
                     left join npc_i18n on quest_i18n.npc_id = npc_i18n.id
            WHERE user_quest.user_email = :user_email
            group by npc_i18n.id, npc_i18n.name
            order by npc_i18n.id
                """
