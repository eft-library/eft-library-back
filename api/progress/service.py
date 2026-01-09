from api.progress.progress_req_models import ProgressItemList
from api.progress.progress_res_models import UserProgressItem, ProgressItem
from database import DataBaseConnector
from sqlalchemy import text
from datetime import datetime
import pytz


class ProgressService:

    @staticmethod
    def get_user_progress(user_email: str | None):
        try:
            session = DataBaseConnector.create_session_factory()

            with session() as s:
                # 전체 아이템 목록
                all_kappa_list = (
                    s.query(ProgressItem)
                    .filter(ProgressItem.progress_type == "Kappa")
                    .all()
                )

                all_rebirth_list = (
                    s.query(ProgressItem)
                    .filter(ProgressItem.progress_type == "Rebirth")
                    .all()
                )

                user_kappa = []
                user_rebirth = []

                if user_email:
                    user_kappa = list(
                        chain.from_iterable(
                            upi.item_list
                            for upi in s.query(UserProgressItem)
                            .filter(
                                UserProgressItem.user_email == user_email,
                                UserProgressItem.progress_type == "Kappa",
                            )
                            .all()
                        )
                    )

                    user_rebirth = list(
                        chain.from_iterable(
                            upi.item_list
                            for upi in s.query(UserProgressItem)
                            .filter(
                                UserProgressItem.user_email == user_email,
                                UserProgressItem.progress_type == "Rebirth",
                            )
                            .all()
                        )
                    )

                return {
                    "userRebirthList": user_rebirth,
                    "userKappaList": user_kappa,
                    "allKappaItemList": all_kappa_list,
                    "allRebirthList": all_rebirth_list,
                }

        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def update_progress(progress_item_list: ProgressItemList, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()

            with session() as s:

                def now_kst():
                    return datetime.now(pytz.timezone("Asia/Seoul"))

                def upsert_progress(progress_type: str, item_list):
                    item = (
                        s.query(UserProgressItem)
                        .filter(
                            UserProgressItem.user_email == user_email,
                            UserProgressItem.progress_type == progress_type,
                        )
                        .first()
                    )

                    if item is None:
                        item = UserProgressItem(
                            user_email=user_email,
                            progress_type=progress_type,
                            item_list=item_list,
                            update_time=now_kst(),
                        )
                        s.add(item)
                    else:
                        item.item_list = item_list
                        item.update_time = now_kst()

                upsert_progress("Rebirth", progress_item_list.userRebirth)
                upsert_progress("Kappa", progress_item_list.userKappa)

                s.commit()

            # commit 이후 새 세션으로 조회 (권장)
            return ProgressService.get_user_progress(user_email)

        except Exception as e:
            print("오류 발생:", e)
            return None
