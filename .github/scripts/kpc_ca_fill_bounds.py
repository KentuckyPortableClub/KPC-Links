#!/usr/bin/env python3
"""Fill data/canada-bounds/ from the checked Canada list (Opus, Oct 22; Brandon: 'go for it' on the waiting lists).

The website draws a Canadian park from data/canada-bounds/<REF>.json (written by kpc_canada_bounds.py, its own older
matcher). The checked list (data/ca-key/, kpc_ca_key.py) joins more parks than that matcher found: on Oct 22, 354 parks
were joined in the list but had no file, so the tools showed no outline. This writes a file for every joined park that
has NONE yet, from the saved outlines (cache/ca/CA-ALL.json.gz, the 'saved shapes' release). It never overwrites an
existing file. A join a person marked approximate ('reviewed-approx') is written with properties.approx = true and the
tools label it 'Approximate, not official'.
Run after kpc_ca_key.py: GEO_CACHE_MODE=only python3 .github/scripts/kpc_ca_fill_bounds.py"""
import gzip, json, glob, os, pathlib

OUT = pathlib.Path('data/canada-bounds')
CF = pathlib.Path(os.environ.get('GEO_CACHE') or 'cache/ca') / 'CA-ALL.json.gz'


def notice(t, m): print(f'::notice title={t}::{m}', flush=True)


def main():
    if not CF.exists():
        notice('Canada fill', 'no saved outlines (cache/ca/CA-ALL.json.gz): nothing written'); return
    with gzip.open(CF, 'rt', encoding='utf-8') as f: recs = json.load(f).get('recs') or []
    # Oct 25 (round 5 hand checks: 400+ Québec ZEC / réserve / parc files were one wrong shape): ids repeat from layer to
    # layer, so an id alone is not enough - the saved record must also carry the joined NAME
    by = {}
    for r in recs: by.setdefault(str(r.get('oid')), []).append(r)
    low = lambda x: ' '.join(str(x or '').lower().split())
    have = {p.stem for p in OUT.glob('CA-*.json')}
    wrote = dropped = 0
    # Oct 25 (storage plan Stage 1: retire most of this 30 MB folder): a park whose joined land is ALL in CPCAD needs no
    # saved file - the website fetches CPCAD outlines live by id (KPCB.caKey; the Map Rep Tool Box already reads CPCAD from
    # the browser). Files are kept only for parks joined to a provincial map or a download, which a browser may not reach.
    cp_only = lambda p: all(str(m[0]).isdigit() for m in p.get('m') or [])
    keyed = set()
    for kf in sorted(glob.glob('data/ca-key/CA-*.json')):
        for ref, p in json.load(open(kf))['parks'].items():
            keyed.add(ref)
            if p.get('m') and cp_only(p) and ref in have:
                (OUT / f'{ref}.json').unlink(); have.discard(ref); dropped += 1
    # Oct 28 (tune pass): a park POTA no longer lists (not in the answer key at all, e.g. CA-2156) loses its old outline file.
    # Only when the key is whole (5,000+ parks), so a half-built key can never empty the folder.
    retired = sorted(have - keyed) if len(keyed) > 5000 else []
    for ref in retired:
        (OUT / f'{ref}.json').unlink(); have.discard(ref)
    for kf in sorted(glob.glob('data/ca-key/CA-*.json')):
        for ref, p in json.load(open(kf))['parks'].items():
            if not p.get('m') or ref in have or cp_only(p): continue
            rings, names, srcs, approx = [], [], [], False
            for m in p['m']:
                oid = str(m[0])
                r = next((x for x in by.get(oid, []) if low(m[1]) in (low(x.get('n')), low(x.get('nf')))), None)
                if not r: continue
                for ring in r.get('_r') or []:
                    pts = [[round(q[0], 5), round(q[1], 5)] for q in ring]
                    if len(pts) >= 4: rings.append([pts])
                names.append(str(m[1])); srcs.append(str(r.get('src') or 'CPCAD'))
                if str(m[3]) == 'reviewed-approx': approx = True
            if not rings: continue
            # Oct 31 (Fable review #10): a rough cached outline (median segment over ~50 m) is NOT written as the park's file: the refine
            # step fetches it fine (R-G6, 3-5 m); until then the tools draw the record live
            import math as _mt
            segs = sorted(_mt.hypot((b[0] - a[0]) * 111320 * _mt.cos(_mt.radians(a[1])), (b[1] - a[1]) * 110574) for rg in rings for ring_ in rg for a, b in zip(ring_, ring_[1:]))
            if segs and segs[len(segs) // 2] > 50: continue
            props = {'ref': ref, 'name': p.get('n'), 'cpcad': names[0], 'type': p.get('t') or '', 'src': 'KPC checked list (' + ', '.join(sorted(set(srcs)))[:120] + ')',
                     'srcShort': 'KPC checked list (' + (srcs[0] if srcs else 'CPCAD') + ')'}
            if approx: props['approx'] = True
            (OUT / f'{ref}.json').write_text(json.dumps({'type': 'Feature', 'properties': props, 'geometry': {'type': 'MultiPolygon', 'coordinates': rings[:80]}}, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
            wrote += 1
    notice('Canada fill', f'{wrote} park outline files written from the checked list (none overwritten); {dropped} CPCAD-only files removed (drawn live now)'
           + (f"; {len(retired)} retired park(s) removed: {', '.join(retired[:10])}" if retired else ''))


if __name__ == '__main__':
    main()
