"""Pure reference calculations. No guessed formula or NULL-to-zero coercion.

Formula provenance: the-hideout/tarkov-data-manager, commit
0366d6527498a627415ed08218255613283a3741, modules/preset-data.mjs.
This is a source-preset reference model, not a simulation of client runtime.
"""
import copy
import hashlib
import json
import math
from functools import lru_cache

from api.modding.reconstruction import allowed, pair_conflict

CALCULATION_VERSION = 'tarkov-dev-preset-0366d652-1'
EXCLUDES = ['client_runtime_rules', 'animation_and_fold_state', 'durability', 'player_skills', 'loaded_ammunition']


def compatibility(nodes, graph):
    issues = []
    occupied = {(n.parent_node_id, n.slot_id) for n in nodes if n.parent_node_id is not None}
    by_id = {n.node_id: n for n in nodes}
    blocked = set().union(*(graph['conflicts']['slots'].get(n.item_id, set()) for n in nodes))
    for n in nodes:
        if n.parent_node_id is not None:
            parent = by_id[n.parent_node_id]
            slot = next((s for s in graph['slots'].get(parent.item_id, []) if s['slot_id'] == n.slot_id), None)
            if slot is None:
                issues.append({'code': 'UNKNOWN_PARENT_SLOT', 'node_id': n.node_id, 'slot_id': n.slot_id})
            elif not allowed(graph, parent.item_id, slot, n.item_id):
                issues.append({'code': 'SLOT_FILTER_REJECTED', 'node_id': n.node_id})
            if n.slot_id in blocked:
                issues.append({'code': 'SLOT_CONFLICT', 'node_id': n.node_id, 'slot_id': n.slot_id})
        for slot in graph['slots'].get(n.item_id, []):
            if slot['required'] and (n.node_id, slot['slot_id']) not in occupied:
                issues.append({'code': 'REQUIRED_SLOT_UNFILLED', 'node_id': n.node_id, 'slot_id': slot['slot_id']})
    for i, n in enumerate(nodes):
        for other in nodes[:i]:
            code = pair_conflict(graph, n.item_id, other.item_id)
            if code:
                issues.append({'code': code, 'node_id': n.node_id, 'item_id': other.item_id})
    unresolved = blocked - graph['known_slot_ids']
    for slot_id in sorted(unresolved):
        issues.append({'code': 'UNRESOLVED_CONFLICT_SLOT', 'slot_id': slot_id})
    status = 'invalid' if any(i['code'] != 'UNRESOLVED_CONFLICT_SLOT' for i in issues) else ('unknown' if unresolved else 'valid')
    return {'scope': 'stored_slot_constraints', 'status': status, 'issues': issues, 'excludes': EXCLUDES}


def calculate(nodes, weapon, items, mods, ballistics, ammo, validation):
    """Hash full inputs, so every synchronized value invalidates the bounded CPU cache."""
    payload = {'version': CALCULATION_VERSION, 'nodes': sorted([n.model_dump() for n in nodes], key=lambda n:n['node_id']),
               'weapon': weapon, 'items': items, 'mods': mods, 'ballistics': ballistics,
               'ammo': ammo, 'compatibility': validation}
    serialized = json.dumps(payload, sort_keys=True, default=str, separators=(',', ':'), allow_nan=False)
    return copy.deepcopy(_calculate(serialized))


