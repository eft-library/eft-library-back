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
from sqlalchemy import text


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
    def get_posts(category: str, page_num: int, word: str, search_type):
        try:
            limit, offset = 20, (page_num - 1) * 20
            session = DataBaseConnector.create_session_factory()

            with session() as s:
                # 1. 기본 쿼리 생성
                query = CommunityFunction.build_get_post_base_query(s)

                # 2. 카테고리별 조건 적용
                query = CommunityFunction.apply_category_filter(query, category)

                # 3. 검색 조건 적용
                query = CommunityFunction.apply_search_filter(query, word, search_type)

                # 4. 게시글 목록 + 페이징 처리
                total, max_page_count, result_posts = (
                    CommunityFunction.fetch_and_format_results(query, limit, offset)
                )

                # 5. issue_posts & notice_posts 조회
                result_issue_posts = CommunityFunction.fetch_issue_posts(s)
                notice_posts = CommunityFunction.fetch_notice_posts(s)

                return {
                    "total": total,
                    "max_page_count": max_page_count,
                    "posts": result_posts,
                    "issue_posts": result_issue_posts,
                    "notice_posts": notice_posts,
                }

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_detail_posts(post_id_slug: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                post_id = CommunityFunction.parse_id_and_slug(post_id_slug)
                post_detail_query = text(CommunityUtil.get_post_detail())
                post_detail_param = {"post_id": post_id, "user_email": user_email}
                post_detail_result = s.execute(post_detail_query, post_detail_param)
                post_detail = [dict(row) for row in post_detail_result.mappings()]

                return {"detail": post_detail[0]}
        except Exception as e:
            print("오류 발생:", e)
            return None
