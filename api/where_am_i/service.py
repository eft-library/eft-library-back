from database import DataBaseConnector
from sqlalchemy import exists
from api.user.user_res_models import User
from api.where_am_i.req_models import ReqWhereAmI
from util.websocket import send_wpf_data_ws_direct


class WhereAmIService:

    @staticmethod
    def check_wpf_user(user_email):
        """
        사용자 확인
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                exists_user = s.query(exists().where(User.email == user_email)).scalar()
                return exists_user
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    async def send_location(req: ReqWhereAmI):
        exists_user = WhereAmIService.check_wpf_user(req.email)
        if exists_user:
            await send_wpf_data_ws_direct(user_email=req.email, location=req.location)
        else:
            print("존재하지 않는 사용자: ", req.email)
            return None
