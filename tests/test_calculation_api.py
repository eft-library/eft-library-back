"""API contracts against additive DDL on isolated PostgreSQL; never operational DB."""
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.modding.router import router, get_session
from api.kord_breach.router import router as rewards_router
from api.modding.calculation import _calculate

ROOT = Path(__file__).parents[1]


@unittest.skipUnless(importlib.util.find_spec('pgserver'), 'pgserver required')
class CalculationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pgserver
        directory = tempfile.TemporaryDirectory(prefix='stats-api-')
        cls.addClassCleanup(directory.cleanup)
        server = pgserver.get_server(Path(directory.name)/'db', cleanup_mode='delete')
        cls.addClassCleanup(server.cleanup)
        cls.engine = create_engine(server.get_uri())
        cls.addClassCleanup(cls.engine.dispose)
        source = (ROOT/'platform_db.sql').read_text()
        with cls.engine.begin() as conn:
            for name in ('items','quests','weapon_items','weapon_allowed_ammo','ammo_items'):
                conn.exec_driver_sql(re.search(rf'create table if not exists {name}\s*\(.*?\n\);',source,re.S).group())
        raw = cls.engine.raw_connection()
        try:
            with raw.cursor() as cur:
                cur.execute((ROOT/'sql/migrations/20261110_weapon_modding.sql').read_text())
                for _ in range(2):
                    cur.execute((ROOT/'sql/migrations/20261113_rewards_and_modding_stats.sql').read_text())
            raw.commit()
        finally:
            raw.close()

    def setUp(self):
        self.conn = self.engine.connect()
        self.addCleanup(self.conn.close)
        transaction = self.conn.begin()
        self.addCleanup(transaction.rollback)
        self.session = Session(bind=self.conn)
        self.addCleanup(self.session.close)
        self.conn.exec_driver_sql('''
            insert into items(id,weight,name_en,normalized_name) values ('g',2,'Gun','gun'),('p',0.2,'Part','part'),('a',0.01,'Ammo','ammo');
            insert into weapon_items(item_id,ergonomics,recoil_vertical,recoil_horizontal,caliber,fire_rate,default_ammo_item_id,is_single_fire)
                values ('g',50,100,200,'caliber',800,'a',true);
            insert into ammo_items(item_id,recoil_modifier,accuracy_modifier) values ('a',0,0);
            insert into weapon_allowed_ammo values ('g','a');
            insert into item_categories(id,normalized_name) values ('weapon','weapon');
            insert into item_category_memberships values ('g','weapon',0);
            insert into item_mod_properties(item_id,properties_type,ergonomics,recoil_modifier) values ('p','ItemPropertiesWeaponMod',2,-0.1);
            insert into item_ballistics(item_id,properties_type,center_of_impact,deviation_curve,velocity_raw,initial_speed_mps) values
                ('g','ItemPropertiesWeapon',0.01,1.35,0,null),('p','ItemPropertiesWeaponMod',null,null,0,null),('a','ItemPropertiesAmmo',null,null,null,900);
            insert into item_slots(item_id,slot_id,name_id,required,sort_order) values ('g','s1','slot1',false,0),('g','s2','slot2',false,1);
            insert into item_slot_item_filters values ('g','s1','allowed','p',0),('g','s2','allowed','p',0);
        ''')
        app = FastAPI()
        app.include_router(router, prefix='/api/modding')
        app.include_router(rewards_router, prefix='/api/kord-breach')
        def session():
            yield self.session
        app.dependency_overrides[get_session] = session
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.request = {'weapon_item_id':'g','nodes':[{'node_id':'root','item_id':'g'},
            {'node_id':'one','item_id':'p','parent_node_id':'root','slot_id':'s1'},
            {'node_id':'two','item_id':'p','parent_node_id':'root','slot_id':'s2'}]}

    def calculate(self, data=None):
        return self.client.post('/api/modding/v3/calculate', json=data or self.request)

    def test_instance_sum_reference_recoil_units_and_default_ammo(self):
        response = self.calculate()
        self.assertEqual(response.status_code,200,response.text)
        data=response.json()['data'];stats=data['statistics']
        self.assertEqual(stats['weight_kg'],2.4)
        self.assertEqual(stats['ergonomics'],54)
        self.assertEqual(stats['recoil_vertical'],80)
        self.assertEqual(stats['recoil_horizontal'],160)
        self.assertEqual(stats['accuracy_moa'],0.34)
        self.assertEqual(stats['fire_rate_rpm'],800)
        self.assertEqual(data['ammo_selection'],'weapon_default')
        self.assertEqual(data['compatibility']['status'],'valid')
        self.assertIsNone(stats['muzzle_velocity_mps'])
        self.assertIn('VELOCITY_FORMULA_UNVERIFIED',[i['code'] for i in data['unavailable']])

    def test_zero_is_distinct_from_missing_and_cache_invalidates(self):
        first=self.calculate().json()['data']
        _calculate.cache_clear()
        self.calculate();self.calculate()
        self.assertGreaterEqual(_calculate.cache_info().hits,1)
        self.conn.exec_driver_sql("update items set weight=0 where id='p'")
        second=self.calculate().json()['data']
        self.assertEqual(second['statistics']['weight_kg'],2)
        self.assertNotEqual(first['source_revision'],second['source_revision'])
        self.conn.exec_driver_sql("update items set weight=null where id='p'")
        third=self.calculate().json()['data']
        self.assertIsNone(third['statistics']['weight_kg'])
        self.assertEqual(next(i for i in third['unavailable'] if i['metric']=='weight_kg')['item_ids'],['p'])

    def test_invalid_structures_are_422(self):
        import copy
        mutations = [lambda x:x['nodes'].append(x['nodes'][1]),
            lambda x:x['nodes'][1].update(parent_node_id='missing'),
            lambda x:x['nodes'][1].update(parent_node_id='one'),
            lambda x:x['nodes'][2].update(slot_id='s1'),
            lambda x:x['nodes'][0].update(slot_id='s1'),
            lambda x:x.update(nodes=[])]
        for mutate in mutations:
            data=copy.deepcopy(self.request);mutate(data)
            self.assertEqual(self.calculate(data).status_code,422)

    def test_unknown_items_and_ammo_errors(self):
        self.request['nodes'][1]['item_id']='missing'
        self.assertEqual(self.calculate().status_code,404)
        self.request['nodes'][1]['item_id']='p'
        self.request['ammo_item_id']='p'
        self.assertEqual(self.calculate().json()['detail'],'MODDING_AMMO_NOT_ALLOWED')

    def test_compatibility_is_separate_from_arithmetic(self):
        self.request['nodes'][1]['slot_id']='missing'
        response=self.calculate()
        self.assertEqual(response.status_code,200)
        data=response.json()['data']
        self.assertEqual(data['compatibility']['status'],'invalid')
        self.assertEqual(data['statistics']['weight_kg'],2.4)
        self.conn.exec_driver_sql("insert into item_conflicting_items values ('p','p',0)")
        self.assertIn('ITEM_CONFLICT',[i['code'] for i in self.calculate().json()['data']['compatibility']['issues']])

    def test_nonzero_ammo_correction_is_not_invented(self):
        self.conn.exec_driver_sql("update ammo_items set recoil_modifier=0.1,accuracy_modifier=0.2 where item_id='a'")
        result=self.calculate().json()['data']
        for key in ('recoil_vertical','recoil_horizontal','accuracy_moa'):
            self.assertIsNone(result['statistics'][key])
        self.assertIn('AMMO_CORRECTION_UNVERIFIED',[i['code'] for i in result['unavailable']])

    def test_ballistics_detail_contract(self):
        data=self.client.get('/api/modding/v3/items/g').json()['data']
        self.assertEqual(data['ballistics']['center_of_impact'],0.01)

    def seed_reward(self):
        self.conn.exec_driver_sql('''insert into quests(id,name_en,min_player_level,normalized_name) values ('q','Quest',30,'quest');
            insert into kord_breach_reward_snapshots values ('kord-breach','manual:verified-game-screen','r1',now());
            insert into kord_breach_rewards values ('kord-breach','reward','p',0,true);
        ''')

    def rewards(self):
        return self.client.get('/api/kord-breach/v3/rewards')

    def test_rewards_missing_snapshot_is_not_empty_success(self):
        response=self.rewards()
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json()['detail'],'KORD_REWARDS_UNAVAILABLE')

    def test_rewards_do_not_confuse_quest_start_and_unlock_levels(self):
        self.seed_reward()
        self.conn.exec_driver_sql("insert into kord_breach_reward_conditions values ('kord-breach','reward',0,0,'quest_completed',null,'q')")
        response=self.rewards();self.assertEqual(response.status_code,200,response.text)
        reward=response.json()['data']['rewards'][0]
        self.assertIsNone(reward['required_level'])
        self.assertEqual(reward['unlock_conditions'][0]['quest']['start_required_level'],30)
        self.assertIsNone(reward['item']['category'])

    def test_direct_level_or_groups_and_missing_quests(self):
        self.seed_reward()
        self.conn.exec_driver_sql("insert into kord_breach_reward_conditions values ('kord-breach','reward',0,0,'player_level',20,null)")
        self.assertEqual(self.rewards().json()['data']['rewards'][0]['required_level'],20)
        self.conn.exec_driver_sql("insert into kord_breach_reward_conditions values ('kord-breach','reward',1,0,'quest_completed',null,'missing')")
        reward=self.rewards().json()['data']['rewards'][0]
        self.assertIsNone(reward['required_level'])
        self.assertFalse(reward['unlock_conditions'][1]['quest']['is_registered'])
        self.assertEqual(reward['unlock_conditions'][1]['quest']['id'],'missing')

    def test_missing_barrel_data_and_multiple_barrels_are_not_guessed(self):
        self.conn.exec_driver_sql("update item_ballistics set properties_type='ItemPropertiesBarrel',center_of_impact=0.02,deviation_max=5 where item_id='p'")
        result=self.calculate().json()['data']
        self.assertIsNone(result['statistics']['accuracy_moa'])
        self.assertIn('MULTIPLE_BARRELS_UNSUPPORTED',[i['code'] for i in result['unavailable']])
        self.request['nodes'].pop()
        self.assertIsNotNone(self.calculate().json()['data']['statistics']['accuracy_moa'])
        self.conn.exec_driver_sql("update item_ballistics set center_of_impact=null where item_id='p'")
        self.assertIsNone(self.calculate().json()['data']['statistics']['accuracy_moa'])

    def test_selected_ammo_and_missing_default_are_explicit(self):
        self.request['ammo_item_id']='a'
        self.assertEqual(self.calculate().json()['data']['ammo_selection'],'requested')
        self.request.pop('ammo_item_id')
        self.conn.exec_driver_sql("update weapon_items set default_ammo_item_id=null where item_id='g'")
        result=self.calculate().json()['data']
        self.assertEqual(result['ammo_selection'],'unavailable')
        self.assertIsNone(result['ammo_item_id'])
        self.assertIsNone(result['statistics']['recoil_vertical'])
        self.assertIsNotNone(result['statistics']['weight_kg'])

    def test_ammo_is_a_separate_selector_not_loaded_weight_nodes(self):
        self.request['nodes'][1]['item_id']='a'
        response=self.calculate()
        self.assertEqual(response.status_code,422)
        self.assertEqual(response.json()['detail'],'MODDING_AMMO_MUST_BE_SEPARATE')

    def test_category_exclusion_and_unresolved_conflicts(self):
        self.conn.exec_driver_sql("insert into item_conflicting_slots values ('p','missing',0)")
        self.assertEqual(self.calculate().json()['data']['compatibility']['status'],'unknown')
        self.conn.exec_driver_sql("insert into item_categories(id) values ('excluded');insert into item_category_memberships values ('p','excluded',0);insert into item_slot_category_filters values ('g','s1','excluded','excluded',0)")
        result=self.calculate().json()['data']
        self.assertEqual(result['compatibility']['status'],'invalid')
        self.assertIn('SLOT_FILTER_REJECTED',[i['code'] for i in result['compatibility']['issues']])
