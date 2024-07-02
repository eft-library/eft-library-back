from sqlalchemy import text

from api.hideout.models import (
    HideoutMaster,
    HideoutLevel,
    HideoutCrafts,
    HideoutBonus,
    HideoutStationRequire,
    HideoutItemRequire,
    HideoutSkillRequire,
    HideoutTraderRequire,
)
from database import DataBaseConnector


class HideoutService:
    @staticmethod
    def get_all_hideout():
        """
        hideout 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(
                    """
                                    SELECT
                                        master_id,
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
                                    FROM (
                                        SELECT
                                            tkl_hideout_master.id as master_id,
                                            tkl_hideout_master.name_en as master_name_en,
                                            tkl_hideout_master.name_kr as master_name_kr,
                                            lid as level_id,
                                            tkl_hideout_master.image as image,
                                            json_agg(
                                                distinct jsonb_build_object(
                                                    'id', tkl_hideout_item_require.id,
                                                    'name_en', tkl_hideout_item_require.name_en,
                                                    'name_kr', tkl_hideout_item_require.name_kr,
                                                    'count', tkl_hideout_item_require.count,
                                                    'quantity', tkl_hideout_item_require.quantity
                                                )
                                            ) as item_require,
                                            json_agg(
                                                distinct jsonb_build_object(
                                                    'level', thl.level,
                                                    'construction_time', thl.construction_time
                                                )
                                            ) as level_info,
                                            json_agg(
                                                distinct jsonb_build_object(
                                                    'name_en', tkl_hideout_trader_require.name_en,
                                                    'name_kr', tkl_hideout_trader_require.name_kr,
                                                    'compare', tkl_hideout_trader_require.compare,
                                                    'require_type', tkl_hideout_trader_require.require_type,
                                                    'value', tkl_hideout_trader_require.value
                                                )
                                            ) as trader_require,
                                            json_agg(
                                                distinct jsonb_build_object(
                                                    'level', tkl_hideout_station_require.level,
                                                    'name_en', tkl_hideout_station_require.name_en,
                                                    'name_kr', tkl_hideout_station_require.name_kr
                                                )
                                            ) as station_require,
                                            json_agg(
                                                distinct jsonb_build_object(
                                                    'level', tkl_hideout_skill_require.level,
                                                    'name_en', tkl_hideout_skill_require.name_en,
                                                    'name_kr', tkl_hideout_skill_require.name_kr
                                                )
                                            ) as skill_require,
                                            json_agg(
                                                distinct jsonb_build_object(
                                                    'name_en', tkl_hideout_bonus.name_en,
                                                    'name_kr', tkl_hideout_bonus.name_kr,
                                                    'value', tkl_hideout_bonus.value,
                                                    'skill_name_en', tkl_hideout_bonus.skill_name_en,
                                                    'skill_name_kr', tkl_hideout_bonus.skill_name_kr
                                                )
                                            ) as bonus,
                                            json_agg(
                                                distinct jsonb_build_object(
                                                    'level', tkl_hideout_crafts.level,
                                                    'name_en', tkl_hideout_crafts.name_en,
                                                    'name_kr', tkl_hideout_crafts.name_kr
                                                )
                                            ) as crafts
                                        FROM
                                            tkl_hideout_master
                                        LEFT JOIN LATERAL
                                            unnest(tkl_hideout_master.level_ids) AS lid ON true
                                        LEFT JOIN
                                            tkl_hideout_item_require ON lid = tkl_hideout_item_require.level_id
                                        LEFT JOIN
                                            tkl_hideout_level thl on lid = thl.id
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
                                        GROUP BY tkl_hideout_master.id, tkl_hideout_master.name_en, tkl_hideout_master.image, lid
                                    ) as a
                                    GROUP BY master_id, master_name_en, master_name_kr, image
                                """
                )

                result = s.execute(query)
                hideouts = []
                for row in result:
                    hideout_dict = {
                        "master_id": row[0],
                        "master_name_en": row[1],
                        "master_name_kr": row[2],
                        "image": row[3],
                        "data": row[4],
                    }
                    hideouts.append(hideout_dict)

                return hideouts
        except Exception as e:
            print("오류 발생:", e)
            return None
