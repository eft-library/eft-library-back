from sqlalchemy import func, and_, or_, text, bindparam
from api.item.models import Item
from api.price.models import (
    ItemPriceHistory,
    ItemPrice,
    PriceSeason,
    PriceRankReq,
)
from database import Database
from collections import defaultdict
import logging

logger = logging.getLogger("api.price")


class PriceService:
    SEASON_GAME_MODE = "pvp-season"

    @staticmethod
    def _to_float(value):
        return float(value) if value is not None else None

    @staticmethod
    def _serialize_item_price(
        item: Item,
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
    def _serialize_price_row(price: ItemPrice):
        return {
            "game_mode": price.game_mode,
            "season_id": price.season_id,
            "highest_trader_price": PriceService._to_float(
                price.highest_trader_price
            ),
            "highest_trader_id": price.highest_trader_id,
            "flea_market_price": PriceService._to_float(price.flea_market_price),
            "trader_count": price.trader_count,
            "has_flea": price.has_flea,
            "update_time": price.update_time,
        }

    @staticmethod
    def _serialize_history_row(history: ItemPriceHistory):
        return {
            "game_mode": history.game_mode,
            "season_id": history.season_id,
            "price": history.price,
            "price_time": history.price_time,
        }

    @staticmethod
    def _serialize_trader_price_row(row):
        return {
            "id": row["id"],
            "game_mode": row["game_mode"],
            "season_id": row["season_id"],
            "trader_id": row["trader_id"],
            "price": PriceService._to_float(row["price"]),
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
    def _get_selected_season_id(s, season_id: str | None):
        if season_id:
            return season_id
        return (
            s.query(PriceSeason.id)
            .filter(PriceSeason.is_current.is_(True))
            .scalar()
        )

    @staticmethod
    def get_price_seasons():
        try:
            with Database.SessionLocal() as s:
                seasons = (
                    s.query(PriceSeason)
                    .order_by(PriceSeason.starts_at.desc().nullslast(), PriceSeason.id)
                    .all()
                )
                return [
                    {
                        "id": season.id,
                        "name": season.name,
                        "starts_at": season.starts_at,
                        "ends_at": season.ends_at,
                        "is_current": season.is_current,
                        "collected_at": season.collected_at,
                        "update_time": season.update_time,
                    }
                    for season in seasons
                ]
        except Exception as e:
            logger.error("get_price_seasons_v3 error: %s", e, exc_info=True)
            return None

    @staticmethod
    def get_item_price(
        page: int, page_size: int, word: str, season_id: str | None = None
    ):
        try:
            offset = (page - 1) * page_size
            search_word = f"%{word}%"

            with Database.SessionLocal() as s:
                selected_season_id = PriceService._get_selected_season_id(
                    s, season_id
                )
                season_scope = or_(
                    ItemPrice.game_mode != PriceService.SEASON_GAME_MODE,
                    and_(
                        ItemPrice.game_mode == PriceService.SEASON_GAME_MODE,
                        ItemPrice.season_id == selected_season_id,
                    ),
                )
                priced_item_ids = s.query(ItemPrice.item_id).distinct().subquery()
                word_filter = or_(
                    Item.name_ko.ilike(search_word),
                    Item.name_ja.ilike(search_word),
                    Item.name_en.ilike(search_word),
                )

                total_count = (
                    s.query(func.count(Item.id))
                    .filter(Item.id.in_(priced_item_ids), word_filter)
                    .scalar()
                )

                max_pages = (total_count // page_size) + (
                    1 if total_count % page_size > 0 else 0
                )

                item_list = (
                    s.query(Item)
                    .filter(Item.id.in_(priced_item_ids), word_filter)
                    .order_by(Item.name_en)
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )
                item_ids = [item.id for item in item_list]

                prices_by_item = defaultdict(dict)
                histories_by_item = defaultdict(
                    lambda: {"pvp": [], "pve": [], "pvp-season": []}
                )
                trader_prices_by_item = defaultdict(
                    lambda: {"pvp": [], "pve": [], "pvp-season": []}
                )

                if item_ids:
                    prices = (
                        s.query(ItemPrice)
                        .filter(ItemPrice.item_id.in_(item_ids), season_scope)
                        .all()
                    )
                    for price in prices:
                        prices_by_item[price.item_id][price.game_mode] = (
                            PriceService._serialize_price_row(price)
                        )

                    histories = (
                        s.query(ItemPriceHistory)
                        .filter(
                            ItemPriceHistory.item_id.in_(item_ids),
                            or_(
                                ItemPriceHistory.game_mode
                                != PriceService.SEASON_GAME_MODE,
                                and_(
                                    ItemPriceHistory.game_mode
                                    == PriceService.SEASON_GAME_MODE,
                                    ItemPriceHistory.season_id
                                    == selected_season_id,
                                ),
                            ),
                        )
                        .order_by(
                            ItemPriceHistory.item_id,
                            ItemPriceHistory.game_mode,
                            ItemPriceHistory.price_time,
                        )
                        .all()
                    )
                    for history in histories:
                        histories_by_item[history.item_id].setdefault(
                            history.game_mode, []
                        ).append(PriceService._serialize_history_row(history))

                    trader_prices = (
                        s.execute(
                            text(
                                """
                                select itp.id,
                                       itp.item_id,
                                       itp.game_mode,
                                       itp.season_id,
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
                                  and (itp.game_mode <> 'pvp-season'
                                       or itp.season_id = :season_id)
                                order by itp.item_id, itp.game_mode, itp.price desc;
                                """
                            ).bindparams(bindparam("item_ids", expanding=True)),
                            {
                                "item_ids": item_ids,
                                "season_id": selected_season_id,
                            },
                        )
                        .mappings()
                        .all()
                    )
                    for trader_price in trader_prices:
                        trader_prices_by_item[trader_price["item_id"]].setdefault(
                            trader_price["game_mode"], []
                        ).append(
                            PriceService._serialize_trader_price_row(trader_price)
                        )

                return {
                    "data": [
                        PriceService._serialize_item_price(
                            item,
                            {
                                "pvp": prices_by_item[item.id].get("pvp"),
                                "pve": prices_by_item[item.id].get("pve"),
                                "pvp-season": prices_by_item[item.id].get(
                                    "pvp-season"
                                ),
                            },
                            histories_by_item[item.id],
                            trader_prices_by_item[item.id],
                        )
                        for item in item_list
                    ],
                    "total_count": total_count,
                    "max_pages": max_pages,
                    "current_page": page,
                    "selected_season_id": selected_season_id,
                }

        except Exception as e:
            logger.error(
                f"get_item_price_v3 error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def _build_price_tiers(rows):
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
    def _get_price_top_rows(
        s, game_mode: str, categories: list[str], season_id: str | None = None
    ):
        query = (
            s.query(Item, ItemPrice)
            .join(ItemPrice, ItemPrice.item_id == Item.id)
            .filter(
                ItemPrice.game_mode == game_mode,
                ItemPrice.flea_market_price.isnot(None),
                Item.width.isnot(None),
                Item.height.isnot(None),
                Item.category.in_(categories),
                and_(Item.width > 0, Item.height > 0),
            )
        )
        if game_mode == PriceService.SEASON_GAME_MODE:
            query = query.filter(ItemPrice.season_id == season_id)
        query = query.all()

        rows = []
        for item, price in query:
            per_slot = PriceService._to_float(price.flea_market_price) / (
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
                    "flea_market_price": PriceService._to_float(
                        price.flea_market_price
                    ),
                    "highest_trader_price": PriceService._to_float(
                        price.highest_trader_price
                    ),
                    "highest_trader_id": price.highest_trader_id,
                    "per_slot": per_slot,
                }
            )

        return sorted(rows, key=lambda row: row["per_slot"], reverse=True)[:700]

    @staticmethod
    def get_price_top(price_rank_req: PriceRankReq):
        try:
            with Database.SessionLocal() as s:
                selected_season_id = PriceService._get_selected_season_id(
                    s, price_rank_req.seasonId
                )
                pvp_rows = PriceService._get_price_top_rows(
                    s, "pvp", price_rank_req.categoryList
                )
                pve_rows = PriceService._get_price_top_rows(
                    s, "pve", price_rank_req.categoryList
                )
                season_rows = PriceService._get_price_top_rows(
                    s,
                    PriceService.SEASON_GAME_MODE,
                    price_rank_req.categoryList,
                    selected_season_id,
                )

                return {
                    "pvp_top_list": PriceService._build_price_tiers(pvp_rows),
                    "pve_top_list": PriceService._build_price_tiers(pve_rows),
                    "pvp-season_top_list": PriceService._build_price_tiers(
                        season_rows
                    ),
                    "selected_season_id": selected_season_id,
                }

        except Exception as e:
            logger.error(
                f"get_price_top_v3: {price_rank_req.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None
