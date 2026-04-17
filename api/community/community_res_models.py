from sqlalchemy import BIGINT, BOOLEAN, INTEGER, TEXT, TIMESTAMP, Column, ForeignKey
from sqlalchemy.orm import relationship

from database import V3Database


class CommunityPostsV3(V3Database.Base):
    __tablename__ = "community_posts"

    id = Column(BIGINT, primary_key=True)
    slug = Column(TEXT)
    user_email = Column(TEXT)
    category = Column(TEXT)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    delete_by_user = Column(BOOLEAN)
    delete_by_admin = Column(BOOLEAN)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)

    hot_issue = relationship("CommunityPostsHotIssueV3", back_populates="post")


class CommunityPostsReactionsV3(V3Database.Base):
    __tablename__ = "community_posts_reactions"

    post_id = Column(BIGINT, primary_key=True)
    user_email = Column(TEXT, primary_key=True)
    reaction_type = Column(INTEGER)
    update_time = Column(TIMESTAMP)


class CommunityPostsViewV3(V3Database.Base):
    __tablename__ = "community_posts_views"

    post_id = Column(BIGINT, primary_key=True)
    view_count = Column(BIGINT)


class CommunityPostsHotIssueV3(V3Database.Base):
    __tablename__ = "community_posts_hot_issue"

    post_id = Column(BIGINT, ForeignKey("community_posts.id"), primary_key=True)
    issue_time = Column(TIMESTAMP)
    post = relationship("CommunityPostsV3", back_populates="hot_issue")


class UserFollowsV3(V3Database.Base):
    __tablename__ = "user_follows"

    follower_email = Column(TEXT, primary_key=True)
    following_email = Column(TEXT, primary_key=True)
    create_time = Column(TIMESTAMP)


class CommunityPostsBookmarkV3(V3Database.Base):
    __tablename__ = "community_posts_bookmark"

    email = Column(TEXT, primary_key=True)
    post_id = Column(BIGINT, primary_key=True)
    create_time = Column(TIMESTAMP)


class PostReportV3(V3Database.Base):
    __tablename__ = "post_report"

    id = Column(INTEGER, primary_key=True)
    target_post_id = Column(BIGINT)
    request_email = Column(TEXT)
    target_email = Column(TEXT)
    reason_type = Column(TEXT)
    reason = Column(TEXT)
    create_time = Column(TIMESTAMP)
