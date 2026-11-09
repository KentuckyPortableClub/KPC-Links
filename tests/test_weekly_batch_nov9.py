#!/usr/bin/env python3
"""Nov 9 2026 weekly batch (local only; Brandon 10:40 AM CST: no PR, no push). Offline checks of what the batch changed:
overrides put back / accepted, the NRHP layer scoped to the 9 states, the KY outlines (Salato, Kingfisher, Carpenter), the
problem solver's two new paths, and a scope guard: every state-GIS hand join names a layer set up for the park's state, or is
on the held list below with its reason. No rules hash moves. No network."""
import glob, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_key_freeze as KF  # noqa: E402
import kpc_pin_edge as PE  # noqa: E402
import kpc_problem_solver as PS  # noqa: E402

ok = True


def check(cond, msg):
    global ok
    ok = ok and bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


# 0. no rules hash moves (the 2-fer run 42649544758 is going)
for k, h in (('us-key', '464d2ce92eda'), ('ca-key', '8feccbb7d9ee'), ('world-key', '10e4092cc97f'), ('fers', '3b3c9a5992bb')):
    check(KF.rules_hash(k) == h, f'{k} rules hash stays {h}')
check('kpc_problem_solver.py' in KF.NOT_RULES, 'the problem solver is not a rules file')

ov = json.load(open(ROOT / 'data/us-key/overrides.json', encoding='utf-8'))['parks']
# 1. the 14 WSR corridor joins (Brandon Nov 8) are back
WSR = {'US-0197': ['fwsr208', 'fwsr41'], 'US-0894': ['fwsr149', 'fwsr252', 'fwsr79'], 'US-12786': ['fwsr88'], 'US-12794': ['fwsr51'],
       'US-12796': ['fwsr143'], 'US-0684': ['wsrc20'], 'US-0886': ['wsrc23'], 'US-9758': ['fwsr180', 'fwsr6', 'fwsr95'],
       'US-12235': ['fwsr16', 'fwsr98'], 'US-12787': ['fwsr89'], 'US-12791': ['fwsr116', 'fwsr40'], 'US-12797': ['fwsr144', 'fwsr63'],
       'US-12800': ['fwsr168'], 'US-12801': ['fwsr231']}
for r, ids in WSR.items():
    e = ov.get(r) or {}
    check(set(ids) <= set(e.get('join') or []) and all(i in (e.get('fp') or {}) for i in ids) and not set(ids) & set(e.get('no') or []),
          f'{r} WSR corridor join {ids} is back with its fingerprint')
check(ov['US-0197'].get('no') == ['wsrc4'], 'US-0197 keeps its Nov 2 NO on wsrc4')
# 2. the Nov 8 KPC-Data rows are here (spot checks)
check('sggab44' in (ov.get('US-3722') or {}).get('join', []), 'US-3722 New Echota hand-layer join (Nov 8) is here')
check('sggaa904' in (ov.get('US-12418') or {}).get('fp', {}), 'US-12418 Tallulah fingerprint of Nov 8 is here')
check('Quality grade PR#50' in (ov.get('US-2200') or {}).get('why', ''), 'US-2200 carries the Nov 8 Quality unjoin note')
ca = json.load(open(ROOT / 'data/ca-key/overrides.json', encoding='utf-8'))['parks']
check('CA-2897' in ca and 'CA-2373' in ca and 'Quality grade PR#50' in ca['CA-2373'].get('why', ''), 'CA-2897 / CA-2373 rows of Nov 8 are here')
# 3. accepted name-matched groups
ACC = {'US-3523': ['184146', '184147'], 'US-1696': ['51804', '51807', '51805'], 'US-6275': ['sgtnh17', '255681'], 'US-6135': ['273812', 'sgwyc14095'],
       'US-10237': ['200896', '200897'], 'US-0384': ['3871', '4815'], 'US-4236': ['sgiaa34365', '5387'], 'US-0723': ['3292'], 'US-9758': ['sgnca9068'],
       'US-0680': ['3500'], 'US-0456': ['5404', '4447'], 'US-0733': ['3201'], 'US-12601': ['3907', '4852'], 'US-4475': ['2809', '2781'],
       'US-4524': ['2697', '2617'], 'US-9387': ['157891']}
for r, ids in ACC.items():
    e = ov.get(r) or {}
    check(set(ids) <= set(e.get('join') or []) and 'Nov 9' in (e.get('decided_by') or '') and not set(ids) & set(e.get('no') or []),
          f'{r} accepted {ids} (Nov 9, Quality pending)')
