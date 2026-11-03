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

from util.location_socket import (
    latest_key, send_wpf_location, send_wpf_log_location,
    send_wpf_raid_state, websocket_handler,
)


class Socket:
    def __init__(self):
        self.out = asyncio.Queue()
        self.incoming = asyncio.Queue()
        self.closed = False
        self.fail = False

    async def accept(self):
        pass

    async def send_text(self, raw):
        if self.fail:
            raise RuntimeError('closed socket')
        await self.out.put(json.loads(raw))

    async def receive_text(self):
        packet = await self.incoming.get()
        if packet is None:
            raise WebSocketDisconnect()
        return packet

    async def close(self, code):
        self.closed = True

    async def next(self, kind):
        async with asyncio.timeout(5):
            while True:
                packet = await self.out.get()
                if packet['type'] == kind:
                    return packet


@unittest.skipUnless(importlib.util.find_spec('redislite'), 'Install redislite for isolated Redis tests')
class LocationSocketTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        import redislite
        cls.root = tempfile.TemporaryDirectory()
        cls.server = redislite.Redis(cls.root.name + '/redis.rdb')

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.root.cleanup()

    async def asyncSetUp(self):
        self.redis = Redis(unix_socket_path=self.server.socket_file, decode_responses=True)
        await self.redis.flushdb()
        self.patch = patch('util.location_socket.get_location_redis', return_value=self.redis)
        self.patch.start()
        self.tasks = []

    async def asyncTearDown(self):
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.patch.stop()
        await self.redis.aclose()

    async def connect(self, email='owner@test.invalid'):
        socket = Socket()
        task = asyncio.create_task(websocket_handler(socket, email))
        self.tasks.append(task)
        await socket.next('init')
        await socket.next('location_connection_status')
        return socket, task

    async def test_tabs_old_disconnect_and_user_isolation(self):
        old, old_task = await self.connect()
        new, _ = await self.connect()
        other, _ = await self.connect('other@test.invalid')
        event_id = await send_wpf_location('owner@test.invalid', 'first', request_id=42)
        for socket in (old, new):
            event = await socket.next('wpf_location')
            self.assertEqual(event['event_id'], event_id)
            self.assertEqual(event['request_id'], 42)
        self.assertTrue(other.out.empty())
        await old.incoming.put(None)
        await asyncio.wait_for(old_task, 3)
        await send_wpf_location('owner@test.invalid', 'second')
        self.assertEqual((await new.next('wpf_location'))['payload'], 'second')
        self.assertTrue(other.out.empty())

    async def test_offline_replay_expiry_and_raid_end(self):
        await send_wpf_location('owner@test.invalid', 'latest')
        socket = Socket()
        task = asyncio.create_task(websocket_handler(socket, 'owner@test.invalid'))
        self.tasks.append(task)
        await socket.next('init')
        replay = await socket.next('wpf_location')
        self.assertTrue(replay['replayed'])
        self.assertEqual(replay['payload'], 'latest')
        self.assertTrue(0 < await self.redis.ttl(latest_key('owner@test.invalid')) <= 60)
        await socket.next('location_connection_status')
        await send_wpf_raid_state('owner@test.invalid', {'is_active': False})
        await socket.next('wpf_raid_state')
        self.assertIsNone(await self.redis.get(latest_key('owner@test.invalid')))
        await send_wpf_log_location('owner@test.invalid', {'x':1,'y':2,'z':3})
        self.assertEqual((await socket.next('wpf_log_location'))['payload']['x'], 1)
        await self.redis.pexpire(latest_key('owner@test.invalid'), 1)
        await asyncio.sleep(.02)
        expired, _ = await self.connect()
        self.assertTrue(expired.out.empty())

    async def test_subscriber_retry_replays_latest_and_keeps_receiving(self):
        socket, _ = await self.connect()
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
        status = await socket.next('location_connection_status')
        self.assertEqual(status['status'], 'reconnecting')
        await send_wpf_location('owner@test.invalid', 'during-recovery')
        replay = await socket.next('wpf_location')
        self.assertEqual(replay['payload'], 'during-recovery')
        self.assertTrue(replay['replayed'])
        self.assertEqual((await socket.next('location_connection_status'))['status'], 'ready')
        await send_wpf_location('owner@test.invalid', 'after-recovery')
        self.assertEqual((await socket.next('wpf_location'))['payload'], 'after-recovery')

    async def test_transparent_redis_reconnect_keeps_delivery(self):
        socket, _ = await self.connect()
        await self.redis.connection_pool.disconnect(inuse_connections=True)
        status = await socket.next('location_connection_status')
        self.assertIn(status['status'], ('ready', 'reconnecting'))
        if status['status'] == 'reconnecting':
            await socket.next('location_connection_status')
        await send_wpf_location('owner@test.invalid', 'after-transparent-reconnect')
        self.assertEqual((await socket.next('wpf_location'))['payload'], 'after-transparent-reconnect')

    async def test_replay_order_duplicates_and_stale_raid_event(self):
        await send_wpf_raid_state('owner@test.invalid', {'is_active':True, 'map':'woods'})
        await send_wpf_location('owner@test.invalid', 'newest')
        socket = Socket()
        task = asyncio.create_task(websocket_handler(socket, 'owner@test.invalid'))
        self.tasks.append(task)
        await socket.next('init')
        state = await asyncio.wait_for(socket.out.get(), 3)
        self.assertEqual(state['type'], 'wpf_raid_state')
        self.assertTrue(state['replayed'])
        location = await socket.next('wpf_location')
        self.assertEqual(location['payload'], 'newest')
        await socket.next('location_connection_status')
        duplicate = await self.redis.get(latest_key('owner@test.invalid'))
        await self.redis.publish('notifications_channel:owner@test.invalid', duplicate)
        await self.redis.publish('notifications_channel:owner@test.invalid', json.dumps({
            'type':'wpf_raid_state', 'payload':{'is_active':False},
            'event_id':'old-raid', 'received_at_unix_us':location['received_at_unix_us'] - 1000000}))
        await send_wpf_location('owner@test.invalid', 'after-stale')
        next_event = await asyncio.wait_for(socket.out.get(), 3)
        self.assertEqual(next_event['type'], 'wpf_location')
        self.assertEqual(next_event['payload'], 'after-stale')

    async def test_failed_tab_does_not_stop_other_tab(self):
        broken, task = await self.connect()
        healthy, _ = await self.connect()
        broken.fail = True
        await send_wpf_location('owner@test.invalid', 'still-delivered')
        self.assertEqual((await healthy.next('wpf_location'))['payload'], 'still-delivered')
        await asyncio.wait_for(task, 3)
        await send_wpf_location('owner@test.invalid', 'next')
        self.assertEqual((await healthy.next('wpf_location'))['payload'], 'next')

    async def test_notification_format_and_malformed_packet(self):
        await self.redis.rpush('notifications:owner@test.invalid', json.dumps({'id':1}))
        socket, _ = await self.connect()
        await self.redis.publish('notifications_channel:owner@test.invalid', 'invalid-json')
        await self.redis.publish('notifications_channel:owner@test.invalid', json.dumps({'id':2, 'noti_type':'reply'}))
        self.assertEqual((await socket.next('message'))['data']['id'], 2)
        await send_wpf_location('owner@test.invalid', 'alive')
        self.assertEqual((await socket.next('wpf_location'))['payload'], 'alive')
