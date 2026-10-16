"""Isolated real Redis tests; never uses configured production Redis."""
import asyncio
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch

from fastapi import WebSocketDisconnect
from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from redis.exceptions import ConnectionError

from util.location_socket_v3 import (
    latest_key_v3, send_wpf_location_v3, send_wpf_log_location_v3,
    send_wpf_raid_state_v3, websocket_handler_v3,
)


class SocketV3:
    def __init__(self):
        self.out_v3 = asyncio.Queue()
        self.in_v3 = asyncio.Queue()
        self.closed_v3 = False
        self.fail_v3 = False

    async def accept(self):
        pass

    async def send_text(self, raw):
        if self.fail_v3:
            raise RuntimeError('closed socket')
        await self.out_v3.put(json.loads(raw))

    async def receive_text(self):
        packet = await self.in_v3.get()
        if packet is None:
            raise WebSocketDisconnect()
        return packet

    async def close(self, code):
        self.closed_v3 = True

    async def next_v3(self, kind):
        async with asyncio.timeout(5):
            while True:
                packet = await self.out_v3.get()
                if packet['type'] == kind:
                    return packet


@unittest.skipUnless(importlib.util.find_spec('redislite'), 'Install redislite for isolated Redis tests')
class LocationSocketTestV3(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        import redislite
        cls.root_v3 = tempfile.TemporaryDirectory()
        cls.server_v3 = redislite.Redis(cls.root_v3.name + '/redis.rdb')

    @classmethod
    def tearDownClass(cls):
        cls.server_v3.shutdown()
        cls.root_v3.cleanup()

    async def asyncSetUp(self):
        self.redis_v3 = Redis(unix_socket_path=self.server_v3.socket_file, decode_responses=True)
        await self.redis_v3.flushdb()
        self.patch_v3 = patch('util.location_socket_v3.get_location_redis_v3', return_value=self.redis_v3)
        self.patch_v3.start()
        self.tasks_v3 = []

    async def asyncTearDown(self):
        for task in self.tasks_v3:
            task.cancel()
        await asyncio.gather(*self.tasks_v3, return_exceptions=True)
        self.patch_v3.stop()
        await self.redis_v3.aclose()

    async def connect_v3(self, email='owner@test.invalid'):
        socket = SocketV3()
        task = asyncio.create_task(websocket_handler_v3(socket, email))
        self.tasks_v3.append(task)
        await socket.next_v3('init')
        await socket.next_v3('location_connection_status')
        return socket, task

    async def test_tabs_old_disconnect_and_user_isolation_v3(self):
        old, old_task = await self.connect_v3()
        new, _ = await self.connect_v3()
        other, _ = await self.connect_v3('other@test.invalid')
        event_id = await send_wpf_location_v3('owner@test.invalid', 'first', request_id=42)
        for socket in (old, new):
            event = await socket.next_v3('wpf_location')
            self.assertEqual(event['event_id'], event_id)
            self.assertEqual(event['request_id'], 42)
        self.assertTrue(other.out_v3.empty())
        await old.in_v3.put(None)
        await asyncio.wait_for(old_task, 3)
        await send_wpf_location_v3('owner@test.invalid', 'second')
        self.assertEqual((await new.next_v3('wpf_location'))['payload'], 'second')
        self.assertTrue(other.out_v3.empty())

    async def test_offline_replay_expiry_and_raid_end_v3(self):
        await send_wpf_location_v3('owner@test.invalid', 'latest')
        socket = SocketV3()
        task = asyncio.create_task(websocket_handler_v3(socket, 'owner@test.invalid'))
        self.tasks_v3.append(task)
        await socket.next_v3('init')
        replay = await socket.next_v3('wpf_location')
        self.assertTrue(replay['replayed'])
        self.assertEqual(replay['payload'], 'latest')
        self.assertTrue(0 < await self.redis_v3.ttl(latest_key_v3('owner@test.invalid')) <= 60)
        await socket.next_v3('location_connection_status')
        await send_wpf_raid_state_v3('owner@test.invalid', {'is_active': False})
        await socket.next_v3('wpf_raid_state')
        self.assertIsNone(await self.redis_v3.get(latest_key_v3('owner@test.invalid')))
        await send_wpf_log_location_v3('owner@test.invalid', {'x':1,'y':2,'z':3})
        self.assertEqual((await socket.next_v3('wpf_log_location'))['payload']['x'], 1)
        await self.redis_v3.pexpire(latest_key_v3('owner@test.invalid'), 1)
        await asyncio.sleep(.02)
        expired, _ = await self.connect_v3()
        self.assertTrue(expired.out_v3.empty())

    async def test_subscriber_retry_replays_latest_and_keeps_receiving_v3(self):
        socket, _ = await self.connect_v3()
        original = PubSub.get_message
        failed = False

        async def fail_once(pubsub, *args, **kwargs):
            nonlocal failed
            if not failed:
                failed = True
                raise ConnectionError('injected disconnect')
            return await original(pubsub, *args, **kwargs)

        patcher = patch.object(PubSub, 'get_message', fail_once)
        patcher.start()
        self.addCleanup(patcher.stop)
        status = await socket.next_v3('location_connection_status')
        self.assertEqual(status['status'], 'reconnecting')
        await send_wpf_location_v3('owner@test.invalid', 'during-recovery')
        replay = await socket.next_v3('wpf_location')
        self.assertEqual(replay['payload'], 'during-recovery')
        self.assertTrue(replay['replayed'])
        self.assertEqual((await socket.next_v3('location_connection_status'))['status'], 'ready')
        await send_wpf_location_v3('owner@test.invalid', 'after-recovery')
        self.assertEqual((await socket.next_v3('wpf_location'))['payload'], 'after-recovery')

    async def test_transparent_redis_reconnect_keeps_delivery_v3(self):
        socket, _ = await self.connect_v3()
        await self.redis_v3.connection_pool.disconnect(inuse_connections=True)
        status = await socket.next_v3('location_connection_status')
        self.assertIn(status['status'], ('ready', 'reconnecting'))
        if status['status'] == 'reconnecting':
            await socket.next_v3('location_connection_status')
        await send_wpf_location_v3('owner@test.invalid', 'after-transparent-reconnect')
        self.assertEqual((await socket.next_v3('wpf_location'))['payload'], 'after-transparent-reconnect')

    async def test_replay_order_duplicates_and_stale_raid_event_v3(self):
        await send_wpf_raid_state_v3('owner@test.invalid', {'is_active':True, 'map':'woods'})
        await send_wpf_location_v3('owner@test.invalid', 'newest')
        socket = SocketV3()
        task = asyncio.create_task(websocket_handler_v3(socket, 'owner@test.invalid'))
        self.tasks_v3.append(task)
        await socket.next_v3('init')
        state = await asyncio.wait_for(socket.out_v3.get(), 3)
        self.assertEqual(state['type'], 'wpf_raid_state')
        self.assertTrue(state['replayed'])
        location = await socket.next_v3('wpf_location')
        self.assertEqual(location['payload'], 'newest')
        await socket.next_v3('location_connection_status')
        duplicate = await self.redis_v3.get(latest_key_v3('owner@test.invalid'))
        await self.redis_v3.publish('notifications_channel:owner@test.invalid', duplicate)
        await self.redis_v3.publish('notifications_channel:owner@test.invalid', json.dumps({
            'type':'wpf_raid_state', 'payload':{'is_active':False},
            'event_id':'old-raid', 'received_at_unix_us':location['received_at_unix_us'] - 1000000}))
        await send_wpf_location_v3('owner@test.invalid', 'after-stale')
        next_event = await asyncio.wait_for(socket.out_v3.get(), 3)
        self.assertEqual(next_event['type'], 'wpf_location')
        self.assertEqual(next_event['payload'], 'after-stale')

    async def test_failed_tab_does_not_stop_other_tab_v3(self):
        broken, task = await self.connect_v3()
        healthy, _ = await self.connect_v3()
        broken.fail_v3 = True
        await send_wpf_location_v3('owner@test.invalid', 'still-delivered')
        self.assertEqual((await healthy.next_v3('wpf_location'))['payload'], 'still-delivered')
        await asyncio.wait_for(task, 3)
        await send_wpf_location_v3('owner@test.invalid', 'next')
        self.assertEqual((await healthy.next_v3('wpf_location'))['payload'], 'next')

    async def test_notification_format_and_malformed_packet_v3(self):
        await self.redis_v3.rpush('notifications:owner@test.invalid', json.dumps({'id':1}))
        socket, _ = await self.connect_v3()
        await self.redis_v3.publish('notifications_channel:owner@test.invalid', 'invalid-json')
        await self.redis_v3.publish('notifications_channel:owner@test.invalid', json.dumps({'id':2, 'noti_type':'reply'}))
        self.assertEqual((await socket.next_v3('message'))['data']['id'], 2)
        await send_wpf_location_v3('owner@test.invalid', 'alive')
        self.assertEqual((await socket.next_v3('wpf_location'))['payload'], 'alive')
