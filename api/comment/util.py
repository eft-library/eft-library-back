class CommentUtil:

    @staticmethod
    def insert_parent_comment():
        return """
            INSERT INTO community_comments (id, parent_id, post_id, contents, path, user_email)
            VALUES (
                :comment_id,        -- id (nanoid)
                NULL,            -- parent_id 없음
                :post_id,               -- post_id
                :contents,
                :comment_id::ltree,  -- path = id
                :user_email
            )        
        """

    @staticmethod
    def insert_child_comment():
        return """
            WITH parent AS (
                SELECT path
                FROM community_comments
                WHERE id = :parent_comment_id
            )
            INSERT INTO community_comments (id, parent_id, post_id, contents, path, user_email)
            SELECT
                :comment_id,       -- id (nanoid)
                :parent_comment_id,       -- parent_id
                :post_id,               -- post_id
                :contents,
                parent.path || :comment_id::ltree,  -- path = 부모 path + 새 id
                :user_email
            FROM parent  
        """

    @staticmethod
    def update_comment():
        return """
        """

    @staticmethod
    def delete_comment_by_user():
        return """
        """

    @staticmethod
    def delete_comment_by_admin():
        return """
        """

    @staticmethod
    def get_comment():
        """
        rn_start = (page - 1) * limit + 1
        rn_end   = page * limit
        """
        return """
            WITH RECURSIVE tree AS (
                -- 최상위 댓글
                SELECT
                    cc.id,
                    cc.parent_id,
                    cc.post_id,
                    cc.path,
                    cc.contents,
                    cc.delete_by_admin,
                    cc.delete_by_user,
                    cc.create_time,
                    cc.update_time,
                    COALESCE(SUM(CASE WHEN ccr.reaction_type = 1 THEN 1 ELSE 0 END), 0) AS like_count,
                    COALESCE(SUM(CASE WHEN ccr.reaction_type = 0 THEN 1 ELSE 0 END), 0) AS dislike_count,
                    nlevel(cc.path) AS depth
                FROM community_comments cc
                         LEFT JOIN community_comments_reactions ccr ON ccr.comment_id = cc.id
                WHERE cc.post_id = :post_id
                  AND nlevel(cc.path) = :post_id
                GROUP BY cc.id
            
                UNION ALL
            
                -- 대댓글
                SELECT
                    c.id,
                    c.parent_id,
                    c.post_id,
                    c.path,
                    c.contents,
                    c.delete_by_admin,
                    c.delete_by_user,
                    c.create_time,
                    c.update_time,
                    COALESCE(SUM(CASE WHEN ccr.reaction_type = 1 THEN 1 ELSE 0 END), 0) AS like_count,
                    COALESCE(SUM(CASE WHEN ccr.reaction_type = 0 THEN 1 ELSE 0 END), 0) AS dislike_count,
                    nlevel(c.path) AS depth
                FROM community_comments c
                         JOIN tree t ON c.parent_id = t.id
                         LEFT JOIN community_comments_reactions ccr ON ccr.comment_id = c.id
                WHERE c.post_id = :post_id
                GROUP BY c.id
            )
            SELECT *
            FROM (
                     SELECT *, row_number() OVER (ORDER BY path, create_time) AS rn
                     FROM tree
                 ) t
            WHERE rn BETWEEN :rn_start AND :rn_end
            ORDER BY pat
        """

    @staticmethod
    def get_comment_total_count():
        return """
            select count(*) from community_comments where post_id = :post_id
        """

    @staticmethod
    def my_page_comment():
        return """
        """
