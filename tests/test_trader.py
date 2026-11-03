"""Trader API integration tests using the authoritative DDL and isolated PostgreSQL."""
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from api.trader.router import router
from database import Database


@unittest.skipUnless(importlib.util.find_spec('pgserver'), 'Install pgserver for isolated PostgreSQL tests')
class TraderApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pgserver
        directory = tempfile.TemporaryDirectory(prefix='trader-api-')
        cls.addClassCleanup(directory.cleanup)
        server = pgserver.get_server(Path(directory.name) / 'postgres', cleanup_mode='delete')
        cls.addClassCleanup(server.cleanup)
        cls.engine = create_engine(server.get_uri())
        cls.addClassCleanup(cls.engine.dispose)
        source = (Path(__file__).parents[1] / 'platform_db.sql').read_text()
        names = ('traders', 'items', 'quests', 'price_seasons', 'trader_offers',
                 'trader_offer_costs', 'trader_offer_rewards',
                 'trader_offer_task_unlocks', 'trader_restock_state')
        with cls.engine.begin() as conn:
            for name in names:
                ddl = re.search(rf'create table if not exists {name}\s*\(.*?\n\);', source, re.S).group()
                conn.exec_driver_sql(ddl)
            conn.execute(text("""
                insert into traders(id,name_ko,sort_order,is_use) values
                    ('prapor','프라퍼',1,true), ('therapist','테라피스트',2,true), ('hidden','숨김',3,false);
                insert into items(id,name_en,name_ko,name_ja,width,height) values
                    ('gun','Rifle','소총','ライフル',2,3), ('cash','Roubles','루블','ルーブル',1,1),
                    ('material','100% part','재료','素材',1,2);
                insert into price_seasons(id,is_current) values ('current',true),('old',false);
                insert into trader_offers(id,source_offer_id,trader_id,trader_level,offer_type,game_mode,season_id,buy_limit,is_unlimited,sort_order) values
                    ('purchase','purchase:gun','prapor',1,'purchase','pvp',null,3,false,1),
                    ('barter','barter:gun','prapor',3,'barter','pvp',null,null,null,2),
                    ('pve','purchase:gun','prapor',1,'purchase','pve',null,null,true,1),
                    ('season','purchase:gun','prapor',1,'purchase','pvp-season','current',null,null,1),
                    ('past','purchase:gun','prapor',1,'purchase','pvp-season','old',null,null,1),
                    ('disabled','disabled','prapor',1,'purchase','pvp',null,null,null,3),
                    ('hidden','hidden','hidden',1,'purchase','pvp',null,null,null,4);
                update trader_offers set is_use=false where id='disabled';
                insert into trader_offer_rewards(offer_id,item_id,quantity) select id,'gun',1 from trader_offers;
                insert into trader_offer_rewards(offer_id,item_id,quantity) values ('barter','material',2);
                insert into trader_offer_costs(offer_id,item_id,quantity) values
                    ('purchase','cash',45000.50),('barter','material',2),('barter','cash',10);
                insert into trader_offer_task_unlocks(offer_id,quest_id) values ('barter','missing-quest');
                insert into trader_restock_state(trader_id,game_mode,next_restock_at) values
                    ('prapor','pvp','2030-01-01T00:00:00Z');
            """))
        cls.sessions = sessionmaker(cls.engine)

    def setUp(self):
        patcher = patch.object(Database, 'SessionLocal', self.sessions)
        patcher.start()
        self.addCleanup(patcher.stop)
        app = FastAPI()
        app.include_router(router, prefix='/api/trader')
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def offers(self, **params):
        response = self.client.get('/api/trader/v3/offers', params=params)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['data']

    def test_traders_order_restock_and_missing_state(self):
        data = self.client.get('/api/trader/v3/list').json()['data']
        self.assertEqual([row['id'] for row in data['traders']], ['prapor','therapist'])
        self.assertTrue(data['traders'][0]['next_restock_at'].startswith('2030-01-01'))
        self.assertIsNone(data['traders'][1]['next_restock_at'])
        self.assertIsNone(self.client.get('/api/trader/v3/list?game_mode=pve').json()['data']['traders'][0]['next_restock_at'])

    def test_offer_level_search_pagination_and_isolation(self):
        self.assertEqual(self.offers()['total'], 2)
        self.assertEqual(self.offers(level=1)['total'], 1)
        for word in ('RIFLE', '소총', 'ライフル'):
            self.assertEqual(self.offers(word=word)['total'], 2)
        self.assertEqual(self.offers(word='100%')['total'], 1)
        self.assertEqual(self.offers(word="' OR 1=1 --")['total'], 0)
        page = self.offers(page=2,page_size=1)
        self.assertEqual(page['total'],2)
        self.assertEqual(page['offers'][0]['id'],'barter')
        self.assertEqual(self.offers(page=10)['offers'], [])
        self.assertEqual(self.offers(trader_id='therapist')['total'], 0)
        self.assertEqual(self.offers(offer_type='barter')['total'], 1)
        self.assertEqual(self.offers(game_mode='pve')['offers'][0]['id'], 'pve')
        self.assertEqual(self.offers(game_mode='pvp-season')['season_id'], 'current')
        self.assertEqual(self.offers(game_mode='pvp-season',season_id='old')['offers'][0]['id'], 'past')

    def test_details_preserve_children_and_unknown_unlock(self):
        result = self.client.get('/api/trader/v3/offers/barter').json()['data']
        self.assertEqual(len(result['costs']), 2)
        self.assertEqual(len(result['rewards']), 2)
        self.assertEqual(result['trader']['name_ko'], '프라퍼')
        self.assertIsNone(result['is_unlimited'])
        self.assertEqual(result['task_unlocks'][0]['quest_id'], 'missing-quest')
        self.assertIsNone(result['task_unlocks'][0]['name_en'])
        purchase = self.client.get('/api/trader/v3/offers/purchase').json()['data']
        self.assertEqual(purchase['costs'][0]['quantity'],45000.5)
        self.assertEqual(purchase['rewards'][0]['item']['height'],3)
        self.assertEqual(purchase['buy_limit'],3)
        self.assertFalse(purchase['is_unlimited'])

    def test_validation_and_missing_resources(self):
        for params in ({'level':0},{'level':5},{'page':0},{'page_size':501},
                       {'game_mode':'regular'},{'offer_type':'bad'}, {'season_id':'old'}):
            self.assertEqual(self.client.get('/api/trader/v3/offers',params=params).status_code,422)
        for url in ('/api/trader/v3/offers/no-such-offer',
                    '/api/trader/v3/offers/disabled','/api/trader/v3/offers/hidden',
                    '/api/trader/v3/offers/pve', '/api/trader/v3/offers?trader_id=missing',
                    '/api/trader/v3/offers?game_mode=pvp-season&season_id=missing'):
            self.assertEqual(self.client.get(url).status_code,404,url)

    def test_database_failure_is_http_error(self):
        with patch.object(Database,'SessionLocal',side_effect=OperationalError('offline',None,Exception())):
            response = self.client.get('/api/trader/v3/offers')
        self.assertEqual(response.status_code,500)
        self.assertEqual(response.json()['detail'],'Trader lookup failed')
