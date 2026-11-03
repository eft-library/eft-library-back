from api.progress.progress_req_models import ProgressItemList
from api.progress.progress_res_models import (
    ProgressItem,
    UserProgressItem,
)
from api.item.models import Item
from database import Database
from datetime import datetime
import pytz
import logging
from sqlalchemy.dialects.postgresql import insert

logger = logging.getLogger("api.progress")


class ProgressService:
    @staticmethod
    def _serialize_progress_item(progress_item: ProgressItem, item: Item | None):
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
    def _get_user_item_ids(s, user_email: str | None, progress_type: str):
        if not user_email:
            return []

        user_progress = (
            s.query(UserProgressItem)
            .filter(
                UserProgressItem.email == user_email,
                UserProgressItem.progress_type == progress_type,
            )
            .first()
        )

        return user_progress.item_list if user_progress else []

    @staticmethod
    def _get_progress_items(s, progress_type: str):
        rows = (
            s.query(ProgressItem, Item)
            .outerjoin(Item, ProgressItem.id == Item.id)
            .filter(ProgressItem.progress_type == progress_type)
            .order_by(Item.name_en, ProgressItem.id)
            .all()
        )
        return [
            ProgressService._serialize_progress_item(progress_item, item)
            for progress_item, item in rows
        ]

    @staticmethod
    def get_user_progress(user_email: str | None):
        try:
            with Database.SessionLocal() as s:
                user_kappa = ProgressService._get_user_item_ids(
                    s, user_email, "Kappa"
                )
                user_rebirth = ProgressService._get_user_item_ids(
                    s, user_email, "Rebirth"
                )

                return {
                    "userRebirthList": user_rebirth,
                    "userKappaList": user_kappa,
                    "allKappaItemList": ProgressService._get_progress_items(
                        s, "Kappa"
                    ),
                    "allRebirthList": ProgressService._get_progress_items(
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
    def update_progress(progress_item_list: ProgressItemList, user_email: str):
        try:
            with Database.SessionLocal() as s:

                def upsert_progress(progress_type: str, item_list):
                    stmt = insert(UserProgressItem).values(
                        email=user_email,
                        progress_type=progress_type,
                        item_list=item_list,
                        update_time=datetime.now(pytz.timezone("Asia/Seoul")),
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=[
                            UserProgressItem.email,
                            UserProgressItem.progress_type,
                        ],
                        set_={
                            "item_list": stmt.excluded.item_list,
                            "update_time": stmt.excluded.update_time,
                        },
                    )
                    s.execute(stmt)

                upsert_progress("Rebirth", progress_item_list.userRebirth)
                upsert_progress("Kappa", progress_item_list.userKappa)

                s.commit()

            return ProgressService.get_user_progress(user_email)

        except Exception as e:
            logger.error(
                f"update_progress_v3: {progress_item_list.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None
