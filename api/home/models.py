from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship

from database import Database


class MenuGroup(Database.Base):
    __tablename__ = "menu_groups"

    id = Column(String, primary_key=True)
    name_en = Column(String)
    name_ko = Column(String)
    name_ja = Column(String)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)
    sub_menus = relationship(
        "MenuSubGroup",
        backref="main_menu",
        order_by=lambda: MenuSubGroup.sort_order,
    )


class MenuSubGroup(Database.Base):
    __tablename__ = "menu_sub_groups"

    id = Column(String, primary_key=True)
    name_en = Column(String)
    name_ko = Column(String)
    name_ja = Column(String)
    parent_group_id = Column(String, ForeignKey("menu_groups.id"))
    url = Column(String)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class MainInfo(Database.Base):
    __tablename__ = "main_contents"

    id = Column(String, primary_key=True)
    name_en = Column(String)
    name_ko = Column(String)
    name_ja = Column(String)
    url = Column(String)
    image = Column(String)
    sort_order = Column(Integer)
    update_time = Column(TIMESTAMP)


class NewsItem(Database.Base):
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
