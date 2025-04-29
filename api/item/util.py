class ItemUtil:

    @staticmethod
    def get_rig_query():
        return """
            SELECT *
            FROM item_i18n
            where category = 'Rig'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_head_wear_query():
        return """
            SELECT *
            FROM item_i18n
            where category = 'Headwear'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_armor_vest_query():
        return """
            SELECT *
            FROM item_i18n
            where category = 'ArmorVest'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_glasses_query():
        return """
            SELECT *
            FROM item_i18n
            where category = 'Glasses'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'blindness_protection')::NUMERIC
        """

    @staticmethod
    def get_face_cover_query():
        return """
            SELECT *
            FROM item_i18n
            where category = 'FaceCover'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_item_detail_query():
        return """
            WITH target_item AS (SELECT *
                                 FROM item_i18n
                                 WHERE url_mapping = :url_mapping),
            
                 -- 📦 바터 정보
                 filtered_barters AS (SELECT n.id                      AS npc_id,
                                             n.name,
                                             n.image,
                                             jsonb_build_object(
                                                     'level', barter ->> 'level',
                                                     'rewardItems', reward,
                                                     'requiredItems', barter -> 'requiredItems'
                                             )                         AS matching_barter,
                                             reward -> 'item' ->> 'id' AS reward_item_id
                                      FROM npc_i18n n,
                                           jsonb_array_elements(n.barter_info) AS barter,
                                           jsonb_array_elements(barter -> 'rewardItems') AS reward),
            
                 -- 🛠 은신처 건설에 사용되는 정보
                 filtered_hideout AS (SELECT thir.id,
                                             thir.level_id,
                                             thir.name,
                                             thir.quantity,
                                             thir.count,
                                             thir.image,
                                             thir.item_id,
                                             thm.name as master_name,
                                             thm.id   as master_id
                                      FROM hideout_item_require_i18n thir
                                               LEFT JOIN hideout_master_i18n thm
                                                         ON SPLIT_PART(thir.level_id, '-', 1) = thm.id),
            
                 -- 🛠 은신처 제작에 사용되는 정보
                 filtered_crafts AS (SELECT DISTINCT ON (thc.id) thc.*,
                                                                 thm.name                as master_name,
                                                                 thm.id                  as master_id,
                                                                 elem -> 'item' ->> 'id' AS required_item_id
                                     FROM hideout_crafts_i18n thc
                                              LEFT JOIN LATERAL jsonb_array_elements(thc.req_item) AS elem on True
                                              LEFT JOIN hideout_master_i18n thm ON SPLIT_PART(thc.level_id, '-', 1) = thm.id),
            
                 -- 🎯 퀘스트 보상으로 사용되는 정보
                 filtered_quests AS (SELECT distinct on (qa.id) qa.id                                           AS quest_id,
                                                                qa.name,
                                                                qa.npc_id,
                                                                qa.url_mapping,
                                                                tn.name                                         as npc_name,
                                                                tn.image                                        AS npc_image,
                                                                jsonb_array_elements(finish_rewards -> 'items') AS reward_elem
                                     FROM quest_i18n qa
                                              left join npc_i18n tn on qa.npc_id = tn.id
                                     WHERE qa.name is not null),
            
                 -- ❗ questItem에 포함된 경우 (예: giveQuestItem, findQuestItem)
                 required_quests_by_quest_item AS (SELECT DISTINCT ON (q.id) q.id     AS quest_id,
                                                                             q.name,
                                                                             q.url_mapping,
                                                                             tn.name  AS npc_name,
                                                                             tn.image AS npc_image,
                                                                             obj      AS objective
                                                   FROM quest_i18n q
                                                            LEFT JOIN LATERAL jsonb_array_elements(q.objectives) AS obj ON TRUE
                                                            LEFT JOIN npc_i18n tn ON q.npc_id = tn.id
                                                   WHERE obj ->> 'type' IN ('findQuestItem', 'giveQuestItem')
                                                     AND q.name IS NOT NULL),
            
                 -- ❗ items 배열에 포함된 경우 (예: giveItem, plantItem, findItem)
                 required_quests_by_items_array AS (SELECT distinct on (q.id) q.id     AS quest_id,
                                                                              q.name,
                                                                              q.url_mapping,
                                                                              tn.name  as npc_name,
                                                                              tn.image AS npc_image,
                                                                              obj      AS objective
                                                    FROM quest_i18n q
                                                             LEFT JOIN LATERAL jsonb_array_elements(q.objectives) AS obj ON TRUE
                                                             LEFT JOIN npc_i18n tn on q.npc_id = tn.id
                                                    WHERE obj ->> 'type' IN ('plantItem', 'giveItem', 'findItem')
                                                      AND q.name is not null
                                                      AND EXISTS (SELECT 1
                                                                  FROM jsonb_array_elements(obj -> 'items') AS item
                                                                  WHERE item ->> 'id' = (SELECT id FROM target_item))),
            
                 item_with_details AS (SELECT ti.id,
                                              ti.name,
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
                                                                      'name', thir.name,
                                                                      'quantity', thir.quantity,
                                                                      'count', thir.count,
                                                                      'image', thir.image,
                                                                      'item_id', thir.item_id,
                                                                      'master_name', thir.master_name,
                                                                      'master_id', thir.master_id
                                                                       )
                                                                      ) FILTER (WHERE thir.id IS NOT NULL),
                                                              '[]'
                                              ) AS hideout_items,
            
                                              -- 은신처 제작에 사용
                                              COALESCE(
                                                              json_agg(
                                                              DISTINCT jsonb_build_object(
                                                                      'id', thc.id,
                                                                      'name', thc.name,
                                                                      'level_id', thc.level_id,
                                                                      'level', thc.level,
                                                                      'duration', thc.duration,
                                                                      'req_item', thc.req_item,
                                                                      'reward_item_id', thc.reward_item_id,
                                                                      'image', thc.image,
                                                                      'quantity', thc.quantity,
                                                                      'master_name', thc.master_name,
                                                                      'master_id', thc.master_id
                                                                       )
                                                                      ) FILTER (WHERE thc.id IS NOT NULL),
                                                              '[]'
                                              ) AS used_in_crafts,
            
                                              -- NPC 바터 보상으로 나오는 정보
                                              COALESCE(
                                                              json_agg(
                                                              DISTINCT jsonb_build_object(
                                                                      'npc_id', fb.npc_id,
                                                                      'npc_image', fb.image,
                                                                      'npc_name', fb.name,
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
                                                                      'name', fq.name,
                                                                      'npc_name', fq.npc_name,
                                                                      'npc_image', fq.npc_image,
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
                                                                      'name', rqi.name,
                                                                      'npc_name', rqi.npc_name,
                                                                      'npc_image', rqi.npc_image,
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
                                                                      'name', rqa.name,
                                                                      'npc_name', rqa.npc_name,
                                                                      'npc_image', rqa.npc_image,
                                                                      'url_mapping', rqa.url_mapping,
                                                                      'objective', rqa.objective
                                                                       )
                                                                      ) FILTER (WHERE rqa.quest_id IS NOT NULL),
                                                              '[]'
                                              ) AS required_by_quest_item_array
            
                                       FROM target_item ti
                                                LEFT JOIN filtered_hideout thir ON ti.id = thir.item_id
                                                LEFT JOIN filtered_crafts thc ON thc.required_item_id = ti.id
                                                LEFT JOIN filtered_barters fb ON fb.reward_item_id = ti.id
                                                LEFT JOIN filtered_quests fq ON fq.reward_elem -> 'item' ->> 'id' = ti.id
                                                LEFT JOIN required_quests_by_quest_item rqi
                                                          ON rqi.objective -> 'questItem' ->> 'id' = ti.id
                                                LEFT JOIN required_quests_by_items_array rqa ON TRUE
                                       GROUP BY ti.id, ti.name, ti.name, ti.category, ti.image,
                                                ti.image_width, ti.image_height, ti.info, ti.update_time, ti.url_mapping)
            
            SELECT *
            FROM item_with_details
        """
