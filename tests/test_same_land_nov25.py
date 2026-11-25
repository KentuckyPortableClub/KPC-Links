#!/usr/bin/env python3
"""25 Nov 2026 (KPC owner, 6:20 + 6:28 AM: 'a better matcher', 'proof or the pin, no hand-offs'): a key record takes the
outline store's id fields only from the fresh store record PROVEN to be the same land (agency id, shared ground, a piece, name
and size; never the row number), and after the match checks a row draws only with proof. Runs the REAL key code (the helper
part of kpc_us_key, as the other store-id tests do). Invented records. Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, math, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
import kpc_match_checks as MC  # noqa: E402
import kpc_source_fields as SF  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


for f in ('kpc_same_land.py', 'kpc_store_attrs.py'):
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts' / f), '--selftest'], capture_output=True, text=True)
    check(f'{f} self-test', 'ALL PASS' in r.stdout)

src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
# the key's whole helper part (everything before the build starts), as the real build runs it
os.environ.setdefault('GEO_CACHE_MODE', 'only'); os.environ.setdefault('KPC_KEY_OFFLINE', '1')
_cwd = os.getcwd(); os.chdir(ROOT)
ns = {'__file__': str(ROOT / '.github/scripts/kpc_us_key.py'), '__name__': 'kpc_us_key_helpers'}
import contextlib, io  # noqa: E402
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src[:src.index('\nidx = {}\n')], ns['__file__'], 'exec'), ns)
os.chdir(_cwd)
ns['OVR'].clear(); ns['notice'] = lambda *a: None
KR, MC, SF = ns['KR'], ns['MC'], ns['SF']


def sq(x, y, d):
    return [[[x, y], [x + d, y], [x + d, y + d], [x, y + d], [x, y]]]


# the MN case: the store read numbers Lost Valley Prairie 210; the key's older copy has it as 55, and its 210 is other land
lost_store = {'pgrm_project': 'SNA01041', '_nm': 'Lost Valley Prairie', '_ac': 216, '_bx': [-92.83, 44.80, -92.82, 44.81],
              '_g': sq(-92.83, 44.80, 0.01), '_st': 'US-MN', '_rd': '2026-11-21'}
ns['_RA'][0] = {'207720': {'_nm': 'Lost Valley Prairie State Scientific and Natural Area', '_ac': 216, '_bx': [-92.83, 44.80, -92.82, 44.81],
                           '_g': sq(-92.83, 44.80, 0.01), '_st': 'US-MN', '_pad': {'Des_Tp': 'SCA', 'Own_Type': 'STAT', 'Mang_Name': 'SDNR'}}}
ns['_RA_RF'][0] = {'sgmnc210': lost_store,
                   'sgmnb7': {'sft': 'SFT00900', '_nm': 'Schoolcraft', '_ac': 216, '_bx': [-94.0, 47.0, -93.99, 47.01], '_g': sq(-94.0, 47.0, 0.01), '_st': 'US-MN'}}
ns['_SL_IDX'][1] = None
slf = ns['same_land_fields']
key55 = {'OBJECTID': 'sgmnc55', 'Unit_Nm': 'Lost Valley Prairie', 'GIS_Acres': 216, '_g': {'rings': sq(-92.8301, 44.8001, 0.01)}, '_k': {'snp'}}
key210 = {'OBJECTID': 'sgmnc210', 'Unit_Nm': 'Crystal Spring', 'GIS_Acres': 40, '_g': {'rings': sq(-92.70, 44.70, 0.003)}, '_k': {'snp'}}
check('the renumbered record finds its fresh twin by shared ground, with the agency id',
      slf('sgmnc55', key55) == ('overlap', {'pgrm_project': 'SNA01041'}))
check("the key's record 210 is other land: it never takes record 210's fields (the number proves nothing)", slf('sgmnc210', key210)[0] == 'none')
other_id = {'OBJECTID': 'sgmnb3', 'Unit_Nm': 'Schoolcraft', 'GIS_Acres': 216, 'SA': {'sft': 'SFT00555'}, '_g': {'rings': sq(-94.0, 47.0, 0.01)}}
check('a fresh record with ANOTHER unit id on the same ground: conflict, no fields', slf('sgmnb3', other_id) == ('conflict', None))
check('the same unit id (leading zeros aside): proven by id', slf('sgmnb3', dict(other_id, SA={'sft': 'SFT900'}))[0] == 'id')
check('no store record of the layer near it: none', slf('sgzza1', {'OBJECTID': 'sgzza1', 'Unit_Nm': 'X', '_g': {'rings': sq(-80, 40, 0.01)}}) == ('none', None))

# the fresh source: today's store records stand in for the old saved copy (N3: only layers the store's manifest says are complete)
ns['CUR_ST']['st'] = 'MN'
ns['_RA_MAN'][0] = {'US-MN': {'sgmnc': {'complete': True}, 'padus': {'complete': True}, 'sgmnb': {'complete': False}}}
for d_ in (ns['_RA'][0], ns['_RA_RF'][0]):   # these stand for the full layer files (owner 8:48 AM: the only fresh source)
    for e_ in d_.values(): e_['_src'] = 'layer'
_real_joined = ns['joined_layers']
ns['joined_layers'] = lambda st, P, layers_read=None: set()   # the gap stop is tested on its own below
old_recs = [key55, key210, {'OBJECTID': 207720, 'Unit_Nm': 'Lost Valley Prairie State Scientific and Natural Area', 'GIS_Acres': 216,
                            '_g': {'rings': sq(-92.83, 44.80, 0.01)}, 'Des_Tp': 'SCA', '_k': {'snp'}}]
for a in old_recs: a['_bb'] = ns['bbox'](a['_g'])
out, alias = ns['fresh_records']('MN', old_recs, {})
ids = {str(a['OBJECTID']): a for a in out}
check('the old record 55 is proven to the fresh 210 and dropped; the fresh record stands in with its own outline and id fields',
      alias.get('sgmnc55') == 'sgmnc210' and ids['sgmnc210'].get('_fresh') and ids['sgmnc210']['SA'] == {'pgrm_project': 'SNA01041'}
      and ids['sgmnc210']['Unit_Nm'] == 'Lost Valley Prairie' and 'snp' in ids['sgmnc210']['_k'])
check("the old record 210 (other land) becomes a hint under another id: it never shares the fresh record's number",
      'sgmnc210~old' in ids and ids['sgmnc210~old'].get('_hint') and ids['sgmnc210~old']['Unit_Nm'] == 'Crystal Spring')
check('a fresh PAD-US record keeps its own PAD-US words', ids['207720'].get('_fresh') and ids['207720'].get('Des_Tp') == 'SCA')
ns['OVR'].update({'K-9': {'join': ['sgmnc55'], 'fp': {'sgmnc55': ['Lost Valley Prairie', 216]}, 'no': ['sgmnc210']}})
ns['repoint_saved']('MN', {'K-9': []}, alias, {a for a in ids if ids[a].get('_fresh')})
o9 = ns['OVR']['K-9']
check("a saved join follows its land to the fresh record (proven), with its fingerprint; a NO on unproven land stays on the old copy",
      o9['join'] == ['sgmnc210'] and 'sgmnc210' in o9['fp'] and o9['no'] == ['sgmnc210~old']
      and any(x[1:5] == ['K-9', 'join', 'sgmnc55', 'sgmnc210'] for x in ns['REPOINTS']))

# the gate: proof or the pin, from fresh records only
gate = ns['proven_only_gate']
ns['SAME_STATE'].clear(); ns['SAME_STATE'].update({'sg2': 'conflict'})
F = lambda i, n, ac: {'OBJECTID': i, 'Unit_Nm': n, 'GIS_Acres': ac, '_fresh': True, '_bb': [-90, 40, -89.99, 40.01]}
byid = {'sg1': F('sg1', 'Alpha WMA', 100), 'sg2': F('sg2', 'Beta WMA', 50), 'sg3': F('sg3', 'Gamma Forest', 900),
        'sg4': F('sg4', 'Delta Lake', 20), 'sg5': F('sg5', 'Echo Marsh', 70), 'sg6': F('sg6', 'Golf State Park', 410),
        'sg7': dict(F('sg7', 'Hotel WMA', 30), _fresh=False, _hint=True)}
ns['OVR'].update({'K-3': {'join': ['sg3'], 'fp': {'sg3': ['Gamma Forest', 880]}},
                  'K-4': {'join': ['sg4'], 'fp': {'sg4': ['Old Name Tract', 20]}},
                  'K-5': {'join': ['sg5'], 'no': ['sg2']}})
facts = {'K-8': {'name': 'Golf State Park', 'size': {'acres': 400, 'witness': 'agency_document'}}}
parks = {'K-1': {'m': [['sg1', 'Alpha WMA', 100, 'name']], 'match': {'status': 'outlined'}, 'g': 'official'},
         'K-2': {'m': [['sg1', 'Alpha WMA', 100, 'name'], ['sg2', 'Beta WMA', 50, 'name']], 'match': {'status': 'confirmed', 'by': 'id'}, 'g': 'official'},
         'K-3': {'m': [['sg3', 'Gamma Forest', 900, 'reviewed']], 'match': {'status': 'outlined'}, 'g': 'official'},
         'K-4': {'m': [['sg4', 'Delta Lake', 20, 'reviewed']], 'match': {'status': 'confirmed', 'by': 'size'}, 'g': 'official'},
         'K-5': {'m': [['sg5', 'Echo Marsh', 70, 'reviewed']], 'match': {'status': 'outlined'}, 'g': 'official'},
         'K-6': {'m': [['nps1', 'Foxtrot NM', 10, 'NPS unit code']], 'match': {'status': 'outlined'}, 'g': 'official'},
         'K-7': {'m': [['sg1', 'Alpha WMA', 100, 'name']], 'match': {'status': 'outlined'}, 'g': 'official'},
         'K-8': {'n': 'Golf State Park', 'm': [['sg6', 'Golf State Park', 410, 'name']], 'match': {'status': 'outlined'}, 'g': 'official'},
         'K-10': {'m': [['sg7', 'Hotel WMA', 30, 'name']], 'match': {'status': 'confirmed', 'by': 'link'}, 'g': 'official'}}
res = gate('MN', parks, byid, skip={'K-7'}, facts=facts)
check('an outlined park with a name row only: pin only, the row marked for the code to fix, the park listed',
      parks['K-1']['m'] == [] and parks['K-1']['g'] == 'pin' and parks['K-1']['match']['status'] == 'pin'
      and parks['K-1']['c'][0][3].startswith('check (code to fix: not proven') and any(x[:2] == ['MN', 'K-1'] for x in ns['PIN_ONLY']))
check('a confirmed park keeps BOTH rows; the one a fresh record with another agency id holds is listed, not dropped (M3)',
      [q[0] for q in parks['K-2']['m']] == ['sg1', 'sg2'] and any(x[1:3] == ['K-2', 'sg2'] for x in ns['LISTED']))
check("a person's join whose fingerprint still fits draws (even on an outlined park)", [q[0] for q in parks['K-3']['m']] == ['sg3'])
check("a person's join whose fingerprint no longer fits never draws (other land holds the number)",
      parks['K-4']['m'] == [] and "other land holds this record number" in parks['K-4']['c'][0][3])
check("a person's join with no fingerprint on an unproven park: pin, and listed for the owner",
      parks['K-5']['m'] == [] and any(x[1:4] == ['K-5', 'join', 'sg5'] for x in ns['FP_PROPOSALS']))
check('a NO with no fingerprint is still applied and listed for the owner', any(x[1:4] == ['K-5', 'no', 'sg2'] for x in ns['FP_PROPOSALS']))
check('a code row (Park Service unit code) stays', [q[0] for q in parks['K-6']['m']] == ['nps1'])
check('a park the gate skips (official trail line) is left alone', parks['K-7']['m'] and parks['K-7']['g'] == 'official')
check("the park's own name and its official size within 10% keep its outline (M4: the owner's proof 3 at park level)",
      [q[0] for q in parks['K-8']['m']] == ['sg6'] and parks['K-8']['match'].get('by') == 'name and official size')
check('an old-copy hint never draws, even on a confirmed park (fresh data only)',
      parks['K-10']['m'] == [] and 'only in the old saved copy' in parks['K-10']['c'][0][3])
check('the counts', res['rows'] == 4 and res['pin_now'] == 4 and res['by_name_size'] == 1 and res['listed'] == 1)
check('the name + size counts say why parks were not kept (M3: missing data or a bug)',
      res['name_size']['tried'] == 5 and res['name_size']['ok'] == 1 and res['name_size']['no witness'] == 4)

# N3 (grade of round 5): a layer the store holds only PART of (manifest: not complete) is handled like a layer not in store
part_old = {'OBJECTID': 'sgmnb3', 'Unit_Nm': 'Far Away Forest', 'GIS_Acres': 50, '_g': {'rings': sq(-91.0, 47.5, 0.004)}, 'rd': '2026-11-12'}
part_old['_bb'] = ns['bbox'](part_old['_g'])
outp, aliasp = ns['fresh_records']('MN', old_recs + [part_old], {})
idp = {str(a['OBJECTID']): a for a in outp}
check('a layer the store holds only part of: an unproven old record is kept (not a hint), and the layer is listed as not complete',
      idp.get('sgmnb3', {}).get('_nostore') and not idp['sgmnb3'].get('_hint') and 'sgmnb' in (ns['FRESH']['MN'].get('partial_layers') or []))
ns['_RA_MAN'][0] = {}
outq, _a = ns['fresh_records']('MN', old_recs, {})
idq = {str(a['OBJECTID']): a for a in outq}
check('no manifest at all: no layer counts as in the store (one record never makes a layer complete); records kept, never hints',
      not any(a.get('_hint') for a in outq) and ns['FRESH']['MN'].get('no_manifest') and idq.get('sgmnc210~old', {}).get('_nostore'))
ns['_RA_MAN'][0] = {'US-MN': {'sgmnc': {'complete': True}, 'padus': {'complete': True}, 'sgmnb': {'complete': False}}}
check('N1: a record read live this run is never listed as a store record (the cutter cuts it from the saved copy)',
      "a.get('_fresh') and not a.get('_read_now')" in src)

# M2 (grade of round 4): a layer the store holds NO record of for this state is not 'missing records'
fws_old = {'OBJECTID': 'fws4026', 'Unit_Nm': 'Detroit Lakes WMD tract', 'GIS_Acres': 80, '_g': {'rings': sq(-95.8, 46.8, 0.005)}, 'rd': '2026-11-12'}
fws_old['_bb'] = ns['bbox'](fws_old['_g'])
out2, alias2 = ns['fresh_records']('MN', old_recs + [fws_old], {})
ids2 = {str(a['OBJECTID']): a for a in out2}
check("a record of a layer the store does not hold keeps its id and is marked 'not in store', never a hint",
      ids2.get('fws4026', {}).get('_nostore') and not ids2['fws4026'].get('_hint') and 'fws4026~old' not in ids2)
ns['OVR']['K-11'] = {'join': ['fws4026']}
ns['repoint_saved']('MN', {'K-11': []}, alias2, set(), set((ns['FRESH'].get('MN') or {}).get('store_layers') or []))
check('its saved join keeps its id, listed as layer not in store', ns['OVR']['K-11']['join'] == ['fws4026']
      and any(x[1] == 'K-11' and 'layer not in store' in x[5] for x in ns['REPOINTS']))
parks2 = {'K-11': {'m': [['fws4026', 'Detroit Lakes WMD tract', 80, 'reviewed']], 'match': {'status': 'confirmed', 'by': 'link'}, 'g': 'official'},
          'K-12': {'n': 'Golf State Park', 'm': [['sg7', 'Golf State Park', 410, 'name']], 'match': {'status': 'outlined'}, 'g': 'official'}}
byid2 = dict(byid, fws4026=ids2['fws4026'], sg7=dict(byid['sg7'], Unit_Nm='Golf State Park', GIS_Acres=410))
facts2 = {'K-12': {'name': 'Golf State Park', 'size': {'acres': 400, 'witness': 'agency_document'}}}
res2 = gate('MN', parks2, byid2, facts=facts2)
check("its rows show the pin with the reason 'layer not in store' (not 'old copy only'), and pin-only-parks says layer_in_store no",
      parks2['K-11']['m'] == [] and 'layer not in store' in parks2['K-11']['c'][0][3]
      and any(x[1] == 'K-11' and x[4] == 'no' for x in ns['PIN_ONLY']))
check('each layer the keys join that the store lacks is listed', any(x[:2] == ['MN', 'fws'] and x[2] == 1 for x in ns['NOSTORE_LAYERS']))
check('M3: a park proven by name and official size whose only row then leaves (an old-copy hint) is NOT counted as kept',
      parks2['K-12']['m'] == [] and res2['by_name_size'] == 0 and res2['name_size']['ok'] == 1)

# switches: MN and NY only (the owner's test order); never Kentucky yet
for sw in ('KPC_SAME_LAND', 'KPC_PROVEN_ONLY', 'KPC_STORE_FRESH'):
    check(f'{sw}: on for MN and NY, off for KY and OH', KR.on(sw, area='MN') and KR.on(sw, area='NY') and not KR.on(sw, area='KY') and not KR.on(sw, area='OH'))
import kpc_key_freeze as KF  # noqa: E402
check('kpc_same_land.py is a US rule file (it moves the US hash)', '.github/scripts/kpc_same_land.py' in KF.RULE_FILES['us-key'])
check('the one line per state: by agency id, by shared ground, pieces, by name and size, not proven',
      all(w in src for w in ("by agency id {_sh.get('id', 0)}", "by shared ground", "by name and size", "not proven {_sh.get('unproven', 0)}", 'now pin only')))
kt = (ROOT / 'tools/pc-keys/kpc_test_keys.py').read_text(encoding='utf-8')
check('the PC test remakes its id file before format 9 and saves the owner lists',
      'fmt < 9' in kt and all(w in kt for w in ('saved-answers-no-fingerprint.csv', 'pin-only-parks.csv', 'saved-answers-moved.csv', 'rows-kept-but-listed.csv', 'layers-not-in-store.csv')))
# owner 8:48 AM: a key build for an area STOPS and lists the gap when any layer it joins is not complete in the full layer files
ns['joined_layers'] = lambda st, P, layers_read=None: {'sgmnc', 'fws', 'sgmnb'}
try:
    ns['fresh_records']('MN', old_recs, {})
    stopped = False
except Exception as e_:   # noqa: BLE001
    stopped = 'not complete for joined layer(s) fws' in str(e_) and 'sgmnb' in str(e_) and 'held' in str(e_)
check('a joined layer missing or not complete in the full layer files stops the state (held, no key written) and names it',
      stopped and any(x[:2] == ['MN', 'fws'] and x[4] == 'no layer file' for x in ns['GAPS']) and any(x[:2] == ['MN', 'sgmnb'] for x in ns['GAPS']))
ns['joined_layers'] = lambda st, P, layers_read=None: set()
check("only full-layer-file records stand in: a park-store record (_src park) is never a fresh record",
      "e.get('_src') == 'layer'" in src)
ns['OVR']['K-20'] = {'join': ['fws123', 'trl9', 207720]}
check('the joined layers come from the website key and the saved answers (never trail lines)',
      {'fws', 'padus'} <= _real_joined('ZZ', {'K-20': []}) and 'trl' not in _real_joined('ZZ', {'K-20': []}))
ns['OVR']['K-21'] = {'join': ['sgiaa544']}
check("a saved answer naming another state's layer (a border park's Iowa record from MN) is not a joined layer of this state",
      'sgiaa' not in _real_joined('ZZ', {'K-21': []}, {'sgmnc', 'padus'}) and 'sgiaa' in _real_joined('ZZ', {'K-21': []}, {'sgiaa'}))

# P2 (grade of round 6): a failed id-file run stops the PC test; it never falls back to an older record-attrs file
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location('kpc_test_keys_p2', ROOT / 'tools/pc-keys/kpc_test_keys.py')
TK = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(TK)
    with tempfile.TemporaryDirectory() as td_:
        td_ = pathlib.Path(td_); (td_ / 'store').mkdir(); (td_ / 'links' / '.pf').mkdir(parents=True)
        (td_ / 'links' / '.pf' / 'record-attrs.json.gz').write_bytes(b'stale')   # an older file that must never be used
        TK.STORE, TK.LINKS, TK.say = td_ / 'store', td_ / 'links', (lambda *a: None)
        import subprocess as _sp
        _run = TK.subprocess.run
        TK.subprocess = type('S', (), {'run': staticmethod(lambda *a, **k: type('R', (), {'returncode': 1})())})
        check('P2: kpc_store_attrs failing = no id file used (the PC test stops), never the older file', TK.store_attrs() is None)
except SystemExit:
    check('P2: kpc_test_keys loads', False)
check('P2: the PC test says STOPPED when the id fields cannot be read', 'STOPPED: the agency id fields could not be read' in kt)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
