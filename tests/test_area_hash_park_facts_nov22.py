#!/usr/bin/env python3
"""Review M3 (KPC owner, 22 Nov 2026): the park facts the US key reads (KPC-Data data/park-facts.json.gz; the agency crosswalk
reaches the key inside it as link.map_tie) and the official sizes (data/acres.json) are in the per-state rebuild fingerprint.
A facts change for one state moves only that state. A Canadian row moves no US state. A missing or unreadable facts file (with
--data given) is a shared part: every US state moves (fail closed). The US composition is ah4, and the first appearance of the
new slices is a declared one-time migration (no rebuild of its own). Invented parks only; offline; no network.

  python3 tests/test_area_hash_park_facts_nov22.py
"""
import gzip, json, pathlib, shutil, socket, sys, tempfile

def _no_net(*a, **k): raise RuntimeError('network refused in this test')
socket.socket.connect = _no_net; socket.create_connection = _no_net

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_area_hash as A  # noqa: E402

bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg, flush=True)

def facts(rows):
    return {'made': '2026-11-22', 'parks': rows}

ROWS = {'US-99901': {'area': 'US-TN', 'name': 'Invented Hollow State Park', 'size': {'acres': 1200}},
        'US-99902': {'area': 'US-OH', 'name': 'Invented Ridge State Forest', 'link': {'map_tie': {'map_layer': 'x', 'map_field': 'y', 'map_id': '1'}}},
        'CA-99903': {'area': 'CA-ON', 'name': 'Invented Lake Provincial Park'}}

tmp = pathlib.Path(tempfile.mkdtemp())
def table(rows, raw=None, acres=None):
    d = tmp / 'data-dir'; shutil.rmtree(d, ignore_errors=True); (d / 'data').mkdir(parents=True)
    if acres is not None: (d / 'data/acres.json').write_text(json.dumps(acres), encoding='utf-8')
    f = d / 'data/park-facts.json.gz'
    if raw is not None: f.write_bytes(raw)
    elif rows is not None:
        with gzip.open(f, 'wt', encoding='utf-8') as g: json.dump(facts(rows), g)
    p = A.Kind(A.Tree(ROOT), 'us', data=str(d)).parts()
    return p, A.area_hashes(p)

try:
    check(A.composition('us') == 'ah4', f"the US composition is ah4 (park facts + acres slices), not {A.composition('us')}")
    p0, h0 = table(ROWS)
    check('data:data/park-facts.json.gz' in p0['TN'] and 'data:data/park-facts.json.gz' in p0['OH'],
          'TN and OH each carry their own park-facts part')
    r1 = json.loads(json.dumps(ROWS)); r1['US-99901']['size']['acres'] = 1500
    p1, h1 = table(r1)
    moved = sorted(a for a in h0 if h0[a] != h1[a])
    check(moved == ['TN'], f'a new size for one TN park moves only TN (moved: {moved[:8]})')
    r2 = json.loads(json.dumps(ROWS)); r2['US-99902']['link']['map_tie']['map_id'] = '2'
    _, h2 = table(r2)
    moved = sorted(a for a in h0 if h0[a] != h2[a])
    check(moved == ['OH'], f'a changed agency-crosswalk tie in the facts moves only OH (moved: {moved[:8]})')
    r3 = json.loads(json.dumps(ROWS)); r3['CA-99903']['name'] = 'Invented Bay Provincial Park'
    _, h3 = table(r3)
    check(h3 == h0, 'a Canadian row moves no US state')
    pm, hm = table(None)
    check(all('shared:data/park-facts.json.gz' in pm[a] for a in pm) and all(hm[a] != h0[a] for a in h0),
          'facts file missing (--data given): a shared part, every US state moves (fail closed)')
    pu, hu = table(None, raw=b'not gzip')
    check(all('shared:data/park-facts.json.gz!unreadable' in pu[a] for a in pu) and all(hu[a] != hm[a] for a in hm),
          'facts file unreadable: a shared !unreadable part, every US state moves (fail closed)')
    old = {k: v for k, v in p0['TN'].items() if not k.startswith(('data:data/park-facts', 'data:data/acres'))}
    check(not A.real_inputs_moved(old, p0['TN'], 'ah4') and A.real_inputs_moved(p0['TN'], p1['TN'], 'ah4'),
          'the first appearance of the facts slice is a one-time migration; after that a facts change is a real move')
    tn_ref = next(r for r, a in A.Kind(A.Tree(ROOT), 'us').ref_map().items() if a == {'TN'})
    _, ha = table(ROWS, acres={'parks': {tn_ref: {'acres': 10}}})
    _, hb = table(ROWS, acres={'parks': {tn_ref: {'acres': 20}}})
    moved = sorted(a for a in ha if ha[a] != hb[a])
    check(moved == ['TN'], f'a changed official size in data/acres.json moves only that park\'s state (moved: {moved[:8]})')
    pn = A.Kind(A.Tree(ROOT), 'us').parts()
    check(not any(k.startswith(('data:data/park-facts', 'shared:data/park-facts')) for a in pn for k in pn[a]),
          'no --data: the facts are not counted (like the pins part)')
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('ALL PASS' if not bad else f'{bad} FAILED - SOME FAILED')
sys.exit(1 if bad else 0)
