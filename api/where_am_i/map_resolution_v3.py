"""Resolve desktop map input using active DB aliases without changing raw input."""
from sqlalchemy import text

from database import V3Database
from .desktop_contract_v3 import normalize_alias_v3


def resolve_map_slug_v3(requested_map_v3):
    if requested_map_v3 is None:
        return None
    try:
        normalized_v3 = normalize_alias_v3(requested_map_v3)
    except ValueError:
        return None
    with V3Database.SessionLocal() as session_v3:
        slug_v3 = session_v3.execute(text('''
            select map_slug from where_am_i_map_aliases
            where is_active is true
              and replace(lower(btrim(alias)), '_preset', '') = :alias
        '''), {'alias':normalized_v3}).scalar_one_or_none()
        if slug_v3 is None:
            # Clients can also send a canonical slug present in active DB aliases.
            slug_v3 = session_v3.execute(text('''
                select map_slug from where_am_i_map_aliases
                where is_active is true and map_slug = :slug
                limit 1
            '''), {'slug': normalized_v3}).scalar_one_or_none()
    return slug_v3
