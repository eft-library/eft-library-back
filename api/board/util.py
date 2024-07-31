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
                           tkl_user.image
                    FROM (SELECT id,
                                 title,
                                 contents,
                                 thumbnail,
                                 writer,
                                 like_count,
                                 dislike_count,
                                 view_count,
                                 type,
                                 create_time,
                                 update_time
                          FROM tkl_board_forum
                          UNION ALL
                          SELECT id,
                                 title,
                                 contents,
                                 thumbnail,
                                 writer,
                                 like_count,
                                 dislike_count,
                                 view_count,
                                 type,
                                 create_time,
                                 update_time
                          FROM tkl_board_arena
                          UNION ALL
                          SELECT id,
                                 title,
                                 contents,
                                 thumbnail,
                                 writer,
                                 like_count,
                                 dislike_count,
                                 view_count,
                                 type,
                                 create_time,
                                 update_time
                          FROM tkl_board_pve
                          UNION ALL
                          SELECT id,
                                 title,
                                 contents,
                                 thumbnail,
                                 writer,
                                 like_count,
                                 dislike_count,
                                 view_count,
                                 type,
                                 create_time,
                                 update_time
                          FROM tkl_board_pvp
                          UNION ALL
                          SELECT id,
                                 title,
                                 contents,
                                 thumbnail,
                                 writer,
                                 like_count,
                                 dislike_count,
                                 view_count,
                                 type,
                                 create_time,
                                 update_time
                          FROM tkl_board_question
                          UNION ALL
                          SELECT id,
                                 title,
                                 contents,
                                 thumbnail,
                                 writer,
                                 like_count,
                                 dislike_count,
                                 view_count,
                                 type,
                                 create_time,
                                 update_time
                          FROM tkl_board_tip) AS combined
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
