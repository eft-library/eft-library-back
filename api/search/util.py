class SearchUtil:
    @staticmethod
    def get_sitemap_query():
        """
        sitemap 조회 쿼리
        """
        return """
                    select '/map-of-tarkov/' || id as tkl_link
                    from tkl_map_parent
                    union all
                    select '/privacy-policy-kr' as tkl_link
                    union all
                    select '/privacy-policy-en' as tkl_link
                    union all
                    select '/terms' as tkl_link
                    union all
                    select '/map/' || id as tkl_link
                    from tkl_map_parent
                    union all
                    select '/boss' as tkl_link
                    union all
                    select '/hideout' as tkl_link
                    union all
                    select '/quest' as tkl_link
                    union all
                    select '/quest/detail/' || id as tkl_link
                    from tkl_quest
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
                    from tkl_notice
                    union all
                    select '/patch-notes/detail/' || id as tkl_link
                    from tkl_patch_notes
                    union all
                    select '/event/detail/' || id as tkl_link
                    from tkl_event
                    union all
                    select '/board/forum/detail/' || id as tkl_link
                    from tkl_board_forum
                    union all
                    select '/board/arena/detail/' || id as tkl_link
                    from tkl_board_arena
                    union all
                    select '/board/pvp/detail/' || id as tkl_link
                    from tkl_board_pvp
                    union all
                    select '/board/pve/detail/' || id as tkl_link
                    from tkl_board_pve
                    union all
                    select '/board/question/detail/' || id as tkl_link
                    from tkl_board_question
                    union all
                    select '/board/tip/detail/' || id as tkl_link
                    from tkl_board_tip
                    order by tkl_link
                    """
