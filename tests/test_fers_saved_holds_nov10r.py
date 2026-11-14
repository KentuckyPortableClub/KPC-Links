#!/usr/bin/env python3
"""2-fer finder: saved copies instead of live reads, and a person's hold wins (owner rule, 2026-11-10). Offline: no network.
1 a record on a saved-copy-only host comes from the key's saved copy in EVERY pass (download), never asked live
1 no saved copy for it = the park is held 'saved copy missing for <layer>: needs download' (decide), never silently dropped
1 W&S river corridors come from the saved copy; none saved = the river's pairs are held, not tested as a line park
1 a live line on a saved-copy-only host is not asked; paged reads never keep a partial answer (stall = error)
3 same-land rows and decide() hold two parks joined to the same records; record ids are compared with their area
3 a river / trail half beside an approximate outline is an APPROXIMATE 2-fer (tagged, not held)
3 'none' only clears the key's to-check list: a park with a record join keeps it; point circles and picture traces as before
3 an outline with no source label is not official (fail closed)"""
import gzip, json, os, pathlib, sys, tempfile, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S))
os.chdir(HERE)
os.environ.setdefault('PASS', '2')
os.environ['HTTP_CACHE'] = ''
try: import cv2  # noqa: F401
except Exception: sys.modules['cv2'] = types.ModuleType('cv2')  # noqa: BLE001
import kpc_fers as K
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


K.HC.DIR = ''   # no bundle: a refused host raises in the guard before any request
CALLS = []
_real_get = K.get


def spy_get(url, params, tries=3, timeout=120):
    CALLS.append(url)
    # Nov 11 (KPC owner): never the network. A host the guard refuses still goes to the real get (it raises in the guard before any
    # request, which is what these checks are about); a host the guard would allow gets an empty stand-in answer instead of a live read
    # (the test used to ask kygisserver.ky.gov for real through live_lines).
    if K.HC.kpc_net_guard.host_ok(url)[0]: return {'features': []}
    return _real_get(url, params, 1, 1)


K.get = spy_get
K.time.sleep = lambda s: None
REF_PRE = next(p for p, v in K.LAYERS_US.items() if not K.HC.kpc_net_guard.host_ok(v[0])[0] and p not in ('wsrc',))
RING = [[-80.0, 35.0], [-79.99, 35.0], [-79.99, 35.01], [-80.0, 35.01], [-80.0, 35.0]]

