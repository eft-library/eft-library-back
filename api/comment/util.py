class CommentUtil:
    @staticmethod
    def get_comment_query():
        """
        특정 게시글 댓글 전체 조회 쿼리
        """

        return """
                WITH RECURSIVE comment_tree AS (
                SELECT
                    ID,
                    BOARD_ID,
                    USER_EMAIL,
                    BOARD_TYPE,
                    PARENT_ID,
                    CONTENTS,
                    DEPTH,
                    CREATE_TIME,
                    UPDATE_TIME,
                    is_delete_by_admin,
                    is_delete_by_user,
                    like_count,
                    dislike_count,
                    ID AS root_id,
                    ARRAY[ID] AS path,
                    CREATE_TIME AS root_create_time
                FROM TKL_COMMENTS
                WHERE DEPTH = 1 and board_id = :board_id
                UNION ALL
                SELECT
                    c.ID,
                    c.BOARD_ID,
                    c.USER_EMAIL,
                    c.BOARD_TYPE,
                    c.PARENT_ID,
                    c.CONTENTS,
                    c.DEPTH,
                    c.CREATE_TIME,
                    c.UPDATE_TIME,
                    c.is_delete_by_admin,
                    c.is_delete_by_user,
                    c.like_count,
                    c.dislike_count,
                    ct.root_id,
                    ct.path || c.ID,
                    ct.root_create_time
                FROM TKL_COMMENTS c
                INNER JOIN comment_tree ct ON c.PARENT_ID = ct.ID
                WHERE c.board_id = :board_id
            )
            SELECT *
            FROM comment_tree
            ORDER BY root_create_time, path
            LIMIT :limit OFFSET :offset; 
            """
