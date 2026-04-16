class HomeQueryV3:
    @staticmethod
    def news_item_sql():
        return """
            select id,
                news_type,
                title_en,
                title_ko,
                title_ja,
                link,
                is_new,
                is_renewal
            from news_items
            where is_active = true
            order by sort_order;
        """

    @staticmethod
    def main_contents_sql():
        return """
            select id, name_en, name_ko, name_ja, url, image
            from main_contents
            order by sort_order;
        """

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
