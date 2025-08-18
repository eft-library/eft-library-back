from sqlalchemy import Column, TIMESTAMP, TEXT, INTEGER
from database import DataBaseConnector


class CommentReaction(DataBaseConnector.Base):

    __tablename__ = "community_comments_reactions"

    comment_id = Column(TEXT, primary_key=True)
    user_email = Column(TEXT, primary_key=True)
    reaction_type = Column(INTEGER)
    update_time = Column(TIMESTAMP)
