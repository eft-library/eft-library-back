"""Real isolated PostgreSQL and Redis. Never connects to configured production services."""
import asyncio
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi import HTTPException
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import func, select

from api.live_map.chat_v3.models import ChatMessageV3, PartyInvitationV3
from api.live_map.chat_v3.router import router_v3
from api.live_map.chat_v3.schemas import ChatSendV3
from api.live_map.chat_v3.service import ChatServiceV3, event_v3, now_v3
from api.live_map.chat_v3.store import ChatStoreV3
from api.user.user_res_models import UserV3
from tests import test_live_map_party_postgres_v3 as postgres_tests_v3


class ChatPostgresTestV3(postgres_tests_v3.PartyPostgresTestV3):
    def setUp(self):
        super().setUp()
        self.chat_store_v3 = ChatStoreV3(self.redis_v3)
        for target in ('api.live_map.chat_v3.store.get_chat_store_v3',
                       'api.live_map.chat_v3.router.get_chat_store_v3',
                       'api.live_map.chat_v3.websocket.get_chat_store_v3'):
            patcher = patch(target, return_value=self.chat_store_v3)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch('api.live_map.chat_v3.websocket.create_party_subscriber_v3', side_effect=self.create_subscriber_v3)
        patcher.start()
        self.addCleanup(patcher.stop)

        def auth_v3(credentials):
            if credentials.credentials == 'bad':
                raise HTTPException(401, 'INVALID_TOKEN')
            return credentials.credentials + '@example.test'
        patcher = patch('api.live_map.chat_v3.websocket.authenticate_party_user_v3', side_effect=auth_v3)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.app_v3.include_router(router_v3, prefix='/live-map')
        with self.sessions_v3.begin() as session:
            session.get(UserV3, 'owner@example.test').is_admin = True
        self.ids_v3 = {}
        for name in ('owner', 'member', 'other', 'outsider'):
            with self.sessions_v3.begin() as session:
                self.ids_v3[name] = ChatServiceV3(session).identity_v3(name + '@example.test').id

    def chat_request_v3(self, method, path, user='owner', **kwargs):
        headers = {} if user is None else {'x-test-user': user}
        return self.client_v3.request(method, '/live-map/v3' + path, headers=headers, **kwargs)

    def chat_send_v3(self, user='owner', **changes):
        body = {'channel': 'lobby', 'message': 'hello', 'request_id': uuid4()}
        body.update(changes)
        with self.sessions_v3.begin() as session:
            service = ChatServiceV3(session, self.chat_store_v3)
            return service.send_v3(service.identity_v3(user + '@example.test'), ChatSendV3(**body))

    def invite_v3(self, room_id, target='member', user='owner'):
        return self.chat_request_v3('POST', '/party-invitations', user=user, json={
            'room_id': room_id, 'invitee_user_id': str(self.ids_v3[target])})

    @contextmanager
    def chat_socket_v3(self, user='owner'):
        with self.client_v3.websocket_connect('/live-map/v3/chat/ws') as websocket:
            websocket.send_json({'type': 'auth', 'token': user})
            yield websocket

    def test_chat_available_by_default_alongside_party_v3(self):
        self.assertEqual(self.chat_request_v3('GET', '/chat/messages?channel=lobby').status_code, 200)
        room = self.create_v3()
        self.assertEqual(self.join_v3(room['room']['id']).status_code, 200)
        with self.chat_socket_v3() as websocket:
            self.assertEqual(self.snapshot_v3(websocket)['data']['party_room_id'], room['room']['id'])

    def test_registration_history_cursor_and_privacy_v3(self):
        for user, status in ((None, 401), ('unknown', 403)):
            self.assertEqual(self.chat_request_v3('GET', '/chat/messages?channel=lobby', user=user).status_code, status)
        for index in range(3):
            self.chat_send_v3(message=f'line {index}')
        first = self.chat_request_v3('GET', '/chat/messages?channel=lobby&limit=2').json()['data']
        self.assertEqual([m['message'] for m in first['messages']], ['line 2', 'line 1'])
        second = self.chat_request_v3('GET', '/chat/messages', params={
            'channel': 'lobby', 'limit': 2, 'before': first['next_before']}).json()['data']
        self.assertEqual([m['message'] for m in second['messages']], ['line 0'])
        self.assertIsNone(second['next_before'])
        self.assertNotIn('email', str(first))
        self.assertNotIn('profile_image', str(first))
        self.assertEqual(set(first['messages'][0]['user']), {'id', 'nickname'})
        self.assertEqual(self.chat_request_v3('GET', '/chat/messages?channel=lobby&before=bad').status_code, 422)

    def test_concurrent_idempotency_rate_limit_and_repetition_v3(self):
        request_id = uuid4()
        ready = threading.Barrier(2)
        def send_v3(_):
            ready.wait(5)
            return self.chat_send_v3(request_id=request_id)
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(send_v3, range(2)))
        self.assertEqual(sorted(row['duplicate'] for row in results), [False, True])
        self.assertEqual(results[0]['message_id'], results[1]['message_id'])
        with self.assertRaises(HTTPException) as error:
            self.chat_send_v3(request_id=request_id, message='changed')
        self.assertEqual(error.exception.detail, 'CHAT_REQUEST_ID_CONFLICT')
        with self.assertRaises(HTTPException) as error:
            self.chat_send_v3()
        self.assertEqual(error.exception.detail, 'CHAT_REPEATED_MESSAGE')
        self.redis_v3.flushdb()
        for index in range(5):
            self.chat_send_v3(message=f'msg {index}')
        with self.assertRaises(HTTPException) as error:
            self.chat_send_v3(message='sixth')
        self.assertEqual(error.exception.detail, 'CHAT_RATE_LIMITED')
        self.assertGreater(int(error.exception.headers['Retry-After']), 0)

    def test_party_permissions_rechecked_after_kick_leave_and_close_v3(self):
        room_id = self.create_v3()['room']['id']
        member = self.join_v3(room_id).json()['data']['me']['id']
        message = self.chat_send_v3(channel='party', room_id=UUID(room_id))
        path = '/chat/messages?channel=party&room_id=' + room_id
        self.assertEqual(self.chat_request_v3('GET', path, user='member').status_code, 200)
        self.assertEqual(self.chat_request_v3('GET', path, user='other').status_code, 403)
        self.request_v3('POST', f'/{room_id}/members/{member}/kick')
        self.assertEqual(self.chat_request_v3('GET', path, user='member').status_code, 403)
        with self.sessions_v3.begin() as session:
            service = ChatServiceV3(session)
            self.assertIsNone(service.forward_v3(service.identity_v3('member@example.test'),
                event_v3('chat_message', {'message_id': message['message_id']})))
        self.join_v3(room_id, user='other')
        self.request_v3('POST', f'/{room_id}/leave', user='other')
        self.assertEqual(self.chat_request_v3('GET', path, user='other').status_code, 403)
        self.request_v3('DELETE', f'/{room_id}')
        self.assertEqual(self.chat_request_v3('GET', path).status_code, 410)

    def test_owner_only_targeted_invite_accept_without_password_v3(self):
        room_id = self.create_v3()['room']['id']
        self.join_v3(room_id, user='other')
        self.assertEqual(self.invite_v3(room_id, user='other').status_code, 403)
        invited = self.invite_v3(room_id)
        self.assertEqual(invited.status_code, 201, invited.text)
        self.assertNotIn('password', invited.text)
        self.assertNotIn('email', invited.text)
        invitation = invited.json()['data']['id']
        self.assertEqual(self.invite_v3(room_id).json()['msg'], 'PARTY_INVITATION_DUPLICATED')
        self.assertEqual(self.chat_request_v3('GET', '/party-invitations', user='outsider').json()['data'], [])
        path = '/party-invitations/' + invitation + '/accept'
        self.assertEqual(self.chat_request_v3('POST', path, user='other').status_code, 403)
        accepted = self.chat_request_v3('POST', path, user='member')
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(accepted.json()['data']['me']['role'], 'member')
        self.assertEqual(self.chat_request_v3('POST', path, user='member').json()['msg'], 'PARTY_INVITATION_ALREADY_HANDLED')
        self.assertEqual(self.request_v3('GET', f'/{room_id}', user='member').status_code, 200)

    def test_invite_locked_full_expired_rejected_revoked_and_kicked_v3(self):
        room_id = self.create_v3(max_members=2)['room']['id']
        invitation = self.invite_v3(room_id).json()['data']['id']
        path = '/party-invitations/' + invitation
        self.request_v3('PATCH', f'/{room_id}', json={'is_locked': True})
        self.assertEqual(self.chat_request_v3('POST', path + '/accept', user='member').json()['msg'], 'PARTY_ROOM_LOCKED')
        self.request_v3('PATCH', f'/{room_id}', json={'is_locked': False})
        with self.sessions_v3.begin() as session:
            session.get(PartyInvitationV3, UUID(invitation)).expires_at = now_v3() - timedelta(seconds=1)
        self.assertEqual(self.chat_request_v3('POST', path + '/accept', user='member').json()['msg'], 'PARTY_INVITATION_EXPIRED')
        invitation = self.invite_v3(room_id).json()['data']['id']
        self.assertEqual(self.chat_request_v3('POST', '/party-invitations/' + invitation + '/reject', user='member').status_code, 200)
        invitation = self.invite_v3(room_id).json()['data']['id']
        self.assertEqual(self.chat_request_v3('DELETE', '/party-invitations/' + invitation, user='outsider').status_code, 403)
        self.assertEqual(self.chat_request_v3('DELETE', '/party-invitations/' + invitation).status_code, 200)
        invitation = self.invite_v3(room_id).json()['data']['id']
        member_id = self.join_v3(room_id, user='other').json()['data']['me']['id']
        self.assertEqual(self.chat_request_v3('POST', '/party-invitations/' + invitation + '/accept', user='member').json()['msg'], 'PARTY_ROOM_FULL')
        self.request_v3('POST', f'/{room_id}/members/{member_id}/kick')
        self.assertEqual(self.invite_v3(room_id, target='other').json()['msg'], 'PARTY_MEMBER_KICKED')

    def test_concurrent_accepts_cannot_exceed_capacity_or_join_two_rooms_v3(self):
        room_id = self.create_v3(max_members=2)['room']['id']
        ids = {name: self.invite_v3(room_id, target=name).json()['data']['id'] for name in ('member', 'other')}
        ready = threading.Barrier(2)
        def accept_v3(name):
            ready.wait(5)
            return self.chat_request_v3('POST', '/party-invitations/' + ids[name] + '/accept', user=name).status_code
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(accept_v3, ids))
        self.assertEqual(sorted(results), [200, 409])
        # A separate recipient cannot concurrently accept invitations to two rooms.
        first = self.create_v3()['room']['id']
        second = self.create_v3()['room']['id']
        invitations = [self.invite_v3(room, target='outsider').json()['data']['id'] for room in (first, second)]
        ready = threading.Barrier(2)
        def accept_other_v3(invitation):
            ready.wait(5)
            return self.chat_request_v3('POST', '/party-invitations/' + invitation + '/accept', user='outsider').status_code
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(accept_other_v3, invitations))
        self.assertEqual(sorted(results), [200, 409])

    def test_block_report_moderation_and_read_while_restricted_v3(self):
        message = self.chat_send_v3(user='member')['message_id']
        member_id = str(self.ids_v3['member'])
        self.assertEqual(self.chat_request_v3('POST', '/chat/blocks/' + str(self.ids_v3['owner'])).status_code, 422)
        self.chat_request_v3('POST', '/chat/blocks/' + member_id)
        self.assertEqual(self.chat_request_v3('GET', '/chat/messages?channel=lobby').json()['data']['messages'], [])
        self.assertEqual(len(self.chat_request_v3('GET', '/chat/messages?channel=lobby', user='member').json()['data']['messages']), 1)
        with self.sessions_v3.begin() as session:
            service = ChatServiceV3(session)
            self.assertIsNone(service.forward_v3(service.identity_v3('owner@example.test'), event_v3('chat_message', {'message_id': message})))
        self.chat_request_v3('DELETE', '/chat/blocks/' + member_id)
        report_path = '/chat/messages/' + message + '/report'
        self.assertEqual(self.chat_request_v3('POST', report_path, json={'reason': 'spam'}).status_code, 201)
        self.assertEqual(self.chat_request_v3('POST', report_path, json={'reason': 'spam'}).status_code, 409)
        self.assertEqual(self.chat_request_v3('GET', '/chat/admin/reports', user='member').status_code, 403)
        self.assertEqual(len(self.chat_request_v3('GET', '/chat/admin/reports').json()['data']), 1)
        path = '/chat/admin/restrictions/' + member_id
        self.assertEqual(self.chat_request_v3('PUT', path, json={'reason': 'spam'}).status_code, 200)
        with self.assertRaises(HTTPException) as error:
            self.chat_send_v3(user='member', message='restricted')
        self.assertEqual(error.exception.detail, 'CHAT_RESTRICTED')
        self.assertEqual(self.chat_request_v3('GET', '/chat/messages?channel=lobby', user='member').status_code, 200)
        self.chat_request_v3('DELETE', path)
        self.chat_send_v3(user='member', message='unrestricted')
        self.assertEqual(self.chat_request_v3('DELETE', '/chat/admin/messages/' + message).status_code, 200)
        with self.sessions_v3() as session:
            self.assertEqual(session.get(ChatMessageV3, UUID(message)).message, '')

    def test_websocket_delivery_ack_reconnect_invite_state_and_deletion_v3(self):
        room_id = self.create_v3()['room']['id']
        with self.chat_socket_v3() as owner, self.chat_socket_v3('member') as member:
            self.snapshot_v3(owner)
            self.snapshot_v3(member)
            request_id = str(uuid4())
            packet = {'type': 'send_message', 'channel': 'lobby', 'message': 'socket hello', 'request_id': request_id}
            owner.send_json(packet)
            ack = self.receive_v3(owner, lambda e: e['type'] == 'message_ack')
            message = self.receive_v3(member, lambda e: e['type'] == 'chat_message')
            self.assertEqual(message['data']['id'], ack['data']['message_id'])
            owner.send_json(packet)
            self.assertTrue(self.receive_v3(owner, lambda e: e['type'] == 'message_ack')['data']['duplicate'])
            self.invite_v3(room_id)
            event = self.receive_v3(member, lambda e: e['type'] == 'party_invitation_created')
            self.assertEqual(event['data']['party']['id'], room_id)
            self.request_v3('PATCH', f'/{room_id}', json={'name': 'renamed'})
            self.receive_v3(member, lambda e: e['type'] == 'party_invitation_updated' and e['data']['party']['name'] == 'renamed')
            self.chat_request_v3('DELETE', '/chat/admin/messages/' + message['data']['id'])
            self.receive_v3(member, lambda e: e['type'] == 'message_deleted')
        with self.chat_socket_v3('member') as member:
            snapshot = self.snapshot_v3(member)['data']
            self.assertEqual(snapshot['lobby'], [])
            self.assertEqual(len(snapshot['party_invitations']), 1)

    def test_socket_auth_validation_and_redis_failure_v3(self):
        for name, msg in (('bad', 'INVALID_TOKEN'), ('unknown', 'REGISTERED_USER_REQUIRED')):
            with self.chat_socket_v3(name) as websocket:
                self.assertEqual(websocket.receive_json()['msg'], msg)
        with self.chat_socket_v3() as websocket:
            self.snapshot_v3(websocket)
            websocket.send_json({'type': 'send_message', 'channel': 'lobby', 'message': ' ', 'request_id': str(uuid4())})
            self.assertEqual(websocket.receive_json()['msg'], 'INVALID_MESSAGE')
        with patch.object(self.redis_v3, 'eval', side_effect=RedisConnectionError):
            with self.assertRaises(HTTPException) as error:
                self.chat_send_v3()
            self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(self.request_v3('GET').status_code, 200)

    def test_retention_and_idempotent_additive_migration_v3(self):
        room = self.create_v3()['room']['id']
        lobby = UUID(self.chat_send_v3()['message_id'])
        party = UUID(self.chat_send_v3(channel='party', room_id=UUID(room), message='party')['message_id'])
        from api.live_map.party_v3.models import PartyRoomV3
        with self.sessions_v3.begin() as session:
            session.get(ChatMessageV3, lobby).create_time = now_v3() - timedelta(days=8)
            session.get(PartyRoomV3, UUID(room)).closed_at = now_v3() - timedelta(hours=25)
        with self.sessions_v3.begin() as session:
            ChatServiceV3(session).cleanup_v3()
        with self.sessions_v3() as session:
            self.assertIsNone(session.get(ChatMessageV3, lobby))
            self.assertIsNone(session.get(ChatMessageV3, party))
            self.assertIsNotNone(session.get(PartyRoomV3, UUID(room)))
        migration = (Path(__file__).parents[1] / 'sql/migrations/20261003_live_map_chat_v3.sql').read_text()
        with self.engine_v3.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
            conn.exec_driver_sql(migration)
            conn.exec_driver_sql(migration)

    def test_post_commit_publish_failure_does_not_duplicate_messages_v3(self):
        with self.chat_socket_v3() as websocket:
            self.snapshot_v3(websocket)
            packet = {'type': 'send_message', 'channel': 'lobby', 'message': 'durable', 'request_id': str(uuid4())}
            with patch.object(self.chat_store_v3, 'publish_v3', side_effect=RedisConnectionError):
                websocket.send_json(packet)
                ack = self.receive_v3(websocket, lambda e: e['type'] == 'message_ack')['data']
                self.assertFalse(ack['realtime_available'])
            websocket.send_json(packet)
            self.assertTrue(self.receive_v3(websocket, lambda e: e['type'] == 'message_ack')['data']['duplicate'])
            websocket.send_json({'type': 'heartbeat'})
            self.assertEqual(self.snapshot_v3(websocket)['data']['lobby'][0]['message'], 'durable')
        with self.sessions_v3() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(ChatMessageV3)), 1)

    def test_openapi_and_missing_chat_schema_preserve_existing_party_v3(self):
        schema = self.app_v3.openapi()
        history = schema['paths']['/live-map/v3/chat/messages']['get']
        self.assertIn('$ref', history['responses']['200']['content']['application/json']['schema'])
        # A missing chat table must not break the existing party endpoints.
        with self.engine_v3.begin() as conn:
            conn.exec_driver_sql('ALTER TABLE live_map_chat_messages_v3 RENAME TO hidden_chat_messages_v3')
        try:
            room_id = self.create_v3()['room']['id']
            self.assertEqual(self.join_v3(room_id).status_code, 200)
            self.assertEqual(self.marker_v3(room_id).status_code, 201)
            self.assertEqual(self.chat_request_v3('GET', '/chat/messages?channel=lobby').status_code, 503)
            self.assertEqual(self.request_v3('GET').status_code, 200)
        finally:
            with self.engine_v3.begin() as conn:
                conn.exec_driver_sql('ALTER TABLE hidden_chat_messages_v3 RENAME TO live_map_chat_messages_v3')

    def test_socket_party_switch_and_leave_revokes_sending_v3(self):
        room_id = self.create_v3()['room']['id']
        invitation = self.invite_v3(room_id).json()['data']['id']
        with self.chat_socket_v3('member') as websocket:
            self.assertIsNone(self.snapshot_v3(websocket)['data']['party_room_id'])
            self.chat_request_v3('POST', '/party-invitations/' + invitation + '/accept', user='member')
            self.snapshot_v3(websocket, lambda e: e['data']['party_room_id'] == room_id)
            websocket.send_json({'type': 'send_message', 'channel': 'party', 'room_id': room_id,
                                 'message': 'joined', 'request_id': str(uuid4())})
            self.receive_v3(websocket, lambda e: e['type'] == 'message_ack')
            self.request_v3('POST', f'/{room_id}/leave', user='member')
            websocket.send_json({'type': 'send_message', 'channel': 'party', 'room_id': room_id,
                                 'message': 'left', 'request_id': str(uuid4())})
            self.receive_v3(websocket, lambda e: e['type'] == 'error' and e['msg'] == 'PARTY_MEMBERSHIP_REQUIRED')
            self.snapshot_v3(websocket, lambda e: e['data']['party_room_id'] is None)

    def test_invitation_cleanup_persists_terminal_state_v3(self):
        room_id = self.create_v3(max_members=2)['room']['id']
        invitation = self.invite_v3(room_id).json()['data']['id']
        self.join_v3(room_id, user='other')
        with self.sessions_v3.begin() as session:
            ChatServiceV3(session).reconcile_batch_v3()
        self.request_v3('POST', f'/{room_id}/leave', user='other')
        with self.sessions_v3() as session:
            self.assertEqual(session.get(PartyInvitationV3, UUID(invitation)).status, 'revoked')
        self.assertEqual(self.chat_request_v3('POST', '/party-invitations/' + invitation + '/accept', user='member').status_code, 409)

    def test_connection_lease_limit_and_release_v3(self):
        user_id = str(self.ids_v3['owner'])
        for index in range(5):
            self.chat_store_v3.lease_v3(user_id, str(index))
        self.chat_store_v3.lease_v3(user_id, '0')
        with self.assertRaises(HTTPException) as error:
            self.chat_store_v3.lease_v3(user_id, 'sixth')
        self.assertEqual(error.exception.detail, 'CHAT_CONNECTION_LIMIT')
        self.chat_store_v3.disconnect_v3(user_id, '0')
        self.chat_store_v3.lease_v3(user_id, 'sixth')
        self.assertLessEqual(self.redis_v3.ttl('live-map:chat:v3:connections:' + user_id), 90)


class ChatLifecycleTestV3(unittest.IsolatedAsyncioTestCase):
    async def test_cleanup_starts_and_stops_with_application_v3(self):
        from api.live_map.chat_v3.lifecycle import chat_lifespan_v3

        started = asyncio.Event()
        stopped = asyncio.Event()

        async def cleanup_v3():
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()

        with patch('api.live_map.chat_v3.lifecycle.chat_cleanup_loop_v3', side_effect=cleanup_v3):
            async with chat_lifespan_v3(None):
                await asyncio.wait_for(started.wait(), timeout=1)
                self.assertFalse(stopped.is_set())
            self.assertTrue(stopped.is_set())
