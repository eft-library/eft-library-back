from sqlalchemy import Column, String, JSON, Integer, TIMESTAMP, TEXT, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from database import DataBaseConnector


class Boss(DataBaseConnector.Base):
    """
    Boss
    """

    __tablename__ = "tkl_boss"

    id = Column(TEXT, primary_key=True)
    name_en = Column(String)
    name_kr = Column(String)
    faction = Column(String)
    location_spawn_chance_en = Column(JSON)
    location_spawn_chance_kr = Column(JSON)
    followers_en = Column(ARRAY(TEXT))
    followers_kr = Column(ARRAY(TEXT))
    image = Column(TEXT)
    health_total = Column(Integer)
    location_guide = Column(TEXT)
    spawn = Column(ARRAY(TEXT))
    order = Column(Integer)
    update_time = Column(TIMESTAMP)
    sub_followers = relationship("Followers", backref="boss")


class Followers(DataBaseConnector.Base):
    """
    Followers
    """

    __tablename__ = "tkl_followers"

    id = Column(TEXT, primary_key=True)
    boss_id = Column(TEXT, ForeignKey("tkl_boss.id"))
    name_en = Column(String)
    name_kr = Column(String)
    health_image = Column(TEXT)
    loot = relationship("FollowersLoot", backref="followers")


class FollowersLoot(DataBaseConnector.Base):
    """
    Followers Loot
    """

    __tablename__ = "tkl_followers_loot"

    item_id = Column(TEXT, primary_key=True)
    boss_id = Column(TEXT)
    follower_id = Column(TEXT, ForeignKey("tkl_followers.id"))
    item_name_en = Column(TEXT)
    item_name_kr = Column(TEXT)
    follower_name_en = Column(TEXT)
    follower_name_kr = Column(TEXT)
    item_type = Column(TEXT)
    item_type_en = Column(TEXT)
    item_type_kr = Column(TEXT)
    item_image = Column(TEXT)
    link = Column(TEXT)
