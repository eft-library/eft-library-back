class PriceUtil:

    @staticmethod
    def get_pve_price_top():
        """
        pve 상위 시세 10개
        """
        return """
                    WITH pve_prices AS (
                        SELECT
                            id,
                            item_name_kr,
                            item_name_en,
                            item_image,
                            width,
                            height,
                            trader->'pve_trader' AS trader_list,
                            jsonb_array_elements(trader->'pve_trader') AS trade_info
                        FROM tkl_item_price
                        WHERE jsonb_typeof(trader->'pve_trader') = 'array'
                    )
                    SELECT
                        id,
                        item_name_kr,
                        item_name_en,
                        item_image,
                        width,
                        height,
                        MAX((trade_info->>'price')::INT) AS flea_market_price,
                        CEIL(MAX((trade_info->>'price')::INT)  / NULLIF(width * height, 0)) as per_slot,
                        trader_list
                    FROM pve_prices
                    WHERE trade_info->'trader'->>'npc_id' = 'FLEA_MARKET'
                    GROUP BY id, item_name_kr, item_name_en, item_image, trader_list, width, height
                    ORDER BY CEIL(MAX((trade_info->>'price')::INT)  / NULLIF(width * height, 0)) DESC
                    LIMIT 280
                """

    @staticmethod
    def get_pvp_price_top():
        """
        pvp 상위 시세 10개
        """
        return """
                    WITH pvp_prices AS (
                        SELECT
                            id,
                            item_name_kr,
                            item_name_en,
                            item_image,
                            width,
                            height,
                            trader->'pvp_trader' AS trader_list,
                            jsonb_array_elements(trader->'pvp_trader') AS trade_info
                        FROM tkl_item_price
                        WHERE jsonb_typeof(trader->'pvp_trader') = 'array'
                    )
                    SELECT
                        id,
                        item_name_kr,
                        item_name_en,
                        item_image,
                        width,
                        height,
                        MAX((trade_info->>'price')::INT) AS flea_market_price,
                        CEIL(MAX((trade_info->>'price')::INT)  / NULLIF(width * height, 0)) as per_slot,
                        trader_list
                    FROM pvp_prices
                    WHERE trade_info->'trader'->>'npc_id' = 'FLEA_MARKET'
                    GROUP BY id, item_name_kr, item_name_en, item_image, trader_list, width, height
                    ORDER BY CEIL(MAX((trade_info->>'price')::INT)  / NULLIF(width * height, 0)) DESC
                    LIMIT 280
                """