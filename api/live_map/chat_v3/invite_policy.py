"""Shared V3 invitation policy; configure identically on every application worker."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class InvitePolicyV3:
    sender_limit: int = 3
    sender_window_seconds: int = 60
    rejection_cooldown_seconds: int = 600


def get_invite_policy_v3():
    values = {
        'sender_limit': int(os.getenv('V3_PARTY_INVITE_SENDER_LIMIT', '3')),
        'sender_window_seconds': int(os.getenv('V3_PARTY_INVITE_WINDOW_SECONDS', '60')),
        'rejection_cooldown_seconds': int(os.getenv('V3_PARTY_INVITE_REJECTION_COOLDOWN_SECONDS', '600')),
    }
    if any(value <= 0 for value in values.values()):
        raise ValueError('V3 party invitation policy values must be positive')
    return InvitePolicyV3(**values)
