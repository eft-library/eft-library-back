"""Load only the preset's source definitions in the caller's read-only snapshot."""
from sqlalchemy import bindparam, text

from api.modding.reconstruction import MAX_NODES, build_graph, reconstruct
from api.modding.service import WEAPON_CONDITION


def reconstruct_preset(session, preset_id, base_item_id, components):
    normalized=[{'component_index':c['component_index'],'item_id':c['item']['id'],
                 'quantity':c['quantity'],'attributes':c['attributes']} for c in components]
    ids=sorted({base_item_id}|{c['item_id'] for c in normalized})
    is_weapon=session.execute(text(f'select 1 from items i where i.id=:id and {WEAPON_CONDITION}'),
                              {'id':base_item_id}).scalar_one_or_none() is not None
    data={'weapon_ids':[base_item_id] if is_weapon else []}
    # Huge quantities are rejected before expansion or loading slot/filter definitions.
    too_large=sum(c['quantity'] for c in normalized)>MAX_NODES
    for table,key in [('items','id'),('item_slots','item_id'),('item_category_memberships','item_id'),
                      ('item_slot_item_filters','item_id'),('item_slot_category_filters','item_id'),
                      ('item_conflicting_items','item_id'),('item_conflicting_categories','item_id'),
                      ('item_conflicting_slots','item_id')]:
        if too_large or not is_weapon:
            data[table]=[]
            continue
        query=text(f'select * from {table} where {key} in :ids').bindparams(bindparam('ids',expanding=True))
        data[table]=[dict(row) for row in session.execute(query,{'ids':ids}).mappings()]
    data['ammunition_ids']=set()
    if not too_large and is_weapon:
        query=text('''select distinct cm.item_id from item_category_memberships cm
            join item_categories c on c.id=cm.category_id
            where cm.item_id in :ids and c.normalized_name='ammo' ''').bindparams(bindparam('ids',expanding=True))
        data['ammunition_ids'].update(session.execute(query,{'ids':ids}).scalars())
    references=sorted({r['conflicting_slot_id'] for r in data['item_conflicting_slots']})
    data['known_slot_ids']={r['slot_id'] for r in data['item_slots']}
    if references:
        query=text('select distinct slot_id from item_slots where slot_id in :ids').bindparams(bindparam('ids',expanding=True))
        data['known_slot_ids'].update(session.execute(query,{'ids':references}).scalars())
    return reconstruct(preset_id,base_item_id,normalized,build_graph(data))
