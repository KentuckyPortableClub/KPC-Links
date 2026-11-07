#!/usr/bin/env python3
"""WORLD TRACT SIDE FILES, BY HAND (Nov 7 2026, KEY / 2-FER / WORLD handoff, Part 1 item 2). Writes data/world-key/tracts/<CC>.json for
GB, IE, AU, NZ (or the countries named) through kpc_tracts.py, the same calls the US / Canada writers and the world key's own
_world_tracts() make, WITHOUT running the world key and WITHOUT touching kpc_world_key.py (a rules file: its hash must not move).
No network. Not wired into any workflow, no cron: run it by hand from a KPC-Data checkout (scripts from KPC-Links):

  python3 .github/scripts/kpc_world_tracts.py [GB IE AU NZ] [--cache cache/world] [--check] [--labels-only] [--out data/world-key]

Inputs (all local):
  data/world-key/<CC>.json            the published world key: per park 'm' rows [record id, name, source label, how]
  cache/world/W-<CC>.json.gz          the world key's record cache (wsave(): every official record with its attributes '_a' and its
                                      rings '_r'), restored by the world workflow's cache step (Links #54). GEO_CACHE overrides it.
  data/world-key/layers.json          source label -> layer address (picks the kpc_source_fields table row: ids, acres, owner)
  data/world-bounds/<CC>/<n>.json     outlines the world key saved for maps a page cannot ask by id ({ref: {n, s, r}})
What it writes, per country, in this order of preference:
  'record cache'    one tract per joined record with its own rings (measured acres, pieces, box) = what _world_tracts writes
  'saved outlines'  no record cache: a park with ONE joined record gets the saved outline's rings; nested parks come from the saved
                    outlines (GUESS: a saved outline merges every record of the park, so a park with several records keeps labels only)
  'key rows only'   neither: labels only (no box, no pieces, no nested). Held (nothing written) unless --labels-only.
--check writes nothing and says whether the file would change. KPC_TRACT_STORE=0 = nothing written (same switch as the writers).
A file built from a better source is never replaced by a poorer one (a world key run's own file = 'record cache'): that country is
held ('held: existing file is better') unless --force.
"""
import argparse, gzip, json, os, pathlib, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_tracts as TR  # noqa: E402
import kpc_source_fields as SF  # noqa: E402

SCOPE = ('GB', 'IE', 'AU', 'NZ')
NOTE = '{cc}: the official layers the world key reads.'   # the same note _world_tracts writes


def _load(p):
    p = pathlib.Path(p)
    for q in (p, pathlib.Path(str(p) + '.gz')) if not str(p).endswith('.gz') else (p,):
        if q.exists():
            op = gzip.open if str(q).endswith('.gz') else open
            with op(q, 'rt', encoding='utf-8') as h: return json.load(h)
    return None


def records(cc, cache):
    j = _load(pathlib.Path(cache) / f'W-{cc}.json.gz')
    return (j or {}).get('recs') or []


def saved_outlines(cc, root='data/world-bounds'):
    out = {}
    d = pathlib.Path(root) / cc
    for f in sorted(d.glob('*.json')) if d.exists() else []:
        for ref, b in (_load(f) or {}).items():
            if isinstance(b, dict) and b.get('r'): out[ref] = [r for r in b['r'] if r and len(r) >= 3]
    return out


