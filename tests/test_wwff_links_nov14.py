#!/usr/bin/env python3
"""Nov 14 (KPC owner, 2026-11-14): the WWFF -> POTA cross reference (kpc_wwff_links.py) and its two writers
(kpc_search_lists.py mk_k = locations.json column 8, kpc_canada.py = data/canada.json VEFF rows).

Part 1 (always): a synthetic sandbox, no network (urlopen is replaced; a request fails the test).
Part 2 (when a KPC-Data checkout is found: env KPC_DATA, else ../KPC-Data next to this repo): the real lists, built in a temp folder
(this checkout is not written)."""
import contextlib, csv, io, json, os, pathlib, runpy, shutil, sys, tempfile, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
import kpc_wwff_links as WL   # noqa: E402
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def fake_urlopen(req, *a, **k):
    u = req.full_url if hasattr(req, 'full_url') else str(req)
    if u.startswith('https://api.pota.app/location/parks/CA-'):
        class R:
            def read(self): return json.dumps(CA_API.get(u, [])).encode()
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return R()
    raise AssertionError('network request in a test: ' + u)


CA_API = {}
urllib.request.urlopen = fake_urlopen
time.sleep = lambda *a, **k: None


def wj(p, v):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v), encoding='utf-8')


def rows_of(pre):
    return {r[0]: r for r in WL.read_xref(pre)['rows']}


