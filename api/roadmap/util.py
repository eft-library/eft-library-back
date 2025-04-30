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
                   qi.name,
                   qi.url_mapping,
                   qi.kappa_required,
                   qi.npc_id,
                   qi.task_next,
                   qi.task_requirements
            from roadmap_node rn
                     left join quest_i18n qi on rn.id = qi.id
        """
