import shutil
import os
import subprocess
from uuid import uuid4
from dotenv import load_dotenv
from sqlalchemy import text, func, desc
from api.board.util import BoardUtil
from api.board.board_res_models import (
    BoardType,
    PostLike,
    PostDisLike,
)
from api.board.board_req_models import AddPost, LikeOrDisPost
from database import DataBaseConnector
from api.user.user_res_models import User
from api.board.board_function import BoardFunction

load_dotenv()


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
                    new_post = BoardFunction.valid_post_type(addPost, user_email)
                    s.add(new_post)
                    s.commit()
                    return {"type": addPost.type}

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def user_like_post(likeOrDis: LikeOrDisPost, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                board_class = BoardFunction.get_post_type(likeOrDis.board_type)
                post = (
                    s.query(board_class).filter(board_class.id == likeOrDis.id).first()
                )

                user_like_info = (
                    s.query(PostLike)
                    .filter(
                        PostLike.user_email == user_email
                        and PostLike.board_id == likeOrDis.id
                    )
                    .first()
                )

                user_dislike_info = (
                    s.query(PostDisLike)
                    .filter(
                        PostDisLike.user_email == user_email
                        and PostDisLike.board_id == likeOrDis.id
                    )
                    .first()
                )

                if likeOrDis.type == "like":
                    BoardFunction.handle_like(
                        s,
                        post,
                        user_like_info,
                        user_dislike_info,
                        likeOrDis.id,
                        user_email,
                    )
                else:
                    BoardFunction.handle_dislike(
                        s,
                        post,
                        user_like_info,
                        user_dislike_info,
                        likeOrDis.id,
                        user_email,
                    )

                return True

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def is_user_like_post(likeOrDis: LikeOrDisPost, user_email: str):
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
                user_dislike_info = (
                    s.query(PostDisLike)
                    .filter(
                        PostDisLike.user_email == user_email
                        and PostDisLike.board_id == likeOrDis.id
                    )
                    .first()
                )

                if user_like_info:
                    return 1
                elif user_dislike_info:
                    return 2
                else:
                    return 3

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
            board_class = BoardFunction.get_post_type(board_type)
            offset = (page - 1) * page_size
            with session() as s:
                total_count = s.query(func.count(board_class.id)).scalar()
                max_pages = (total_count // page_size) + (
                    1 if total_count % page_size > 0 else 0
                )
                post_list = (
                    s.query(board_class, User.email, User.icon, User.nick_name)
                    .join(User, User.email == board_class.writer)  # join 조건 수정
                    .order_by(desc(board_class.create_time))
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )
                result = []
                for post, email, icon, nick_name in post_list:
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
                        "icon": icon,
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
            board_class = BoardFunction.get_post_type(board_type)
            with session() as s:
                posts = (
                    s.query(board_class, User.email, User.icon, User.nick_name)
                    .join(User, User.email == board_class.writer)
                    .filter(board_class.id == board_id)
                    .all()
                )
                for post, email, icon, nick_name in posts:
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
                        "icon": icon,
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
