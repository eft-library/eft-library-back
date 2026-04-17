from sqlalchemy import Column, INTEGER, TEXT, TIMESTAMP

from database import V3Database


class CommentReactionV3(V3Database.Base):
    __tablename__ = "community_comments_reactions"

    comment_id = Column(TEXT, primary_key=True)
    email = Column(TEXT, primary_key=True)
    reaction_type = Column(INTEGER)
    reaction_time = Column(TIMESTAMP)


class CommentReportV3(V3Database.Base):
    __tablename__ = "comment_report"

    id = Column(INTEGER, primary_key=True)
    target_comment_id = Column(TEXT)
    request_email = Column(TEXT)
    target_email = Column(TEXT)
    reason_type = Column(TEXT)
    reason = Column(TEXT)
    create_time = Column(TIMESTAMP)
