#!/usr/bin/env python3
"""23 Nov 2026, owner 9:20 AM (job 7, the saved answers that no longer find their record). His answers: "Wouldn't fixing records
id be best solution?" (re-point the answer to the record's new number), "Fix it to where all parks that are mutiple states have
record in each one" (read the record from the bordering state's saved copy), "figure it out and fix it" (split pieces, bare
names, the rest retired with a reason so the normal matching decides), "All parcels inside the park" (look-alike parcels that all
carry the park's name all join). Invented records; no connection is opened. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import pathlib, socket, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_key_rules as KR  # noqa: E402
import kpc_match_checks as MC  # noqa: E402
import kpc_saved_answers_fix as S  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


PIN = (45.0, -90.0)
B = [-90.02, 44.98, -89.98, 45.02]      # a box around the pin
FAR = [-95.02, 40.98, -94.98, 41.02]    # far away
rows = [('sgzza900', 'Heron Marsh State Park', 830.0, B),          # the state layer, new number
        ('272288', 'Heron Marsh State Park', 834.0, B),            # PAD-US, the same land
        ('sgzzb11', 'Otter Run Wildlife Area', 410.0, B), ('sgzzb12', 'Otter Run Wildlife Area', 395.0, B),   # two pieces = the old 800 ac
        ('sgzzc7', 'Fox Den State Recreation Area', 120.0, B),
        ('sgzzd1', 'Cedar Knob State Park', 40.1, B), ('sgzzd2', 'Cedar Knob State Park', 39.8, B), ('sgzzd3', 'Cedar Knob State Park', 40.3, B)]

# 1. a changed record number: the same name and acres, the same land in two layers = one answer (the closest acres)
ov = {'fp': {'zza100': ['Heron Marsh State Park', 829]}}
p = S.plan_fix('zza100', ov, rows, *PIN, 'Heron Marsh State Park')
check('a changed number is re-pointed to the same name + acres (the same land in two layers counts once: the closest acres)', p[0] == 'renumber' and p[1] == 'sgzza900')
# 2. split into pieces that add up to the saved acres
p = S.plan_fix('zzb5', {'fp': {'zzb5': ['Otter Run Wildlife Area', 800]}}, rows, *PIN, 'Otter Run Wildlife Area')
check('a record split into pieces that add up joins the pieces', p[0] == 'split' and sorted(x for x, _ in p[1]) == ['sgzzb11', 'sgzzb12'])
# 3. a bare name answer whose record now carries the same place's other spelling
p = S.plan_fix('Fox Den SRA', {}, rows, *PIN, 'Fox Den State Recreation Area')
check('a bare-name answer becomes the one record of that place near the pin (id + fingerprint)', p[0] == 'name' and p[1] == 'sgzzc7')
# 4. nothing of that name and size: retired with the reason
p = S.plan_fix('zze9', {'fp': {'zze9': ['Lost Lake State Park', 500]}}, rows, *PIN, 'Lost Lake State Park')
check('nothing of that name near the pin = retired with its reason', p[0] == 'retire' and 'gone' in p[1])
p = S.plan_fix('zza100', {'fp': {'zza100': ['Heron Marsh State Park', 2000]}}, rows, *PIN, 'Heron Marsh State Park')
check('the same name but another size (split, merged or redrawn) = retired, never re-joined by name alone', p[0] == 'retire' and 'split, merged' in p[1])
p = S.plan_fix('zzf3', {}, rows, *PIN, 'X State Park')
check('no fingerprint = retired (an id alone is never trusted)', p[0] == 'retire' and 'fingerprint' in p[1])
# 5. all parcels inside the park
check("look-alike parcels that all carry the park's own name all join", MC.all_parcels_ok('Cedar Knob State Park', ['Cedar Knob State Park'] * 3))
check("parcels with a county ending of the park's name all join (W8)", MC.all_parcels_ok('Mud Test State Wildlife Area', ['Mud Test Wildlife Area-Columbia'] * 4))
check('a fit with another name stops it (as before: the first joins and it is said)', not MC.all_parcels_ok('Cedar Knob State Park', ['Cedar Knob State Park', 'Cedar Creek Lake']))
v, ids = S.test_answer('sgzzd9', {'fp': {'sgzzd9': ['Cedar Knob State Park', 40]}}, rows, {x[0]: x for x in rows}, *PIN, all_parcels=True, park_name='Cedar Knob State Park')
check('the saved-answer test joins every parcel of the park', v == 'found' and sorted(ids) == ['sgzzd1', 'sgzzd2', 'sgzzd3'])
v, _ = S.test_answer('sgzzd9', {'fp': {'sgzzd9': ['Cedar Knob State Park', 40]}}, rows, {x[0]: x for x in rows}, *PIN)
check('without the switch it still says "fits two" (unchanged)', v == 'two')
# 6. the bordering state's saved copy
import json as _json
NB = _json.loads((ROOT / 'data/us-key/area-tables.json').read_text(encoding='utf-8'))['US_NEIGHBOURS']
check('neighbours: a state and the states on its border, from the area tables (none for Alaska)', 'MS' in KR.neighbours('AL', NB) and KR.neighbours('AK', NB) == [])
copies = {'MS': [{'OBJECTID': 'sgmsa5', 'Unit_Nm': 'Natchez Test Parkway'}], 'TN': [{'OBJECTID': 'sgmsa5', 'Unit_Nm': 'a later copy'}], 'GA': [{'OBJECTID': 'sggaa1', 'Unit_Nm': 'other'}]}
got = KR.next_state_records(['sgmsa5', 'sgmsa6'], lambda s: copies.get(s), KR.neighbours('AL', NB))
check("a saved answer's record is read from the bordering state's copy, once", [a['Unit_Nm'] for a in got] == ['Natchez Test Parkway'])
check('a state that does not border is never read', KR.next_state_records(['sgmsa5'], lambda s: copies.get(s), ['TX']) == [])
nd = {'sgmsa5': ('MS', ('sgmsa5', 'Natchez Test Parkway', 9000.0, B))}
v, _ = S.test_answer('sgmsa5', {}, rows, {x[0]: x for x in rows}, *PIN, next_door=nd)
check('the saved-answer test finds it next door', v == 'found')
nd_far = {'sgmsa5': ('MS', ('sgmsa5', 'Natchez Test Parkway', 9000.0, FAR))}
check('a record next door far from the pin is not taken', S.test_answer('sgmsa5', {}, rows, {x[0]: x for x in rows}, *PIN, next_door=nd_far)[0] == 'none')
# 7. the builder uses both, behind their switches, on saved copies only
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check('the builder reads saved answers from the bordering states (KPC_SAVED_NEXT_STATE)', "_kr('KPC_SAVED_NEXT_STATE')" in src and 'KR.next_state_records(' in src)
check('the builder joins all the parcels (KPC_SAVED_ALL_PARCELS)', "_kr('KPC_SAVED_ALL_PARCELS') and MC.all_parcels_ok(name" in src and '_oid(a) in _all_ids' in src)
sw = (ROOT / '.github/key-switches.json').read_text(encoding='utf-8')
check('the bordering-states table lives in the area tables (D6), not in a rule file', 'US_NEIGHBOURS = {' not in (ROOT / '.github/scripts/kpc_key_rules.py').read_text(encoding='utf-8') and 'KR.neighbours(st, US_NEIGHBOURS)' in src)
check('both switches are on in every state', '"KPC_SAVED_NEXT_STATE": {"on": ["AK"' in sw and '"KPC_SAVED_ALL_PARCELS": {"on": ["AK"' in sw)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
