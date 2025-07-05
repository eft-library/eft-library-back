from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, Integer, Boolean, JSON
from sqlalchemy.orm import relationship

from database import DataBaseConnector


class MenuGroup(DataBaseConnector.Base):
    """
    MenuGroup
    """

    __tablename__ = "menu_group_i18n"

    value = Column(String, primary_key=True)
    name = Column(JSON)
    order = Column(Integer)
    update_time = Column(TIMESTAMP)
    sub_menus = relationship(
        "MenuSubGroup", backref="main_menu", order_by="MenuSubGroup.order"
    )


class MenuSubGroup(DataBaseConnector.Base):
    """
    MenuSubGroup
    """

    __tablename__ = "menu_sub_group_i18n"

    value = Column(String, primary_key=True)
    name = Column(JSON)
    parent_value = Column(String, ForeignKey("menu_group_i18n.value"))
    link = Column(String)
    order = Column(Integer)
    update_time = Column(TIMESTAMP)


class MainInfo(DataBaseConnector.Base):
    """
    MainInfo
    """

    __tablename__ = "main_i18n"

    value = Column(String, primary_key=True)
    name = Column(JSON)
    link = Column(String)
    order = Column(Integer)
    image = Column(String)
    use_slide = Column(Boolean)
    slide_image = Column(String)
    update_time = Column(TIMESTAMP)
