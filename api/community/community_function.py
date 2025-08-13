import re

import math
from sqlalchemy import func, case

from api.community.community_res_models import (
    CommunityPosts,
    CommunityPostsHotIssue,
    CommunityPostsView,
    CommunityPostsReactions,
)


class CommunityFunction:

    @staticmethod
    def extract_thumbnail_img(html):
        # 정규 표현식을 사용하여 첫 번째 <img> 태그의 src 값 찾아서 썸네일 반환
        match = re.search(r'<img[^>]+src="([^"]+)"', html)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def build_get_post_base_query(session):
        reaction_score_expr = func.greatest(
            func.coalesce(
                func.sum(case((CommunityPostsReactions.reaction_type == 1, 1), else_=0))
                - func.sum(
                    case((CommunityPostsReactions.reaction_type == 0, 1), else_=0)
                ),
                0,
            ),
            0,
        )

        return (
            session.query(
                CommunityPosts,
                reaction_score_expr.label("reaction_score"),
                func.coalesce(CommunityPostsView.view_count, 0).label("view_count"),
            )
            .outerjoin(
                CommunityPostsReactions,
                CommunityPosts.id == CommunityPostsReactions.post_id,
            )
            .outerjoin(
                CommunityPostsView,
                CommunityPosts.id == CommunityPostsView.post_id,
            )
        )

    @staticmethod
    def apply_category_filter(query, category):
        if category == "issue":
            return (
                query.join(CommunityPostsHotIssue.post)
                .group_by(
                    CommunityPosts.id,
                    CommunityPostsView.view_count,
                    CommunityPostsHotIssue.issue_time,
                )
                .order_by(CommunityPostsHotIssue.issue_time.desc())
            )
        elif category == "all":
            return query.group_by(
                CommunityPosts.id,
                CommunityPostsView.view_count,
                CommunityPosts.create_time,
            ).order_by(CommunityPosts.create_time.desc())
        else:
            return (
                query.filter(CommunityPosts.category == category)
                .group_by(
                    CommunityPosts.id,
                    CommunityPostsView.view_count,
                    CommunityPosts.create_time,
                )
                .order_by(CommunityPosts.create_time.desc())
            )

    @staticmethod
    def apply_search_filter(query, word, search_type):
        if not word:
            return query

        if search_type == "title":
            return query.filter(CommunityPosts.title.contains(word))
        elif search_type == "title_content":
            return query.filter(
                (CommunityPosts.title.contains(word))
                | (CommunityPosts.contents.contains(word))
            )
        return query

    @staticmethod
    def fetch_and_format_results(query, limit, offset):
        total = query.count()
        posts = query.limit(limit).offset(offset).all()
        max_page_count = math.ceil(total / limit) if total > 0 else 1

        result_posts = []
        for post, reaction_score, view_count in posts:
            post_dict = post.__dict__.copy()
            post_dict.pop("_sa_instance_state", None)
            post_dict["id"] = str(post_dict["id"])
            post_dict["reaction_score"] = reaction_score
            post_dict["view_count"] = view_count
            result_posts.append(post_dict)

        return {
            "total": total,
            "max_page_count": max_page_count,
            "posts": result_posts,
        }
