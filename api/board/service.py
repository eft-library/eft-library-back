import shutil
import os
import subprocess
from uuid import uuid4
from dotenv import load_dotenv
from sqlalchemy import text, func, desc
from api.board.util import BoardUtil
from api.board.board_res_models import (
    ForumBoard,
    PvpBoard,
    PveBoard,
    TipBoard,
    NoticeBoard,
    ArenaBoard,
    QuestionBoard,
    BoardType,
    Issue,
    PostLike,
)
from api.board.board_req_models import AddPost, LikeOrDisPost
from database import DataBaseConnector
from api.user.user_res_models import User
from datetime import datetime
import re

load_dotenv()


def get_post_type(board_type: str):
    # 각 게시물 유형에 해당하는 클래스를 매핑하는 딕셔너리
    board_classes = {
        "arena": ArenaBoard,
        "pvp": PvpBoard,
        "pve": PveBoard,
        "question": QuestionBoard,
        "notice": NoticeBoard,
        "tip": TipBoard,
        "forum": ForumBoard,
    }
    board_class = board_classes.get(board_type, ForumBoard)
    return board_class


def valid_post_type(addPost: AddPost, user_email: str):
    # 게시물 생성에 필요한 공통 필드
    common_fields = {
        "id": uuid4(),
        "title": addPost.title,
        "contents": remove_video_delete_button(addPost.contents),
        "writer": user_email,
        "view_count": 0,
        "create_time": datetime.now(),
    }

    # 유형에 따라 추가 필드를 설정
    if addPost.type in ["arena", "pvp", "pve", "question", "tip", "forum"]:
        specific_fields = {
            "thumbnail": extract_thumbnail_img(addPost.contents),
            "like_count": 0,
            "dislike_count": 0,
            "type": addPost.type,
        }
        common_fields.update(specific_fields)

    # 선택한 클래스에 따라 객체를 생성
    board_class = get_post_type(addPost.type)  # 기본값은 ForumBoard
    new_post = board_class(**common_fields)

    return new_post


def remove_video_delete_button(html):
    # 정규 표현식을 사용하여 <button class="ql-video-delete"> 태그를 제거합니다.
    cleaned_html = re.sub(
        r'<button class="ql-video-delete"[^>]*>.*?</button>', "", html, flags=re.DOTALL
    )
    return cleaned_html


def extract_thumbnail_img(html):
    # 정규 표현식을 사용하여 첫 번째 <img> 태그의 src 값을 찾습니다.
    match = re.search(r'<img[^>]+src="([^"]+)"', html)
    if match:
        return match.group(1)
    return None


