import html
import logging
import re

from api.news.models import Wipe, Information, InformationV3, WipeV3
from database import DataBaseConnector, V3Database
from sqlalchemy import func, desc, text
from api.news.util import NewsUtil

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
            "content_en": NewsService._build_preview_text(information.content_en),
            "content_ko": NewsService._build_preview_text(information.content_ko),
            "content_ja": NewsService._build_preview_text(information.content_ja),
            "update_time": information.update_time,
        }

    # TODO: 삭제 예정
    @staticmethod
    def get_wipe():
        try:

            with DataBaseConnector.SessionLocal() as s:
                wipe = s.query(Wipe).order_by(desc(Wipe.season_start)).all()
                return wipe
        except Exception as e:
            logger.error(
                f"get_wipe error: {e}",
                exc_info=True,
            )
            return None

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

    # TODO: 삭제 예정
    @staticmethod
    def get_information_list(page: int, page_size: int, info_type: str):
        try:

            offset = (page - 1) * page_size
            with DataBaseConnector.SessionLocal() as s:
                total_count = (
                    s.query(func.count(Information.id))
                    .filter(Information.type == info_type)
                    .scalar()
                )

                # 최대 페이지 수 계산
                max_pages = (total_count // page_size) + (
                    1 if total_count % page_size > 0 else 0
                )

                # 현재 페이지의 데이터 조회 (type으로 필터링)
                information_list = (
                    s.query(Information)
                    .filter(Information.type == info_type)
                    .order_by(desc(Information.update_time))
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )

                return {
                    "data": information_list,
                    "total_count": total_count,
                    "max_pages": max_pages,
                    "current_page": page,
                }
        except Exception as e:
            logger.exception(f"get_information_list error: {e}")
            return None

    # TODO: 삭제 예정
    @staticmethod
    def get_information_by_id(info_id: str, info_type: str):
        try:

            with DataBaseConnector.SessionLocal() as s:
                information = (
                    s.query(Information)
                    .filter(Information.id == info_id, Information.type == info_type)
                    .first()
                )

                if not information:
                    return None

                information_group_query = text(NewsUtil.get_information_group())
                param = {"id": info_id, "type": info_type}
                result = s.execute(information_group_query, param)
                information_group = [dict(row._mapping) for row in result]

                result_dict = {
                    "information": information,
                    "information_group": information_group,
                }

                return result_dict
        except Exception as e:
            logger.exception(f"get_information_by_id error: {e}")
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
                        NewsService._serialize_information_preview_v3(information)
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
                        NewsService._serialize_information_preview_v3(group_info)
                        for group_info in above_infos
                    ],
                    NewsService._serialize_information_preview_v3(information),
                    *[
                        NewsService._serialize_information_preview_v3(group_info)
                        for group_info in below_infos
                    ],
                ]
                information_group.sort(
                    key=lambda information_data: information_data["update_time"],
                    reverse=True,
                )

                return {
                    "information": NewsService._serialize_information_v3(information),
                    "information_group": information_group,
                }
        except Exception as e:
            logger.exception(f"get_information_by_id_v3 error: {e}")
            return None