def build(cc, parks, recs, urls, saved=None):
    """(PT, SH, add, how): tract records per park, shapes per park (for nested), parks whose every record has official acres."""
    rid = {(r.get('src'), r.get('id')): r for r in recs if r.get('id') is not None}
    maps, PT, SH, add = {}, {}, {}, 0
    for ref, p in parks.items():
        ts, rg = [], []
        m = p.get('m') or []
        for q in m:
            r = rid.get((q[2], q[0])) if len(q) > 2 else None
            if r is None:
                ring = (saved or {}).get(ref) if len(m) == 1 else None
                if ring:
                    t = TR.tract(q[0], q[1], q[3] if len(q) > 3 else '', src_key='other', rings=ring)
                    ts.append(t); rg += ring
                else: ts.append(TR.tract(q[0], q[1], q[3] if len(q) > 3 else '', src_key='other'))
                continue
            a = r.get('_a') if isinstance(r.get('_a'), dict) else {}
            k = r.get('src') or ''
            if k not in maps:
                mp = SF.mapping(str(urls.get(k) or ''), k, list(a.keys()))
                if not mp.get('key') or mp.get('key') == 'auto': mp = dict(mp, key=re.sub(r'[^a-z0-9]+', '_', k.lower()).strip('_')[:40] or 'unknown')
                maps[k] = mp
            t = TR.tract(q[0], q[1], q[3] if len(q) > 3 else '', a, maps[k], r.get('_r'), k)
            ts.append(t); rg += r.get('_r') or []
        if ts: PT[ref] = ts
        if rg: SH[ref] = rg
        elif saved and saved.get(ref): SH[ref] = saved[ref]
        if ts and all(t.get('ac') is not None for t in ts): add += 1
    return PT, SH, add


RANK = {'record cache': 3, 'saved outlines': 2, 'key rows only': 1}


def rank_of(doc):
    """How good an existing side file is: the world key's own file (no 'from') was built from its records."""
    if not isinstance(doc, dict): return 0
    f = str(doc.get('from') or 'record cache')
    return next((v for k, v in RANK.items() if f.startswith(k)), 0)


def run(cc, out='data/world-key', cache=None, check=False, labels_only=False, wb='data/world-bounds', force=False):
    """-> (status, path, how). status: 'written' | 'same' | 'would change' | 'held' | 'no key' | 'off'."""
    if not TR.on(): return 'off', None, ''
    key = _load(pathlib.Path(out) / f'{cc}.json')
    if not key or not isinstance(key.get('parks'), dict): return 'no key', None, ''
    cache = cache or os.environ.get('GEO_CACHE') or 'cache/world'
    recs = records(cc, cache)
    saved = {} if recs else saved_outlines(cc, wb)
    how = 'record cache' if recs else 'saved outlines' if saved else 'key rows only'
    if how == 'key rows only' and not labels_only: return 'held', None, how
    path = pathlib.Path(out) / 'tracts' / f'{cc}.json'
    if not force and rank_of(_load(path)) > RANK[how]: return 'held: existing file is better', path, how
    urls = _load(pathlib.Path(out) / 'layers.json') or {}
    PT, SH, add = build(cc, key['parks'], recs, urls, saved)
    d = TR.doc(cc, PT, TR.nested_geometry(SH), NOTE.format(cc=cc))
    d['acres_would_add'] = {'parks': add, 'mode': 'off (KPC_WORLD_ACRES=1 writes them as ac in the key)'}
    d['ac_measured_detail'] = 'outline as the world key keeps it (thinned)' if how == 'record cache' else \
        'outline the world key saved for the website (data/world-bounds)' if how == 'saved outlines' else 'none (key rows only)'
    d['from'] = how + ' (kpc_world_tracts.py)'
    if check:
        old = _load(path)
        strip = lambda x: {k: v for k, v in (x or {}).items() if k != 'built'}  # noqa: E731
        return ('same' if strip(old) == strip(json.loads(json.dumps(d))) else 'would change'), path, how
    TR.save(path, d)
    return 'written', path, how


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cc', nargs='*', default=list(SCOPE))
    ap.add_argument('--out', default='data/world-key')
    ap.add_argument('--cache', default=None)
    ap.add_argument('--world-bounds', default='data/world-bounds')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--labels-only', action='store_true')
    ap.add_argument('--force', action='store_true', help='replace a file built from a better source')
    a = ap.parse_args(argv)
    bad = 0
    for cc in [c.upper() for c in a.cc]:
        st, path, how = run(cc, a.out, a.cache, a.check, a.labels_only, a.world_bounds, a.force)
        print(f'::notice title=World tracts {cc}::{st}' + (f' ({how})' if how else '') + (f' {path}' if path else ''), flush=True)
        bad += st in ('no key',)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
