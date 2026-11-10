"""Bounded constraint search over preset instances. Results are inferred, never source trees."""
from collections import Counter, defaultdict
from time import monotonic
import json

MAX_NODES = 200
MAX_STATES = 20000
MAX_SECONDS = 0.25
MAX_SOLUTIONS = 3


def build_graph(data):
    """Build a pure solver input from normalized source rows (also usable in offline tests)."""
    items = {r['id'] for r in data['items']}
    categories = defaultdict(set)
    for row in data['item_category_memberships']:
        categories[row['item_id']].add(row['category_id'])
    slots = defaultdict(list)
    slot_index = {}
    for row in data['item_slots']:
        slot = {'slot_id':row['slot_id'],'required':row['required'],
                'allowed_items':set(),'excluded_items':set(),
                'allowed_categories':set(),'excluded_categories':set()}
        slots[row['item_id']].append(slot)
        slot_index[(row['item_id'],row['slot_id'])] = slot
    for row in data['item_slot_item_filters']:
        slot_index[(row['item_id'],row['slot_id'])][row['filter_type']+'_items'].add(row['target_item_id'])
    for row in data['item_slot_category_filters']:
        slot_index[(row['item_id'],row['slot_id'])][row['filter_type']+'_categories'].add(row['category_id'])
    conflicts = {}
    for name,column in [('items','conflicting_item_id'),('categories','category_id'),('slots','conflicting_slot_id')]:
        target = defaultdict(set)
        for row in data['item_conflicting_'+name]:
            target[row['item_id']].add(row[column])
        conflicts[name] = target
    for value in slots.values():
        value.sort(key=lambda s:s['slot_id'])
    return {'items':items,'categories':categories,'slots':slots,'conflicts':conflicts,
            'known_slot_ids':set(data.get('known_slot_ids', [r['slot_id'] for r in data['item_slots']])),
            'weapon_ids':set(data['weapon_ids']), 'ammunition_ids':set(data.get('ammunition_ids',()))}


def allowed(graph, parent_item, slot, child_item):
    categories = graph['categories'].get(child_item,set())
    return ((child_item in slot['allowed_items'] or bool(categories & slot['allowed_categories']))
            and child_item not in slot['excluded_items']
            and not categories & slot['excluded_categories'])


def pair_conflict(graph, first, second):
    conflicts = graph['conflicts']
    if second in conflicts['items'].get(first,set()) or first in conflicts['items'].get(second,set()):
        return 'ITEM_CONFLICT'
    if (graph['categories'].get(second,set()) & conflicts['categories'].get(first,set())
            or graph['categories'].get(first,set()) & conflicts['categories'].get(second,set())):
        return 'CATEGORY_CONFLICT'
    return None


