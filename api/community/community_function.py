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
    def fetch_issue_posts(s):
        issue_posts = (
            s.query(CommunityPosts)
            .join(
                CommunityPostsHotIssue,
                CommunityPosts.id == CommunityPostsHotIssue.post_id,
            )
            .order_by(CommunityPostsHotIssue.issue_time.desc())
            .limit(5)
            .all()
        )

        result_issue_posts = []
        for post in issue_posts:
            post_dict = post.__dict__.copy()
            post_dict.pop("_sa_instance_state", None)
            post_dict["id"] = str(post_dict["id"])
            result_issue_posts.append(post_dict)

        return result_issue_posts

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
            get_post_query = text(CommunityUtil.get_posts_with_category())
            get_post_count_query = text(CommunityUtil.get_post_category_count())
            get_post_current_page_num_query = text(
                CommunityUtil.get_current_post_category_page_num()
            )

        # 현재 페이지 번호
        current_page_num_result = session.execute(
            get_post_current_page_num_query,
            {"category": page_category, "post_id": post_id},
        )
        current_page_num = (current_page_num_result.scalar() - 1) // limit + 1

        # 페이징 offset
        offset = (current_page_num - 1) * limit

        # 게시글 목록
        posts_result = session.execute(
            get_post_query,
            {"limit": limit, "offset": offset, "category": page_category},
        )
        posts = [dict(row) for row in posts_result.mappings()]

        # 전체 개수
        total_result = session.execute(
            get_post_count_query, {"category": page_category}
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
        return s.query(Notice).order_by(Notice.update_time.desc()).limit(5).all()

    @staticmethod
    def parse_id_and_slug(value: str):
        try:
            id_str, slug = value.split("-", 1)  # 1번만 split (slug에 '-'가 있어도 유지)
            return int(id_str)
        except ValueError:
            raise ValueError(f"잘못된 형식입니다: {value}")
