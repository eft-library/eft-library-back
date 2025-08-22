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
                CAST(:comment_id AS ltree),  -- path = id
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
                parent.path || CAST(:comment_id AS ltree),  -- path = 부모 path + 새 id
                :user_email
            FROM parent  
        """

    @staticmethod
    def update_comment():
        return """
            update community_comments
            set contents = :contents,
                update_time = :update_time
            where id = :comment_id
        """

    @staticmethod
    def delete_comment_by_user():
        return """
            update community_comments
            set delete_by_user = true,
                update_time = :update_time
            where id = :comment_id
        """

    @staticmethod
    def delete_comment_by_admin():
        return """
            update community_comments
            set delete_by_admin = true,
                update_time = :update_time
            where id = :comment_id
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
                    cc.post_id::text AS post_id,
                    cc.user_email,
                    cc.contents,
                    cc.delete_by_admin,
                    cc.delete_by_user,
                    cc.create_time,
                    cc.update_time,
                    1 AS depth,
                    ARRAY[EXTRACT(EPOCH FROM cc.create_time)::BIGINT] AS sort_path
                FROM community_comments cc
                WHERE cc.post_id = :post_id
                  AND cc.parent_id IS NULL
            
                UNION ALL
            
                -- 대댓글
                SELECT
                    c.id,
                    c.parent_id,
                    c.post_id::text AS post_id,
                    c.user_email,
                    c.contents,
                    c.delete_by_admin,
                    c.delete_by_user,
                    c.create_time,
                    c.update_time,
                    t.depth + 1 AS depth,
                    t.sort_path || EXTRACT(EPOCH FROM c.create_time)::BIGINT
                FROM community_comments c
                JOIN tree t ON c.parent_id = t.id
                WHERE c.post_id = :post_id
            ),
            aggregated AS (
                SELECT
                    t.*,
                    COALESCE(SUM(CASE WHEN r.reaction_type = 1 THEN 1 ELSE 0 END), 0) AS like_count,
                    COALESCE(SUM(CASE WHEN r.reaction_type = 0 THEN 1 ELSE 0 END), 0) AS dislike_count,
                    ui.nickname,
                    COALESCE(ccr.reaction_type, -1) AS is_like
                FROM tree t
                LEFT JOIN community_comments_reactions r 
                       ON r.comment_id = t.id
                LEFT JOIN community_comments_reactions ccr 
                       ON t.id = ccr.comment_id AND ccr.user_email = :user_email
                JOIN user_info ui 
                       ON t.user_email = ui.email
                GROUP BY t.id, t.parent_id, t.post_id, t.user_email, t.contents,
                         t.delete_by_admin, t.delete_by_user, t.create_time, t.update_time, t.depth, t.sort_path, ui.nickname, ccr.reaction_type
            ),
            ranked AS (
                SELECT a.*,
                       ROW_NUMBER() OVER (ORDER BY a.sort_path) AS rn
                FROM aggregated a
            )
            SELECT *
            FROM ranked
            WHERE rn BETWEEN :rn_start AND :rn_end
            ORDER BY sort_path
        """

    @staticmethod
    def get_comment_total_count():
        return """
            select count(*) from community_comments where post_id = :post_id
        """

    @staticmethod
    def get_issue_comment_page():
        return """
            WITH RECURSIVE tree AS (
                SELECT
                    cc.id,
                    cc.parent_id,
                    cc.post_id::text AS post_id,
                    cc.create_time,
                    ARRAY[EXTRACT(EPOCH FROM cc.create_time)::BIGINT] AS sort_path
                FROM community_comments cc
                WHERE cc.post_id = :post_id AND cc.parent_id IS NULL
            
                UNION ALL
            
                SELECT
                    c.id,
                    c.parent_id,
                    c.post_id::text AS post_id,
                    c.create_time,
                    t.sort_path || EXTRACT(EPOCH FROM c.create_time)::BIGINT
                FROM community_comments c
                JOIN tree t ON c.parent_id = t.id
                WHERE c.post_id = :post_id
            ),
            ordered AS (
                SELECT
                    t.id,
                    ROW_NUMBER() OVER (ORDER BY t.sort_path) AS row_num
                FROM tree t
            )
            SELECT CEIL(row_num / CAST(:limit AS numeric)) AS page_num
            FROM ordered
            WHERE id = :comment_id       
        """

    @staticmethod
    def get_issue_comment():
        return """
            SELECT 
                c.id,
                c.parent_id,
                c.post_id::text AS post_id,
                c.path,
                c.user_email,
                c.contents,
                c.delete_by_user,
                c.delete_by_admin,
                c.create_time,
                c.update_time,
                nlevel(c.path) AS depth,
                -- 좋아요 / 싫어요 개수
                COALESCE(SUM(CASE WHEN r.reaction_type = 1 THEN 1 ELSE 0 END), 0) AS like_count,
                COALESCE(SUM(CASE WHEN r.reaction_type = 0 THEN 1 ELSE 0 END), 0) AS dislike_count,
                -- 점수 (좋아요 - 싫어요)
                COALESCE(SUM(CASE WHEN r.reaction_type = 1 THEN 1 ELSE 0 END), 0)
                  - COALESCE(SUM(CASE WHEN r.reaction_type = 0 THEN 1 ELSE 0 END), 0) AS score
            FROM community_comments c
            LEFT JOIN community_comments_reactions r 
                   ON r.comment_id = c.id
            WHERE c.post_id = :post_id
            GROUP BY c.id, c.parent_id, c.post_id, c.path, c.user_email, 
                     c.contents, c.delete_by_user, c.delete_by_admin, c.create_time, c.update_time
            ORDER BY score DESC, like_count DESC, c.create_time ASC
            LIMIT 3
        """

    @staticmethod
    def my_page_comment():
        return """
        """
