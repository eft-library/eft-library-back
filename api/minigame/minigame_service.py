from api.minigame.res_models import ItemFleaSummary, UserMinigameScore
from database import DataBaseConnector
from api.minigame.req_models import SaveScore
from sqlalchemy import text
from api.minigame.util import MinigameUtil
import logging

logger = logging.getLogger("api.minigame")


class MinigameService:

    @staticmethod
    def get_rng_item_list():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                rng_item_list = s.query(ItemFleaSummary).all()
                return rng_item_list
        except Exception as e:
            logger.error(
                f"get_rng_item_list error: {e}",
                exc_info=True,
            )
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
            logger.error(
                f"insert_user_minigame_score: {result.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_all_rng_item_rank():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(MinigameUtil.get_rng_item_rank())
                result = s.execute(query)
                data = [dict(row) for row in result.mappings()]
            return data
        except Exception as e:
            logger.error(
                f"get_all_rng_item_rank error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_rng_item_my_rank(score: int):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(MinigameUtil.get_rng_item_my_rank_list())
                param = {"score": score}
                result = s.execute(query, param)
                data = [dict(row) for row in result.mappings()]
            return data
        except Exception as e:
            logger.error(
                f"get_rng_item_my_rank: {score}, error: {e}",
                exc_info=True,
            )
            return None
