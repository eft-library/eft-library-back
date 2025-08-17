from PIL.ImageChops import offset
from fastapi import UploadFile, File, HTTPException
from api.community.community_res_models import (
    CommunityPosts,
    CommunityPostsView,
    CommunityPostsReactions,
    CommunityPostsBookmark,
    UserFollows,
)
from api.community.util import CommunityUtil
from api.community.community_req_models import (
    CreateCommunity,
)
from database import DataBaseConnector
from util.snowflake_id import SnowflakeGenerator
from slugify import slugify
import os
from api.community.community_function import CommunityFunction
from dotenv import load_dotenv
from datetime import datetime
from PIL import Image
from minio import Minio
from minio.error import S3Error
import io
from sqlalchemy import text, case, and_

load_dotenv()
snowflake = SnowflakeGenerator(datacenter_id=1, worker_id=1)
bucket_name = "eftlibrary"
folder_name = "tkl_community/posts_image"

minio_client = Minio(
    os.getenv("MINIO_ENDPOINT").replace("http://", "").replace("https://", ""),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False,
)


class CommunityService:

    @staticmethod
    def upload_image(file: UploadFile = File(...)):
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        filename_wo_ext = os.path.splitext(file.filename.replace(" ", "_"))[0]
        object_name = f"{folder_name}/{timestamp}_{filename_wo_ext}.webp"  # ✅ .webp 확장자로 저장
        try:
            # 1. 이미지 열기 (UploadFile -> PIL Image)
            image = Image.open(file.file)

            # 2. 리사이징 (선택적): 너무 큰 이미지 줄이기
            max_size = (1200, 1200)
            image.thumbnail(max_size)

            # 3. WebP로 저장
            buffer = io.BytesIO()
            image.save(buffer, format="WEBP", quality=80, method=6)  # ✅ 압축률 조정
            buffer.seek(0)

            # 4. MinIO에 업로드
            minio_client.put_object(
                bucket_name,
                object_name,
                data=buffer,
                length=buffer.getbuffer().nbytes,
                content_type="image/webp",
            )

        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"MinIO 업로드 실패: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"이미지 처리 실패: {e}")

        url = f"https://image.eftlibrary.com/{bucket_name}/{object_name}"
        result = {"image_url": url}

        return result

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
                    delete_by_user=False,
                    delete_by_admin=False,
                    create_time=datetime.now(),
                    update_time=datetime.now(),
                )
                s.add(new_post)

                # view count 1 생성
                new_view_count = CommunityPostsView(post_id=new_id, view_count=1)
                s.add(new_view_count)
                s.commit()

                # 리턴은 snowflake-slug
                return {"url": f"{new_id}-{slug}"}
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_posts(category: str, page_num: int):
        try:
            limit, offset = 20, (page_num - 1) * 20
            session = DataBaseConnector.create_session_factory()

            with session() as s:
                if category == "issue":
                    get_post_query = text(CommunityUtil.get_posts_with_issue())
                    get_post_count_query = text(CommunityUtil.get_post_issue_count())
                else:
                    get_post_query = text(CommunityUtil.get_posts_with_category())
                    get_post_count_query = text(CommunityUtil.get_post_category_count())
                get_post_params = {
                    "limit": limit,
                    "offset": offset,
                    "category": category,
                }
                get_post_data_result = s.execute(get_post_query, get_post_params)
                get_post_data = [dict(row) for row in get_post_data_result.mappings()]
                get_post_count_result = s.execute(
                    get_post_count_query, {"category": category}
                )
                total = get_post_count_result.scalar()

                max_page_count = (total + limit - 1) // limit

                # issue_posts & notice_posts 조회
                result_issue_posts = CommunityFunction.fetch_issue_posts(s)
                notice_posts = CommunityFunction.fetch_notice_posts(s)

                return {
                    "total": total,
                    "max_page_count": max_page_count,
                    "posts": get_post_data,
                    "issue_posts": result_issue_posts,
                    "notice_posts": notice_posts,
                }

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_detail_post(post_id_slug: str, user_email: str, page_category: str):
        try:
            limit = 20
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                post_id = CommunityFunction.parse_id_and_slug(post_id_slug)

                # 게시글 상세 정보
                post_detail_query = text(CommunityUtil.get_post_detail())
                post_detail_param = {"post_id": post_id, "user_email": user_email}
                post_detail_result = s.execute(post_detail_query, post_detail_param)
                post_detail = [dict(row) for row in post_detail_result.mappings()]

                result_issue_posts = CommunityFunction.fetch_issue_posts(s)
                notice_posts = CommunityFunction.fetch_notice_posts(s)

                # 작성자 정보
                author_meta_data_query = text(
                    CommunityUtil.get_detail_author_meta_data()
                )
                author_meta_data_param = {"post_id": post_id, "user_email": user_email}
                author_meta_data_result = s.execute(
                    author_meta_data_query, author_meta_data_param
                )
                author_meta_data = [
                    dict(row) for row in author_meta_data_result.mappings()
                ]

                # 게시글 목록
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

                get_post_current_page_num = s.execute(
                    get_post_current_page_num_query,
                    {"category": page_category, "post_id": post_id},
                )
                current_page_num = (get_post_current_page_num - 1) / limit + 1

                offset = (current_page_num - 1) * 20

                get_post_params = {
                    "limit": limit,
                    "offset": offset,
                    "category": page_category,
                }
                get_post_data_result = s.execute(get_post_query, get_post_params)
                get_post_data = [dict(row) for row in get_post_data_result.mappings()]

                # total, max_pages, current_page_num 필요
                get_post_count_result = s.execute(
                    get_post_count_query, {"category": page_category}
                )
                total = get_post_count_result.scalar()

                max_page_count = (total + limit - 1) // limit

                return {
                    "post_detail": post_detail[0],
                    "issue_posts": result_issue_posts,
                    "notice_posts": notice_posts,
                    "author_detail": author_meta_data[0],
                    "posts": {
                        "total": total,
                        "max_page_count": max_page_count,
                        "posts": get_post_data,
                        "current_page_num": current_page_num,
                    },
                }
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_detail_post_meta_data(post_id_slug: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                post_id = CommunityFunction.parse_id_and_slug(post_id_slug)
                post_detail_query = text(CommunityUtil.get_post_detail_meta_data())
                post_detail_param = {"post_id": post_id, "user_email": user_email}
                post_detail_result = s.execute(post_detail_query, post_detail_param)
                post_detail = [dict(row) for row in post_detail_result.mappings()]

                return post_detail[0]
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def like_post(post_id: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                bigint_post_id = int(post_id)

                # 기존 reaction 조회
                reaction = (
                    s.query(CommunityPostsReactions)
                    .filter(
                        CommunityPostsReactions.post_id == bigint_post_id,
                        CommunityPostsReactions.user_email == user_email,
                    )
                    .first()
                )

                if reaction:
                    # 기존 값에 따라 변경
                    if reaction.reaction_type == 0:
                        reaction.reaction_type = 1
                    elif reaction.reaction_type == 1:
                        reaction.reaction_type = -1
                    elif reaction.reaction_type == -1:
                        reaction.reaction_type = 1
                    # update_time 갱신
                    reaction.update_time = datetime.now()
                else:
                    # 없으면 새로 생성 (1로 시작)
                    reaction = CommunityPostsReactions(
                        post_id=bigint_post_id,
                        user_email=user_email,
                        reaction_type=1,
                        update_time=datetime.now(),
                    )
                    s.add(reaction)

                s.commit()
                return {"result": reaction.reaction_type}  # 현재 상태 반환

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def dislike_post(post_id: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                bigint_post_id = int(post_id)

                # 기존 reaction 조회
                reaction = (
                    s.query(CommunityPostsReactions)
                    .filter(
                        CommunityPostsReactions.post_id == bigint_post_id,
                        CommunityPostsReactions.user_email == user_email,
                    )
                    .first()
                )

                if reaction:
                    # 기존 값에 따라 변경
                    if reaction.reaction_type == 0:
                        reaction.reaction_type = -1
                    elif reaction.reaction_type == 1:
                        reaction.reaction_type = 0
                    elif reaction.reaction_type == -1:
                        reaction.reaction_type = 0
                    # update_time 갱신
                    reaction.update_time = datetime.now()
                else:
                    # 없으면 새로 생성 (0으로 시작)
                    reaction = CommunityPostsReactions(
                        post_id=bigint_post_id,
                        user_email=user_email,
                        reaction_type=0,
                        update_time=datetime.now(),
                    )
                    s.add(reaction)

                s.commit()
                return {"result": reaction.reaction_type}  # 현재 상태 반환

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def bookmark_post(post_id: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                bigint_post_id = int(post_id)

                # 기존 bookmark 조회 (ORM 방식)
                bookmark = (
                    s.query(CommunityPostsBookmark)
                    .filter(
                        CommunityPostsBookmark.post_id == bigint_post_id,
                        CommunityPostsBookmark.user_email == user_email,
                    )
                    .first()
                )

                if bookmark:
                    # 있으면 제거
                    s.delete(bookmark)
                else:
                    # 없으면 새로 생성
                    new_bookmark = CommunityPostsBookmark(
                        post_id=bigint_post_id,
                        user_email=user_email,
                        create_time=datetime.now(),
                    )
                    s.add(new_bookmark)

                s.commit()
                return {"result": 1}  # 성공

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def toggle_follow(author_email: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 현재 팔로우 상태 확인
                follower_status = (
                    s.query(UserFollows)
                    .filter(
                        UserFollows.follower_email == author_email,
                        UserFollows.following_email == user_email,
                    )
                    .first()
                )

                if follower_status:
                    # 이미 팔로우 중이면 → 언팔로우
                    s.delete(follower_status)
                else:
                    # 팔로우 중이 아니면 → 팔로우
                    new_follow = UserFollows(
                        follower_email=author_email,
                        following_email=user_email,
                        create_time=datetime.now(),
                    )
                    s.add(new_follow)

                s.commit()
                return {"result": 1}

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def check_user_following(author_email: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                check_follow_query = text(CommunityUtil.check_follow())
                check_follow_param = {
                    "author_email": author_email,
                    "user_email": user_email,
                }
                check_follow_result = s.execute(check_follow_query, check_follow_param)
                check_follow = [dict(row) for row in check_follow_result.mappings()]

                return check_follow[0]
        except Exception as e:
            print("오류 발생:", e)
            return None