def quiet(f, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: r = f(*a, **k)
        except SystemExit as e: r = e.code
    return r, buf.getvalue()


# ================================================================ part 1: synthetic
d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-'))
os.chdir(d)
WL.MIN_ROWS = {'KFF': 1, 'VEFF': 1}; WL.MIN_POTA = {'KFF': 1, 'VEFF': 1}
POTA_US = [['POTA', 'US-0001', 'Alpha State Park', 37.0, -90.0, 'u'],        # MO
           ['POTA', 'US-0002', 'Bravo National Forest', 38.0, -91.0, 'u'],   # MO
           ['POTA', 'US-0003', 'Charlie State Park', 39.0, -92.0, 'u'],      # MO
           ['POTA', 'US-0005', 'Echo Lake State Park', 36.0, -88.0, 'u'],    # TN only (the WWFF area says MO)
           ['POTA', 'US-0006', 'Foxtrot National Trail', 36.5, -89.5, 'u'],  # MO + TN (POTA lists it in both)
           ['POTA', 'US-7001', 'Golf Wildlife Area', 37.5, -90.5, 'u'],      # MO
           ['POTA', 'US-0099', 'Wrong Park', 30.0, -95.0, 'u'],              # TX
           ['POTA', 'US-7005', 'Kilo Lake State Park', 37.0, -91.0, 'u'],    # MO
           ['POTA', 'US-7006', 'Lima Creek Wildlife Management Area', 38.5, -91.5, 'u'], ['POTA', 'US-7007', 'Lima Creek State Park', 38.503, -91.5, 'u'],
           ['POTA', 'US-0007', 'November Hill', 38.0, -92.0, 'u'], ['POTA', 'US-7008', 'Mike Marsh Conservation Area', 38.703, -91.7, 'u'],
           ['POTA', 'US-1001', 'Kentucky Park', 37.5, -85.0, 'u']]           # KY
# (US-0004 is NOT on the POTA list: retired)
WWFF_ROWS = [['WWFF', 'KFF-0001', 'Alpha', 37.0, -90.0, 'https://wwff.co/directory/', None, 'US-0001'],   # repo + 2018 + rule
             ['WWFF', 'KFF-0002', 'Bravo', 38.01, -91.0, 'https://wwff.co/directory/', None, ''],        # 2018 + rule, no link yet
             ['WWFF', 'KFF-0003', 'Charlie', 39.0, -92.0, 'https://wwff.co/directory/', None, 'US-0099'],  # repo vs 2018: conflict
             ['WWFF', 'KFF-0004', 'Delta', 39.5, -92.5, 'https://wwff.co/directory/', None, ''],         # 2018 says US-0004: retired
             ['WWFF', 'KFF-0005', 'Echo Lake', 36.0, -88.0, 'https://wwff.co/directory/', None, ''],     # 2018 says US-0005: other state
             ['WWFF', 'KFF-0006', 'Foxtrot Trail (MO)', 36.5, -89.5, 'https://wwff.co/directory/', None, ''],   # multi-state park
             ['WWFF', 'KFF-7001', 'Golf Wildlife Area', 37.5135, -90.5, 'https://wwff.co/directory/', None, ''],  # new ref: name rule only, pins 1.5 km apart
             ['WWFF', 'KFF-7005', 'Kilo Lake', 37.0045, -91.0, 'https://wwff.co/directory/', None, ''],  # same name, pins 0.5 km: confirmed alone
             ['WWFF', 'KFF-7006', 'Lima Creek', 38.5, -91.5, 'https://wwff.co/directory/', None, ''],    # two same-name parks within 1 km
             ['WWFF', 'KFF-0007', 'Mike Marsh', 38.7, -91.7, 'https://wwff.co/directory/', None, ''],    # 2018 says US-0007, close pin says US-7008
             ['WWFF', 'KFF-7002', 'Hotel', 37.6, -90.6, 'https://wwff.co/directory/', None, 'US-0002'],  # repo only
             ['WWFF', 'KFF-7003', 'India', 37.7, -90.7, 'https://wwff.co/directory/', None, 'US-0099'],  # hand fix (US-0099 -> US-0003)
             ['WWFF', 'KFF-7004', 'Juliet', 37.8, -90.8, 'https://wwff.co/directory/', None, ''],        # nothing
             ['WWFF', 'KFF-6001', 'Kentucky Park', 37.5, -85.0, 'https://wwff.co/directory/', None, 'US-1001']]  # Kentucky row
KFF = [[r[1], r[2], r[3], r[4], '', 'K-MO', 'K-MO'] for r in WWFF_ROWS if r[1] != 'KFF-6001'] + [['KFF-6001', 'Kentucky Park', 37.5, -85.0, '', 'K-KY', 'K-KY']]
VEFF = [['VEFF-0001', 'Lima Provincial Park', 45.0, -75.0, '', 'VE-ON', 'VE-ON'],     # community + rule
        ['VEFF-0002', 'Mike Provincial Park', 46.0, -76.0, '', 'VE-ON', 'VE-ON'],     # community only
        ['VEFF-0003', 'November Wildlife Area', 47.0, -77.0, '', 'VE-QC', 'VE-QC'],   # community vs rule
        ['VEFF-0004', 'Oscar', 48.0, -78.0, '', 'VE-ON', 'VE-ON'],                    # community gives two parks
        ['VEFF-0005', 'Papa', 49.0, -79.0, '', 'VE-MN', 'VE-MN']]                     # nothing
CAN = {'rows': [['POTA', 'CA-0001', 'Lima Provincial Park', 45.0, -75.0, 'u'], ['POTA', 'CA-0002', 'Mike Provincial Park', 46.2, -76.0, 'u'],
                ['POTA', 'CA-0003', 'November Wildlife Area', 47.0, -77.0, 'u'], ['POTA', 'CA-0009', 'Old November', 47.1, -77.1, 'u'],
                ['POTA', 'CA-0004', 'Oscar A', 48.0, -78.0, 'u'], ['POTA', 'CA-0005', 'Oscar B', 48.01, -78.0, 'u']]}
wj('locations.json', POTA_US + WWFF_ROWS)
wj('kpc-ky-data.json', {'parks': [{'c': 'US-1001', 'n': 'Kentucky Park', 'la': 37.5, 'lo': -85.0}],
                        'kff': [{'c': 'KFF-6001', 'n': 'Kentucky Park', 'la': 37.5, 'lo': -85.0, 'p': 'US-1001'}], 'summits': []})
wj('locations-ky.json', {'box': [36, 39, -90, -81], 'rows': [], 'total': 0})
wj('data/canada.json', CAN)
wj('data/wwff/KFF.json', KFF); wj('data/wwff/VEFF.json', VEFF)
park = lambda ref, n, la, lo, *extra: [n, '', '', '', '', la, lo, 0, 0, 0, *extra]
wj('data/parkinfo/US-MO.json', {'parks': {r: park(r, '', 0, 0) for r in ('US-0001', 'US-0002', 'US-0003', 'US-0006', 'US-7001', 'US-7005', 'US-7006', 'US-7007', 'US-0007', 'US-7008')}})
wj('data/parkinfo/US-TN.json', {'parks': {r: park(r, '', 0, 0) for r in ('US-0005', 'US-0006')}})
wj('data/parkinfo/US-TX.json', {'parks': {'US-0099': park('US-0099', '', 0, 0)}})
wj('data/parkinfo/CA.json', {'parks': {r[1]: park(r[1], r[2], r[3], r[4], 'QC' if r[1] in ('CA-0003', 'CA-0009') else 'ON') for r in CAN['rows']}})
SRC = {'repo_baseline': {r[1]: r[7] for r in WWFF_ROWS if r[7]},
       'community_veff_2025': {'pairs': [['VEFF-0001', 'CA-0001'], ['VEFF-0002', 'CA-0002'], ['VEFF-0003', 'CA-0009'],
                                         ['VEFF-0004', 'CA-0004'], ['VEFF-0004', 'CA-0005']]},
       'community_kff_2018': {'direct_from': 1, 'direct_to': 7, 'direct_except': [], 'pairs': []},
       'hand': [{'wwff': 'KFF-7003', 'pota': 'US-0003', 'decided_by': 'KPC owner', 'date': '2026-11-14', 'why': 'test'}]}
# the KFF 2025 list (the main US community list)
WWFF_ROWS += [['WWFF', 'KFF-0008', 'Oscar Bend', 39.2, -92.2, 'https://wwff.co/directory/', None, 'US-0099'],     # site US-0099; 2025 + 2018 say US-0008
              ['WWFF', 'KFF-7010', 'Papa Pond', 39.3, -92.3, 'https://wwff.co/directory/', None, 'US-0099'],      # site US-0099; 2025 alone says US-7010
              ['WWFF', 'KFF-7011', 'Quebec Hill', 39.4, -92.4, 'https://wwff.co/directory/', None, 'US-7011'],    # 2025: not in POTA
              ['WWFF', 'KFF-0009', 'Romeo Unit', 39.5, -92.5, 'https://wwff.co/directory/', None, ''],            # 2025: US-0009 + US-7012 (primary = same number)
              ['WWFF', 'KFF-7013', 'Sierra Group', 39.6, -92.6, 'https://wwff.co/directory/', None, ''],          # 2025: two parks, no primary
              ['WWFF', 'KFF-0010', 'Tango Flat', 39.7, -92.7, 'https://wwff.co/directory/', None, '']]            # 2018 US-0010, 2025 US-7016
POTA_US += [['POTA', r, n, la, -92.0, 'u'] for r, n, la in (('US-0008', 'Ninth Hill', 39.0), ('US-7010', 'Tenth Hill', 39.0), ('US-7011', 'Quebec Hill Park', 39.4),
            ('US-0009', 'Romeo Unit Park', 39.5), ('US-7012', 'Romeo Annex', 39.5), ('US-7014', 'Sierra One', 39.6), ('US-7015', 'Sierra Two', 39.6),
            ('US-0010', 'Uniform', 39.7), ('US-7016', 'Victor', 39.7))]
KFF += [[r[1], r[2], r[3], r[4], '', 'K-MO', 'K-MO'] for r in WWFF_ROWS[-6:]]
wj('locations.json', POTA_US + WWFF_ROWS); wj('data/wwff/KFF.json', KFF)
mo = json.load(open('data/parkinfo/US-MO.json')); mo['parks'].update({r: park(r, '', 0, 0) for r in ('US-0008', 'US-7010', 'US-7011', 'US-0009', 'US-7012', 'US-7014', 'US-7015', 'US-0010', 'US-7016')})
wj('data/parkinfo/US-MO.json', mo)
SRC['repo_baseline'] = {r[1]: r[7] for r in WWFF_ROWS if r[7]}
SRC['community_kff_2018']['direct_to'] = 10
SRC['community_kff_2025'] = {'pairs': [['KFF-0008', 'US-0008'], ['KFF-7010', 'US-7010'], ['KFF-0009', 'US-7012'], ['KFF-0009', 'US-0009'],
                                       ['KFF-7013', 'US-7014'], ['KFF-7013', 'US-7015'], ['KFF-0010', 'US-7016']], 'not_in_pota': ['KFF-7011'], 'deleted': []}
wj(WL.SOURCES, SRC)

r, out = quiet(WL.main, ['build', '--date', '2026-11-14'])
check(r == 0, 'build runs on the sandbox')
K, V = rows_of('KFF'), rows_of('VEFF')
st = lambda R, ref: (R[ref][5], R[ref][3])
check(st(K, 'KFF-0001') == ('confirmed', 'US-0001') and K['KFF-0001'][4] == 'repo+community-KFF-2018+rule-same-name-close-pin', 'repo + 2018 + rule agree: confirmed, all three sources named')
check(st(K, 'KFF-0002') == ('confirmed', 'US-0002'), '2018 direct range + name rule agree: confirmed (no site link yet)')
check(st(K, 'KFF-0003') == ('conflict', 'US-0099|US-0003') and K['KFF-0003'][4].startswith('repo|community-KFF-2018'), 'repo and 2018 disagree: conflict, both parks and both sources listed')
check(st(K, 'KFF-0004')[0] == 'proposed' and 'not on today' in K['KFF-0004'][8], 'a retired POTA park is never confirmed')
check(st(K, 'KFF-0005')[0] == 'proposed' and 'POTA lists the park in TN' in K['KFF-0005'][8], 'a park POTA lists only in another state is never confirmed (no link across states)')
check(st(K, 'KFF-0006') == ('confirmed', 'US-0006'), 'a park POTA lists in several states (a trail) is confirmed in each of them')
check(st(K, 'KFF-7001') == ('proposed', 'US-7001') and K['KFF-7001'][4] == 'rule-name-distance', 'same name but pins 1.5 km apart, no other source: proposed (not confirmed)')
check(st(K, 'KFF-7005') == ('confirmed', 'US-7005') and K['KFF-7005'][4] == 'rule-same-name-close-pin', 'owner rule: same name + same state + pins within 1 km + one such park: confirmed alone')
check(K['KFF-7006'][5] == 'conflict' and set(K['KFF-7006'][3].split('|')) == {'US-7006', 'US-7007'}, 'owner rule: two same-name parks within 1 km: not confirmed (a conflict listing both)')
check(st(K, 'KFF-0007') == ('conflict', 'US-0007|US-7008'), 'owner rule: another source naming a different park: conflict, never confirmed over the disagreement')
check(st(K, 'KFF-7002') == ('proposed', 'US-0002') and K['KFF-7002'][4] == 'repo', 'repo only: proposed')
check(st(K, 'KFF-7003') == ('confirmed', 'US-0003') and K['KFF-7003'][4] == 'hand' and 'other sources: repo US-0099' in K['KFF-7003'][8], 'a hand decision is confirmed and names the other source')
check(st(K, 'KFF-7004') == ('none', ''), 'no source: none')
check(st(K, 'KFF-0008') == ('confirmed', 'US-0008') and K['KFF-0008'][8].startswith(WL.REPLACES + 'US-0099'), '2025 + 2018 against the site link alone: the 2025 value is confirmed, marked as replacing it')
check(st(K, 'KFF-7010')[0] == 'conflict', '2025 alone against the site link: conflict (no change on one source)')
check(st(K, 'KFF-7011') == ('conflict', 'US-7011') and 'not in POTA' in K['KFF-7011'][8], "2025 'not in POTA' against a site link: conflict, never confirmed")
check(st(K, 'KFF-0009') == ('confirmed', 'US-0009') and 'US-7012' in K['KFF-0009'][8], '2025 with several parks: the same-number primary counts (with 2018), the others are noted')
check(st(K, 'KFF-7013')[0] == 'conflict' and set(K['KFF-7013'][3].split('|')) == {'US-7014', 'US-7015'}, '2025 with several parks and no clear primary: conflict listing all')
check(st(K, 'KFF-0010') == ('proposed', 'US-7016') and 'the 2018 list said US-0010' in K['KFF-0010'][8], 'the 2018 list is weaker: a 2018 value the 2025 list contradicts is left out (noted)')
check(st(V, 'VEFF-0001') == ('confirmed', 'CA-0001'), 'VEFF community + rule: confirmed')
check(st(V, 'VEFF-0002')[0] == 'proposed', 'VEFF community only: proposed')
check(st(V, 'VEFF-0003') == ('conflict', 'CA-0009|CA-0003'), 'VEFF community vs rule: conflict')
check(st(V, 'VEFF-0004')[0] == 'conflict' and 'one WWFF ref, several POTA parks' in V['VEFF-0004'][8], 'one WWFF ref -> two POTA parks is flagged')
check(st(V, 'VEFF-0005') == ('none', ''), 'VEFF nothing: none')
rev = {r['wwff_ref']: r for r in csv.DictReader(open(WL.REVIEW))}
check({'KFF-0003', 'KFF-0004', 'KFF-0005', 'KFF-7001', 'KFF-7002', 'KFF-7003', 'VEFF-0002', 'VEFF-0003', 'VEFF-0004'} <= set(rev)
      and 'KFF-0001' not in rev and 'KFF-7004' not in rev, 'review list: proposed, conflict and hand rows; not confirmed or none')
check(rev['KFF-0003']['pota_name'] == 'Wrong Park | Charlie State Park', 'review list: both parks named')

# ---- the search list (mk_k)
import kpc_search_lists as SL   # noqa: E402
kff = {r[0]: {'name': r[1], 'la': r[2], 'lo': r[3]} for r in KFF}
quiet(SL.update, kff=kff)
L = {r[1]: r for r in json.load(open('locations.json')) if r[0] == 'WWFF'}
check(L['KFF-0002'][7] == 'US-0002', 'mk_k: a row with no link gets the confirmed link')
check(L['KFF-0003'][7] == 'US-0099', 'mk_k: a conflict never changes the link the row has')
check(L['KFF-7001'][7] == '' and L['KFF-0004'][7] == '' and L['KFF-0005'][7] == '', 'mk_k: proposed links are not written')
check(L['KFF-7002'][7] == 'US-0002', 'mk_k: a link the row already has is kept')
check(L['KFF-7003'][7] == 'US-0003', 'mk_k: a hand decision replaces the old link')
check(L['KFF-0008'][7] == 'US-0008' and L['KFF-7010'][7] == 'US-0099' and L['KFF-7011'][7] == 'US-7011', 'mk_k: two sources replace the site link; one source (or a 2025 none) never does')
check(L['KFF-0009'][7] == 'US-0009' and L['KFF-7013'][7] == '', 'mk_k: one-to-many: the clear primary is written; no primary = nothing written')
check(L['KFF-6001'][7] == 'US-1001', 'mk_k: Kentucky still comes from kpc-ky-data.json')
check(all(len(r) == 8 and r[6] is None for r in L.values()), 'mk_k: row shape unchanged (8 columns, column 7 None)')
check({r[1]: r[3:5] for r in json.load(open('locations.json')) if r[0] == 'POTA'} == {r[1]: r[3:5] for r in POTA_US}, 'POTA rows untouched (no pin moved)')
# no cross reference file: exactly as before (old link carried forward only)
wj('locations.json', POTA_US + WWFF_ROWS)
os.rename(WL.XREF['KFF'][0], 'x.json')
_, out = quiet(SL.update, kff=kff)
L = {r[1]: r for r in json.load(open('locations.json')) if r[0] == 'WWFF'}
check({k: v[7] for k, v in L.items()} == {r[1]: r[7] for r in WWFF_ROWS} and 'missing or unreadable' in out, 'mk_k without the file: links carried forward only, as before (and said)')
os.rename('x.json', WL.XREF['KFF'][0])

# ---- data/canada.json (kpc_canada.py)
for pv in 'AB BC MB NB NL NS NT NU ON PE QC SK YT'.split(): CA_API[f'https://api.pota.app/location/parks/CA-{pv}'] = []
CA_API['https://api.pota.app/location/parks/CA-ON'] = [{'reference': r[1], 'name': r[2], 'latitude': r[3], 'longitude': r[4]} for r in CAN['rows']]
quiet(runpy.run_path, str(SCR / 'kpc_canada.py'), run_name='__main__')
C = json.load(open('data/canada.json'))['rows']
CW = {r[1]: r for r in C if r[0] == 'WWFF'}
check(CW['VEFF-0001'][6:] == [None, 'CA-0001'] and CW['VEFF-0002'][6:] == [None, ''] and CW['VEFF-0003'][6:] == [None, ''], 'canada.json: VEFF rows get [None, confirmed link], blank otherwise')
check({r[1]: r[:5] for r in C if r[0] == 'POTA'} == {r[1]: r[:5] for r in CAN['rows']}, 'canada.json: POTA rows unchanged (name, pin)')
os.rename(WL.XREF['VEFF'][0], 'x.json')
quiet(runpy.run_path, str(SCR / 'kpc_canada.py'), run_name='__main__')
check(all(len(r) == 6 for r in json.load(open('data/canada.json'))['rows'] if r[0] == 'WWFF'), 'canada.json without the file: VEFF rows stay 6 long, as before')
os.rename('x.json', WL.XREF['VEFF'][0])

# ---- a person's answers in the review list
rv = list(csv.DictReader(open(WL.REVIEW)))
for r in rv:
    if r['wwff_ref'] == 'KFF-7001': r['person_decision'] = 'yes'
    if r['wwff_ref'] == 'VEFF-0002': r['person_decision'] = 'no'
    if r['wwff_ref'] == 'VEFF-0003': r['person_decision'] = 'CA-0003'
with open(WL.REVIEW, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rv[0])); w.writeheader(); w.writerows(rv)
quiet(WL.main, ['build', '--date', '2026-11-21'])
K, V = rows_of('KFF'), rows_of('VEFF')
check(st(K, 'KFF-7001') == ('confirmed', 'US-7001') and K['KFF-7001'][4] == 'hand', "review answer 'yes': confirmed by hand")
check(st(V, 'VEFF-0003') == ('confirmed', 'CA-0003'), 'review answer with a POTA ref: that park, confirmed by hand')
check(V['VEFF-0002'][5] == 'proposed' and 'answered no' in V['VEFF-0002'][8], "review answer 'no': never written")
rev = {r['wwff_ref']: r for r in csv.DictReader(open(WL.REVIEW))}
check(rev['KFF-7001']['person_decision'] == 'yes' and rev['VEFF-0002']['person_decision'] == 'no', 'review answers are kept in the next list')
check(K['KFF-0001'][7] == '2026-11-14' and K['KFF-7001'][7] == '2026-11-21', 'checked_date: kept when the answer is the same, new when it changed')

