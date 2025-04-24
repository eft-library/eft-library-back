from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP

from database import DataBaseConnector


class DynamicInfo(DataBaseConnector.Base):
    """
    DynamicInfo
    """

    __tablename__ = "dynamic_info_i18n"

    id = Column(Integer, primary_key=True)
    json_value = Column(JSON)
    update_time = Column(TIMESTAMP)
