from certifi import contents
from unicodedata import category

from api.community.community_res_models import CommunityPosts, CommunityPostsView, CommunityPostsReactions, CommunityPostsHotIssue
from api.community.community_req_models import CreateCommunity, UpdateCommunity, ViewCount, PostReaction
from database import DataBaseConnector
from util.snowflake_id import SnowflakeGenerator
from slugify import slugify
from api.community.community_function import CommunityFunction


snowflake = SnowflakeGenerator(datacenter_id=1, worker_id=1)

class CommunityService:

    @staticmethod
    def create_posts(post_info: CreateCommunity, user_email: str):
        # snowflake 생성
        new_id = snowflake.generate_id()
        # slug 생성
        slug = slugify(post_info.title)
        # thumbnail 추출
        thumbnail = CommunityFunction.extract_thumbnail_img(post_info.contents)

        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 삽입
                new_post = CommunityPosts(
                    id=new_id,
                    slug=slug,
                    user_email=user_email,
                    category=post_info.category,
                    title=post_info.title,
                    contents=post_info.contents,
                    thumbnail=thumbnail,
                )
                s.add(new_post)

                # view count 1 생성
                new_view_count = ViewCount(id=new_id, user_id=user_email)
                s.add(new_view_count)
                s.commit()

                # 리턴은 snowflake-slug
                return {"url": f"{new_id}-{slug}"}
            pass
        except Exception as e:
            print("오류 발생:", e)
            return None