# ---- fail closed
before = {p: open(p).read() for p in WL.XREF['KFF'] + WL.XREF['VEFF'] + [WL.REVIEW]}
WL.MIN_ROWS = {'KFF': 100, 'VEFF': 1}
r, out = quiet(WL.main, ['build'])
check(r == 1 and 'nothing written' in out and before == {p: open(p).read() for p in before}, 'a short WWFF copy: nothing written, exit 1')
WL.MIN_ROWS = {'KFF': 1, 'VEFF': 1}
SRC2 = dict(SRC, repo_baseline={}, community_kff_2018={'pairs': []}, community_veff_2025={'pairs': []}, hand=[])
wj(WL.SOURCES, SRC2); WL.CLOSE_KM = -1
r, out = quiet(WL.main, ['build'])
WL.CLOSE_KM = 1.0
check(r == 1 and 'would drop' in out and before == {p: open(p).read() for p in before}, 'losing over a fifth of the confirmed links: nothing written, exit 1')
wj(WL.SOURCES, SRC)
txt = ''.join(open(p).read() for p in before).lower()
check(not any(x in txt for x in ('protectedplanet', 'wdpa', 'iucn')), 'no WDPA ids, links or IUCN categories in the outputs')
shutil.rmtree(d, ignore_errors=True)

