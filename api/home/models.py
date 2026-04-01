from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, Integer, Boolean, JSON
from sqlalchemy.orm import relationship

from database import DataBaseConnector, V3Database


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
    update_time = Column(TIMESTAMP)


class MenuGroupV3(V3Database.Base):
    __tablename__ = "menu_groups"

    id = Column(String, primary_key=True)
    name_en = Column(String)
    name_ko = Column(String)
    name_ja = Column(String)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)
    sub_menus = relationship(
        "MenuSubGroupV3",
        backref="main_menu",
        order_by="MenuSubGroupV3.sort_order",
    )


class MenuSubGroupV3(V3Database.Base):
    __tablename__ = "menu_sub_groups"

    id = Column(String, primary_key=True)
    name_en = Column(String)
    name_ko = Column(String)
    name_ja = Column(String)
    parent_group_id = Column(String, ForeignKey("menu_groups.id"))
    url = Column(String)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class MainInfoV3(V3Database.Base):
    __tablename__ = "main_contents"

    id = Column(String, primary_key=True)
    name_en = Column(String)
    name_ko = Column(String)
    name_ja = Column(String)
    url = Column(String)
    image = Column(String)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class NewsItemV3(V3Database.Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True)
    news_type = Column(String)
    title_en = Column(String)
    title_ko = Column(String)
    title_ja = Column(String)
    link = Column(String)
    is_new = Column(Boolean)
    is_renewal = Column(Boolean)
    is_active = Column(Boolean)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class AutocompleteItemV3(V3Database.Base):
    __tablename__ = "autocomplete_items"

    url = Column(String, primary_key=True)
    autocomplete_text_en = Column(String)
    autocomplete_text_ko = Column(String)
    autocomplete_text_ja = Column(String)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)
