class PlannerUtil:

    @staticmethod
    def user_quest_query():
        """
        사용자 퀘스트 조회 쿼리
        """

        return """
                select tkl_npc.id                                                                                                  as npc_id,
                       tkl_npc.name_kr                                                                                             as npc_name_kr,
                       tkl_npc.name_en                                                                                             as npc_name_en,
                       tkl_npc.image                                                                                               as npc_image,
                       jsonb_agg(jsonb_build_object('quest_id', rq, 'quest_name_en', tkl_quest.name_en, 'quest_name_kr',
                                                    tkl_quest.name_kr, 'requirements_kr', tkl_quest.requirements_kr, 'requirements_en',
                                                    tkl_quest.requirements_en, 'objectives_kr', tkl_quest.objectives_kr,
                                                    'objectives_en',
                                                    tkl_quest.objectives_en, 'url_mapping', tkl_quest.url_mapping, 'next',
                                                    COALESCE(tkl_quest.next, jsonb '[]'::jsonb)))                                  as quest_info
                from tkl_user_quest
                         left join lateral unnest(tkl_user_quest.quest_id) AS rq ON true
                         left join tkl_quest on rq = tkl_quest.id
                         left join tkl_npc on tkl_quest.npc_value = tkl_npc.id
                WHERE tkl_user_quest.user_email = :user_email
                group by tkl_npc.id, tkl_npc.name_kr, tkl_npc.name_en
                order by tkl_npc.id
                """
