from typing import List
from sqlalchemy import text
from database import DataBaseConnector
from api.hideout.util import HideoutUtil
from datetime import datetime
from api.hideout.hideout_res_models import UserHideOut
from api.hideout.hideout_req_models import ItemType
import pytz


class HideoutService:

    @staticmethod
    def get_station(user_email: str | None):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_hideout = {}

                # 은신처 기본 정보
                hideout_query = text(HideoutUtil.get_hideout_query())
                hideouts = s.execute(hideout_query).mappings().all()
                user_hideout["hideout_info"] = list(hideouts)

                # 완료 레벨 목록
                user_info = None
                if user_email:
                    user_info = (
                        s.query(UserHideOut)
                        .filter(UserHideOut.user_email == user_email)
                        .first()
                    )

                user_hideout["complete_list"] = (
                    user_info.complete_list if user_info else []
                )

                user_hideout["item_list"] = user_info.item_list if user_info else []

                # 아이템 필요 정보
                item_require_query = text(HideoutUtil.get_item_require_info())
                item_require = (
                    s.execute(item_require_query, {"user_email": user_email})
                    .mappings()
                    .all()
                )
                user_hideout["item_require_info"] = list(item_require)

                return user_hideout

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def save_station(complete_list: List[str], user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                user_hideout = (
                    s.query(UserHideOut).filter_by(user_email=user_email).first()
                )
                utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
                kst = pytz.timezone("Asia/Seoul")
                kst_now = utc_now.astimezone(kst)

                if user_hideout:
                    user_hideout.complete_list = complete_list
                    user_hideout.update_time = kst_now
                    s.commit()
                else:
                    new_user_hideout = UserHideOut(
                        user_email=user_email,
                        item_list=[],
                        complete_list=complete_list,
                        update_time=kst_now,
                    )
                    s.add(new_user_hideout)
                    s.commit()
                return HideoutService.get_station(user_email)
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def save_station_item(item_list: List[ItemType], user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            item_list_json = [item.model_dump() for item in item_list]

            utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
            kst_now = utc_now.astimezone(pytz.timezone("Asia/Seoul"))

            with session() as s:
                user_hideout = (
                    s.query(UserHideOut).filter_by(user_email=user_email).first()
                )

                if user_hideout:
                    user_hideout.item_list = item_list_json
                    user_hideout.update_time = kst_now
                else:
                    user_hideout = UserHideOut(
                        user_email=user_email,
                        item_list=item_list_json,
                        update_time=kst_now,
                    )
                    s.add(user_hideout)

                s.commit()
                return user_hideout

        except Exception as e:
            print("오류 발생:", e)
            return None
