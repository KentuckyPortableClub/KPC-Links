#!/usr/bin/env python3
"""Nov 9 PAD-US load fix (LOCAL batch prep/nov9-weekly-batch; nothing pushed, no run started).
ROOT CAUSE (11:28 AM CST): kpc_us_key.py's load filters (State_Nm read, Category Fee / Designation, owner or manager FED / STAT / DIST)
ran BEFORE overrides.json, so a saved join to a filtered record (US-2238 Heyburn -> 199938, Category 'Other') pointed at nothing.
(1) a saved id (overrides 'join' / 'fp') is ALWAYS loaded, by id if need be, whatever its Category, owner or PAD-US state;
(2) Brandon 11:24 AM CST 'Yes': a filtered record whose name strictly matches a POTA park (with no saved id) is kept;
(3) Brandon 11:26 AM CST: order = PAD-US passes, else the state layer's (state-gis.json) record of the name, else the PAD-US name exception.
Offline: page()/get() are stubbed, no request is sent."""
import pathlib, sys, types, os, io, contextlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
os.chdir(ROOT)
import kpc_key_freeze as KZ
ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)

src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8').split('\nidx = {}\n')[0]
U = types.ModuleType('kpc_us_key'); U.__dict__['__file__'] = str(ROOT / '.github/scripts/kpc_us_key.py')
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src, 'kpc_us_key.py', 'exec'), U.__dict__)
NOTES = []; U.notice = lambda t, m: NOTES.append((t, m)); U.time.sleep = lambda s: None

def feat(oid, nm, cat='Fee', own='FED', mang='FED', st='ID', des=''):
    return {'attributes': {'OBJECTID': oid, 'Unit_Nm': nm, 'Loc_Nm': nm, 'Category': cat, 'Own_Type': own, 'Mang_Type': mang, 'State_Nm': st, 'Des_Tp': des, 'GIS_Acres': 100},
            'geometry': {'rings': [[[-116.8, 47.3], [-116.7, 47.3], [-116.7, 47.4], [-116.8, 47.3]]]}}

U.OVR = {'US-2238': {'join': ['199938'], 'fp': {'199938': ['Heyburn State Park', 8094]}},
         'US-0329': {'join': ['5300', 'Silvio by name'], 'fp': {'5300': ['Silvio O. Conte National Fish And Wildlife Refuge', 7893]}}}
P = {'US-2238': ['Heyburn State Park', '', 'State Park', 0, 0, 47.37, -116.76],
     'US-4036': ['Walnut Creek State Recreation Area', '', 'State Recreation Area', 0, 0, 47.35, -116.75],
     'US-9999': ['Riverside State Park', '', 'State Park', 0, 0, 47.36, -116.74]}

sv = U.saved_ids({'US-2238': P['US-2238'], 'US-0329': ['x']})
check('saved ids: numeric join + fp ids only (a name join is not an id)', sv == {'199938': ('US-2238', 'Heyburn State Park'), '5300': ('US-0329', 'Silvio O. Conte National Fish And Wildlife Refuge')})
check('load filter unchanged for passing records', U._passes_load(feat(1, 'x')['attributes']) and not U._passes_load(feat(1, 'x', cat='Other')['attributes'])
      and not U._passes_load(feat(1, 'x', own='LOC', mang='CITY')['attributes']) and U._passes_load(feat(1, 'x', own='DIST', mang='LOC')['attributes']))

FE = [feat(10, 'Some State Forest'),                                                          # passes: kept as always
      feat(199938, 'Heyburn State Park', cat='Other', own='STAT', mang='SDNR'),              # saved id, Category Other: kept (root cause)
      feat(118464, 'Walnut Creek Recreation Area', own='LOC', mang='CITY', des='LP'),        # no saved id, strict name match: kept
      feat(20, 'Riverside Park', own='LOC', mang='CITY', des='LP'),                          # city park: says no kind -> dropped
      feat(21, 'Central Park', own='LOC', mang='CITY'),                                      # a city park of no POTA name -> dropped
      feat(22, 'Heyburn State Park Annex Lot', own='PVT', mang='PVT')]                       # Heyburn has a saved id: no name exception
U.page = lambda st, off: {'features': FE if off == 0 else []}
U.pad_cross = lambda st, P, recs, idx, hand: []
recs, n = U.pad_state('ID', P)
got = {a['OBJECTID'] for a in recs}
check('passing record kept', 10 in got)
check('saved id 199938 (Category Other) kept: the root cause', 199938 in got and 'saved id' in next(a for a in recs if a['OBJECTID'] == 199938)['KPC_NameKeep'])
check('filtered record with the POTA park name kept (Walnut Creek, Brandon 11:24 AM)', 118464 in got)
check('city parks with no kind word / no POTA name dropped (no flood)', not got & {20, 21})
check('a park with a saved id gets no name exception', 22 not in got)
check('kept records are tagged in a saved field (survives the boundary cache)', all(not k.startswith('_') for k in ['KPC_NameKeep']) and all(a.get('KPC_NameKeep') for a in recs if a['OBJECTID'] != 10))

