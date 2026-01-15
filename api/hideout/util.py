class HideoutUtil:
    @staticmethod
    def get_hideout_query():
        """
        하이드 아웃 전체 조회 쿼리
        """

        return """
            SELECT master_id,
                   master_name,
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
            FROM (SELECT hideout_master_i18n.id      as master_id,
                         hideout_master_i18n.name    as master_name,
                         lid                         as level_id,
                         COALESCE(
                                         json_agg(
                                         distinct jsonb_build_object(
                                                 'id', hideout_item_require_i18n.id,
                                                 'level_id', hideout_item_require_i18n.level_id,
                                                 'name', hideout_item_require_i18n.name,
                                                 'count', hideout_item_require_i18n.count,
                                                 'quantity', hideout_item_require_i18n.quantity,
                                                 'found_in_raid', hideout_item_require_i18n.found_in_raid,
                                                 'image', hideout_item_require_i18n.image
                                                  )
                                                 )
                                         FILTER (WHERE hideout_item_require_i18n.id IS NOT NULL),
                                         '[]'::json) as item_require,
                         COALESCE(
                                         json_agg(
                                         distinct jsonb_build_object(
                                                 'level', hideout_level_i18n.level,
                                                 'construction_time', hideout_level_i18n.construction_time
                                                  )
                                                 ) FILTER (WHERE hideout_level_i18n.level IS NOT NULL),
                                         '[]'::json) as level_info,
                         COALESCE(
                                         json_agg(
                                         distinct jsonb_build_object(
                                                 'name', hideout_trader_require_i18n.name,
                                                 'level_id', hideout_trader_require_i18n.level_id,
                                                 'value', hideout_trader_require_i18n.value,
                                                 'image', hideout_trader_require_i18n.image
                                                  )
                                                 ) FILTER (WHERE hideout_trader_require_i18n.name IS NOT NULL),
                                         '[]'::json) as trader_require,
                         COALESCE(
                                         json_agg(
                                         distinct jsonb_build_object(
                                                 'level', hideout_station_require_i18n.level,
                                                 'level_id', hideout_station_require_i18n.level_id,
                                                 'name', hideout_station_require_i18n.name,
                                                 'station_master_id', hideout_station_require_i18n.station_master_id
                                                  )
                                                 ) FILTER (WHERE hideout_station_require_i18n.level IS NOT NULL),
                                         '[]'::json) as station_require,
                         COALESCE(
                                         json_agg(
                                         distinct jsonb_build_object(
                                                 'level', hideout_skill_require_i18n.level,
                                                 'level_id', hideout_skill_require_i18n.level_id,
                                                 'name', hideout_skill_require_i18n.name,
                                                 'image', hideout_skill_require_i18n.image
                                                  )
                                                 ) FILTER (WHERE hideout_skill_require_i18n.level IS NOT NULL),
                                         '[]'::json) as skill_require,
                         COALESCE(
                                         json_agg(
                                         distinct jsonb_build_object(
                                                 'name', hideout_bonus_i18n.name,
                                                 'value', hideout_bonus_i18n.value,
                                                 'skill_name', hideout_bonus_i18n.skill_name
                                                  )
                                                 ) FILTER (WHERE hideout_bonus_i18n.name IS NOT NULL),
                                         '[]'::json) as bonus,
                         COALESCE(
                                         json_agg(
                                         distinct jsonb_build_object(
                                                 'level', hideout_crafts_i18n.level,
                                                 'width', hideout_crafts_i18n.width,
                                                 'height', hideout_crafts_i18n.height,
                                                 'name', hideout_crafts_i18n.name,
                                                 'req_item', hideout_crafts_i18n.req_item,
                                                 'duration', hideout_crafts_i18n.duration,
                                                 'quantity', hideout_crafts_i18n.quantity,
                                                 'image', hideout_crafts_i18n.image
                                                  )
                                                 ) FILTER (WHERE hideout_crafts_i18n.level IS NOT NULL),
                                         '[]'::json) as crafts
                  FROM hideout_master_i18n
                           LEFT JOIN LATERAL
                      unnest(hideout_master_i18n.level_ids) AS lid ON true
                           LEFT JOIN
                       hideout_item_require_i18n ON lid = hideout_item_require_i18n.level_id
                           LEFT JOIN
                       hideout_level_i18n on lid = hideout_level_i18n.id
                           LEFT JOIN
                       hideout_trader_require_i18n on lid = hideout_trader_require_i18n.level_id
                           LEFT JOIN
                       hideout_station_require_i18n on lid = hideout_station_require_i18n.level_id
                           LEFT JOIN
                       hideout_skill_require_i18n on lid = hideout_skill_require_i18n.level_id
                           LEFT JOIN
                       hideout_bonus_i18n on lid = hideout_bonus_i18n.level_id
                           LEFT JOIN
                       hideout_crafts_i18n on lid = hideout_crafts_i18n.level_id
                  GROUP BY hideout_master_i18n.id, hideout_master_i18n.name, lid) as a
            GROUP BY master_id, master_name
                    """

    @staticmethod
    def get_item_require_info():
        return """
            SELECT
                hiri.item_id,
                hiri.name,
                SUM(
                    CASE
                        WHEN uh.complete_list IS NOT NULL
                             AND hiri.level_id::text = ANY (uh.complete_list)
                        THEN 0
                        ELSE hiri.quantity
                    END
                ) AS quantity,
                hiri.image,
                hiri.found_in_raid
            FROM hideout_item_require_i18n hiri
            LEFT JOIN user_hideout uh ON uh.user_email = :user_email
            WHERE hiri.item_id not in ('5449016a4bdc2d6f028b456f', '569668774bdc2da2298b4568', '5696686a4bdc2da3298b456a')
            GROUP BY hiri.item_id, hiri.name, hiri.image, hiri.found_in_raid;
        """
