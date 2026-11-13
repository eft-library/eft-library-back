"""User build transactions, privacy, publication isolation, copying and ranking."""
import importlib.util
import json
import re
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from api.weapon_builds.router import router
from database import Database
from tests import test_modding_api as modding_fixture


@unittest.skipUnless(importlib.util.find_spec('pgserver'), 'Install pgserver for isolated PostgreSQL tests')
class WeaponBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        modding_fixture.ModdingApiTest.setUpClass.__func__(cls)
        root=Path(__file__).parents[1]
        source=(root/'platform_db.sql').read_text()
        with cls.engine.begin() as conn:
            conn.exec_driver_sql(re.search(r'create table if not exists user_info\s*\(.*?\n\);',source,re.S).group())
            conn.exec_driver_sql("insert into user_info(email,nickname,is_admin) values ('alice','Alice',false),('bob','Bob',false),('admin','Admin',true)")
        raw=cls.engine.raw_connection()
        try:
            with raw.cursor() as cur:
                migration=(root/'sql/migrations/20261110_user_weapon_builds.sql').read_text()
                cur.execute(migration)
                cur.execute(migration)
            raw.commit()
        finally:
            raw.close()

    def setUp(self):
        with self.engine.begin() as conn:
            conn.exec_driver_sql('truncate user_weapon_builds cascade')
        patcher=patch.object(Database,'SessionLocal',self.sessions)
        patcher.start();self.addCleanup(patcher.stop)
        auth=patch('api.weapon_builds.router.verify_google_access_token',side_effect=lambda token:token)
        auth.start();self.addCleanup(auth.stop)
        app=FastAPI();app.include_router(router,prefix='/api/modding')
        self.app=app;self.client=TestClient(app);self.addCleanup(self.client.close)

    def call(self, method, path='', user=None, **kwargs):
        headers={'Authorization':'Bearer '+user} if user else {}
        return self.client.request(method,'/api/modding/v3/builds'+path,headers=headers,**kwargs)

    def data(self,response,status=200):
        self.assertEqual(response.status_code,status,response.text)
        return response.json()['data'] if status==200 else response.json()

    def content(self,title='My build'):
        return {'weapon_item_id':'gun','title':title,'description':'plain text',
                'nodes':[{'node_id':'root','item_id':'gun'},
                         {'node_id':'receiver','parent_node_id':'root','slot_id':'receiver-slot','item_id':'receiver'},
                         {'node_id':'sight','parent_node_id':'receiver','slot_id':'rear-slot','item_id':'sight'}]}

    def create(self,user='alice',title='My build',request_id=None):
        return self.data(self.call('POST',user=user,json={**self.content(title),'request_id':request_id or str(uuid4())}))

    def publish(self,build,user='alice'):
        return self.data(self.call('POST','/'+build['id']+'/publication',user=user,json={'expected_version':build['version']}))

    def test_mine_search_filters_before_paging_and_never_leaks_other_owners(self):
        first=self.create(title='M4 소음기')
        self.publish(self.create(title='m4 기본형'))
        self.create(title='AK 기본형')
        self.create(user='bob',title='M4 타인 빌드')
        self.assertEqual(self.data(self.call('GET','/mine',user='alice'))['total'],3)
        result=self.data(self.call('GET','/mine',user='alice',params={'word':'  M4  ','page_size':1}))
        self.assertEqual(result['total'],2)
        self.assertEqual(len(result['builds']),1)
        second=self.data(self.call('GET','/mine',user='alice',params={'word':'M4','page_size':1,'page':2}))
        self.assertEqual(second['total'],2)
        self.assertNotEqual(result['builds'][0]['id'],second['builds'][0]['id'])
        found=self.data(self.call('GET','/mine',user='alice',params={'word':'소음기','weapon_item_id':'gun'}))
        self.assertEqual([b['id'] for b in found['builds']],[first['id']])
        for params in ({'word':"' OR 1=1 --"},{'word':'%'},{'word':'_'},{'word':'M4','weapon_item_id':'other'}):
            self.assertEqual(self.data(self.call('GET','/mine',user='alice',params=params))['total'],0)
        self.assertEqual(self.data(self.call('GET','/mine',user='alice',params={'word':'  '}))['total'],3)
        self.assertEqual(self.data(self.call('GET','/mine',user='alice',params={'word':'M4','page':100}))['builds'],[])
        self.data(self.call('GET','/mine',params={'word':'M4'}),401)
        for params in ({'word':'a'*201},{'weapon_item_id':''}):
            self.data(self.call('GET','/mine',user='alice',params=params),422)

    def test_private_visibility_owner_checks_and_registered_auth(self):
        build=self.create();path='/'+build['id']
        self.data(self.call('GET',path),404)
        self.data(self.call('GET',path,user='bob'),404)
        owned=self.call('GET',path,user='alice')
        self.assertEqual(self.data(owned)['view'],'draft')
        self.assertEqual(owned.headers['cache-control'],'private, no-store')
        self.data(self.call('PUT',path,user='bob',json={**self.content(),'expected_version':1}),404)
        self.data(self.call('DELETE',path,user='bob',params={'expected_version':1}),404)
        self.data(self.call('GET','/mine'),401)
        self.data(self.call('POST',user='unknown',json={**self.content(),'request_id':str(uuid4())}),403)
        self.assertEqual(self.data(self.call('GET'))['total'],0)

    def test_publication_is_frozen_until_republished_and_version_guard(self):
        build=self.publish(self.create());path='/'+build['id']
        first=self.data(self.call('GET',path));self.assertEqual(first['revision'],2)
        draft=self.data(self.call('PUT',path,user='alice',json={**self.content('Private edit'),'expected_version':2}))
        self.assertEqual(draft['version'],3)
        self.assertEqual(self.data(self.call('GET',path))['content']['title'],'My build')
        self.assertEqual(self.data(self.call('GET'))['builds'][0]['title'],'My build')
        self.data(self.call('PUT',path,user='alice',json={**self.content(),'expected_version':2}),409)
        self.data(self.call('POST',path+'/publication',user='alice',json={'expected_version':2}),409)
        published=self.publish(draft)
        self.assertEqual(published['published_revision'],4)
        self.assertEqual(self.data(self.call('GET',path))['content']['title'],'Private edit')
        unchanged=self.publish(published)
        self.assertEqual(unchanged['published_revision'],4)

    def test_copy_is_independent_and_request_ids_are_idempotent(self):
        source=self.publish(self.create());path='/'+source['id']
        source=self.data(self.call('PUT',path,user='alice',json={**self.content('Unpublished edit'),'expected_version':source['version']}))
        request={'request_id':str(uuid4()),'revision':source['published_revision']}
        copy=self.data(self.call('POST',path+'/copy',user='bob',json=request))
        replay=self.data(self.call('POST',path+'/copy',user='bob',json=request))
        self.assertEqual(copy['id'],replay['id'])
        self.assertFalse(copy['is_public'])
        self.assertEqual(copy['content']['title'],'My build')
        self.assertEqual(copy['copied_from']['author_nickname'],'Alice')
        self.data(self.call('POST',path+'/copy',user='bob',json={**request,'revision':999}),409)
        self.data(self.call('DELETE',path,user='alice',params={'expected_version':source['version']}))
        copied=self.data(self.call('GET','/'+copy['id'],user='bob'))
        self.assertEqual(len(copied['content']['nodes']),3)
        self.assertIsNone(copied['copied_from']['build_id'])
        self.assertEqual(copied['copied_from']['title'],'My build')

    def test_create_idempotency_and_tree_validation(self):
        request=str(uuid4());a=self.create(request_id=request);b=self.create(request_id=request)
        self.assertEqual(a['id'],b['id'])
        self.data(self.call('POST',user='alice',json={**self.content('different'),'request_id':request}),409)
        invalid=[
            [{'node_id':'a','item_id':'gun'},{'node_id':'b','item_id':'gun'}],
            [{'node_id':'root','item_id':'gun'},{'node_id':'x','parent_node_id':'missing','slot_id':'s','item_id':'sight'}],
            [{'node_id':'root','item_id':'gun'},{'node_id':'x','parent_node_id':'y','slot_id':'a','item_id':'sight'},
             {'node_id':'y','parent_node_id':'x','slot_id':'b','item_id':'sight'}],
            [{'node_id':'root','item_id':'gun'},{'node_id':'x','parent_node_id':'root','slot_id':'a','item_id':'sight'},
             {'node_id':'y','parent_node_id':'root','slot_id':'a','item_id':'sight'}],
        ]
        for nodes in invalid:
            with self.subTest(nodes=nodes):
                self.data(self.call('POST',user='alice',json={**self.content(),'nodes':nodes,'request_id':str(uuid4())}),422)
        self.assertEqual(self.data(self.call('GET','/mine',user='alice'))['total'],1)

    def test_vote_is_unique_and_republication_has_separate_votes(self):
        source=self.publish(self.create());path='/'+source['id'];revision=source['published_revision']
        self.data(self.call('PUT',path+'/vote',user='alice',json={'revision':revision}),403)
        for _ in range(2):
            self.assertEqual(self.data(self.call('PUT',path+'/vote',user='bob',json={'revision':revision}))['vote_count'],1)
        self.assertTrue(self.data(self.call('GET',path,user='bob'))['has_voted'])
        self.assertEqual(self.data(self.call('GET',params={'sort':'best','period':'week'}))['builds'][0]['score'],1)
        draft=self.data(self.call('PUT',path,user='alice',json={**self.content('new'),'expected_version':source['version']}))
        source=self.publish(draft)
        self.assertEqual(self.data(self.call('GET',path))['vote_count'],0)
        self.data(self.call('PUT',path+'/vote',user='bob',json={'revision':revision}),409)
        self.data(self.call('DELETE',path+'/vote',user='bob',params={'revision':source['published_revision']}))

    def test_ranking_windows_use_vote_time_and_publication_metadata(self):
        source=self.publish(self.create());path='/'+source['id']
        self.data(self.call('PUT',path+'/vote',user='bob',json={'revision':source['published_revision']}))
        with self.engine.begin() as c:
            c.execute(text("update user_weapon_build_votes set created_at=now()-interval '10 days'"))
        self.assertEqual(self.data(self.call('GET',params={'sort':'best','period':'week'}))['builds'][0]['score'],0)
        self.assertEqual(self.data(self.call('GET',params={'sort':'best','period':'month'}))['builds'][0]['score'],1)
        default=self.data(self.call('GET',params={'sort':'best'}))
        self.assertEqual(default['period'],'month')
        self.assertEqual(default['builds'][0]['score'],1)
        self.assertEqual(self.data(self.call('GET',params={'weapon_item_id':'missing'}))['total'],0)
        self.assertEqual(self.data(self.call('GET',params={'word':"' OR 1=1 --"}))['total'],0)

    def test_comments_idempotency_permissions_versions_and_revision_isolation(self):
        source=self.publish(self.create());path='/'+source['id'];revision=source['published_revision']
        request={'request_id':str(uuid4()),'revision':revision,'content':' Hello '}
        comment=self.data(self.call('POST',path+'/comments',user='bob',json=request))
        self.assertEqual(self.data(self.call('POST',path+'/comments',user='bob',json=request))['id'],comment['id'])
        comment_path=path+'/comments/'+comment['id']
        self.data(self.call('PUT',comment_path,user='alice',json={'expected_version':1,'content':'Hijack'}),404)
        updated=self.data(self.call('PUT',comment_path,user='bob',json={'expected_version':1,'content':'Updated'}))
        self.assertEqual(updated['version'],2)
        self.data(self.call('DELETE',comment_path,user='bob',params={'expected_version':1}),409)
        listing=self.data(self.call('GET',path+'/comments',user='bob'))
        self.assertEqual(listing['total'],1)
        self.assertTrue(listing['comments'][0]['is_mine'])
        self.assertEqual(listing['comments'][0]['content'],'Updated')
        draft=self.data(self.call('PUT',path,user='alice',json={**self.content('new'),'expected_version':source['version']}))
        self.publish(draft)
        self.assertEqual(self.data(self.call('GET',path+'/comments'))['total'],0)
        self.data(self.call('POST',path+'/comments',user='bob',json={**request,'request_id':str(uuid4())}),409)
        self.data(self.call('DELETE',comment_path,user='admin',params={'expected_version':2}))

    def test_withdrawal_hides_build_and_copy(self):
        source=self.publish(self.create());path='/'+source['id']
        private=self.data(self.call('DELETE',path+'/publication',user='alice',params={'expected_version':source['version']}))
        self.assertFalse(private['is_public'])
        self.data(self.call('GET',path),404)
        self.data(self.call('GET',path+'/comments'),404)
        self.data(self.call('POST',path+'/copy',user='bob',json={'revision':source['published_revision'],'request_id':str(uuid4())}),404)
        self.assertEqual(self.data(self.call('GET'))['total'],0)

    def test_unknown_item_rejected_and_changed_source_warns_without_destroying_copy(self):
        content=self.content();content['nodes'][2]['item_id']='not-in-source'
        self.data(self.call('POST',user='alice',json={**content,'request_id':str(uuid4())}),404)
        with self.engine.begin() as c:
            c.exec_driver_sql("insert into items(id,name_en) values ('temporary-part','Retired part')")
        content=self.content();content['nodes'][2]['item_id']='temporary-part'
        draft=self.data(self.call('POST',user='alice',json={**content,'request_id':str(uuid4())}))
        source=self.publish(draft);path='/'+source['id']
        with self.engine.begin() as c:
            c.exec_driver_sql("delete from items where id='temporary-part'")
        public=self.data(self.call('GET',path))
        self.assertEqual(public['warnings'],[{'node_id':'sight','code':'SOURCE_ITEM_MISSING'}])
        copied=self.data(self.call('POST',path+'/copy',user='bob',json={'revision':source['published_revision'],'request_id':str(uuid4())}))
        self.assertEqual(copied['content']['nodes'][2]['item']['name_en'],'Retired part')
        updated=self.data(self.call('PUT','/'+copied['id'],user='bob',json={**content,'expected_version':copied['version']}))
        self.assertEqual(updated['warnings'],[{'node_id':'sight','code':'SOURCE_ITEM_MISSING'}])
        content['nodes'][2]['slot_id']='missing-slot'
        updated=self.data(self.call('PUT','/'+copied['id'],user='bob',json={**content,'expected_version':updated['version']}))
        self.assertIn({'node_id':'sight','code':'SOURCE_SLOT_MISSING'},updated['warnings'])
        self.assertEqual(updated['validation_scope'],'structure_only')

    def test_parallel_votes_and_creates_do_not_duplicate(self):
        source=self.publish(self.create());path='/'+source['id']
        def vote(_):
            with TestClient(self.app) as client:
                return client.put('/api/modding/v3/builds'+path+'/vote',headers={'Authorization':'Bearer bob'},json={'revision':source['published_revision']}).status_code
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(vote,range(4))),[200]*4)
        self.assertEqual(self.data(self.call('GET',path))['vote_count'],1)
        request={'request_id':str(uuid4()),**self.content('parallel')}
        def create(_):
            with TestClient(self.app) as client:
                r=client.post('/api/modding/v3/builds',headers={'Authorization':'Bearer bob'},json=request)
                self.assertEqual(r.status_code,200,r.text)
                return r.json()['data']['id']
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(len(set(pool.map(create,range(4)))),1)

    def test_failed_node_write_rolls_back_build_and_deferred_fk_is_checked(self):
        from api.weapon_builds import service
        original=service.write_nodes
        def fail(session, build_id, nodes):
            original(session,build_id,nodes)
            raise OperationalError('failure',None,Exception())
        with patch('api.weapon_builds.service.write_nodes',side_effect=fail),self.assertLogs('api.weapon_builds.router',level='ERROR'):
            self.data(self.call('POST',user='alice',json={**self.content(),'request_id':str(uuid4())}),503)
        self.assertEqual(self.data(self.call('GET','/mine',user='alice'))['total'],0)

    def test_deferred_publication_fk_failure_cannot_return_false_success(self):
        from api.weapon_builds.service import BuildService
        original=BuildService.create
        def broken(session, actor, request):
            result=original(session,actor,request)
            session.execute(text("update user_weapon_builds set version=999,published_revision=999,is_public=true where id=:id"),{'id':result['id']})
            return result
        with patch.object(BuildService,'create',side_effect=broken),self.assertLogs('api.weapon_builds.router',level='ERROR'):
            self.data(self.call('POST',user='alice',json={**self.content(),'request_id':str(uuid4())}),503)
        self.assertEqual(self.data(self.call('GET','/mine',user='alice'))['total'],0)

    def test_parallel_edits_reject_stale_version(self):
        build=self.create();path='/'+build['id']
        def update(index):
            with TestClient(self.app) as client:
                return client.put('/api/modding/v3/builds'+path,headers={'Authorization':'Bearer alice'},
                    json={**self.content('edit '+str(index)),'expected_version':1}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(update,range(2))),[200,409])
        self.assertEqual(self.data(self.call('GET',path,user='alice'))['version'],2)

    def test_comment_rate_limit_and_build_quota(self):
        source=self.publish(self.create());path='/'+source['id']
        for i in range(10):
            self.data(self.call('POST',path+'/comments',user='bob',json={
                'request_id':str(uuid4()),'revision':source['published_revision'],'content':'comment '+str(i)}))
        response=self.call('POST',path+'/comments',user='bob',json={
            'request_id':str(uuid4()),'revision':source['published_revision'],'content':'too many'})
        self.data(response,429)
        self.assertEqual(response.headers['retry-after'],'60')
        with self.engine.begin() as c:
            c.execute(text("""insert into user_weapon_builds
                (id,owner_email,request_id,request_fingerprint,weapon_item_id,title)
                values (:id,'bob',:request,'seed','gun','seed')"""),
                [{'id':uuid4(),'request':uuid4()} for _ in range(100)])
        self.data(self.call('POST',user='bob',json={**self.content(),'request_id':str(uuid4())}),429)

    def test_account_deletion_cascades_content_but_preserves_other_users_copies(self):
        source=self.publish(self.create());path='/'+source['id']
        copied=self.data(self.call('POST',path+'/copy',user='bob',json={'revision':source['published_revision'],'request_id':str(uuid4())}))
        try:
            with self.engine.begin() as c:
                c.exec_driver_sql("delete from user_info where email='alice'")
            self.data(self.call('GET',path),404)
            detail=self.data(self.call('GET','/'+copied['id'],user='bob'))
            self.assertIsNone(detail['copied_from']['build_id'])
            self.assertEqual(detail['copied_from']['author_nickname'],'Alice')
            self.assertEqual(len(detail['content']['nodes']),3)
        finally:
            with self.engine.begin() as c:
                c.exec_driver_sql("insert into user_info(email,nickname,is_admin) values ('alice','Alice',false) on conflict do nothing")

    def test_public_detail_and_comments_allow_anonymous_without_token_verification(self):
        source=self.publish(self.create());path='/'+source['id']
        with patch('api.weapon_builds.router.verify_google_access_token') as verify:
            detail=self.data(self.call('GET',path))
            comments=self.data(self.call('GET',path+'/comments',params={'revision':source['published_revision']}))
            verify.assert_not_called()
        self.assertFalse(detail['is_mine'])
        self.assertFalse(detail['has_voted'])
        self.assertEqual(comments['revision'],detail['revision'])
        from util.http_exceptions import HttpError
        with patch('api.weapon_builds.router.verify_google_access_token',side_effect=HttpError.INVALID_TOKEN.exception()):
            self.data(self.call('GET',path,user='invalid'),401)
            self.data(self.call('GET',path+'/comments',user='invalid'),401)

    def test_comment_revision_prevents_reading_a_different_publication(self):
        source=self.publish(self.create());path='/'+source['id'];old=source['published_revision']
        self.assertEqual(self.data(self.call('GET',path+'/comments',params={'revision':old}))['revision'],old)
        draft=self.data(self.call('PUT',path,user='alice',json={**self.content('Republished'),'expected_version':source['version']}))
        source=self.publish(draft)
        response=self.call('GET',path+'/comments',params={'revision':old})
        self.assertEqual(self.data(response,409)['detail'],'BUILD_REVISION_CONFLICT')
        self.assertEqual(self.data(self.call('GET',path+'/comments'))['revision'],source['published_revision'])
        self.assertEqual(self.data(self.call('GET',path+'/comments',params={'revision':source['published_revision']}))['revision'],source['published_revision'])
        self.data(self.call('GET',path+'/comments',params={'revision':0}),422)

    def test_openapi_optional_auth_error_models_and_retry_header(self):
        schema=self.app.openapi();paths=schema['paths'];base='/api/modding/v3/builds'
        for suffix in ('/{build_id}','/{build_id}/comments'):
            security=paths[base+suffix]['get']['security']
            self.assertIn({},security)
            self.assertIn({'OAuth2PasswordBearer':[]},security)
        self.assertNotIn({},paths[base+'/mine']['get']['security'])
        self.assertNotIn({},paths[base]['post']['security'])
        self.assertNotIn('security',paths[base]['get'])
        for path in paths.values():
            for method,operation in path.items():
                if method not in ('get','post','put','delete'):
                    continue
                self.assertIn('503',operation['responses'])
                for status,response in operation['responses'].items():
                    if status in ('401','403','404','409','429','503'):
                        self.assertEqual(response['content']['application/json']['schema']['$ref'],'#/components/schemas/BuildError')
        comment=paths[base+'/{build_id}/comments']
        self.assertIn('revision',[p['name'] for p in comment['get']['parameters']])
        retry=comment['post']['responses']['429']['headers']['Retry-After']
        self.assertEqual(retry['example'],'60')
        conflict=comment['get']['responses']['409']['content']['application/json']['examples']
        self.assertIn('BUILD_REVISION_CONFLICT',conflict)
        defaults=next(p for p in paths[base]['get']['parameters'] if p['name']=='period')
        self.assertEqual(defaults['schema']['default'],'month')

    def test_omitted_root_mount_fields_normalize_to_null_but_child_fields_are_required(self):
        created=self.create()
        root=created['content']['nodes'][0]
        self.assertIsNone(root['parent_node_id'])
        self.assertIsNone(root['slot_id'])
        invalid=self.content();del invalid['nodes'][1]['slot_id']
        self.data(self.call('POST',user='alice',json={**invalid,'request_id':str(uuid4())}),422)
        invalid=self.content();del invalid['nodes'][1]['parent_node_id']
        self.data(self.call('POST',user='alice',json={**invalid,'request_id':str(uuid4())}),422)
        schema=self.app.openapi()['components']['schemas']['BuildNodeInput']
        self.assertNotIn('parent_node_id',schema['required'])
        self.assertNotIn('slot_id',schema['required'])

    def test_no_owner_email_or_token_in_public_payload(self):
        source=self.publish(self.create());path='/'+source['id']
        for endpoint in (path,'',path+'/comments'):
            data=self.data(self.call('GET',endpoint))
            serialized=json.dumps(data)
            self.assertNotIn('owner_email',serialized)
            self.assertNotIn('author_email',serialized)
            self.assertNotIn('access_token',serialized)
