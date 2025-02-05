from sqlalchemy import func, desc, text, or_
from api.price.models import Price
from database import DataBaseConnector


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
                    s.query(Price)
                    .filter(
                        or_(
                            Price.item_name_en.ilike(f"%{word}%"),
                            Price.item_name_kr.ilike(f"%{word}%")
                        )
                    )
                    .limit(page_size)
                    .offset(offset)
                    .all()
                )

                return {
                    "data": price_list,
                    "total_count": total_count,
                    "max_pages": max_pages,
                    "current_page": page,
                }

        except Exception as e:
            print("오류 발생:", e)
            return None
