from api.progress.progress_req_models import ProgressItemList
from api.progress.progress_res_models import UserProgressItem
from database import DataBaseConnector
from sqlalchemy import text
from datetime import datetime
import pytz


class ProgressService:

    @staticmethod
    def get_user_progress(user_email):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text("")
                kappa_result = s.execute(query, {"user_email": user_email})
                rebirth_result = s.execute(query, {"user_email": user_email})
                if kappa_result and rebirth_result:
                    return {
                        "rebirthItemList": [
                            dict(row) for row in rebirth_result.mappings()
                        ],
                        "kappaItemList": [dict(row) for row in kappa_result.mappings()],
                    }
                else:
                    return {"rebirthItemList": [], "kappaItemList": []}
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def update_progress(progress_item_list: ProgressItemList, user_email: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:

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
                        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
                        kst = pytz.timezone("Asia/Seoul")
                        kst_now = utc_now.astimezone(kst)
                        item = UserProgressItem(
                            user_email=user_email,
                            progress_type=progress_type,
                            item_list=item_list,
                            update_time=kst_now,
                        )
                        s.add(item)
                    else:
                        item.item_list = item_list

                # Rebirth
                upsert_progress("Rebirth", progress_item_list.rebirthItemList)

                # Kappa
                upsert_progress("Kappa", progress_item_list.kappaItemList)

                s.commit()

                # 이후 조회 로직 (예시)
                query = text(
                    """
                    SELECT *
                    FROM user_progress_items
                    WHERE user_email = :user_email
                """
                )
                result = s.execute(query, {"user_email": user_email})
                new_user_quests = [dict(row) for row in result.mappings()]

                return new_user_quests

        except Exception as e:
            print("오류 발생:", e)
            return None
