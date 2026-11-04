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


# Nov 2 evening (Mapping; quality notes 2026-11-02, Witless Bay CA-1275 = 25,103 ac against about 7,166 in CPCAD): the park was
# joined to the same land three times (CPCAD, a CPCAD top-up copy and the Newfoundland copy), and every ring of every copy was
# stacked into one file. A record whose land is already drawn (80% or more) is now left out, and so is a ring that is only a dot.
# Nov 3 re-cut (Quality should-fix, S2-06): 3 distinct points is not enough - a 3-point FLAT ring (collinear, or a speck) passed and
# kept a zero-area "outline" (CA-4106 Skyline Park 0.0 ac, CA-4798 Twin Falls Tea House 0.0001 ac, CA-5438 Fort St. Louis 0.007 ac
# = 27 m2). A ring must also draw at least REAL_MIN_AC. The smallest real outline on main is CA-3699 at 0.066 ac, so 0.01 ac
# (about 40 m2) leaves every real one alone.
# Recut addendum (Quality grade of the recut; Brandon OK'd clearing all three to pins, relayed by Super 7:11-7:12 PM CST Nov 3):
# the three files are DELETED in this patch. A run alone would not clear them all: main() skips a file with detail_m (refined
# Oct 29), so only CA-4106 would go; CA-4798 (27 m2) and CA-5438 (0.5 m2) would stay as specks.
REAL_MIN_AC = 0.01
def _pts3(ring): return len({(round(q[0], 6), round(q[1], 6)) for q in ring}) >= 3
def _real(ring): return _pts3(ring) and _ring_ac(list(ring)) >= REAL_MIN_AC   # an outer ring / a fill piece
def _in(x, y, ring):
    ins, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi, xj, yj = ring[i][0], ring[i][1], ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi: ins = not ins
        j = i
    return ins
def _cover(new, kept, n=24):
    """Share of the new land (a list of rings) that kept rings already draw, from a grid of points inside the new rings."""
    if not kept: return 0.0
    xs = [q[0] for r in new for q in r]; ys = [q[1] for r in new for q in r]
    pts = [(min(xs) + (max(xs) - min(xs)) * (i + .5) / n, min(ys) + (max(ys) - min(ys)) * (k + .5) / n) for i in range(n) for k in range(n)]
    pts = [(x, y) for x, y in pts if sum(_in(x, y, r) for r in new) % 2]
    return sum(1 for x, y in pts if sum(_in(x, y, r) for r in kept) % 2) / len(pts) if pts else 0.0
def _in_poly(x, y, poly): return _in(x, y, poly[0]) and not any(_in(x, y, h) for h in poly[1:])   # outer ring minus its holes
def _ring_ac(r):
    """Rough acres of one ring (flat-earth shoelace at the ring's latitude): only used to size the land a copy alone draws."""
    import math
    if len(r) < 3: return 0.0
    lat = sum(q[1] for q in r) / len(r)
    k = 111320 * math.cos(math.radians(lat)) * 110574
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(r, r[1:] + r[:1]))) / 2 * k / 4046.86
def _unstack(coords):
    """The polygons of a file with repeats left out (same outline twice, or a polygon 80%+ inside the ones before it, holes
    counted, so an island in a lake is kept). None = nothing to change. [] = nothing real is left (the caller removes the file).
    Nov 3 (Quality, grade of the Canada key fixes):
    - a dot or a flat line (not _real) is left out here too, as the fill already does (CA-3380 Coyote Springs was a 2-point line
      drawn twice), and so is a hole that is only a dot;
    - a copy that is 80-98% inside the kept land is left out only when the land it alone draws is under 1 acre. At 80% East
      Sooke CA-3212 lost 137 ac and CA-3229 22 ac of real land (616 ac over 66 files; with this, about 11 ac)."""
    seen, keep, hit = set(), [], False
    for poly in coords or []:
        if not poly: continue
        if not _real(poly[0]): hit = True; continue
        if any(not _pts3(h) for h in poly[1:]): poly = [poly[0]] + [h for h in poly[1:] if _pts3(h)]; hit = True   # holes: only dots go (no area floor)
        k = frozenset((round(q[0], 4), round(q[1], 4)) for q in poly[0])
        if k in seen: hit = True; continue
        seen.add(k)
        if len(k) >= 3 and keep:
            xs = [q[0] for q in poly[0]]; ys = [q[1] for q in poly[0]]; n = 24
            pts = [(min(xs) + (max(xs) - min(xs)) * (i + .5) / n, min(ys) + (max(ys) - min(ys)) * (j + .5) / n) for i in range(n) for j in range(n)]
            pts = [(x, y) for x, y in pts if _in_poly(x, y, poly)]
            c = sum(1 for x, y in pts if any(_in_poly(x, y, kp) for kp in keep)) / len(pts) if pts else 0.0
            own = (1 - c) * max(0.0, _ring_ac(poly[0]) - sum(_ring_ac(h) for h in poly[1:]))
            if pts and (c >= .98 or (c >= .8 and own < 1.0)): hit = True; continue
        keep.append(poly)
    return keep if hit else None


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
    # a file THIS script wrote earlier (src 'KPC checked list', never refined) that repeats the same land: the repeats are taken out
    unstacked, emptied = [], []
    for f in sorted(OUT.glob('CA-*.json')):
        try: j = json.loads(f.read_text(encoding='utf-8'))
        except Exception: continue  # noqa: BLE001
        pr = j.get('properties') or {}
        if not str(pr.get('src', '')).startswith('KPC checked list') or 'detail_m' in pr: continue
        keep = _unstack((j.get('geometry') or {}).get('coordinates'))
        if keep is None: continue
        if not keep:   # Nov 3: only dots / flat lines: not an outline. The tools then show the pin, as for any park with no file.
            f.unlink(); emptied.append(f.stem); continue
        j['geometry']['coordinates'] = keep
        f.write_text(json.dumps(j, separators=(',', ':'), ensure_ascii=False), encoding='utf-8'); unstacked.append(f.stem)
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
            rings, names, srcs, approx, dup = [], [], [], False, []
            for m in p['m']:
                oid = str(m[0])
                r = next((x for x in by.get(oid, []) if low(m[1]) in (low(x.get('n')), low(x.get('nf')))), None)
                if not r: continue
                mine = [[[round(q[0], 5), round(q[1], 5)] for q in ring] for ring in r.get('_r') or []]
                mine = [pts for pts in mine if len(pts) >= 4 and _real(pts)]
                if not mine: continue
                if _cover(mine, [rg[0] for rg in rings]) >= .8: dup.append(str(m[0])); continue   # another copy of land already drawn
                rings += [[pts] for pts in mine]
                names.append(str(m[1])); srcs.append(str(r.get('src') or 'CPCAD'))
                if str(m[3]) == 'reviewed-approx': approx = True
            if dup: notice('Canada fill', f"{ref}: {len(dup)} joined record(s) are copies of land already drawn, left out: {', '.join(dup)[:150]}")
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
           + (f"; {len(retired)} retired park(s) removed: {', '.join(retired[:10])}" if retired else '')
           + (f"; {len(unstacked)} older file(s) had the same land drawn more than once (or dots / flat lines), taken out: {', '.join(unstacked[:12])}" if unstacked else '')
           + (f"; {len(emptied)} older file(s) held only dots / flat lines and were removed: {', '.join(emptied[:12])}" if emptied else ''))


if __name__ == '__main__':
    main()
