class CommunityUtil:

    @staticmethod
    def get_post_detail():
        return """
            SELECT
                cp.id::text AS id,
                cp.slug,
                cp.user_email,
                ui.nickname,
                cp.category,
                (select CASE WHEN uf.following_email = :user_email THEN 1 ELSE 0 END from user_follows uf) as is_follow,
                cp.title,
                cp.contents,
                cp.thumbnail,
                cp.create_time,
                cp.update_time,
                cpv.view_count,
                -- 작성자 팔로워 수
                (SELECT COUNT(*)
                 FROM user_follows uf
                 WHERE uf.following_email = cp.user_email) AS follower_count,
                -- 작성자 게시글 전체 수
                (SELECT COUNT(*)
                 FROM community_posts cp2
                 WHERE cp2.user_email = cp.user_email) AS total_post_count
            FROM community_posts cp
            LEFT JOIN user_info ui ON cp.user_email = ui.email
            LEFT JOIN community_posts_views cpv on cp.id = cpv.post_id
            WHERE cp.id = :post_id
        """

    @staticmethod
    def get_post_detail_meta_data():
        return """
            SELECT
                cp.id::text AS id,
                COALESCE(cpr.reaction_type, -1) AS is_like,
                CASE
                    WHEN cpb.post_id IS NOT NULL THEN 1
                    ELSE 0
                END AS is_bookmarked,
                (
                    SELECT 
                        COALESCE(SUM(CASE WHEN cpr2.reaction_type = 1 THEN 1 ELSE 0 END), 0)
                        - COALESCE(SUM(CASE WHEN cpr2.reaction_type = 0 THEN 1 ELSE 0 END), 0)
                    FROM community_posts_reactions cpr2
                    WHERE cpr2.post_id = cp.id
                ) AS like_count
            FROM community_posts cp
            LEFT JOIN community_posts_bookmark cpb
                   ON cp.id = cpb.post_id AND cpb.user_email = :user_email
            LEFT JOIN community_posts_reactions cpr
                   ON cp.id = cpr.post_id AND cpr.user_email = :user_email
            WHERE cp.id = :post_id
        """
