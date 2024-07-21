from api.item.models import (
    Headset,
    Headwear,
    ArmorVest,
    Rig,
    Backpack,
    Container,
    Key,
    Provisions,
    Medical,
    Ammo,
    Loot,
    FaceCover,
)
from database import DataBaseConnector
from sqlalchemy import desc, text


class ItemService:
    @staticmethod
    def get_all_headset():
        """
        headset 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                headset = s.query(Headset).order_by(Headset.name).all()
                return headset
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_headwear():
        """
        headwear 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                headwear = s.query(Headwear).order_by(Headwear.class_value).all()

            class_headwear = []

            no_class_headwear = []

            for wear in headwear:
                if wear.class_value is None:
                    no_class_headwear.append(wear)
                else:
                    class_headwear.append(wear)

            result_headwear = {
                "class_headwear": [item.__dict__ for item in class_headwear],
                "no_class_headwear": [item.__dict__ for item in no_class_headwear],
            }

            return result_headwear
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_armor_vest():
        """
        armor vest 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                armor_vest = s.query(ArmorVest).order_by(ArmorVest.class_value).all()
                return armor_vest
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_backpack():
        """
        backpack 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                backpack = s.query(Backpack).order_by(Backpack.capacity).all()
                return backpack
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_container():
        """
        container 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                container = s.query(Container).order_by(Container.capacity).all()
                return container
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_key():
        """
        key 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(
                    """
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
                )
                result = s.execute(query)
                key = []
                for row in result:
                    key_dict = {
                        "id": row[0],
                        "name": row[1],
                        "short_name": row[2],
                        "uses": row[3],
                        "use_map_en": row[4],
                        "use_map_kr": row[5],
                        "map_value": row[6],
                        "image": row[7],
                        "related_quests": row[8],
                    }
                    key.append(key_dict)
                return key
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_rig():
        """
        rig 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                rig = s.query(Rig).order_by(Rig.class_value, Rig.capacity).all()

            class_rig = []
            no_class_rig = []

            for item in rig:
                if item.class_value is None:
                    no_class_rig.append(item)
                else:
                    class_rig.append(item)

            result_rig = {
                "class_rig": [item.__dict__ for item in class_rig],
                "no_class_rig": [item.__dict__ for item in no_class_rig],
            }

            return result_rig
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_provisions():
        """
        provisions 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(
                    """
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
                )
                result = s.execute(query)
                provisions = []
                for row in result:
                    provision_dict = {
                        "id": row[0],
                        "name_en": row[1],
                        "name_kr": row[2],
                        "short_name": row[3],
                        "category": row[4],
                        "energy": row[5],
                        "hydration": row[6],
                        "stim_effects": row[7],
                        "image": row[8],
                        "related_quests": row[9],
                    }
                    provisions.append(provision_dict)
                return provisions
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_medical():
        """
        medical 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                medical = s.query(Medical).order_by(Medical.category).all()
                return medical
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_ammo():
        """
        ammo 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                ammo = s.query(Ammo).order_by(Ammo.armor_damage).all()
                return ammo
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_loot():
        """
        loot 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                query = text(
                    """
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
                                    jsonb_build_object('id', hid, 'master_id', tkl_related_hideout.hideout_master_id, 'name',
                                                       tkl_related_hideout.hideout_master_name_en, 'name_kr',
                                                       tkl_related_hideout.hideout_master_name_kr, 'count', tkl_related_hideout."count"))
                                    FILTER (WHERE hid IS NOT NULL), '[]'::jsonb) as hideout_notes
                    from tkl_loot
                             LEFT JOIN LATERAL unnest(tkl_loot.related_quests) AS rq ON true
                             LEFT JOIN tkl_related_quest on rq = tkl_related_quest.quest_id and tkl_loot.id = tkl_related_quest.item_id
                             LEFT JOIN tkl_quest on rq = tkl_quest.id
                             LEFT JOIN LATERAL unnest(tkl_loot.related_hideout) AS hid on true
                             LEFT JOIN tkl_related_hideout on hid = tkl_related_hideout.hideout_sub_id
                    group by tkl_loot.id, tkl_loot.name_en, tkl_loot.name_kr, tkl_loot.short_name,
                             tkl_loot.category, tkl_loot.image
                    """
                )
                result = s.execute(query)
                loot = []
                for row in result:
                    loot_dict = {
                        "id": row[0],
                        "name_en": row[1],
                        "name_kr": row[2],
                        "short_name": row[3],
                        "category": row[4],
                        "image": row[5],
                        "related_quests": row[6],
                        "related_hideout": row[7]
                    }
                    loot.append(loot_dict)
                return loot
        except Exception as e:
            print("오류 발생:", e)
            return None

    @staticmethod
    def get_all_face_cover():
        """
        face cover 전체 조회
        """
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                face_cover = s.query(FaceCover).order_by(FaceCover.class_value).all()

            class_face_cover = []

            no_class_face_cover = []

            for cover in face_cover:
                if cover.class_value is None:
                    no_class_face_cover.append(cover)
                else:
                    class_face_cover.append(cover)

            result_face_cover = {
                "class_face_cover": [item.__dict__ for item in class_face_cover],
                "no_class_face_cover": [item.__dict__ for item in no_class_face_cover],
            }

            return result_face_cover
        except Exception as e:
            print("오류 발생:", e)
            return None
