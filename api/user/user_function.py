from api.user.user_res_models import User
from api.planner.planner_res_models import UserQuest
from api.user.user_req_models import AddUserReq
from dotenv import load_dotenv
from datetime import datetime, date
import pytz

load_dotenv()


default_icon = "/tkl_user/icon/cat.png"


class UserFunction:
    @staticmethod
    def _get_existing_user(session, email: str) -> User:
        return session.query(User).filter(User.email == email).first()

    @staticmethod
    def _handle_existing_user(session, user: User):
        today = date.today()
        tz = pytz.timezone("Asia/Seoul")
        start_of_today, end_of_today = UserFunction._get_start_and_end_of_day(tz, today)

        if user.attendance_time.tzinfo is None:
            user.attendance_time = tz.localize(user.attendance_time)

        if not (start_of_today <= user.attendance_time <= end_of_today):
            user.attendance_count += 1
            user.attendance_time = datetime.now(tz)
            session.commit()

    @staticmethod
    def _get_start_and_end_of_day(tz, today):
        start_of_today = tz.localize(datetime.combine(today, datetime.min.time()))
        end_of_today = tz.localize(datetime.combine(today, datetime.max.time()))
        return start_of_today, end_of_today

    @staticmethod
    def _create_delete_user(session, user: User):
        session.delete(user)
        session.commit()

    @staticmethod
    def _create_new_user(session, addUserReq: AddUserReq):
        new_user = User(
            id=addUserReq.id,
            name=addUserReq.name,
            email=addUserReq.email,
            is_admin=False,
            attendance_count=1,
            create_time=datetime.now(),
            attendance_time=datetime.now(),
        )
        session.add(new_user)
        UserFunction._create_user_related_entries(
            session,
            addUserReq.email,
        )
        session.commit()

    @staticmethod
    def _create_user_related_entries(session, email: str):
        new_user_quest = UserQuest(
            user_email=email,
            quest_id=[],
            update_time=datetime.now()
        )
        session.add(new_user_quest)

    @staticmethod
    def _get_user_data(session, user_email: str):
        user = session.query(User).filter(User.email == user_email).first()
        user_data = {
            "user": user,
        }
        return user_data
