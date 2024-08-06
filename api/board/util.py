class BoardUtil:
    @staticmethod
    def get_post_query():
        """
        커뮤니티 전체 조회 쿼리
        """

        return """
                    SELECT combined.id,
                           combined.title,
                           combined.contents,
                           combined.thumbnail,
                           combined.writer,
                           combined.like_count,
                           combined.dislike_count,
                           combined.view_count,
                           combined.type,
                           combined.create_time,
                           combined.update_time,
                           combined.name_kr as type_kr,
                           tkl_user.icon,
                           tkl_user.nick_name
                    FROM (SELECT tkl_board_forum.id,
                                 tkl_board_forum.title,
                                 tkl_board_forum.contents,
                                 tkl_board_forum.thumbnail,
                                 tkl_board_forum.writer,
                                 tkl_board_forum.like_count,
                                 tkl_board_forum.dislike_count,
                                 tkl_board_forum.view_count,
                                 tkl_board_forum.type,
                                 tkl_board_forum.create_time,
                                 tkl_board_forum.update_time,
                                 tkl_board_type.name_kr
                          FROM tkl_board_forum
                                   left join tkl_board_type on tkl_board_forum.type = tkl_board_type.value
                          UNION ALL
                          SELECT tkl_board_arena.id,
                                 tkl_board_arena.title,
                                 tkl_board_arena.contents,
                                 tkl_board_arena.thumbnail,
                                 tkl_board_arena.writer,
                                 tkl_board_arena.like_count,
                                 tkl_board_arena.dislike_count,
                                 tkl_board_arena.view_count,
                                 tkl_board_arena.type,
                                 tkl_board_arena.create_time,
                                 tkl_board_arena.update_time,
                                 tkl_board_type.name_kr
                          FROM tkl_board_arena
                                   left join tkl_board_type on tkl_board_arena.type = tkl_board_type.value
                          UNION ALL
                          SELECT tkl_board_pve.id,
                                 tkl_board_pve.title,
                                 tkl_board_pve.contents,
                                 tkl_board_pve.thumbnail,
                                 tkl_board_pve.writer,
                                 tkl_board_pve.like_count,
                                 tkl_board_pve.dislike_count,
                                 tkl_board_pve.view_count,
                                 tkl_board_pve.type,
                                 tkl_board_pve.create_time,
                                 tkl_board_pve.update_time,
                                 tkl_board_type.name_kr
                          FROM tkl_board_pve
                                   left join tkl_board_type on tkl_board_pve.type = tkl_board_type.value
                          UNION ALL
                          SELECT tkl_board_pvp.id,
                                 tkl_board_pvp.title,
                                 tkl_board_pvp.contents,
                                 tkl_board_pvp.thumbnail,
                                 tkl_board_pvp.writer,
                                 tkl_board_pvp.like_count,
                                 tkl_board_pvp.dislike_count,
                                 tkl_board_pvp.view_count,
                                 tkl_board_pvp.type,
                                 tkl_board_pvp.create_time,
                                 tkl_board_pvp.update_time,
                                 tkl_board_type.name_kr
                          FROM tkl_board_pvp
                                   left join tkl_board_type on tkl_board_pvp.type = tkl_board_type.value
                          UNION ALL
                          SELECT tkl_board_question.id,
                                 tkl_board_question.title,
                                 tkl_board_question.contents,
                                 tkl_board_question.thumbnail,
                                 tkl_board_question.writer,
                                 tkl_board_question.like_count,
                                 tkl_board_question.dislike_count,
                                 tkl_board_question.view_count,
                                 tkl_board_question.type,
                                 tkl_board_question.create_time,
                                 tkl_board_question.update_time,
                                 tkl_board_type.name_kr
                          FROM tkl_board_question
                                   left join tkl_board_type on tkl_board_question.type = tkl_board_type.value
                          UNION ALL
                          SELECT tkl_board_tip.id,
                                 tkl_board_tip.title,
                                 tkl_board_tip.contents,
                                 tkl_board_tip.thumbnail,
                                 tkl_board_tip.writer,
                                 tkl_board_tip.like_count,
                                 tkl_board_tip.dislike_count,
                                 tkl_board_tip.view_count,
                                 tkl_board_tip.type,
                                 tkl_board_tip.create_time,
                                 tkl_board_tip.update_time,
                                 tkl_board_type.name_kr
                          FROM tkl_board_tip
                                   left join tkl_board_type on tkl_board_tip.type = tkl_board_type.value) AS combined
                             left join tkl_user on combined.writer = tkl_user.email
                    ORDER BY create_time DESC
                    LIMIT :limit OFFSET :offset
                """

    @staticmethod
    def get_post_max_cnt_query():
        """
        커뮤니티 전체 데이터 수 조회 쿼리
        """

        return """
                    SELECT COUNT(*)
                    FROM (
                        SELECT id FROM tkl_board_forum
                        UNION ALL
                        SELECT id FROM tkl_board_arena
                        UNION ALL
                        SELECT id FROM tkl_board_pve
                        UNION ALL
                        SELECT id FROM tkl_board_pvp
                        UNION ALL
                        SELECT id FROM tkl_board_question
                        UNION ALL
                        SELECT id FROM tkl_board_tip
                    ) AS combined
                """

    @staticmethod
    def get_issue_max_cnt_query():
        """
        issue 전체 개수
        """

        return """
        SELECT COUNT(*) from tkl_board_issue
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
    def get_issue_post_query():
        """
        커뮤니티 이슈글 전체 조회 쿼리
        """

        return """
                        SELECT combined.id,
                               combined.title,
                               combined.contents,
                               combined.thumbnail,
                               combined.writer,
                               combined.like_count,
                               combined.dislike_count,
                               combined.view_count,
                               combined.type,
                               combined.create_time,
                               combined.update_time,
                               combined.name_kr as type_kr,
                               tkl_user.icon,
                               tkl_user.nick_name
                        from (select tkl_board_issue.board_id as id,
                                     tkl_board_forum.type,
                                     tkl_board_forum.create_time,
                                     tkl_board_forum.title,
                                     tkl_board_forum.contents,
                                     tkl_board_forum.thumbnail,
                                     tkl_board_forum.writer,
                                     tkl_board_forum.like_count,
                                     tkl_board_forum.dislike_count,
                                     tkl_board_forum.view_count,
                                     tkl_board_forum.update_time,
                                     tkl_board_type.name_kr
                              from tkl_board_issue
                                       join tkl_board_forum on tkl_board_issue.board_id = tkl_board_forum.id
                                       left join tkl_board_type on tkl_board_forum.type = tkl_board_type.value
                              union all
                              select tkl_board_issue.board_id,
                                     tkl_board_question.type,
                                     tkl_board_issue.create_time,
                                     tkl_board_question.title,
                                     tkl_board_question.contents,
                                     tkl_board_question.thumbnail,
                                     tkl_board_question.writer,
                                     tkl_board_question.like_count,
                                     tkl_board_question.dislike_count,
                                     tkl_board_question.view_count,
                                     tkl_board_question.update_time,
                                     tkl_board_type.name_kr
                              from tkl_board_issue
                                       join tkl_board_question on tkl_board_issue.board_id = tkl_board_question.id
                                       left join tkl_board_type on tkl_board_question.type = tkl_board_type.value
                              union all
                              select tkl_board_issue.board_id as id,
                                     tkl_board_arena.type,
                                     tkl_board_issue.create_time,
                                     tkl_board_arena.title,
                                     tkl_board_arena.contents,
                                     tkl_board_arena.thumbnail,
                                     tkl_board_arena.writer,
                                     tkl_board_arena.like_count,
                                     tkl_board_arena.dislike_count,
                                     tkl_board_arena.view_count,
                                     tkl_board_arena.update_time,
                                     tkl_board_type.name_kr
                              from tkl_board_issue
                                       join tkl_board_arena on tkl_board_issue.board_id = tkl_board_arena.id
                                       left join tkl_board_type on tkl_board_arena.type = tkl_board_type.value
                              union all
                              select tkl_board_issue.board_id as id,
                                     tkl_board_tip.type,
                                     tkl_board_issue.create_time,
                                     tkl_board_tip.title,
                                     tkl_board_tip.contents,
                                     tkl_board_tip.thumbnail,
                                     tkl_board_tip.writer,
                                     tkl_board_tip.like_count,
                                     tkl_board_tip.dislike_count,
                                     tkl_board_tip.view_count,
                                     tkl_board_tip.update_time,
                                     tkl_board_type.name_kr
                              from tkl_board_issue
                                       join tkl_board_tip on tkl_board_issue.board_id = tkl_board_tip.id
                                       left join tkl_board_type on tkl_board_tip.type = tkl_board_type.value
                              union all
                              select tkl_board_issue.board_id as id,
                                     tkl_board_pvp.type,
                                     tkl_board_issue.create_time,
                                     tkl_board_pvp.title,
                                     tkl_board_pvp.contents,
                                     tkl_board_pvp.thumbnail,
                                     tkl_board_pvp.writer,
                                     tkl_board_pvp.like_count,
                                     tkl_board_pvp.dislike_count,
                                     tkl_board_pvp.view_count,
                                     tkl_board_pvp.update_time,
                                     tkl_board_type.name_kr
                              from tkl_board_issue
                                       join tkl_board_pvp on tkl_board_issue.board_id = tkl_board_pvp.id
                                       left join tkl_board_type on tkl_board_pvp.type = tkl_board_type.value
                              union all
                              select tkl_board_issue.board_id as id,
                                     tkl_board_pve.type,
                                     tkl_board_issue.create_time,
                                     tkl_board_pve.title,
                                     tkl_board_pve.contents,
                                     tkl_board_pve.thumbnail,
                                     tkl_board_pve.writer,
                                     tkl_board_pve.like_count,
                                     tkl_board_pve.dislike_count,
                                     tkl_board_pve.view_count,
                                     tkl_board_pve.update_time,
                                     tkl_board_type.name_kr
                              from tkl_board_issue
                                       join tkl_board_pve on tkl_board_issue.board_id = tkl_board_pve.id
                                       left join tkl_board_type on tkl_board_pve.type = tkl_board_type.value) as combined
                                 left join tkl_user on combined.writer = tkl_user.email
                        ORDER BY create_time DESC
                        LIMIT :limit OFFSET :offset
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
