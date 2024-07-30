import shutil
import os
import subprocess
from uuid import uuid4
from dotenv import load_dotenv
from api.board.board_res_models import (
    ForumBoard,
    HumorBoard,
    TipBoard,
    NoticeBoard,
    IncidentBoard,
    Issue,
    PostLike,
)
from api.board.board_req_models import AddPost, LikeOrDisPost
from database import DataBaseConnector
from api.user.user_res_models import User
from datetime import datetime
import re

load_dotenv()


def valid_post_type(addPost: AddPost, user_email: str):
    # 각 게시물 유형에 해당하는 클래스를 매핑하는 딕셔너리
    board_classes = {
        "Humor": HumorBoard,
        "Notice": NoticeBoard,
        "Incident": IncidentBoard,
        "Tip": TipBoard,
        "Forum": ForumBoard,
    }

    # 게시물 생성에 필요한 공통 필드
    common_fields = {
        "title": addPost.title,
        "contents": remove_video_delete_button(addPost.contents),
        "writer": user_email,
        "view_count": 0,
        "create_time": datetime.now(),
    }

    # 유형에 따라 추가 필드를 설정
    if addPost.type in ["Humor", "Incident", "Tip", "Forum"]:
        specific_fields = {
            "thumbnail": extract_thumbnail_img(addPost.contents),
            "like_count": 0,
            "dislike_count": 0,
            "type": addPost.type,
        }
        common_fields.update(specific_fields)

    # 선택한 클래스에 따라 객체를 생성
    BoardClass = board_classes.get(addPost.type, ForumBoard)  # 기본값은 ForumBoard
    new_post = BoardClass(**common_fields)

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

        return file_location, unique_filename

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
