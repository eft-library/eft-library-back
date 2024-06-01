from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, TEXT
from sqlalchemy.dialects.postgresql import ARRAY

from database import DataBaseConnector


class TableColumn(DataBaseConnector.Base):
    """
    Table Column
    """

    __tablename__ = "tkw_table_column"

    id = Column(Integer, primary_key=True)
    value_en = Column(ARRAY(TEXT))
    value_kr = Column(ARRAY(TEXT))
    json_value = Column(JSON)
    type = Column(String)
    update_time = Column(TIMESTAMP)
