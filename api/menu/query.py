class MenuQuery:
    @staticmethod
    def menu_groups_sql():
        return """
            select id,
                name_en,
                name_ko,
                name_ja
            from menu_groups
            order by sort_order;
        """

    @staticmethod
    def menu_sub_groups_sql():
        return """
            select id,
                name_en,
                name_ko,
                name_ja,
                parent_group_id,
                url
            from menu_sub_groups
            order by sort_order;
        """

    @staticmethod
    def autocomplete_items_sql():
        return """
            select url, autocomplete_text_en, autocomplete_text_ko, autocomplete_text_ja
            from autocomplete_items
            order by sort_order;
        """