check(ov['US-10237'].get('approx') is True, 'US-10237 fen units are labelled Approximate')
check('sgcab584' in ov['US-3523'].get('no', []) and 'sgcta4199' in ov['US-1696'].get('no', []), 'the older NOs on other layers stay')
for r in ('US-5758', 'US-8396'):
    check(not (ov.get(r) or {}).get('decided_by'), f'{r} held (not accepted)')
# 4. US-10025: the newer NO wins, the stale join is gone
e = ov['US-10025']
check('sgakh1935' in e.get('no', []) and 'sgakh1935' not in (e.get('join') or []) and 'sgakh1935' not in (e.get('fp') or {}),
      'US-10025: the stale join on sgakh1935 is gone, the Nov 2 NO stays')
# 5. NRHP scoped to the hand-joined records in 9 states
sg = json.load(open(ROOT / 'data/state-gis.json', encoding='utf-8'))['states']
NRHP = 'https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/1'
want = {'AL': {379681, 383567}, 'HI': {395518, 400944}, 'KS': {400284}, 'MD': {382060}, 'ND': {379041, 379181, 383579, 400132, 400204},
        'NE': {400205}, 'NV': {397680}, 'OK': {386929, 387660, 400282, 400286}, 'UT': {401149}}
for st, ids in want.items():
    ls = [l for l in sg.get(st, []) if l.get('url') == NRHP]
    got = set(map(int, re.findall(r'\d+', ls[0].get('where', '')))) if len(ls) == 1 else set()
    check(got == ids and ls[0]['where'].startswith('OBJECTID IN ('), f'{st}: NRHP layer limited to {sorted(ids)}')
    for i in ids:
        refs = [r for r, o in ov.items() if f'sgaki{i}' in (o.get('join') or [])]
        check(len(refs) == 1, f'sgaki{i} is a hand join of one park ({refs})')
check(sum(len(v) for v in want.values()) == 18, '18 NRHP records in all')
# 6. KY outlines
pad = {f['properties']['ref']: f for f in json.load(open(ROOT / 'ky-padus-parks.geojson', encoding='utf-8'))['features']}
s = pad['US-10172']
check(s['properties'].get('KDFWR_OID') == 1 and abs(PE.acres_geojson(s['geometry']) - 132.33) < 1.0 and PE.inside(38.1777, -84.9231, PE.geojson_rings(s['geometry'])),
      'Salato US-10172 = KDFWR HQ OID 1, ~132 ac, the pin inside')
for r, ac, pin in (('US-13599', 41.67, (37.8469, -86.9736)), ('US-13600', 79.99, (37.8452, -86.9784))):
    f = pad[r]
    check(abs(PE.acres_geojson(f['geometry']) - ac) < 0.1 and PE.inside(*pin, PE.geojson_rings(f['geometry'])) and 'county tax parcel' in f['properties']['SOURCE'],
          f'{r}: water + KDFWR parcel outline ~{ac} ac, the pin inside')
for r in ('US-13598', 'US-13601', 'US-13606', 'US-13607'):
    check(pad[r]['properties']['SOURCE'].startswith('USGS PAD-US') and 'PARCEL_PIECES' not in pad[r]['properties'], f'{r} keeps its water outline (held)')
ky = json.load(open(ROOT / 'data/ky-answer-key.json', encoding='utf-8'))['parks']
check(ky['US-10172']['tracts'][0][2] == 132 and ky['US-13599']['tracts'][0][2] == 41 and ky['US-13600']['tracts'][0][2] == 79, 'the KY answer key has the new acres')
txt = (ROOT / 'kpc-bounds.js').read_text(encoding='utf-8')
check("?v=20261109a'" in txt and "?v=20261018q'" not in txt, 'the KY outline cache string moved (the new outlines load)')
# 7. problem solver: why a hand join is missing
lay = PS.layer_states(ROOT)
check(lay.get('sgaki', {}).get('states', set()) >= set(want) | {'AK'}, 'layer_states reads the NRHP states')
R = PS.solve('US-X', {'n': 'Fort Test State Historic Site', 't': 'Other', 'm': [], 'c': []}, (40.0, -100.0), {}, {'join': ['sgakd1']}, 'US-ZZ',
             ctx={'layer_states': {'sgakd': {'name': 'NPS legal boundary', 'states': {'AK'}}}})