@lru_cache(maxsize=128)
def _calculate(serialized):
    p = json.loads(serialized)
    nodes, weapon, items, mods, ballistic = (p[k] for k in ('nodes', 'weapon', 'items', 'mods', 'ballistics'))
    root = next(n for n in nodes if n['parent_node_id'] is None)
    parts = [n['item_id'] for n in nodes if n['parent_node_id'] is not None]
    unavailable = []
    def missing(metric, code, ids=()):
        unavailable.append({'metric': metric, 'code': code, 'item_ids': sorted(set(ids))})
        return None
    def finite(value):
        return value is not None and math.isfinite(float(value))
    def total(metric, values):
        bad = [iid for iid, value in values if not finite(value)]
        return missing(metric, 'MISSING_SOURCE_VALUE', bad) if bad else sum(float(v) for _, v in values)
    weight = total('weight_kg', [(n['item_id'], items[n['item_id']].get('weight')) for n in nodes])
    ergo = total('ergonomics', [(root['item_id'], weapon.get('ergonomics'))] + [(iid, mods.get(iid, {}).get('ergonomics')) for iid in parts])
    recoil = {}
    for metric in ('recoil_vertical', 'recoil_horizontal'):
        base = weapon.get(metric)
        modifier = total(metric, [(iid, mods.get(iid, {}).get('recoil_modifier')) for iid in parts])
        if not finite(base):
            recoil[metric] = missing(metric, 'MISSING_SOURCE_VALUE', [root['item_id']])
        elif modifier is None:
            recoil[metric] = None
        else:
            # JS Math.round, as used by the reference producer (not Python bankers' rounding).
            recoil[metric] = math.floor(float(base) * (1 + modifier) + 0.5)
    moa = None
    base = ballistic.get(root['item_id'], {})
    impact = base.get('center_of_impact')
    curve = base.get('deviation_curve')
    barrels = [iid for iid in parts if ballistic.get(iid, {}).get('properties_type') == 'ItemPropertiesBarrel']
    if len(barrels) > 1:
        moa = missing('accuracy_moa', 'MULTIPLE_BARRELS_UNSUPPORTED', barrels)
    elif barrels and not finite(ballistic[barrels[0]].get('center_of_impact')):
        moa = missing('accuracy_moa', 'MISSING_SOURCE_VALUE', barrels)
    elif not finite(impact) or not finite(curve):
        moa = missing('accuracy_moa', 'MISSING_SOURCE_VALUE', [root['item_id']])
    elif any(iid not in ballistic for iid in parts):
        moa = missing('accuracy_moa', 'MISSING_SOURCE_VALUE', [iid for iid in parts if iid not in ballistic])
    else:
        impact = float(impact) + sum(float(ballistic[iid]['center_of_impact']) for iid in parts if finite(ballistic[iid].get('center_of_impact')))
        maximum = ballistic[barrels[0]].get('deviation_max') if barrels else 100.0
        if barrels and not finite(maximum):
            moa = missing('accuracy_moa', 'MISSING_SOURCE_VALUE', barrels)
        else:
            curve = float(curve)
            discriminant = (100 - 2 * curve) * 100 + curve
            if discriminant < 0:
                moa = missing('accuracy_moa', 'INVALID_SOURCE_VALUE')
            else:
                t = 100 / (2 * curve) if 100 - 2 * curve == 0 else (-curve + math.sqrt(discriminant)) / (100 - 2 * curve)
                deviation = (1-t)**2 * float(maximum or 100) + 2*t*(1-t)*curve + t*t
                moa = math.floor(impact * deviation * 100 / 2.9089 * 100 + 0.5) / 100
    ammo = p['ammo']
    # Reference presets contain no selected-ammo correction. Never invent that extension.
    if ammo:
        for key, metrics in [('recoil_modifier', ('recoil_vertical', 'recoil_horizontal')), ('accuracy_modifier', ('accuracy_moa',))]:
            value = ammo.get(key)
            if value is None or float(value) != 0:
                for metric in metrics:
                    missing(metric, 'AMMO_CORRECTION_UNVERIFIED' if value is not None else 'MISSING_AMMO_MODIFIER', [ammo['item_id']])
                    if metric == 'accuracy_moa': moa = None
                    else: recoil[metric] = None
    else:
        for metric in ('recoil_vertical', 'recoil_horizontal', 'accuracy_moa'):
            missing(metric, 'AMMO_UNAVAILABLE')
        recoil = {k: None for k in recoil}
        moa = None
    speed = missing('muzzle_velocity_mps', 'VELOCITY_FORMULA_UNVERIFIED')
    if not ammo or not finite(ammo.get('initial_speed_mps')):
        # Keep formula and missing-data reasons separate.
        missing('muzzle_velocity_mps', 'MISSING_AMMO_INITIAL_SPEED')
    modes = [name for name in ('single_fire', 'full_auto', 'burst_fire', 'double_action', 'double_tap', 'semi_auto') if weapon.get('is_' + name)]
    if any(weapon.get('is_'+name) is None for name in ('single_fire','full_auto','burst_fire','double_action','double_tap','semi_auto')):
        modes = missing('fire_modes', 'MISSING_SOURCE_VALUE', [root['item_id']])
    caliber = weapon.get('caliber')
    rpm = weapon.get('fire_rate')
    if caliber is None: missing('caliber', 'MISSING_SOURCE_VALUE', [root['item_id']])
    if rpm is None: missing('fire_rate_rpm', 'MISSING_SOURCE_VALUE', [root['item_id']])
    return {'calculation_version': CALCULATION_VERSION,
            'source_revision': hashlib.sha256(serialized.encode()).hexdigest(),
            'ammo_item_id': ammo['item_id'] if ammo else None,
            'ammo_selection': 'unavailable',  # Set by caller; request omission is not part of numerical cache.
            'assumptions': ['source_preset_reference', 'durability_100_percent', 'unloaded_weight', 'each_node_counted_once', 'no_player_skill_bonuses'],
            'compatibility': p['compatibility'],
            'statistics': {'weight_kg': round(weight, 3) if weight is not None else None,
                           'ergonomics': ergo, **recoil, 'accuracy_moa': moa, 'muzzle_velocity_mps': speed,
                           'fire_modes': modes, 'caliber': caliber, 'fire_rate_rpm': rpm},
            'unavailable': unavailable}
