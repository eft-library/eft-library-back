from uuid import uuid4
from api.board.board_res_models import (
    ForumBoard,
    PvpBoard,
    PveBoard,
    TipBoard,
    ArenaBoard,
    QuestionBoard,
    PostLike,
    PostDisLike,
    BoardReport,
    DeleteBoard,
    TrashBoard,
)
from api.board.board_req_models import AddPost, ReportBoard
from datetime import datetime
import re


class BoardFunction:
    @staticmethod
    def _get_post_type(board_type: str):
        # 각 게시물 유형에 해당하는 클래스를 매핑하는 딕셔너리
        board_classes = {
            "arena": ArenaBoard,
            "pvp": PvpBoard,
            "pve": PveBoard,
            "question": QuestionBoard,
            "tip": TipBoard,
            "forum": ForumBoard,
            "trash": TrashBoard,
        }
        board_class = board_classes.get(board_type, ForumBoard)
        return board_class

    @staticmethod
    def _valid_post_type(addPost: AddPost, user_email: str):
        # 게시물 생성에 필요한 공통 필드
        common_fields = {
            "id": uuid4(),
            "title": addPost.title,
            "contents": BoardFunction._remove_video_delete_button(addPost.contents),
            "writer": user_email,
            "view_count": 0,
            "create_time": datetime.now(),
            "thumbnail": BoardFunction._extract_thumbnail_img(addPost.contents),
            "like_count": 0,
            "type": addPost.type,
        }

        # 선택한 클래스에 따라 객체를 생성
        board_class = BoardFunction._get_post_type(addPost.type)  # 기본값은 ForumBoard
        new_post = board_class(**common_fields)

        return new_post

    @staticmethod
    def _remove_video_delete_button(html):
        # 정규 표현식을 사용하여 <button class="ql-video-delete"> 태그를 제거합니다.
        cleaned_html = re.sub(
            r'<button class="ql-video-delete"[^>]*>.*?</button>',
            "",
            html,
            flags=re.DOTALL,
        )
        return cleaned_html

    @staticmethod
    def _extract_thumbnail_img(html):
        # 정규 표현식을 사용하여 첫 번째 <img> 태그의 src 값을 찾습니다.
        match = re.search(r'<img[^>]+src="([^"]+)"', html)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _handle_like(
        session, post, user_like_info, user_dislike_info, post_id, user_email
    ):
        if user_like_info:
            session.delete(user_like_info)
            post.like_count -= 1
        elif user_dislike_info:
            session.delete(user_dislike_info)
            post.like_count += 2
            new_like_user = PostLike(
                board_id=post_id,
                user_email=user_email,
                update_time=datetime.now(),
            )
            session.add(new_like_user)
        else:
            new_like_user = PostLike(
                board_id=post_id,
                user_email=user_email,
                update_time=datetime.now(),
            )
            session.add(new_like_user)
            post.like_count += 1
        session.commit()

    @staticmethod
    def _handle_dislike(
        session, post, user_like_info, user_dislike_info, post_id, user_email
    ):
        if user_like_info:
            session.delete(user_like_info)
            post.like_count -= 2
            new_dislike_user = PostDisLike(
                board_id=post_id,
                user_email=user_email,
                update_time=datetime.now(),
            )
            session.add(new_dislike_user)
        elif user_dislike_info:
            session.delete(user_dislike_info)
            post.like_count += 1
        else:
            new_dislike_user = PostDisLike(
                board_id=post_id,
                user_email=user_email,
                update_time=datetime.now(),
            )
            session.add(new_dislike_user)
            post.like_count -= 1
        session.commit()

    @staticmethod
    def _create_board_report(reportBoard: ReportBoard, user_email: str):
        new_report = BoardReport(
            board_id=reportBoard.board_id,
            board_type=reportBoard.board_type,
            report_reason=reportBoard.reason,
            report_user=user_email,
            create_time=datetime.now(),
        )
        return new_report

    @staticmethod
    def _create_board_delete(post, user_email: str):
        new_delete = DeleteBoard(
            id=post.id,
            title=post.title,
            contents=post.contents,
            thumbnail=post.thumbnail,
            writer=post.writer,
            like_count=post.like_count,
            view_count=post.view_count,
            type=post.type,
            create_time=post.create_time,
            update_time=post.update_time,
            delete_time=datetime.now(),
            delete_user=user_email,
        )
        return new_delete

    @staticmethod
    def _get_max_pages(total_count, page_size):
        return (total_count // page_size) + (1 if total_count % page_size > 0 else 0)