class BoardService:
    @staticmethod
    def save_file(file, filename):
        os.makedirs(os.getenv("LOCAL_UPLOAD_PATH"), exist_ok=True)
        file_extension = filename.split(".")[-1]
        unique_filename = f"{uuid4()}.{file_extension}"
        file_location = os.path.join(os.getenv("LOCAL_UPLOAD_PATH"), unique_filename)

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_url = (
            f"{os.getenv('NAS_DATA')}{os.getenv('BOARD_IMAGE_PATH')}/{unique_filename}"
        )

        return file_location, unique_filename, image_url

    @staticmethod
    def upload_to_remote(local_path: str, filename: str) -> bool:
        """
        deprecated
        """
        try:
            subprocess.run(
                [
                    "sshpass",
                    "-p",
                    os.getenv("SERVER_PW"),
                    "scp",
                    # "-O",
                    "-P",
                    os.getenv("SERVER_PORT"),
                    local_path,
                    f"{os.getenv('SERVER_HOST')}:{os.getenv('SERVER_PATH')}/{filename}",
                ],
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def add_new_post(addPost: AddPost, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 사용자 확인
                check_user = s.query(User).filter(User.email == user_email).first()

                if check_user:
                    new_post = valid_post_type(addPost, user_email)
                    s.add(new_post)
                    s.commit()
                    return True

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def change_user_like_post(likeOrDis: LikeOrDisPost, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_like_info = (
                    s.query(PostLike)
                    .filter(
                        PostLike.user_email == user_email
                        and PostLike.board_id == likeOrDis.id
                    )
                    .first()
                )

                if user_like_info:
                    s.delete(user_like_info)
                    s.commit()
                else:
                    new_like_user = PostLike(
                        board_id=likeOrDis.id,
                        user_email=user_email,
                        update_time=datetime.now(),
                    )
                    s.add(new_like_user)
                    s.commit()
                return True

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_post(page: int, page_size: int):
        session_factory = DataBaseConnector.create_session_factory()

        try:
            with session_factory() as session:
                # 전체 데이터 수를 구하는 쿼리
                max_cnt_query = text(BoardUtil.get_post_max_cnt_query())

                # OFFSET 계산
                offset = (page - 1) * page_size

                # 전체 데이터 수 조회
                result = session.execute(max_cnt_query)
                real_total_count = result.scalar()

                # 총 페이지 수 계산
                max_pages = (real_total_count // page_size) + (
                    1 if real_total_count % page_size > 0 else 0
                )

                # 실제 데이터 조회 쿼리
                query = text(BoardUtil.get_post_query())

                # 데이터 조회
                params = {"limit": page_size, "offset": offset}
                result = session.execute(query, params).fetchall()

                # 컬럼 이름과 값을 매핑하여 딕셔너리로 변환
                posts = [dict(row._mapping) for row in result]

                return {
                    "data": posts,
                    "total_count": real_total_count,
                    "max_pages": max_pages,
                    "current_page": page,
                }

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_type_post(page: int, page_size: int, board_type: str):
        try:
            session = DataBaseConnector.create_session_factory()
            board_class = get_post_type(board_type)
            offset = (page - 1) * page_size
            with session() as s:
                total_count = s.query(func.count(board_class.id)).scalar()
                max_pages = (total_count // page_size) + (
                    1 if total_count % page_size > 0 else 0
                )
                post_list = (
                    s.query(board_class, User.email, User.image, User.nick_name)
                    .join(User, User.email == board_class.writer)  # join 조건 수정
                    .order_by(desc(board_class.create_time))
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )
                result = []
                for post, email, image, nick_name in post_list:
                    post_dict = {
                        "id": post.id,
                        "title": post.title,
                        "contents": post.contents,
                        "thumbnail": post.thumbnail,
                        "writer": post.writer,
                        "like_count": post.like_count,
                        "dislike_count": post.dislike_count,
                        "view_count": post.view_count,
                        "type": post.type,
                        "create_time": post.create_time,
                        "update_time": post.update_time,
                        "image": image,
                        "nick_name": nick_name,
                    }
                    result.append(post_dict)
                return {
                    "data": result,
                    "total_count": total_count,
                    "max_pages": max_pages,
                    "current_page": page,
                }

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_post_by_id(board_id: str, board_type: str):
        try:
            session = DataBaseConnector.create_session_factory()
            board_class = get_post_type(board_type)
            with session() as s:
                posts = (
                    s.query(board_class, User.email, User.image, User.nick_name)
                    .join(User, User.email == board_class.writer)
                    .filter(board_class.id == board_id)
                    .all()
                )
                for post, email, image, nick_name in posts:
                    post_dict = {
                        "id": post.id,
                        "title": post.title,
                        "contents": post.contents,
                        "thumbnail": post.thumbnail,
                        "writer": post.writer,
                        "like_count": post.like_count,
                        "dislike_count": post.dislike_count,
                        "view_count": post.view_count,
                        "type": post.type,
                        "create_time": post.create_time,
                        "update_time": post.update_time,
                        "image": image,
                        "nick_name": nick_name,
                    }
                    return post_dict

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_board_type():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                board_type = s.query(BoardType).order_by(BoardType.order).all()
                return board_type
        except Exception as e:
            print("오류 발생:", e)
            return None
