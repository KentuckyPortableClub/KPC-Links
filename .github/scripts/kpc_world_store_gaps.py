#!/usr/bin/env python3
"""kpc_world_store_gaps.py: which world countries a store-mode key run cannot build (KPC owner, 2026-11-15; keys in store mode).

A store-mode world key run (repo variable KPC_KEY_SOURCE=store, GEO_CACHE_MODE=only) builds a country from its saved copy
W-<CC>.json.gz on the boundary-cache release ONLY, and uses that copy whole: a source of the country (its built-in layers in
data/world-key/area-tables.json, plus the approved layers of extra-layers.json and sheet-countries.json, exactly as the key reads
them) that has no record in the copy would silently lose every park joined through it. Such a country has a GAP and is not
built in store mode: it is left out with a plain line and its key is left as it is (never emptied). A country with no saved copy
at all is a gap too.

  plan     --assets FILE --gaps data/outlines/world-store-gaps.json COUNTRY...
           (the plan job) prints the countries to build, one line: those with a saved copy on the release (asset list FILE)
           and no gap in the gaps file; every other country gets one plain line on stderr.
  check    --cache cache/world --out FILE COUNTRY...
           (the build job, on the copies really downloaded) writes the countries with a gap to FILE, one per line, with a plain
           line each; exit 0 (the list decides).
  scan     --cache DIR [--out data/outlines/world-store-gaps.json] [COUNTRY...]
           (the keeper, by hand: download the W-*.json.gz copies into DIR first) writes the gaps file: per country, the copy's
           date and every source with no record in it (label, reader, address, layer), so the gaps can be filled later.
  --selftest

A source matches a saved record by its source id (kind, address, layer), or, for a copy saved before source ids, by its label
when that label is unique in the country: the same test the key uses when a live source fails (kpc_world_key.py).
Offline, read only (scan writes only --out). Not a rule file: it decides no join (kpc_key_freeze.NOT_RULES). Standard library only.
"""
import argparse, collections, contextlib, gzip, io, json, os, pathlib, sys, time

HERE = pathlib.Path(__file__).resolve().parent
KEY = HERE / 'kpc_world_key.py'
MARK = "COUNTRIES = (os.environ.get('COUNTRIES')"


def sources(root='.'):
    """{CC: [source tuple]} exactly as kpc_world_key.py builds SRC (its own code, run up to the country list; no network)."""
    src = KEY.read_text(encoding='utf-8')
    if MARK not in src: raise SystemExit(f'::error title=Store gaps::{KEY.name} changed (no country list line): cannot read its sources')
    ns = {'__file__': str(KEY), '__name__': 'kpc_world_key_sources'}
    cwd = os.getcwd()
    try:
        os.chdir(root)
        with contextlib.redirect_stdout(io.StringIO()): exec(compile(src[:src.index(MARK)], str(KEY), 'exec'), ns)   # noqa: S102
    finally: os.chdir(cwd)
    return ns['SRC']


def src_id(s):   # = kpc_world_key.src_id
    return repr((s[1], s[2], s[3] if len(s) > 3 else None))


