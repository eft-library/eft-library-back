from datetime import datetime
import shutil
import os
import subprocess
from uuid import uuid4
from dotenv import load_dotenv
from sqlalchemy import text, and_
from api.board.util import BoardUtil
from api.board.board_res_models import BoardType, PostLike, PostDisLike
from api.board.board_req_models import (
    AddPost,
    LikeOrDisPost,
    ReportBoard,
    DeletePost,
    UpdatePost,
    AddBoardViewCount,
)
from database import DataBaseConnector
from api.user.user_res_models import User
from api.board.board_function import BoardFunction
from sqlalchemy.orm import subqueryload

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
                    new_post = BoardFunction._valid_post_type(addPost, user_email)
                    s.add(new_post)
                    check_user.point += 20
                    s.commit()
                    return {"type": addPost.type}

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def update_post(updatePost: UpdatePost):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                board_class = BoardFunction._get_post_type(updatePost.type)
                post = (
                    s.query(board_class).filter(board_class.id == updatePost.id).first()
                )
                clean_html = BoardFunction._remove_video_delete_button(
                    updatePost.contents
                )
                new_thumbnail = BoardFunction._extract_thumbnail_img(
                    updatePost.contents
                )

                post.title = updatePost.title
                post.thumbnail = new_thumbnail
                post.contents = clean_html
                post.update_time = datetime.now()
                s.commit()
                return True
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def user_like_post(likeOrDis: LikeOrDisPost, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                board_class = BoardFunction._get_post_type(likeOrDis.board_type)
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
                    BoardFunction._handle_like(
                        s,
                        post,
                        user_like_info,
                        user_dislike_info,
                        likeOrDis.id,
                        user_email,
                    )
                else:
                    BoardFunction._handle_dislike(
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
                        and_(
                            PostLike.user_email == user_email,
                            PostLike.board_id == likeOrDis.id,
                        )
                    )
                    .first()
                )
                user_dislike_info = (
                    s.query(PostDisLike)
                    .filter(
                        and_(
                            PostDisLike.user_email == user_email,
                            PostDisLike.board_id == likeOrDis.id,
                        )
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
    def get_post_v2(
        page: int,
        page_size: int,
        board_type: str,
        issue: bool,
        word: str,
        search_type: str,
    ):
        session_factory = DataBaseConnector.create_session_factory()
        try:
            with session_factory() as session:
                # 전체 데이터 수를 구하는 쿼리
                count_queries = BoardUtil.get_post_count_query(board_type)
                count_join_clause = BoardUtil.get_post_count_issue_clause(issue)
                count_where_clause = BoardUtil.get_post_count_where_clause(search_type)
                max_count_query = BoardUtil.get_post_max_cnt_query_v2()
                max_count_query = text(
                    max_count_query.format(
                        count_all_query=count_queries,
                        count_join_clause=count_join_clause,
                        count_where_clause=count_where_clause,
                    )
                )

                # 전체 데이터 수 조회
                count_param = {"word": f"%{word}%"}
                count_result = session.execute(max_count_query, count_param)
                total_count = count_result.scalar()

                # 총 페이지 수 계산
                max_pages = BoardFunction._get_max_pages(total_count, page_size)

                # 실제 데이터 조회 쿼리
                union_clause = BoardUtil.get_post_query(board_type)
                join_clause = BoardUtil.get_post_issue_clause(issue)
                where_clause = BoardUtil.get_post_where_clause(search_type)
                all_post_query = BoardUtil.get_post_query_v2()
                all_post_query = all_post_query.format(
                    union_clause=union_clause,
                    join_clause=join_clause,
                    where_clause=where_clause,
                )
                all_post_query = text(all_post_query)

                # 데이터 조회
                offset = (page - 1) * page_size
                params = {"limit": page_size, "offset": offset, "word": f"%{word}%"}
                result = session.execute(all_post_query, params).fetchall()

                # 컬럼 이름과 값을 매핑하여 딕셔너리로 변환
                posts = [dict(row._mapping) for row in result]

                return {
                    "data": posts,
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
            board_class = BoardFunction._get_post_type(board_type)
            with session() as s:
                posts = (
                    s.query(board_class, User.email, User.icon, User.nick_name)
                    .options(subqueryload(board_class.type_kr))
                    .outerjoin(User, User.email == board_class.writer)
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
                        "view_count": post.view_count,
                        "type": post.type,
                        "type_kr": post.type_kr.name_kr,
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

    @staticmethod
    def get_user_posts(page: int, page_size: int, user_email: str):
        session_factory = DataBaseConnector.create_session_factory()

        try:
            with session_factory() as session:
                # 전체 데이터 수를 구하는 쿼리
                cnt_params = {"email": user_email}
                max_cnt_query = text(BoardUtil.get_user_max_cnt_query())

                # OFFSET 계산
                offset = (page - 1) * page_size

                # 전체 데이터 수 조회
                result = session.execute(max_cnt_query, cnt_params)
                real_total_count = result.scalar()

                # 총 페이지 수 계산
                max_pages = BoardFunction._get_max_pages(real_total_count, page_size)

                # 실제 데이터 조회 쿼리
                query = text(BoardUtil.get_user_posts())

                # 데이터 조회
                params = {"limit": page_size, "offset": offset, "email": user_email}
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
    def report_board(reportBoard: ReportBoard, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                new_report = BoardFunction._create_board_report(reportBoard, user_email)
                s.add(new_report)
                s.commit()
                return True
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def delete_board(deletePost: DeletePost, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                board_class = BoardFunction._get_post_type(deletePost.board_type)
                post = (
                    s.query(board_class)
                    .filter(board_class.id == deletePost.board_id)
                    .first()
                )
                new_delete = BoardFunction._create_board_delete(post, user_email)
                user = s.query(User).filter(User.email == user_email).first()
                user.point -= post.like_count + 20
                s.add(new_delete)
                s.delete(post)
                s.commit()

                return post
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def add_board_view_count(addBoardViewCount: AddBoardViewCount):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                board_class = BoardFunction._get_post_type(addBoardViewCount.board_type)
                post = (
                    s.query(board_class)
                    .filter(board_class.id == addBoardViewCount.board_id)
                    .first()
                )
                post.view_count += 1
                s.commit()
                return True
        except Exception as e:
            print("오류 발생:", e)
            return None
