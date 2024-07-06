from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship

from database import DataBaseConnector


class FilterCategories(DataBaseConnector.Base):
    """
    filter categories
    """

    __tablename__ = "tkl_filter_categories"

    value = Column(String, primary_key=True)
    en = Column(String)
    kr = Column(String)
    update_time = Column(TIMESTAMP)
    sub = relationship("FilterSubCategories", backref="FilterCategories")


class FilterSubCategories(DataBaseConnector.Base):
    """
    filter sub categories
    """

    __tablename__ = "tkl_filter_sub_categories"

    value = Column(String, primary_key=True)
    en = Column(String)
    kr = Column(String)
    parent_value = Column(String, ForeignKey("tkl_filter_categories.value"))
    image = Column(String)
    update_time = Column(TIMESTAMP)
