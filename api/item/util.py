class ItemUtil:
    @staticmethod
    def get_key_query():
        return """
                    select tkl_key.id,
                           tkl_key.name,
                           tkl_key.short_name,
                           tkl_key.uses,
                           tkl_key.use_map_en,
                           tkl_key.use_map_kr,
                           tkl_key.map_value,
                           tkl_key.image,
                           COALESCE(jsonb_agg(distinct
                                    jsonb_build_object('id', rq, 'name', tkl_quest.name_en, 'name_kr', tkl_quest.name_kr, 'in_raid',
                                                       tkl_related_quest.in_raid, 'count', tkl_related_quest."count"))
                                    FILTER (WHERE rq IS NOT NULL), '[]'::jsonb) as notes
                    from tkl_key
                             LEFT JOIN LATERAL unnest(tkl_key.related_quests) AS rq ON true
                             LEFT JOIN tkl_related_quest on rq = tkl_related_quest.quest_id and tkl_key.id = tkl_related_quest.item_id
                             LEFT JOIN tkl_quest on rq = tkl_quest.id
                    group by tkl_key.id, tkl_key.name, tkl_key.short_name, tkl_key.uses, tkl_key.use_map_en, tkl_key.use_map_kr,
                             tkl_key.map_value, tkl_key.image
                    """

    @staticmethod
    def get_provisions_query():
        return """
                select tkl_provisions.id,
                       tkl_provisions.name_en,
                       tkl_provisions.name_kr,
                       tkl_provisions.short_name,
                       tkl_provisions.category,
                       tkl_provisions.energy,
                       tkl_provisions.hydration,
                       tkl_provisions.stim_effects,
                       tkl_provisions.image,
                       COALESCE(jsonb_agg(distinct
                                jsonb_build_object('id', rq, 'name', tkl_quest.name_en, 'name_kr', tkl_quest.name_kr, 'in_raid',
                                                   tkl_related_quest.in_raid, 'count', tkl_related_quest."count"))
                                FILTER (WHERE rq IS NOT NULL), '[]'::jsonb) as notes
                from tkl_provisions
                         LEFT JOIN LATERAL unnest(tkl_provisions.related_quests) AS rq ON true
                         LEFT JOIN tkl_related_quest on rq = tkl_related_quest.quest_id and tkl_provisions.id = tkl_related_quest.item_id
                         LEFT JOIN tkl_quest on rq = tkl_quest.id
                group by tkl_provisions.id, tkl_provisions.name_en, tkl_provisions.name_kr, tkl_provisions.short_name,
                         tkl_provisions.category, tkl_provisions.energy, tkl_provisions.hydration, tkl_provisions.stim_effects,
                         tkl_provisions.image
                """

    @staticmethod
    def get_loot_query():
        return """
                        select tkl_loot.id,
                               tkl_loot.name_en,
                               tkl_loot.name_kr,
                               tkl_loot.short_name,
                               tkl_loot.category,
                               tkl_loot.image,
                               COALESCE(jsonb_agg(distinct
                                        jsonb_build_object('id', rq, 'name', tkl_quest.name_en, 'name_kr', tkl_quest.name_kr, 'in_raid',
                                                           tkl_related_quest.in_raid, 'count', tkl_related_quest."count"))
                                        FILTER (WHERE rq IS NOT NULL), '[]'::jsonb)  as quest_notes,
                               COALESCE(jsonb_agg(distinct
                                        jsonb_build_object('item_id', tkl_related_hideout.item_id, 'level_id', hid, 'master_id',
                                                           tkl_related_hideout.hideout_master_id, 'name',
                                                           tkl_related_hideout.hideout_master_name_en, 'name_kr',
                                                           tkl_related_hideout.hideout_master_name_kr, 'count', tkl_related_hideout."count"))
                                        FILTER (WHERE hid IS NOT NULL), '[]'::jsonb) as hideout_notes
                        from tkl_loot
                                 LEFT JOIN LATERAL unnest(tkl_loot.related_quests) AS rq ON true
                                 LEFT JOIN tkl_related_quest on rq = tkl_related_quest.quest_id and tkl_loot.id = tkl_related_quest.item_id
                                 LEFT JOIN tkl_quest on rq = tkl_quest.id
                                 LEFT JOIN LATERAL unnest(tkl_loot.related_hideout) AS hid on true
                                 LEFT JOIN tkl_related_hideout
                                           on hid = tkl_related_hideout.hideout_sub_id and tkl_loot.id = tkl_related_hideout.item_id
                        group by tkl_loot.id, tkl_loot.name_en, tkl_loot.name_kr, tkl_loot.short_name,
                                 tkl_loot.category, tkl_loot.image
                    """

    @staticmethod
    def get_glasses_query():
        return """
                    select tkl_glasses.id,
                           tkl_glasses.name,
                           tkl_glasses.short_name,
                           tkl_glasses.class_value,
                           tkl_glasses.durability,
                           tkl_glasses.blindness_protection,
                           tkl_glasses.image,
                           COALESCE(jsonb_agg(distinct
                                    jsonb_build_object('id', rq, 'name', tkl_quest.name_en, 'name_kr', tkl_quest.name_kr, 'in_raid',
                                                       tkl_related_quest.in_raid, 'count', tkl_related_quest."count"))
                                    FILTER (WHERE rq IS NOT NULL), '[]'::jsonb) as notes
                    from tkl_glasses
                             LEFT JOIN LATERAL unnest(tkl_glasses.related_quests) AS rq ON true
                             LEFT JOIN tkl_related_quest
                                       on rq = tkl_related_quest.quest_id and tkl_glasses.id = tkl_related_quest.item_id
                             LEFT JOIN tkl_quest on rq = tkl_quest.id
                    group by tkl_glasses.id, tkl_glasses.name, tkl_glasses.short_name,
                             tkl_glasses.class_value, tkl_glasses.durability, tkl_glasses.blindness_protection,
                             tkl_glasses.image
                    order by tkl_glasses.blindness_protection
                    """
