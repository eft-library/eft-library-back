from sqlalchemy import Column, String, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship

from database import DataBaseConnector


class FilterGroup(DataBaseConnector.Base):
    """
    filter group
    """

    __tablename__ = "filter_group_i18n"

    value = Column(String, primary_key=True)
    name = Column(JSON)
    update_time = Column(TIMESTAMP)
    sub = relationship("FilterSubGroup", backref="FilterGroup")


class FilterSubGroup(DataBaseConnector.Base):
    """
    filter sub FilterSubCategories
    """

    __tablename__ = "filter_sub_group_i18n"

    value = Column(String, primary_key=True)
    name = Column(JSON)
    parent_value = Column(String, ForeignKey("filter_group_i18n.value"))
    update_time = Column(TIMESTAMP)
