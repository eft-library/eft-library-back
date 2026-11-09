"""Read source modding relationships without inventing mounting trees or stat formulas."""
from sqlalchemy import text

from util.http_exceptions import HttpError


# All interpolated SQL fragments are internal constants; request values are bound.
ITEM_JSON = """jsonb_build_object(
    'id', i.id, 'name_en', i.name_en, 'name_ko', i.name_ko, 'name_ja', i.name_ja,
    'normalized_name', i.normalized_name, 'image', i.image, 'weight', i.weight,
    'width', i.width, 'height', i.height,
    'slot_count', (select count(*) from item_slots s where s.item_id=i.id),
    'mod_properties', (select to_jsonb(m)-'item_id' from item_mod_properties m where m.item_id=i.id)
)"""
CATEGORY_JSON = """jsonb_build_object(
    'id', c.id, 'parent_id', c.parent_id, 'name_key', c.name_key,
    'name_en', c.name_en, 'name_ko', c.name_ko, 'name_ja', c.name_ja,
    'normalized_name', c.normalized_name
)"""
WEAPON_CONDITION = """exists (
    select 1 from weapon_items w where w.item_id=i.id
) and exists (
    select 1 from item_category_memberships cm join item_categories c on c.id=cm.category_id
    where cm.item_id=i.id and c.normalized_name='weapon'
)"""
SEARCH_CONDITION = """(:word='' or
    strpos(lower(coalesce(i.name_en,'')),lower(:word))>0 or
    strpos(lower(coalesce(i.name_ko,'')),lower(:word))>0 or
    strpos(lower(coalesce(i.name_ja,'')),lower(:word))>0 or
    strpos(lower(coalesce(i.normalized_name,'')),lower(:word))>0 or i.id=:word)"""
PRESET_COLUMNS = """p.base_item_id, p.is_default, p.ergonomics,
    p.recoil_vertical, p.recoil_horizontal, p.moa, p.collected_at, p.update_time"""


