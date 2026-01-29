from api.news.models import Wipe, Event, Notice, PatchNotes
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
            print("get_event_quest 오류:", e)
            return None

    @staticmethod
    def get_event_by_id(event_id: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:

                # 현재 페이지의 데이터 조회
                event = s.query(Event).filter(Event.id == event_id).first()
                event_group_query = text(NewsUtil.get_event_group())
                param = {"id": event_id}
                result = s.execute(event_group_query, param)
                event_group = [dict(row._mapping) for row in result]

                result_dict = {
                    "information": event,
                    "information_group": event_group,
                }

                return result_dict
        except Exception as e:
            print("get_event_by_id 오류:", e)
            return None

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
            print("get_notice 오류:", e)
            return None

    @staticmethod
    def get_notice_by_id(notice_id: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:

                # 현재 페이지의 데이터 조회
                notice = s.query(Notice).filter(Notice.id == notice_id).first()
                notice_group_query = text(NewsUtil.get_notice_group())
                param = {"id": notice_id}
                result = s.execute(notice_group_query, param)
                notice_group = [dict(row._mapping) for row in result]

                result_dict = {"information": notice, "information_group": notice_group}

                return result_dict
        except Exception as e:
            print("get_notice_by_id 오류:", e)
            return None

    @staticmethod
    def get_patch_notes(page: int, page_size: int):
        try:
            session = DataBaseConnector.create_session_factory()
            offset = (page - 1) * page_size
            with session() as s:
                # 전체 행 수 조회
                total_count = s.query(func.count(PatchNotes.id)).scalar()

                # 최대 페이지 수 계산
                max_pages = (total_count // page_size) + (
                    1 if total_count % page_size > 0 else 0
                )

                # 현재 페이지의 데이터 조회
                notice_list = (
                    s.query(PatchNotes)
                    .order_by(desc(PatchNotes.update_time))
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
            print("get_patch_notes 오류:", e)
            return None

    @staticmethod
    def get_patch_notes_by_id(patch_notes_id: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:

                # 현재 페이지의 데이터 조회
                patch_notes = (
                    s.query(PatchNotes).filter(PatchNotes.id == patch_notes_id).first()
                )
                patch_notes_group_query = text(NewsUtil.get_patch_notes_group())
                param = {"id": patch_notes_id}
                result = s.execute(patch_notes_group_query, param)
                patch_notes_group = [dict(row._mapping) for row in result]

                result_dict = {
                    "information": patch_notes,
                    "information_group": patch_notes_group,
                }

                return result_dict
        except Exception as e:
            print("get_patch_notes_by_id 오류:", e)
            return None