check(R.get('fault') == 'key setup' and any('set up only for AK' in w for w in R['reasons']) and R['verdict'] == 'needs a person',
      'a hand join on a layer set up for another state is explained (key setup)')
R = PS.solve('US-X', {'n': 'Fort Test', 't': 'Other', 'm': [], 'c': []}, (40.0, -100.0), {}, {'join': ['12345']}, 'US-ZZ', ctx={})
check(R.get('fault') == 'key setup' and any('saved id is always loaded by id' in w and '464d2ce92eda' in w for w in R['reasons']),
      'a PAD-US hand join the key did not read is explained (Nov 9 PAD-US load fix: the next US key build reads it)')
# 8. problem solver: no saved outline -> the key's own distance (plain case only), never a moved pin
row = {'n': 'Test Canyon Recreation Area', 't': 'Recreation Area', 'm': [], 'c': [['sgzza7', 'Test Canyon Recreation Area', 500, 'held']],
       'bk': ['sgzza7', 4.2, '', '-'], 'held': {'ids': ['sgzza7']}, 'ac': 520}
R = PS.solve('US-X', row, (40.0, -100.0), {}, None, 'US-ZZ', ctx={'cache_note': 'from 2026-11-03'})
check(PS.no_outline_fallback(PS.solve('US-X', dict(row, bk=None), (40.0, -100.0), {}, None, 'US-ZZ'), row, 'sgzza7', row['c'][0][1], ['sgzza7'], 4.2, row['c'], 'US-ZZ', [])['verdict'] == 'pin wrong' and R['verdict'] == 'needs a person' and any('2026-11-03' in w for w in R['reasons']),
      'no saved outline: still a person (fallback written, not wired: Quality decides); the cache date is named')
row2 = dict(row, ac=5000)
check(PS.no_outline_fallback({'type': 'Recreation Area', 'reasons': [], 'verdict': 'needs a person'}, row2, 'sgzza7', row['c'][0][1], ['sgzza7'], 4.2, row['c'], 'US-ZZ', [])['verdict'] == 'needs a person', 'fallback: acres far apart stays with a person')
row3 = dict(row, c=row['c'] + [['sgzza8', 'Test Canyon Recreation Area', 40, 'held']])
check(PS.solve('US-X', row3, (40.0, -100.0), {}, None, 'US-ZZ')['verdict'] == 'needs a person', 'two records with the name: stays with a person')
# 9. scope guard: a state-GIS hand join must name a layer set up for one of the park's states, unless it is held below
HELD = {  # prefix: why it is not set up for the other states this batch (Nov 9 robots checks; see the weekly batch WRITEUP)
    'sgakd': 'NPS Land Resources Division on services1.arcgis.com: robots.txt 403 = disallow; held',
    'sgmng': 'FWS refuge boundaries on services.arcgis.com: robots.txt 403 = disallow; held',
    'sgidd': 'FS BasicOwnership on apps.fs.usda.gov: robots.txt 403 = disallow; held',
    'sgnvg': 'FS forest boundaries on apps.fs.usda.gov: robots.txt 403 = disallow; held',
    'sggae': 'National Heritage Areas on services1.arcgis.com: robots.txt 403 = disallow; held',
    'sgide': 'USACE recreation areas on services7.arcgis.com: robots.txt 403 = disallow; held',
    'sgnmc': 'BLM recreation site polygons on services1.arcgis.com: robots.txt 403 = disallow; held',
    'sgnvh': 'BLM ACEC (gis.blm.gov, allowed): not verified this batch; listed for the next one',
    'sgaki': 'NRHP: the 18 checked records are set up; US-8287 (ME) was not checked this batch',
}
st_of = {}
for f in glob.glob(str(ROOT / 'data/us-key/US-??.json')):
    for r in json.load(open(f, encoding='utf-8')).get('parks') or {}: st_of.setdefault(r, set()).add(pathlib.Path(f).stem[3:])
new_bad = []
for r, o in ov.items():
    for i in o.get('join') or []:
        pre = re.match(r'[a-z]*', str(i)).group(0)
        if pre in lay and r in st_of and not (lay[pre]['states'] & st_of[r]) and pre not in HELD: new_bad.append(f'{r}:{i}')
check(not new_bad, 'every state-GIS hand join is set up for its park\'s state or held with a reason' + (f' ({", ".join(new_bad[:8])})' if new_bad else ''))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
