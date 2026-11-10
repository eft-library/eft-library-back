"""Constraint reconstruction, ambiguity, instance accounting and bounded proof claims."""
import copy
import unittest

from api.modding.reconstruction import build_graph, reconstruct


def source(items=('gun','receiver','sight')):
    return {'items':[{'id':i} for i in items], 'weapon_ids':['gun'],
            'item_slots':[], 'item_category_memberships':[],
            'item_slot_item_filters':[], 'item_slot_category_filters':[],
            'item_conflicting_items':[], 'item_conflicting_categories':[], 'item_conflicting_slots':[]}


def slot(data, owner, key, allowed=(), required=False, excluded=(), categories=(), excluded_categories=()):
    data['item_slots'].append({'item_id':owner,'slot_id':key,'required':required})
    for typ,items in [('allowed',allowed),('excluded',excluded)]:
        data['item_slot_item_filters'] += [{'item_id':owner,'slot_id':key,'filter_type':typ,'target_item_id':i} for i in items]
    for typ,values in [('allowed',categories),('excluded',excluded_categories)]:
        data['item_slot_category_filters'] += [{'item_id':owner,'slot_id':key,'filter_type':typ,'category_id':i} for i in values]


def components(*ids):
    return [{'component_index':n,'item_id':item,'quantity':1,'attributes':{}} for n,item in enumerate(ids)]


