from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, Integer
from sqlalchemy.orm import relationship

from database import DataBaseConnector


class MainMenu(DataBaseConnector.Base):
    """
    MainMenu
    """

    __tablename__ = "tkl_main_menu"

    value = Column(String, primary_key=True)
    en_name = Column(String)
    kr_name = Column(String)
    link = Column(String)
    order = Column(Integer)
    image = Column(String)
    update_time = Column(TIMESTAMP)
    sub = relationship("SubMenu", backref="main_menu", order_by="SubMenu.order")


class SubMenu(DataBaseConnector.Base):
    """
    SubMenu
    """

    __tablename__ = "tkl_sub_menu"

    value = Column(String, primary_key=True)
    en_name = Column(String)
    kr_name = Column(String)
    parent_value = Column(String, ForeignKey("tkl_main_menu.value"))
    link = Column(String)
    order = Column(Integer)
    image = Column(String)
    update_time = Column(TIMESTAMP)


class MainInfo(DataBaseConnector.Base):
    """
    MainInfo
    """

    __tablename__ = "tkl_main"

    value = Column(String, primary_key=True)
    en_name = Column(String)
    kr_name = Column(String)
    link = Column(String)
    order = Column(Integer)
    image = Column(String)
    update_time = Column(TIMESTAMP)
