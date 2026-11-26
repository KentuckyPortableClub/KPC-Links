#!/usr/bin/env python3
"""25 Nov 2026, batch 16 (grade of #380 round 15 + the owner's 25v test). Invented records only.
  1  published key record ids use the agency's own id ('sgmne' + su_id), never the row number (OBJECTID); the store reader, the
     outline cutter and the outline scorer spell one file the same way; a number lookup never finds an agency-keyed record;
     old ids follow their proven fresh record (fresh_old_parks)
  2  _sane_ac on the fresh records' acres (square feet / metres)
  3  the KPC_KEY_ONLY_PARKS keep path goes through fresh_old_parks
  (4, 5: the website-copy sha guard and 'never writes into originals' are in tests/test_pc_kit_nov24.py)
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, math, os, pathlib, re, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_store_attrs as SA  # noqa: E402
import kpc_key_rules as KR  # noqa: E402
import kpc_match_checks as MC  # noqa: E402
import kpc_same_land as SL  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def rec(oid, su=None, name='MINNESOTA VALLEY', layer='sgmne', x=-93.5):
    a = {'objectid': oid, 'su_acres': 16.4, 'mgtprjname': name}
    if su is not None: a['su_id'] = su
    q = 10 ** 6; pts = [(x, 44.7), (x + .01, 44.7), (x + .01, 44.71), (x, 44.71), (x, 44.7)]
    ring = [round(pts[0][0] * q), round(pts[0][1] * q)]   # the store's ring: first point, then steps (q = 6 decimals)
    for (ax, ay), (bx_, by_) in zip(pts, pts[1:]): ring += [round(bx_ * q) - round(ax * q), round(by_ * q) - round(ay * q)]
    return {'key': f'{layer}@{oid}' if False else f'{layer}{oid}', 'layer': layer, 'record_id': str(oid), 'record_name': name,
            'attributes': a, 'q': 6, 'rings': [ring], 'read': '2026-11-25', 'publishable': True, 'layer_url': 'https://x.example/0'}


# ---- 1: the agency's own id ---------------------------------------------------------------------------------------------------
rs = [rec(3033, 89125.0), rec(3046, 89126), rec(15), rec(500, 777), rec(501, 777), rec(600, 3033),
      {'key': '237576', 'layer': 'PAD-US', 'record_id': '237576', 'record_name': 'Some Park', 'attributes': {'su_id': 5}, 'rings': []}]
pk = SA.publish_keys(rs)
check(f"1: a DNR parcel is spelled by its su_id with a leading zero, not its row number ({pk[0]}, {pk[1]})", pk[0] == 'sgmne089125' and pk[1] == 'sgmne089126')
check('1: a record with no su_id keeps its row spelling; PAD-US is untouched (its own Unit id field is not an agency record id)',
      pk[2] == 'sgmne15' and pk[6] == '237576')
check('1: two records with ONE su_id both keep their row spelling (never two records, one key)', pk[3] == 'sgmne500' and pk[4] == 'sgmne501')
check("1: every key in the file is different (an su_id 3033 parcel is 'sgmne03033', never row 3033's key)",
      pk[5] == 'sgmne03033' and len(set(pk)) == len(pk))
pk2 = SA.publish_keys([rec(15), rec(700, 15)])
check("1: an su_id equal to a record's row number never clashes: 'sgmne015' (agency 15) and 'sgmne15' (row 15)",
      pk2 == ['sgmne15', 'sgmne015'])
def wrec(oid, u):
    return {'key': f'sgmna{oid}', 'layer': 'sgmna', 'record_id': str(oid), 'attributes': {'objectid': oid, 'uniqueid': u}}
check("1: a DNR wildlife area is spelled by its uniqueid ('WMA0038200' -> 'sgmna038200'), the same letters on every record",
      SA.publish_keys([wrec(1, 'WMA0038200'), wrec(2, 'WMA0012900'), wrec(3, None)]) == ['sgmna038200', 'sgmna012900', 'sgmna3'])
check('1: ids with different letters on one layer are never cut to digits (two ids could become one): the row spelling',
      SA.publish_keys([wrec(1, 'WMA0038200'), wrec(2, 'AMA0038201')]) == ['sgmna1', 'sgmna2'])
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    doc = {'area': 'US-ZZ', 'kpcstore_layers': True, 'made': '2026-11-25', 'records': rs[:6],
           'manifest': {'sgmne': {'complete': True, 'source_count': 6, 'store_count': 6, 'read': '2026-11-25'}}}
    with gzip.open(td / 'US-ZZ.layer-records.json.gz', 'wt', encoding='utf-8') as fh: json.dump(doc, fh)
    SA.run(str(td), str(td / 'attrs.json.gz'), today='2026-11-25')
    with gzip.open(td / 'attrs.json.gz', 'rt', encoding='utf-8') as fh: d = json.load(fh)
    r_ = d['records']
    check('1: the store reader keys the parcel by its su_id and marks it (never found by a row number)',
          'sgmne089125' in r_ and r_['sgmne089125'].get('_agk') == 1 and r_['sgmne089125'].get('su_id') == 89125.0 and 'sgmne3046' not in r_
          and 'sgmne15' in r_ and not r_['sgmne15'].get('_agk'))
    check('1: the id file is format 14 (the PC test remakes an older one)', d.get('format') == 14)
    import kpc_outlines_from_key as OK_
    sr = OK_.store_records(str(td), 'US-ZZ')
    check('1: the outline cutter spells the same file the same way (the key ids and the outline ids agree)',
          set(sr) == set(pk[:6]) and 'sgmne089125' in sr)
    import kpc_outline_score as OS_
    by_id, _bn = OS_.store_index(str(td))
    check('1: the outline scorer too', set(by_id) == set(pk[:6]))

src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ns = {'os': os, 're': re, 'json': json, 'gzip': gzip, 'math': math, 'KR': KR, 'MC': MC, 'SL': SL, 'notice': lambda *a: None}
exec(src[src.index('def _oid(a)'):src.index('\n', src.index('def _oid(a)'))], ns)
exec(src[src.index('_RA = [None]'):src.index('\nimport kpc_same_land as SL')] if '_RA = [None]' in src else '', ns)
if 'store_fields' in ns:
    ns['_RA'][0] = {'sgmne3045': {'_agk': 1, 'su_id': 3045, '_nm': 'OTHER LAND'}, 'sgnya12': {'UNIT': 'X', '_nm': 'X'}}
    ns['_RA_RF'][0] = {}
    check("1: the key's row-number lookup never takes an agency-keyed record (old 'sgmne3045' is not su_id 3045)",
          ns['store_fields']('sgmne3045', {'Unit_Nm': 'MINNESOTA VALLEY'})[0] != 'id' and ns['store_fields']('sgnya12', {})[0] == 'id')
else:
    check("1: the key's row-number lookup refuses an agency-keyed record (source)", "if not (_e or {}).get('_agk')" in src)
exec(src[src.index('RA_USED = {}'):src.index('\ndef _maiden6')], ns)
recs = [{'OBJECTID': 'sgmne89125', 'Unit_Nm': 'MINNESOTA VALLEY', 'GIS_Acres': 16.4, '_fresh': True},
        {'OBJECTID': 'sgmne3045', 'Unit_Nm': 'OTHER', 'GIS_Acres': 5.0, '_fresh': True},    # su_id 3045: another parcel
        {'OBJECTID': 'sgmne9001~old', 'Unit_Nm': 'GONE', 'GIS_Acres': 5, '_hint': True}]
old = {'US-9200': {'n': 'Minnesota Valley State Recreation Area', 'm': [['sgmne3045', 'MINNESOTA VALLEY', 16, 'name'], ['sgmne9001', 'GONE', 5, 'name']]}}
new = ns['fresh_old_parks'](old, {'sgmne3045': 'sgmne89125'}, recs)['US-9200']['m']
check(f"1: an old row-number id follows its proven parcel to the agency id, never the parcel whose su_id is that number ({new[0][:2]})",
      new[0][0] == 'sgmne89125' and new[0][2] == 16 and new[1][0] == 'sgmne9001~old')

# ---- 2: _sane_ac on the fresh acres (the store reader's record_acres, and fresh_records)  ---------------------------------------------------------------------------------------------
fr = src[src.index('def fresh_records('):src.index('\ndef fresh_old_parks(')]
check('2: the fresh records size goes through the live reader check (square feet / metres)',
      "rec['GIS_Acres'] = _sane_ac(float(e.get('_ac') or pad.get('GIS_Acres') or 0), rec['_bb'])" in fr)
exec(src[src.index('def _sane_ac('):src.index('\n_SAVED_NAMED')], ns)
r40 = rec(9, 1)
check("2: the store reader's record_acres: 40 acres stays, 1,742,400 (square feet) becomes 40, an impossible size = None (measured)",
      SA.record_acres(dict(r40, attributes={'su_acres': 40})) == 40 and SA.record_acres(dict(r40, attributes={'su_acres': 1742400})) == 40.0
      and SA.record_acres(dict(r40, attributes={'su_acres': 9e12})) is None)
bb = [-93.5, 44.7, -93.49, 44.71]   # about 0.8 x 1.1 km = ~220 acres
check('2: a 40-acre parcel stays; 1,742,400 (square feet) becomes 40; an impossible size is left out (0 = measured)',
      ns['_sane_ac'](40, bb) == 40 and ns['_sane_ac'](1742400, bb) == 40.0 and ns['_sane_ac'](9e12, bb) == 0)

# ---- 3: the key-only keep path ----------------------------------------------------------------------------------------------------
run_ = src[src.index('def run(st):'):]
i = run_.index("_old = json.load(open(OUT / f'US-{st}.json')).get('parks', {}); _kept = 0")
check('3: the KPC_KEY_ONLY_PARKS keep path reads the website key through fresh_old_parks',
      "if _kr('KPC_STORE_FRESH'): _old = fresh_old_parks(_old, _alias, recs)" in run_[i:i + 400] and run_.count('fresh_old_parks(') == 3)

# ---- 4: a layer whose address changed keeps its saved prefix (Adirondack Park, NY 5:43 PM test) ------------------------------
_cwd = os.getcwd(); os.chdir(ROOT)
try:
    hs = {'__name__': 'kpc_us_key_part', '__file__': str(ROOT / '.github/scripts/kpc_us_key.py')}
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()): exec(compile(src[:src.index('\nidx = {}')], 'kpc_us_key.py', 'exec'), hs)
finally:
    os.chdir(_cwd)
bl = [x[0] for x in hs['XS'] if 'BluelinePolygon' in x[1]]
# the owner's PC: a build had written layers.json with the polygon as 'sgnye'; the table's prefix must still win
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    import shutil as _sh
    _sh.copytree(ROOT / 'data', td / 'data', ignore=_sh.ignore_patterns('*.gz', 'outlines', 'trails', 'world-key', 'ca-key', 'access*', 'pota', 'tracts'))
    lj = json.loads((td / 'data/us-key/layers.json').read_text())
    lj['sgnye'] = ['https://services2.arcgis.com/8krRUWgifzA4cgL3/ArcGIS/rest/services/BluelinePolygon/FeatureServer/0/query', '', 'x']
    (td / 'data/us-key/layers.json').write_text(json.dumps(lj))
    os.chdir(td)
    try:
        hs2 = {'__name__': 'kpc_us_key_part', '__file__': str(ROOT / '.github/scripts/kpc_us_key.py')}
        with contextlib.redirect_stdout(io.StringIO()): exec(compile(src[:src.index('\nidx = {}')], 'kpc_us_key.py', 'exec'), hs2)
    finally:
        os.chdir(_cwd)
bl2 = [x[0] for x in hs2['XS'] if 'BluelinePolygon' in x[1]]
check(f"4: the APA polygon layer keeps the prefix its store records carry ('sgnyc', not a new one: {bl}) and its fixed name",
      bl == ['sgnyc'] and hs['FIXED_NAME'].get('sgnyc') == 'Adirondack Park' and sorted(x[0] for x in hs['XS'] if x[0].startswith('sgny')) == ['sgnya', 'sgnyb', 'sgnyc', 'sgnyd'])
check(f"4: ... also when a build's layers.json already names the polygon 'sgnye' (the owner's PC): still 'sgnyc' ({bl2})",
      bl2 == ['sgnyc'] and hs2['FIXED_NAME'].get('sgnyc') == 'Adirondack Park')

# ---- 5: a fresh record carries its layer's second name (US-2077 Honeoye Lake State Park) -----------------------------------------
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    hr = rec(361, None, 'Honeoye Marine Park', 'sgnyb', -77.5078)
    hr['attributes'] = {'OBJECTID': 361, 'Name': 'Honeoye Marine Park', 'Label': 'Honeoye Lake Marine Park', 'Acreage': 8.818, 'Total_acre': 9}
    hr['layer_url'] = 'https://services.arcgis.com/1xFZPtKn1wKC6POA/ArcGIS/rest/services/NYS_Park_Polygons/FeatureServer/0/query'
    doc = {'area': 'US-YY', 'kpcstore_layers': True, 'made': '2026-11-25', 'records': [hr],
           'manifest': {'sgnyb': {'complete': True, 'source_count': 1, 'store_count': 1, 'read': '2026-11-25'}}}
    with gzip.open(td / 'US-YY.layer-records.json.gz', 'wt', encoding='utf-8') as fh: json.dump(doc, fh)
    SA.run(str(td), str(td / 'attrs.json.gz'), today='2026-11-25')
    with gzip.open(td / 'attrs.json.gz', 'rt', encoding='utf-8') as fh: e = json.load(fh)['records'].get('sgnyb361') or {}
check(f"5: NY State Parks' Label is the fresh record's second name, as the live reader reads it (nm2) ({e.get('_nms')}, {e.get('_ac')} ac)",
      e.get('_nm') == 'Honeoye Marine Park' and e.get('_nms') == ['Honeoye Lake Marine Park'] and abs(e.get('_ac', 0) - 8.818) < 0.01)
check("5: the second-name fields come from data/state-gis.json's nm2 (by layer address)",
      SA.second_name_fields().get('https://services.arcgis.com/1xfzptkn1wkc6poa/arcgis/rest/services/nys_park_polygons/featureserver/0') == 'Label')

# ---- 6: W-G13, a national unit is the federal land whatever its link names (US-4518 Finger Lakes National Forest) -------------
state_link = {'name': 'Finger Lakes National Forest', 'link': {'website': 'dec.ny.gov', 'agency': 'NY Dept of Environmental Conservation',
              'site': 'agency (known)', 'usable': True}}
usfs = {'OBJECTID': 3042, 'Unit_Nm': 'Finger Lakes National Forest', 'Mang_Name': 'USFS', 'Mang_Type': 'FED', 'Own_Type': 'FED', 'Des_Tp': 'NF'}
la = MC.link_agency(state_link, 'NY')
check(f"6: POTA's link names the state ({la}); the Forest Service's record with the forest's own name agrees (W-G13)",
      la == 'STATE' and MC.agency_check(state_link, usfs, 'NY') == 'agrees')
check('6: a federal record with ANOTHER name still differs; a non-federal record still differs',
      MC.agency_check(state_link, dict(usfs, Unit_Nm='Hector Ranger District Office'), 'NY') == 'differs'
      and MC.agency_check(state_link, dict(usfs, Mang_Name='NGO', Mang_Type='NGO', Own_Type='NGO'), 'NY') == 'differs')
wma = dict(state_link, name='St. Francis National Forest Wildlife Management Area')
check("6: only when the park's own KIND is the national unit (a state WMA inside a national forest is not)",
      not MC.FED_UNIT.search(wma['name']) and MC.FED_UNIT.search('Finger Lakes National Forest'))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
