from fastapi import UploadFile, File, HTTPException
from api.community.community_res_models import CommunityPosts, CommunityPostsView, CommunityPostsReactions, CommunityPostsHotIssue
from api.community.community_req_models import CreateCommunity, UpdateCommunity, ViewCount, PostReaction
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
        object_name = (
            f"{folder_name}/{timestamp}_{filename_wo_ext}.webp"  # ✅ .webp 확장자로 저장
        )
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
                    update_time=datetime.now()
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
