import re

from sqlalchemy import text

from api.community.community_res_models import (
    CommunityPosts,
    CommunityPostsHotIssue,
)
from api.community.util import CommunityUtil
from api.notice.models import Notice


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
        session, post_id: int, page_category: str, limit: int = 20
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
        current_page_num = (current_page_num_result.scalar() - 1) // limit + 1

        # 페이징 offset
        offset = (current_page_num - 1) * limit

        # 게시글 목록
        posts_result = session.execute(
            get_post_query,
            {"limit": limit, "offset": offset, "post_id": post_id},
        )
        posts = [dict(row) for row in posts_result.mappings()]

        # 전체 개수
        total_result = session.execute(get_post_count_query, {"post_id": post_id})
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
        return s.query(Notice).order_by(Notice.update_time.desc()).limit(5).all()

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
                       cp.update_time
                FROM community_posts cp
                         LEFT JOIN user_info ui ON cp.user_email = ui.email
                         LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                         LEFT JOIN comment_count cc ON cc.post_id = cp.id
                         LEFT JOIN reaction_sum r ON r.post_id = cp.id
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND cp.title ILIKE :word 
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
                       COUNT(DISTINCT cc.id) AS comment_count,
                       COALESCE(SUM(CASE
                                        WHEN cpr.reaction_type = 1 THEN 1
                                        WHEN cpr.reaction_type = 0 THEN -1
                                        ELSE 0 END), 0) AS reaction_score,
                       cp.thumbnail,
                       cp.delete_by_user,
                       cp.delete_by_admin,
                       cp.create_time,
                       cp.update_time
                FROM community_posts cp
                         LEFT JOIN user_info ui ON cp.user_email = ui.email
                         LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                         LEFT JOIN community_comments cc 
                                   ON cc.post_id = cp.id AND cc.contents ILIKE :word   
                         LEFT JOIN community_posts_reactions cpr ON cpr.post_id = cp.id
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND (
                          cp.title ILIKE :word        
                          OR cp.contents ILIKE :word  
                          OR cc.id IS NOT NULL        
                      )
                GROUP BY cp.id, ui.nickname, cpv.view_count, cp.create_time
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
                       json_agg(
                           json_build_object(
                               'id', c.id,
                               'contents', c.contents,
                               'user_email', c.user_email,
                               'create_time', c.create_time,
                               'update_time', c.update_time
                           )
                       ) FILTER (WHERE c.id IS NOT NULL) AS comments
                FROM community_posts cp
                         LEFT JOIN user_info ui ON cp.user_email = ui.email
                         LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                         LEFT JOIN comment_count cc ON cc.post_id = cp.id
                         LEFT JOIN reaction_sum r ON r.post_id = cp.id
                         LEFT JOIN community_comments c ON c.post_id = cp.id AND c.contents ILIKE :word 
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND (
                          cp.title ILIKE :word 
                          OR cp.contents ILIKE :word 
                          OR c.id IS NOT NULL
                      )
                GROUP BY cp.id, ui.nickname, cpv.view_count, cp.create_time, cc.comment_count, r.reaction_score
                ORDER BY cp.create_time DESC
                LIMIT :limit OFFSET :offset
    """,
            "all": """
        SELECT cp.id::text AS id,
               cp.slug,
               cp.user_email,
               cp.category,
               ui.nickname,
               cp.title,
               cp.contents,
               cpv.view_count,
               cc_all.comment_count,
               COALESCE(cpr_sum.reaction_score, 0) AS reaction_score,
               cp.thumbnail,
               cp.delete_by_user,
               cp.delete_by_admin,
               cp.create_time,
               cp.update_time,
               json_build_object(
                   'id', cc.id,
                   'contents', cc.contents,
                   'user_email', cc.user_email,
                   'create_time', cc.create_time,
                   'update_time', cc.update_time
               ) AS comment
        FROM community_posts cp
                 LEFT JOIN user_info ui ON cp.user_email = ui.email
                 LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                 LEFT JOIN (
                     SELECT post_id, COUNT(*) AS comment_count
                     FROM community_comments
                     GROUP BY post_id
                 ) cc_all ON cc_all.post_id = cp.id
                 LEFT JOIN (
                     SELECT post_id,
                            SUM(CASE
                                    WHEN reaction_type = 1 THEN 1
                                    WHEN reaction_type = 0 THEN -1
                                    ELSE 0 END) AS reaction_score
                     FROM community_posts_reactions
                     GROUP BY post_id
                 ) cpr_sum ON cpr_sum.post_id = cp.id
                 LEFT JOIN community_comments cc ON cc.post_id = cp.id
        WHERE cp.delete_by_admin = false
          AND cp.delete_by_user = false
          AND (
                cp.contents ILIKE :word 
                OR cc.contents ILIKE :word 
              )
        ORDER BY cp.create_time DESC
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
                       json_agg(
                           json_build_object(
                               'id', c.id,
                               'contents', c.contents,
                               'user_email', c.user_email,
                               'create_time', c.create_time,
                               'update_time', c.update_time
                           )
                       ) FILTER (WHERE c.id IS NOT NULL) AS comments
                FROM community_posts cp
                         LEFT JOIN user_info ui ON cp.user_email = ui.email
                         LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                         LEFT JOIN comment_count cc ON cc.post_id = cp.id
                         LEFT JOIN reaction_sum r ON r.post_id = cp.id
                         LEFT JOIN community_comments c 
                                   ON c.post_id = cp.id 
                                  AND c.user_email ILIKE :word 
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND (
                          c.id IS NOT NULL
                          OR cp.user_email ILIKE :word 
                      )
                GROUP BY cp.id, ui.nickname, cpv.view_count, cp.create_time, cc.comment_count, r.reaction_score
                ORDER BY cp.create_time DESC
                LIMIT :limit OFFSET :offset
    """,
        }

        return queries[search_type]

    @staticmethod
    def get_search_total_count_sql(search_type: str):
        queries = {
            "title": """
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
                SELECT count(*)
                FROM community_posts cp
                         LEFT JOIN user_info ui ON cp.user_email = ui.email
                         LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                         LEFT JOIN comment_count cc ON cc.post_id = cp.id
                         LEFT JOIN reaction_sum r ON r.post_id = cp.id
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND cp.title ILIKE :word 
            """,
            "titleContent": """
                SELECT count(*)
                FROM community_posts cp
                         LEFT JOIN user_info ui ON cp.user_email = ui.email
                         LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                         LEFT JOIN community_comments cc 
                                   ON cc.post_id = cp.id AND cc.contents ILIKE :word   
                         LEFT JOIN community_posts_reactions cpr ON cpr.post_id = cp.id
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND (
                          cp.title ILIKE :word        
                          OR cp.contents ILIKE :word  
                          OR cc.id IS NOT NULL        
                      )
                GROUP BY cp.id, ui.nickname, cpv.view_count, cp.create_time
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
                SELECT count(*)
                FROM community_posts cp
                         LEFT JOIN user_info ui ON cp.user_email = ui.email
                         LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                         LEFT JOIN comment_count cc ON cc.post_id = cp.id
                         LEFT JOIN reaction_sum r ON r.post_id = cp.id
                         LEFT JOIN community_comments c ON c.post_id = cp.id AND c.contents ILIKE :word 
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND (
                          cp.title ILIKE :word 
                          OR cp.contents ILIKE :word 
                          OR c.id IS NOT NULL
                      )
                GROUP BY cp.id, ui.nickname, cpv.view_count, cp.create_time, cc.comment_count, r.reaction_score
    """,
            "all": """
        SELECT count(*)
        FROM community_posts cp
                 LEFT JOIN user_info ui ON cp.user_email = ui.email
                 LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                 LEFT JOIN (
                     SELECT post_id, COUNT(*) AS comment_count
                     FROM community_comments
                     GROUP BY post_id
                 ) cc_all ON cc_all.post_id = cp.id
                 LEFT JOIN (
                     SELECT post_id,
                            SUM(CASE
                                    WHEN reaction_type = 1 THEN 1
                                    WHEN reaction_type = 0 THEN -1
                                    ELSE 0 END) AS reaction_score
                     FROM community_posts_reactions
                     GROUP BY post_id
                 ) cpr_sum ON cpr_sum.post_id = cp.id
                 LEFT JOIN community_comments cc ON cc.post_id = cp.id
        WHERE cp.delete_by_admin = false
          AND cp.delete_by_user = false
          AND (
                cp.contents ILIKE :word 
                OR cc.contents ILIKE :word 
              )
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
                SELECT count(*)
                FROM community_posts cp
                         LEFT JOIN user_info ui ON cp.user_email = ui.email
                         LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                         LEFT JOIN comment_count cc ON cc.post_id = cp.id
                         LEFT JOIN reaction_sum r ON r.post_id = cp.id
                         LEFT JOIN community_comments c 
                                   ON c.post_id = cp.id 
                                  AND c.user_email ILIKE :word 
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND (
                          c.id IS NOT NULL
                          OR cp.user_email ILIKE :word 
                      )
                GROUP BY cp.id, ui.nickname, cpv.view_count, cp.create_time, cc.comment_count, r.reaction_score
    """,
        }

        return queries[search_type]
