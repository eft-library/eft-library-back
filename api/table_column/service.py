from api.table_column.models import TableColumn
from database import DataBaseConnector


class TableColumnService:
    @staticmethod
    def get_all_column():
        """
        column 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                column_list = s.query(TableColumn).all()
                return column_list
        except Exception as e:
            print("오류 발생:", e)
        return None

    @staticmethod
    def get_column(column_key: str):
        """
        column 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                column_list = (
                    s.query(TableColumn).filter(TableColumn.id == column_key).first()
                )
                return column_list
        except Exception as e:
            print("오류 발생:", e)
        return None
