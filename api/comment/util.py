class CommentUtilV3:
    @staticmethod
    def insert_parent_comment():
        return """
            INSERT INTO community_comments (id, parent_id, post_id, contents, path, user_email)
            VALUES (
                :comment_id,
                NULL,
                :post_id,
                :contents,
                CAST(:comment_id AS ltree),
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
                :comment_id,
                :parent_comment_id,
                :post_id,
                :contents,
                parent.path || CAST(:comment_id AS ltree),
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
        return """
            WITH RECURSIVE tree AS (
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
                    t.id,
                    t.parent_id,
                    t.post_id,
                    t.user_email,
                    CASE
                        WHEN ub.id IS NOT NULL THEN 'blocked'
                        ELSE t.contents
                    END AS contents,
                    t.delete_by_admin,
                    t.delete_by_user,
                    t.create_time,
                    t.update_time,
                    t.depth,
                    t.sort_path,
                    COALESCE(SUM(CASE WHEN r.reaction_type = 1 THEN 1 ELSE 0 END), 0) AS like_count,
                    COALESCE(SUM(CASE WHEN r.reaction_type = 0 THEN 1 ELSE 0 END), 0) AS dislike_count,
                    COALESCE(ui.nickname, t.user_email) AS nickname,
                    COALESCE(pui.nickname, pc.user_email) AS parent_nickname,
                    COALESCE(ccr.reaction_type, -1) AS is_like
                FROM tree t
                LEFT JOIN community_comments_reactions r
                       ON r.comment_id = t.id
                LEFT JOIN community_comments_reactions ccr
                       ON t.id = ccr.comment_id AND ccr.email = :user_email
                LEFT JOIN user_info ui
                       ON t.user_email = ui.email
                LEFT JOIN community_comments pc
                       ON t.parent_id = pc.id
                LEFT JOIN user_info pui
                       ON pc.user_email = pui.email
                LEFT JOIN user_block ub
                       ON ub.request_email = :user_email
                      AND ub.target_email = t.user_email
                GROUP BY
                    t.id, t.parent_id, t.post_id, t.user_email, t.contents,
                    t.delete_by_admin, t.delete_by_user, t.create_time, t.update_time,
                    t.depth, t.sort_path, COALESCE(ui.nickname, t.user_email),
                    COALESCE(pui.nickname, pc.user_email), ccr.reaction_type, ub.id
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
                COALESCE(ui.nickname, c.user_email) AS nickname,
                COALESCE(pui.nickname, pc.user_email) AS parent_nickname,
                c.contents,
                c.delete_by_user,
                c.delete_by_admin,
                c.create_time,
                c.update_time,
                nlevel(c.path) AS depth,
                COALESCE(SUM(CASE WHEN r.reaction_type = 1 THEN 1 ELSE 0 END), 0) AS like_count,
                COALESCE(SUM(CASE WHEN r.reaction_type = 0 THEN 1 ELSE 0 END), 0) AS dislike_count,
                COALESCE(SUM(CASE WHEN r.reaction_type = 1 THEN 1 ELSE 0 END), 0)
                  - COALESCE(SUM(CASE WHEN r.reaction_type = 0 THEN 1 ELSE 0 END), 0) AS score
            FROM community_comments c
            LEFT JOIN community_comments_reactions r
                   ON r.comment_id = c.id
            LEFT JOIN user_info ui
                 ON c.user_email = ui.email
            LEFT JOIN community_comments pc
                   ON c.parent_id = pc.id
            LEFT JOIN user_info pui
                   ON pc.user_email = pui.email
            WHERE c.post_id = :post_id
            GROUP BY
                c.id, c.parent_id, c.post_id, c.path, c.user_email,
                COALESCE(ui.nickname, c.user_email), COALESCE(pui.nickname, pc.user_email),
                c.contents, c.delete_by_user, c.delete_by_admin, c.create_time, c.update_time
            HAVING
                (COALESCE(SUM(CASE WHEN r.reaction_type = 1 THEN 1 ELSE 0 END), 0)
                 + COALESCE(SUM(CASE WHEN r.reaction_type = 0 THEN 1 ELSE 0 END), 0)) >= 5
            ORDER BY
                score DESC,
                like_count DESC,
                c.create_time ASC
            LIMIT 3
        """
