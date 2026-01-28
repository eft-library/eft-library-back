from pydantic import BaseModel


class SaveScore(BaseModel):
    nickname: str
    game_type: str
    score: int
