import html
import logging
import re

from api.news.models import Information, Wipe
from database import Database
from sqlalchemy import func, desc

logger = logging.getLogger("api.wipe")


class NewsService:
    PREVIEW_LENGTH = 140

    # 미리보기도 프론트 말고 백에서 잘라 보내기
    @staticmethod
    def _build_preview_text(content: str | None):
        if content is None:
            return None

        plain_text = re.sub(r"<[^>]+>", " ", content)
        plain_text = html.unescape(plain_text)
        plain_text = re.sub(r"\s+", " ", plain_text).strip()

        if len(plain_text) <= NewsService.PREVIEW_LENGTH:
            return plain_text

        return f"{plain_text[:NewsService.PREVIEW_LENGTH].rstrip()}..."

    @staticmethod
    def _serialize_information(information: Information):
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
    def _serialize_information_preview(information: Information):
        return {
            "id": information.id,
            "information_type": information.information_type,
            "title_en": information.title_en,
            "title_ko": information.title_ko,
            "title_ja": information.title_ja,
            "content_en": NewsService._build_preview_text(information.content_en),
            "content_ko": NewsService._build_preview_text(information.content_ko),
            "content_ja": NewsService._build_preview_text(information.content_ja),
            "update_time": information.update_time,
        }

    @staticmethod
    def get_wipe():
        try:
            with Database.SessionLocal() as s:
                wipe = s.query(Wipe).order_by(desc(Wipe.season_start)).all()
                return wipe
        except Exception as e:
            logger.error(
                f"get_wipe_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_information_list(page: int, page_size: int, info_type: str):
        try:
            offset = (page - 1) * page_size
            with Database.SessionLocal() as s:
                total_count = (
                    s.query(func.count(Information.id))
                    .filter(Information.information_type == info_type)
                    .scalar()
                )

                max_pages = (total_count // page_size) + (
                    1 if total_count % page_size > 0 else 0
                )

                information_list = (
                    s.query(Information)
                    .filter(Information.information_type == info_type)
                    .order_by(desc(Information.update_time))
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )

                return {
                    "data": [
                        NewsService._serialize_information_preview(information)
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
    def get_information_by_id(info_id: str, info_type: str):
        try:
            with Database.SessionLocal() as s:
                information = (
                    s.query(Information)
                    .filter(
                        Information.id == info_id,
                        Information.information_type == info_type,
                    )
                    .first()
                )

                if not information:
                    return None

                above_infos = (
                    s.query(Information)
                    .filter(
                        Information.information_type == info_type,
                        Information.update_time > information.update_time,
                    )
                    .order_by(Information.update_time.asc())
                    .limit(2)
                    .all()
                )
                below_infos = (
                    s.query(Information)
                    .filter(
                        Information.information_type == info_type,
                        Information.update_time < information.update_time,
                    )
                    .order_by(Information.update_time.desc())
                    .limit(2)
                    .all()
                )

                information_group = [
                    *[
                        NewsService._serialize_information_preview(group_info)
                        for group_info in above_infos
                    ],
                    NewsService._serialize_information_preview(information),
                    *[
                        NewsService._serialize_information_preview(group_info)
                        for group_info in below_infos
                    ],
                ]
                information_group.sort(
                    key=lambda information_data: information_data["update_time"],
                    reverse=True,
                )

                return {
                    "information": NewsService._serialize_information(information),
                    "information_group": information_group,
                }
        except Exception as e:
            logger.exception(f"get_information_by_id_v3 error: {e}")
            return None
