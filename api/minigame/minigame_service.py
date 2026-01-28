from api.minigame.res_models import ItemFleaSummary, UserMinigameScore
from database import DataBaseConnector
from api.minigame.req_models import SaveScore


class MinigameService:

    @staticmethod
    def get_rng_item_list():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                rng_item_list = s.query(ItemFleaSummary).all()
                return rng_item_list
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def insert_user_minigame_score(result: SaveScore):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                new_score = UserMinigameScore(
                    nickname=result.nickname,
                    game_type=result.game_type,
                    score=result.score,
                )
                s.add(new_score)
                s.commit()
                s.refresh(new_score)  # 자동 생성 id 반영
                return new_score
        except Exception as e:
            print("오류 발생:", e)
            return None
