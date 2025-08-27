from sqlalchemy import Column, TIMESTAMP, TEXT, INTEGER
from database import DataBaseConnector


class CommentReaction(DataBaseConnector.Base):

    __tablename__ = "community_comments_reactions"

    comment_id = Column(TEXT, primary_key=True)
    user_email = Column(TEXT, primary_key=True)
    reaction_type = Column(INTEGER)
    update_time = Column(TIMESTAMP)


class CommentReport(DataBaseConnector.Base):

    __tablename__ = "comment_report"

    id = Column(INTEGER, primary_key=True)
    comment_id = Column(TEXT)
    reporter_email = Column(TEXT)
    reported_email = Column(TEXT)
    reason_type = Column(TEXT)
    reason = Column(TEXT)
    create_time = Column(TIMESTAMP)
