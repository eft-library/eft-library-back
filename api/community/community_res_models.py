from sqlalchemy import Column, BIGINT, TIMESTAMP, TEXT, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database import DataBaseConnector

class CommunityPosts(DataBaseConnector.Base):

    __tablename__ = "community_posts"

    id = Column(BIGINT, primary_key=True)
    slug = Column(TEXT)
    user_email = Column(TEXT)
    category = Column(TEXT)
    title = Column(TEXT)
    contents = Column(TEXT)
    thumbnail = Column(TEXT)
    delete_by_user = Column(Boolean)
    delete_by_admin = Column(Boolean)
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)

    hot_issue = relationship("CommunityPostsHotIssue", back_populates="post")

class CommunityPostsReactions(DataBaseConnector.Base):

    __tablename__ = "community_posts_reactions"

    post_id = Column(BIGINT, primary_key=True)
    user_email = Column(TEXT, primary_key=True)
    reaction_type = Column(TEXT)
    update_time = Column(TIMESTAMP)

class CommunityPostsView(DataBaseConnector.Base):

    __tablename__ = "community_posts_views"

    post_id = Column(BIGINT, primary_key=True)
    view_count = Column(BIGINT)

class CommunityPostsHotIssue(DataBaseConnector.Base):

    __tablename__ = "community_posts_hot_issue"

    post_id = Column(BIGINT, ForeignKey("community_posts.id"), primary_key=True)
    issue_time = Column(TIMESTAMP)
    post = relationship("CommunityPosts", back_populates="hot_issue")

