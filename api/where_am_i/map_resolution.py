"""Resolve desktop map input using active DB aliases without changing raw input."""
from sqlalchemy import text

from database import Database
from .desktop_contract import normalize_alias


def resolve_map_slug(requested_map):
    if requested_map is None:
        return None
    try:
        normalized = normalize_alias(requested_map)
    except ValueError:
        return None
    with Database.SessionLocal() as session:
        slug = session.execute(text('''
            select map_slug from where_am_i_map_aliases
            where is_active is true
              and replace(lower(btrim(alias)), '_preset', '') = :alias
        '''), {'alias':normalized}).scalar_one_or_none()
        if slug is None:
            # Clients can also send a canonical slug present in active DB aliases.
            slug = session.execute(text('''
                select map_slug from where_am_i_map_aliases
                where is_active is true and map_slug = :slug
                limit 1
            '''), {'slug': normalized}).scalar_one_or_none()
    return slug
