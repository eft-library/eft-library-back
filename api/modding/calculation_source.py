"""Read normalized rows in the route's repeatable-read transaction."""
from sqlalchemy import bindparam, text
from api.modding.calculation import calculate, compatibility
from api.modding.reconstruction import build_graph
from api.modding.service import WEAPON_CONDITION
from util.http_exceptions import HttpError


def calculate_configuration(session, request):
    weapon = session.execute(text(f'''select w.* from weapon_items w join items i on i.id=w.item_id
        where w.item_id=:id and {WEAPON_CONDITION}'''), {'id':request.weapon_item_id}).mappings().one_or_none()
    if weapon is None:
        raise HttpError.MODDING_WEAPON_NOT_FOUND.exception()
    weapon = dict(weapon)
    ammo_id = request.ammo_item_id or weapon['default_ammo_item_id']
    ids = sorted({n.item_id for n in request.nodes} | ({ammo_id} if ammo_id else set()))
    def rows(table, key='item_id', selected=ids):
        query = text(f'select * from {table} where {key} in :ids').bindparams(bindparam('ids', expanding=True))
        return [dict(r) for r in session.execute(query, {'ids':selected}).mappings()]
    items = {r['id']:r for r in rows('items', 'id')}
    if any(n.item_id not in items for n in request.nodes) or (request.ammo_item_id and ammo_id not in items):
        raise HttpError.MODDING_ITEM_NOT_FOUND.exception()
    if ammo_id:
        allowed_ammo = session.execute(text('select 1 from weapon_allowed_ammo where item_id=:weapon and ammo_item_id=:ammo'),
            {'weapon':request.weapon_item_id, 'ammo':ammo_id}).scalar_one_or_none()
        if allowed_ammo is None and request.ammo_item_id:
            raise HttpError.MODDING_AMMO_NOT_ALLOWED.exception()
        if allowed_ammo is None:
            ammo_id = None
    ballistics = {r['item_id']:r for r in rows('item_ballistics')}
    ammo_rows = {r['item_id']:r for r in rows('ammo_items')}
    if any(n.item_id in ammo_rows or ballistics.get(n.item_id, {}).get('properties_type') == 'ItemPropertiesAmmo' for n in request.nodes):
        raise HttpError.MODDING_AMMO_MUST_BE_SEPARATE.exception()
    ammo = ammo_rows.get(ammo_id) if ammo_id else None
    if request.ammo_item_id and ammo is None:
        raise HttpError.MODDING_AMMO_NOT_ALLOWED.exception()
    if ammo:
        ammo['initial_speed_mps'] = ballistics.get(ammo_id, {}).get('initial_speed_mps')
    data = {table:rows(table, 'id' if table == 'items' else 'item_id') for table in (
        'item_slots', 'item_category_memberships', 'item_slot_item_filters', 'item_slot_category_filters',
        'item_conflicting_items', 'item_conflicting_categories', 'item_conflicting_slots')}
    data.update(items=list(items.values()), weapon_ids=[request.weapon_item_id])
    known = {r['slot_id'] for r in data['item_slots']}
    referenced = sorted({r['conflicting_slot_id'] for r in data['item_conflicting_slots']})
    if referenced:
        known.update(r['slot_id'] for r in rows('item_slots', 'slot_id', referenced))
    data['known_slot_ids'] = known
    mods = {r['item_id']:r for r in rows('item_mod_properties')}
    result = calculate(request.nodes, weapon, items, mods, ballistics, ammo, compatibility(request.nodes, build_graph(data)))
    result['ammo_selection'] = ('requested' if request.ammo_item_id else 'weapon_default') if ammo else 'unavailable'
    return result
