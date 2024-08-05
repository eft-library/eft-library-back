from api.user.user_res_models import User, UserQuest, UserGrade, UserIconList
from api.user.user_req_models import (
    AddUserReq,
)
from database import DataBaseConnector
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime, timedelta, date
import pytz

load_dotenv()


class UserService:
    @staticmethod
    def add_new_user(addUserReq: AddUserReq):
        try:
            uuid_v5 = f"{os.getenv('UUID_NAME')}-{uuid.uuid5(uuid.NAMESPACE_DNS, addUserReq.email)}"
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 이미 존재하는 사용자인지 확인
                check_user = (
                    s.query(User).filter(User.email == addUserReq.email).first()
                )

                if check_user:
                    # 출석일 수 관련
                    today = date.today()
                    tz = pytz.timezone("Asia/Seoul")  # 필요한 타임존으로 변경

                    # 오프셋 정보를 포함하여 datetime 객체 생성
                    start_of_today = tz.localize(
                        datetime.combine(today, datetime.min.time())
                    )
                    end_of_today = tz.localize(
                        datetime.combine(today, datetime.max.time())
                    )

                    # check_user.attendance_time이 오프셋 정보를 포함하고 있는지 확인하고, 없으면 로컬라이즈
                    if check_user.attendance_time.tzinfo is None:
                        check_user.attendance_time = tz.localize(
                            check_user.attendance_time
                        )

                    # 사용자가 처음 출석하거나 오늘 처음 출석하는 경우
                    if not (
                        start_of_today <= check_user.attendance_time <= end_of_today
                    ):
                        check_user.attendance_count += 1
                        check_user.attendance_time = datetime.now(tz)
                        check_user.point += 10
                        s.commit()  # 변경 사항을 커밋

                    return True
                else:
                    new_user = User(
                        id=addUserReq.id,
                        name=addUserReq.name,
                        email=addUserReq.email,
                        icon="/tkl_user/icon/newbie.gif",
                        nick_name=uuid_v5[:10],
                        point=10,
                        is_admin=False,
                        attendance_count=1,
                        create_time=datetime.now(),
                        attendance_time=datetime.now(),
                    )
                    s.add(new_user)
                    new_user_quest = UserQuest(
                        user_email=addUserReq.email,
                        quest_id=[],
                    )
                    s.add(new_user_quest)
                    new_icon_list = UserIconList(
                        user_email=addUserReq.email,
                        icon_list=["/tkl_user/icon/newbie.gif"],
                    )
                    s.add(new_icon_list)
                    s.commit()
                    return True
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_user_data(s, user_email: str):
        user = s.query(User).filter(User.email == user_email).first()
        grade = (
            s.query(UserGrade)
            .filter(
                UserGrade.min_point <= user.point,
                UserGrade.max_point >= user.point,
            )
            .first()
        )
        icon_list = (
            s.query(UserIconList).filter(user.email == UserIconList.user_email).first()
        )
        user_data = {
            "user": user,
            "grade": grade.value if grade else "뉴비",
            "icon_list": (
                icon_list.icon_list if icon_list else ["/tkl_user/icon/newbie.gif"]
            ),
        }
        return user_data

    @staticmethod
    def get_user(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_data = UserService.get_user_data(s, user_email)
                return user_data
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def change_user_nickname(new_nickname: str, user_email: str):
        """
        요건 적합 : return user
        30일 안지남 : return 2
        중복 : return 3
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = s.query(User).filter(User.email == user_email).first()

                # 수정 시간이 30일이 지났는지 확인
                thirty_days_ago = datetime.now(pytz.UTC) - timedelta(days=30)

                if (
                    user.update_time is None
                    or user.update_time.replace(tzinfo=pytz.UTC) < thirty_days_ago
                ):
                    # 30일 지났거나 변경한 적 없음
                    nickname_duplicate = (
                        s.query(User).filter(User.nick_name == new_nickname).first()
                    )
                    if nickname_duplicate:
                        # 중복
                        return 3
                    else:
                        user.nick_name = new_nickname
                        user.update_time = datetime.now()
                        s.commit()

                        user_data = UserService.get_user_data(s, user_email)
                        return user_data
                else:
                    # 30일 안 되었음
                    return 2
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def change_user_icon(new_icon: str, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user = s.query(User).filter(User.email == user_email).first()
                if user:
                    user.icon = new_icon
                    s.commit()
                user_data = UserService.get_user_data(s, user_email)
                return user_data
        except Exception as e:
            print("오류 발생:", e)
            return None