# ================================================================ part 2: the real lists
data = pathlib.Path(os.environ.get('KPC_DATA') or ROOT.parent / 'KPC-Data')
if not (data / 'data' / 'wwff' / 'KFF.json').exists():
    print('SKIP real data: no KPC-Data checkout (set KPC_DATA)')
else:
    import importlib; importlib.reload(WL)
    t = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-real-'))
    for f in ('locations.json', 'kpc-ky-data.json', 'data/canada.json', WL.SOURCES):
        (t / f).parent.mkdir(parents=True, exist_ok=True); shutil.copy(ROOT / f, t / f)
    os.chdir(t)
    r, out = quiet(WL.main, ['build', '--data', str(data), '--date', '2026-11-14'])
    check(r == 0, 'real: build runs')
    K, V = rows_of('KFF'), rows_of('VEFF')
    print('     ' + ' | '.join(x for x in out.splitlines() if 'WWFF links' in x))
    for ref in ('KFF-4642', 'KFF-4643', 'KFF-4645'):
        check(st(K, ref) == ('confirmed', 'US-4475') and K[ref][4] == 'hand', f'real: {ref} -> US-4475 Caribou-Targhee (hand fix of US-4575)')
    CHG = {'KFF-0302': 'US-0302', 'KFF-2357': 'US-2357', 'KFF-0465': 'US-0465', 'KFF-0646': 'US-0646', 'KFF-0680': 'US-0680', 'KFF-1542': 'US-1542',
           'KFF-2776': 'US-2776', 'KFF-2805': 'US-2805', 'KFF-4666': 'US-8163', 'KFF-4800': 'US-6344', 'KFF-6705': 'US-6444'}
    check(all(K[x][5] == 'confirmed' and K[x][3] == p and K[x][8].startswith(WL.REPLACES) for x, p in CHG.items()),
          'real: site link against the 2025 list + 2018 / close pin: the 2025 value is confirmed and marked as replacing the site link (11)')
    check(K['KFF-4255'][3] == 'US-4304' and K['KFF-4304'][5] == 'conflict', 'real: KFF-4255 / 4304: the 2025 list sides with the site; the 2018 value is left out')
    check(K['KFF-0680'][3] == 'US-0680' and 'US-8090' in K['KFF-0680'][8], 'real: KFF-0680 (11 POTA parks in the 2025 list): the same-number primary, the others noted')
    six = ['VEFF-0871', 'VEFF-1246', 'VEFF-2137', 'VEFF-2176', 'VEFF-2379', 'VEFF-4287']
    check(all(V[x][5] == 'conflict' for x in six), 'real: the 6 Canada disagreements are conflicts with both sides')
    check(V['VEFF-2501'][5] == 'conflict', 'real: VEFF-2501 (two POTA parks in the community list) is flagged')
    loc = json.load(open('locations.json'))
    P = {x[1] for x in loc if x[0] == 'POTA'} | {x[1] for x in json.load(open('data/canada.json'))['rows'] if x[0] == 'POTA'}
    check(all(x[3] in P for R in (K, V) for x in R.values() if x[5] == 'confirmed'), 'real: every confirmed link is a park on today\'s POTA list')
    check(all(x[5] != 'confirmed' or x[4] in ('hand', 'rule-same-name-close-pin') or '+' in x[4] for R in (K, V) for x in R.values()), 'real: every confirmed link has two sources, the close-pin rule or a hand decision')
    check(len(K) == 7450 and len(V) == 5264, f'real: one row per WWFF ref ({len(K)} KFF, {len(V)} VEFF)')
    check(all(os.path.getsize(p) < 1_000_000 for p in WL.XREF['KFF'] + WL.XREF['VEFF'] + [WL.REVIEW]), 'real: every output under 1 MB')
    r, out = quiet(WL.main, ['preview'])
    print('     ' + out.replace('\n', ' / '))
    chg = {l.split()[1]: (l.split()[2], l.split()[3]) for l in out.splitlines() if l.startswith('  change')}
    want = {k: v for k, v in CHG.items()}; want.update({'KFF-4642': 'US-4475', 'KFF-4643': 'US-4475', 'KFF-4645': 'US-4475'})
    check({k: v[1] for k, v in chg.items()} == want, f'real: the only links that change are the 11 two-source fixes and the 3 Caribou-Targhee fixes ({len(chg)})')
    shutil.rmtree(t, ignore_errors=True)

os.chdir(tempfile.mkdtemp(prefix='kpc-wwff-end-'))   # kpc_save writes its status file at exit, relative to here: never into this checkout
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
