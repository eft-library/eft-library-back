import re

from sqlalchemy import text
from api.community.util import CommunityUtil
from api.news.models import Information, InformationV3


class CommunityFunction:

    @staticmethod
    def extract_thumbnail_img(html):
        # 정규 표현식을 사용하여 첫 번째 <img> 태그의 src 값 찾아서 썸네일 반환
        match = re.search(r'<img[^>]+src="([^"]+)"', html)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def fetch_post_detail(session, post_id: int, user_email: str):
        query = text(CommunityUtil.get_post_detail())
        params = {"post_id": post_id, "user_email": user_email}
        result = session.execute(query, params)
        return [dict(row) for row in result.mappings()][0]

    @staticmethod
    def fetch_author_meta(session, post_id: int, user_email: str):
        query = text(CommunityUtil.get_detail_author_meta_data())
        params = {"post_id": post_id, "user_email": user_email}
        result = session.execute(query, params)
        return [dict(row) for row in result.mappings()][0]

    @staticmethod
    def fetch_posts_with_paging(
        session, post_id: int, page_category: str, user_email: str, limit: int = 20
    ):
        if page_category == "issue":
            get_post_query = text(CommunityUtil.get_posts_with_issue())
            get_post_count_query = text(CommunityUtil.get_post_issue_count())
            get_post_current_page_num_query = text(
                CommunityUtil.get_current_post_issue_page_num()
            )
        else:
            get_post_query = text(CommunityUtil.get_posts_with_post_id())
            get_post_count_query = text(
                CommunityUtil.get_post_category_count_with_post_id()
            )
            get_post_current_page_num_query = text(
                CommunityUtil.get_current_post_category_page_num()
            )

        # 현재 페이지 번호
        current_page_num_result = session.execute(
            get_post_current_page_num_query,
            {"post_id": post_id},
        )
        current_page_num_raw = current_page_num_result.scalar()
        current_page_num = ((current_page_num_raw or 1) - 1) // limit + 1

        # 페이징 offset
        offset = (current_page_num - 1) * limit

        # 게시글 목록
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

        # 전체 개수
        total_result = session.execute(
            get_post_count_query, {"post_id": post_id, "user_email": user_email}
        )
        total = total_result.scalar()
        max_page_count = (total + limit - 1) // limit

        return {
            "total": total,
            "max_page_count": max_page_count,
            "posts": posts,
            "current_page_num": current_page_num,
        }

    @staticmethod
    def fetch_notice_posts(s):
        return (
            s.query(Information)
            .filter(Information.type == "NOTICE")
            .order_by(Information.update_time.desc())
            .limit(5)
            .all()
        )

    @staticmethod
    def parse_id_and_slug(value: str):
        try:
            id_str, slug = value.split("-", 1)  # 1번만 split (slug에 '-'가 있어도 유지)
            return int(id_str)
        except ValueError:
            raise ValueError(f"잘못된 형식입니다: {value}")

    @staticmethod
    def get_search_sql(search_type: str):
        queries = {
            "title": """
                SELECT cp.id::text AS id,
                       cp.slug,
                       cp.user_email,
                       cp.category,
                       ui.nickname,
                       cp.title,
                       cp.contents,
                       cpv.view_count,
                       COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score,
                       cp.thumbnail,
                       cp.delete_by_user,
                       cp.delete_by_admin,
                       cp.create_time,
                       cp.update_time
                FROM community_posts cp
                LEFT JOIN user_info ui ON cp.user_email = ui.email
                LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                LEFT JOIN (
                    SELECT post_id, COUNT(*) AS comment_count
                    FROM community_comments
                    GROUP BY post_id
                ) cc ON cc.post_id = cp.id
                LEFT JOIN (
                    SELECT post_id,
                           SUM(CASE
                                   WHEN reaction_type = 1 THEN 1
                                   WHEN reaction_type = 0 THEN -1
                                   ELSE 0 END) AS reaction_score
                    FROM community_posts_reactions
                    GROUP BY post_id
                ) r ON r.post_id = cp.id
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND cp.title ILIKE :word
                  AND NOT EXISTS (
                        SELECT 1
                        FROM user_block ub
                        WHERE ub.blocker_email = :user_email
                          AND ub.blocked_email = cp.user_email
                    )
                ORDER BY cp.create_time DESC
                LIMIT :limit OFFSET :offset
            """,
            "titleContent": """
                SELECT cp.id::text AS id,
                       cp.slug,
                       cp.user_email,
                       cp.category,
                       ui.nickname,
                       cp.title,
                       cp.contents,
                       cpv.view_count,
                       COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score,
                       cp.thumbnail,
                       cp.delete_by_user,
                       cp.delete_by_admin,
                       cp.create_time,
                       cp.update_time
                FROM community_posts cp
                LEFT JOIN user_info ui ON cp.user_email = ui.email
                LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                LEFT JOIN (
                    SELECT post_id, COUNT(*) AS comment_count
                    FROM community_comments
                    GROUP BY post_id
                ) cc ON cc.post_id = cp.id
                LEFT JOIN (
                    SELECT post_id,
                           SUM(CASE
                                   WHEN reaction_type = 1 THEN 1
                                   WHEN reaction_type = 0 THEN -1
                                   ELSE 0 END) AS reaction_score
                    FROM community_posts_reactions
                    GROUP BY post_id
                ) r ON r.post_id = cp.id
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND (cp.title ILIKE :word OR cp.contents ILIKE :word)
                  AND NOT EXISTS (
                        SELECT 1
                        FROM user_block ub
                        WHERE ub.blocker_email = :user_email
                          AND ub.blocked_email = cp.user_email
                    )
                ORDER BY cp.create_time DESC
                LIMIT :limit OFFSET :offset
            """,
            "comment": """
                WITH comment_count AS (
                    SELECT post_id, COUNT(*) AS comment_count
                    FROM community_comments
                    GROUP BY post_id
                ),
                reaction_sum AS (
                    SELECT post_id,
                           SUM(CASE
                                   WHEN reaction_type = 1 THEN 1
                                   WHEN reaction_type = 0 THEN -1
                                   ELSE 0 END) AS reaction_score
                    FROM community_posts_reactions
                    GROUP BY post_id
                )
                SELECT cp.id::text AS id,
                       cp.slug,
                       cp.user_email,
                       cp.category,
                       ui.nickname,
                       cp.title,
                       cp.contents,
                       cpv.view_count,
                       COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score,
                       cp.thumbnail,
                       cp.delete_by_user,
                       cp.delete_by_admin,
                       cp.create_time,
                       cp.update_time,
                       json_build_object(
                           'id', c.id,
                           'contents', c.contents,
                           'user_email', c.user_email,
                           'create_time', c.create_time,
                           'nickname', cui.nickname,
                           'update_time', c.update_time
                       ) AS comment
                FROM community_posts cp
                         LEFT JOIN user_info ui ON cp.user_email = ui.email
                         LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                         LEFT JOIN comment_count cc ON cc.post_id = cp.id
                         LEFT JOIN reaction_sum r ON r.post_id = cp.id
                         INNER JOIN community_comments c 
                                 ON c.post_id = cp.id 
                                AND c.contents ILIKE :word
                         LEFT JOIN user_info cui ON c.user_email = cui.email
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND c.delete_by_admin = false
                  AND c.delete_by_user = false
                  AND NOT EXISTS (
                      SELECT 1
                      FROM user_block ub
                      WHERE ub.blocker_email = :user_email
                        AND ub.blocked_email = cp.user_email
                  )
                ORDER BY cp.create_time DESC
                LIMIT :limit OFFSET :offset
    """,
            "all": """
            WITH comment_count AS (
                SELECT post_id, COUNT(*) AS comment_count
                FROM community_comments
                GROUP BY post_id
            ),
            reaction_sum AS (
                SELECT post_id,
                       SUM(CASE
                               WHEN reaction_type = 1 THEN 1
                               WHEN reaction_type = 0 THEN -1
                               ELSE 0 END) AS reaction_score
                FROM community_posts_reactions
                GROUP BY post_id
            )
            SELECT *
            FROM (
                -- 1. 게시글 제목/내용 검색
                SELECT cp.id::text AS id,
                       cp.slug,
                       cp.user_email,
                       ui.nickname ,
                       cp.title,
                       cp.category,
                       cp.contents,
                       cpv.view_count,
                       COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score,
                       cp.thumbnail,
                       NULL::json AS comment,
                       cp.create_time
                FROM community_posts cp
                LEFT JOIN user_info ui ON cp.user_email = ui.email
                LEFT JOIN comment_count cc ON cc.post_id = cp.id
                LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                LEFT JOIN reaction_sum r ON r.post_id = cp.id
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND NOT EXISTS (
                      SELECT 1
                      FROM user_block ub
                      WHERE ub.blocker_email = :user_email
                        AND ub.blocked_email = cp.user_email
                  )
                  AND (cp.title ILIKE :word OR cp.contents ILIKE :word)
            
                UNION ALL
            
                -- 2. 댓글 내용 검색
                SELECT cp.id::text AS id,
                       cp.slug,
                       cp.user_email,
                       ui.nickname ,
                       cp.category,
                       cp.title,
                       cp.contents,
                       cpv.view_count,
                       COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score,
                       cp.thumbnail,
                       json_build_object(
                           'id', c.id,
                           'contents', c.contents,
                           'user_email', c.user_email,
                           'nickname', cui.nickname,
                           'create_time', c.create_time,
                           'update_time', c.update_time
                       ) AS comment,
                       cp.create_time
                FROM community_posts cp
                LEFT JOIN user_info ui ON cp.user_email = ui.email
                LEFT JOIN comment_count cc ON cc.post_id = cp.id
                LEFT JOIN reaction_sum r ON r.post_id = cp.id
                LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                INNER JOIN community_comments c ON c.post_id = cp.id
                LEFT JOIN user_info cui ON c.user_email = cui.email
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND c.delete_by_admin = false
                  AND c.delete_by_user = false
                  AND NOT EXISTS (
                      SELECT 1
                      FROM user_block ub
                      WHERE ub.blocker_email = :user_email
                        AND ub.blocked_email = cp.user_email
                  )
                  AND c.contents ILIKE :word
            
                UNION ALL
            
                -- 3. 작성자 검색 (게시글 작성자 + 댓글 작성자)
                SELECT cp.id::text AS id,
                       cp.slug,
                       cp.user_email,
                       ui.nickname,
                       cp.category,
                       cp.title,
                       cp.contents,
                       cpv.view_count,
                       COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score,
                       cp.thumbnail,
                       json_build_object(
                           'id', c.id,
                           'contents', c.contents,
                           'user_email', c.user_email,
                           'nickname', cui.nickname,
                           'create_time', c.create_time,
                           'update_time', c.update_time
                       ) AS comment,
                       cp.create_time
                FROM community_posts cp
                LEFT JOIN user_info ui ON cp.user_email = ui.email
                LEFT JOIN comment_count cc ON cc.post_id = cp.id
                LEFT JOIN reaction_sum r ON r.post_id = cp.id
                LEFT JOIN community_comments c ON c.post_id = cp.id
                LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                LEFT JOIN user_info cui ON c.user_email = cui.email
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND c.delete_by_admin = false
                  AND c.delete_by_user = false
                  AND NOT EXISTS (
                      SELECT 1
                      FROM user_block ub
                      WHERE ub.blocker_email = :user_email
                        AND ub.blocked_email = cp.user_email
                  )
                  AND (ui.nickname ILIKE :word OR cui.nickname ILIKE :word)
            
            ) AS combined
            ORDER BY create_time DESC
            LIMIT :limit OFFSET :offset
            """,
            "author": """
                WITH comment_count AS (
                    SELECT post_id, COUNT(*) AS comment_count
                    FROM community_comments
                    GROUP BY post_id
                ),
                reaction_sum AS (
                    SELECT post_id,
                           SUM(CASE
                                   WHEN reaction_type = 1 THEN 1
                                   WHEN reaction_type = 0 THEN -1
                                   ELSE 0 END) AS reaction_score
                    FROM community_posts_reactions
                    GROUP BY post_id
                )
                SELECT cp.id::text AS id,
                       cp.slug,
                       cp.user_email,
                       cp.category,
                       ui.nickname ,
                       cp.title,
                       cp.contents,
                       cpv.view_count,
                       COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score,
                       cp.thumbnail,
                       cp.delete_by_user,
                       cp.delete_by_admin,
                       cp.create_time,
                       cp.update_time,
                       json_build_object(
                           'id', c.id,
                           'contents', c.contents,
                           'user_email', c.user_email,
                           'create_time', c.create_time,
                           'nickname', cui.nickname,
                           'update_time', c.update_time
                       ) AS comment
                FROM community_posts cp
                LEFT JOIN user_info ui ON cp.user_email = ui.email
                LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                LEFT JOIN comment_count cc ON cc.post_id = cp.id
                LEFT JOIN reaction_sum r ON r.post_id = cp.id
                INNER JOIN community_comments c 
                        ON c.post_id = cp.id
                LEFT JOIN user_info cui ON c.user_email = cui.email
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND c.delete_by_admin = false
                  AND c.delete_by_user = false
                  AND (
                        ui.nickname ILIKE :word 
                        OR cui.nickname ILIKE :word 
                      )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM user_block ub
                      WHERE ub.blocker_email = :user_email
                        AND ub.blocked_email = cp.user_email
                  )
                ORDER BY cp.create_time DESC
                LIMIT :limit OFFSET :offset
            """,
        }

        return queries[search_type]


