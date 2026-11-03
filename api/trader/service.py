from fastapi import HTTPException
from sqlalchemy import bindparam, text


class TraderService:
    @staticmethod
    def resolve_season(session, game_mode, season_id):
        if game_mode != "pvp-season":
            if season_id is not None:
                raise HTTPException(422, "season_id is only supported for pvp-season")
            return None
        if season_id is None:
            season_id = session.execute(text(
                "select id from price_seasons where is_current"
            )).scalar_one_or_none()
        if season_id is None or session.execute(text(
            "select id from price_seasons where id = :id"
        ), {"id": season_id}).scalar_one_or_none() is None:
            raise HTTPException(404, "Season not found")
        return season_id

    @staticmethod
    def get_traders(session, game_mode, season_id):
        rows = session.execute(text("""
            select t.id, t.name_en, t.name_ko, t.name_ja, t.normalized_name,
                   t.image, t.sort_order, r.next_restock_at,
                   r.collected_at as restock_collected_at
            from traders t
            left join trader_restock_state r on r.trader_id = t.id
                and r.game_mode = :game_mode and r.season_key = :season_key
            where t.is_use is true
            order by t.sort_order nulls last, t.id
        """), {"game_mode": game_mode, "season_key": season_id or ""}).mappings()
        return {"game_mode": game_mode, "season_id": season_id,
                "traders": [dict(row) for row in rows]}

    @staticmethod
    def require_trader(session, trader_id):
        if session.execute(text(
            "select id from traders where id = :id and is_use is true"
        ), {"id": trader_id}).scalar_one_or_none() is None:
            raise HTTPException(404, "Trader not found")

    @staticmethod
    def get_offers(session, game_mode, season_id, trader_id=None,
                   level=None, word="", offer_type=None, page=1, page_size=100,
                   offer_id=None):
        params = {"game_mode": game_mode, "season_key": season_id or ""}
        conditions = ["o.is_use is true", "t.is_use is true",
                      "o.game_mode = :game_mode", "o.season_key = :season_key"]
        if trader_id is not None:
            TraderService.require_trader(session, trader_id)
            conditions.append("o.trader_id = :trader_id")
            params["trader_id"] = trader_id
        if level is not None:
            conditions.append("o.trader_level <= :level")
            params["level"] = level
        if offer_type is not None:
            conditions.append("o.offer_type = :offer_type")
            params["offer_type"] = offer_type
        if offer_id is not None:
            conditions.append("o.id = :offer_id")
            params["offer_id"] = offer_id
        if word.strip():
            conditions.append("""exists (
                select 1 from trader_offer_rewards rw join items i on i.id = rw.item_id
                where rw.offer_id = o.id and (
                    strpos(lower(coalesce(i.name_en, '')), lower(:word)) > 0 or
                    strpos(lower(coalesce(i.name_ko, '')), lower(:word)) > 0 or
                    strpos(lower(coalesce(i.name_ja, '')), lower(:word)) > 0
                ))""")
            params["word"] = word.strip()
        where = " and ".join(conditions)
        source = " from trader_offers o join traders t on t.id = o.trader_id where " + where
        total = session.execute(text("select count(*)" + source), params).scalar_one()
        rows = session.execute(text("""
            select o.id, o.source_offer_id, o.trader_id, o.trader_level,
                   o.offer_type, o.game_mode, o.season_id, o.buy_limit,
                   o.raw_buy_limit, o.is_unlimited, o.sort_order,
                   o.collected_at, o.update_time,
                   t.name_en as trader_name_en, t.name_ko as trader_name_ko,
                   t.name_ja as trader_name_ja, t.image as trader_image,
                   t.normalized_name as trader_normalized_name
        """ + source + """
            order by o.sort_order nulls last, o.trader_level, o.id
            limit :limit offset :offset
        """), {**params, "limit": page_size, "offset": (page - 1) * page_size}).mappings().all()
        offers = {}
        for row in rows:
            offer = dict(row)
            offer["trader"] = {"id": offer["trader_id"]}
            for key in ("name_en", "name_ko", "name_ja", "image", "normalized_name"):
                offer["trader"][key] = offer.pop("trader_" + key)
            offer.update(costs=[], rewards=[], task_unlocks=[])
            offers[offer["id"]] = offer
        if offers:
            # Table names are fixed internal constants; values remain bound parameters.
            for kind, table in (("costs", "trader_offer_costs"), ("rewards", "trader_offer_rewards")):
                statement = text(f"""
                    select d.offer_id, d.quantity, i.id, i.name_en, i.name_ko,
                           i.name_ja, i.normalized_name, i.image, i.width, i.height
                    from {table} d join items i on i.id = d.item_id
                    where d.offer_id in :ids
                    order by d.sort_order nulls last, d.item_id
                """).bindparams(bindparam("ids", expanding=True))
                for row in session.execute(statement, {"ids": list(offers)}).mappings():
                    item = dict(row)
                    parent = item.pop("offer_id")
                    quantity = item.pop("quantity")
                    offers[parent][kind].append({"item": item, "quantity": quantity})
            statement = text("""
                select u.offer_id, u.quest_id, q.name_en, q.name_ko, q.name_ja,
                       q.normalized_name
                from trader_offer_task_unlocks u left join quests q on q.id = u.quest_id
                where u.offer_id in :ids order by u.quest_id
            """).bindparams(bindparam("ids", expanding=True))
            for row in session.execute(statement, {"ids": list(offers)}).mappings():
                quest = dict(row)
                parent = quest.pop("offer_id")
                offers[parent]["task_unlocks"].append(quest)
        return {"game_mode": game_mode, "season_id": season_id, "total": total,
                "page": page, "page_size": page_size, "offers": list(offers.values())}