class PresetReconstructionTest(unittest.TestCase):
    def solve(self,data,parts,**kwargs):
        return reconstruct('preset','gun',parts,build_graph(data),**kwargs)

    def assert_complete(self,result,parts):
        self.assertTrue(result['can_import'])
        self.assertFalse(result['is_source_tree'])
        for tree in result['candidate_trees']:
            nodes=tree['nodes'];ids={n['node_id']:n for n in nodes}
            self.assertEqual(len(nodes),sum(p['quantity'] for p in parts))
            self.assertEqual(len(ids),len(nodes))
            self.assertEqual(len({(n['source_component_index'],n['source_unit_index']) for n in nodes}),len(nodes))
            roots=[n for n in nodes if n['parent_node_id'] is None]
            self.assertEqual(len(roots),1)
            self.assertEqual(roots[0]['item_id'],'gun')
            occupied=set()
            for node in nodes:
                visited=set();current=node
                while current['parent_node_id'] is not None:
                    self.assertNotIn(current['node_id'],visited)
                    visited.add(current['node_id']);current=ids[current['parent_node_id']]
                if node['parent_node_id'] is not None:
                    key=(node['parent_node_id'],node['slot_id'])
                    self.assertNotIn(key,occupied);occupied.add(key)
                row=next(p for p in parts if p['component_index']==node['source_component_index'])
                self.assertEqual(node['item_id'],row['item_id'])
                self.assertEqual(node['attributes'],row['attributes'])
                self.assertLess(node['source_unit_index'],row['quantity'])

    def test_unique_multi_level_tree_with_root_not_first(self):
        data=source();slot(data,'gun','receiver',('receiver',),True);slot(data,'receiver','rear',('sight',),True)
        parts=components('sight','gun','receiver')
        result=self.solve(data,parts);self.assert_complete(result,parts)
        self.assertEqual(result['status'],'unique')
        self.assertTrue(result['search_complete'])
        self.assertTrue(result['is_unique'])
        nodes={n['item_id']:n for n in result['candidate_trees'][0]['nodes']}
        self.assertEqual(nodes['sight']['parent_node_id'],nodes['receiver']['node_id'])

    def test_multiple_slots_produce_ambiguous_distinct_candidates(self):
        data=source();slot(data,'gun','left',('sight',));slot(data,'gun','right',('sight',))
        parts=components('gun','sight');result=self.solve(data,parts);self.assert_complete(result,parts)
        self.assertEqual(result['status'],'ambiguous')
        self.assertEqual(result['solution_count_lower_bound'],2)
        self.assertFalse(result['is_unique'])

    def test_identical_instances_do_not_create_false_ambiguity(self):
        data=source();slot(data,'gun','left',('sight',),True);slot(data,'gun','right',('sight',),True)
        parts=components('gun','sight');parts[1]['quantity']=2
        result=self.solve(data,parts);self.assert_complete(result,parts)
        self.assertEqual(result['status'],'unique')
        self.assertEqual(len(result['candidate_trees'][0]['nodes']),3)

    def test_distinct_attributes_keep_genuinely_different_layouts(self):
        data=source();slot(data,'gun','left',('sight',),True);slot(data,'gun','right',('sight',),True)
        parts=components('gun','sight','sight');parts[1]['attributes']={'mode':{'zoom':[1,4]}}
        result=self.solve(data,parts);self.assert_complete(result,parts)
        self.assertEqual(result['status'],'ambiguous')

    def test_categories_and_item_exclusions_are_applied(self):
        data=source();data['item_category_memberships']=[{'item_id':'sight','category_id':'optics'}]
        slot(data,'gun','category',categories=('optics',));slot(data,'gun','excluded-item',('sight',),excluded=('sight',))
        slot(data,'gun','excluded-category',('sight',),excluded_categories=('optics',))
        result=self.solve(data,components('gun','sight'))
        self.assertEqual(result['status'],'unique')
        self.assertEqual(result['candidate_trees'][0]['nodes'][1]['slot_id'],'category')

    def test_cycles_cannot_serve_as_a_rooted_tree(self):
        data=source();slot(data,'receiver','sight',('sight',));slot(data,'sight','receiver',('receiver',))
        result=self.solve(data,components('gun','receiver','sight'))
        self.assertFalse(result['can_import'])
        self.assertEqual(result['status'],'incomplete')
        self.assertEqual(len(result['partial_tree']['nodes']),1)
        self.assertEqual(sum(c['quantity'] for c in result['unplaced_components']),2)

    def test_required_slot_is_not_silently_ignored(self):
        data=source();slot(data,'gun','missing-required',('receiver',),True)
        result=self.solve(data,components('gun'))
        self.assertFalse(result['can_import'])
        self.assertIn('REQUIRED_SLOT_UNFILLED',{i['code'] for i in result['issues']})

    def test_required_slot_forces_choice(self):
        data=source();slot(data,'gun','optional',('sight',));slot(data,'gun','required',('sight',),True)
        result=self.solve(data,components('gun','sight'))
        self.assertEqual(result['status'],'unique')
        self.assertEqual(result['candidate_trees'][0]['nodes'][1]['slot_id'],'required')

    def test_directional_item_or_category_conflict_blocks_full_import(self):
        for kind in ('items','categories'):
            data=source();slot(data,'gun','receiver',('receiver',));slot(data,'gun','sight',('sight',))
            if kind=='items':data['item_conflicting_items']=[{'item_id':'sight','conflicting_item_id':'receiver'}]
            else:
                data['item_category_memberships']=[{'item_id':'receiver','category_id':'receiver-category'}]
                data['item_conflicting_categories']=[{'item_id':'sight','category_id':'receiver-category'}]
            with self.subTest(kind=kind):
                result=self.solve(data,components('gun','receiver','sight'))
                self.assertFalse(result['can_import'])
                self.assertIn('ITEM_CONFLICT' if kind=='items' else 'CATEGORY_CONFLICT',{i['code'] for i in result['issues']})
                self.assertEqual(len(result['partial_tree']['nodes'])+sum(x['quantity'] for x in result['unplaced_components']),3)

    def test_conflicting_slot_prevents_occupancy_but_not_empty_definition(self):
        data=source();slot(data,'gun','left',('sight',));slot(data,'gun','right',('sight',))
        data['item_conflicting_slots']=[{'item_id':'sight','conflicting_slot_id':'left'}]
        result=self.solve(data,components('gun','sight'))
        self.assertEqual(result['status'],'unique')
        self.assertEqual(result['candidate_trees'][0]['nodes'][1]['slot_id'],'right')

    def test_unresolved_slot_reference_is_explicit_warning(self):
        data=source();slot(data,'gun','sight',('sight',))
        data['item_conflicting_slots']=[{'item_id':'sight','conflicting_slot_id':'unknown-slot'}]
        result=self.solve(data,components('gun','sight'))
        self.assertTrue(result['can_import'])
        self.assertIn('UNRESOLVED_CONFLICT_SLOT',{i['code'] for i in result['issues']})

    def test_limits_never_claim_uniqueness_without_proof(self):
        data=source();slot(data,'gun','left',('sight',));slot(data,'gun','right',('sight',))
        parts=components('gun','sight')
        result=self.solve(data,parts,max_solutions=1)
        self.assertTrue(result['can_import'])
        self.assertEqual(result['status'],'search_limited')
        self.assertFalse(result['search_complete'])
        self.assertIsNone(result['is_unique'])
        for limits in ({'max_states':0},{'max_seconds':0},{'max_nodes':1}):
            with self.subTest(limits=limits):
                result=self.solve(data,parts,**limits)
                self.assertFalse(result['can_import'])
                self.assertEqual(result['status'],'search_limited')
                self.assertFalse(result['search_complete'])

    def test_ammunition_is_not_assigned_to_an_invented_magazine_slot(self):
        data=source(('gun','ammo'));data['ammunition_ids']=['ammo']
        parts=components('gun','ammo');parts[1]['quantity']=30
        result=self.solve(data,parts)
        self.assertFalse(result['can_import'])
        self.assertIn('AMMUNITION_WITHOUT_SLOT',{i['code'] for i in result['issues']})
        self.assertEqual(result['unplaced_components'][0]['quantity'],30)
        self.assertEqual(len(result['partial_tree']['nodes']),1)

    def test_missing_root_or_nonweapon_is_not_invented(self):
        data=source();slot(data,'gun','sight',('sight',))
        for parts in (components('sight'),components('gun','gun')):
            self.assertFalse(self.solve(data,parts)['can_import'])
            self.assertEqual(self.solve(data,parts)['status'],'unavailable')
        data['weapon_ids']=[]
        self.assertEqual(self.solve(data,components('gun'))['issues'][0]['code'],'UNSUPPORTED_BASE_ITEM')

    def test_unreachable_part_keeps_quantity_and_attributes(self):
        data=source();parts=components('gun','sight');parts[1]['quantity']=2
        parts[1]['attributes']={'nested':{'x':[1,None,True]}}
        result=self.solve(data,parts)
        self.assertFalse(result['can_import'])
        self.assertEqual(result['unplaced_components'],[{'component_index':1,'item_id':'sight','quantity':2,'attributes':parts[1]['attributes']}])
