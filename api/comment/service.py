from datetime import datetime
import json
import logging

from nanoid import generate
from sqlalchemy import text

from api.comment.comment_req_models import (
    InsertChildComment,
    InsertParentComment,
    ReqCommentReport,
)
from api.comment.comment_res_models import CommentReactionV3, CommentReportV3
from api.comment.util import CommentUtilV3
from database import V3Database
from util.kafka_producer import produce_notification

logger = logging.getLogger("api.comment")


class CommentServiceV3:
    @staticmethod
    def insert_parent_comment_v3(request_info: InsertParentComment, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                new_id = generate(size=12)
                bigint_post_id = int(request_info.post_id)
                s.execute(
                    text(CommentUtilV3.insert_parent_comment()),
                    {
                        "comment_id": new_id,
                        "post_id": bigint_post_id,
                        "contents": request_info.contents,
                        "user_email": user_email,
                    },
                )
                s.commit()

                if request_info.post_author_email != user_email:
                    produce_notification(
                        json.dumps(
                            {
                                "url": f"{bigint_post_id}-{request_info.slug}?comment_id={new_id}",
                                "author_email": user_email,
                                "post_id": bigint_post_id,
                                "author_nickname": request_info.nickname,
                                "title": request_info.title,
                                "noti_type": "create_parent_comment",
                            }
                        )
                    )

                return {"result": 1}
        except Exception as e:
            logger.error(
                f"insert_parent_comment_v3: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def insert_child_comment_v3(request_info: InsertChildComment, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                new_id = generate(size=12)
                bigint_post_id = int(request_info.post_id)
                s.execute(
                    text(CommentUtilV3.insert_child_comment()),
                    {
                        "comment_id": new_id,
                        "parent_comment_id": request_info.parent_comment_id,
                        "post_id": bigint_post_id,
                        "contents": request_info.contents,
                        "user_email": user_email,
                    },
                )
                s.commit()

                if request_info.post_author_email != user_email:
                    produce_notification(
                        json.dumps(
                            {
                                "url": f"{bigint_post_id}-{request_info.slug}?comment_id={new_id}",
                                "author_email": user_email,
                                "post_id": bigint_post_id,
                                "parent_comment_id": request_info.parent_comment_id,
                                "author_nickname": request_info.nickname,
                                "title": request_info.title,
                                "noti_type": "create_child_comment",
                            }
                        )
                    )

                return {"result": 1}
        except Exception as e:
            logger.error(
                f"insert_child_comment_v3: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_comment_v3(
        post_id: str, page_num: int, issue_comment_id: str, user_email: str
    ):
        try:
            limit = 20
            with V3Database.SessionLocal() as s:
                bigint_post_id = int(post_id)
                total = s.execute(
                    text(CommentUtilV3.get_comment_total_count()),
                    {"post_id": bigint_post_id},
                ).scalar()
                max_page_count = (total + limit - 1) // limit

                if issue_comment_id:
                    current_page_num = s.execute(
                        text(CommentUtilV3.get_issue_comment_page()),
                        {
                            "post_id": bigint_post_id,
                            "comment_id": issue_comment_id,
                            "limit": limit,
                        },
                    ).scalar()
                elif page_num == 0:
                    current_page_num = max_page_count
                else:
                    current_page_num = page_num

                rn_start = (current_page_num - 1) * limit + 1
                rn_end = current_page_num * limit

                comments = s.execute(
                    text(CommentUtilV3.get_comment()),
                    {
                        "post_id": bigint_post_id,
                        "user_email": user_email,
                        "rn_start": rn_start,
                        "rn_end": rn_end,
                    },
                )
                issue_comments = s.execute(
                    text(CommentUtilV3.get_issue_comment()),
                    {"post_id": bigint_post_id},
                )

                return {
                    "comments": [dict(row) for row in comments.mappings()],
                    "issue_comments": [dict(row) for row in issue_comments.mappings()],
                    "total": total,
                    "max_page_count": max_page_count,
                    "current_page_num": current_page_num,
                }
        except Exception as e:
            logger.error(f"get_comment_v3 error: {e}", exc_info=True)
            return None

    @staticmethod
    def update_comment_v3(comment_id: str, contents: str):
        try:
            with V3Database.SessionLocal() as s:
                s.execute(
                    text(CommentUtilV3.update_comment()),
                    {
                        "comment_id": comment_id,
                        "contents": contents,
                        "update_time": datetime.now(),
                    },
                )
                s.commit()
                return {"result": 1}
        except Exception as e:
            logger.error(
                f"update_comment_v3: {comment_id}, {contents}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def delete_comment_by_user_v3(comment_id: str):
        return CommentServiceV3._delete_comment_v3(
            comment_id, CommentUtilV3.delete_comment_by_user(), "user"
        )

    @staticmethod
    def delete_comment_by_admin_v3(comment_id: str):
        return CommentServiceV3._delete_comment_v3(
            comment_id, CommentUtilV3.delete_comment_by_admin(), "admin"
        )

    @staticmethod
    def _delete_comment_v3(comment_id: str, sql: str, delete_type: str):
        try:
            with V3Database.SessionLocal() as s:
                s.execute(
                    text(sql),
                    {"comment_id": comment_id, "update_time": datetime.now()},
                )
                s.commit()
                return {"result": 1}
        except Exception as e:
            logger.error(
                f"delete_comment_by_{delete_type}_v3: {comment_id}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def like_comment_v3(comment_id: str, user_email: str):
        return CommentServiceV3._toggle_reaction_v3(comment_id, user_email, 1)

    @staticmethod
    def dislike_comment_v3(comment_id: str, user_email: str):
        return CommentServiceV3._toggle_reaction_v3(comment_id, user_email, 0)

    @staticmethod
    def _toggle_reaction_v3(comment_id: str, user_email: str, next_value: int):
        try:
            with V3Database.SessionLocal() as s:
                result = s.execute(
                    text(
                        """
                        INSERT INTO community_comments_reactions
                            (comment_id, email, reaction_type, reaction_time)
                        VALUES
                            (:comment_id, :email, :next_value, :reaction_time)
                        ON CONFLICT (comment_id, email) DO UPDATE
                        SET reaction_type = CASE
                                WHEN :next_value = 1 THEN
                                    CASE
                                        WHEN COALESCE(community_comments_reactions.reaction_type, -1) IN (0, -1)
                                        THEN 1
                                        ELSE -1
                                    END
                                ELSE
                                    CASE
                                        WHEN COALESCE(community_comments_reactions.reaction_type, -1) IN (1, -1)
                                        THEN 0
                                        ELSE -1
                                    END
                            END,
                            reaction_time = excluded.reaction_time
                        RETURNING reaction_type;
                        """
                    ),
                    {
                        "comment_id": comment_id,
                        "email": user_email,
                        "next_value": next_value,
                        "reaction_time": datetime.now(),
                    },
                )
                reaction_type = result.scalar_one()
                s.commit()
                return {"result": reaction_type}
        except Exception as e:
            logger.error(
                f"toggle_reaction_v3: {comment_id}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def report_comment_v3(request_info: ReqCommentReport, user_email: str):
        try:
            with V3Database.SessionLocal() as s:
                s.add(
                    CommentReportV3(
                        target_comment_id=request_info.comment_id,
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
                f"report_comment_v3: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None
