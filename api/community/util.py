class CommunityUtil:

    @staticmethod
    def get_posts_with_post_id():
        return """
            select cp.id::text AS id,
                   cp.slug,
                   cp.user_email,
                   ui.nickname,
                   cp.category,
                   cp.title,
                   cp.contents,
                   cp.thumbnail,
                   cp.delete_by_user,
                   cp.delete_by_admin,
                   cp.create_time,
                   cp.update_time,
                   cpv.view_count                           as view_count,
                   coalesce((SELECT COUNT(*)
                             FROM community_comments cc
                             WHERE cc.post_id = cp.id), 0) AS comment_count,
                   coalesce((SELECT SUM(CASE
                                            WHEN cpr.reaction_type = 1 THEN 1
                                            WHEN cpr.reaction_type = 0 THEN -1
                                            ELSE 0 END)
                             FROM community_posts_reactions cpr
                             WHERE cpr.post_id = cp.id), 0) as reaction_score
            from community_posts cp
                     LEFT JOIN user_info ui on cp.user_email = ui.email
                     LEFT JOIN community_posts_views cpv on cp.id = cpv.post_id
            where cp.category = (select category from community_posts where id = :post_id)
              and cp.delete_by_user = false
              and cp.delete_by_admin = false
            order by cp.create_time desc
            limit :limit
            offset :offset
        """

    @staticmethod
    def get_posts_with_category():
        return """
            select cp.id::text AS id,
                   cp.slug,
                   cp.user_email,
                   ui.nickname,
                   cp.category,
                   cp.title,
                   cp.contents,
                   cp.thumbnail,
                   cp.delete_by_user,
                   cp.delete_by_admin,
                   cp.create_time,
                   cp.update_time,
                   cpv.view_count                           as view_count,
                   coalesce((SELECT COUNT(*)
                             FROM community_comments cc
                             WHERE cc.post_id = cp.id), 0) AS comment_count,
                   coalesce((SELECT SUM(CASE
                                            WHEN cpr.reaction_type = 1 THEN 1
                                            WHEN cpr.reaction_type = 0 THEN -1
                                            ELSE 0 END)
                             FROM community_posts_reactions cpr
                             WHERE cpr.post_id = cp.id), 0) as reaction_score
            from community_posts cp
                     LEFT JOIN user_info ui on cp.user_email = ui.email
                     LEFT JOIN community_posts_views cpv on cp.id = cpv.post_id
            where cp.category = :category
              and cp.delete_by_user = false
              and cp.delete_by_admin = false
            order by cp.create_time desc
            limit :limit
            offset :offset
        """

    @staticmethod
    def get_post_category_count():
        return """
            select count(*)
            from community_posts
            where category = :category
              and delete_by_user = false
              and delete_by_admin = false
        """

    @staticmethod
    def get_post_category_count_with_post_id():
        return """
            select count(*)
            from community_posts
            where category = (select category from community_posts where id = :post_id)
              and delete_by_user = false
              and delete_by_admin = false
        """

    @staticmethod
    def get_post_issue_count():
        return """
            select count(*)
            from community_posts_hot_issue        
        """

    @staticmethod
    def get_posts_with_issue():
        return """
            SELECT
                cphi.post_id::text AS id,
                cphi.issue_time,
                cp.slug,
                cp.user_email,
                ui.nickname,
                cp.category,
                cp.title,
                cp.contents,
                cp.thumbnail,
                cp.delete_by_user,
                cp.delete_by_admin,
                cp.create_time,
                cp.update_time,
                cpv.view_count AS view_count,
                coalesce((SELECT COUNT(*)
                          FROM community_comments cc
                          WHERE cc.post_id = cp.id), 0) AS comment_count,
                coalesce((SELECT SUM(CASE
                                         WHEN cpr.reaction_type = 1 THEN 1
                                         WHEN cpr.reaction_type = 0 THEN -1
                                         ELSE 0 END) AS reaction_score
                          FROM community_posts_reactions cpr
                          WHERE cpr.post_id = cp.id), 0) AS reaction_score
            FROM community_posts_hot_issue cphi
            LEFT JOIN community_posts cp ON cphi.post_id = cp.id
            LEFT JOIN user_info ui ON cp.user_email = ui.email
            LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
            where cp.delete_by_user = false and cp.delete_by_admin = false
            ORDER BY cphi.issue_time DESC
            LIMIT :limit 
            OFFSET :offset
        """

    @staticmethod
    def get_post_detail():
        return """
            SELECT
                cp.id::text AS id,
                cp.slug,
                cp.user_email,
                ui.nickname,
                cp.category,
                cp.title,
                cp.contents,
                cp.thumbnail,
                cp.create_time,
                cp.update_time,
                cpv.view_count,
                coalesce((SELECT COUNT(*)
                          FROM community_comments cc
                          WHERE cc.post_id = cp.id), 0) AS comment_count,
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

    @staticmethod
    def get_detail_author_meta_data():
        return """
        select cp.user_email,
               ui.nickname,
               count(distinct cp2.id) as posts_count,
               count(cpr.post_id) filter (where cpr.reaction_type = 1) as like_count,
               case when uf.follower_email is not null then 1 else 0 end as is_follow
        from community_posts cp
                 join user_info ui on cp.user_email = ui.email
                 left join community_posts cp2 on cp2.user_email = cp.user_email
                 left join community_posts_reactions cpr on cp2.id = cpr.post_id
                 left join user_follows uf
                           on uf.following_email = :user_email
                               and uf.follower_email = cp.user_email
        where cp.id = :post_id
        and cp.delete_by_user = false and cp.delete_by_admin = false
        group by cp.user_email, ui.nickname, uf.follower_email
        """

    @staticmethod
    def check_follow():
        return """
        SELECT
            CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END AS is_follow
        FROM user_follows
        WHERE following_email = :user_email
          AND follower_email = :author_email;
        """

    @staticmethod
    def get_current_post_category_page_num():
        return """
            WITH post_category AS (
                SELECT category
                FROM community_posts
                WHERE id = :post_id
            ),
            ordered_posts AS (
                SELECT id,
                       ROW_NUMBER() OVER (ORDER BY create_time DESC) AS rn
                FROM community_posts cp
                WHERE cp.category = (SELECT category FROM post_category)
                  AND delete_by_user = false
                  AND delete_by_admin = false
            )
            SELECT rn
            FROM ordered_posts
            WHERE id = :post_id  
        """

    @staticmethod
    def get_current_post_issue_page_num():
        return """
            WITH ordered_posts AS (
                SELECT post_id as id,
                       ROW_NUMBER() OVER (ORDER BY issue_time DESC) AS rn
                FROM community_posts_hot_issue
            )
            SELECT rn
            FROM ordered_posts
            WHERE id = :post_id     
        """
