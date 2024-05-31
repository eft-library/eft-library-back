from api.table_column.models import TableColumn
from database import DataBaseConnector


class TableColumnService:
    @staticmethod
    def get_all_column():
        """
        column 전체 조회
        """
        try:
            session = DataBaseConnector.create_session()
            column_list = session.query(TableColumn).all()
            session.close()
            return column_list
        except Exception as e:
            print("오류 발생:", e)
        return None
