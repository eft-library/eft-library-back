from sqlalchemy import func, desc, text

from api.notice.models import Notice
from database import DataBaseConnector
from api.notice.util import NoticeUtil


class NoticeService:

    @staticmethod
    def get_notice(page: int, page_size: int):
        try:
            session = DataBaseConnector.create_session_factory()
            offset = (page - 1) * page_size
            with session() as s:
                # 전체 행 수 조회
                total_count = s.query(func.count(Notice.id)).scalar()

                # 최대 페이지 수 계산
                max_pages = (total_count // page_size) + (
                    1 if total_count % page_size > 0 else 0
                )

                # 현재 페이지의 데이터 조회
                notice_list = (
                    s.query(Notice)
                    .order_by(desc(Notice.update_time))
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )

                return {
                    "data": notice_list,
                    "total_count": total_count,
                    "max_pages": max_pages,
                    "current_page": page,
                }
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_notice_by_id(notice_id: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:

                # 현재 페이지의 데이터 조회
                notice = s.query(Notice).filter(Notice.id == notice_id).first()
                notice_group_query = text(NoticeUtil.get_notice_group())
                param = {"id": notice_id}
                result = s.execute(notice_group_query, param)
                notice_group = [dict(row._mapping) for row in result]

                result_dict = {"information": notice, "information_group": notice_group}

                return result_dict
        except Exception as e:
            print("오류 발생:", e)
            return None
