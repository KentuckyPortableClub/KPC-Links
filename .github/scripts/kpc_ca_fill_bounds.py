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
    by = {}
    for r in recs: by.setdefault(str(r.get('oid')), r)
    have = {p.stem for p in OUT.glob('CA-*.json')}
    wrote = 0
    for kf in sorted(glob.glob('data/ca-key/CA-*.json')):
        for ref, p in json.load(open(kf))['parks'].items():
            if not p.get('m') or ref in have: continue
            rings, names, srcs, approx = [], [], [], False
            for m in p['m']:
                r = by.get(str(m[0]))
                if not r: continue
                for ring in r.get('_r') or []:
                    pts = [[round(q[0], 5), round(q[1], 5)] for q in ring]
                    if len(pts) >= 4: rings.append([pts])
                names.append(str(m[1])); srcs.append(str(r.get('src') or 'CPCAD'))
                if str(m[3]) == 'reviewed-approx': approx = True
            if not rings: continue
            props = {'ref': ref, 'name': p.get('n'), 'cpcad': names[0], 'type': p.get('t') or '', 'src': 'KPC checked list (' + ', '.join(sorted(set(srcs)))[:120] + ')',
                     'srcShort': 'KPC checked list (' + (srcs[0] if srcs else 'CPCAD') + ')'}
            if approx: props['approx'] = True
            (OUT / f'{ref}.json').write_text(json.dumps({'type': 'Feature', 'properties': props, 'geometry': {'type': 'MultiPolygon', 'coordinates': rings[:80]}}, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
            wrote += 1
    notice('Canada fill', f'{wrote} park outline files written from the checked list (none overwritten)')


if __name__ == '__main__':
    main()
