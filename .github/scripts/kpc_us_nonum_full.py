#!/usr/bin/env python3
"""Full 'no POTA park joined' list per US state, without the key builder's 300-row cap (Nov 7 prep, Task D).

The US key builder (kpc_us_key.py) keeps only the biggest 300 federal/state places with no POTA park joined
('nonum', cut at the line that writes the key file). Alabama has 309. This script writes the whole list to a side
file, data/us-key/new/US-<ST>-nonum.json, and never touches the key file. It is not a rule file and never decides a
join, so the US rules hash stays put (listed in kpc_key_freeze.NOT_RULES).

Where the rows come from:
  - records: the saved outlines the builder itself reads with GEO_CACHE_MODE=use (cache/us/US-<ST>.json.gz, the
    'boundary-cache' release; download it the same way kpc-boundary-check.yml does). Same fields, same acres check.
  - joined ids: the published key file (data/us-key/US-<ST>.json): every record id in a park's 'm' list, plus the
    ids the one-record-two-parks pass moved to 'c' (note starts 'record also joined to'), which the builder also
    counted as used.

Records a later pass joined after the builder's cut (seen on real keys: reviewed FWS district tracts, e.g. Iowa WPAs
joined to US-0270) are in a park's 'm' but still in the key's nonum. They are left out here (not 'possible new parks')
and listed in 'joined_since_cut'.

Self-check, per state: every key nonum row not joined since must be rebuilt with the same acres; no rebuilt row bigger
than the key's cut may be missing from the key; row count between those and counts.nonum. If not (saved copy older or
newer than the key), nothing is written for that state and it is listed as STALE. Exit 1 when any state is STALE.

  python3 .github/scripts/kpc_us_nonum_full.py [--states AL,AK] [--cache cache/us] [--out data/us-key/new] [--dry-run]
  python3 .github/scripts/kpc_us_nonum_full.py --selftest
"""
import argparse, gzip, json, math, pathlib, sys, tempfile

MOVED = 'record also joined to'


def sane_ac(ac, bb):
    """Same check as kpc_us_key._sane_ac (square feet / square metres turned into acres when the box can't hold it)."""
    if not ac or not bb: return ac or 0
    k = math.cos(math.radians((bb[1] + bb[3]) / 2))
    box = max((bb[2] - bb[0]) * 111.32 * k, .01) * max((bb[3] - bb[1]) * 110.57, .01) * 247.105 * 1.6
    if ac <= box: return ac
    for div in (43560.0, 4046.86):
        if ac / div <= box: return round(ac / div, 1)
    return 0


