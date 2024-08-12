from sqlalchemy import func, desc

from api.event.models import Event
from database import DataBaseConnector
from sqlalchemy.orm import subqueryload


class EventService:

    @staticmethod
    def get_event_quest(page: int, page_size: int):
        try:
            session = DataBaseConnector.create_session_factory()
            offset = (page - 1) * page_size
            with session() as s:
                # 전체 행 수 조회
                total_count = s.query(func.count(Event.id)).scalar()

                # 최대 페이지 수 계산
                max_pages = (total_count // page_size) + (
                    1 if total_count % page_size > 0 else 0
                )

                # 현재 페이지의 데이터 조회
                event_list = (
                    s.query(Event)
                    .order_by(desc(Event.update_time))
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )

                return {
                    "data": event_list,
                    "total_count": total_count,
                    "max_pages": max_pages,
                    "current_page": page,
                }
        except Exception as e:
            print("오류 발생:", e)
            return None
