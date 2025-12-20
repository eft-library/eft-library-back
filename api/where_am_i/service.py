from database import DataBaseConnector
from sqlalchemy import exists
from api.user.user_res_models import User
from api.where_am_i.req_models import ReqWhereAmI
from util.kafka_producer import produce_where_am_i
import json
from datetime import datetime, timezone


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
    def save_where_am_i(req: ReqWhereAmI):
        exists_user = WhereAmIService.check_wpf_user(req.user_email)
        if exists_user:
            kafka_message = {
                "user_email": req.email,
                "save_time": datetime.now(timezone.utc).isoformat(),
                "location": req.location,
            }
            json_str = json.dumps(kafka_message)
            produce_where_am_i(json_str)
        else:
            print("존재하지 않는 사용자: ", req.user_email)
            return None
