from api.progress.progress_req_models import ProgressItemList
from api.progress.progress_res_models import (
    ProgressItemV3,
    UserProgressItemV3,
)
from api.item.models import ItemV3
from database import V3Database
from datetime import datetime
import pytz
import logging

logger = logging.getLogger("api.progress")


class ProgressServiceV3:
    @staticmethod
    def _serialize_progress_item_v3(progress_item: ProgressItemV3, item: ItemV3 | None):
        return {
            "id": progress_item.id,
            "progress_type": progress_item.progress_type,
            "update_time": progress_item.update_time,
            "item": (
                {
                    "id": item.id,
                    "normalized_name": item.normalized_name,
                    "name_en": item.name_en,
                    "name_ko": item.name_ko,
                    "name_ja": item.name_ja,
                    "image": item.image,
                    "width": item.width,
                    "height": item.height,
                }
                if item is not None
                else None
            ),
        }

    @staticmethod
    def _get_user_item_ids_v3(s, user_email: str | None, progress_type: str):
        if not user_email:
            return []

        user_progress = (
            s.query(UserProgressItemV3)
            .filter(
                UserProgressItemV3.email == user_email,
                UserProgressItemV3.progress_type == progress_type,
            )
            .first()
        )

        return user_progress.item_list if user_progress else []

    @staticmethod
    def _get_progress_items_v3(s, progress_type: str):
        rows = (
            s.query(ProgressItemV3, ItemV3)
            .outerjoin(ItemV3, ProgressItemV3.id == ItemV3.id)
            .filter(ProgressItemV3.progress_type == progress_type)
            .order_by(ItemV3.name_en, ProgressItemV3.id)
            .all()
        )
        return [
            ProgressServiceV3._serialize_progress_item_v3(progress_item, item)
            for progress_item, item in rows
        ]

    @staticmethod
    def get_user_progress_v3(user_email: str | None):
        try:
            with V3Database.SessionLocal() as s:
                user_kappa = ProgressServiceV3._get_user_item_ids_v3(
                    s, user_email, "Kappa"
                )
                user_rebirth = ProgressServiceV3._get_user_item_ids_v3(
                    s, user_email, "Rebirth"
                )

                return {
                    "userRebirthList": user_rebirth,
                    "userKappaList": user_kappa,
                    "allKappaItemList": ProgressServiceV3._get_progress_items_v3(
                        s, "Kappa"
                    ),
                    "allRebirthList": ProgressServiceV3._get_progress_items_v3(
                        s, "Rebirth"
                    ),
                }

        except Exception as e:
            logger.error(
                f"get_user_progress_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def update_progress_v3(progress_item_list: ProgressItemList, user_email: str):
        try:
            with V3Database.SessionLocal() as s:

                def now_kst():
                    return datetime.now(pytz.timezone("Asia/Seoul"))

                def upsert_progress(progress_type: str, item_list):
                    item = (
                        s.query(UserProgressItemV3)
                        .filter(
                            UserProgressItemV3.email == user_email,
                            UserProgressItemV3.progress_type == progress_type,
                        )
                        .first()
                    )

                    if item is None:
                        item = UserProgressItemV3(
                            email=user_email,
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

            return ProgressServiceV3.get_user_progress_v3(user_email)

        except Exception as e:
            logger.error(
                f"update_progress_v3: {progress_item_list.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None