def reconstruct(preset_id, base_item_id, components, graph, *, max_states=MAX_STATES,
                max_seconds=MAX_SECONDS, max_solutions=MAX_SOLUTIONS, max_nodes=MAX_NODES):
    started = monotonic()
    issues = []
    result = {'method':'inferred','algorithm_version':1,'is_source_tree':False,
              'validation_scope':'stored_slot_constraints','status':'unavailable','can_import':False,
              'requires_confirmation':True,'is_unique':None,'search_complete':True,
              'solution_count_lower_bound':0,'states_examined':0,'candidate_trees':[],
              'partial_tree':None,'unplaced_components':[], 'issues':issues,'issues_truncated':False}
    rows = sorted(components,key=lambda c:c['component_index'])
    result['unplaced_components']=[{k:r.get(k) for k in ('component_index','item_id','quantity','attributes')} for r in rows]
    def issue(code, **details):
        value={'code':code,**details}
        if value in issues:return
        if len(issues)<50:
            issues.append(value)
        else:
            result['issues_truncated']=True
    if base_item_id not in graph['weapon_ids']:
        issue('UNSUPPORTED_BASE_ITEM',item_id=base_item_id)
        return result
    if not rows or any(type(r['quantity']) is not int or r['quantity']<=0 for r in rows):
        issue('INVALID_COMPONENTS')
        return result
    if sum(r['quantity'] for r in rows)>max_nodes:
        issue('NODE_LIMIT')
        result.update(status='search_limited',search_complete=False)
        return result
    instances=[]
    for row in rows:
        for unit in range(row['quantity']):
            instances.append({'node_id':f"c{row['component_index']}-u{unit}",
                'item_id':row['item_id'],'attributes':row.get('attributes'),
                'source_component_index':row['component_index'],'source_unit_index':unit})
    roots=[i for i,n in enumerate(instances) if n['item_id']==base_item_id]
    if len(roots)!=1:
        issue('ROOT_COMPONENT_COUNT',item_id=base_item_id)
        return result
    root=roots[0]
    missing={n['item_id'] for n in instances}-graph['items']
    if missing:
        for item in sorted(missing):issue('MISSING_ITEM_DEFINITION',item_id=item)
        return result
    ids=[n['item_id'] for n in instances]
    blocked=set().union(*(graph['conflicts']['slots'].get(item,set()) for item in ids))
    for slot in sorted(blocked-graph['known_slot_ids']):
        issue('UNRESOLVED_CONFLICT_SLOT',slot_id=slot)
    conflicts=[]
    for i in range(len(instances)):
        for j in range(i):
            code=pair_conflict(graph,ids[i],ids[j])
            if code:
                conflicts.append((i,j,code))
                issue(code,node_id=instances[i]['node_id'],other_node_id=instances[j]['node_id'])
    domains={}
    required=set()
    domain_steps=0
    for parent,item_id in enumerate(ids):
        for slot in graph['slots'].get(item_id,[]):
            key=(parent,slot['slot_id'])
            if slot['required']:required.add(key)
            if slot['slot_id'] in blocked:continue
            for child,child_item in enumerate(ids):
                domain_steps+=1
                if domain_steps%256==0 and monotonic()-started>=max_seconds:
                    issue('SEARCH_LIMIT')
                    result.update(status='search_limited',search_complete=False)
                    return result
                if child!=root and child!=parent and allowed(graph,item_id,slot,child_item):
                    domains.setdefault(child,[]).append(key)
    for child in range(len(instances)):
        if child!=root:
            domains.setdefault(child,[])
            domains[child].sort()
    no_domain=[i for i,values in domains.items() if not values]
    unreachable_components=set()
    for i in no_domain:
        component=instances[i]['source_component_index']
        if component not in unreachable_components:
            issue('AMMUNITION_WITHOUT_SLOT' if instances[i]['item_id'] in graph['ammunition_ids'] else 'SLOT_UNREACHABLE',
                  node_id=instances[i]['node_id'])
            unreachable_components.add(component)
    assignments={}
    occupied=set()
    solutions=[]
    signatures=set()
    truncated=False
    limit_reason=None
    best={}

    def nodes_for(mapping):
        connected={root}
        while True:
            more={child for child,(parent,_) in mapping.items() if parent in connected}-connected
            if not more:break
            connected.update(more)
        nodes=[]
        for i,node in enumerate(instances):
            if i not in connected:continue
            parent,slot=mapping.get(i,(None,None))
            nodes.append({**node,'parent_node_id':instances[parent]['node_id'] if parent is not None else None,'slot_id':slot})
        return nodes

    def canonical(mapping):
        children=defaultdict(list)
        for child,(parent,slot) in mapping.items():children[parent].append((slot,child))
        def visit(index):
            node=instances[index]
            return (node['item_id'],json.dumps(node['attributes'],sort_keys=True,separators=(',',':')),
                    tuple(sorted((slot,visit(child)) for slot,child in children[index])))
        return visit(root)

    def acyclic(child,parent):
        seen={child}
        while True:
            if parent in seen:return False
            seen.add(parent)
            if parent not in assignments:return True
            parent=assignments[parent][0]

    def search():
        nonlocal truncated,best,limit_reason
        if result['states_examined']>=max_states or monotonic()-started>=max_seconds:
            truncated=True;limit_reason='SEARCH_LIMIT';return
        result['states_examined']+=1
        if len(assignments)>len(best):
            # Only connected nodes are used when producing a partial preview below.
            best=dict(assignments)
        if len(assignments)==len(instances)-1:
            if not required<=occupied:return
            signature=canonical(assignments)
            if signature not in signatures:
                signatures.add(signature)
                solutions.append({'nodes':nodes_for(assignments)})
            return
        choices={}
        probes=0
        for child,values in domains.items():
            if child in assignments:continue
            available=[]
            for key in values:
                probes+=1
                if probes%256==0 and monotonic()-started>=max_seconds:
                    truncated=True;limit_reason='SEARCH_LIMIT';return
                if key not in occupied and acyclic(child,key[0]):available.append(key)
            choices[child]=available
        if any(not values for values in choices.values()):return
        forced=None
        for key in sorted(required-occupied):
            capable=[child for child,values in choices.items() if key in values]
            if not capable:return
            if len(capable)==1:
                forced=(capable[0],key);break
        if forced:
            child,key=forced;options=[key]
        else:
            child=min(choices,key=lambda i:(len(choices[i]),instances[i]['node_id']))
            options=choices[child]
        for key in options:
            assignments[child]=key;occupied.add(key)
            search()
            occupied.remove(key);assignments.pop(child)
            if truncated:return
            if len(solutions)>=max_solutions:
                truncated=True;limit_reason='SOLUTION_LIMIT';return

    if not conflicts and not no_domain:
        search()
    if solutions:
        result.update(candidate_trees=solutions,can_import=True,unplaced_components=[],solution_count_lower_bound=len(solutions),
                      search_complete=not truncated,is_unique=False if len(solutions)>1 else (None if truncated else True),
                      status='ambiguous' if len(solutions)>1 else ('search_limited' if truncated else 'unique'))
        if len(solutions)>1:issue('MULTIPLE_SOLUTIONS')
        if truncated:issue(limit_reason)
        return result

    # A bounded deterministic partial preview never silently drops unmatched parts.
    # It is not importable as a complete preset and isn't claimed to be the maximal subtree.
    mapping={};mounted={root};used=set()
    partial_steps=0
    while monotonic()-started<max_seconds and partial_steps<max_states:
        progress=False
        for child in range(len(instances)):
            partial_steps+=1
            if partial_steps>=max_states or monotonic()-started>=max_seconds:break
            if child in mounted:continue
            if any(pair_conflict(graph,ids[child],ids[other]) for other in mounted):continue
            options=[]
            candidate_blocked=set().union(*(graph['conflicts']['slots'].get(ids[i],set()) for i in mounted|{child}))
            if any(slot in candidate_blocked for _,slot in used):continue
            for parent in sorted(mounted):
                for slot in graph['slots'].get(ids[parent],[]):
                    key=(parent,slot['slot_id'])
                    if key not in used and slot['slot_id'] not in candidate_blocked and allowed(graph,ids[parent],slot,ids[child]):
                        options.append((not slot['required'],parent,slot['slot_id']))
            if options:
                _,parent,slot=min(options);mapping[child]=(parent,slot)
                used.add((parent,slot));mounted.add(child);progress=True
        if not progress:break
    if not conflicts and not no_domain:
        connected_best=nodes_for(best)
        if len(connected_best)>len(mounted):
            mapping=best
            mounted={i for i,n in enumerate(instances) if n['node_id'] in {x['node_id'] for x in connected_best}}
            used={key for child,key in best.items() if child in mounted}
    nodes=nodes_for(mapping)
    used_nodes={n['node_id'] for n in nodes}
    used_counts=Counter(n['source_component_index'] for n in nodes)
    unplaced=[]
    for row in rows:
        count=row['quantity']-used_counts[row['component_index']]
        if count:
            unplaced.append({'component_index':row['component_index'],'item_id':row['item_id'],
                             'quantity':count,'attributes':row.get('attributes')})
    for parent,slot in sorted(required-used):
        if instances[parent]['node_id'] in used_nodes:
            issue('REQUIRED_SLOT_UNFILLED',node_id=instances[parent]['node_id'],slot_id=slot)
    issue('NO_COMPLETE_TREE')
    if truncated:issue(limit_reason)
    result.update(status='search_limited' if truncated else 'incomplete',search_complete=not truncated,
                  partial_tree={'nodes':nodes},unplaced_components=unplaced)
    return result