class CommunityFunctionV3:

    @staticmethod
    def extract_thumbnail_img(html):
        return CommunityFunction.extract_thumbnail_img(html)

    @staticmethod
    def parse_id_and_slug(value: str):
        return CommunityFunction.parse_id_and_slug(value)

    @staticmethod
    def fetch_post_detail(session, post_id: int, user_email: str):
        from api.community.util import CommunityUtilV3

        query = text(CommunityUtilV3.get_post_detail())
        params = {"post_id": post_id, "user_email": user_email}
        result = session.execute(query, params)
        return [dict(row) for row in result.mappings()][0]

    @staticmethod
    def fetch_author_meta(session, post_id: int, user_email: str):
        from api.community.util import CommunityUtilV3

        query = text(CommunityUtilV3.get_detail_author_meta_data())
        params = {"post_id": post_id, "user_email": user_email}
        result = session.execute(query, params)
        return [dict(row) for row in result.mappings()][0]

    @staticmethod
    def fetch_posts_with_paging(
        session, post_id: int, page_category: str, user_email: str, limit: int = 20
    ):
        from api.community.util import CommunityUtilV3

        if page_category == "issue":
            get_post_query = text(CommunityUtilV3.get_posts_with_issue())
            get_post_count_query = text(CommunityUtilV3.get_post_issue_count())
            get_post_current_page_num_query = text(
                CommunityUtilV3.get_current_post_issue_page_num()
            )
        else:
            get_post_query = text(CommunityUtilV3.get_posts_with_post_id())
            get_post_count_query = text(
                CommunityUtilV3.get_post_category_count_with_post_id()
            )
            get_post_current_page_num_query = text(
                CommunityUtilV3.get_current_post_category_page_num()
            )

        current_page_num_result = session.execute(
            get_post_current_page_num_query,
            {"post_id": post_id},
        )
        current_page_num_raw = current_page_num_result.scalar()
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

        total_result = session.execute(
            get_post_count_query, {"post_id": post_id, "user_email": user_email}
        )
        total = total_result.scalar()
        max_page_count = (total + limit - 1) // limit

        return {
            "total": total,
            "max_page_count": max_page_count,
            "posts": posts,
            "current_page_num": current_page_num,
        }

    @staticmethod
    def fetch_notice_posts(s):
        return (
            s.query(InformationV3)
            .filter(InformationV3.information_type == "NOTICE")
            .order_by(InformationV3.update_time.desc())
            .limit(5)
            .all()
        )

    @staticmethod
    def get_search_sql(search_type: str):
        return (
            CommunityFunction.get_search_sql(search_type)
            .replace("ub.blocker_email", "ub.request_email")
            .replace("ub.blocked_email", "ub.target_email")
        )

    @staticmethod
    def get_search_total_count_sql(search_type: str):
        return (
            CommunityFunction.get_search_total_count_sql(search_type)
            .replace("ub.blocker_email", "ub.request_email")
            .replace("ub.blocked_email", "ub.target_email")
        )

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
                        SELECT 1
                        FROM user_block ub
                        WHERE ub.blocker_email = :user_email
                          AND ub.blocked_email = cp.user_email
                    )
            """,
            "titleContent": """
                SELECT count(*)
                FROM community_posts cp
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND (cp.title ILIKE :word OR cp.contents ILIKE :word)
                  AND NOT EXISTS (
                        SELECT 1
                        FROM user_block ub
                        WHERE ub.blocker_email = :user_email
                          AND ub.blocked_email = cp.user_email
                    )
            """,
            "comment": """
                SELECT count(*)
                FROM community_posts cp
                         INNER JOIN community_comments c 
                                 ON c.post_id = cp.id 
                                AND c.contents ILIKE :word
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND c.delete_by_admin = false
                  AND c.delete_by_user = false
                  AND NOT EXISTS (
                      SELECT 1
                      FROM user_block ub
                      WHERE ub.blocker_email = :user_email
                        AND ub.blocked_email = cp.user_email
                  )
    """,
            "all": """
                SELECT COUNT(*) AS total_count
                FROM (
                    -- 1. 게시글 제목/내용 검색
                    SELECT cp.id::text AS id
                    FROM community_posts cp
                    LEFT JOIN user_info ui ON cp.user_email = ui.email
                    WHERE cp.delete_by_admin = false
                      AND cp.delete_by_user = false
                      AND NOT EXISTS (
                          SELECT 1
                          FROM user_block ub
                          WHERE ub.blocker_email = :user_email
                            AND ub.blocked_email = cp.user_email
                      )
                      AND (cp.title ILIKE :word OR cp.contents ILIKE :word)
                
                    UNION ALL
                
                    -- 2. 댓글 내용 검색
                    SELECT cp.id::text AS id
                    FROM community_posts cp
                    INNER JOIN community_comments c ON c.post_id = cp.id
                    LEFT JOIN user_info ui ON cp.user_email = ui.email
                    LEFT JOIN user_info cui ON c.user_email = cui.email
                    WHERE cp.delete_by_admin = false
                      AND cp.delete_by_user = false
                      AND c.delete_by_admin = false
                      AND c.delete_by_user = false
                      AND NOT EXISTS (
                          SELECT 1
                          FROM user_block ub
                          WHERE ub.blocker_email = :user_email
                            AND ub.blocked_email = cp.user_email
                      )
                      AND c.contents ILIKE :word
                
                    UNION ALL
                
                    -- 3. 작성자 검색 (게시글 작성자 + 댓글 작성자)
                    SELECT cp.id::text AS id
                    FROM community_posts cp
                    LEFT JOIN user_info ui ON cp.user_email = ui.email
                    LEFT JOIN community_comments c ON c.post_id = cp.id
                    LEFT JOIN user_info cui ON c.user_email = cui.email
                    WHERE cp.delete_by_admin = false
                      AND cp.delete_by_user = false
                      AND c.delete_by_admin = false
                      AND c.delete_by_user = false
                      AND NOT EXISTS (
                          SELECT 1
                          FROM user_block ub
                          WHERE ub.blocker_email = :user_email
                            AND ub.blocked_email = cp.user_email
                      )
                      AND (ui.nickname ILIKE :word OR cui.nickname ILIKE :word)
                ) AS combined
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
                  AND (
                        ui.nickname ILIKE :word 
                        OR cui.nickname ILIKE :word 
                      )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM user_block ub
                      WHERE ub.blocker_email = :user_email
                        AND ub.blocked_email = cp.user_email
                  )
            """,
        }

        return queries[search_type]


CommunityFunction.get_search_total_count_sql = staticmethod(
    CommunityFunctionV3.get_search_total_count_sql
)


def _get_search_total_count_sql_v3(search_type: str):
    return (
        CommunityFunction.get_search_total_count_sql(search_type)
        .replace("ub.blocker_email", "ub.request_email")
        .replace("ub.blocked_email", "ub.target_email")
    )


CommunityFunctionV3.get_search_total_count_sql = staticmethod(
    _get_search_total_count_sql_v3
)
