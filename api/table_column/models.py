from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, TEXT
from sqlalchemy.dialects.postgresql import ARRAY

from database import DataBaseConnector


class TableColumn(DataBaseConnector.Base):
    """
    Table Column
    """

    __tablename__ = "tkw_table_column_info"

    column_id = Column(Integer, primary_key=True)
    column_value_en = Column(ARRAY(TEXT))
    column_value_kr = Column(ARRAY(TEXT))
    column_json_value = Column(JSON)
    column_type = Column(String)
    column_update_time = Column(TIMESTAMP)
