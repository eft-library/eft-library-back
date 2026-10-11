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

from fastapi import HTTPException, Request
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import func, select

from api.live_map.chat_v3.models import ChatConnectionV3, ChatMessageV3, ChatUserV3, PartyInvitationV3
from api.live_map.chat_v3.router import router_v3
from api.live_map.chat_v3.schemas import ChatSendV3
from api.live_map.chat_v3.security import optional_chat_user_v3
from api.live_map.chat_v3.service import ChatServiceV3, event_v3, now_v3
from api.live_map.chat_v3.store import ChatStoreV3
from api.live_map.party_v3.models import PartyRoomV3
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
        def optional_identity_v3(request: Request):
            user = request.headers.get('x-test-user')
            return user + '@example.test' if user else None
        self.app_v3.dependency_overrides[optional_chat_user_v3] = optional_identity_v3
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
        for user, status in ((None, 200), ('unknown', 403)):
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
        self.assertEqual(self.invite_v3(room_id).json()['msg'], 'PARTY_INVITATION_REJECT_COOLDOWN')
        with self.sessions_v3.begin() as session:
            rejected = session.get(PartyInvitationV3, UUID(invitation))
            rejected.update_time = rejected.create_time = now_v3() - timedelta(minutes=11)
        invitation = self.invite_v3(room_id).json()['data']['id']
        self.assertEqual(self.chat_request_v3('DELETE', '/party-invitations/' + invitation, user='outsider').status_code, 403)
        revoked = self.chat_request_v3('DELETE', '/party-invitations/' + invitation)
        self.assertEqual(revoked.status_code, 200)
        self.assertEqual(revoked.json()['data']['status_reason'], 'cancelled')
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
        second = self.create_v3(user='other')['room']['id']
        invitations = [self.invite_v3(first, target='outsider').json()['data']['id'],
                       self.invite_v3(second, target='outsider', user='other').json()['data']['id']]
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
            session.get(ChatMessageV3, lobby).create_time = now_v3() - timedelta(hours=25)
            session.get(PartyRoomV3, UUID(room)).closed_at = now_v3() - timedelta(hours=25)
        with self.sessions_v3.begin() as session:
            ChatServiceV3(session).cleanup_v3()
        with self.sessions_v3() as session:
            self.assertIsNone(session.get(ChatMessageV3, lobby))
            self.assertIsNone(session.get(ChatMessageV3, party))
            self.assertIsNotNone(session.get(PartyRoomV3, UUID(room)))
        migration = (Path(__file__).parents[1] / 'sql/migrations/20261003_live_map_chat_v3.sql').read_text()
        reason_migration = (
            Path(__file__).parents[1] / 'sql/migrations/20261004_party_invitation_status_reason.sql'
        ).read_text()
        with self.engine_v3.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
            conn.exec_driver_sql(migration)
            conn.exec_driver_sql(migration)
            conn.exec_driver_sql(reason_migration)
            conn.exec_driver_sql(reason_migration)

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
            conn.exec_driver_sql('ALTER TABLE live_map_chat_messages RENAME TO hidden_chat_messages_v3')
        try:
            room_id = self.create_v3()['room']['id']
            self.assertEqual(self.join_v3(room_id).status_code, 200)
            self.assertEqual(self.marker_v3(room_id).status_code, 201)
            self.assertEqual(self.chat_request_v3('GET', '/chat/messages?channel=lobby').status_code, 503)
            self.assertEqual(self.request_v3('GET').status_code, 200)
        finally:
            with self.engine_v3.begin() as conn:
                conn.exec_driver_sql('ALTER TABLE hidden_chat_messages_v3 RENAME TO live_map_chat_messages')

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
            row = session.get(PartyInvitationV3, UUID(invitation))
            self.assertEqual(row.status, 'revoked')
            self.assertEqual(row.status_reason, 'room_full')
        self.assertEqual(self.chat_request_v3('POST', '/party-invitations/' + invitation + '/accept', user='member').status_code, 409)

    def test_invitation_status_reasons_cover_room_and_member_changes_v3(self):
        cases = []
        for action in ('close', 'kick', 'join'):
            room_id = self.create_v3()['room']['id']
            invitation_id = self.invite_v3(room_id).json()['data']['id']
            if action == 'close':
                self.request_v3('DELETE', f'/{room_id}')
                expected = 'room_closed'
            elif action == 'kick':
                member_id = self.join_v3(room_id, user='member').json()['data']['me']['id']
                self.request_v3('POST', f'/{room_id}/members/{member_id}/kick')
                expected = 'member_kicked'
            else:
                other_room = self.create_v3(user='other')['room']['id']
                self.join_v3(other_room, user='member')
                expected = 'already_joined'
            cases.append((UUID(room_id), UUID(invitation_id), expected))

        with self.sessions_v3.begin() as session:
            service = ChatServiceV3(session)
            for room_id, _, _ in cases:
                room = session.get(PartyRoomV3, room_id)
                service.reconcile_room_v3(room)

        with self.sessions_v3() as session:
            for _, invitation_id, expected in cases:
                invitation = session.get(PartyInvitationV3, invitation_id)
                self.assertEqual(invitation.status, 'revoked')
                self.assertEqual(invitation.status_reason, expected)

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


    def test_migration_renames_existing_tables_preserving_data_v3(self):
        message_id = UUID(self.chat_send_v3()['message_id'])
        names = ('live_map_chat_users', 'live_map_chat_messages', 'live_map_chat_blocks',
                 'live_map_chat_reports', 'live_map_chat_restrictions', 'live_map_party_invitations')
        migration = (Path(__file__).parents[1] / 'sql/migrations/20261003_live_map_chat_v3.sql').read_text()
        rename = (Path(__file__).parents[1] / 'sql/migrations/20261004_rename_chat_objects.sql').read_text()
        with self.engine_v3.begin() as conn:
            for name in names:
                constraints = conn.exec_driver_sql(
                    f"SELECT conname FROM pg_constraint WHERE conrelid = '{name}'::regclass"
                ).scalars().all()
                for constraint in constraints:
                    old_name = constraint.replace(name, name + '_v3', 1)
                    if old_name != constraint:
                        conn.exec_driver_sql(
                            f'ALTER TABLE {name} RENAME CONSTRAINT {constraint} TO {old_name}')
                indexes = conn.exec_driver_sql(
                    f"SELECT indexname FROM pg_indexes WHERE tablename = '{name}'"
                ).scalars().all()
                for index in indexes:
                    if '_v3' not in index:
                        prefix, suffix = index.rsplit('_', 1)
                        conn.exec_driver_sql(f'ALTER INDEX {index} RENAME TO {prefix}_v3_{suffix}')
                conn.exec_driver_sql(f'ALTER TABLE {name} RENAME TO {name}_v3')
        with self.engine_v3.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
            conn.exec_driver_sql(rename)
            conn.exec_driver_sql(rename)
            conn.exec_driver_sql(migration)
            for name in names:
                self.assertIsNone(conn.exec_driver_sql(f"SELECT to_regclass('{name}_v3')").scalar())
                indexes = conn.exec_driver_sql(
                    f"SELECT indexname FROM pg_indexes WHERE tablename = '{name}'"
                ).scalars().all()
                self.assertTrue(indexes)
                self.assertTrue(all('_v3' not in index for index in indexes))
                constraints = conn.exec_driver_sql(
                    f"SELECT conname FROM pg_constraint WHERE conrelid = '{name}'::regclass"
                ).scalars().all()
                self.assertTrue(all('_v3' not in constraint for constraint in constraints))
        with self.sessions_v3() as session:
            self.assertEqual(session.get(ChatMessageV3, message_id).message, 'hello')
        self.assertEqual(self.chat_request_v3('POST', '/chat/messages/' + str(message_id) + '/report',
                                            json={'reason': 'spam'}).status_code, 201)

    def test_guest_history_is_lobby_only_and_mutations_require_login_v3(self):
        room_id = self.create_v3()['room']['id']
        self.chat_send_v3(message='public')
        private = self.chat_send_v3(channel='party', room_id=UUID(room_id), message='private')
        response = self.chat_request_v3('GET', '/chat/messages?channel=lobby', user=None)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m['message'] for m in response.json()['data']['messages']], ['public'])
        for room in (room_id, str(uuid4())):
            self.assertEqual(self.chat_request_v3('GET', '/chat/messages?channel=party&room_id=' + room,
                                                 user=None).status_code, 401)
        for method, path, body in (
            ('GET', '/party-invitations', None),
            ('POST', '/party-invitations', {'room_id': room_id, 'invitee_user_id': str(self.ids_v3['member'])}),
            ('POST', '/party-invitations/' + str(uuid4()) + '/accept', None),
            ('GET', '/chat/blocks', None),
            ('POST', '/chat/blocks/' + str(self.ids_v3['owner']), None),
            ('POST', '/chat/messages/' + private['message_id'] + '/report', {'reason': 'spam'}),
            ('GET', '/chat/admin/reports', None),
        ):
            self.assertEqual(self.chat_request_v3(method, path, user=None, json=body).status_code, 401)
        with self.sessions_v3.begin() as session:
            service = ChatServiceV3(session)
            self.assertIsNone(service.forward_v3(None, event_v3('chat_message', {'message_id': private['message_id']})))
            self.assertIsNone(service.forward_v3(None, event_v3('message_deleted', {'message_id': private['message_id']})))
            self.assertEqual(session.scalar(select(func.count()).select_from(ChatUserV3)), 4)

    def test_optional_auth_does_not_downgrade_invalid_credentials_v3(self):
        self.app_v3.dependency_overrides.pop(optional_chat_user_v3)
        self.assertEqual(self.chat_request_v3('GET', '/chat/messages?channel=lobby', user=None).status_code, 200)
        for header in ('Bearer', 'Basic abc', ''):
            response = self.client_v3.get('/live-map/v3/chat/messages?channel=lobby', headers={'Authorization': header})
            self.assertEqual(response.status_code, 401)
        with patch('api.live_map.chat_v3.security.authenticate_party_user_v3', side_effect=HTTPException(401, 'INVALID_TOKEN')):
            response = self.client_v3.get('/live-map/v3/chat/messages?channel=lobby', headers={'Authorization': 'Bearer bad'})
            self.assertEqual(response.status_code, 401)

    def test_guest_socket_snapshot_live_delivery_deletion_and_read_only_v3(self):
        room_id = self.create_v3()['room']['id']
        self.invite_v3(room_id)
        with self.client_v3.websocket_connect('/live-map/v3/chat/ws') as guest, self.chat_socket_v3() as owner:
            guest.send_json({'type': 'guest'})
            snapshot = self.snapshot_v3(guest)['data']
            self.assertIsNone(snapshot['user'])
            self.assertIsNone(snapshot['party_room_id'])
            self.assertEqual(snapshot['party'], [])
            self.assertEqual(snapshot['party_invitations'], [])
            self.snapshot_v3(owner)
            for channel, room, message in (('party', room_id, 'private'), ('lobby', None, 'public')):
                owner.send_json({'type': 'send_message', 'channel': channel, 'room_id': room,
                                 'message': message, 'request_id': str(uuid4())})
                self.receive_v3(owner, lambda e: e['type'] == 'message_ack')
            received = self.receive_v3(guest, lambda e: e['type'] == 'chat_message')['data']
            self.assertEqual(received['message'], 'public')
            for channel, room in (('lobby', None), ('party', room_id)):
                request_id = str(uuid4())
                guest.send_json({'type': 'send_message', 'channel': channel, 'room_id': room,
                                 'message': 'forbidden', 'request_id': request_id})
                error = self.receive_v3(
                    guest, lambda e: e['type'] == 'error' and e['msg'] == 'LOGIN_REQUIRED')
                self.assertEqual(error['request_id'], request_id)
            guest.send_json({'type': 'heartbeat'})
            self.assertEqual(len(self.snapshot_v3(guest)['data']['lobby']), 1)
            self.chat_request_v3('DELETE', '/chat/admin/messages/' + received['id'])
            self.receive_v3(guest, lambda e: e['type'] == 'message_deleted')
        with self.sessions_v3() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(ChatMessageV3)), 2)
            self.assertEqual(session.scalar(select(func.count()).select_from(ChatUserV3)), 4)


    def test_lobby_retention_boundary_applies_to_reads_events_and_cleanup_v3(self):
        reference = now_v3()
        ids = [UUID(self.chat_send_v3(message=f'age {index}')['message_id']) for index in range(3)]
        with self.sessions_v3.begin() as session:
            for message_id, age in zip(ids, (timedelta(hours=24, seconds=1),
                                            timedelta(hours=24), timedelta(hours=24) - timedelta(seconds=1))):
                session.get(ChatMessageV3, message_id).create_time = reference - age
        with patch('api.live_map.chat_v3.service.now_v3', return_value=reference):
            for user in (None, 'owner'):
                response = self.chat_request_v3('GET', '/chat/messages?channel=lobby', user=user)
                self.assertEqual([m['id'] for m in response.json()['data']['messages']], [str(ids[2])])
            with self.sessions_v3.begin() as session:
                service = ChatServiceV3(session)
                self.assertEqual([m['id'] for m in service.snapshot_v3(None)['lobby']], [str(ids[2])])
                for message_id in ids[:2]:
                    self.assertIsNone(service.forward_v3(None, event_v3('chat_message', {'message_id': str(message_id)})))
                self.assertIsNotNone(service.forward_v3(None, event_v3('chat_message', {'message_id': str(ids[2])})))
                service.cleanup_v3()
            with self.sessions_v3() as session:
                self.assertEqual(list(session.scalars(select(ChatMessageV3.id))), [ids[2]])


    def test_party_repetition_allowed_with_cross_channel_and_rate_limits_v3(self):
        room_id = UUID(self.create_v3()['room']['id'])
        first = self.chat_send_v3(channel='party', room_id=room_id, message='네')
        second = self.chat_send_v3(channel='party', room_id=room_id, message='네')
        self.assertNotEqual(first['message_id'], second['message_id'])
        self.chat_send_v3(message='네')  # Party history must not block lobby.
        self.chat_send_v3(channel='party', room_id=room_id, message='네')
        self.chat_send_v3(channel='party', room_id=room_id, message='네')
        with self.assertRaises(HTTPException) as error:
            self.chat_send_v3(channel='party', room_id=room_id, message='네')
        self.assertEqual(error.exception.detail, 'CHAT_RATE_LIMITED')
        self.redis_v3.flushdb()
        with self.assertRaises(HTTPException) as error:
            self.chat_send_v3(message='  네  ')
        self.assertEqual(error.exception.detail, 'CHAT_REPEATED_MESSAGE')
        request_id = uuid4()
        sent = self.chat_send_v3(channel='party', room_id=room_id, message='네', request_id=request_id)
        duplicate = self.chat_send_v3(channel='party', room_id=room_id, message='네', request_id=request_id)
        self.assertTrue(duplicate['duplicate'])
        self.assertEqual(sent['message_id'], duplicate['message_id'])

    def test_moderation_list_state_expiry_and_permissions_v3(self):
        target = str(self.ids_v3['member'])
        path = '/chat/admin/restrictions/' + target
        self.assertEqual(self.chat_request_v3('GET', '/chat/admin/restrictions', user='member').status_code, 403)
        self.assertEqual(self.chat_request_v3('PUT', path, user='member', json={'reason': 'spam'}).status_code, 403)
        self.assertEqual(self.chat_request_v3('PUT', path, json={'reason': 'spam'}).status_code, 200)
        state = self.chat_request_v3('GET', '/chat/me/moderation', user='member').json()['data']
        self.assertEqual(state, {'is_admin': False, 'restricted': True, 'reason': 'spam', 'expires_at': None})
        rows = self.chat_request_v3('GET', '/chat/admin/restrictions').json()['data']
        self.assertEqual(rows[0]['user']['id'], target)
        self.assertNotIn('email', str(rows))
        with self.assertRaises(HTTPException) as error:
            self.chat_send_v3(user='member')
        self.assertEqual(error.exception.detail, 'CHAT_RESTRICTED')
        from api.live_map.chat_v3.models import ChatRestrictionV3
        with self.sessions_v3.begin() as session:
            session.get(ChatRestrictionV3, self.ids_v3['member']).expires_at = now_v3() - timedelta(seconds=1)
        self.assertFalse(self.chat_request_v3('GET', '/chat/me/moderation', user='member').json()['data']['restricted'])
        self.assertEqual(self.chat_request_v3('GET', '/chat/admin/restrictions').json()['data'], [])
        self.assertEqual(self.chat_request_v3('DELETE', path).status_code, 200)
        self.chat_send_v3(user='member')

    def test_party_badge_counts_incoming_effective_invitations_only_v3(self):
        room_id = self.create_v3(max_members=2)['room']['id']
        invitation = self.invite_v3(room_id).json()['data']
        self.assertEqual(invitation['notification_tab'], 'party')
        path = '/party-invitations/notifications'
        self.assertEqual(self.chat_request_v3('GET', path, user=None).status_code, 401)
        for name, count in (('owner', 0), ('member', 1), ('outsider', 0)):
            data = self.chat_request_v3('GET', path, user=name).json()['data']
            self.assertEqual(data, {'party_invitation_count': count, 'notification_tab': 'party'})
        self.join_v3(room_id, user='other')
        self.assertEqual(self.chat_request_v3('GET', path, user='member').json()['data']['party_invitation_count'], 0)
        with self.sessions_v3.begin() as session:
            service = ChatServiceV3(session)
            self.assertEqual(service.snapshot_v3(None)['notifications']['party_invitation_count'], 0)

    def test_nickname_actions_kick_reinvite_and_owner_privacy_v3(self):
        room_id = self.create_v3()['room']['id']
        target = str(self.ids_v3['member'])
        path = '/chat/users/' + target + '/actions'
        self.assertEqual(self.chat_request_v3('GET', path, user=None).status_code, 401)
        data = self.chat_request_v3('GET', path, params={'room_id': room_id}).json()['data']
        self.assertTrue(data['can_invite'])
        self.assertTrue(data['can_restrict'])
        self.assertFalse(data['can_unkick'])
        self.assertEqual(self.chat_request_v3('GET', path, user='outsider', params={'room_id': room_id}).status_code, 403)
        old_id = self.invite_v3(room_id).json()['data']['id']
        self.assertEqual(self.chat_request_v3('GET', path, params={'room_id': room_id}).json()['data']['invite_disabled_reason'], 'PARTY_INVITATION_DUPLICATED')
        member_id = self.join_v3(room_id).json()['data']['me']['id']
        kick_path = f'/{room_id}/members/{member_id}/kick'
        self.request_v3('POST', kick_path)
        data = self.chat_request_v3('GET', path, params={'room_id': room_id}).json()['data']
        self.assertEqual(data['member_id'], member_id)
        self.assertTrue(data['can_unkick'])
        self.assertEqual(data['invite_disabled_reason'], 'PARTY_MEMBER_KICKED')
        self.assertEqual(self.request_v3('DELETE', kick_path).status_code, 200)
        # The old pending invitation must not revive after an intervening join/kick.
        self.assertEqual(self.chat_request_v3('GET', '/party-invitations', user='member').json()['data'], [])
        data = self.chat_request_v3('GET', path, params={'room_id': room_id}).json()['data']
        self.assertTrue(data['can_invite'])
        self.assertFalse(data['can_unkick'])
        self.assertEqual(self.chat_request_v3('POST', '/party-invitations/' + old_id + '/accept', user='member').status_code, 409)
        reinvited = self.invite_v3(room_id)
        self.assertEqual(reinvited.status_code, 201)
        self.assertEqual(self.chat_request_v3('POST', '/party-invitations/' + reinvited.json()['data']['id'] + '/accept', user='member').status_code, 200)
        self.chat_request_v3('POST', '/chat/blocks/' + target)
        self.assertTrue(self.chat_request_v3('GET', path).json()['data']['blocked'])

    def test_socket_party_badge_and_moderation_updates_v3(self):
        room_id = self.create_v3()['room']['id']
        with self.chat_socket_v3('member') as websocket:
            snapshot = self.snapshot_v3(websocket)['data']
            self.assertEqual(snapshot['notifications']['party_invitation_count'], 0)
            self.assertFalse(snapshot['moderation']['restricted'])
            invitation = self.invite_v3(room_id).json()['data']['id']
            updated = self.receive_v3(websocket, lambda e: e['type'] == 'party_notifications_updated')
            self.assertEqual(updated['data']['party_invitation_count'], 1)
            self.chat_request_v3('POST', '/party-invitations/' + invitation + '/reject', user='member')
            updated = self.receive_v3(websocket, lambda e: e['type'] == 'party_notifications_updated')
            self.assertEqual(updated['data']['party_invitation_count'], 0)
            path = '/chat/admin/restrictions/' + str(self.ids_v3['member'])
            self.chat_request_v3('PUT', path, json={'reason': 'spam'})
            self.assertTrue(self.receive_v3(websocket, lambda e: e['type'] == 'chat_moderation_updated')['data']['restricted'])
            self.chat_request_v3('DELETE', path)
            self.assertFalse(self.receive_v3(websocket, lambda e: e['type'] == 'chat_moderation_updated')['data']['restricted'])

    def test_online_users_deduplicate_expire_and_preserve_privacy_v3(self):
        user_id = str(self.ids_v3['owner'])
        store = self.chat_store_v3
        store.lease_v3(user_id, 'tab-a')
        store.lease_v3(user_id, 'tab-b')
        store.lease_v3('guest:anonymous', 'guest-tab')
        response = self.chat_request_v3('GET', '/chat/online-users', user=None)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'private, no-store')
        users = response.json()['data']
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]['id'], user_id)
        self.assertEqual(set(users[0]), {'id', 'nickname'})
        store.disconnect_v3(user_id, 'tab-a')
        self.assertEqual(store.online_user_ids_v3(), [user_id])
        store.disconnect_v3(user_id, 'tab-b')
        self.assertEqual(store.online_user_ids_v3(), [])
        store.lease_v3(user_id, 'crashed-tab')
        self.redis_v3.zadd(store.presence_key_v3, {user_id + '/crashed-tab': 0})
        self.assertEqual(self.chat_request_v3('GET', '/chat/online-users').json()['data'], [])
        with patch.object(self.redis_v3, 'eval', side_effect=RedisConnectionError):
            self.assertEqual(self.chat_request_v3('GET', '/chat/online-users').status_code, 503)

    def test_online_users_socket_snapshot_and_updates_v3(self):
        with self.client_v3.websocket_connect('/live-map/v3/chat/ws') as guest:
            guest.send_json({'type': 'guest'})
            self.assertEqual(self.snapshot_v3(guest)['data']['online_users'], [])
            with self.chat_socket_v3() as owner:
                users = self.snapshot_v3(owner)['data']['online_users']
                self.assertEqual([row['id'] for row in users], [str(self.ids_v3['owner'])])
                while True:
                    event = guest.receive_json()
                    if event['type'] == 'online_users_updated':
                        self.assertEqual(event['data'], users)
                        break
            while True:
                event = guest.receive_json()
                if event['type'] == 'online_users_updated':
                    self.assertEqual(event['data'], [])
                    break


    def test_connection_history_tracks_heartbeat_tabs_and_close_v3(self):
        path = '/chat/admin/connections'
        self.assertEqual(self.chat_request_v3('GET', path, user='member').status_code, 403)
        with self.chat_socket_v3() as first, self.chat_socket_v3() as second:
            self.snapshot_v3(first)
            self.snapshot_v3(second)
            active = self.chat_request_v3('GET', path, params={'online_only': True}).json()['data']
            self.assertEqual(len(active), 2)
            self.assertEqual({row['user']['id'] for row in active}, {str(self.ids_v3['owner'])})
            self.assertNotIn('email', str(active))
            self.assertTrue(all(row['online'] for row in active))
            previous = {row['id']: row['last_seen_at'] for row in active}
            first.send_json({'type': 'heartbeat'})
            self.snapshot_v3(first)
        history = self.chat_request_v3('GET', path).json()['data']
        self.assertEqual(len(history), 2)
        self.assertTrue(all(not row['online'] and row['disconnect_reason'] == 'closed' for row in history))
        self.assertTrue(any(row['last_seen_at'] > previous[row['id']] for row in history))
        self.assertEqual(self.chat_request_v3('GET', path, params={'online_only': True}).json()['data'], [])
        self.assertEqual(len(self.chat_request_v3('GET', path, params={'limit': 1}).json()['data']), 1)

    def test_connection_expiry_and_migration_idempotency_v3(self):
        connection_id = str(uuid4())
        with self.sessions_v3.begin() as session:
            service = ChatServiceV3(session)
            service.connect_session_v3(service.identity_v3('member@example.test'), connection_id)
        with self.sessions_v3.begin() as session:
            row = session.get(ChatConnectionV3, UUID(connection_id))
            row.connected_at = now_v3() - timedelta(minutes=3)
            row.last_seen_at = now_v3() - timedelta(minutes=2)
            row.expires_at = now_v3() - timedelta(seconds=30)
        self.assertEqual(self.chat_request_v3('GET', '/chat/admin/connections?online_only=true').json()['data'], [])
        with self.sessions_v3.begin() as session:
            service = ChatServiceV3(session)
            service.touch_session_v3(service.identity_v3('member@example.test'), connection_id)
            service.expire_sessions_v3()
        history = self.chat_request_v3('GET', '/chat/admin/connections').json()['data']
        self.assertEqual(history[0]['disconnect_reason'], 'expired')
        self.assertFalse(history[0]['online'])
        migration = (Path(__file__).parents[1] / 'sql/migrations/20261009_chat_connections_v3.sql').read_text()
        with self.engine_v3.connect() as connection:
            for _ in range(2):
                connection.exec_driver_sql(migration)
                connection.commit()
        self.assertEqual(len(self.chat_request_v3('GET', '/chat/admin/connections').json()['data']), 1)


    def test_invite_preferences_default_validation_cancel_and_reenable_v3(self):
        path = '/chat/me/party-invite-preferences'
        self.assertEqual(self.chat_request_v3('GET', path, user=None).status_code, 401)
        self.assertEqual(self.chat_request_v3('PUT', path, user=None, json={'allow_party_invites': False}).status_code, 401)
        self.assertEqual(self.chat_request_v3('GET', path, user='member').json()['data'], {'allow_party_invites': True})
        for body in ({}, {'allow_party_invites': 'false'}, {'allow_party_invites': 0},
                     {'allow_party_invites': False, 'user_id': str(self.ids_v3['owner'])}):
            self.assertEqual(self.chat_request_v3('PUT', path, user='member', json=body).status_code, 422)
        first = self.create_v3()['room']['id']
        second = self.create_v3(user='other')['room']['id']
        ids = [self.invite_v3(first).json()['data']['id'],
               self.invite_v3(second, user='other').json()['data']['id']]
        self.assertEqual(self.chat_request_v3('GET', '/party-invitations/notifications', user='member').json()['data']['party_invitation_count'], 2)
        self.chat_store_v3.lease_v3(str(self.ids_v3['member']), 'online-tab')
        response = self.chat_request_v3('PUT', path, user='member', json={'allow_party_invites': False})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['data'], {'allow_party_invites': False})
        with self.sessions_v3() as session:
            for invitation_id in ids:
                row = session.get(PartyInvitationV3, UUID(invitation_id))
                self.assertEqual((row.status, row.status_reason), ('revoked', 'receiver_unavailable'))
        self.assertEqual(self.chat_request_v3('GET', '/party-invitations/notifications', user='member').json()['data']['party_invitation_count'], 0)
        self.assertEqual([u['id'] for u in self.chat_request_v3('GET', '/chat/online-users', user=None).json()['data']], [str(self.ids_v3['member'])])
        actions = self.chat_request_v3('GET', '/chat/users/' + str(self.ids_v3['member']) + '/actions', params={'room_id': first}).json()['data']
        self.assertFalse(actions['can_invite'])
        self.assertEqual(actions['invite_disabled_reason'], 'PARTY_INVITATIONS_UNAVAILABLE')
        self.assertEqual(self.invite_v3(first).json()['msg'], 'PARTY_INVITATIONS_UNAVAILABLE')
        self.chat_request_v3('PUT', path, user='member', json={'allow_party_invites': True})
        self.assertEqual(self.chat_request_v3('GET', '/party-invitations', user='member').json()['data'], [])
        self.assertEqual(self.invite_v3(first).status_code, 201)

    def test_invite_reverse_block_is_private_and_sender_block_is_directional_v3(self):
        room_id = self.create_v3()['room']['id']
        path = '/chat/users/' + str(self.ids_v3['member']) + '/actions'
        self.chat_request_v3('POST', '/chat/blocks/' + str(self.ids_v3['owner']), user='member')
        denied = self.invite_v3(room_id)
        self.assertEqual((denied.status_code, denied.json()['msg']), (403, 'PARTY_INVITATIONS_UNAVAILABLE'))
        actions = self.chat_request_v3('GET', path, params={'room_id': room_id}).json()['data']
        self.assertFalse(actions['blocked'])  # Only the caller's own block relationship is exposed.
        self.assertFalse(actions['can_invite'])
        self.assertEqual(actions['invite_disabled_reason'], denied.json()['msg'])
        self.chat_request_v3('DELETE', '/chat/blocks/' + str(self.ids_v3['owner']), user='member')
        self.chat_request_v3('PUT', '/chat/me/party-invite-preferences', user='member', json={'allow_party_invites': False})
        self.assertEqual(self.invite_v3(room_id).json(), denied.json())
        self.chat_request_v3('PUT', '/chat/me/party-invite-preferences', user='member', json={'allow_party_invites': True})
        self.chat_request_v3('POST', '/chat/blocks/' + str(self.ids_v3['member']))
        self.assertEqual(self.invite_v3(room_id).status_code, 201)

    def test_invite_rejection_cooldown_shared_across_rooms_and_senders_v3(self):
        first = self.create_v3()['room']['id']
        second = self.create_v3()['room']['id']
        invitation_id = self.invite_v3(first).json()['data']['id']
        self.chat_request_v3('POST', '/party-invitations/' + invitation_id + '/reject', user='member')
        denied = self.invite_v3(second)
        self.assertEqual((denied.status_code, denied.json()['msg']), (429, 'PARTY_INVITATION_REJECT_COOLDOWN'))
        retry = denied.json()['data']['retry_after']
        self.assertTrue(1 <= retry <= 600)
        self.assertEqual(int(denied.headers['Retry-After']), retry)
        actions = self.chat_request_v3('GET', '/chat/users/' + str(self.ids_v3['member']) + '/actions', params={'room_id': second}).json()['data']
        self.assertFalse(actions['can_invite'])
        self.assertEqual(actions['invite_disabled_reason'], 'PARTY_INVITATION_REJECT_COOLDOWN')
        self.assertTrue(1 <= actions['retry_after'] <= 600)
        other = self.create_v3(user='other')['room']['id']
        self.assertEqual(self.invite_v3(other, user='other').status_code, 201)
        with self.sessions_v3.begin() as session:
            session.get(PartyInvitationV3, UUID(invitation_id)).update_time = now_v3() - timedelta(seconds=601)
        self.assertEqual(self.invite_v3(second).status_code, 201)

    def test_invite_sender_sliding_limit_and_failed_attempts_v3(self):
        room_id = self.create_v3()['room']['id']
        ids = []
        for target in ('member', 'other', 'outsider'):
            result = self.invite_v3(room_id, target=target)
            self.assertEqual(result.status_code, 201, result.text)
            ids.append(result.json()['data']['id'])
        self.chat_request_v3('DELETE', '/party-invitations/' + ids[0])
        denied = self.invite_v3(room_id)
        self.assertEqual((denied.status_code, denied.json()['msg']), (429, 'PARTY_INVITATION_RATE_LIMITED'))
        self.assertTrue(1 <= denied.json()['data']['retry_after'] <= 60)
        actions = self.chat_request_v3('GET', '/chat/users/' + str(self.ids_v3['member']) + '/actions', params={'room_id': room_id}).json()['data']
        self.assertEqual(actions['invite_disabled_reason'], 'PARTY_INVITATION_RATE_LIMITED')
        with self.sessions_v3.begin() as session:
            session.get(PartyInvitationV3, UUID(ids[0])).create_time = now_v3() - timedelta(seconds=61)
        self.assertEqual(self.invite_v3(room_id).status_code, 201)

    def test_concurrent_invites_use_sender_lock_across_rooms_v3(self):
        # Four distinct targets and rooms; room locks alone cannot enforce sender quota.
        names = ['target-' + str(index) for index in range(4)]
        with self.sessions_v3.begin() as session:
            for name in names:
                session.add(UserV3(email=name + '@example.test', nickname=name, is_admin=False))
        for name in names:
            with self.sessions_v3.begin() as session:
                self.ids_v3[name] = ChatServiceV3(session).identity_v3(name + '@example.test').id
        rooms = [self.create_v3()['room']['id'] for _ in names]
        ready = threading.Barrier(4)
        def invite_concurrent_v3(index):
            ready.wait(5)
            response = self.invite_v3(rooms[index], target=names[index])
            return response.status_code, response.json()['msg']
        with ThreadPoolExecutor(4) as pool:
            results = list(pool.map(invite_concurrent_v3, range(4)))
        self.assertEqual(sorted(status for status, _ in results), [201, 201, 201, 429])
        self.assertEqual([msg for status, msg in results if status == 429], ['PARTY_INVITATION_RATE_LIMITED'])
        with self.sessions_v3() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(PartyInvitationV3)), 3)

    def test_concurrent_duplicate_invites_and_settings_disable_v3(self):
        rooms = [self.create_v3()['room']['id'] for _ in range(2)]
        ready = threading.Barrier(2)
        def invite_concurrent_v3(room_id):
            ready.wait(5)
            return self.invite_v3(room_id).status_code
        with ThreadPoolExecutor(2) as pool:
            self.assertEqual(sorted(pool.map(invite_concurrent_v3, rooms)), [201, 409])
        # Concurrent disable either rejects creation or revokes the just-created invite.
        ready = threading.Barrier(2)
        def race_v3(operation):
            ready.wait(5)
            if operation == 'disable':
                return self.chat_request_v3('PUT', '/chat/me/party-invite-preferences', user='other', json={'allow_party_invites': False}).status_code
            return self.invite_v3(rooms[0], target='other').status_code
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(race_v3, ['disable', 'invite']))
        self.assertEqual(results[0], 200)
        self.assertIn(results[1], [201, 403])
        with self.sessions_v3() as session:
            pending = session.scalar(select(func.count()).select_from(PartyInvitationV3).where(
                PartyInvitationV3.invitee_id == self.ids_v3['other'], PartyInvitationV3.status == 'pending'))
            self.assertEqual(pending, 0)

    def test_invite_preferences_other_tabs_events_and_privacy_v3(self):
        room_id = self.create_v3()['room']['id']
        with self.chat_socket_v3('member') as first, self.chat_socket_v3('member') as second, self.chat_socket_v3() as owner:
            self.assertEqual(self.snapshot_v3(first)['data']['party_invite_preferences'], {'allow_party_invites': True})
            self.snapshot_v3(second)
            self.snapshot_v3(owner)
            invitation_id = self.invite_v3(room_id).json()['data']['id']
            self.receive_v3(first, lambda e: e['type'] == 'party_invitation_created')
            self.receive_v3(second, lambda e: e['type'] == 'party_invitation_created')
            self.chat_request_v3('PUT', '/chat/me/party-invite-preferences', user='member', json={'allow_party_invites': False})
            for socket in (first, second):
                received = {}
                while len(received) < 3:
                    event = self.receive_v3(socket, lambda e: e['type'] in (
                        'party_invite_preferences_updated', 'party_invitation_updated', 'party_notifications_updated'))
                    if event['type'] == 'party_notifications_updated' and event['data']['party_invitation_count'] != 0:
                        continue
                    received[event['type']] = event['data']
                self.assertEqual(received['party_invite_preferences_updated'], {'allow_party_invites': False})
                revoked = received['party_invitation_updated']
                self.assertEqual(revoked['id'], invitation_id)
                self.assertEqual((revoked['status'], revoked['status_reason']), ('revoked', 'receiver_unavailable'))
            with self.sessions_v3.begin() as session:
                service = ChatServiceV3(session)
                event = event_v3('party_invite_preferences_updated', {'user_id': str(self.ids_v3['member'])})
                self.assertIsNone(service.forward_v3(None, event))
                self.assertIsNone(service.forward_v3(service.identity_v3('owner@example.test'), event))

    def test_invite_preferences_migration_is_repeatable_v3(self):
        self.chat_request_v3('PUT', '/chat/me/party-invite-preferences', user='member', json={'allow_party_invites': False})
        migration = (Path(__file__).parents[1] / 'sql/migrations/20261009_party_invite_preferences_v3.sql').read_text()
        with self.engine_v3.connect() as connection:
            for _ in range(2):
                connection.exec_driver_sql(migration)
                connection.commit()
        self.assertEqual(self.chat_request_v3('GET', '/chat/me/party-invite-preferences', user='member').json()['data'], {'allow_party_invites': False})


    def test_invite_creation_waits_for_concurrent_rejection_v3(self):
        first = self.create_v3()['room']['id']
        second = self.create_v3()['room']['id']
        invitation_id = self.invite_v3(first).json()['data']['id']
        started = threading.Event()
        finished = threading.Event()
        def create_while_rejecting_v3():
            started.set()
            response = self.invite_v3(second)
            finished.set()
            return response
        with ThreadPoolExecutor(1) as pool:
            with self.sessions_v3.begin() as session:
                service = ChatServiceV3(session)
                service.handle_invitation_v3(service.identity_v3('member@example.test'), UUID(invitation_id), 'reject')
                future = pool.submit(create_while_rejecting_v3)
                self.assertTrue(started.wait(2))
                self.assertFalse(finished.wait(0.1))
            response = future.result(timeout=5)
        self.assertEqual((response.status_code, response.json()['msg']), (429, 'PARTY_INVITATION_REJECT_COOLDOWN'))

    def test_invite_policy_configuration_and_failed_requests_do_not_consume_quota_v3(self):
        room_id = self.create_v3()['room']['id']
        with patch.dict('os.environ', {'V3_PARTY_INVITE_SENDER_LIMIT': '1',
                                     'V3_PARTY_INVITE_WINDOW_SECONDS': '5',
                                     'V3_PARTY_INVITE_REJECTION_COOLDOWN_SECONDS': '10'}):
            self.chat_request_v3('PUT', '/chat/me/party-invite-preferences', user='member', json={'allow_party_invites': False})
            for _ in range(4):
                self.assertEqual(self.invite_v3(room_id).status_code, 403)
            self.chat_request_v3('PUT', '/chat/me/party-invite-preferences', user='member', json={'allow_party_invites': True})
            invitation_id = self.invite_v3(room_id).json()['data']['id']
            self.chat_request_v3('DELETE', '/party-invitations/' + invitation_id)
            response = self.invite_v3(room_id, target='other')
            self.assertEqual(response.json()['msg'], 'PARTY_INVITATION_RATE_LIMITED')
            self.assertTrue(1 <= response.json()['data']['retry_after'] <= 5)
            with self.sessions_v3.begin() as session:
                session.get(PartyInvitationV3, UUID(invitation_id)).create_time = now_v3() - timedelta(seconds=6)
            invitation_id = self.invite_v3(room_id, target='other').json()['data']['id']
            self.chat_request_v3('POST', '/party-invitations/' + invitation_id + '/reject', user='other')
            response = self.invite_v3(room_id, target='other')
            self.assertEqual(response.json()['msg'], 'PARTY_INVITATION_REJECT_COOLDOWN')
            self.assertTrue(1 <= response.json()['data']['retry_after'] <= 10)


    def test_guest_session_isolation_validation_and_reuse_v3(self):
        import hashlib
        first = self.chat_request_v3('POST', '/chat/guest-session', user=None, json={})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.headers['cache-control'], 'no-store')
        token = first.json()['data']['guest_token']
        reused = self.chat_request_v3('POST', '/chat/guest-session', user=None,
                                     json={'guest_token': token}).json()['data']['guest_token']
        self.assertEqual(token, reused)
        identity = self.chat_store_v3.guest_identity_v3(token)
        for _ in range(20):
            self.chat_store_v3.consume_v3(identity, 'connect', 20)
        second = self.chat_request_v3('POST', '/chat/guest-session', user=None, json={}).json()['data']['guest_token']
        with self.client_v3.websocket_connect('/live-map/v3/chat/ws') as ws:
            ws.send_json({'type': 'guest', 'guest_token': second})
            self.assertEqual(self.snapshot_v3(ws)['type'], 'snapshot')
        with self.client_v3.websocket_connect('/live-map/v3/chat/ws') as ws:
            ws.send_json({'type': 'guest', 'guest_token': token})
            self.assertEqual(ws.receive_json()['msg'], 'CHAT_CONNECT_RATE_LIMITED')
        with self.client_v3.websocket_connect('/live-map/v3/chat/ws') as ws:
            ws.send_json({'type': 'guest', 'guest_token': 'invented'})
            self.assertEqual(ws.receive_json()['msg'], 'CHAT_GUEST_SESSION_INVALID')
        self.redis_v3.delete('live-map:chat:v3:guest-session:' + hashlib.sha256(second.encode()).hexdigest())
        with self.assertRaises(HTTPException) as expired:
            self.chat_store_v3.guest_identity_v3(second)
        self.assertEqual(expired.exception.status_code, 401)

    def test_guest_cookie_session_reuse_and_websocket_v3(self):
        from api.live_map.chat_v3.security import GUEST_COOKIE_NAME_V3
        first = self.chat_request_v3('POST', '/chat/guest-session', user=None, json={})
        token = first.json()['data']['guest_token']
        cookie = first.headers['set-cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('Secure', cookie)
        self.assertIn('SameSite=lax', cookie)
        self.assertIn('Path=/', cookie)
        self.assertNotIn('Domain=', cookie)
        headers = {'cookie': f'{GUEST_COOKIE_NAME_V3}={token}'}
        reused = self.client_v3.post('/live-map/v3/chat/guest-session', json={}, headers=headers)
        self.assertEqual(reused.json()['data']['guest_token'], token)
        with self.client_v3.websocket_connect('/live-map/v3/chat/ws', headers=headers) as ws:
            ws.send_json({'type': 'guest', 'session': 'cookie'})
            self.assertEqual(self.snapshot_v3(ws)['type'], 'snapshot')
        with self.client_v3.websocket_connect('/live-map/v3/chat/ws') as ws:
            ws.send_json({'type': 'guest', 'session': 'cookie'})
            self.assertEqual(ws.receive_json()['msg'], 'CHAT_GUEST_SESSION_INVALID')
        with self.client_v3.websocket_connect('/live-map/v3/chat/ws',
                headers={'cookie': f'{GUEST_COOKIE_NAME_V3}=invalid'}) as ws:
            ws.send_json({'type': 'guest', 'session': 'cookie'})
            self.assertEqual(ws.receive_json()['msg'], 'CHAT_GUEST_SESSION_INVALID')

    def test_guest_and_user_connection_rate_limit_has_distinct_code_v3(self):
        import hashlib
        guest_id = 'guest:' + hashlib.sha256(b'testclient').hexdigest()
        for identity in (guest_id, str(self.ids_v3['owner'])):
            for _ in range(20):
                self.chat_store_v3.consume_v3(identity, 'connect', 20)
        for auth in ({'type': 'guest'}, {'type': 'auth', 'token': 'owner'}):
            with self.client_v3.websocket_connect('/live-map/v3/chat/ws') as websocket:
                websocket.send_json(auth)
                error = websocket.receive_json()
                self.assertEqual((error['status'], error['msg']), (429, 'CHAT_CONNECT_RATE_LIMITED'))
                self.assertTrue(1 <= error['retry_after'] <= 60)
                self.assertEqual(websocket.receive()['code'], 4429)


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
