class BoardUtil:
    @staticmethod
    def get_post_query_v2():
        """
        커뮤니티 검색, 이슈, 타입별 전체 조회 쿼리 v2
        """

        return """
        SELECT combined.id,
               combined.title,
               combined.contents,
               combined.thumbnail,
               combined.writer,
               combined.like_count,
               combined.view_count,
               combined.type,
               combined.create_time,
               combined.update_time,
               combined.name_kr as type_kr,
               tkl_user.icon,
               tkl_user.nick_name
        FROM (
            SELECT board.id,
                   board.type,
                   board.create_time,
                   board.title,
                   board.contents,
                   board.thumbnail,
                   board.writer,
                   board.like_count,
                   board.view_count,
                   board.update_time,
                   tkl_board_type.name_kr
            FROM (
                {union_all_query}
            ) as board
            {join_clause}
            LEFT JOIN tkl_board_type ON board.type = tkl_board_type.value
        ) as combined
        LEFT JOIN tkl_user ON combined.writer = tkl_user.email
        {where_clause}
        ORDER BY create_time DESC
        LIMIT :limit OFFSET :offset        
        """

    @staticmethod
    def get_post_max_cnt_query_v2():
        """
        커뮤니티 전체 데이터 수 조회 쿼리 v2
        """
        return """
        select count(*)
        from (SELECT *
              FROM ({count_all_query}) AS combined
                       join tkl_user on writer = tkl_user.email
                       {count_join_clause}
                       {count_where_clause}) as a
        """

    @staticmethod
    def get_user_max_cnt_query():
        """
        직상힌 글 전체 개수
        """
        return """
                select count(*)
                from (select *
                      from tkl_board_pvp
                      where writer = :email
                      union all
                      select *
                      from tkl_board_pve
                      where writer = :email
                      union all
                      select *
                      from tkl_board_tip
                      where writer = :email
                      union all
                      select *
                      from tkl_board_arena
                      where writer = :email
                      union all
                      select *
                      from tkl_board_forum
                      where writer = :email
                      union all
                      select *
                      from tkl_board_question
                      where writer = :email) as a
                """

    @staticmethod
    def get_user_posts():
        """
        사용자 작성글 조회
        """

        return """
                select *
                from tkl_board_pvp
                where writer = :email
                union all
                select *
                from tkl_board_pve
                where writer = :email
                union all
                select *
                from tkl_board_tip
                where writer = :email
                union all
                select *
                from tkl_board_arena
                where writer = :email
                union all
                select *
                from tkl_board_forum
                where writer = :email
                union all
                select *
                from tkl_board_question
                where writer = :email
                ORDER BY create_time DESC
                LIMIT :limit OFFSET :offset
                """
