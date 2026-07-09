from datetime import datetime
import io
import json
import logging
import os
from typing import Optional

from fastapi import File, HTTPException, UploadFile
from minio import Minio
from minio.error import S3Error
from PIL import Image
from slugify import slugify
from sqlalchemy import text

from api.community.community_function import CommunityFunctionV3
from api.community.community_req_models import CreateCommunity, FollowUser, ReqPostReport
from api.community.community_res_models import (
    CommunityPostsBookmarkV3,
    CommunityPostsReactionsV3,
    CommunityPostsV3,
    CommunityPostsViewV3,
    PostReportV3,
    UserFollowsV3,
)
from api.community.util import CommunityUtilV3
from database import V3Database
from dotenv import load_dotenv
from util.kafka_producer import produce_notification
from util.snowflake_id import SnowflakeGenerator

logger = logging.getLogger("api.community")

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


class CommunityServiceV3:
    @staticmethod
    def upload_image_v3(file: UploadFile = File(...)):
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        filename_wo_ext = os.path.splitext(file.filename.replace(" ", "_"))[0]
        object_name = f"{folder_name}/{timestamp}_{filename_wo_ext}.webp"
        try:
            image = Image.open(file.file)
            image.thumbnail((1200, 1200))
            buffer = io.BytesIO()
            image.save(buffer, format="WEBP", quality=80, method=6)
            buffer.seek(0)
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

        return {"image_url": f"https://image.eftlibrary.com/{bucket_name}/{object_name}"}

    @staticmethod
    def create_posts_v3(post_info: CreateCommunity, user_email: str):
        try:
            new_id = snowflake.generate_id()
            slug = slugify(post_info.title)
            thumbnail = CommunityFunctionV3.extract_thumbnail_img(post_info.contents)

            with V3Database.SessionLocal() as s:
                s.add(
                    CommunityPostsV3(
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
                )
                s.add(CommunityPostsViewV3(post_id=new_id, view_count=1))
                s.commit()

            produce_notification(
                json.dumps(
                    {
                        "url": f"{new_id}-{slug}",
                        "title": post_info.title,
                        "author_email": user_email,
                        "author_nickname": post_info.nickname,
                        "noti_type": "create_post",
                    }
                )
            )
            return {"url": f"{new_id}-{slug}"}
        except Exception as e:
            logger.error(
                f"create_posts_v3: {post_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_posts_v3(category: str, page_num: int, user_email: Optional[str] = None):
        try:
            limit, offset = 20, (page_num - 1) * 20
            with V3Database.SessionLocal() as s:
                if category == "issue":
                    posts_sql = text(CommunityUtilV3.get_posts_with_issue())
                    count_sql = text(CommunityUtilV3.get_post_issue_count())
                elif category == "all":
                    posts_sql = text(CommunityUtilV3.get_posts_with_all())
                    count_sql = text(CommunityUtilV3.get_post_all_count())
                else:
                    posts_sql = text(CommunityUtilV3.get_posts_with_category())
                    count_sql = text(CommunityUtilV3.get_post_category_count())
                params = {
                    "limit": limit,
                    "offset": offset,
                    "category": category,
                    "user_email": user_email,
                }
                posts = [dict(row) for row in s.execute(posts_sql, params).mappings()]
                total = s.execute(count_sql, params).scalar() or 0
                return {
                    "total": total,
                    "max_page_count": (total + limit - 1) // limit,
                    "posts": posts,
                }
        except Exception as e:
            logger.error(f"get_posts_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def get_detail_post_v3(post_id_slug: str, user_email: str, page_category: str):
        try:
            with V3Database.SessionLocal() as s:
                post_id = CommunityFunctionV3.parse_id_and_slug(post_id_slug)
                return {
                    "post_detail": CommunityFunctionV3.fetch_post_detail(
                        s, post_id, user_email
                    ),
                    "author_detail": CommunityFunctionV3.fetch_author_meta(
                        s, post_id, user_email
                    ),
                    "posts": CommunityFunctionV3.fetch_posts_with_paging(
                        s, post_id, page_category, user_email
                    ),
                }
        except Exception as e:
            logger.error(
                f"get_detail_post_v3: {post_id_slug}, {page_category}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_side_info_v3(user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                issue_posts = s.execute(
                    text(CommunityUtilV3.get_posts_with_issue()),
                    {"limit": 5, "offset": 0, "user_email": user_email},
                )
                return {
                    "issue_posts": [dict(row) for row in issue_posts.mappings()],
                    "notice_posts": CommunityFunctionV3.fetch_notice_posts(s),
                }
        except Exception as e:
            logger.error(f"get_side_info_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def get_detail_post_meta_data_v3(post_id_slug: str, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                post_id = CommunityFunctionV3.parse_id_and_slug(post_id_slug)
                result = s.execute(
                    text(CommunityUtilV3.get_post_detail_meta_data()),
                    {"post_id": post_id, "user_email": user_email},
                )
                return [dict(row) for row in result.mappings()][0]
        except Exception as e:
            logger.error(
                f"get_detail_post_meta_data_v3: {post_id_slug}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def like_post_v3(post_id: str, user_email: str):
        return CommunityServiceV3._toggle_post_reaction_v3(int(post_id), user_email, 1)

    @staticmethod
    def dislike_post_v3(post_id: str, user_email: str):
        return CommunityServiceV3._toggle_post_reaction_v3(int(post_id), user_email, 0)

    @staticmethod
    def _toggle_post_reaction_v3(post_id: int, user_email: str, next_value: int):
        try:
            with V3Database.SessionLocal() as s:
                result = s.execute(
                    text(
                        """
                        INSERT INTO community_posts_reactions
                            (post_id, user_email, reaction_type, update_time)
                        VALUES
                            (:post_id, :user_email, :next_value, :update_time)
                        ON CONFLICT (post_id, user_email) DO UPDATE
                        SET reaction_type = CASE
                                WHEN :next_value = 1 THEN
                                    CASE
                                        WHEN COALESCE(community_posts_reactions.reaction_type, -1) IN (0, -1)
                                        THEN 1
                                        ELSE -1
                                    END
                                ELSE
                                    CASE
                                        WHEN COALESCE(community_posts_reactions.reaction_type, -1) IN (1, -1)
                                        THEN 0
                                        ELSE -1
                                    END
                            END,
                            update_time = excluded.update_time
                        RETURNING reaction_type;
                        """
                    ),
                    {
                        "post_id": post_id,
                        "user_email": user_email,
                        "next_value": next_value,
                        "update_time": datetime.now(),
                    },
                )
                reaction_type = result.scalar_one()
                s.commit()
                return {"result": reaction_type}
        except Exception as e:
            logger.error(f"toggle_post_reaction_v3: {post_id}, error: {e}", exc_info=True)
            return None

    @staticmethod
    def bookmark_post_v3(post_id: str, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                bigint_post_id = int(post_id)
                deleted = s.execute(
                    text(
                        """
                        DELETE FROM community_posts_bookmark
                        WHERE email = :email AND post_id = :post_id
                        RETURNING 1;
                        """
                    ),
                    {"email": user_email, "post_id": bigint_post_id},
                )
                if deleted.scalar() is None:
                    s.execute(
                        text(
                            """
                            INSERT INTO community_posts_bookmark
                                (email, post_id, create_time)
                            VALUES
                                (:email, :post_id, :create_time)
                            ON CONFLICT (email, post_id) DO NOTHING;
                            """
                        ),
                        {
                            "email": user_email,
                            "post_id": bigint_post_id,
                            "create_time": datetime.now(),
                        },
                    )
                s.commit()
                return {"result": 1}
        except Exception as e:
            logger.error(f"bookmark_post_v3: {post_id}, error: {e}", exc_info=True)
            return None

    @staticmethod
    def toggle_follow_v3(request_info: FollowUser, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                deleted = s.execute(
                    text(
                        """
                        DELETE FROM user_follows
                        WHERE follower_email = :follower_email
                          AND following_email = :following_email
                        RETURNING 1;
                        """
                    ),
                    {
                        "follower_email": request_info.following_user_email,
                        "following_email": user_email,
                    },
                )
                if deleted.scalar() is None:
                    inserted = s.execute(
                        text(
                            """
                            INSERT INTO user_follows
                                (follower_email, following_email, create_time)
                            VALUES
                                (:follower_email, :following_email, :create_time)
                            ON CONFLICT (follower_email, following_email) DO NOTHING
                            RETURNING 1;
                            """
                        ),
                        {
                            "follower_email": request_info.following_user_email,
                            "following_email": user_email,
                            "create_time": datetime.now(),
                        },
                    )
                    if (
                        inserted.scalar() is not None
                        and request_info.following_user_email != user_email
                    ):
                        produce_notification(
                            json.dumps(
                                {
                                    "follower_email": request_info.following_user_email,
                                    "following_email": user_email,
                                    "author_nickname": request_info.nickname,
                                    "noti_type": "follow_user",
                                }
                            )
                        )
                s.commit()
                return {"result": 1}
        except Exception as e:
            logger.error(
                f"toggle_follow_v3: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def check_user_following_v3(author_email: str, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                result = s.execute(
                    text(CommunityUtilV3.check_follow()),
                    {"author_email": author_email, "user_email": user_email},
                )
                return [dict(row) for row in result.mappings()][0]
        except Exception as e:
            logger.error(
                f"check_user_following_v3: {author_email}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def update_post_v3(
        post_id: str,
        slug: str,
        page_category: str,
        title: str,
        contents: str,
        user_email: str,
    ):
        new_slug = slugify(title)
        thumbnail = CommunityFunctionV3.extract_thumbnail_img(contents)
        try:
            with V3Database.SessionLocal() as s:
                post = s.query(CommunityPostsV3).filter(CommunityPostsV3.id == int(post_id)).first()
                if post and post.user_email == user_email:
                    post.update_time = datetime.now()
                    post.title = title
                    post.contents = contents
                    post.thumbnail = thumbnail
                    post.slug = new_slug
                    post.category = page_category
                    s.commit()
                    return {"url": f"{post_id}-{new_slug}"}
                return {"url": f"{post_id}-{slug}"}
        except Exception as e:
            logger.error(f"update_post_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def get_update_post_detail_v3(post_id: str, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                post = s.query(CommunityPostsV3).filter(CommunityPostsV3.id == int(post_id)).first()
                if post and post.user_email == user_email:
                    post.id = str(post.id)
                    return post
                return None
        except Exception as e:
            logger.error(
                f"get_update_post_detail_v3: {post_id}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def delete_post_by_admin_v3(post_id: str):
        return CommunityServiceV3._delete_post_v3(post_id, "admin")

    @staticmethod
    def delete_post_by_user_v3(post_id: str):
        return CommunityServiceV3._delete_post_v3(post_id, "user")

    @staticmethod
    def _delete_post_v3(post_id: str, delete_type: str):
        try:
            with V3Database.SessionLocal() as s:
                post = s.query(CommunityPostsV3).filter(CommunityPostsV3.id == int(post_id)).first()
                if post:
                    post.update_time = datetime.now()
                    if delete_type == "admin":
                        post.delete_by_admin = True
                    else:
                        post.delete_by_user = True
                s.commit()
                return {"result": 1}
        except Exception as e:
            logger.error(f"delete_post_by_{delete_type}_v3: {post_id}, error: {e}", exc_info=True)
            return None

    @staticmethod
    def get_search_v3(
        search_type: str, word: str, page_num: int, user_email: Optional[str] = None
    ):
        try:
            limit, offset = 20, (page_num - 1) * 20
            params = {
                "limit": limit,
                "offset": offset,
                "word": f"%{word}%",
                "user_email": user_email,
            }
            with V3Database.SessionLocal() as s:
                search_result = s.execute(
                    text(CommunityFunctionV3.get_search_sql(search_type)),
                    params,
                )
                total = s.execute(
                    text(CommunityFunctionV3.get_search_total_count_sql(search_type)),
                    params,
                ).scalar()
                return {
                    "search_result": [dict(row) for row in search_result.mappings()],
                    "total_count": total,
                    "max_page_count": (total + limit - 1) // limit,
                }
        except Exception as e:
            logger.error(f"get_search_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def report_post_v3(request_info: ReqPostReport, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                s.add(
                    PostReportV3(
                        target_post_id=int(request_info.post_id),
                        request_email=user_email,
                        target_email=request_info.reported_email,
                        reason_type=request_info.reason_type,
                        reason=request_info.reason,
                        create_time=datetime.now(),
                    )
                )
                s.commit()
                return {"result": 1}
        except Exception as e:
            logger.error(
                f"report_post_v3: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def increase_view_count_v3(post_id_slug: str):
        try:
            with V3Database.SessionLocal() as s:
                post_id = CommunityFunctionV3.parse_id_and_slug(post_id_slug)
                s.execute(text(CommunityUtilV3.increase_view_count()), {"post_id": post_id})
                s.commit()
                return {"result": 1}
        except Exception as e:
            logger.error(
                f"increase_view_count_v3: {post_id_slug}, error: {e}",
                exc_info=True,
            )
            return None
