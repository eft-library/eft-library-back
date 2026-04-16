import html
import logging
import re

from api.news.models import InformationV3, WipeV3
from database import V3Database
from sqlalchemy import func, desc

logger = logging.getLogger("api.wipe")


class NewsServiceV3:
    PREVIEW_LENGTH = 140

    # 미리보기도 프론트 말고 백에서 잘라 보내기
    @staticmethod
    def _build_preview_text_v3(content: str | None):
        if content is None:
            return None

        plain_text = re.sub(r"<[^>]+>", " ", content)
        plain_text = html.unescape(plain_text)
        plain_text = re.sub(r"\s+", " ", plain_text).strip()

        if len(plain_text) <= NewsServiceV3.PREVIEW_LENGTH:
            return plain_text

        return f"{plain_text[:NewsServiceV3.PREVIEW_LENGTH].rstrip()}..."

    @staticmethod
    def _serialize_information_v3(information: InformationV3):
        return {
            "id": information.id,
            "information_type": information.information_type,
            "title_en": information.title_en,
            "title_ko": information.title_ko,
            "title_ja": information.title_ja,
            "content_en": information.content_en,
            "content_ko": information.content_ko,
            "content_ja": information.content_ja,
            "update_time": information.update_time,
        }

    @staticmethod
    def _serialize_information_preview_v3(information: InformationV3):
        return {
            "id": information.id,
            "information_type": information.information_type,
            "title_en": information.title_en,
            "title_ko": information.title_ko,
            "title_ja": information.title_ja,
            "content_en": NewsServiceV3._build_preview_text_v3(information.content_en),
            "content_ko": NewsServiceV3._build_preview_text_v3(information.content_ko),
            "content_ja": NewsServiceV3._build_preview_text_v3(information.content_ja),
            "update_time": information.update_time,
        }

    @staticmethod
    def get_wipe_v3():
        try:
            with V3Database.SessionLocal() as s:
                wipe = s.query(WipeV3).order_by(desc(WipeV3.season_start)).all()
                return wipe
        except Exception as e:
            logger.error(
                f"get_wipe_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_information_list_v3(page: int, page_size: int, info_type: str):
        try:
            offset = (page - 1) * page_size
            with V3Database.SessionLocal() as s:
                total_count = (
                    s.query(func.count(InformationV3.id))
                    .filter(InformationV3.information_type == info_type)
                    .scalar()
                )

                max_pages = (total_count // page_size) + (
                    1 if total_count % page_size > 0 else 0
                )

                information_list = (
                    s.query(InformationV3)
                    .filter(InformationV3.information_type == info_type)
                    .order_by(desc(InformationV3.update_time))
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )

                return {
                    "data": [
                        NewsServiceV3._serialize_information_preview_v3(information)
                        for information in information_list
                    ],
                    "total_count": total_count,
                    "max_pages": max_pages,
                    "current_page": page,
                }
        except Exception as e:
            logger.exception(f"get_information_list_v3 error: {e}")
            return None

    @staticmethod
    def get_information_by_id_v3(info_id: str, info_type: str):
        try:
            with V3Database.SessionLocal() as s:
                information = (
                    s.query(InformationV3)
                    .filter(
                        InformationV3.id == info_id,
                        InformationV3.information_type == info_type,
                    )
                    .first()
                )

                if not information:
                    return None

                above_infos = (
                    s.query(InformationV3)
                    .filter(
                        InformationV3.information_type == info_type,
                        InformationV3.update_time > information.update_time,
                    )
                    .order_by(InformationV3.update_time.asc())
                    .limit(2)
                    .all()
                )
                below_infos = (
                    s.query(InformationV3)
                    .filter(
                        InformationV3.information_type == info_type,
                        InformationV3.update_time < information.update_time,
                    )
                    .order_by(InformationV3.update_time.desc())
                    .limit(2)
                    .all()
                )

                information_group = [
                    *[
                        NewsServiceV3._serialize_information_preview_v3(group_info)
                        for group_info in above_infos
                    ],
                    NewsServiceV3._serialize_information_preview_v3(information),
                    *[
                        NewsServiceV3._serialize_information_preview_v3(group_info)
                        for group_info in below_infos
                    ],
                ]
                information_group.sort(
                    key=lambda information_data: information_data["update_time"],
                    reverse=True,
                )

                return {
                    "information": NewsServiceV3._serialize_information_v3(information),
                    "information_group": information_group,
                }
        except Exception as e:
            logger.exception(f"get_information_by_id_v3 error: {e}")
            return None