def bbox(rings):
    xs = [p[0] for r in rings or [] for p in r]; ys = [p[1] for r in rings or [] for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def load_recs(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f: blob = json.load(f)
    out = []
    for r in blob.get('recs') or []:
        a = {k: v for k, v in r.items() if k not in ('_r', '_k')}
        if str(a.get('OBJECTID', '')).startswith('sg') and a.get('GIS_Acres'): a['GIS_Acres'] = sane_ac(a['GIS_Acres'], bbox(r.get('_r')))
        out.append(a)
    return out


def used_ids(key):
    used = set()
    for p in (key.get('parks') or {}).values():
        for q in p.get('m') or []: used.add(str(q[0]))
        for q in p.get('c') or []:
            if len(q) > 3 and str(q[3]).startswith(MOVED): used.add(str(q[0]))
    return used


def nonum_rows(recs, used):
    return sorted(([a['OBJECTID'], a.get('Unit_Nm') or a.get('Loc_Nm') or '', a.get('d_Des_Tp') or a.get('Des_Tp') or '',
                    a.get('Loc_Mang') or a.get('Mang_Name') or '', round(a.get('GIS_Acres') or 0)]
                   for a in recs if str(a['OBJECTID']) not in used), key=lambda x: -x[4])


def check(rows, key, used):
    """'' when the rows agree with the key file, else the reason.
    The key's list was cut before later passes (e.g. a reviewed FWS district join) joined some of its records to a park;
    those are left out here on purpose (they are not 'possible new parks') and are not a disagreement."""
    want = (key.get('counts') or {}).get('nonum')
    top = key.get('nonum') or []
    keep = [x for x in top if str(x[0]) not in used]
    if want is not None and not (len(keep) <= len(rows) <= want): return f'{len(rows)} rows, key says {want} ({len(keep)} of its top rows still unjoined)'
    have = {(str(r[0]), r[4]) for r in rows}
    miss = [x[0] for x in keep if (str(x[0]), x[4]) not in have]
    if miss: return f'{len(miss)} key rows not rebuilt (e.g. {miss[0]})'
    if top and want is not None and want > len(top):
        floor = min(x[4] for x in top); ids = {str(x[0]) for x in top}
        extra = [r[0] for r in rows if r[4] > floor and str(r[0]) not in ids]
        if extra: return f'{len(extra)} rebuilt rows bigger than the key cut but not in the key (e.g. {extra[0]})'
    return ''


def joined_since(key, used):
    return [x[0] for x in key.get('nonum') or [] if str(x[0]) in used]


def run(root, cache, out, states, dry):
    root = pathlib.Path(root); stale, done = [], []
    keys = sorted((root / 'data/us-key').glob('US-??.json'))
    for kf in keys:
        st = kf.stem[3:]
        if states and st not in states: continue
        cf = pathlib.Path(cache) / f'US-{st}.json.gz'
        if not cf.is_file(): print(f'{st}: no saved copy at {cf}; skipped'); continue
        key = json.load(open(kf, encoding='utf-8'))
        rows = nonum_rows(load_recs(cf), used_ids(key))
        u = used_ids(key); why = check(rows, key, u)
        if why: print(f'{st}: STALE ({why}); nothing written'); stale.append(st); continue
        js = joined_since(key, u)
        done.append(st); print(f'{st}: {len(rows)} places with no POTA park joined (key file keeps {len(key.get("nonum") or [])}; {len(js)} of those now joined)')
        if dry: continue
        o = pathlib.Path(out); o.mkdir(parents=True, exist_ok=True)
        json.dump({'state': st, 'key_built': key.get('updated') or key.get('built') or '', 'rows': len(rows),
                   'cols': ['objectid', 'name', 'designation', 'manager', 'acres'], 'nonum': rows,
                   'joined_since_cut': js},
                  open(o / f'US-{st}-nonum.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'done {len(done)}, stale {len(stale)}' + (f": {' '.join(stale)}" if stale else ''))
    return 1 if stale else 0


def selftest():
    ok = 0
    def t(c, m):
        nonlocal ok
        if not c: print('FAIL', m); sys.exit(1)
        ok += 1
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d); (d / 'data/us-key').mkdir(parents=True); (d / 'cache').mkdir()
        recs = [{'OBJECTID': i, 'Unit_Nm': f'P{i}', 'Des_Tp': 'SP', 'Mang_Name': 'SDNR', 'GIS_Acres': 1000 - i, '_r': [[[0, 0], [1, 0], [1, 1], [0, 0]]]} for i in range(1, 8)]
        recs.append({'OBJECTID': 'sg9', 'Loc_Nm': 'Feet', 'GIS_Acres': 4356000.0, '_r': [[[0, 0], [.01, 0], [.01, .01], [0, 0]]]})  # sq ft -> 100 ac
        with gzip.open(d / 'cache/US-ZZ.json.gz', 'wt', encoding='utf-8') as f: json.dump({'recs': recs}, f)
        parks = {'US-1': {'m': [[1, 'x', 'y']], 'c': []}, 'US-2': {'m': [], 'c': [[2, 'x', 'y', 'record also joined to US-1 whose kind it names']]},
                 'US-3': {'m': [], 'c': [[3, 'x', 'y', 'far place']]}}
        full = nonum_rows(load_recs(d / 'cache/US-ZZ.json.gz'), used_ids({'parks': parks}))
        t([r[0] for r in full] == [3, 4, 5, 6, 7, 'sg9'], f'joined (m) and moved (c) ids left out, far place kept, sorted by acres: {[r[0] for r in full]}')
        t(full[-1][4] == 100, 'square-feet acres converted like the builder')
        key = {'parks': parks, 'counts': {'nonum': 6}, 'nonum': [list(r) for r in full[:3]]}
        json.dump(key, open(d / 'data/us-key/US-ZZ.json', 'w'))
        t(check(full, key, used_ids(key)) == '', 'agrees with a key cut at 3 rows')
        t(run(d, d / 'cache', d / 'out', {'ZZ'}, False) == 0, 'run exits 0 when the saved copy agrees')
        j = json.load(open(d / 'out/US-ZZ-nonum.json')); t(j['rows'] == 6 and len(j['nonum']) == 6, 'side file has every row, not the cut')
        t(json.load(open(d / 'data/us-key/US-ZZ.json')) == key, 'key file not changed')
        key['counts']['nonum'] = 5; json.dump(key, open(d / 'data/us-key/US-ZZ.json', 'w')); (d / 'out/US-ZZ-nonum.json').unlink()
        t(run(d, d / 'cache', d / 'out', {'ZZ'}, False) == 1 and not (d / 'out/US-ZZ-nonum.json').exists(), 'stale saved copy: exit 1, nothing written')
        key['counts']['nonum'] = 6; key['nonum'][0][4] = 1; t(check(full, key, used_ids(key)) != '', 'acres disagreement is caught')
        key['nonum'][0][4] = full[0][4]; key['nonum'].insert(0, [1, 'P1', 'SP', 'SDNR', 999]); key['counts']['nonum'] = 7
        t(check(full, key, used_ids(key)) == '' and joined_since(key, used_ids(key)) == [1], 'a key row joined after the cut is left out and reported, not an error')
    print(f'selftest OK ({ok} checks)')


if __name__ == '__main__':
    if '--selftest' in sys.argv: selftest(); sys.exit(0)
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.'); ap.add_argument('--cache', default='cache/us'); ap.add_argument('--out', default='data/us-key/new')
    ap.add_argument('--states', default=''); ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    sys.exit(run(a.root, a.cache, a.out, {s.strip().upper() for s in a.states.split(',') if s.strip()}, a.dry_run))