U.OVR['US-4036'] = {}; U.NAME_KEEP = False
check('KPC_PADUS_NAME_KEEP=0: the old filters exactly', {a['OBJECTID'] for a in U.pad_state('ID', P)[0]} == {10}); U.NAME_KEEP = True

# saved id filed under another state (US-0329 Silvio O. Conte, MA park, PAD-US 5300 is NH): asked for by id
ASK = []
def fake_get(q, tries=3):
    ASK.append(q); return {'features': [feat(5300, 'Silvio O. Conte National Fish And Wildlife Refuge', st='NH')]}
U.get = fake_get
PM = {'US-0329': ['Silvio O Conte National Wildlife Refuge', '', 'National Wildlife Refuge', 0, 0, 44.77, -71.70]}
out = U.saved_fetch('MA', PM, [])
check('cross-state saved id read BY ID (one ask, OBJECTID IN, no State_Nm filter)', len(ASK) == 1 and ASK[0]['where'] == 'OBJECTID IN (5300)' and 'State_Nm' not in ASK[0]['where'])
check('5300 loaded for MA, tagged filed under NH', [a['OBJECTID'] for a in out] == [5300] and 'filed under NH' in out[0]['KPC_NameKeep'])
check('nothing asked when the saved id is already read', not U.saved_fetch('MA', PM, [dict(feat(5300, 'x')['attributes'])]) and len(ASK) == 1)

# order (Brandon 11:26 AM): the state layer's record of the name beats the PAD-US name exception; a saved id is never dropped
pad = U._shape(dict(feat(118464, 'Walnut Creek Recreation Area', own='LOC')['attributes'], KPC_NameKeep='name'), feat(1, 'x'))
lay = U._shape({'OBJECTID': 'sgnea17', 'Unit_Nm': 'Walnut Creek Recreation Area (NRD)', 'Loc_Nm': '', 'Category': 'Fee', 'Des_Tp': ''}, feat(1, 'x'))
U.OVR['US-2255'] = {'join': ['199940'], 'fp': {'199940': ['Farragut State Park', 4000]}}
P2 = dict(P, **{'US-2255': ['Farragut State Park', '', 'State Park', 0, 0, 47.95, -116.6]})
hy = U._shape(dict(feat(199940, 'Farragut State Park', cat='Other')['attributes'], KPC_NameKeep='saved id'), feat(1, 'x'))
lay2 = U._shape({'OBJECTID': 'sgid5', 'Unit_Nm': 'Farragut State Park', 'Loc_Nm': '', 'Category': 'Fee', 'Des_Tp': ''}, feat(1, 'x'))
U.OVR.pop('US-4036', None)
left = {a['OBJECTID'] for a in U.prefer_state_layer('ID', [pad, lay, hy, lay2], P2)}
check('state layer first: the name-only PAD-US record is left out when sgnea17 names Walnut Creek', 118464 not in left and 'sgnea17' in left)
check('a saved id is kept even when the state layer names the park too (noted for Quality)', 199940 in left and any('Quality to look' in m for t, m in NOTES))
check('no name-kept record, no change', U.prefer_state_layer('ID', [lay], P) == [lay])

src_full = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check('run(): state layer read with name-only records left out of its duplicate list', "_have([a for a in recs if not a.get('KPC_NameKeep')])" in src_full)
check('run(): saved ids topped up on the saved-copy path too', 'saved_fetch(st, P, recs)' in src_full.split('def run(st)')[1].split('if _kr(')[0])
check('no new host: the by-id ask uses the PAD-US query url Q only', 'nationalmap.gov' in U.Q and 'arcgis.com/33TOOklri9xpic7U' not in src_full and 'natureserve' not in src_full)
check('Brandon 11:24 AM "Yes" recorded with the new US hash', 'Brandon Nov 9, 2026, 11:24 AM CST' in (ROOT / 'docs/key-rules-change.txt').read_text() and KZ.rules_hash('us-key') in (ROOT / 'docs/key-rules-change.txt').read_text())
check('rules hashes: US 19d219f37114, CA 22f16bc69b96 (blocked_ids, Brandon t918u/t919u), world unchanged, fers eb92de7a5f65',
      (KZ.rules_hash('us-key'), KZ.rules_hash('ca-key'), KZ.rules_hash('world-key'), KZ.rules_hash('fers')) == ('19d219f37114', '22f16bc69b96', '10e4092cc97f', 'eb92de7a5f65'))
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
