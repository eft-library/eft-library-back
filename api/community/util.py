class CommunityUtil:
    @staticmethod
    def _get_post_page(
        page_sql: str, order_by: str, preview: bool, *, include_issue_time: bool = False
    ) -> str:
        contents = CommunityUtil.post_preview_sql("cp.contents") if preview else "cp.contents"
        thumbnail = CommunityUtil.thumbnail_url_sql() if preview else "cp.thumbnail"
        issue_time = "page.issue_time," if include_issue_time else ""
        return f"""
            SELECT cp.id::text AS id,
                   {issue_time}
                   cp.slug,
                   cp.user_email,
                   ui.nickname,
                   cp.category,
                   cp.title,
                   {contents} AS contents,
                   {thumbnail} AS thumbnail,
                   cp.delete_by_user,
                   cp.delete_by_admin,
                   cp.create_time,
                   cp.update_time,
                   cpv.view_count,
                   (SELECT COUNT(*) FROM community_comments cc WHERE cc.post_id = cp.id) AS comment_count,
                   COALESCE((SELECT SUM(CASE
                                            WHEN cpr.reaction_type = 1 THEN 1
                                            WHEN cpr.reaction_type = 0 THEN -1
                                            ELSE 0 END)
                             FROM community_posts_reactions cpr
                             WHERE cpr.post_id = cp.id), 0) AS reaction_score
            FROM ({page_sql}) page
            JOIN community_posts cp ON cp.id = page.id
            LEFT JOIN user_info ui ON ui.email = cp.user_email
            LEFT JOIN community_posts_views cpv ON cpv.post_id = cp.id
            ORDER BY {order_by}
        """

    @staticmethod
    def post_preview_sql(column: str) -> str:
        return f"""
            left(trim(regexp_replace(
                replace(regexp_replace(left({column}, 16384), '<[^>]*(>|$)', ' ', 'g'), '&nbsp;', ' '),
                '[[:space:]]+', ' ', 'g'
            )), 140)
        """

    @staticmethod
    def thumbnail_url_sql() -> str:
        return """
            CASE WHEN octet_length(cp.thumbnail) <= 2048 THEN
                CASE WHEN cp.thumbnail ~* '^https?://[^/[:space:]?#]+[^[:space:]]*$'
                     THEN cp.thumbnail END
            END
        """

    @staticmethod
    def _get_recent_posts(
        extra_filter: str = "", preview: bool = False, *, filter_blocked: bool = True
    ) -> str:
        block_filter = """
            AND NOT EXISTS (
                SELECT 1 FROM user_block ub
                WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email
            )
        """ if filter_blocked else ""
        return CommunityUtil._get_post_page(
            f"""
            SELECT cp.id, cp.create_time
            FROM community_posts cp
            WHERE cp.delete_by_user = false AND cp.delete_by_admin = false
            {extra_filter}
            {block_filter}
            ORDER BY cp.create_time DESC
            LIMIT :limit OFFSET :offset
            """,
            "page.create_time DESC",
            preview,
        )

    @staticmethod
    def get_posts_with_post_id():
        return CommunityUtil._get_recent_posts(
            "AND cp.category = (SELECT category FROM community_posts WHERE id = :post_id)",
            filter_blocked=False,
        )

    @staticmethod
    def get_posts_with_category(preview: bool = False):
        return CommunityUtil._get_recent_posts("AND cp.category = :category", preview)

    @staticmethod
    def get_posts_with_all(preview: bool = False):
        return CommunityUtil._get_recent_posts(preview=preview)

    @staticmethod
    def get_post_category_count():
        return """
            select count(*)
            from community_posts cp
            where category = :category
              and delete_by_user = false
              and delete_by_admin = false
              AND NOT EXISTS (
                  SELECT 1
                  FROM user_block ub
                  WHERE ub.request_email = :user_email
                    AND ub.target_email = cp.user_email
              )
        """

    @staticmethod
    def get_post_all_count():
        return """
            select count(*)
            from community_posts cp
            where delete_by_user = false
              and delete_by_admin = false
              AND NOT EXISTS (
                  SELECT 1
                  FROM user_block ub
                  WHERE ub.request_email = :user_email
                    AND ub.target_email = cp.user_email
              )
        """

    @staticmethod
    def get_post_category_count_with_post_id():
        return """
            select count(*)
            from community_posts cp
            where category = (select category from community_posts where id = :post_id)
              and delete_by_user = false
              and delete_by_admin = false
        """

    @staticmethod
    def get_post_all_count_with_post_id():
        return """
            select count(*)
            from community_posts cp
            where delete_by_user = false
              and delete_by_admin = false
        """

    @staticmethod
    def get_post_issue_count():
        return """
            select count(*)
            from community_posts_hot_issue cphi
            left join community_posts cp on cphi.post_id = cp.id
            where NOT EXISTS (
                  SELECT 1
                  FROM user_block ub
                  WHERE ub.request_email = :user_email
                    AND ub.target_email = cp.user_email
              )
        """

    @staticmethod
    def get_posts_with_issue(preview: bool = False):
        return CommunityUtil._get_post_page(
            """
            SELECT cp.id, cphi.issue_time
            FROM community_posts_hot_issue cphi
            JOIN community_posts cp ON cp.id = cphi.post_id
            WHERE cp.delete_by_user = false AND cp.delete_by_admin = false
              AND NOT EXISTS (
                  SELECT 1 FROM user_block ub
                  WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email
              )
            ORDER BY cphi.issue_time DESC
            LIMIT :limit OFFSET :offset
            """,
            "page.issue_time DESC",
            preview,
            include_issue_time=True,
        )

    @staticmethod
    def get_related_post_links():
        return """
            SELECT cp.id::text AS id, cp.slug, cp.title
            FROM community_posts cp
            WHERE cp.category = :category
              AND cp.delete_by_user = false AND cp.delete_by_admin = false
              AND NOT EXISTS (
                  SELECT 1 FROM user_block ub
                  WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email
              )
            ORDER BY cp.create_time DESC
            LIMIT 6
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
                coalesce((SELECT COUNT(*) FROM community_comments cc WHERE cc.post_id = cp.id), 0) AS comment_count,
                (SELECT COUNT(*) FROM user_follows uf WHERE uf.following_email = cp.user_email) AS follower_count,
                (SELECT COUNT(*) FROM community_posts cp2 WHERE cp2.user_email = cp.user_email) AS total_post_count
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
                CASE WHEN cpb.post_id IS NOT NULL THEN 1 ELSE 0 END AS is_bookmarked,
                (
                    SELECT COALESCE(SUM(CASE WHEN cpr2.reaction_type = 1 THEN 1 ELSE 0 END), 0)
                         - COALESCE(SUM(CASE WHEN cpr2.reaction_type = 0 THEN 1 ELSE 0 END), 0)
                    FROM community_posts_reactions cpr2
                    WHERE cpr2.post_id = cp.id
                ) AS like_count
            FROM community_posts cp
            LEFT JOIN community_posts_bookmark cpb
                   ON cp.id = cpb.post_id AND cpb.email = :user_email
            LEFT JOIN community_posts_reactions cpr
                   ON cp.id = cpr.post_id AND cpr.user_email = :user_email
            WHERE cp.id = :post_id
        """

    @staticmethod
    def get_detail_author_meta_data():
        return """
            select cp.user_email,
                   coalesce(ui.nickname, cp.user_email) as nickname,
                   count(distinct cp2.id) as posts_count,
                   count(cpr.post_id) filter (where cpr.reaction_type = 1) as like_count,
                   case when uf.follower_email is not null then 1 else 0 end as is_follow
            from community_posts cp
                     left join user_info ui on cp.user_email = ui.email
                     left join community_posts cp2 on cp2.user_email = cp.user_email
                     left join community_posts_reactions cpr on cp2.id = cpr.post_id
                     left join user_follows uf
                               on uf.following_email = :user_email
                                  and uf.follower_email = cp.user_email
            where cp.id = :post_id
              and cp.delete_by_user = false
              and cp.delete_by_admin = false
            group by cp.user_email, coalesce(ui.nickname, cp.user_email), uf.follower_email
        """

    @staticmethod
    def check_follow():
        return """
            SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END AS is_follow
            FROM user_follows
            WHERE following_email = :user_email
              AND follower_email = :author_email
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
    def get_current_post_all_page_num():
        return """
            WITH ordered_posts AS (
                SELECT id,
                       ROW_NUMBER() OVER (ORDER BY create_time DESC) AS rn
                FROM community_posts cp
                WHERE delete_by_user = false
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

    @staticmethod
    def increase_view_count():
        return """
            UPDATE community_posts_views
            SET view_count = view_count + 1
            WHERE post_id = :post_id
        """
