"""PostgreSQL owns history and authorization; Redis is never an authority for membership."""
import base64
import json
import math
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from redis.exceptions import RedisError
from fastapi import HTTPException
from sqlalchemy import delete, func, or_, select, text, tuple_, update
from sqlalchemy.dialects.postgresql import insert

from api.live_map.party_v3.models import PartyMemberV3, PartyRoomV3
from api.live_map.party_v3.service import PartyServiceV3
from api.user.user_res_models import UserV3
from .invite_policy import get_invite_policy_v3
from .models import (
    ChatInvitePreferencesV3, ChatConnectionV3, ChatBlockV3, ChatMessageV3, ChatReportV3, ChatRestrictionV3, ChatUserV3, PartyInvitationV3,
)


def now_v3():
    return datetime.now(timezone.utc)


def event_v3(kind, data):
    return {'type': kind, 'event_id': str(uuid4()), 'server_time': now_v3().isoformat(), 'data': data}


class ChatServiceV3:
    lobby_retention_v3 = timedelta(hours=24)

    def __init__(self, session, limiter=None):
        self.session = session
        # Bounds apply only to new chat transactions, never the existing API sessions.
        self.session.execute(text("SET LOCAL statement_timeout = '5s'"))
        self.session.execute(text("SET LOCAL lock_timeout = '2s'"))
        self.party = PartyServiceV3(session)
        self.limiter = limiter

    def identity_v3(self, email):
        self.party._account_v3(email)
        user = self.session.scalar(select(ChatUserV3).where(ChatUserV3.user_email == email))
        if user is None:
            self.session.execute(insert(ChatUserV3).values(
                id=uuid4(), user_email=email, create_time=now_v3(),
            ).on_conflict_do_nothing(index_elements=['user_email']))
            user = self.session.scalar(select(ChatUserV3).where(ChatUserV3.user_email == email))
        return user

    def target_v3(self, user_id):
        user = self.session.get(ChatUserV3, user_id)
        if user is None:
            raise HTTPException(404, 'CHAT_USER_NOT_FOUND')
        return user

    def public_user_v3(self, user_id):
        user = self.target_v3(user_id)
        account = self.party._account_v3(user.user_email)
        return {'id': str(user.id), 'nickname': account.nickname or '플레이어'}

    def admin_v3(self, user):
        if not self.party._account_v3(user.user_email).is_admin:
            raise HTTPException(403, 'CHAT_ADMIN_REQUIRED')

    def lock_user_v3(self, user):
        self.session.scalar(select(ChatUserV3).where(ChatUserV3.id == user.id).with_for_update())

    def rate_v3(self, user, action, limit, seconds=60):
        if self.limiter is None:
            from .store import get_chat_store_v3
            self.limiter = get_chat_store_v3()
        self.limiter.consume_v3(str(user.id), action, limit, seconds)

    def channel_v3(self, user, channel, room_id):
        if (channel == 'party') != (room_id is not None):
            raise HTTPException(422, 'CHAT_INVALID_CHANNEL')
        if channel == 'party':
            if user is None:
                raise HTTPException(401, 'LOGIN_REQUIRED')
            self.party._room_v3(room_id)
            self.party._member_v3(room_id, user.user_email)

    def current_room_v3(self, user):
        # Existing party APIs permit multiple rooms. Preserve that contract and select
        # the most recently joined open room for the new chat snapshot.
        return self.session.scalar(select(PartyMemberV3.room_id).join(
            PartyRoomV3, PartyRoomV3.id == PartyMemberV3.room_id,
        ).where(PartyMemberV3.user_email == user.user_email,
                PartyMemberV3.status == 'joined', PartyRoomV3.closed_at.is_(None))
            .order_by(PartyMemberV3.joined_at.desc(), PartyMemberV3.id.desc()).limit(1))

    def blocked_v3(self, user, target_id):
        return user is not None and self.session.get(ChatBlockV3, (user.id, target_id)) is not None

    def message_data_v3(self, message):
        return {'id': str(message.id), 'channel': message.channel,
                'room_id': str(message.room_id) if message.room_id else None,
                'user': self.public_user_v3(message.user_id), 'message': message.message,
                'create_time': message.create_time.isoformat()}

    def retained_v3(self, message):
        if message.channel == 'lobby':
            return message.create_time > now_v3() - self.lobby_retention_v3
        room = self.session.get(PartyRoomV3, message.room_id)
        return room is not None and (room.closed_at is None or room.closed_at > now_v3() - timedelta(hours=24))

    def cursor_v3(self, message):
        return base64.urlsafe_b64encode(json.dumps([
            message.create_time.isoformat(), str(message.id), message.channel,
            str(message.room_id) if message.room_id else None,
        ]).encode()).decode()

    def history_v3(self, user, channel, room_id=None, before=None, limit=50):
        self.channel_v3(user, channel, room_id)
        filters = [ChatMessageV3.channel == channel, ChatMessageV3.room_id == room_id,
                   ChatMessageV3.deleted_at.is_(None)]
        if user is not None:
            filters.append(~ChatMessageV3.user_id.in_(
                select(ChatBlockV3.target_id).where(ChatBlockV3.user_id == user.id)))
        if channel == 'lobby':
            filters.append(ChatMessageV3.create_time > now_v3() - self.lobby_retention_v3)
        if before:
            try:
                stamp, message_id, cursor_channel, cursor_room = json.loads(base64.b64decode(
                    before, altchars=b'-_', validate=True,
                ))
                stamp = datetime.fromisoformat(stamp)
                if stamp.tzinfo is None or cursor_channel != channel or cursor_room != (str(room_id) if room_id else None):
                    raise ValueError
                filters.append(tuple_(ChatMessageV3.create_time, ChatMessageV3.id) < tuple_(stamp, UUID(message_id)))
            except (ValueError, TypeError, KeyError):
                raise HTTPException(422, 'CHAT_INVALID_CURSOR') from None
        rows = list(self.session.scalars(select(ChatMessageV3).where(*filters).order_by(
            ChatMessageV3.create_time.desc(), ChatMessageV3.id.desc(),
        ).limit(limit + 1)))
        return {'messages': [self.message_data_v3(row) for row in rows[:limit]],
                'next_before': self.cursor_v3(rows[limit - 1]) if len(rows) > limit else None}

    def send_v3(self, user, data):
        if user is None:
            raise HTTPException(401, 'LOGIN_REQUIRED')
        self.channel_v3(user, data.channel, data.room_id)
        self.lock_user_v3(user)  # serializes idempotency, repetition and moderation per sender
        existing = self.session.scalar(select(ChatMessageV3).where(
            ChatMessageV3.user_id == user.id, ChatMessageV3.request_id == data.request_id,
        ))
        if existing is not None:
            if existing.channel != data.channel or existing.room_id != data.room_id or (
                existing.deleted_at is None and existing.message != data.message
            ):
                raise HTTPException(409, 'CHAT_REQUEST_ID_CONFLICT')
            return {'message_id': str(existing.id), 'request_id': str(data.request_id), 'duplicate': True}
        restriction = self.session.get(ChatRestrictionV3, user.id)
        if restriction and (restriction.expires_at is None or restriction.expires_at > now_v3()):
            raise HTTPException(403, 'CHAT_RESTRICTED')
        self.rate_v3(user, 'send-short', 5, 5)
        self.rate_v3(user, 'send-minute', 30)
        if data.channel == 'lobby':
            repeated = self.session.scalar(select(ChatMessageV3.id).where(
                ChatMessageV3.user_id == user.id, ChatMessageV3.channel == 'lobby',
                ChatMessageV3.message == data.message,
                ChatMessageV3.create_time > now_v3() - timedelta(seconds=30),
            ).limit(1))
            if repeated:
                raise HTTPException(429, 'CHAT_REPEATED_MESSAGE', headers={'Retry-After': '30'})
        message = ChatMessageV3(id=uuid4(), user_id=user.id, channel=data.channel,
                                room_id=data.room_id, request_id=data.request_id,
                                message=data.message, create_time=now_v3())
        self.session.add(message)
        self.session.flush()
        self.queue_v3('chat_message', {'message_id': str(message.id)})
        return {'message_id': str(message.id), 'request_id': str(data.request_id), 'duplicate': False}

    def queue_v3(self, kind, data):
        self.session.info.setdefault('chat_events_v3', []).append(event_v3(kind, data))

    def forward_v3(self, user, event):
        if event['type'] == 'party_notifications_updated':
            if user is not None and event['data']['user_id'] == str(user.id):
                return {**event, 'data': self.notifications_v3(user)}
            return None
        if event['type'] == 'party_invite_preferences_updated':
            if user is not None and event['data']['user_id'] == str(user.id):
                return {**event, 'data': self.invite_preferences_v3(user)}
            return None
        if event['type'] in ('party_invitation_created', 'party_invitation_updated'):
            invitation = self.session.get(PartyInvitationV3, UUID(event['data']['invitation_id']))
            if user is None or invitation is None or user.id not in (invitation.inviter_id, invitation.invitee_id):
                return None
            return {**event, 'data': self.invitation_data_v3(invitation)}
        if event['type'] not in ('chat_message', 'message_deleted'):
            return None
        message = self.session.get(ChatMessageV3, UUID(event['data']['message_id']))
        if message is None or (user is None and message.channel != 'lobby'):
            return None
        if not self.retained_v3(message) or self.blocked_v3(user, message.user_id):
            return None
        try:
            self.channel_v3(user, message.channel, message.room_id)
        except HTTPException as exc:
            if exc.status_code in (403, 404, 410):
                return None
            raise
        if event['type'] == 'chat_message':
            if message.deleted_at is not None:
                return None
            data = self.message_data_v3(message)
        else:
            data = {'message_id': str(message.id), 'channel': message.channel,
                    'room_id': str(message.room_id) if message.room_id else None}
        return {**event, 'data': data}

    def block_v3(self, user, target_id, remove=False):
        self.target_v3(target_id)
        if user.id == target_id:
            raise HTTPException(422, 'CHAT_CANNOT_BLOCK_SELF')
        self.lock_user_v3(user)
        block = self.session.get(ChatBlockV3, (user.id, target_id))
        if remove and block:
            self.session.delete(block)
        elif not remove and not block:
            self.session.add(ChatBlockV3(user_id=user.id, target_id=target_id, create_time=now_v3()))
        return {'user_id': str(target_id), 'blocked': not remove}

    def blocks_v3(self, user):
        return [self.public_user_v3(target) for target in self.session.scalars(
            select(ChatBlockV3.target_id).where(ChatBlockV3.user_id == user.id).order_by(ChatBlockV3.create_time))]

    def report_v3(self, user, message_id, data):
        message = self.session.get(ChatMessageV3, message_id)
        if message is None or message.deleted_at or not self.retained_v3(message):
            raise HTTPException(404, 'CHAT_MESSAGE_NOT_FOUND')
        self.channel_v3(user, message.channel, message.room_id)
        self.lock_user_v3(user)
        existing = self.session.scalar(select(ChatReportV3).where(
            ChatReportV3.user_id == user.id, ChatReportV3.message_id == message_id,
        ))
        if existing:
            raise HTTPException(409, 'CHAT_ALREADY_REPORTED')
        self.rate_v3(user, 'report', 10)
        report = ChatReportV3(id=uuid4(), user_id=user.id, message_id=message_id,
                              **data.model_dump(), create_time=now_v3())
        self.session.add(report)
        return {'id': str(report.id)}

    def delete_message_v3(self, user, message_id):
        self.admin_v3(user)
        message = self.session.scalar(select(ChatMessageV3).where(ChatMessageV3.id == message_id).with_for_update())
        if message is None:
            raise HTTPException(404, 'CHAT_MESSAGE_NOT_FOUND')
        if message.deleted_at is None:
            message.deleted_at, message.message = now_v3(), ''
            self.queue_v3('message_deleted', {'message_id': str(message.id)})
        return {'message_id': str(message.id)}

    def restrict_v3(self, user, target_id, data=None):
        self.admin_v3(user)
        target = self.target_v3(target_id)
        self.lock_user_v3(target)
        row = self.session.get(ChatRestrictionV3, target_id)
        if data is None:
            if row:
                self.session.delete(row)
        else:
            if row is None:
                row = ChatRestrictionV3(user_id=target_id)
                self.session.add(row)
            row.moderator_id, row.reason = user.id, data.reason
            row.expires_at, row.create_time = data.expires_at, now_v3()
        return {'user_id': str(target_id), 'restricted': data is not None}

    def moderation_state_v3(self, user):
        if user is None:
            return {'is_admin': False, 'restricted': False, 'reason': None, 'expires_at': None}
        row = self.session.get(ChatRestrictionV3, user.id)
        active = row is not None and (row.expires_at is None or row.expires_at > now_v3())
        return {'is_admin': bool(self.party._account_v3(user.user_email).is_admin),
                'restricted': active, 'reason': row.reason if active else None,
                'expires_at': row.expires_at.isoformat() if active and row.expires_at else None}

    def restrictions_v3(self, user, limit, offset):
        self.admin_v3(user)
        rows = self.session.scalars(select(ChatRestrictionV3).where(or_(
            ChatRestrictionV3.expires_at.is_(None), ChatRestrictionV3.expires_at > now_v3(),
        )).order_by(ChatRestrictionV3.create_time.desc(), ChatRestrictionV3.user_id)
            .limit(limit).offset(offset))
        return [{'user': self.public_user_v3(row.user_id), 'reason': row.reason,
                 'expires_at': row.expires_at, 'create_time': row.create_time} for row in rows]

    def notifications_v3(self, user):
        # Count incoming effective pending invitations only, independently of the
        # capped inbox list and without counting invitations the user sent.
        rows = self.session.scalars(select(PartyInvitationV3).where(
            PartyInvitationV3.invitee_id == user.id, PartyInvitationV3.status == 'pending',
            PartyInvitationV3.expires_at > now_v3())) if user is not None else []
        count = sum(self.invitation_data_v3(row)['status'] == 'pending' for row in rows)
        return {'party_invitation_count': count, 'notification_tab': 'party'}

    def invite_preferences_v3(self, user):
        allowed = self.session.scalar(select(ChatInvitePreferencesV3.allow_party_invites).where(
            ChatInvitePreferencesV3.user_id == user.id))
        return {'allow_party_invites': True if allowed is None else allowed}

    def set_invite_preferences_v3(self, user, allowed):
        # Recipient lock serializes settings, blocks and new invitations.
        self.lock_user_v3(user)
        timestamp = self.session.scalar(select(func.clock_timestamp()))
        self.session.execute(insert(ChatInvitePreferencesV3).values(
            user_id=user.id, allow_party_invites=allowed, update_time=timestamp,
        ).on_conflict_do_update(index_elements=['user_id'], set_={
            'allow_party_invites': allowed, 'update_time': timestamp,
        }))
        if not allowed:
            ids = self.session.scalars(update(PartyInvitationV3).where(
                PartyInvitationV3.invitee_id == user.id, PartyInvitationV3.status == 'pending',
            ).values(status='revoked', status_reason='receiver_unavailable', update_time=timestamp)
                .returning(PartyInvitationV3.id)).all()
            for invitation_id in ids:
                self.queue_v3('party_invitation_updated', {'invitation_id': str(invitation_id)})
        self.queue_v3('party_invite_preferences_updated', {'user_id': str(user.id)})
        self.queue_v3('party_notifications_updated', {'user_id': str(user.id)})
        return self.invite_preferences_v3(user)

    def lock_invite_users_v3(self, inviter_id, invitee_id):
        # All invitation paths lock the room first, then account UUIDs in order.
        # Preference changes lock only the recipient and never acquire a room lock.
        list(self.session.scalars(select(ChatUserV3).where(
            ChatUserV3.id.in_([inviter_id, invitee_id]),
        ).order_by(ChatUserV3.id).with_for_update()))

    def invite_receiver_checks_v3(self, sender, target):
        if not self.invite_preferences_v3(target)['allow_party_invites'] or self.blocked_v3(target, sender.id):
            # Same response for opt-out and a private reverse block.
            raise HTTPException(403, 'PARTY_INVITATIONS_UNAVAILABLE')

    def invite_abuse_checks_v3(self, sender, target):
        self.invite_receiver_checks_v3(sender, target)
        policy = get_invite_policy_v3()
        timestamp = self.session.scalar(select(func.clock_timestamp()))
        rejected_at = self.session.scalar(select(func.max(PartyInvitationV3.update_time)).where(
            PartyInvitationV3.inviter_id == sender.id, PartyInvitationV3.invitee_id == target.id,
            PartyInvitationV3.status == 'rejected'))
        if rejected_at is not None:
            retry = math.ceil((rejected_at + timedelta(seconds=policy.rejection_cooldown_seconds) - timestamp).total_seconds())
            if retry > 0:
                raise HTTPException(429, 'PARTY_INVITATION_REJECT_COOLDOWN', headers={'Retry-After': str(retry)})
        pending = self.session.scalars(select(PartyInvitationV3).where(
            PartyInvitationV3.inviter_id == sender.id, PartyInvitationV3.invitee_id == target.id,
            PartyInvitationV3.status == 'pending', PartyInvitationV3.expires_at > timestamp))
        if any(self.invitation_data_v3(row)['status'] == 'pending' for row in pending):
            raise HTTPException(409, 'PARTY_INVITATION_DUPLICATED')
        active = self.session.scalar(select(func.count()).select_from(PartyInvitationV3).where(
            PartyInvitationV3.invitee_id == target.id, PartyInvitationV3.status == 'pending',
            PartyInvitationV3.expires_at > timestamp))
        if active >= 50:
            raise HTTPException(429, 'PARTY_INVITATION_LIMIT', headers={'Retry-After': '60'})
        recent = list(self.session.scalars(select(PartyInvitationV3.create_time).where(
            PartyInvitationV3.inviter_id == sender.id,
            PartyInvitationV3.create_time > timestamp - timedelta(seconds=policy.sender_window_seconds),
        ).order_by(PartyInvitationV3.create_time.desc()).limit(policy.sender_limit)))
        if len(recent) >= policy.sender_limit:
            retry = max(1, math.ceil((recent[-1] + timedelta(seconds=policy.sender_window_seconds) - timestamp).total_seconds()))
            raise HTTPException(429, 'PARTY_INVITATION_RATE_LIMITED', headers={'Retry-After': str(retry)})

    def user_actions_v3(self, user, target_id, room_id=None):
        target = self.target_v3(target_id)
        is_self = user.id == target.id
        result = {'user': self.public_user_v3(target.id), 'blocked': self.blocked_v3(user, target.id),
                  'can_block': not is_self, 'can_restrict': not is_self and
                  bool(self.party._account_v3(user.user_email).is_admin), 'can_invite': False,
                  'invite_disabled_reason': 'PARTY_ROOM_REQUIRED', 'retry_after': None, 'member_id': None, 'can_unkick': False}
        if room_id is None:
            return result
        room = self.party._room_v3(room_id)
        # Membership identifiers and kick state are visible only to this room's owner.
        self.party._owner_v3(room.id, user.user_email)
        member = self.session.scalar(select(PartyMemberV3).where(
            PartyMemberV3.room_id == room.id, PartyMemberV3.user_email == target.user_email))
        result['member_id'] = str(member.id) if member else None
        result['can_unkick'] = member is not None and member.status == 'kicked'
        try:
            if is_self:
                raise HTTPException(422, 'PARTY_CANNOT_INVITE_SELF')
            self.invite_checks_v3(room, target)
            self.invite_abuse_checks_v3(user, target)
            pending = self.session.scalars(select(PartyInvitationV3).where(
                PartyInvitationV3.room_id == room.id, PartyInvitationV3.invitee_id == target.id,
                PartyInvitationV3.status == 'pending'))
            if any(self.invitation_data_v3(row)['status'] == 'pending' for row in pending):
                raise HTTPException(409, 'PARTY_INVITATION_DUPLICATED')
        except HTTPException as exc:
            result['invite_disabled_reason'] = exc.detail
            retry = (exc.headers or {}).get('Retry-After')
            result['retry_after'] = int(retry) if retry else None
        else:
            result['can_invite'], result['invite_disabled_reason'] = True, None
        return result

    def reports_v3(self, user, limit, offset):
        self.admin_v3(user)
        return [{'id': str(row.id), 'user_id': str(row.user_id), 'message_id': str(row.message_id),
                 'reason': row.reason, 'detail': row.detail, 'create_time': row.create_time.isoformat(),
                 'message': self.message_data_v3(self.session.get(ChatMessageV3, row.message_id))}
                for row in self.session.scalars(select(ChatReportV3).order_by(
                    ChatReportV3.create_time.desc(), ChatReportV3.id.desc()).limit(limit).offset(offset))]

    def room_state_v3(self, room):
        count = self.session.scalar(select(func.count()).select_from(PartyMemberV3).where(
            PartyMemberV3.room_id == room.id, PartyMemberV3.status == 'joined'))
        return {'id': str(room.id), 'name': room.name, 'member_count': count,
                'max_members': room.max_members, 'is_locked': room.is_locked,
                'closed': room.closed_at is not None,
                'can_join': room.closed_at is None and not room.is_locked and count < room.max_members}

    def invitation_data_v3(self, invitation):
        room = self.session.get(PartyRoomV3, invitation.room_id)
        state = self.room_state_v3(room)
        status = invitation.status
        status_reason = invitation.status_reason
        if status == 'pending':
            target = self.target_v3(invitation.invitee_id)
            member = self.session.scalar(select(PartyMemberV3).where(
                PartyMemberV3.room_id == room.id, PartyMemberV3.user_email == target.user_email))
            if invitation.expires_at <= now_v3():
                status = 'expired'
            elif state['closed']:
                status = 'revoked'
                status_reason = 'room_closed'
            elif member is not None and member.status == 'kicked':
                status = 'revoked'
                status_reason = 'member_kicked'
            elif (member is not None and member.joined_at > invitation.create_time) or self.current_room_v3(target) is not None:
                status = 'revoked'
                status_reason = 'already_joined'
            elif state['member_count'] >= state['max_members']:
                status = 'revoked'
                status_reason = 'room_full'
        return {'id': str(invitation.id), 'invitation_id': str(invitation.id),
                'notification_tab': 'party', 'room_id': str(invitation.room_id), 'inviter': self.public_user_v3(invitation.inviter_id),
                'invitee_user_id': str(invitation.invitee_id), 'status': status,
                'status_reason': status_reason,
                'expires_at': invitation.expires_at.isoformat(), 'party': state}

    def reconcile_room_v3(self, room):
        # All invitation state changes use the existing party room row lock.
        state = self.room_state_v3(room)
        pending = list(self.session.scalars(select(PartyInvitationV3).where(
            PartyInvitationV3.room_id == room.id, PartyInvitationV3.status == 'pending')))
        for invitation in pending:
            target = self.target_v3(invitation.invitee_id)
            member = self.session.scalar(select(PartyMemberV3).where(
                PartyMemberV3.room_id == room.id, PartyMemberV3.user_email == target.user_email))
            status = reason = None
            if invitation.expires_at <= now_v3():
                status = 'expired'
            elif state['closed']:
                status = 'revoked'
                reason = 'room_closed'
            elif member is not None and member.status == 'kicked':
                status = 'revoked'
                reason = 'member_kicked'
            elif (member is not None and member.joined_at > invitation.create_time) or self.current_room_v3(target) is not None:
                status = 'revoked'
                reason = 'already_joined'
            elif state['member_count'] >= state['max_members']:
                status = 'revoked'
                reason = 'room_full'
            if status:
                invitation.status, invitation.status_reason = status, reason
                invitation.update_time = now_v3()
        self.session.flush()

    def invitations_v3(self, user, status='pending'):
        filters = [or_(PartyInvitationV3.invitee_id == user.id, PartyInvitationV3.inviter_id == user.id)]
        # Include stored pending rows when filtering terminal effective states.
        if status:
            filters.append(PartyInvitationV3.status.in_([status, 'pending']))
        rows = [self.invitation_data_v3(row) for row in self.session.scalars(
            select(PartyInvitationV3).where(*filters).order_by(
                (PartyInvitationV3.status == 'pending').desc(),
                PartyInvitationV3.create_time.desc(), PartyInvitationV3.id.desc()).limit(500))]
        return [row for row in rows if status is None or row['status'] == status]

    def invite_checks_v3(self, room, target):
        if room.closed_at is not None:
            raise HTTPException(410, 'PARTY_ROOM_CLOSED')
        if room.is_locked:
            raise HTTPException(403, 'PARTY_ROOM_LOCKED')
        member = self.session.scalar(select(PartyMemberV3).where(
            PartyMemberV3.room_id == room.id, PartyMemberV3.user_email == target.user_email))
        if member and member.status == 'kicked':
            raise HTTPException(403, 'PARTY_MEMBER_KICKED')
        if self.current_room_v3(target) is not None:
            raise HTTPException(409, 'PARTY_ALREADY_JOINED')
        if len(self.party._joined_v3(room.id)) >= room.max_members:
            raise HTTPException(409, 'PARTY_ROOM_FULL')
        return member

    def create_invitation_v3(self, user, data):
        if user.id == data.invitee_user_id:
            raise HTTPException(422, 'PARTY_CANNOT_INVITE_SELF')
        target = self.target_v3(data.invitee_user_id)
        room = self.session.scalar(select(PartyRoomV3).where(PartyRoomV3.id == data.room_id).with_for_update())
        if room is None:
            raise HTTPException(404, 'ROOM_NOT_FOUND')
        self.party._owner_v3(room.id, user.user_email)
        self.lock_invite_users_v3(user.id, target.id)
        self.invite_checks_v3(room, target)
        self.invite_abuse_checks_v3(user, target)
        self.reconcile_room_v3(room)
        duplicate = self.session.scalar(select(PartyInvitationV3.id).where(
            PartyInvitationV3.room_id == room.id, PartyInvitationV3.invitee_id == target.id,
            PartyInvitationV3.status == 'pending'))
        if duplicate:
            raise HTTPException(409, 'PARTY_INVITATION_DUPLICATED')
        # Bounded active inbox makes reconnect and room-state reconciliation bounded.
        active = self.session.scalar(select(func.count()).select_from(PartyInvitationV3).where(
            PartyInvitationV3.invitee_id == target.id, PartyInvitationV3.status == 'pending',
            PartyInvitationV3.expires_at > now_v3()))
        if active >= 50:
            raise HTTPException(429, 'PARTY_INVITATION_LIMIT', headers={'Retry-After': '60'})
        now = self.session.scalar(select(func.clock_timestamp()))
        invitation = PartyInvitationV3(id=uuid4(), room_id=room.id, inviter_id=user.id,
            invitee_id=target.id, status='pending', status_reason=None,
            expires_at=now + timedelta(minutes=10),
            create_time=now, update_time=now)
        self.session.add(invitation)
        self.session.flush()
        self.queue_v3('party_invitation_created', {'invitation_id': str(invitation.id)})
        self.queue_v3('party_notifications_updated', {'user_id': str(target.id)})
        return self.invitation_data_v3(invitation)

    def handle_invitation_v3(self, user, invitation_id, action):
        invitation = self.session.get(PartyInvitationV3, invitation_id)
        if invitation is None:
            raise HTTPException(404, 'PARTY_INVITATION_NOT_FOUND')
        # Never expose another recipient's invitation, even if the UUID is known.
        if action != 'revoke' and invitation.invitee_id != user.id:
            raise HTTPException(403, 'PARTY_INVITATION_FORBIDDEN')
        room = self.session.scalar(select(PartyRoomV3).where(
            PartyRoomV3.id == invitation.room_id).with_for_update())
        self.lock_invite_users_v3(invitation.inviter_id, invitation.invitee_id)
        self.session.refresh(invitation)
        if action == 'revoke' and invitation.inviter_id != user.id:
            try:
                self.party._owner_v3(room.id, user.user_email)
            except HTTPException:
                raise HTTPException(403, 'PARTY_INVITATION_FORBIDDEN') from None
        if invitation.expires_at <= now_v3() or invitation.status == 'expired':
            raise HTTPException(410, 'PARTY_INVITATION_EXPIRED')
        if invitation.status != 'pending':
            raise HTTPException(409, 'PARTY_INVITATION_ALREADY_HANDLED')
        if action == 'accept':
            self.invite_receiver_checks_v3(self.target_v3(invitation.inviter_id), user)
            member = self.invite_checks_v3(room, user)
            if member is not None and member.joined_at > invitation.create_time:
                raise HTTPException(409, 'PARTY_INVITATION_ALREADY_HANDLED')
            joined = self.party._joined_v3(room.id)
            now = now_v3()
            if member is None:
                member = PartyMemberV3(id=uuid4(), room_id=room.id,
                    user_email=user.user_email, create_time=now)
                self.session.add(member)
            member.nickname = self.party._nickname_v3(self.party._account_v3(user.user_email), None)
            member.color = self.party._color_v3(joined, member.color)
            member.role, member.status, member.left_at = 'member', 'joined', None
            member.joined_at = member.update_time = now
            room.empty_since, room.update_time = None, now
            invitation.status, invitation.status_reason, invitation.update_time = 'accepted', None, now
            self.session.info['chat_party_room_v3'] = room.id
            snapshot = self.party._snapshot_v3(room, member)
            self.reconcile_room_v3(room)
            self.queue_v3('party_invitation_updated', {'invitation_id': str(invitation.id)})
            self.queue_v3('party_notifications_updated', {'user_id': str(invitation.invitee_id)})
            return snapshot.model_dump(mode='json')
        invitation.status = 'rejected' if action == 'reject' else 'revoked'
        invitation.status_reason = None if action == 'reject' else 'cancelled'
        invitation.update_time = self.session.scalar(select(func.clock_timestamp()))
        self.session.flush()
        self.queue_v3('party_invitation_updated', {'invitation_id': str(invitation.id)})
        self.queue_v3('party_notifications_updated', {'user_id': str(invitation.invitee_id)})
        return self.invitation_data_v3(invitation)

    def connect_session_v3(self, user, connection_id):
        timestamp = now_v3()
        self.session.add(ChatConnectionV3(
            id=UUID(connection_id), user_id=user.id, connected_at=timestamp,
            last_seen_at=timestamp, expires_at=timestamp + timedelta(seconds=90),
        ))

    def touch_session_v3(self, user, connection_id):
        timestamp = now_v3()
        self.session.execute(update(ChatConnectionV3).where(
            ChatConnectionV3.id == UUID(connection_id), ChatConnectionV3.user_id == user.id,
            ChatConnectionV3.disconnected_at.is_(None), ChatConnectionV3.expires_at > timestamp,
        ).values(last_seen_at=timestamp, expires_at=timestamp + timedelta(seconds=90)))

    def disconnect_session_v3(self, connection_id):
        timestamp = now_v3()
        self.session.execute(update(ChatConnectionV3).where(
            ChatConnectionV3.id == UUID(connection_id), ChatConnectionV3.disconnected_at.is_(None),
        ).values(disconnected_at=timestamp, disconnect_reason='closed'))

    def expire_sessions_v3(self):
        self.session.execute(update(ChatConnectionV3).where(
            ChatConnectionV3.disconnected_at.is_(None), ChatConnectionV3.expires_at <= now_v3(),
        ).values(disconnected_at=ChatConnectionV3.expires_at, disconnect_reason='expired'))

    def connection_history_v3(self, user, online_only=False, limit=50, offset=0):
        self.admin_v3(user)
        timestamp = now_v3()
        query = select(ChatConnectionV3, ChatUserV3.id, UserV3.nickname).join(
            ChatUserV3, ChatUserV3.id == ChatConnectionV3.user_id,
        ).join(UserV3, UserV3.email == ChatUserV3.user_email)
        if online_only:
            query = query.where(ChatConnectionV3.disconnected_at.is_(None),
                                ChatConnectionV3.expires_at > timestamp)
        rows = self.session.execute(query.order_by(
            ChatConnectionV3.connected_at.desc(), ChatConnectionV3.id.desc(),
        ).limit(limit).offset(offset))
        return [{'id': str(row.id), 'user': {'id': str(user_id), 'nickname': nickname or '플레이어'},
                 'connected_at': row.connected_at, 'last_seen_at': row.last_seen_at,
                 'expires_at': row.expires_at, 'disconnected_at': row.disconnected_at,
                 'disconnect_reason': row.disconnect_reason,
                 'online': row.disconnected_at is None and row.expires_at > timestamp}
                for row, user_id, nickname in rows]

    def online_users_v3(self):
        from .store import get_chat_store_v3
        store = self.limiter if self.limiter is not None else get_chat_store_v3()
        try:
            ids = [UUID(value) for value in store.online_user_ids_v3()]
        except RedisError:
            raise HTTPException(503, 'CHAT_PRESENCE_UNAVAILABLE') from None
        if not ids:
            return []
        rows = self.session.execute(select(ChatUserV3.id, UserV3.nickname).join(
            UserV3, UserV3.email == ChatUserV3.user_email,
        ).where(ChatUserV3.id.in_(ids)))
        users = [{'id': str(user_id), 'nickname': nickname or '플레이어'}
                 for user_id, nickname in rows]
        return sorted(users, key=lambda row: (row['nickname'], row['id']))

    def snapshot_v3(self, user):
        invitations = self.invitations_v3(user) if user is not None else []
        room_id = self.current_room_v3(user) if user is not None else None
        lobby = self.history_v3(user, 'lobby')
        party = self.history_v3(user, 'party', room_id) if room_id else {'messages': [], 'next_before': None}
        return {'user': self.public_user_v3(user.id) if user is not None else None, 'lobby': lobby['messages'], 'party': party['messages'],
                'lobby_next_before': lobby['next_before'], 'party_next_before': party['next_before'],
                'party_room_id': str(room_id) if room_id else None,
                'party_invite_preferences': self.invite_preferences_v3(user) if user is not None else None,
                'online_users': self.online_users_v3(), 'party_invitations': invitations, 'notifications': self.notifications_v3(user),
                'moderation': self.moderation_state_v3(user), 'heartbeat_interval_seconds': 30}

    def cleanup_v3(self, limit=500):
        old_rooms = select(PartyRoomV3.id).where(PartyRoomV3.closed_at <= now_v3() - timedelta(hours=24))
        ids = select(ChatMessageV3.id).where(or_(
            (ChatMessageV3.channel == 'lobby') & (ChatMessageV3.create_time <= now_v3() - self.lobby_retention_v3),
            ChatMessageV3.room_id.in_(old_rooms),
        )).limit(limit)
        self.session.execute(delete(ChatMessageV3).where(ChatMessageV3.id.in_(ids)))
        policy = get_invite_policy_v3()
        retention = timedelta(seconds=max(7 * 86400, policy.sender_window_seconds, policy.rejection_cooldown_seconds))
        invitations = select(PartyInvitationV3.id).where(
            PartyInvitationV3.expires_at <= now_v3() - retention,
            PartyInvitationV3.update_time <= now_v3() - retention).limit(limit)
        self.session.execute(delete(PartyInvitationV3).where(PartyInvitationV3.id.in_(invitations)))

    def reconcile_batch_v3(self, after_id=None, limit=100):
        room_ids = select(PartyInvitationV3.room_id).where(
            PartyInvitationV3.status == 'pending').distinct()
        query = select(PartyRoomV3).where(PartyRoomV3.id.in_(room_ids))
        if after_id is not None:
            query = query.where(PartyRoomV3.id > after_id)
        rooms = list(self.session.scalars(query.order_by(PartyRoomV3.id).limit(limit)
            .with_for_update(skip_locked=True)))
        for room in rooms:
            self.reconcile_room_v3(room)
        return rooms[-1].id if len(rooms) == limit else None
