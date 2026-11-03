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

from api.live_map.party.models import PartyMember, PartyRoom
from api.live_map.party.service import PartyService
from api.user.user_res_models import User
from .invite_policy import get_invite_policy
from .models import (
    ChatInvitePreferences, ChatConnection, ChatBlock, ChatMessage, ChatReport, ChatRestriction, ChatUser, PartyInvitation,
)

from util.http_exceptions import HttpError


def utc_now():
    return datetime.now(timezone.utc)


def build_event(kind, data):
    return {'type': kind, 'event_id': str(uuid4()), 'server_time': utc_now().isoformat(), 'data': data}


class ChatService:
    lobby_retention = timedelta(hours=24)

    def __init__(self, session, limiter=None):
        self.session = session
        # Bounds apply only to new chat transactions, never the existing API sessions.
        self.session.execute(text("SET LOCAL statement_timeout = '5s'"))
        self.session.execute(text("SET LOCAL lock_timeout = '2s'"))
        self.party = PartyService(session)
        self.limiter = limiter

    def identity(self, email):
        self.party._account(email)
        user = self.session.scalar(select(ChatUser).where(ChatUser.user_email == email))
        if user is None:
            self.session.execute(insert(ChatUser).values(
                id=uuid4(), user_email=email, create_time=utc_now(),
            ).on_conflict_do_nothing(index_elements=['user_email']))
            user = self.session.scalar(select(ChatUser).where(ChatUser.user_email == email))
        return user

    def target(self, user_id):
        user = self.session.get(ChatUser, user_id)
        if user is None:
            raise HttpError.CHAT_USER_NOT_FOUND.exception()
        return user

    def public_user(self, user_id):
        user = self.target(user_id)
        account = self.party._account(user.user_email)
        return {'id': str(user.id), 'nickname': account.nickname or '플레이어'}

    def admin(self, user):
        if not self.party._account(user.user_email).is_admin:
            raise HttpError.CHAT_ADMIN_REQUIRED.exception()

    def lock_user(self, user):
        self.session.scalar(select(ChatUser).where(ChatUser.id == user.id).with_for_update())

    def rate(self, user, action, limit, seconds=60):
        if self.limiter is None:
            from .store import get_chat_store
            self.limiter = get_chat_store()
        self.limiter.consume(str(user.id), action, limit, seconds)

    def channel(self, user, channel, room_id):
        if (channel == 'party') != (room_id is not None):
            raise HttpError.CHAT_INVALID_CHANNEL.exception()
        if channel == 'party':
            if user is None:
                raise HttpError.LOGIN_REQUIRED.exception()
            self.party._room(room_id)
            self.party._member(room_id, user.user_email)

    def current_room(self, user):
        # Existing party APIs permit multiple rooms. Preserve that contract and select
        # the most recently joined open room for the new chat snapshot.
        return self.session.scalar(select(PartyMember.room_id).join(
            PartyRoom, PartyRoom.id == PartyMember.room_id,
        ).where(PartyMember.user_email == user.user_email,
                PartyMember.status == 'joined', PartyRoom.closed_at.is_(None))
            .order_by(PartyMember.joined_at.desc(), PartyMember.id.desc()).limit(1))

    def blocked(self, user, target_id):
        return user is not None and self.session.get(ChatBlock, (user.id, target_id)) is not None

    def message_data(self, message):
        return {'id': str(message.id), 'channel': message.channel,
                'room_id': str(message.room_id) if message.room_id else None,
                'user': self.public_user(message.user_id), 'message': message.message,
                'create_time': message.create_time.isoformat()}

    def retained(self, message):
        if message.channel == 'lobby':
            return message.create_time > utc_now() - self.lobby_retention
        room = self.session.get(PartyRoom, message.room_id)
        return room is not None and (room.closed_at is None or room.closed_at > utc_now() - timedelta(hours=24))

    def cursor(self, message):
        return base64.urlsafe_b64encode(json.dumps([
            message.create_time.isoformat(), str(message.id), message.channel,
            str(message.room_id) if message.room_id else None,
        ]).encode()).decode()

    def history(self, user, channel, room_id=None, before=None, limit=50):
        self.channel(user, channel, room_id)
        filters = [ChatMessage.channel == channel, ChatMessage.room_id == room_id,
                   ChatMessage.deleted_at.is_(None)]
        if user is not None:
            filters.append(~ChatMessage.user_id.in_(
                select(ChatBlock.target_id).where(ChatBlock.user_id == user.id)))
        if channel == 'lobby':
            filters.append(ChatMessage.create_time > utc_now() - self.lobby_retention)
        if before:
            try:
                stamp, message_id, cursor_channel, cursor_room = json.loads(base64.b64decode(
                    before, altchars=b'-_', validate=True,
                ))
                stamp = datetime.fromisoformat(stamp)
                if stamp.tzinfo is None or cursor_channel != channel or cursor_room != (str(room_id) if room_id else None):
                    raise ValueError
                filters.append(tuple_(ChatMessage.create_time, ChatMessage.id) < tuple_(stamp, UUID(message_id)))
            except (ValueError, TypeError, KeyError):
                raise HttpError.CHAT_INVALID_CURSOR.exception() from None
        rows = list(self.session.scalars(select(ChatMessage).where(*filters).order_by(
            ChatMessage.create_time.desc(), ChatMessage.id.desc(),
        ).limit(limit + 1)))
        return {'messages': [self.message_data(row) for row in rows[:limit]],
                'next_before': self.cursor(rows[limit - 1]) if len(rows) > limit else None}

    def send(self, user, data):
        if user is None:
            raise HttpError.LOGIN_REQUIRED.exception()
        self.channel(user, data.channel, data.room_id)
        self.lock_user(user)  # serializes idempotency, repetition and moderation per sender
        existing = self.session.scalar(select(ChatMessage).where(
            ChatMessage.user_id == user.id, ChatMessage.request_id == data.request_id,
        ))
        if existing is not None:
            if existing.channel != data.channel or existing.room_id != data.room_id or (
                existing.deleted_at is None and existing.message != data.message
            ):
                raise HttpError.CHAT_REQUEST_ID_CONFLICT.exception()
            return {'message_id': str(existing.id), 'request_id': str(data.request_id), 'duplicate': True}
        restriction = self.session.get(ChatRestriction, user.id)
        if restriction and (restriction.expires_at is None or restriction.expires_at > utc_now()):
            raise HttpError.CHAT_RESTRICTED.exception()
        self.rate(user, 'send-short', 5, 5)
        self.rate(user, 'send-minute', 30)
        if data.channel == 'lobby':
            repeated = self.session.scalar(select(ChatMessage.id).where(
                ChatMessage.user_id == user.id, ChatMessage.channel == 'lobby',
                ChatMessage.message == data.message,
                ChatMessage.create_time > utc_now() - timedelta(seconds=30),
            ).limit(1))
            if repeated:
                raise HttpError.CHAT_REPEATED_MESSAGE.exception(headers={'Retry-After': '30'})
        message = ChatMessage(id=uuid4(), user_id=user.id, channel=data.channel,
                                room_id=data.room_id, request_id=data.request_id,
                                message=data.message, create_time=utc_now())
        self.session.add(message)
        self.session.flush()
        self.queue('chat_message', {'message_id': str(message.id)})
        return {'message_id': str(message.id), 'request_id': str(data.request_id), 'duplicate': False}

    def queue(self, kind, data):
        self.session.info.setdefault('chat_events_v3', []).append(build_event(kind, data))

    def forward(self, user, event):
        if event['type'] == 'party_notifications_updated':
            if user is not None and event['data']['user_id'] == str(user.id):
                return {**event, 'data': self.notifications(user)}
            return None
        if event['type'] == 'party_invite_preferences_updated':
            if user is not None and event['data']['user_id'] == str(user.id):
                return {**event, 'data': self.invite_preferences(user)}
            return None
        if event['type'] in ('party_invitation_created', 'party_invitation_updated'):
            invitation = self.session.get(PartyInvitation, UUID(event['data']['invitation_id']))
            if user is None or invitation is None or user.id not in (invitation.inviter_id, invitation.invitee_id):
                return None
            return {**event, 'data': self.invitation_data(invitation)}
        if event['type'] not in ('chat_message', 'message_deleted'):
            return None
        message = self.session.get(ChatMessage, UUID(event['data']['message_id']))
        if message is None or (user is None and message.channel != 'lobby'):
            return None
        if not self.retained(message) or self.blocked(user, message.user_id):
            return None
        try:
            self.channel(user, message.channel, message.room_id)
        except HTTPException as exc:
            if exc.status_code in (403, 404, 410):
                return None
            raise
        if event['type'] == 'chat_message':
            if message.deleted_at is not None:
                return None
            data = self.message_data(message)
        else:
            data = {'message_id': str(message.id), 'channel': message.channel,
                    'room_id': str(message.room_id) if message.room_id else None}
        return {**event, 'data': data}

    def block(self, user, target_id, remove=False):
        self.target(target_id)
        if user.id == target_id:
            raise HttpError.CHAT_CANNOT_BLOCK_SELF.exception()
        self.lock_user(user)
        block = self.session.get(ChatBlock, (user.id, target_id))
        if remove and block:
            self.session.delete(block)
        elif not remove and not block:
            self.session.add(ChatBlock(user_id=user.id, target_id=target_id, create_time=utc_now()))
        return {'user_id': str(target_id), 'blocked': not remove}

    def blocks(self, user):
        return [self.public_user(target) for target in self.session.scalars(
            select(ChatBlock.target_id).where(ChatBlock.user_id == user.id).order_by(ChatBlock.create_time))]

    def report(self, user, message_id, data):
        message = self.session.get(ChatMessage, message_id)
        if message is None or message.deleted_at or not self.retained(message):
            raise HttpError.CHAT_MESSAGE_NOT_FOUND.exception()
        self.channel(user, message.channel, message.room_id)
        self.lock_user(user)
        existing = self.session.scalar(select(ChatReport).where(
            ChatReport.user_id == user.id, ChatReport.message_id == message_id,
        ))
        if existing:
            raise HttpError.CHAT_ALREADY_REPORTED.exception()
        self.rate(user, 'report', 10)
        report = ChatReport(id=uuid4(), user_id=user.id, message_id=message_id,
                              **data.model_dump(), create_time=utc_now())
        self.session.add(report)
        return {'id': str(report.id)}

    def delete_message(self, user, message_id):
        self.admin(user)
        message = self.session.scalar(select(ChatMessage).where(ChatMessage.id == message_id).with_for_update())
        if message is None:
            raise HttpError.CHAT_MESSAGE_NOT_FOUND.exception()
        if message.deleted_at is None:
            message.deleted_at, message.message = utc_now(), ''
            self.queue('message_deleted', {'message_id': str(message.id)})
        return {'message_id': str(message.id)}

    def restrict(self, user, target_id, data=None):
        self.admin(user)
        target = self.target(target_id)
        self.lock_user(target)
        row = self.session.get(ChatRestriction, target_id)
        if data is None:
            if row:
                self.session.delete(row)
        else:
            if row is None:
                row = ChatRestriction(user_id=target_id)
                self.session.add(row)
            row.moderator_id, row.reason = user.id, data.reason
            row.expires_at, row.create_time = data.expires_at, utc_now()
        return {'user_id': str(target_id), 'restricted': data is not None}

    def moderation_state(self, user):
        if user is None:
            return {'is_admin': False, 'restricted': False, 'reason': None, 'expires_at': None}
        row = self.session.get(ChatRestriction, user.id)
        active = row is not None and (row.expires_at is None or row.expires_at > utc_now())
        return {'is_admin': bool(self.party._account(user.user_email).is_admin),
                'restricted': active, 'reason': row.reason if active else None,
                'expires_at': row.expires_at.isoformat() if active and row.expires_at else None}

    def restrictions(self, user, limit, offset):
        self.admin(user)
        rows = self.session.scalars(select(ChatRestriction).where(or_(
            ChatRestriction.expires_at.is_(None), ChatRestriction.expires_at > utc_now(),
        )).order_by(ChatRestriction.create_time.desc(), ChatRestriction.user_id)
            .limit(limit).offset(offset))
        return [{'user': self.public_user(row.user_id), 'reason': row.reason,
                 'expires_at': row.expires_at, 'create_time': row.create_time} for row in rows]

    def notifications(self, user):
        # Count incoming effective pending invitations only, independently of the
        # capped inbox list and without counting invitations the user sent.
        rows = self.session.scalars(select(PartyInvitation).where(
            PartyInvitation.invitee_id == user.id, PartyInvitation.status == 'pending',
            PartyInvitation.expires_at > utc_now())) if user is not None else []
        count = sum(self.invitation_data(row)['status'] == 'pending' for row in rows)
        return {'party_invitation_count': count, 'notification_tab': 'party'}

    def invite_preferences(self, user):
        allowed = self.session.scalar(select(ChatInvitePreferences.allow_party_invites).where(
            ChatInvitePreferences.user_id == user.id))
        return {'allow_party_invites': True if allowed is None else allowed}

    def set_invite_preferences(self, user, allowed):
        # Recipient lock serializes settings, blocks and new invitations.
        self.lock_user(user)
        timestamp = self.session.scalar(select(func.clock_timestamp()))
        self.session.execute(insert(ChatInvitePreferences).values(
            user_id=user.id, allow_party_invites=allowed, update_time=timestamp,
        ).on_conflict_do_update(index_elements=['user_id'], set_={
            'allow_party_invites': allowed, 'update_time': timestamp,
        }))
        if not allowed:
            ids = self.session.scalars(update(PartyInvitation).where(
                PartyInvitation.invitee_id == user.id, PartyInvitation.status == 'pending',
            ).values(status='revoked', status_reason='receiver_unavailable', update_time=timestamp)
                .returning(PartyInvitation.id)).all()
            for invitation_id in ids:
                self.queue('party_invitation_updated', {'invitation_id': str(invitation_id)})
        self.queue('party_invite_preferences_updated', {'user_id': str(user.id)})
        self.queue('party_notifications_updated', {'user_id': str(user.id)})
        return self.invite_preferences(user)

    def lock_invite_users(self, inviter_id, invitee_id):
        # All invitation paths lock the room first, then account UUIDs in order.
        # Preference changes lock only the recipient and never acquire a room lock.
        list(self.session.scalars(select(ChatUser).where(
            ChatUser.id.in_([inviter_id, invitee_id]),
        ).order_by(ChatUser.id).with_for_update()))

    def invite_receiver_checks(self, sender, target):
        if not self.invite_preferences(target)['allow_party_invites'] or self.blocked(target, sender.id):
            # Same response for opt-out and a private reverse block.
            raise HttpError.PARTY_INVITATIONS_UNAVAILABLE.exception()

    def invite_abuse_checks(self, sender, target):
        self.invite_receiver_checks(sender, target)
        policy = get_invite_policy()
        timestamp = self.session.scalar(select(func.clock_timestamp()))
        rejected_at = self.session.scalar(select(func.max(PartyInvitation.update_time)).where(
            PartyInvitation.inviter_id == sender.id, PartyInvitation.invitee_id == target.id,
            PartyInvitation.status == 'rejected'))
        if rejected_at is not None:
            retry = math.ceil((rejected_at + timedelta(seconds=policy.rejection_cooldown_seconds) - timestamp).total_seconds())
            if retry > 0:
                raise HttpError.PARTY_INVITATION_REJECT_COOLDOWN.exception(headers={'Retry-After': str(retry)})
        pending = self.session.scalars(select(PartyInvitation).where(
            PartyInvitation.inviter_id == sender.id, PartyInvitation.invitee_id == target.id,
            PartyInvitation.status == 'pending', PartyInvitation.expires_at > timestamp))
        if any(self.invitation_data(row)['status'] == 'pending' for row in pending):
            raise HttpError.PARTY_INVITATION_DUPLICATED.exception()
        active = self.session.scalar(select(func.count()).select_from(PartyInvitation).where(
            PartyInvitation.invitee_id == target.id, PartyInvitation.status == 'pending',
            PartyInvitation.expires_at > timestamp))
        if active >= 50:
            raise HttpError.PARTY_INVITATION_LIMIT.exception(headers={'Retry-After': '60'})
        recent = list(self.session.scalars(select(PartyInvitation.create_time).where(
            PartyInvitation.inviter_id == sender.id,
            PartyInvitation.create_time > timestamp - timedelta(seconds=policy.sender_window_seconds),
        ).order_by(PartyInvitation.create_time.desc()).limit(policy.sender_limit)))
        if len(recent) >= policy.sender_limit:
            retry = max(1, math.ceil((recent[-1] + timedelta(seconds=policy.sender_window_seconds) - timestamp).total_seconds()))
            raise HttpError.PARTY_INVITATION_RATE_LIMITED.exception(headers={'Retry-After': str(retry)})

    def user_actions(self, user, target_id, room_id=None):
        target = self.target(target_id)
        is_self = user.id == target.id
        result = {'user': self.public_user(target.id), 'blocked': self.blocked(user, target.id),
                  'can_block': not is_self, 'can_restrict': not is_self and
                  bool(self.party._account(user.user_email).is_admin), 'can_invite': False,
                  'invite_disabled_reason': 'PARTY_ROOM_REQUIRED', 'retry_after': None, 'member_id': None, 'can_unkick': False}
        if room_id is None:
            return result
        room = self.party._room(room_id)
        # Membership identifiers and kick state are visible only to this room's owner.
        self.party._owner(room.id, user.user_email)
        member = self.session.scalar(select(PartyMember).where(
            PartyMember.room_id == room.id, PartyMember.user_email == target.user_email))
        result['member_id'] = str(member.id) if member else None
        result['can_unkick'] = member is not None and member.status == 'kicked'
        try:
            if is_self:
                raise HttpError.PARTY_CANNOT_INVITE_SELF.exception()
            self.invite_checks(room, target)
            self.invite_abuse_checks(user, target)
            pending = self.session.scalars(select(PartyInvitation).where(
                PartyInvitation.room_id == room.id, PartyInvitation.invitee_id == target.id,
                PartyInvitation.status == 'pending'))
            if any(self.invitation_data(row)['status'] == 'pending' for row in pending):
                raise HttpError.PARTY_INVITATION_DUPLICATED.exception()
        except HTTPException as exc:
            result['invite_disabled_reason'] = exc.detail
            retry = (exc.headers or {}).get('Retry-After')
            result['retry_after'] = int(retry) if retry else None
        else:
            result['can_invite'], result['invite_disabled_reason'] = True, None
        return result

    def reports(self, user, limit, offset):
        self.admin(user)
        return [{'id': str(row.id), 'user_id': str(row.user_id), 'message_id': str(row.message_id),
                 'reason': row.reason, 'detail': row.detail, 'create_time': row.create_time.isoformat(),
                 'message': self.message_data(self.session.get(ChatMessage, row.message_id))}
                for row in self.session.scalars(select(ChatReport).order_by(
                    ChatReport.create_time.desc(), ChatReport.id.desc()).limit(limit).offset(offset))]

    def room_state(self, room):
        count = self.session.scalar(select(func.count()).select_from(PartyMember).where(
            PartyMember.room_id == room.id, PartyMember.status == 'joined'))
        return {'id': str(room.id), 'name': room.name, 'member_count': count,
                'max_members': room.max_members, 'is_locked': room.is_locked,
                'closed': room.closed_at is not None,
                'can_join': room.closed_at is None and not room.is_locked and count < room.max_members}

    def invitation_data(self, invitation):
        room = self.session.get(PartyRoom, invitation.room_id)
        state = self.room_state(room)
        status = invitation.status
        status_reason = invitation.status_reason
        if status == 'pending':
            target = self.target(invitation.invitee_id)
            member = self.session.scalar(select(PartyMember).where(
                PartyMember.room_id == room.id, PartyMember.user_email == target.user_email))
            if invitation.expires_at <= utc_now():
                status = 'expired'
            elif state['closed']:
                status = 'revoked'
                status_reason = 'room_closed'
            elif member is not None and member.status == 'kicked':
                status = 'revoked'
                status_reason = 'member_kicked'
            elif (member is not None and member.joined_at > invitation.create_time) or self.current_room(target) is not None:
                status = 'revoked'
                status_reason = 'already_joined'
            elif state['member_count'] >= state['max_members']:
                status = 'revoked'
                status_reason = 'room_full'
        return {'id': str(invitation.id), 'invitation_id': str(invitation.id),
                'notification_tab': 'party', 'room_id': str(invitation.room_id), 'inviter': self.public_user(invitation.inviter_id),
                'invitee_user_id': str(invitation.invitee_id), 'status': status,
                'status_reason': status_reason,
                'expires_at': invitation.expires_at.isoformat(), 'party': state}

    def reconcile_room(self, room):
        # All invitation state changes use the existing party room row lock.
        state = self.room_state(room)
        pending = list(self.session.scalars(select(PartyInvitation).where(
            PartyInvitation.room_id == room.id, PartyInvitation.status == 'pending')))
        for invitation in pending:
            target = self.target(invitation.invitee_id)
            member = self.session.scalar(select(PartyMember).where(
                PartyMember.room_id == room.id, PartyMember.user_email == target.user_email))
            status = reason = None
            if invitation.expires_at <= utc_now():
                status = 'expired'
            elif state['closed']:
                status = 'revoked'
                reason = 'room_closed'
            elif member is not None and member.status == 'kicked':
                status = 'revoked'
                reason = 'member_kicked'
            elif (member is not None and member.joined_at > invitation.create_time) or self.current_room(target) is not None:
                status = 'revoked'
                reason = 'already_joined'
            elif state['member_count'] >= state['max_members']:
                status = 'revoked'
                reason = 'room_full'
            if status:
                invitation.status, invitation.status_reason = status, reason
                invitation.update_time = utc_now()
        self.session.flush()

    def invitations(self, user, status='pending'):
        filters = [or_(PartyInvitation.invitee_id == user.id, PartyInvitation.inviter_id == user.id)]
        # Include stored pending rows when filtering terminal effective states.
        if status:
            filters.append(PartyInvitation.status.in_([status, 'pending']))
        rows = [self.invitation_data(row) for row in self.session.scalars(
            select(PartyInvitation).where(*filters).order_by(
                (PartyInvitation.status == 'pending').desc(),
                PartyInvitation.create_time.desc(), PartyInvitation.id.desc()).limit(500))]
        return [row for row in rows if status is None or row['status'] == status]

    def invite_checks(self, room, target):
        if room.closed_at is not None:
            raise HttpError.PARTY_ROOM_CLOSED.exception()
        if room.is_locked:
            raise HttpError.PARTY_ROOM_LOCKED.exception()
        member = self.session.scalar(select(PartyMember).where(
            PartyMember.room_id == room.id, PartyMember.user_email == target.user_email))
        if member and member.status == 'kicked':
            raise HttpError.PARTY_MEMBER_KICKED.exception()
        if self.current_room(target) is not None:
            raise HttpError.PARTY_ALREADY_JOINED.exception()
        if len(self.party._joined(room.id)) >= room.max_members:
            raise HttpError.PARTY_ROOM_FULL.exception()
        return member

    def create_invitation(self, user, data):
        if user.id == data.invitee_user_id:
            raise HttpError.PARTY_CANNOT_INVITE_SELF.exception()
        target = self.target(data.invitee_user_id)
        room = self.session.scalar(select(PartyRoom).where(PartyRoom.id == data.room_id).with_for_update())
        if room is None:
            raise HttpError.ROOM_NOT_FOUND.exception()
        self.party._owner(room.id, user.user_email)
        self.lock_invite_users(user.id, target.id)
        self.invite_checks(room, target)
        self.invite_abuse_checks(user, target)
        self.reconcile_room(room)
        duplicate = self.session.scalar(select(PartyInvitation.id).where(
            PartyInvitation.room_id == room.id, PartyInvitation.invitee_id == target.id,
            PartyInvitation.status == 'pending'))
        if duplicate:
            raise HttpError.PARTY_INVITATION_DUPLICATED.exception()
        # Bounded active inbox makes reconnect and room-state reconciliation bounded.
        active = self.session.scalar(select(func.count()).select_from(PartyInvitation).where(
            PartyInvitation.invitee_id == target.id, PartyInvitation.status == 'pending',
            PartyInvitation.expires_at > utc_now()))
        if active >= 50:
            raise HttpError.PARTY_INVITATION_LIMIT.exception(headers={'Retry-After': '60'})
        now = self.session.scalar(select(func.clock_timestamp()))
        invitation = PartyInvitation(id=uuid4(), room_id=room.id, inviter_id=user.id,
            invitee_id=target.id, status='pending', status_reason=None,
            expires_at=now + timedelta(minutes=10),
            create_time=now, update_time=now)
        self.session.add(invitation)
        self.session.flush()
        self.queue('party_invitation_created', {'invitation_id': str(invitation.id)})
        self.queue('party_notifications_updated', {'user_id': str(target.id)})
        return self.invitation_data(invitation)

    def handle_invitation(self, user, invitation_id, action):
        invitation = self.session.get(PartyInvitation, invitation_id)
        if invitation is None:
            raise HttpError.PARTY_INVITATION_NOT_FOUND.exception()
        # Never expose another recipient's invitation, even if the UUID is known.
        if action != 'revoke' and invitation.invitee_id != user.id:
            raise HttpError.PARTY_INVITATION_FORBIDDEN.exception()
        room = self.session.scalar(select(PartyRoom).where(
            PartyRoom.id == invitation.room_id).with_for_update())
        self.lock_invite_users(invitation.inviter_id, invitation.invitee_id)
        self.session.refresh(invitation)
        if action == 'revoke' and invitation.inviter_id != user.id:
            try:
                self.party._owner(room.id, user.user_email)
            except HTTPException:
                raise HttpError.PARTY_INVITATION_FORBIDDEN.exception() from None
        if invitation.expires_at <= utc_now() or invitation.status == 'expired':
            raise HttpError.PARTY_INVITATION_EXPIRED.exception()
        if invitation.status != 'pending':
            raise HttpError.PARTY_INVITATION_ALREADY_HANDLED.exception()
        if action == 'accept':
            self.invite_receiver_checks(self.target(invitation.inviter_id), user)
            member = self.invite_checks(room, user)
            if member is not None and member.joined_at > invitation.create_time:
                raise HttpError.PARTY_INVITATION_ALREADY_HANDLED.exception()
            joined = self.party._joined(room.id)
            now = utc_now()
            if member is None:
                member = PartyMember(id=uuid4(), room_id=room.id,
                    user_email=user.user_email, create_time=now)
                self.session.add(member)
            member.nickname = self.party._nickname(self.party._account(user.user_email), None)
            member.color = self.party._color(joined, member.color)
            member.role, member.status, member.left_at = 'member', 'joined', None
            member.joined_at = member.update_time = now
            room.empty_since, room.update_time = None, now
            invitation.status, invitation.status_reason, invitation.update_time = 'accepted', None, now
            self.session.info['chat_party_room_v3'] = room.id
            snapshot = self.party._snapshot(room, member)
            self.reconcile_room(room)
            self.queue('party_invitation_updated', {'invitation_id': str(invitation.id)})
            self.queue('party_notifications_updated', {'user_id': str(invitation.invitee_id)})
            return snapshot.model_dump(mode='json')
        invitation.status = 'rejected' if action == 'reject' else 'revoked'
        invitation.status_reason = None if action == 'reject' else 'cancelled'
        invitation.update_time = self.session.scalar(select(func.clock_timestamp()))
        self.session.flush()
        self.queue('party_invitation_updated', {'invitation_id': str(invitation.id)})
        self.queue('party_notifications_updated', {'user_id': str(invitation.invitee_id)})
        return self.invitation_data(invitation)

    def connect_session(self, user, connection_id):
        timestamp = utc_now()
        self.session.add(ChatConnection(
            id=UUID(connection_id), user_id=user.id, connected_at=timestamp,
            last_seen_at=timestamp, expires_at=timestamp + timedelta(seconds=90),
        ))

    def touch_session(self, user, connection_id):
        timestamp = utc_now()
        self.session.execute(update(ChatConnection).where(
            ChatConnection.id == UUID(connection_id), ChatConnection.user_id == user.id,
            ChatConnection.disconnected_at.is_(None), ChatConnection.expires_at > timestamp,
        ).values(last_seen_at=timestamp, expires_at=timestamp + timedelta(seconds=90)))

    def disconnect_session(self, connection_id):
        timestamp = utc_now()
        self.session.execute(update(ChatConnection).where(
            ChatConnection.id == UUID(connection_id), ChatConnection.disconnected_at.is_(None),
        ).values(disconnected_at=timestamp, disconnect_reason='closed'))

    def expire_sessions(self):
        self.session.execute(update(ChatConnection).where(
            ChatConnection.disconnected_at.is_(None), ChatConnection.expires_at <= utc_now(),
        ).values(disconnected_at=ChatConnection.expires_at, disconnect_reason='expired'))

    def connection_history(self, user, online_only=False, limit=50, offset=0):
        self.admin(user)
        timestamp = utc_now()
        query = select(ChatConnection, ChatUser.id, User.nickname).join(
            ChatUser, ChatUser.id == ChatConnection.user_id,
        ).join(User, User.email == ChatUser.user_email)
        if online_only:
            query = query.where(ChatConnection.disconnected_at.is_(None),
                                ChatConnection.expires_at > timestamp)
        rows = self.session.execute(query.order_by(
            ChatConnection.connected_at.desc(), ChatConnection.id.desc(),
        ).limit(limit).offset(offset))
        return [{'id': str(row.id), 'user': {'id': str(user_id), 'nickname': nickname or '플레이어'},
                 'connected_at': row.connected_at, 'last_seen_at': row.last_seen_at,
                 'expires_at': row.expires_at, 'disconnected_at': row.disconnected_at,
                 'disconnect_reason': row.disconnect_reason,
                 'online': row.disconnected_at is None and row.expires_at > timestamp}
                for row, user_id, nickname in rows]

    def online_users(self):
        from .store import get_chat_store
        store = self.limiter if self.limiter is not None else get_chat_store()
        try:
            ids = [UUID(value) for value in store.online_user_ids()]
        except RedisError:
            raise HttpError.CHAT_PRESENCE_UNAVAILABLE.exception() from None
        if not ids:
            return []
        rows = self.session.execute(select(ChatUser.id, User.nickname).join(
            User, User.email == ChatUser.user_email,
        ).where(ChatUser.id.in_(ids)))
        users = [{'id': str(user_id), 'nickname': nickname or '플레이어'}
                 for user_id, nickname in rows]
        return sorted(users, key=lambda row: (row['nickname'], row['id']))

    def snapshot(self, user):
        invitations = self.invitations(user) if user is not None else []
        room_id = self.current_room(user) if user is not None else None
        lobby = self.history(user, 'lobby')
        party = self.history(user, 'party', room_id) if room_id else {'messages': [], 'next_before': None}
        return {'user': self.public_user(user.id) if user is not None else None, 'lobby': lobby['messages'], 'party': party['messages'],
                'lobby_next_before': lobby['next_before'], 'party_next_before': party['next_before'],
                'party_room_id': str(room_id) if room_id else None,
                'party_invite_preferences': self.invite_preferences(user) if user is not None else None,
                'online_users': self.online_users(), 'party_invitations': invitations, 'notifications': self.notifications(user),
                'moderation': self.moderation_state(user), 'heartbeat_interval_seconds': 30}

    def cleanup(self, limit=500):
        old_rooms = select(PartyRoom.id).where(PartyRoom.closed_at <= utc_now() - timedelta(hours=24))
        ids = select(ChatMessage.id).where(or_(
            (ChatMessage.channel == 'lobby') & (ChatMessage.create_time <= utc_now() - self.lobby_retention),
            ChatMessage.room_id.in_(old_rooms),
        )).limit(limit)
        self.session.execute(delete(ChatMessage).where(ChatMessage.id.in_(ids)))
        policy = get_invite_policy()
        retention = timedelta(seconds=max(7 * 86400, policy.sender_window_seconds, policy.rejection_cooldown_seconds))
        invitations = select(PartyInvitation.id).where(
            PartyInvitation.expires_at <= utc_now() - retention,
            PartyInvitation.update_time <= utc_now() - retention).limit(limit)
        self.session.execute(delete(PartyInvitation).where(PartyInvitation.id.in_(invitations)))

    def reconcile_batch(self, after_id=None, limit=100):
        room_ids = select(PartyInvitation.room_id).where(
            PartyInvitation.status == 'pending').distinct()
        query = select(PartyRoom).where(PartyRoom.id.in_(room_ids))
        if after_id is not None:
            query = query.where(PartyRoom.id > after_id)
        rooms = list(self.session.scalars(query.order_by(PartyRoom.id).limit(limit)
            .with_for_update(skip_locked=True)))
        for room in rooms:
            self.reconcile_room(room)
        return rooms[-1].id if len(rooms) == limit else None
