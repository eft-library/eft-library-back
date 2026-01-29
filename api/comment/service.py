from api.comment.util import CommentUtil
from database import DataBaseConnector
from sqlalchemy import text
from nanoid import generate
from api.comment.comment_res_models import CommentReaction, CommentReport
from datetime import datetime
from api.comment.comment_req_models import (
    ReqCommentReport,
    InsertParentComment,
    InsertChildComment,
)
from util.kafka_producer import produce_notification
import json
import logging

logger = logging.getLogger("api.comment")


class CommentService:
    @staticmethod
    def insert_parent_comment(request_info: InsertParentComment, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # nano id 생성
                new_id = generate(size=12)
                bigint_post_id = int(request_info.post_id)

                insert_comment_query = text(CommentUtil.insert_parent_comment())
                insert_comment_params = {
                    "comment_id": new_id,
                    "post_id": bigint_post_id,
                    "contents": request_info.contents,
                    "user_email": user_email,
                }
                s.execute(insert_comment_query, insert_comment_params)
                s.commit()

                # 본인이 작성한 거는 무시
                if request_info.post_author_email != user_email:
                    kafka_message = {
                        "url": f"{bigint_post_id}-{request_info.slug}?comment_id={new_id}",
                        "author_email": user_email,
                        "post_id": bigint_post_id,
                        "author_nickname": request_info.nickname,
                        "title": request_info.title,
                        "noti_type": "create_parent_comment",
                    }
                    json_str = json.dumps(kafka_message)
                    produce_notification(json_str)

                return {"result": 1}
        except Exception as e:
            logger.error(
                f"insert_parent_comment: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def inset_child_comment(request_info: InsertChildComment, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # nano id 생성
                new_id = generate(size=12)
                bigint_post_id = int(request_info.post_id)

                insert_comment_query = text(CommentUtil.insert_child_comment())
                insert_comment_params = {
                    "comment_id": new_id,
                    "parent_comment_id": request_info.parent_comment_id,
                    "post_id": bigint_post_id,
                    "contents": request_info.contents,
                    "user_email": user_email,
                }
                s.execute(insert_comment_query, insert_comment_params)
                s.commit()

                # 본인이 작성한 거는 무시
                if request_info.post_author_email != user_email:
                    kafka_message = {
                        "url": f"{bigint_post_id}-{request_info.slug}?comment_id={new_id}",
                        "author_email": user_email,
                        "post_id": bigint_post_id,
                        "parent_comment_id": request_info.parent_comment_id,
                        "author_nickname": request_info.nickname,
                        "title": request_info.title,
                        "noti_type": "create_child_comment",
                    }
                    json_str = json.dumps(kafka_message)
                    produce_notification(json_str)

                return {"result": 1}
        except Exception as e:
            logger.error(
                f"inset_child_comment: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_comment(
        post_id: str, page_num: int, issue_comment_id: str, user_email: str
    ):
        try:
            limit = 20
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                bigint_post_id = int(post_id)
                # 전체 개수 조회
                total_query = text(CommentUtil.get_comment_total_count())
                total_result = s.execute(total_query, {"post_id": bigint_post_id})
                total = total_result.scalar()

                # 최대 페이지 수
                max_page_count = (total + limit - 1) // limit

                # issue comment 바로가기 동작
                if len(issue_comment_id) > 0:
                    current_issue_comment_page_query = text(
                        CommentUtil.get_issue_comment_page()
                    )
                    current_issue_comment_page_result = s.execute(
                        current_issue_comment_page_query,
                        {
                            "post_id": bigint_post_id,
                            "comment_id": issue_comment_id,
                            "limit": limit,
                        },
                    )
                    current_page_num = current_issue_comment_page_result.scalar()
                # 마지막 페이지 요청 (page_num == 0)
                elif page_num == 0:
                    current_page_num = max_page_count
                else:
                    current_page_num = page_num

                # rn_start, rn_end 계산
                rn_start = (current_page_num - 1) * limit + 1
                rn_end = current_page_num * limit
                # comment 조회할 때 user_email로 좋아요인지 싫어요인지 가져와야 함
                get_comment_query = text(CommentUtil.get_comment())
                get_comment_param = {
                    "post_id": bigint_post_id,
                    "user_email": user_email,
                    "rn_start": rn_start,
                    "rn_end": rn_end,
                }
                comments = s.execute(get_comment_query, get_comment_param)

                get_issue_comment_query = text(CommentUtil.get_issue_comment())
                issue_comments = s.execute(
                    get_issue_comment_query, {"post_id": bigint_post_id}
                )

                return {
                    "comments": [dict(row) for row in comments.mappings()],
                    "issue_comments": [dict(row) for row in issue_comments.mappings()],
                    "total": total,
                    "max_page_count": max_page_count,
                    "current_page_num": current_page_num,
                }
        except Exception as e:
            logger.error(
                f"get_comment error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def update_comment(comment_id: str, contents: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                update_comment_query = text(CommentUtil.update_comment())
                update_comment_params = {
                    "comment_id": comment_id,
                    "contents": contents,
                    "update_time": datetime.now(),
                }
                s.execute(update_comment_query, update_comment_params)
                s.commit()
                return {"result": 1}
        except Exception as e:
            logger.error(
                f"update_comment: {comment_id}, {contents}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def delete_comment_by_user(comment_id: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                delete_comment_query = text(CommentUtil.delete_comment_by_user())
                delete_comment_params = {
                    "comment_id": comment_id,
                    "update_time": datetime.now(),
                }
                s.execute(delete_comment_query, delete_comment_params)
                s.commit()
                return {"result": 1}
        except Exception as e:
            logger.error(
                f"delete_comment_by_user: {comment_id}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def delete_comment_by_admin(comment_id: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                delete_comment_query = text(CommentUtil.delete_comment_by_admin())
                delete_comment_params = {
                    "comment_id": comment_id,
                    "update_time": datetime.now(),
                }
                s.execute(delete_comment_query, delete_comment_params)
                s.commit()
                return {"result": 1}
        except Exception as e:
            logger.error(
                f"delete_comment_by_admin: {comment_id}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def like_comment(comment_id: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 기존 reaction 조회
                reaction = (
                    s.query(CommentReaction)
                    .filter(
                        CommentReaction.comment_id == comment_id,
                        CommentReaction.user_email == user_email,
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
                    reaction = CommentReaction(
                        comment_id=comment_id,
                        user_email=user_email,
                        reaction_type=1,
                        update_time=datetime.now(),
                    )
                    s.add(reaction)

                s.commit()
                return {"result": reaction.reaction_type}  # 현재 상태 반환

        except Exception as e:
            logger.error(
                f"like_comment: {comment_id}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def dislike_comment(comment_id: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 기존 reaction 조회
                reaction = (
                    s.query(CommentReaction)
                    .filter(
                        CommentReaction.comment_id == comment_id,
                        CommentReaction.user_email == user_email,
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
                    reaction = CommentReaction(
                        comment_id=comment_id,
                        user_email=user_email,
                        reaction_type=0,
                        update_time=datetime.now(),
                    )
                    s.add(reaction)

                s.commit()
                return {"result": reaction.reaction_type}  # 현재 상태 반환

        except Exception as e:
            logger.error(
                f"dislike_comment: {comment_id}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def report_comment(request_info: ReqCommentReport, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                new_post_report = CommentReport(
                    comment_id=request_info.comment_id,
                    reporter_email=user_email,
                    reported_email=request_info.reported_email,
                    reason_type=request_info.reason_type,
                    reason=request_info.reason,
                    create_time=datetime.now(),
                )
                s.add(new_post_report)
                s.commit()

                return {"result": 1}
        except Exception as e:
            logger.error(
                f"report_comment: {request_info.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None