class ModdingService:
    @staticmethod
    def require_item(session, item_id, weapon=False):
        condition = 'i.id=:id' + (' and ' + WEAPON_CONDITION if weapon else '')
        item = session.execute(text(f'select {ITEM_JSON} from items i where {condition}'),
                               {'id': item_id}).scalar_one_or_none()
        if item is None:
            error = HttpError.MODDING_WEAPON_NOT_FOUND if weapon else HttpError.MODDING_ITEM_NOT_FOUND
            raise error.exception()
        return item

    @staticmethod
    def page(session, source, params, projection, page, page_size, key):
        total = session.execute(text('select count(*) ' + source), params).scalar_one()
        rows = session.execute(text(f"select {projection} {source} "
                                    "order by i.name_en nulls last,i.id limit :limit offset :offset"),
                               {**params,'limit':page_size,'offset':(page-1)*page_size}).mappings()
        return {'total':total,'page':page,'page_size':page_size,key:[dict(row) for row in rows]}

    @staticmethod
    def weapons(session, word, page, page_size):
        source = f'from items i where {WEAPON_CONDITION} and {SEARCH_CONDITION}'
        projection = f"""{ITEM_JSON} as item,
            (select to_jsonb(w)-'item_id' from weapon_items w where w.item_id=i.id) as weapon_properties,
            (select count(*) from weapon_preset_links l where l.weapon_item_id=i.id) as preset_count"""
        return ModdingService.page(session,source,{'word':word.strip()},projection,page,page_size,'weapons')

    @staticmethod
    def item_detail(session, item_id):
        item = ModdingService.require_item(session,item_id)
        params = {'id':item_id}
        categories = session.execute(text(f"""
            select {CATEGORY_JSON} as category, cm.sort_order
            from item_category_memberships cm join item_categories c on c.id=cm.category_id
            where cm.item_id=:id order by cm.sort_order,c.id
        """),params).mappings().all()
        slots = {row['slot_id']:dict(row,filters={
            'allowed_items':[], 'excluded_items':[], 'allowed_categories':[], 'excluded_categories':[]
        }) for row in session.execute(text('select * from item_slots where item_id=:id order by sort_order,slot_id'),params).mappings()}
        if slots:
            for row in session.execute(text(f"""
                select f.slot_id,f.filter_type,f.sort_order,{ITEM_JSON} as item
                from item_slot_item_filters f join items i on i.id=f.target_item_id
                where f.item_id=:id order by f.slot_id,f.filter_type,f.sort_order
            """),params).mappings():
                slots[row['slot_id']]['filters'][row['filter_type']+'_items'].append(
                    {'sort_order':row['sort_order'],'item':row['item']})
            for row in session.execute(text(f"""
                select f.slot_id,f.filter_type,f.sort_order,{CATEGORY_JSON} as category
                from item_slot_category_filters f join item_categories c on c.id=f.category_id
                where f.item_id=:id order by f.slot_id,f.filter_type,f.sort_order
            """),params).mappings():
                slots[row['slot_id']]['filters'][row['filter_type']+'_categories'].append(
                    {'sort_order':row['sort_order'],'category':row['category']})
        conflicting_items = [dict(row) for row in session.execute(text(f"""
            select x.sort_order,{ITEM_JSON} as item
            from item_conflicting_items x join items i on i.id=x.conflicting_item_id
            where x.item_id=:id order by x.sort_order
        """),params).mappings()]
        conflicting_categories = [dict(row) for row in session.execute(text(f"""
            select x.sort_order,{CATEGORY_JSON} as category
            from item_conflicting_categories x join item_categories c on c.id=x.category_id
            where x.item_id=:id order by x.sort_order
        """),params).mappings()]
        # One raw conflict entry can resolve to zero or several owner/slot pairs.
        conflicting_slots = [dict(row) for row in session.execute(text("""
            select x.sort_order,x.conflicting_slot_id as slot_id,
                   coalesce((select jsonb_agg(jsonb_build_object(
                       'item_id',s.item_id,'slot_id',s.slot_id,'name_id',s.name_id,
                       'name_key',s.name_key,'name_en',s.name_en,'name_ko',s.name_ko,'name_ja',s.name_ja
                   ) order by s.item_id) from item_slots s where s.slot_id=x.conflicting_slot_id),'[]'::jsonb) as definitions
            from item_conflicting_slots x where x.item_id=:id order by x.sort_order
        """),params).mappings()]
        weapon = session.execute(text("select to_jsonb(w)-'item_id' from weapon_items w where item_id=:id"),params).scalar_one_or_none()
        # weapon_items currently also contains some ammo; never present these as gun stats.
        is_weapon = session.execute(text(f'select exists(select 1 from items i where i.id=:id and {WEAPON_CONDITION})'),params).scalar_one()
        ammo = [row[0] for row in session.execute(text(f"""
            select {ITEM_JSON} from weapon_allowed_ammo a join items i on i.id=a.ammo_item_id
            where a.item_id=:id order by i.name_en nulls last,i.id
        """),params)] if is_weapon else []
        return {'item':item,'categories':[dict(row) for row in categories],
                'weapon_properties':weapon if is_weapon else None,'allowed_ammo':ammo,
                'slots':list(slots.values()),
                'conflicts':{'items':conflicting_items,'slots':conflicting_slots,'categories':conflicting_categories}}

    @staticmethod
    def candidates(session, item_id, slot_id, word, page, page_size):
        ModdingService.require_item(session,item_id)
        if session.execute(text('select 1 from item_slots where item_id=:owner and slot_id=:slot'),
                           {'owner':item_id,'slot':slot_id}).scalar_one_or_none() is None:
            raise HttpError.MODDING_SLOT_NOT_FOUND.exception()
        # These are source slot-filter candidates only. Loadout conflicts and required
        # slots are intentionally not evaluated without an instance-level build model.
        conditions = []
        for filter_type in ('allowed','excluded'):
            conditions.append(f"""(
                exists(select 1 from item_slot_item_filters f
                    where f.item_id=:owner and f.slot_id=:slot
                    and f.filter_type='{filter_type}' and f.target_item_id=i.id)
                or exists(select 1 from item_slot_category_filters f
                    join item_category_memberships cm on cm.category_id=f.category_id
                    where f.item_id=:owner and f.slot_id=:slot
                    and f.filter_type='{filter_type}' and cm.item_id=i.id)
            )""")
        source = f'from items i where {conditions[0]} and not {conditions[1]} and {SEARCH_CONDITION}'
        result = ModdingService.page(session,source,{'owner':item_id,'slot':slot_id,'word':word.strip()},
                                     f'{ITEM_JSON} as item',page,page_size,'candidates')
        return {'item_id':item_id,'slot_id':slot_id,'validation_scope':'slot_filters_only',**result}

    @staticmethod
    def weapon_presets(session, weapon_id, page, page_size):
        ModdingService.require_item(session,weapon_id,weapon=True)
        params={'id':weapon_id}
        source='from weapon_preset_links l join item_presets p on p.preset_item_id=l.preset_item_id join items i on i.id=p.preset_item_id where l.weapon_item_id=:id'
        total=session.execute(text('select count(*) '+source),params).scalar_one()
        rows=session.execute(text(f"""select {ITEM_JSON} as item,{PRESET_COLUMNS},
            jsonb_build_object('is_listed',l.is_listed,'is_default_reference',l.is_default_reference,
                              'sort_order',l.sort_order) as link
            {source} order by l.is_default_reference desc,l.sort_order nulls last,i.id
            limit :limit offset :offset"""),{**params,'limit':page_size,'offset':(page-1)*page_size}).mappings()
        return {'weapon_item_id':weapon_id,'total':total,'page':page,'page_size':page_size,
                'presets':[dict(row) for row in rows]}

    @staticmethod
    def preset_detail(session, preset_id):
        params={'id':preset_id}
        preset=session.execute(text(f"""select {ITEM_JSON} as item,{PRESET_COLUMNS}
            from item_presets p join items i on i.id=p.preset_item_id where p.preset_item_id=:id"""),params).mappings().one_or_none()
        if preset is None:
            raise HttpError.MODDING_PRESET_NOT_FOUND.exception()
        components=[dict(row) for row in session.execute(text(f"""
            select x.component_index,x.quantity,x.attributes,{ITEM_JSON} as item
            from item_preset_components x join items i on i.id=x.item_id
            where x.preset_item_id=:id order by x.component_index
        """),params).mappings()]
        links=[dict(row) for row in session.execute(text("""
            select weapon_item_id,is_listed,is_default_reference,sort_order
            from weapon_preset_links where preset_item_id=:id order by weapon_item_id
        """),params).mappings()]
        return {'preset':dict(preset),'components':components,'weapon_links':links,
                'composition_type':'flat_source_list'}
