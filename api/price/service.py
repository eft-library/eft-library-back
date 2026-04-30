from sqlalchemy import func, and_, or_, text, bindparam
from api.item.models import ItemV3
from api.price.models import (
    ItemPriceHistoryV3,
    ItemPriceV3,
    PriceRankReqV3,
)
from database import V3Database
from collections import defaultdict
import logging

logger = logging.getLogger("api.price")


class PriceServiceV3:
    @staticmethod
    def _to_float_v3(value):
        return float(value) if value is not None else None

    @staticmethod
    def _serialize_item_price_v3(
        item: ItemV3,
        prices_by_mode,
        histories_by_mode,
        trader_prices_by_mode,
    ):
        return {
            "id": item.id,
            "normalized_name": item.normalized_name,
            "name_en": item.name_en,
            "name_ko": item.name_ko,
            "name_ja": item.name_ja,
            "image": item.image,
            "category": item.category,
            "parent_category": item.parent_category,
            "width": item.width,
            "height": item.height,
            "prices": prices_by_mode,
            "history_by_type": histories_by_mode,
            "trader_prices": trader_prices_by_mode,
        }

    @staticmethod
    def _serialize_price_row_v3(price: ItemPriceV3):
        return {
            "game_mode": price.game_mode,
            "highest_trader_price": PriceServiceV3._to_float_v3(
                price.highest_trader_price
            ),
            "highest_trader_id": price.highest_trader_id,
            "flea_market_price": PriceServiceV3._to_float_v3(price.flea_market_price),
            "trader_count": price.trader_count,
            "has_flea": price.has_flea,
            "update_time": price.update_time,
        }

    @staticmethod
    def _serialize_history_row_v3(history: ItemPriceHistoryV3):
        return {
            "game_mode": history.game_mode,
            "price": history.price,
            "price_time": history.price_time,
        }

    @staticmethod
    def _serialize_trader_price_row_v3(row):
        return {
            "id": row["id"],
            "game_mode": row["game_mode"],
            "trader_id": row["trader_id"],
            "price": PriceServiceV3._to_float_v3(row["price"]),
            "trader": (
                {
                    "id": row["trader_id"],
                    "normalized_name": row["trader_normalized_name"],
                    "name_en": row["trader_name_en"],
                    "name_ko": row["trader_name_ko"],
                    "name_ja": row["trader_name_ja"],
                    "image": row["trader_image"],
                }
                if row["trader_normalized_name"] is not None
                else None
            ),
        }

    @staticmethod
    def get_item_price_v3(page: int, page_size: int, word: str):
        try:
            offset = (page - 1) * page_size
            search_word = f"%{word}%"

            with V3Database.SessionLocal() as s:
                priced_item_ids = s.query(ItemPriceV3.item_id).distinct().subquery()
                word_filter = or_(
                    ItemV3.name_ko.ilike(search_word),
                    ItemV3.name_ja.ilike(search_word),
                    ItemV3.name_en.ilike(search_word),
                )

                total_count = (
                    s.query(func.count(ItemV3.id))
                    .filter(ItemV3.id.in_(priced_item_ids), word_filter)
                    .scalar()
                )

                max_pages = (total_count // page_size) + (
                    1 if total_count % page_size > 0 else 0
                )

                item_list = (
                    s.query(ItemV3)
                    .filter(ItemV3.id.in_(priced_item_ids), word_filter)
                    .order_by(ItemV3.name_en)
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )
                item_ids = [item.id for item in item_list]

                prices_by_item = defaultdict(dict)
                histories_by_item = defaultdict(lambda: {"pvp": [], "pve": []})
                trader_prices_by_item = defaultdict(lambda: {"pvp": [], "pve": []})

                if item_ids:
                    prices = (
                        s.query(ItemPriceV3)
                        .filter(ItemPriceV3.item_id.in_(item_ids))
                        .all()
                    )
                    for price in prices:
                        prices_by_item[price.item_id][price.game_mode] = (
                            PriceServiceV3._serialize_price_row_v3(price)
                        )

                    histories = (
                        s.query(ItemPriceHistoryV3)
                        .filter(ItemPriceHistoryV3.item_id.in_(item_ids))
                        .order_by(
                            ItemPriceHistoryV3.item_id,
                            ItemPriceHistoryV3.game_mode,
                            ItemPriceHistoryV3.price_time,
                        )
                        .all()
                    )
                    for history in histories:
                        histories_by_item[history.item_id].setdefault(
                            history.game_mode, []
                        ).append(PriceServiceV3._serialize_history_row_v3(history))

                    trader_prices = (
                        s.execute(
                            text(
                                """
                                select itp.id,
                                       itp.item_id,
                                       itp.game_mode,
                                       itp.trader_id,
                                       itp.price,
                                       t.normalized_name as trader_normalized_name,
                                       t.name_en as trader_name_en,
                                       t.name_ko as trader_name_ko,
                                       t.name_ja as trader_name_ja,
                                       t.image as trader_image
                                from item_trader_prices itp
                                         left join traders t on itp.trader_id = t.id
                                where itp.item_id in :item_ids
                                order by itp.item_id, itp.game_mode, itp.price desc;
                                """
                            ).bindparams(bindparam("item_ids", expanding=True)),
                            {"item_ids": item_ids},
                        )
                        .mappings()
                        .all()
                    )
                    for trader_price in trader_prices:
                        trader_prices_by_item[trader_price["item_id"]].setdefault(
                            trader_price["game_mode"], []
                        ).append(
                            PriceServiceV3._serialize_trader_price_row_v3(trader_price)
                        )

                return {
                    "data": [
                        PriceServiceV3._serialize_item_price_v3(
                            item,
                            {
                                "pvp": prices_by_item[item.id].get("pvp"),
                                "pve": prices_by_item[item.id].get("pve"),
                            },
                            histories_by_item[item.id],
                            trader_prices_by_item[item.id],
                        )
                        for item in item_list
                    ],
                    "total_count": total_count,
                    "max_pages": max_pages,
                    "current_page": page,
                }

        except Exception as e:
            logger.error(
                f"get_item_price_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def _build_price_tiers_v3(rows):
        tiers = ["S", "A", "B", "C", "D", "E", "F"]
        tier_size = 100
        tier_dict = {
            tier: {"min": float("inf"), "max": 0, "list": []} for tier in tiers
        }

        for index, row in enumerate(rows):
            tier_index = index // tier_size
            if tier_index >= len(tiers):
                continue

            tier_name = tiers[tier_index]
            per_slot = row["per_slot"]

            if per_slot < tier_dict[tier_name]["min"]:
                tier_dict[tier_name]["min"] = per_slot
            if per_slot > tier_dict[tier_name]["max"]:
                tier_dict[tier_name]["max"] = per_slot

            tier_dict[tier_name]["list"].append(row)

        return [
            {
                "tier": tier,
                "min": 0 if not tier_dict[tier]["list"] else tier_dict[tier]["min"],
                "max": 0 if not tier_dict[tier]["list"] else tier_dict[tier]["max"],
                "list": tier_dict[tier]["list"],
            }
            for tier in tiers
        ]

    @staticmethod
    def _get_price_top_rows_v3(s, game_mode: str, categories: list[str]):
        query = (
            s.query(ItemV3, ItemPriceV3)
            .join(ItemPriceV3, ItemPriceV3.item_id == ItemV3.id)
            .filter(
                ItemPriceV3.game_mode == game_mode,
                ItemPriceV3.flea_market_price.isnot(None),
                ItemV3.width.isnot(None),
                ItemV3.height.isnot(None),
                ItemV3.category.in_(categories),
                and_(ItemV3.width > 0, ItemV3.height > 0),
            )
            .all()
        )

        rows = []
        for item, price in query:
            per_slot = PriceServiceV3._to_float_v3(price.flea_market_price) / (
                item.width * item.height
            )
            rows.append(
                {
                    "id": item.id,
                    "normalized_name": item.normalized_name,
                    "name_en": item.name_en,
                    "name_ko": item.name_ko,
                    "name_ja": item.name_ja,
                    "image": item.image,
                    "width": item.width,
                    "height": item.height,
                    "category": item.category,
                    "flea_market_price": PriceServiceV3._to_float_v3(
                        price.flea_market_price
                    ),
                    "highest_trader_price": PriceServiceV3._to_float_v3(
                        price.highest_trader_price
                    ),
                    "highest_trader_id": price.highest_trader_id,
                    "per_slot": per_slot,
                }
            )

        return sorted(rows, key=lambda row: row["per_slot"], reverse=True)[:700]

    @staticmethod
    def get_price_top_v3(price_rank_req_v3: PriceRankReqV3):
        try:
            with V3Database.SessionLocal() as s:
                pvp_rows = PriceServiceV3._get_price_top_rows_v3(
                    s, "pvp", price_rank_req_v3.categoryList
                )
                pve_rows = PriceServiceV3._get_price_top_rows_v3(
                    s, "pve", price_rank_req_v3.categoryList
                )

                return {
                    "pvp_top_list": PriceServiceV3._build_price_tiers_v3(pvp_rows),
                    "pve_top_list": PriceServiceV3._build_price_tiers_v3(pve_rows),
                }

        except Exception as e:
            logger.error(
                f"get_price_top_v3: {price_rank_req_v3.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None
