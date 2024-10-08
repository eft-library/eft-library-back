class CommentUtil:
    @staticmethod
    def get_comment_query():
        """
        특정 게시글 댓글 전체 조회 쿼리
        """

        return """
                WITH RECURSIVE comment_tree AS (
                SELECT
                    tkl_comments.ID,
                    tkl_comments.BOARD_ID,
                    tkl_comments.USER_EMAIL,
                    tkl_comments.BOARD_TYPE,
                    tkl_comments.PARENT_ID,
                    CASE
                        WHEN tkl_comments.is_delete_by_admin THEN '<p>해당 댓글은 관리 규정에 따라 삭제되었습니다.</p>'
                        WHEN tkl_comments.is_delete_by_user THEN '<p>해당 댓글은 작성자에 의해 삭제되었습니다.</p>'
                        ELSE tkl_comments.CONTENTS
                    END AS CONTENTS,
                    tkl_comments.DEPTH,
                    tkl_comments.CREATE_TIME,
                    tkl_comments.UPDATE_TIME,
                    tkl_comments.is_delete_by_admin,
                    tkl_comments.is_delete_by_user,
                    tkl_comments.like_count,
                    tkl_comments.dislike_count,
                    tkl_comments.ID AS root_id,
                    ARRAY[tkl_comments.ID] AS path,
                    tkl_comments.CREATE_TIME AS root_create_time,
                    a.nick_name,
                    a.icon,
                    b.nick_name as parent_nick_name
                FROM TKL_COMMENTS
                LEFT JOIN TKL_USER a ON tkl_comments.user_email = a.email
                LEFT JOIN TKL_USER b ON tkl_comments.parent_user_email = b.email
                WHERE DEPTH = 1 AND board_id = :board_id
                UNION ALL
                SELECT
                    c.ID,
                    c.BOARD_ID,
                    c.USER_EMAIL,
                    c.BOARD_TYPE,
                    c.PARENT_ID,
                    CASE
                        WHEN c.is_delete_by_admin THEN '<p>해당 댓글은 관리 규정에 따라 삭제되었습니다.</p>'
                        WHEN c.is_delete_by_user THEN '<p>해당 댓글은 작성자에 의해 삭제되었습니다.</p>'
                        ELSE c.CONTENTS
                    END AS CONTENTS,
                    c.DEPTH,
                    c.CREATE_TIME,
                    c.UPDATE_TIME,
                    c.is_delete_by_admin,
                    c.is_delete_by_user,
                    c.like_count,
                    c.dislike_count,
                    ct.root_id,
                    ct.path || c.ID,
                    ct.root_create_time,
                    a.nick_name,
                    a.icon,
                    b.nick_name as parent_nick_name
                FROM TKL_COMMENTS c
                INNER JOIN comment_tree ct ON c.PARENT_ID = ct.ID
                INNER JOIN TKL_USER a ON c.user_email = a.email
                INNER JOIN TKL_USER b ON c.parent_user_email = b.email
                WHERE c.board_id = :board_id
            )
            SELECT
                ct.*,
                CASE
                    WHEN tcl.comment_id IS NOT NULL THEN true
                    ELSE false
                END AS is_liked_by_user,
                CASE
                    WHEN tcdl.comment_id IS NOT NULL THEN true
                    ELSE false
                END AS is_disliked_by_user,
                b.ban_reason,
                b.ban_start_time,
                b.ban_end_time
            FROM
                comment_tree ct
            LEFT JOIN
                tkl_comment_like tcl
                ON ct.id = tcl.comment_id AND tcl.user_email = :user_email
            LEFT JOIN
                tkl_comment_dislike tcdl
                ON ct.id = tcdl.comment_id AND tcdl.user_email = :user_email
            LEFT JOIN
                tkl_user_ban b
                ON ct.user_email = b.user_email
            {where_clause}
            """

    @staticmethod
    def get_issue_comment_rank_query():
        return """
                WITH OrderedComments AS (SELECT id,
                                                ROW_NUMBER() OVER (ORDER BY create_time) AS row_num
                                         FROM tkl_comments
                                         WHERE board_id = :board_id)
                SELECT row_num AS comment_offset
                FROM OrderedComments
                WHERE id = :comment_id
                """

    @staticmethod
    def comment_where_clause(is_issue: bool):
        if is_issue:
            return """
                WHERE ct.like_count > 2 AND ct.is_delete_by_admin = false AND ct.is_delete_by_user = false
                ORDER BY
                    ct.like_count desc, ct.path
                LIMIT 3;
                """
        else:
            return """
                ORDER BY 
                    ct.create_time, ct.path
                LIMIT :limit OFFSET :offset; 
                """