with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    (td / 'us').mkdir()
    with gzip.open(td / 'us/US-NC.json.gz', 'wt') as fh:
        json.dump({'saved': '2026-11-01', 'recs': [{'OBJECTID': f'{REF_PRE}5', 'Unit_Nm': 'Saved Park', '_r': [RING]},
                                                   {'OBJECTID': 'wsrc7', 'Unit_Nm': 'Obed', '_r': [RING]}]}, fh)
    K.CACHE_US = td / 'us'; K._SAVED_BY.clear(); K.SAVED_STR.clear(); K.SAVED_NAME.clear()
    os.environ['KPC_FERS_LIVE_DIR'] = str(td / 'live')
    parks = {'US-T1': {'st': 'US-NC', 'ids': [f'{REF_PRE}5'], 'names': {f'{REF_PRE}5': 'Saved Park'}},
             'US-T2': {'st': 'US-NC', 'ids': [f'{REF_PRE}6'], 'names': {f'{REF_PRE}6': 'Not Saved'}}}
    K.MISSING_SAVED.clear(); CALLS.clear()
    got, bad = K.download(parks, ['US-T1', 'US-T2'], K.DET, K.PREC)
    check('US-T1' in got and got['US-T1'] == [[RING]], 'a saved-copy-only record is read from the saved copy (pass 2-3 download)')
    check(not any(f'{REF_PRE}5' in str(c) for c in CALLS) and K.MAPDATE.get('US-T1', '').startswith('saved copy'), 'the saved record is never asked live; its date says saved copy')
    check('US-T2' in bad and K.MISSING_SAVED.get('US-T2') == REF_PRE, f'a record in no saved copy is held with its layer ({K.MISSING_SAVED})')
    check(K.saved_missing_why('US-T2') == f'saved copy missing for {REF_PRE}: needs download', 'the hold reason names the layer')
    src = open(S / 'kpc_fers.py', encoding='utf-8').read()
    check("_sm = [saved_missing_why(r) for r in ub if r in MISSING_SAVED]" in src, 'pass 2-3 rows say saved copy missing (not "could not be read")')
    check("if ref in got and ref not in SAVED_USE: LIVE[ref]" in src, "a saved copy is never re-saved as a live read")
    check("len(bad - _held) > 20" in src, 'held parks do not stop pass 1 as an agency outage')

    # W&S corridors from the saved copy
    PIN = {'US-9001': ('Obed Wild and Scenic River', 35.005, -79.995, '', 'National Wild and Scenic River', 'NC')}
    LN = {'US-9001': {'lines': [[[-80.0, 35.0], [-79.99, 35.01]]], 'kind': 'river'}}
    pk = {}; CALLS.clear()
    n = K.wsr_corridors(pk, PIN, LN)
    check(n == 1 and pk.get('US-9001', {}).get('ids') == ['wsrc7'] and 'US-9001' not in LN and not CALLS, 'a W&S river is joined to its saved corridor (no live read)')
    K.SAVED_STR.pop('wsrc7'); LN = {'US-9001': {'lines': [[[-80.0, 35.0], [-79.99, 35.01]]], 'kind': 'river'}}; pk = {}
    K.wsr_corridors(pk, PIN, LN)
    check('US-9001' in K.WSR_HELD and 'US-9001' in LN, 'no saved corridor copy: the river is held (kept as a line row, never counted)')

    # decide() holds
    K.PINS.update(PIN); K.PINS['US-9002'] = ('Other Park', 35.0, -80.0, '', 'State Park', 'NC')
    st_of = lambda r: 'US-NC'
    def run(spot, parks_):
        s = dict(spot); K.decide(s, parks_, {}, {}, K.PINS, '2026-11-10', set(), st_of); return s
    s = run({'refs': ['US-9001', 'US-9002'], 'kind': 'river', 'id': 'x'}, {})
    check(s['status'].startswith('not sure: saved copy missing for wsrc'), f"decide holds a river with no saved corridor ({s['status'][:70]})")
    K.WSR_HELD.clear()
    K.PINS['US-T2'] = ('Not Saved', 35.0, -80.0, '', 'State Park', 'NC')
    s = run({'refs': ['US-T2', 'US-9002'], 'kind': 'area', 'id': 'y'}, parks)
    check(s['status'] == f'not sure: saved copy missing for {REF_PRE}: needs download', f"decide holds a pair whose saved copy is missing ({s['status'][:70]})")
    K.MISSING_SAVED.clear()
    K.APX_PARKS.add('US-9002')
    s = {'refs': ['US-9001', 'US-9002'], 'kind': 'trail', 'id': 'z'}
    try: K.decide(s, {}, {}, {}, K.PINS, '2026-11-10', set(), st_of)
    except KeyError: pass   # goes on to the geometry test (this spot has no centre): the tag is already set
    check(s.get('approx') and 'US-9002' in (s.get('approx_refs') or []) and not str(s.get('status') or '').startswith('not sure: approximate'),
          f"a trail half beside an approximate outline is tagged approximate, not held ({str(s.get('status'))[:70]})")
    K.APX_PARKS.discard('US-9002')

    # same records: area-aware ids
    same = {'US-A': {'st': 'US-PA', 'ids': [3425]}, 'US-B': {'st': 'US-PA', 'ids': [3425]}, 'CA-C': {'st': 'CA-NB', 'ids': [3425]},
            'W-1': {'st': 'W-AU', 'ids': [7], 'm': [[7, 'x', 'CAPAD']]}, 'W-2': {'st': 'W-AU', 'ids': [7], 'm': [[7, 'x', 'Other layer']]}}
    check(K.identical_records_hold(same, ['US-A', 'US-B']) == K.SAME_RECORDS_HOLD, 'two US parks on the same PAD-US record are held')
    check(K.identical_records_hold(same, ['US-A', 'CA-C']) == '', 'PAD-US 3425 and a Canadian record 3425 are different records')
    check(K.identical_records_hold(same, ['W-1', 'W-2']) == '', 'two world layers with the same number are different records')
    s = run({'refs': ['US-A', 'US-B'], 'kind': 'area', 'id': 'w'}, same)
    check(s['status'] == K.SAME_RECORDS_JOIN_HOLD and s.get('person_review') and s.get('pin_outside') == ['US-A', 'US-B'] and s.get('shared_records') == ['3425'],
          'decide: same records and the pins cannot be shown inside the outline = held as a likely join to fix, pins and records listed')
    check(src.count('same_records_verdict(parks, (a, b), PIN, G)') == 2, 'same-land rows (pass 1 and pass 5) use the same test')
    _real = K.pin_in_outline
    try:
        K.pin_in_outline = lambda r, PIN, G: True
        _near = {'US-A': ['A Park', 38.0, -86.0], 'US-B': ['B Park', 38.0004, -86.0]}   # 0.04 km apart: the same spot (owner rule, 2026-11-10: pins close)
        check(K.same_records_verdict(same, ['US-A', 'US-B'], _near, {}) == ('approx', []), 'both pins inside the shared outline and close = approximate 2-fer')
        row = {'refs': ['US-A', 'US-B'], 'status': 'candidate', 'person_review': True}
        check(K.same_records_mark(row, ('approx', []), same, {}) is False and row.get('approx') and row.get('same_records') and row['status'] == 'candidate'
              and 'person_review' not in row and 'not confirmed' in row['approx_note'], 'the approximate row keeps its status, gets the approximate note, no person review')
        check(K.pc_tag({'spots': [row]})['spots'][0].get('tier') == 'approximate', 'the map tier for that row is approximate')
        K.pin_in_outline = lambda r, PIN, G: r != 'US-B'
        check(K.same_records_verdict(same, ['US-A', 'US-B'], {}, {}) == ('held', ['US-B']), 'one pin outside = held, that park named')
        check(K.same_records_verdict(same, ['US-A', 'CA-C'], {}, {}) == (), 'different records = no same-record rule at all')
    finally: K.pin_in_outline = _real
    check(K.pin_in_outline('US-A', {'US-A': ['n', None, None]}, {}) is None and K.pin_in_outline('US-A', {'US-A': ['n', 1.0, 2.0]}, {}) is None,
          'a bad pin or a park with no outline cannot be tested (never counted as inside)')

    # paging: never a partial answer
    pages = [{'features': [{'attributes': {'OBJECTID': 1}}], 'exceededTransferLimit': True}]
    try: K.read_pages(lambda off: pages[0]); stalled = False
    except RuntimeError: stalled = True
    check(stalled, 'a map that ignores resultOffset (same first record twice) is an error, not an endless loop')
    seq = iter([{'features': [{'attributes': {'OBJECTID': 1}}], 'exceededTransferLimit': True}, {'features': [{'attributes': {'OBJECTID': 2}}]}])
    check(len(K.read_pages(lambda off: next(seq))) == 2, 'pages are read to the last one')
    check("polys = []; LOG.append(f'PAD-US {nm}" in src, 'a failed Kentucky PAD-US read keeps nothing (no partial park)')
    CALLS.clear(); LN2 = {}
    K.live_lines(LN2)
    check(any('apps.fs.usda.gov' in c for c in CALLS), 'the Forest Service live line is asked (stub; KPC owner, 2026-11-13: apps.fs.usda.gov is no longer saved-copy only)')

    # 'none' is no blanket hold; unlabelled outlines are not official
    root = td / 'tree'; (root / 'data/us-key').mkdir(parents=True); (root / 'data/ca-key').mkdir(parents=True); (root / 'data/world-key').mkdir(parents=True)
    json.dump({'parks': {'US-N1': {'none': True}, 'US-N2': {'none': True}, 'US-N3': {'none': True}}}, open(root / 'data/us-key/overrides.json', 'w'))
    json.dump({'parks': {}}, open(root / 'data/ca-key/overrides.json', 'w')); json.dump({'parks': {}}, open(root / 'data/world-key/overrides.json', 'w'))
    json.dump({'parks': {'US-N1': {'g': 'pin', 'm': []}, 'US-N2': {'g': 'official', 'm': [[11, 'Joined', 1, 'name']]},
                         'US-P1': {'g': 'pin', 'm': []}, 'US-U1': {'g': 'official', 'm': [['zzz9', 'No label', 1, 'name']]},
                         'US-OK': {'g': 'official', 'm': [[12, 'Labelled', 1, 'name']]}}}, open(root / 'data/us-key/US-NC.json', 'w'))
    json.dump({'parks': {'US-N3': {'name': 'Trace', 'src': 'picture trace of an official map', 'rings': [RING]},
                         'US-T9': {'name': 'No src', 'rings': [RING]}}}, open(root / 'data/fers-approx-outlines.json', 'w'))
    cwd = os.getcwd(); os.chdir(root)
    try:
        K.PC.clear(); K.PC.update({r: {'kind': K.PC_KIND, 'pt': [-80.0, 35.0]} for r in ('US-N1', 'US-N2', 'US-P1')})
        K.APX_OUT.clear(); K.SKIPWHY.clear()
        P = {r: (r, 35.0, -80.0, '', 'State Park', 'NC') for r in ('US-N1', 'US-N2', 'US-N3', 'US-P1', 'US-U1', 'US-OK', 'US-T9')}
        _hs = K.has_official_outline; K.has_official_outline = lambda ref, parks=None, root=None: bool(((parks or {}).get(ref) or {}).get('ids')) and not ((parks or {}).get(ref) or {}).get('pc')
        try: pk, skip = K.official_parks(P)
        finally: K.has_official_outline = _hs
    finally: os.chdir(cwd)
    check('US-P1' in pk and pk['US-P1'].get('pc'), 'a park with no boundary and no hold still gets its point circle')
    check('US-N1' in pk and pk['US-N1'].get('pc'), "a 'none' park keeps its official-point circle (approximate tier)")
    check('US-N2' in pk and not pk['US-N2'].get('pc') and pk['US-N2']['ids'] == [11],
          "a 'none' park the key joined to an official record keeps that join (no blanket 'none' hold)")
    check('US-N3' in pk and pk['US-N3'].get('approx'), "a 'none' park keeps its person-made picture trace (approximate)")
    check('US-T9' not in pk, 'an approximate trace with no source label is not used')
    check('US-U1' not in pk and 'US-OK' in pk, 'an outline whose record source cannot be named is not official (fail closed)')

print('ALL_OK' if ok else 'FAILED')
sys.exit(0 if ok else 1)
