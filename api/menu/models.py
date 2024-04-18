from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, INT
from sqlalchemy.orm import relationship

from database import DataBaseConnector


class MainMenu(DataBaseConnector.Base):
    """
    MainMenu
    """
    __tablename__ = "tkw_main_menu_info"

    main_menu_value = Column(String, primary_key=True)
    main_menu_en_name = Column(String)
    main_menu_kr_name = Column(String)
    main_menu_link = Column(String)
    main_menu_order = Column(INT)
    main_menu_update_time = Column(TIMESTAMP)
    sub_menus = relationship("SubMenu", backref="main_menu")


class SubMenu(DataBaseConnector.Base):
    """
    SubMenu
    """
    __tablename__ = "tkw_sub_menu_info"

    sub_menu_value = Column(String, primary_key=True)
    sub_menu_en_name = Column(String)
    sub_menu_kr_name = Column(String)
    sub_menu_parent_value = Column(String, ForeignKey('tkw_main_menu_info.main_menu_value'))
    sub_menu_link = Column(String)
    sub_menu_update_time = Column(TIMESTAMP)
