class QuestUtil:

    @staticmethod
    def get_quest_detail_query():
        return """
            SELECT qi.id,
                   qi.npc_id,
                   qi.url_mapping,
                   qi.name,
                   qi.wiki_url,
                   qi.kappa_required,
                   qi.objectives,
                   qi.finish_rewards,
                   qi.min_player_level,
                   qi."order",
                   qi.guide,
                   qi.task_next,
                   qi.task_requirements,
                   ni.name  as npc_name,
                   ni.image as npc_image,
                   ni.barter_info
            FROM quest_i18n qi
                     LEFT JOIN npc_i18n ni on qi.npc_id = ni.id
            WHERE qi.url_mapping = :url_mapping
        """