def load_copy(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f: blob = json.load(f)
    return blob.get('saved'), blob.get('recs') or []


def missing(srcs, recs):
    """The sources with no record in the saved copy (same matching as the key's failed-source fallback)."""
    sids = collections.Counter(r.get('sid') for r in recs if 'sid' in r)
    old_labels = {r.get('src') for r in recs if 'sid' not in r}
    labels = collections.Counter(s[0] for s in srcs)
    # the key reads an 'arcgis_alt' source only when the same zones did not come from IGN (kpc_world_key.py: 'the same zones already
    # came from IGN'), so with IGN ZNIEFF records in the copy an alternate source with none is not missing
    ign = any(str(r.get('src', '')).startswith('IGN Géoplateforme ZNIEFF') for r in recs)
    return [s for s in srcs if not sids.get(src_id(s)) and not (labels[s[0]] == 1 and s[0] in old_labels) and not (s[1] == 'arcgis_alt' and ign)]


def row(s): return {'label': s[0], 'reader': s[1], 'address': s[2], 'layer': s[3] if len(s) > 3 else None}


def scan(cache, countries, srcs):
    out = {}
    for cc in countries:
        f = pathlib.Path(cache) / f'W-{cc}.json.gz'
        if not f.exists():
            out[cc] = {'copy': None, 'saved': None, 'records': 0, 'sources': len(srcs.get(cc, [])), 'missing': [row(s) for s in srcs.get(cc, [])],
                       'why': 'no saved copy W-%s.json.gz on the boundary-cache release' % cc}
            continue
        saved, recs = load_copy(f)
        miss = missing(srcs.get(cc, []), recs)
        out[cc] = {'copy': f.name, 'saved': saved, 'records': len(recs), 'sources': len(srcs.get(cc, [])), 'missing': [row(s) for s in miss]}
        if miss: out[cc]['why'] = f'{len(miss)} of {len(srcs.get(cc, []))} source(s) have no record in the saved copy'
        del recs
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('plan', 'check', 'scan'))
    ap.add_argument('--assets'); ap.add_argument('--gaps', default='data/outlines/world-store-gaps.json')
    ap.add_argument('--cache', default='cache/world'); ap.add_argument('--out'); ap.add_argument('--root', default='.')
    ap.add_argument('countries', nargs='*')
    a = ap.parse_args(argv)
    ccs = [c.upper() for c in dict.fromkeys(' '.join(a.countries).split())]
    if a.cmd == 'plan':
        have = set(open(a.assets, encoding='utf-8').read().split()) if a.assets else set()
        try: gaps = json.load(open(a.gaps, encoding='utf-8')).get('countries') or {}
        except FileNotFoundError: gaps = {}
        keep = []
        for cc in ccs:
            if f'W-{cc}.json.gz' not in have:
                print(f'World key {cc}: no saved copy on the boundary-cache release; left out of this store-mode run, its key is left as it is', file=sys.stderr)
            elif (gaps.get(cc) or {}).get('missing'):
                g = gaps[cc]['missing']
                print(f"World key {cc}: the saved copy has no record from {len(g)} source(s) ({'; '.join(x['label'] for x in g)[:300]}); "
                      f'left out of this store-mode run, its key is left as it is (data/outlines/world-store-gaps.json)', file=sys.stderr)
            else: keep.append(cc)
        print(' '.join(keep))
        return 0
    srcs = sources(a.root)
    if a.cmd == 'check':
        if not a.out: ap.error('check needs --out')
        bad = []
        for cc in ccs:
            f = pathlib.Path(a.cache) / f'W-{cc}.json.gz'
            if not f.exists():
                print(f'World key {cc}: no saved copy; not built in store mode, its key is left as it is'); bad.append(cc); continue
            miss = missing(srcs.get(cc, []), load_copy(f)[1])
            if miss:
                print(f"World key {cc}: the saved copy has no record from {len(miss)} source(s) ({'; '.join(s[0] for s in miss)[:300]}); "
                      f'not built in store mode, its key is left as it is')
                bad.append(cc)
            else: print(f'World key {cc}: the saved copy has records from all {len(srcs.get(cc, []))} source(s)')
        pathlib.Path(a.out).write_text(''.join(c + '\n' for c in bad))
        return 0
    ccs = ccs or sorted(srcs)
    rows = scan(a.cache, ccs, srcs)
    doc = {'about': 'World countries a store-mode key run (KPC_KEY_SOURCE=store) cannot build: no saved copy W-<CC>.json.gz on the '
                    'boundary-cache release, or sources with no record in it. Such a country is left out of a store-mode run and keeps '
                    'its key. To fill a gap: save a whole copy of the country that has every source, upload it, run '
                    '`python3 .github/scripts/kpc_world_store_gaps.py scan --cache <dir with the W-*.json.gz copies>` again. '
                    'Made by kpc_world_store_gaps.py (not a rule file).',
           'made': time.strftime('%Y-%m-%d'),
           'gaps': sorted(cc for cc, r in rows.items() if r['missing']),
           'countries': rows}
    text = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + '\n'
    if a.out: pathlib.Path(a.out).write_text(text, encoding='utf-8')
    else: sys.stdout.write(text)
    print(f"store gaps: {len(rows)} countries scanned, {len(doc['gaps'])} with a gap: {' '.join(doc['gaps'])}", file=sys.stderr)
    return 0


def selftest():
    import tempfile
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)
    A, B, C = ('Parks', 'arcgis', 'https://x/0'), ('Reserves', 'wfs', 'https://y/wfs', 'r:1'), ('Parks', 'arcgis', 'https://z/0')
    check('every source has a record = no gap', missing([A, B], [{'sid': src_id(A)}, {'sid': src_id(B)}]) == [])
    check('a source with no record = a gap', missing([A, B], [{'sid': src_id(A)}]) == [B])
    check('an old copy (no source ids) matches a unique label', missing([A, B], [{'src': 'Parks'}, {'src': 'Reserves'}]) == [])
    check('an old copy never matches a shared label (two "Parks" sources)', missing([A, B, C], [{'src': 'Parks'}, {'src': 'Reserves'}]) == [A, C])
    Z = ('ZNIEFF alt', 'arcgis_alt', 'https://w/0')
    check('an alternate source is not missing when the IGN zones are in the copy', missing([Z], [{'sid': 'x', 'src': 'IGN Géoplateforme ZNIEFF type I'}]) == [])
    check('an alternate source with no IGN zones in the copy is missing', missing([Z], [{'sid': 'x', 'src': 'other'}]) == [Z])
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        with gzip.open(t / 'W-XA.json.gz', 'wt') as f: json.dump({'saved': '2026-11-01', 'recs': [{'sid': src_id(A)}]}, f)
        rows = scan(t, ['XA', 'XB'], {'XA': [A, B], 'XB': [A]})
        check('scan: XA misses B, XB has no copy', [x['label'] for x in rows['XA']['missing']] == ['Reserves'] and rows['XB']['copy'] is None)
        (t / 'assets.txt').write_text('W-XA.json.gz\nW-XC.json.gz\n')
        json.dump({'countries': {'XA': {'missing': [row(B)]}}}, open(t / 'gaps.json', 'w'))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            main(['plan', '--assets', str(t / 'assets.txt'), '--gaps', str(t / 'gaps.json'), 'XA', 'XB', 'XC'])
        check(f'plan: only XC is built (XA gap, XB no copy): {buf.getvalue().split()}', buf.getvalue().split() == ['XC'])
    s = sources()
    check(f'the key\'s own sources are read ({len(s)} countries, GB {len(s.get("GB", []))})', len(s) > 20 and len(s.get('GB', [])) > 5)
    print('SELFTEST PASS' if ok else 'SELFTEST FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    if sys.argv[1:2] == ['--selftest']: sys.exit(selftest())
    sys.exit(main())
