class RoadmapUtil:
    @staticmethod
    def get_roadmap_node():
        return """
            select rn.id,
                   rn.total_x_coordinate,
                   rn.total_y_coordinate,
                   rn.single_x_coordinate,
                   rn.single_y_coordinate,
                   rn.node_color,
                   rn.update_time,
                   qi.url_mapping,
                   qi.url_mapping,
                   qi.name,
                   qi.required_kappa,
                   qi.npc_id,
                   qi.next,
                   qi.prev
            from roadmap_node rn
                     left join public.quest_i18n qi on rn.id = qi.id    
        """
