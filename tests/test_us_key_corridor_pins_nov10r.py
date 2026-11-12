#!/usr/bin/env python3
"""kpc_us_key.py, owner rule 2026-11-10:
1. the five Wild and Scenic corridor parks kept as pins (US-8015, US-10709, US-12234, US-12792, US-12798) are pins by DATA:
   their overrides.json rows carry a 'no' on the corridor record(s); the builder's own code path joins nothing for them;
2. a 'none' row only clears the to-check list: a park with an official same-name join KEEPS it (no blanket 'none' hold).
The whole builder runs on a temp folder with a tiny saved copy (GEO_CACHE_MODE=only); sockets are disabled in the child."""
import gzip, json, os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = ROOT / '.github/scripts/kpc_us_key.py'
sys.path.insert(0, str(ROOT / '.github/scripts')); import kpc_overrides as _KOVR
OVR = _KOVR.load(ROOT / 'data/us-key/overrides.json')['parks']
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


FIVE = {'US-8015': ('NH', 'Wildcat National Wild and Scenic River', 'National Wild and Scenic River', 44.1952, -71.1931),   # POTA name, type, pin
        'US-10709': ('WA', 'Klickitat National Wild and Scenic River', 'National Wild & Scenic River', 45.7159, -121.26),
        'US-12234': ('PA', 'Allegheny National Wild and Scenic River', 'National Wild & Scenic River', 41.6815, -79.4108),
        'US-12792': ('MI', 'Manistee National Wild and Scenic River', 'National Wild and Scenic River', 44.2672, -86.0154),
        'US-12798': ('MI', 'Sturgeon (Hiawatha) National Wild and Scenic River', 'National Wild and Scenic River', 45.9351, -86.707)}
for ref in FIVE:
    o = OVR.get(ref) or {}
    check(f"{ref}: overrides row keeps 'none', has a 'no' on fwsr record(s), decided_by the owner ({o.get('no')})",
          o.get('none') is True and o.get('no') and all(str(x).startswith('fwsr') for x in o['no']) and o.get('decided_by') == 'KPC owner, Nov 9 2026'
          and set(o.get('nofp') or {}) == {str(x) for x in o['no']})
for ref in ('US-12799', 'US-12343', 'US-12795'):
    check(f"{ref} (another approximate W&S river) has no 'no' added", not (OVR.get(ref) or {}).get('no'))

CHILD = r'''
import runpy, socket, sys
def _off(*a, **k): raise OSError('network disabled in this test')
socket.socket.connect = _off; socket.create_connection = _off; socket.getaddrinfo = _off
key = sys.argv[1]; sys.argv = [key]
runpy.run_path(key, run_name='__main__')
'''


def sq(la, lo, d): return [[[lo - d, la - d], [lo + d, la - d], [lo + d, la + d], [lo - d, la + d], [lo - d, la - d]]]


def rec(oid, name, ac, la, lo, d, own, label, k):
    return {'OBJECTID': oid, 'Unit_Nm': name, 'Loc_Nm': '', 'Own_Type': own, 'Mang_Type': own, 'Mang_Name': oid[:4].upper(), 'Loc_Mang': label,
            'Des_Tp': '', 'GIS_Acres': ac, 'Category': 'Fee', '_r': sq(la, lo, d), '_k': k}


def build(states, P, rows, recs):
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        for d in ('data/parkinfo', 'data/us-key', 'cache/us'): (t / d).mkdir(parents=True)
        (t / 'data/us-key/overrides.json').write_text(json.dumps({'parks': rows}))
        for st in states:
            (t / f'data/parkinfo/US-{st}.json').write_text(json.dumps({'parks': {r: v for r, (s, v) in P.items() if s == st}, 'state': st}))
            with gzip.open(t / f'cache/us/US-{st}.json.gz', 'wt', encoding='utf-8') as f:
                json.dump({'recs': recs.get(st, []), 'seen': len(recs.get(st, [])), 'detail': 0.01}, f)
        env = {k: v for k, v in os.environ.items() if not k.startswith(('KPC_', 'GEO_', 'STATES'))}
        r = subprocess.run([sys.executable, '-c', CHILD, str(KEY)], cwd=t, capture_output=True, text=True, timeout=600,
                           env=dict(env, STATES=' '.join(states), GEO_CACHE_MODE='only', no_proxy='*', HTTPS_PROXY='', HTTP_PROXY='', https_proxy='', http_proxy=''))
        out = {}
        for st in states:
            f = t / f'data/us-key/US-{st}.json'
            if f.exists(): out.update(json.loads(f.read_text())['parks'])
        return r, out


P, recs, rows = {}, {}, {}
for ref, (st, name, typ, la, lo) in FIVE.items():
    P[ref] = (st, [name, '', typ, '', '', la, lo, 0, 0, 0])
    rows[ref] = OVR[ref]
    for i, oid in enumerate(OVR[ref].get('no') or []):   # the corridor record(s) the published key joined (name + acres saved in 'nofp'), around the pin
        fn, fa = (OVR[ref].get('nofp') or {}).get(oid) or [name, 1000]
        recs.setdefault(st, []).append(rec(oid, fn, fa, la, lo, .03 + .01 * i, 'FED', 'Forest Service Wild and Scenic River corridor (official boundary)', ['wsr']))
# a synthetic 'none' park (the Oct 22 waiting-list style) that later got an official exact-name join from a state layer
P['US-99001'] = ('NH', ['Example Pond State Park', '', 'State Park', '', '', 43.5, -71.5, 0, 0, 0])
rows['US-99001'] = {'none': True, 'when': '2026-10-22', 'why': 'a different place, not this park; no outline of its own on file (hand review Oct 22 (waiting list))'}
recs['NH'].append(rec('sgnhx1', 'Example Pond State Park', 300, 43.5, -71.5, .01, 'STAT', 'Example state parks (state GIS table)', ['sp']))

r, parks = build(sorted({v[0] for v in P.values()}), P, rows, recs)
if not parks: print(r.stdout[-3000:], r.stderr[-3000:])
for ref in FIVE:
    p = parks.get(ref) or {}
    check(f"{ref}: built with no joined record and grade pin (m={p.get('m')}, g={p.get('g')})", ref in parks and not p.get('m') and p.get('g') == 'pin')
p = parks.get('US-99001') or {}
check(f"a 'none' park with an official exact-name join KEEPS it (m={p.get('m')}, g={p.get('g')})",
      [x[0] for x in p.get('m') or []] == ['sgnhx1'] and p.get('g') not in (None, 'pin') and 'held' not in p)

# the same build without the 'no' rows: the corridor records DO join (so the 'no' is what makes them pins)
r2, parks2 = build(sorted({v[0] for v in P.values()}), P, {k: {kk: vv for kk, vv in v.items() if kk != 'no'} for k, v in rows.items()}, recs)
check(f"control: without 'no' the corridor joins ({sum(1 for k in FIVE if (parks2.get(k) or {}).get('m'))} of 5 joined)",
      all((parks2.get(k) or {}).get('m') for k in FIVE))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
