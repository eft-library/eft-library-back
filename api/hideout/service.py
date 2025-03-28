from typing import List

from sqlalchemy import text
from database import DataBaseConnector
from api.hideout.util import HideoutUtil
from datetime import datetime
from api.hideout.hideout_res_models import UserHideOut


class HideoutService:

    @staticmethod
    def get_station(user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_hideout = {}
                query = text(HideoutUtil.get_hideout_query())
                result = s.execute(query)
                hideouts = [dict(row) for row in result.mappings()]
                user_hideout['hideout_info'] = hideouts

                if user_email is not None:
                    complete_list = (
                        s.query(UserHideOut)
                        .filter(UserHideOut.user_email == user_email)
                        .first()
                    )
                    if complete_list is not None:
                        user_hideout["complete_list"] = complete_list.complete_list
                    else:
                        user_hideout["complete_list"] = []
                    return user_hideout
                else:
                    user_hideout["complete_list"] = []
                    return user_hideout
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def save_station(complete_list: List[str], user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_hideout = s.query(UserHideOut).filter_by(user_email=user_email).first()
                if user_hideout:
                    user_hideout.complete_list = complete_list
                    user_hideout.update_time = datetime.utcnow()
                    s.commit()
                else:
                    new_user_hideout = UserHideOut(
                        user_email=user_email,
                        complete_list=complete_list,
                        update_time=datetime.utcnow()
                    )
                    s.add(new_user_hideout)
                    s.commit()
                return user_hideout
        except Exception as e:
            print("오류 발생:", e)
            return None

