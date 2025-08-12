import math
from sqlalchemy import func, case
from fastapi import UploadFile, File, HTTPException
from api.community.community_res_models import (
    CommunityPosts,
    CommunityPostsView,
    CommunityPostsReactions,
    CommunityPostsHotIssue,
)
from api.community.community_req_models import (
    CreateCommunity,
    UpdateCommunity,
    ViewCount,
    PostReaction,
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
            limit = 20
            offset = (page_num - 1) * limit
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 좋아요-싫어요 계산식
                reaction_score_expr = func.greatest(
                    func.coalesce(
                        func.sum(
                            case(
                                (CommunityPostsReactions.reaction_type == 1, 1),
                                else_=0,
                            )
                        )
                        - func.sum(
                            case(
                                (CommunityPostsReactions.reaction_type == 0, 1),
                                else_=0,
                            )
                        ),
                        0,
                    ),
                    0,
                )

                # 기본 SELECT 구성
                query = (
                    s.query(
                        CommunityPosts,
                        reaction_score_expr.label("reaction_score"),
                        func.coalesce(CommunityPostsView.view_count, 0).label(
                            "view_count"
                        ),
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

                # 카테고리별 처리
                if category == "issue":
                    query = (
                        query.join(CommunityPostsHotIssue.post)
                        .group_by(
                            CommunityPosts.id,
                            CommunityPostsView.view_count,
                            CommunityPostsHotIssue.issue_time,
                        )
                        .order_by(CommunityPostsHotIssue.issue_time.desc())
                    )
                elif category == "all":
                    query = query.group_by(
                        CommunityPosts.id,
                        CommunityPostsView.view_count,
                        CommunityPosts.create_time,
                    ).order_by(CommunityPosts.create_time.desc())
                else:
                    query = (
                        query.filter(CommunityPosts.category == category)
                        .group_by(
                            CommunityPosts.id,
                            CommunityPostsView.view_count,
                            CommunityPosts.create_time,
                        )
                        .order_by(CommunityPosts.create_time.desc())
                    )

                # 검색 조건
                if word:
                    if search_type == "title":
                        query = query.filter(CommunityPosts.title.contains(word))
                    elif search_type == "title_content":
                        query = query.filter(
                            (CommunityPosts.title.contains(word))
                            | (CommunityPosts.contents.contains(word))
                        )

                total = query.count()
                posts = query.limit(limit).offset(offset).all()
                max_page_count = math.ceil(total / limit) if total > 0 else 1

                # 아 괜히 snowflake id 썼나 번거롭네;;;
                # id / post_id만 문자열로 변환
                result_posts = []
                for post, reaction_score, view_count in posts:
                    post_dict = post.__dict__.copy()
                    post_dict.pop("_sa_instance_state", None)
                    post_dict["id"] = str(post_dict["id"])
                    post_dict["reaction_score"] = reaction_score
                    post_dict["view_count"] = view_count
                    result_posts.append(post_dict)

                issue_posts = s.query(CommunityPosts).join(CommunityPostsHotIssue.post).order_by(CommunityPostsHotIssue.issue_time.desc()).limit(5).all()

                result_issue_posts = []
                for post in issue_posts:
                    post_dict = post.__dict__.copy()
                    # 내부에 _sa_instance_state 같은 SQLAlchemy 내부 속성 제거
                    post_dict.pop("_sa_instance_state", None)

                    # id 변환
                    if "id" in post_dict:
                        post_dict["id"] = str(post_dict["id"])
                    result_issue_posts.append(post_dict)

                return {
                    "total": total,
                    "max_page_count": max_page_count,
                    "posts": result_posts,
                }

                return {
                    "total": total,
                    "max_page_count": max_page_count,
                    "posts": result_posts,
                    "issue_posts": result_issue_posts
                }
        except Exception as e:
            print("오류 발생:", e)
            return None
