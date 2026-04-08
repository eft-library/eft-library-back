from sqlalchemy import func, text, or_, String
from api.price.models import PriceModel, PriceRankReq
from api.price.util import PriceUtil
from database import DataBaseConnector
from sqlalchemy.orm import subqueryload
from collections import defaultdict
from datetime import timedelta
import logging

logger = logging.getLogger("api.price")


class PriceService:

    @staticmethod
    def get_item_price(page: int, page_size: int, word: str):
        try:

            with DataBaseConnector.SessionLocal() as s:
                offset = (page - 1) * page_size

                total_param = {"word": f"%{word}%"}

                max_count_query = text(
                    """
                        select count(*)
                        from item_price_i18n
                        where item_price_i18n.name ->> 'ko' ilike :word
                           or item_price_i18n.name ->> 'ko' ilike :word
                           or item_price_i18n.name ->> 'ja' ilike :word
                    """
                )

                total_count = s.execute(max_count_query, total_param).scalar()

                max_pages = (total_count // page_size) + (
                    1 if total_count % page_size > 0 else 0
                )

                price_list = (
                    s.query(PriceModel)
                    .filter(
                        or_(
                            func.cast(PriceModel.name["ko"], String).ilike(f"%{word}%"),
                            func.cast(PriceModel.name["ja"], String).ilike(f"%{word}%"),
                            func.cast(PriceModel.name["en"], String).ilike(f"%{word}%"),
                        )
                    )
                    .options(subqueryload(PriceModel.history))
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )

                for price in price_list:
                    if price.update_time is not None:
                        price.update_time = price.update_time + timedelta(hours=9)

                    # price_type별로 pvp, pve로 나누기
                    categorized_history = defaultdict(list)

                    for history in price.history:
                        if history.price_time is not None:
                            history.price_time = history.price_time + timedelta(hours=9)
                        if history.execute_time is not None:
                            history.execute_time = history.execute_time + timedelta(
                                hours=9
                            )

                        categorized_history[history.price_type].append(history)

                    # 결과를 PriceModel에 추가
                    price.history_by_type = {
                        "pvp": categorized_history.get("PVP", []),
                        "pve": categorized_history.get("PVE", []),
                    }

                    price.history = []

                return {
                    "data": price_list,
                    "total_count": total_count,
                    "max_pages": max_pages,
                    "current_page": page,
                }

        except Exception as e:
            logger.error(
                f"get_item_price error: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    def get_price_top(priceRankReq: PriceRankReq):
        try:

            with DataBaseConnector.SessionLocal() as s:
                tiers = ["S", "A", "B", "C", "D", "E", "F"]
                tier_size = 100
                pvp_tier_dict = {
                    tier: {"min": float("inf"), "max": 0, "list": []} for tier in tiers
                }
                pve_tier_dict = {
                    tier: {"min": float("inf"), "max": 0, "list": []} for tier in tiers
                }

                pve_top_query = text(PriceUtil.get_pve_price_top())
                pvp_top_query = text(PriceUtil.get_pvp_price_top())

                pve_top_list = s.execute(
                    pve_top_query, {"categories": tuple(priceRankReq.categoryList)}
                )
                pve_result = [dict(row) for row in pve_top_list.mappings()]

                pvp_top_list = s.execute(
                    pvp_top_query, {"categories": tuple(priceRankReq.categoryList)}
                )
                pvp_result = [dict(row) for row in pvp_top_list.mappings()]

                for i, item in enumerate(pvp_result):
                    tier_index = i // tier_size
                    if tier_index < len(tiers):
                        tier_name = tiers[tier_index]
                        per_slot = item["per_slot"]

                        # 티어의 최소, 최대 금액 업데이트
                        if per_slot < pvp_tier_dict[tier_name]["min"]:
                            pvp_tier_dict[tier_name]["min"] = per_slot
                        if per_slot > pvp_tier_dict[tier_name]["max"]:
                            pvp_tier_dict[tier_name]["max"] = per_slot

                        # 티어 리스트에 항목 추가
                        pvp_tier_dict[tier_name]["list"].append(item)

                for i, item in enumerate(pve_result):
                    tier_index = i // tier_size
                    if tier_index < len(tiers):
                        tier_name = tiers[tier_index]
                        per_slot = item["per_slot"]

                        # 티어의 최소, 최대 금액 업데이트
                        if per_slot < pve_tier_dict[tier_name]["min"]:
                            pve_tier_dict[tier_name]["min"] = per_slot
                        if per_slot > pve_tier_dict[tier_name]["max"]:
                            pve_tier_dict[tier_name]["max"] = per_slot

                        # 티어 리스트에 항목 추가
                        pve_tier_dict[tier_name]["list"].append(item)

                for tier in tiers:
                    if not pvp_tier_dict[tier]["list"]:
                        pvp_tier_dict[tier]["min"] = 0
                        pvp_tier_dict[tier]["max"] = 0
                    if not pve_tier_dict[tier]["list"]:
                        pve_tier_dict[tier]["min"] = 0
                        pve_tier_dict[tier]["max"] = 0

                # 리스트 형태로 변환
                pvp_tier_list = [
                    {
                        "tier": tier,
                        "min": pvp_tier_dict[tier]["min"],
                        "max": pvp_tier_dict[tier]["max"],
                        "list": pvp_tier_dict[tier]["list"],
                    }
                    for tier in tiers
                ]

                pve_tier_list = [
                    {
                        "tier": tier,
                        "min": pve_tier_dict[tier]["min"],
                        "max": pve_tier_dict[tier]["max"],
                        "list": pve_tier_dict[tier]["list"],
                    }
                    for tier in tiers
                ]

                return {"pvp_top_list": pvp_tier_list, "pve_top_list": pve_tier_list}

        except Exception as e:
            logger.error(
                f"get_price_top: {priceRankReq.model_dump()}, error: {e}",
                exc_info=True,
            )
            return None
