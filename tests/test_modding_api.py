"""Read-only modding API contracts on isolated PostgreSQL using authoritative DDL."""
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from api.modding.router import get_session, router
from database import Database


@unittest.skipUnless(importlib.util.find_spec('pgserver'), 'Install pgserver for isolated PostgreSQL tests')
class ModdingApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pgserver
        directory = tempfile.TemporaryDirectory(prefix='modding-api-')
        cls.addClassCleanup(directory.cleanup)
        server = pgserver.get_server(Path(directory.name)/'postgres',cleanup_mode='delete')
        cls.addClassCleanup(server.cleanup)
        cls.engine = create_engine(server.get_uri())
        cls.addClassCleanup(cls.engine.dispose)
        source = (Path(__file__).parents[1]/'platform_db.sql').read_text()
        with cls.engine.begin() as conn:
            for name in ('items','weapon_items','weapon_allowed_ammo'):
                conn.exec_driver_sql(re.search(rf'create table if not exists {name}\s*\(.*?\n\);',source,re.S).group())
        raw = cls.engine.raw_connection()
        try:
            with raw.cursor() as cur:
                cur.execute((Path(__file__).parents[1]/'sql/migrations/20261110_weapon_modding.sql').read_text())
                cur.execute((Path(__file__).parents[1]/'sql/migrations/20261113_rewards_and_modding_stats.sql').read_text())
                cur.execute("""
                    insert into items(id,name_en,name_ko,normalized_name,weight) values
                        ('gun','Rifle','소총','rifle',2.5),('ammo','Ammo','탄약','ammo',0.01),
                        ('receiver','Upper receiver','리시버','receiver',0.27),('sight','Sight','가늠자','sight',0.01),
                        ('scope','Scope','조준경','scope',0.4),('blocked','Blocked','제외','blocked',0.1),
                        ('blocked-cat','Blocked category','분류 제외','blocked-cat',0.1),
                        ('other','Other','기타','other',0.1),('preset','Preset','프리셋','preset',3.2),
                        ('other-preset','Other preset','다른 프리셋','other-preset',3.1);
                    insert into weapon_items(item_id,ergonomics) values ('gun',48),('ammo',99);
                    insert into weapon_allowed_ammo values ('gun','ammo');
                    insert into item_categories(id,normalized_name) values ('weapons','weapon'),('optics','optics'),('excluded','excluded');
                    insert into item_category_memberships values
                        ('gun','weapons',0),('scope','optics',0),('blocked-cat','optics',0),('blocked-cat','excluded',1);
                    insert into item_slots(item_id,slot_id,name_id,required,sort_order) values
                        ('gun','receiver-slot','mod_reciever',true,0),
                        ('receiver','rear-slot','mod_sight_rear',false,0),
                        ('receiver','shared-slot','mod_tactical',false,1),
                        ('other','shared-slot','mod_tactical',false,0);
                    insert into item_slot_item_filters values
                        ('gun','receiver-slot','allowed','receiver',0),
                        ('receiver','rear-slot','allowed','sight',0),
                        ('receiver','rear-slot','allowed','sight',1),
                        ('receiver','rear-slot','allowed','blocked',2),
                        ('receiver','rear-slot','excluded','blocked',0);
                    insert into item_slot_category_filters values
                        ('receiver','rear-slot','allowed','optics',0),
                        ('receiver','rear-slot','excluded','excluded',0);
                    insert into item_conflicting_items values ('scope','sight',0),('scope','sight',1);
                    insert into item_conflicting_categories values ('scope','excluded',0);
                    insert into item_conflicting_slots values ('scope','missing-slot',0),('scope','shared-slot',1);
                    insert into item_mod_properties(item_id,properties_type,ergonomics,recoil_modifier,item_recoil_modifier,zoom_levels)
                        values ('scope','ItemPropertiesScope',-3.5,-0.01,-1,'[[1,4],[2.5]]');
                    insert into item_presets(preset_item_id,base_item_id,is_default,ergonomics,moa) values
                        ('preset','gun',false,47.5,1.96),('other-preset','gun',true,null,null);
                    insert into weapon_preset_links values ('gun','preset',false,true,null),('gun','other-preset',true,false,0);
                    insert into item_preset_components values
                        ('preset',0,'gun',1,'{}'),
                        ('preset',1,'sight',1,'{"nested":{"value":[1,2]}}'),
                        ('preset',2,'sight',2,'{}');
                """)
            raw.commit()
        finally:
            raw.close()
        cls.sessions = sessionmaker(cls.engine)

    def setUp(self):
        patcher = patch.object(Database,'SessionLocal',self.sessions)
        patcher.start()
        self.addCleanup(patcher.stop)
        app = FastAPI()
        app.include_router(router,prefix='/api/modding')
        self.app = app
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def get_data(self,path,**params):
        response=self.client.get('/api/modding/v3/'+path,params=params)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['msg'],'OK')
        return response.json()['data']

    def test_weapon_list_excludes_ammo_and_supports_search_and_empty_pages(self):
        data=self.get_data('weapons')
        self.assertEqual(data['total'],1)
        self.assertEqual(data['weapons'][0]['item']['id'],'gun')
        self.assertEqual(data['weapons'][0]['preset_count'],2)
        for word in ('소총','RIFLE','gun'):
            self.assertEqual(self.get_data('weapons',word=word)['total'],1)
        self.assertEqual(self.get_data('weapons',word="' OR 1=1 --")['total'],0)
        self.assertEqual(self.get_data('weapons',page=2)['weapons'],[])

    def test_default_preset_summary_uses_reference_and_stays_lightweight(self):
        # Fixture deliberately has properties.default=false but the weapon reference=true.
        summary=self.get_data('weapons')['weapons'][0]['default_preset']
        self.assertEqual(summary,{'id':'preset','name_en':'Preset','name_ko':'프리셋','name_ja':None,'image':None})
        self.assertEqual(set(summary),{'id','name_en','name_ko','name_ja','image'})
        with self.engine.begin() as conn:
            conn.exec_driver_sql("update weapon_preset_links set is_default_reference=false,is_listed=true,sort_order=1 where weapon_item_id='gun' and preset_item_id='preset'")
        try:
            self.assertIsNone(self.get_data('weapons')['weapons'][0]['default_preset'])
            self.assertEqual(self.get_data('weapons')['weapons'][0]['preset_count'],2)
        finally:
            with self.engine.begin() as conn:
                conn.exec_driver_sql("update weapon_preset_links set is_default_reference=true,is_listed=false,sort_order=null where weapon_item_id='gun' and preset_item_id='preset'")

    def test_item_slots_preserve_duplicates_order_and_multi_level_loading(self):
        gun=self.get_data('items/gun')
        self.assertEqual(gun['weapon_properties']['ergonomics'],48)
        self.assertEqual(gun['allowed_ammo'][0]['id'],'ammo')
        receiver=gun['slots'][0]['filters']['allowed_items'][0]['item']
        self.assertEqual(receiver['id'],'receiver')
        self.assertEqual(receiver['slot_count'],2)
        part=self.get_data('items/'+receiver['id'])
        allowed=part['slots'][0]['filters']['allowed_items']
        self.assertEqual([r['item']['id'] for r in allowed],['sight','sight','blocked'])
        self.assertEqual([r['sort_order'] for r in allowed],[0,1,2])
        self.assertFalse(part['slots'][0]['required'])
        ammo=self.get_data('items/ammo')
        self.assertIsNone(ammo['weapon_properties'])
        self.assertEqual(ammo['slots'],[])

    def test_candidates_apply_category_and_explicit_exclusions_and_deduplicate(self):
        path='items/receiver/slots/rear-slot/candidates'
        data=self.get_data(path)
        self.assertEqual(data['validation_scope'],'slot_filters_only')
        self.assertEqual(data['total'],2)
        self.assertEqual({r['item']['id'] for r in data['candidates']},{'sight','scope'})
        self.assertEqual(self.get_data(path,word='조준경')['total'],1)
        page=self.get_data(path,page_size=1,page=2)
        self.assertEqual(page['total'],2)
        self.assertEqual(len(page['candidates']),1)
        self.assertEqual(self.get_data('items/receiver/slots/shared-slot/candidates')['total'],0)
        self.assertEqual(self.get_data('items/other/slots/shared-slot/candidates')['total'],0)

    def test_conflicts_remain_directional_and_unresolved_slots_are_preserved(self):
        data=self.get_data('items/scope')
        self.assertEqual([x['item']['id'] for x in data['conflicts']['items']],['sight','sight'])
        self.assertEqual(data['conflicts']['slots'][0],{'sort_order':0,'slot_id':'missing-slot','definitions':[]})
        self.assertEqual(len(data['conflicts']['slots'][1]['definitions']),2)
        self.assertEqual(data['conflicts']['categories'][0]['category']['id'],'excluded')
        self.assertEqual(self.get_data('items/sight')['conflicts']['items'],[])
        stats=data['item']['mod_properties']
        self.assertEqual(stats['zoom_levels'],[[1,4],[2.5]])
        self.assertEqual(stats['recoil_modifier'],-0.01)
        self.assertEqual(stats['item_recoil_modifier'],-1)
        self.assertIsNone(stats['accuracy_modifier'])

    def test_presets_keep_source_flags_and_components_without_invented_slots(self):
        listed=self.get_data('weapons/gun/presets',page_size=1)
        self.assertEqual(listed['total'],2)
        default=listed['presets'][0]
        self.assertFalse(default['is_default'])
        self.assertTrue(default['link']['is_default_reference'])
        self.assertFalse(default['link']['is_listed'])
        self.assertIsNone(default['link']['sort_order'])
        detail=self.get_data('presets/preset')
        self.assertEqual(detail['composition_type'],'flat_source_list')
        self.assertEqual([x['item']['id'] for x in detail['components']],['gun','sight','sight'])
        self.assertEqual(detail['components'][1]['attributes'],{'nested':{'value':[1,2]}})
        self.assertEqual(detail['components'][2]['quantity'],2)
        self.assertNotIn('slot_id',detail['components'][1])
        self.assertEqual(detail['weapon_links'][0]['weapon_item_id'],'gun')
        self.assertEqual(self.get_data('presets/other-preset')['components'],[])

    def test_inferred_tree_is_separate_from_source_components_and_importable(self):
        with self.engine.begin() as conn:
            conn.exec_driver_sql("""
                insert into items(id) values ('tree-preset');
                insert into item_presets(preset_item_id,base_item_id) values ('tree-preset','gun');
                insert into item_preset_components values
                    ('tree-preset',0,'gun',1,'{}'),('tree-preset',1,'receiver',1,'{}'),
                    ('tree-preset',2,'sight',1,'{"mode":{"value":[1,4]}}');
            """)
        try:
            detail=self.get_data('presets/tree-preset')
            self.assertEqual(detail['composition_type'],'flat_source_list')
            self.assertNotIn('parent_node_id',detail['components'][1])
            result=detail['reconstruction']
            self.assertEqual(result['method'],'inferred')
            self.assertFalse(result['is_source_tree'])
            self.assertEqual(result['status'],'unique')
            self.assertTrue(result['can_import'])
            nodes=result['candidate_trees'][0]['nodes']
            self.assertEqual(len(nodes),3)
            by_item={n['item_id']:n for n in nodes}
            self.assertEqual(by_item['sight']['parent_node_id'],by_item['receiver']['node_id'])
            self.assertEqual(by_item['sight']['attributes'],{'mode':{'value':[1,4]}})
            from api.weapon_builds.schemas import CreateBuild
            from uuid import uuid4
            CreateBuild.model_validate({'request_id':str(uuid4()),'weapon_item_id':'gun','title':'Import','nodes':nodes})
        finally:
            with self.engine.begin() as conn:
                conn.exec_driver_sql("delete from item_presets where preset_item_id='tree-preset'")
                conn.exec_driver_sql("delete from items where id='tree-preset'")

    def test_not_found_and_validation(self):
        for path,code in [('items/missing','MODDING_ITEM_NOT_FOUND'),
                          ('items/gun/slots/rear-slot/candidates','MODDING_SLOT_NOT_FOUND'),
                          ('weapons/ammo/presets','MODDING_WEAPON_NOT_FOUND'),
                          ('presets/missing','MODDING_PRESET_NOT_FOUND')]:
            response=self.client.get('/api/modding/v3/'+path)
            self.assertEqual(response.status_code,404)
            self.assertEqual(response.json()['detail'],code)
        for params in ({'page':0},{'page_size':101},{'page_size':0},{'word':'x'*201},{'page':1_000_001}):
            self.assertEqual(self.client.get('/api/modding/v3/weapons',params=params).status_code,422)

    def test_database_outage_is_503(self):
        with patch.object(Database,'SessionLocal',side_effect=OperationalError('offline',None,Exception())), \
             self.assertLogs('api.modding.router',level='ERROR'):
            response=self.client.get('/api/modding/v3/weapons')
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json(),{'detail':'MODDING_LOOKUP_UNAVAILABLE'})

    def test_reads_use_one_repeatable_read_readonly_transaction(self):
        session_generator=get_session()
        session=next(session_generator)
        try:
            self.assertEqual(session.connection().exec_driver_sql('show transaction_isolation').scalar_one(),'repeatable read')
            self.assertEqual(session.connection().exec_driver_sql('show transaction_read_only').scalar_one(),'on')
        finally:
            session_generator.close()

    def test_openapi_has_typed_responses(self):
        schema=self.app.openapi()
        self.assertEqual(len(schema['paths']),6)
        self.assertIn('SlotFilters',schema['components']['schemas'])
        self.assertIn('PresetComponent',schema['components']['schemas'])
