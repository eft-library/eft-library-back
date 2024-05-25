from api.table_column.models import TableColumn
from database import DataBaseConnector


class TableColumnService:
    @staticmethod
    def get_column(column_id):
        """
        column 조회
        """
        try:
            session = DataBaseConnector.create_session()
            weapon_column = session.query(TableColumn).filter(TableColumn.column_type == column_id).all()
            session.close()
            return weapon_column
        except Exception as e:
            print("오류 발생:", e)
        return None

