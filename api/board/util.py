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
               tkl_user.nick_name,
               combined.comment_cnt
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
                   tkl_board_type.name_kr,
                   count(tkl_comments.id) as comment_cnt
            FROM (
                {union_all_query}
            ) as board
            {join_clause}
            LEFT JOIN tkl_board_type ON board.type = tkl_board_type.value
            LEFT join tkl_comments on board.id = tkl_comments.board_id
            group by board.id, board.type, board.create_time, board.title, board.contents, board.thumbnail, board.writer, board.like_count, board.view_count, board.update_time, tkl_board_type.name_kr
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

    @staticmethod
    def get_post_count_query(board_type: str):
        if "forum" == board_type:
            return "SELECT id, contents, title, writer FROM tkl_board_forum"
        elif "arena" == board_type:
            return "SELECT id, contents, title, writer  FROM tkl_board_arena"
        elif "pve" == board_type:
            return "SELECT id, contents, title, writer  FROM tkl_board_pve"
        elif "pvp" == board_type:
            return "SELECT id, contents, title, writer  FROM tkl_board_pvp"
        elif "question" == board_type:
            return "SELECT id, contents, title, writer  FROM tkl_board_question"
        elif "tip" == board_type:
            return "SELECT id, contents, title, writer  FROM tkl_board_tip"
        elif "trash" == board_type:
            return "SELECT id, contents, title, writer  FROM tkl_board_trash"
        else:
            return """
                    SELECT id, contents, title, writer  FROM tkl_board_forum
                    UNION ALL
                    SELECT id, contents, title, writer  FROM tkl_board_arena
                    UNION ALL
                    SELECT id, contents, title, writer  FROM tkl_board_pve
                    UNION ALL
                    SELECT id, contents, title, writer  FROM tkl_board_pvp
                    UNION ALL
                    SELECT id, contents, title, writer  FROM tkl_board_question
                    UNION ALL
                    SELECT id, contents, title, writer  FROM tkl_board_tip
                """

    @staticmethod
    def get_post_count_issue_clause(issue: bool):
        return (
            "join tkl_board_issue on tkl_board_issue.board_id = combined.id"
            if issue
            else ""
        )

    @staticmethod
    def get_post_query(board_type: str):
        if "forum" == board_type:
            return "SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_forum"
        elif "arena" == board_type:
            return "SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_arena"
        elif "pve" == board_type:
            return "SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_pve"
        elif "pvp" == board_type:
            return "SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_pvp"
        elif "question" == board_type:
            return "SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_question"
        elif "tip" == board_type:
            return "SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_tip"
        elif "trash" == board_type:
            return "SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_trash"
        else:
            return """
                SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_forum
                UNION ALL
                SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_arena
                UNION ALL
                SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_pve
                UNION ALL
                SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_pvp
                UNION ALL
                SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_question
                UNION ALL
                SELECT id, title, contents, thumbnail, writer, like_count, view_count, type, create_time, update_time FROM tkl_board_tip
            """

    @staticmethod
    def get_post_issue_clause(issue: bool):
        return (
            "JOIN tkl_board_issue ON board.id = tkl_board_issue.board_id"
            if issue
            else ""
        )

    @staticmethod
    def get_post_where_clause(search_type: str):
        if search_type == "contents":
            return "WHERE contents LIKE :word"
        elif search_type == "contents_title":
            return "WHERE contents LIKE :word OR title LIKE :word"
        elif search_type == "title":
            return "WHERE title LIKE :word"
        elif search_type == "nickname":
            return "WHERE nick_name LIKE :word"
        else:
            return ""

    @staticmethod
    def get_post_count_where_clause(search_type: str):
        if search_type == "contents":
            return "WHERE contents LIKE :word"
        elif search_type == "contents_title":
            return "WHERE contents LIKE :word OR title LIKE :word"
        elif search_type == "title":
            return "WHERE title LIKE :word"
        elif search_type == "nickname":
            return "WHERE nick_name LIKE :word"
        else:
            return ""
