import re

from sqlalchemy import text

from api.community.util import CommunityUtilV3
from api.news.models import InformationV3


class CommunityFunctionV3:
    @staticmethod
    def extract_thumbnail_img(html):
        match = re.search(r'<img[^>]+src="([^"]+)"', html)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def fetch_post_detail(session, post_id: int, user_email: str):
        result = session.execute(
            text(CommunityUtilV3.get_post_detail()),
            {"post_id": post_id, "user_email": user_email},
        )
        return [dict(row) for row in result.mappings()][0]

    @staticmethod
    def fetch_author_meta(session, post_id: int, user_email: str):
        result = session.execute(
            text(CommunityUtilV3.get_detail_author_meta_data()),
            {"post_id": post_id, "user_email": user_email},
        )
        row = result.mappings().first()
        if row is None:
            return {
                "user_email": None,
                "nickname": None,
                "posts_count": 0,
                "like_count": 0,
                "is_follow": 0,
            }
        return dict(row)

    @staticmethod
    def fetch_posts_with_paging(
        session, post_id: int, page_category: str, user_email: str, limit: int = 20
    ):
        if page_category == "issue":
            get_post_query = text(CommunityUtilV3.get_posts_with_issue())
            get_post_count_query = text(CommunityUtilV3.get_post_issue_count())
            current_page_query = text(CommunityUtilV3.get_current_post_issue_page_num())
        else:
            get_post_query = text(CommunityUtilV3.get_posts_with_post_id())
            get_post_count_query = text(
                CommunityUtilV3.get_post_category_count_with_post_id()
            )
            current_page_query = text(
                CommunityUtilV3.get_current_post_category_page_num()
            )

        current_page_num_raw = session.execute(
            current_page_query, {"post_id": post_id}
        ).scalar()
        current_page_num = ((current_page_num_raw or 1) - 1) // limit + 1
        offset = (current_page_num - 1) * limit

        posts_result = session.execute(
            get_post_query,
            {
                "limit": limit,
                "offset": offset,
                "post_id": post_id,
                "user_email": user_email,
            },
        )
        posts = [dict(row) for row in posts_result.mappings()]
        total = session.execute(
            get_post_count_query, {"post_id": post_id, "user_email": user_email}
        ).scalar()

        return {
            "total": total,
            "max_page_count": (total + limit - 1) // limit,
            "posts": posts,
            "current_page_num": current_page_num,
        }

    @staticmethod
    def fetch_notice_posts(session):
        return (
            session.query(InformationV3)
            .filter(InformationV3.information_type == "NOTICE")
            .order_by(InformationV3.update_time.desc())
            .limit(5)
            .all()
        )

    @staticmethod
    def parse_id_and_slug(value: str):
        id_str, _slug = value.split("-", 1)
        return int(id_str)

    @staticmethod
    def get_search_sql(search_type: str):
        queries = {
            "title": """
                SELECT cp.id::text AS id, cp.slug, cp.user_email, cp.category, ui.nickname,
                       cp.title, cp.contents, cpv.view_count,
                       COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score,
                       cp.thumbnail, cp.delete_by_user, cp.delete_by_admin, cp.create_time, cp.update_time
                FROM community_posts cp
                LEFT JOIN user_info ui ON cp.user_email = ui.email
                LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                LEFT JOIN (SELECT post_id, COUNT(*) AS comment_count FROM community_comments GROUP BY post_id) cc ON cc.post_id = cp.id
                LEFT JOIN (
                    SELECT post_id,
                           SUM(CASE WHEN reaction_type = 1 THEN 1 WHEN reaction_type = 0 THEN -1 ELSE 0 END) AS reaction_score
                    FROM community_posts_reactions GROUP BY post_id
                ) r ON r.post_id = cp.id
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND cp.title ILIKE :word
                  AND NOT EXISTS (
                        SELECT 1 FROM user_block ub
                        WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email
                    )
                ORDER BY cp.create_time DESC
                LIMIT :limit OFFSET :offset
            """,
            "titleContent": """
                SELECT cp.id::text AS id, cp.slug, cp.user_email, cp.category, ui.nickname,
                       cp.title, cp.contents, cpv.view_count,
                       COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score,
                       cp.thumbnail, cp.delete_by_user, cp.delete_by_admin, cp.create_time, cp.update_time
                FROM community_posts cp
                LEFT JOIN user_info ui ON cp.user_email = ui.email
                LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                LEFT JOIN (SELECT post_id, COUNT(*) AS comment_count FROM community_comments GROUP BY post_id) cc ON cc.post_id = cp.id
                LEFT JOIN (
                    SELECT post_id,
                           SUM(CASE WHEN reaction_type = 1 THEN 1 WHEN reaction_type = 0 THEN -1 ELSE 0 END) AS reaction_score
                    FROM community_posts_reactions GROUP BY post_id
                ) r ON r.post_id = cp.id
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND (cp.title ILIKE :word OR cp.contents ILIKE :word)
                  AND NOT EXISTS (
                        SELECT 1 FROM user_block ub
                        WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email
                    )
                ORDER BY cp.create_time DESC
                LIMIT :limit OFFSET :offset
            """,
            "comment": """
                WITH comment_count AS (
                    SELECT post_id, COUNT(*) AS comment_count FROM community_comments GROUP BY post_id
                ),
                reaction_sum AS (
                    SELECT post_id,
                           SUM(CASE WHEN reaction_type = 1 THEN 1 WHEN reaction_type = 0 THEN -1 ELSE 0 END) AS reaction_score
                    FROM community_posts_reactions GROUP BY post_id
                )
                SELECT cp.id::text AS id, cp.slug, cp.user_email, cp.category, ui.nickname,
                       cp.title, cp.contents, cpv.view_count,
                       COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score,
                       cp.thumbnail, cp.delete_by_user, cp.delete_by_admin, cp.create_time, cp.update_time,
                       json_build_object(
                           'id', c.id, 'contents', c.contents, 'user_email', c.user_email,
                           'create_time', c.create_time, 'nickname', cui.nickname, 'update_time', c.update_time
                       ) AS comment
                FROM community_posts cp
                LEFT JOIN user_info ui ON cp.user_email = ui.email
                LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                LEFT JOIN comment_count cc ON cc.post_id = cp.id
                LEFT JOIN reaction_sum r ON r.post_id = cp.id
                INNER JOIN community_comments c ON c.post_id = cp.id AND c.contents ILIKE :word
                LEFT JOIN user_info cui ON c.user_email = cui.email
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND c.delete_by_admin = false
                  AND c.delete_by_user = false
                  AND NOT EXISTS (
                      SELECT 1 FROM user_block ub
                      WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email
                  )
                ORDER BY cp.create_time DESC
                LIMIT :limit OFFSET :offset
            """,
            "author": """
                SELECT count(*) FROM community_posts WHERE false
            """,
            "all": """
                SELECT count(*) FROM community_posts WHERE false
            """,
        }
        if search_type == "author":
            return """
                WITH comment_count AS (
                    SELECT post_id, COUNT(*) AS comment_count FROM community_comments GROUP BY post_id
                ),
                reaction_sum AS (
                    SELECT post_id,
                           SUM(CASE WHEN reaction_type = 1 THEN 1 WHEN reaction_type = 0 THEN -1 ELSE 0 END) AS reaction_score
                    FROM community_posts_reactions GROUP BY post_id
                )
                SELECT cp.id::text AS id, cp.slug, cp.user_email, cp.category, ui.nickname,
                       cp.title, cp.contents, cpv.view_count, COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score, cp.thumbnail,
                       cp.delete_by_user, cp.delete_by_admin, cp.create_time, cp.update_time,
                       json_build_object(
                           'id', c.id, 'contents', c.contents, 'user_email', c.user_email,
                           'create_time', c.create_time, 'nickname', cui.nickname, 'update_time', c.update_time
                       ) AS comment
                FROM community_posts cp
                LEFT JOIN user_info ui ON cp.user_email = ui.email
                LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                LEFT JOIN comment_count cc ON cc.post_id = cp.id
                LEFT JOIN reaction_sum r ON r.post_id = cp.id
                INNER JOIN community_comments c ON c.post_id = cp.id
                LEFT JOIN user_info cui ON c.user_email = cui.email
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND c.delete_by_admin = false
                  AND c.delete_by_user = false
                  AND (ui.nickname ILIKE :word OR cui.nickname ILIKE :word)
                  AND NOT EXISTS (
                      SELECT 1 FROM user_block ub
                      WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email
                  )
                ORDER BY cp.create_time DESC
                LIMIT :limit OFFSET :offset
            """
        if search_type == "all":
            return """
                WITH comment_count AS (
                    SELECT post_id, COUNT(*) AS comment_count FROM community_comments GROUP BY post_id
                ),
                reaction_sum AS (
                    SELECT post_id,
                           SUM(CASE WHEN reaction_type = 1 THEN 1 WHEN reaction_type = 0 THEN -1 ELSE 0 END) AS reaction_score
                    FROM community_posts_reactions GROUP BY post_id
                )
                SELECT *
                FROM (
                    SELECT cp.id::text AS id, cp.slug, cp.user_email, ui.nickname, cp.category, cp.title, cp.contents,
                           cpv.view_count, COALESCE(cc.comment_count, 0) AS comment_count,
                           COALESCE(r.reaction_score, 0) AS reaction_score, cp.thumbnail, NULL::json AS comment,
                           cp.create_time
                    FROM community_posts cp
                    LEFT JOIN user_info ui ON cp.user_email = ui.email
                    LEFT JOIN comment_count cc ON cc.post_id = cp.id
                    LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                    LEFT JOIN reaction_sum r ON r.post_id = cp.id
                    WHERE cp.delete_by_admin = false AND cp.delete_by_user = false
                      AND NOT EXISTS (SELECT 1 FROM user_block ub WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email)
                      AND (cp.title ILIKE :word OR cp.contents ILIKE :word)

                    UNION ALL

                    SELECT cp.id::text AS id, cp.slug, cp.user_email, ui.nickname, cp.category, cp.title, cp.contents,
                           cpv.view_count, COALESCE(cc.comment_count, 0) AS comment_count,
                           COALESCE(r.reaction_score, 0) AS reaction_score, cp.thumbnail,
                           json_build_object('id', c.id, 'contents', c.contents, 'user_email', c.user_email, 'nickname', cui.nickname, 'create_time', c.create_time, 'update_time', c.update_time) AS comment,
                           cp.create_time
                    FROM community_posts cp
                    LEFT JOIN user_info ui ON cp.user_email = ui.email
                    LEFT JOIN comment_count cc ON cc.post_id = cp.id
                    LEFT JOIN reaction_sum r ON r.post_id = cp.id
                    LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                    INNER JOIN community_comments c ON c.post_id = cp.id
                    LEFT JOIN user_info cui ON c.user_email = cui.email
                    WHERE cp.delete_by_admin = false AND cp.delete_by_user = false
                      AND c.delete_by_admin = false AND c.delete_by_user = false
                      AND NOT EXISTS (SELECT 1 FROM user_block ub WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email)
                      AND (c.contents ILIKE :word OR ui.nickname ILIKE :word OR cui.nickname ILIKE :word)
                ) AS combined
                ORDER BY create_time DESC
                LIMIT :limit OFFSET :offset
            """
        return queries[search_type]

    @staticmethod
    def get_search_total_count_sql(search_type: str):
        queries = {
            "title": """
                SELECT count(*)
                FROM community_posts cp
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND cp.title ILIKE :word
                  AND NOT EXISTS (
                        SELECT 1 FROM user_block ub
                        WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email
                    )
            """,
            "titleContent": """
                SELECT count(*)
                FROM community_posts cp
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND (cp.title ILIKE :word OR cp.contents ILIKE :word)
                  AND NOT EXISTS (
                        SELECT 1 FROM user_block ub
                        WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email
                    )
            """,
            "comment": """
                SELECT count(*)
                FROM community_posts cp
                INNER JOIN community_comments c ON c.post_id = cp.id AND c.contents ILIKE :word
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND c.delete_by_admin = false
                  AND c.delete_by_user = false
                  AND NOT EXISTS (
                      SELECT 1 FROM user_block ub
                      WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email
                  )
            """,
            "author": """
                SELECT count(*)
                FROM community_posts cp
                LEFT JOIN user_info ui ON cp.user_email = ui.email
                INNER JOIN community_comments c ON c.post_id = cp.id
                LEFT JOIN user_info cui ON c.user_email = cui.email
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND c.delete_by_admin = false
                  AND c.delete_by_user = false
                  AND (ui.nickname ILIKE :word OR cui.nickname ILIKE :word)
                  AND NOT EXISTS (
                      SELECT 1 FROM user_block ub
                      WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email
                  )
            """,
            "all": """
                SELECT COUNT(*) AS total_count
                FROM (
                    SELECT cp.id::text AS id
                    FROM community_posts cp
                    WHERE cp.delete_by_admin = false
                      AND cp.delete_by_user = false
                      AND NOT EXISTS (SELECT 1 FROM user_block ub WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email)
                      AND (cp.title ILIKE :word OR cp.contents ILIKE :word)
                    UNION ALL
                    SELECT cp.id::text AS id
                    FROM community_posts cp
                    INNER JOIN community_comments c ON c.post_id = cp.id
                    LEFT JOIN user_info ui ON cp.user_email = ui.email
                    LEFT JOIN user_info cui ON c.user_email = cui.email
                    WHERE cp.delete_by_admin = false
                      AND cp.delete_by_user = false
                      AND c.delete_by_admin = false
                      AND c.delete_by_user = false
                      AND NOT EXISTS (SELECT 1 FROM user_block ub WHERE ub.request_email = :user_email AND ub.target_email = cp.user_email)
                      AND (c.contents ILIKE :word OR ui.nickname ILIKE :word OR cui.nickname ILIKE :word)
                ) AS combined
            """,
        }
        return queries[search_type]
