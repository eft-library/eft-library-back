from sqlalchemy import func, desc, text, or_
from api.price.models import PriceModel
from api.price.util import PriceUtil
from database import DataBaseConnector
from sqlalchemy.orm import subqueryload
from collections import defaultdict


class PriceService:

    @staticmethod
    def get_item_price(page: int, page_size: int, word: str):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                offset = (page - 1) * page_size

                total_param = {"word": f"%{word}%"}

                max_count_query = text(
                    """
                    select count(*) from tkl_item_price
                    where item_name_en ilike :word or item_name_kr ilike :word
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
                            PriceModel.item_name_en.ilike(f"%{word}%"),
                            PriceModel.item_name_kr.ilike(f"%{word}%")
                        )
                    )
                    .options(subqueryload(PriceModel.history))
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )

                for price in price_list:
                    # price_type별로 pvp, pve로 나누기
                    categorized_history = defaultdict(list)

                    for history in price.history:
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
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_price_top():
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:

                pve_top_query = text(PriceUtil.get_pve_price_top())
                pvp_top_query = text(PriceUtil.get_pvp_price_top())

                pve_top_list = s.execute(pve_top_query)
                pve_result = [dict(row) for row in pve_top_list.mappings()]

                pvp_top_list = s.execute(pvp_top_query)
                pvp_result = [dict(row) for row in pvp_top_list.mappings()]

                return {
                    'pvp_top_list': pvp_result,
                    'pve_top_list': pve_result
                }

        except Exception as e:
            print("오류 발생:", e)
            return None
