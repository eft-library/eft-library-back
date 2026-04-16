from database import V3Database
from sqlalchemy import Column, INTEGER, TEXT, BIGINT
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP


class UserMinigameScoreV3(V3Database.Base):
    __tablename__ = "user_minigame_score"

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    nickname = Column(TEXT)
    game_type = Column(TEXT)
    score = Column(BIGINT)
    create_time = Column(TIMESTAMP(timezone=True), server_default=func.now())
