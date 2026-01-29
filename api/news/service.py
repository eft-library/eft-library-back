from api.news.models import Wipe, Information
from database import DataBaseConnector
from sqlalchemy import func, desc, text
from api.news.util import NewsUtil

import logging

logger = logging.getLogger("api.wipe")


class NewsService:

    @staticmethod
    def get_wipe():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                wipe = s.query(Wipe).order_by(desc(Wipe.season_start)).all()
                return wipe
        except Exception as e:
            logger.error(
                f"get_wipe error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_information_list(page: int, page_size: int, info_type: str):
        try:
            session = DataBaseConnector.create_session_factory()
            offset = (page - 1) * page_size
            with session() as s:
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

    @staticmethod
    def get_information_by_id(info_id: str, info_type: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
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
