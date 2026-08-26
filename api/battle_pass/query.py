class BattlePassQueryV3:
    @staticmethod
    def active_season_sql():
        return """
            select id,
                   code,
                   title_en,
                   title_ko,
                   title_ja,
                   description_en,
                   description_ko,
                   description_ja,
                   page_count,
                   start_time,
                   end_time,
                   sort_order,
                   update_time
            from battle_pass_seasons
            where is_active is true
              and (start_time is null or start_time <= now())
              and (end_time is null or end_time >= now())
            order by sort_order nulls last, start_time desc nulls last, id
            limit 1;
        """

    @staticmethod
    def season_by_code_sql():
        return """
            select id,
                   code,
                   title_en,
                   title_ko,
                   title_ja,
                   description_en,
                   description_ko,
                   description_ja,
                   page_count,
                   start_time,
                   end_time,
                   is_active,
                   sort_order,
                   update_time
            from battle_pass_seasons
            where code = :season_code
            limit 1;
        """

    @staticmethod
    def documents_by_season_sql():
        return """
            select id,
                   name_en,
                   name_ko,
                   name_ja,
                   image,
                   document_role,
                   sort_order
            from battle_pass_documents
            where season_id = :season_id
              and is_use is true
            order by sort_order nulls last, id;
        """

    @staticmethod
    def rewards_by_season_sql():
        return """
            select id,
                   page_number,
                   reward_type,
                   name_en,
                   name_ko,
                   name_ja,
                   image,
                   reward_quantity,
                   document_price,
                   sort_order
            from battle_pass_rewards
            where season_id = :season_id
              and is_use is true
            order by page_number, sort_order, id;
        """

    @staticmethod
    def requirements_by_season_sql():
        return """
            select bprr.reward_id,
                   bprr.document_id,
                   bprr.quantity,
                   bprr.sort_order,
                   bpd.name_en as document_name_en,
                   bpd.name_ko as document_name_ko,
                   bpd.name_ja as document_name_ja,
                   bpd.image as document_image,
                   bpd.document_role
            from battle_pass_reward_requirements bprr
                     join battle_pass_rewards bpr
                          on bprr.reward_id = bpr.id
                     join battle_pass_documents bpd
                          on bprr.document_id = bpd.id
            where bpr.season_id = :season_id
              and bpr.is_use is true
              and bpd.is_use is true
            order by bprr.reward_id, bprr.sort_order nulls last, bprr.document_id;
        """
