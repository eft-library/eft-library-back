from api.item.models import ItemV3
from api.minigame.res_models import UserMinigameScoreV3
from api.price.models import ItemPriceV3
from database import V3Database
from api.minigame.req_models import SaveScore
from sqlalchemy import text
from api.minigame.query import MinigameQueryV3
import logging

logger = logging.getLogger("api.minigame")


class MinigameServiceV3:
    @staticmethod
    def get_rng_item_list_v3():
        try:
            with V3Database.SessionLocal() as s:
                item_price_rows = (
                    s.query(ItemV3, ItemPriceV3)
                    .join(ItemPriceV3, ItemPriceV3.item_id == ItemV3.id)
                    .filter(
                        ItemPriceV3.game_mode == "pve",
                        ItemPriceV3.flea_market_price.isnot(None),
                        ItemV3.category != "Etc",
                    )
                    .order_by(ItemV3.category, ItemPriceV3.flea_market_price.desc())
                    .all()
                )

                return [
                    {
                        "id": item.id,
                        "normalized_name": item.normalized_name,
                        "name_en": item.name_en,
                        "name_ko": item.name_ko,
                        "name_ja": item.name_ja,
                        "image": item.image,
                        "category": item.category,
                        "width": item.width,
                        "height": item.height,
                        "flea_market_price": (
                            float(price.flea_market_price)
                            if price.flea_market_price is not None
                            else None
                        ),
                        "update_time": price.update_time,
                    }
                    for item, price in item_price_rows
                ]
        except Exception as e:
            logger.error(
                f"get_rng_item_list_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def insert_user_minigame_score_v3(result: SaveScore):
        try:
            with V3Database.SessionLocal() as s:
                new_score = UserMinigameScoreV3(
                    nickname=result.nickname,
                    game_type=result.game_type,
                    score=result.score,
                )
                s.add(new_score)
                s.commit()
                s.refresh(new_score)
                return new_score
        except Exception as e:
            logger.error(
                f"insert_user_minigame_score_v3: {result.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_all_rng_item_rank_v3():
        try:
            with V3Database.SessionLocal() as s:
                query = text(MinigameQueryV3.get_rng_item_rank_v3())
                result = s.execute(query)
                data = [dict(row) for row in result.mappings()]
            return data
        except Exception as e:
            logger.error(
                f"get_all_rng_item_rank_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_rng_item_my_rank_v3(score: int):
        try:
            with V3Database.SessionLocal() as s:
                query = text(MinigameQueryV3.get_rng_item_my_rank_list_v3())
                param = {"score": score}
                result = s.execute(query, param)
                data = [dict(row) for row in result.mappings()]
            return data
        except Exception as e:
            logger.error(
                f"get_rng_item_my_rank_v3: {score}, error: {e}",
                exc_info=True,
            )
            return None
