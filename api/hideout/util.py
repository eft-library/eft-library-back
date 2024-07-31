class HideoutUtil:
    @staticmethod
    def get_hideout_query():
        """
        하이드 아웃 전체 조회 쿼리
        """

        return """
                    SELECT master_id,
                           master_name_en,
                           master_name_kr,
                           image,
                           json_agg(
                                   jsonb_build_object(
                                           'level_id', level_id,
                                           'item_require', item_require,
                                           'level_info', level_info,
                                           'trader_require', trader_require,
                                           'station_require', station_require,
                                           'skill_require', skill_require,
                                           'bonus', bonus,
                                           'crafts', crafts
                                   )
                           ) as data
                    FROM (SELECT tkl_hideout_master.id as master_id,
                                 tkl_hideout_master.name_en as master_name_en,
                                 tkl_hideout_master.name_kr as master_name_kr,
                                 lid as level_id,
                                 tkl_hideout_master.image as image,
                                 COALESCE(
                                                 json_agg(
                                                 distinct jsonb_build_object(
                                                         'id', tkl_hideout_item_require.id,
                                                         'name_en', tkl_hideout_item_require.name_en,
                                                         'name_kr', tkl_hideout_item_require.name_kr,
                                                         'count', tkl_hideout_item_require.count,
                                                         'quantity', tkl_hideout_item_require.quantity,
                                                         'image', tkl_hideout_item_require.image
                                                          )
                                                         )
                                                 FILTER (WHERE tkl_hideout_item_require.id IS NOT NULL),
                                                 '[]'::json) as item_require,
                                 COALESCE(
                                                 json_agg(
                                                 distinct jsonb_build_object(
                                                         'level', tkl_hideout_level.level,
                                                         'construction_time', tkl_hideout_level.construction_time
                                                          )
                                                         ) FILTER (WHERE tkl_hideout_level.level IS NOT NULL),
                                                 '[]'::json) as level_info,
                                 COALESCE(
                                                 json_agg(
                                                 distinct jsonb_build_object(
                                                         'name_en', tkl_hideout_trader_require.name_en,
                                                         'name_kr', tkl_hideout_trader_require.name_kr,
                                                         'compare', tkl_hideout_trader_require.compare,
                                                         'require_type', tkl_hideout_trader_require.require_type,
                                                         'value', tkl_hideout_trader_require.value,
                                                         'image', tkl_hideout_trader_require.image
                                                          )
                                                         ) FILTER (WHERE tkl_hideout_trader_require.name_en IS NOT NULL),
                                                 '[]'::json) as trader_require,
                                 COALESCE(
                                                 json_agg(
                                                 distinct jsonb_build_object(
                                                         'level', tkl_hideout_station_require.level,
                                                         'name_en', tkl_hideout_station_require.name_en,
                                                         'name_kr', tkl_hideout_station_require.name_kr,
                                                         'image', tkl_hideout_station_require.image
                                                          )
                                                         ) FILTER (WHERE tkl_hideout_station_require.level IS NOT NULL),
                                                 '[]'::json) as station_require,
                                 COALESCE(
                                                 json_agg(
                                                 distinct jsonb_build_object(
                                                         'level', tkl_hideout_skill_require.level,
                                                         'name_en', tkl_hideout_skill_require.name_en,
                                                         'name_kr', tkl_hideout_skill_require.name_kr,
                                                         'image', tkl_hideout_skill_require.image
                                                          )
                                                         ) FILTER (WHERE tkl_hideout_skill_require.level IS NOT NULL),
                                                 '[]'::json) as skill_require,
                                 COALESCE(
                                                 json_agg(
                                                 distinct jsonb_build_object(
                                                         'name_en', tkl_hideout_bonus.name_en,
                                                         'name_kr', tkl_hideout_bonus.name_kr,
                                                         'value', tkl_hideout_bonus.value,
                                                         'skill_name_en', tkl_hideout_bonus.skill_name_en,
                                                         'skill_name_kr', tkl_hideout_bonus.skill_name_kr
                                                          )
                                                         ) FILTER (WHERE tkl_hideout_bonus.name_en IS NOT NULL),
                                                 '[]'::json) as bonus,
                                 COALESCE(
                                                 json_agg(
                                                 distinct jsonb_build_object(
                                                         'level', tkl_hideout_crafts.level,
                                                         'name_en', tkl_hideout_crafts.name_en,
                                                         'name_kr', tkl_hideout_crafts.name_kr
                                                          )
                                                         ) FILTER (WHERE tkl_hideout_crafts.level IS NOT NULL),
                                                 '[]'::json) as crafts
                          FROM tkl_hideout_master
                                   LEFT JOIN LATERAL
                              unnest(tkl_hideout_master.level_ids) AS lid ON true
                                   LEFT JOIN
                               tkl_hideout_item_require ON lid = tkl_hideout_item_require.level_id
                                   LEFT JOIN
                               tkl_hideout_level on lid = tkl_hideout_level.id
                                   LEFT JOIN
                               tkl_hideout_trader_require on lid = tkl_hideout_trader_require.level_id
                                   LEFT JOIN
                               tkl_hideout_station_require on lid = tkl_hideout_station_require.level_id
                                   LEFT JOIN
                               tkl_hideout_skill_require on lid = tkl_hideout_skill_require.level_id
                                   LEFT JOIN
                               tkl_hideout_bonus on lid = tkl_hideout_bonus.level_id
                                   LEFT JOIN
                               tkl_hideout_crafts on lid = tkl_hideout_crafts.level_id
                          GROUP BY tkl_hideout_master.id, tkl_hideout_master.name_en, tkl_hideout_master.image, lid) as a
                    GROUP BY master_id, master_name_en, master_name_kr, image
                    """
