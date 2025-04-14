class ItemUtil:

    @staticmethod
    def get_rig_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'Rig'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_head_wear_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'Headwear'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_glasses_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'Glasses'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'blindness_protection')::NUMERIC
        """

    @staticmethod
    def get_face_cover_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'FaceCover'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_item_detail_query():
        return """
            WITH target_item AS (SELECT *
                                 FROM tkl_item
                                 WHERE url_mapping = :url_mapping),
            
            -- 📦 바터 정보
                 filtered_barters AS (SELECT n.id                      AS npc_id,
                                             n.name_kr,
                                             jsonb_build_object(
                                                     'level', barter ->> 'level',
                                                     'rewardItems', reward,
                                                     'requiredItems', barter -> 'requiredItems'
                                             )                         AS matching_barter,
                                             reward -> 'item' ->> 'id' AS reward_item_id
                                      FROM tkl_npc n,
                                           jsonb_array_elements(n.barter_info) AS barter,
                                           jsonb_array_elements(barter -> 'rewardItems') AS reward),
            
            -- 🛠 은신처 제작에 사용되는 정보
                 filtered_crafts AS (SELECT thc.*,
                                            elem -> 'item' ->> 'id' AS required_item_id
                                     FROM tkl_hideout_crafts thc,
                                          jsonb_array_elements(thc.req_item) AS elem),
            
            -- 🎯 퀘스트 보상으로 사용되는 정보
                 filtered_quests AS (SELECT qa.id                                           AS quest_id,
                                            qa.name_en,
                                            qa.name_kr,
                                            qa.url_mapping,
                                            jsonb_array_elements(finish_rewards -> 'items') AS reward_elem
                                     FROM tkl_api_quest qa),
            
            -- ❗ questItem에 포함된 경우 (예: giveQuestItem, findQuestItem)
                 required_quests_by_quest_item AS (SELECT q.id AS quest_id,
                                                          q.name_kr,
                                                          q.name_en,
                                                          q.url_mapping,
                                                          obj  AS objective
                                                   FROM tkl_api_quest q,
                                                        jsonb_array_elements(q.objectives) AS obj
                                                   WHERE obj ->> 'type' IN ('findQuestItem', 'giveQuestItem')),
            
            -- ❗ items 배열에 포함된 경우 (예: giveItem, plantItem, findItem)
                 required_quests_by_items_array AS (SELECT q.id AS quest_id,
                                                           q.name_kr,
                                                           q.name_en,
                                                           q.url_mapping,
                                                           obj  AS objective
                                                    FROM tkl_api_quest q,
                                                         jsonb_array_elements(q.objectives) AS obj
                                                    WHERE obj ->> 'type' IN ('plantItem', 'giveItem', 'findItem')
                                                      AND EXISTS (SELECT 1
                                                                  FROM jsonb_array_elements(obj -> 'items') AS item
                                                                  WHERE item ->> 'id' = (SELECT id FROM target_item))),
            
                 item_with_details AS (SELECT ti.id,
                                              ti.name_en,
                                              ti.name_kr,
                                              ti.category,
                                              ti.image,
                                              ti.image_width,
                                              ti.image_height,
                                              ti.info,
                                              ti.update_time,
                                              ti.url_mapping,
            
                                              -- 은신처 아이템 요구 정보
                                              COALESCE(
                                                              json_agg(
                                                              DISTINCT jsonb_build_object(
                                                                      'id', thir.id,
                                                                      'level_id', thir.level_id,
                                                                      'name_en', thir.name_en,
                                                                      'name_kr', thir.name_kr,
                                                                      'quantity', thir.quantity,
                                                                      'count', thir.count,
                                                                      'image', thir.image,
                                                                      'item_id', thir.item_id
                                                                       )
                                                                      ) FILTER (WHERE thir.id IS NOT NULL),
                                                              '[]'
                                              ) AS hideout_items,
            
                                              -- 은신처 제작에 사용
                                              COALESCE(
                                                              json_agg(
                                                              DISTINCT jsonb_build_object(
                                                                      'id', thc.id,
                                                                      'name_en', thc.name_en,
                                                                      'name_kr', thc.name_kr,
                                                                      'level_id', thc.level_id,
                                                                      'level', thc.level,
                                                                      'duration', thc.duration,
                                                                      'reward_item_id', thc.reward_item_id,
                                                                      'image', thc.image,
                                                                      'quantity', thc.quantity
                                                                       )
                                                                      ) FILTER (WHERE thc.id IS NOT NULL),
                                                              '[]'
                                              ) AS used_in_crafts,
            
                                              -- NPC 바터 보상으로 나오는 정보
                                              COALESCE(
                                                              json_agg(
                                                              DISTINCT jsonb_build_object(
                                                                      'npc_id', fb.npc_id,
                                                                      'npc_name_kr', fb.name_kr,
                                                                      'barter_info', fb.matching_barter
                                                                       )
                                                                      ) FILTER (WHERE fb.npc_id IS NOT NULL),
                                                              '[]'
                                              ) AS rewarded_by_npcs,
            
                                              -- 퀘스트 보상으로 나오는 정보
                                              COALESCE(
                                                              json_agg(
                                                              DISTINCT jsonb_build_object(
                                                                      'quest_id', fq.quest_id,
                                                                      'name_en', fq.name_en,
                                                                      'name_kr', fq.name_kr,
                                                                      'url_mapping', fq.url_mapping,
                                                                      'reward', fq.reward_elem
                                                                       )
                                                                      ) FILTER (WHERE fq.quest_id IS NOT NULL),
                                                              '[]'
                                              ) AS rewarded_by_quests,
            
                                              -- 📌 questItem에 들어 있는 퀘스트
                                              COALESCE(
                                                              json_agg(
                                                              DISTINCT jsonb_build_object(
                                                                      'quest_id', rqi.quest_id,
                                                                      'name_kr', rqi.name_kr,
                                                                      'name_en', rqi.name_en,
                                                                      'url_mapping', rqi.url_mapping,
                                                                      'objective', rqi.objective
                                                                       )
                                                                      ) FILTER (
                                                                  WHERE rqi.objective -> 'questItem' ->> 'id' = ti.id
                                                                  ),
                                                              '[]'
                                              ) AS required_by_quest_item,
            
                                              -- 📌 items 배열에 들어 있는 퀘스트
                                              COALESCE(
                                                              json_agg(
                                                              DISTINCT jsonb_build_object(
                                                                      'quest_id', rqa.quest_id,
                                                                      'name_kr', rqa.name_kr,
                                                                      'name_en', rqa.name_en,
                                                                      'url_mapping', rqa.url_mapping,
                                                                      'objective', rqa.objective
                                                                       )
                                                                      ) FILTER (WHERE rqa.quest_id IS NOT NULL),
                                                              '[]'
                                              ) AS required_by_quest_item_array
            
                                       FROM target_item ti
                                                LEFT JOIN tkl_hideout_item_require thir ON ti.id = thir.item_id
                                                LEFT JOIN filtered_crafts thc ON thc.required_item_id = ti.id
                                                LEFT JOIN filtered_barters fb ON fb.reward_item_id = ti.id
                                                LEFT JOIN filtered_quests fq ON fq.reward_elem -> 'item' ->> 'id' = ti.id
                                                LEFT JOIN required_quests_by_quest_item rqi
                                                          ON rqi.objective -> 'questItem' ->> 'id' = ti.id
                                                LEFT JOIN required_quests_by_items_array rqa ON TRUE
                                       GROUP BY ti.id, ti.name_en, ti.name_kr, ti.category, ti.image,
                                                ti.image_width, ti.image_height, ti.info, ti.update_time, ti.url_mapping)
            
            SELECT *
            FROM item_with_details
        """