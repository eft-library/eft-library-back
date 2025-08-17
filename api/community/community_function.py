import re

import math
from sqlalchemy import func, case

from api.community.community_res_models import (
    CommunityPosts,
    CommunityPostsHotIssue,
    CommunityPostsView,
    CommunityPostsReactions,
    UserFollows,
    CommunityPostsBookmark,
)
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
    def fetch_notice_posts(s):
        return s.query(Notice).order_by(Notice.update_time.desc()).limit(5).all()

    @staticmethod
    def parse_id_and_slug(value: str):
        try:
            id_str, slug = value.split("-", 1)  # 1번만 split (slug에 '-'가 있어도 유지)
            return int(id_str)
        except ValueError:
            raise ValueError(f"잘못된 형식입니다: {value}")
