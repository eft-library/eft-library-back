class SearchUtil:
    @staticmethod
    def get_sitemap_query():
        """
        sitemap 조회 쿼리
        """
        return """
            select '/map-of-tarkov/' || id as tkl_link
            from map_group_i18n
            union all
            select '/rank' as tkl_link
            union all
            select '/wipe' as tkl_link
            union all
            select '/roadmap' as tkl_link
            union all
            select '/price' as tkl_link
            union all
            select '/planner' as tkl_link
            union all
            select '/privacy-policy' as tkl_link
            union all
            select '/terms' as tkl_link
            union all
            select '/map/' || id as tkl_link
            from map_group_i18n
            union all
            select '/boss/' || url_mapping as tkl_link
            from boss_i18n
            where is_boss
            union all
            select '/hideout' as tkl_link
            union all
            select '/quest' as tkl_link
            union all
            select '/quest/detail/' || url_mapping as tkl_link
            from quest_i18n
            union all
            select '/weapon' as tkl_link
            union all
            select '/ammo' as tkl_link
            union all
            select '/head-wear' as tkl_link
            union all
            select '/rig' as tkl_link
            union all
            select '/armor-vest' as tkl_link
            union all
            select '/headset' as tkl_link
            union all
            select '/backpack' as tkl_link
            union all
            select '/medical' as tkl_link
            union all
            select '/container' as tkl_link
            union all
            select '/key' as tkl_link
            union all
            select '/provisions' as tkl_link
            union all
            select '/loot' as tkl_link
            union all
            select '/face-cover' as tkl_link
            union all
            select '/arm-band' as tkl_link
            union all
            select '/glasses' as tkl_link
            union all
            select '/notice/detail/' || id as tkl_link
            from notice_i18n
            union all
            select '/patch-notes/detail/' || id as tkl_link
            from patch_notes_i18n
            union all
            select '/event/detail/' || id as tkl_link
            from event_i18n
            order by tkl_link
                    """
