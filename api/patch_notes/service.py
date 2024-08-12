from sqlalchemy import func, desc, text

from api.patch_notes.models import PatchNotes
from database import DataBaseConnector
from api.patch_notes.util import PatchNotesUtil


class PatchNotesService:

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
            print("오류 발생:", e)
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
                patch_notes_group_query = text(PatchNotesUtil.get_patch_notes_group())
                param = {"id": patch_notes_id}
                result = s.execute(patch_notes_group_query, param)
                patch_notes_group = [dict(row._mapping) for row in result]

                result_dict = {
                    "information": patch_notes,
                    "information_group": patch_notes_group,
                }

                return result_dict
        except Exception as e:
            print("오류 발생:", e)
            return None
