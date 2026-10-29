#!/usr/bin/env python3
"""LAYERED-LAND LIST (chat 2, Oct 29 2026; chat 8's list + Brandon 7:48 AM 'track them for review', rule R4). Every pair of POTA
parks in the 2-fer files where one is a FEDERAL unit and the other a STATE park / WMA / forest (rows live, very tight, water
only, merged, not sure) goes into <fers>/layered.json. New pairs are APPENDED each run; columns already filled are KEPT.
With NET=1 the empty columns are filled from PAD-US at the patch (point query): Own_Type / Own_Name / Mang_Type / Mang_Name /
Des_Tp of every PAD-US record there (federal owns + state manages = layered = 2-fer by R4; state owns = hard boundary).
POTA's type word comes from parkinfo. Usage: kpc_fers_layered.py [fers dir] [parkinfo dir]. Never fails."""
import glob, gzip, json, os, re, sys, time, urllib.parse, urllib.request

PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
UA = {'User-Agent': 'KPC park-map bot (kentuckyportableclub.github.io; ham radio club)'}
FED = re.compile(r'national|federal|\bblm\b|bureau of land|wilderness|corps|usace|refuge', re.I)
STATE = re.compile(r'state|provincial|wildlife management|\bwma\b|game land|fish and wildlife area|conservation area', re.I)
KEEP = ('candidate', 'very tight', 'water only', 'merged', 'not sure')


def pad_at(lon, lat):
    for k in range(3):
        try:
            q = {'geometry': f'{lon},{lat}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                 'outFields': 'Unit_Nm,Own_Type,Own_Name,Mang_Type,Mang_Name,Des_Tp,Category', 'returnGeometry': 'false', 'f': 'json'}
            with urllib.request.urlopen(urllib.request.Request(PADUS + '?' + urllib.parse.urlencode(q), headers=UA), timeout=60) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            time.sleep(2)
            return [f.get('attributes') or {} for f in j.get('features') or []]
        except Exception:  # noqa: BLE001
            time.sleep(5 * (k + 1))
    return None


def main(fdir='data/fers', pdir='data/parkinfo'):
    P = {}
    for f in glob.glob(os.path.join(pdir, 'US-*.json')):
        try:
            for r, v in json.load(open(f))['parks'].items(): P[r] = (str(v[0]), str(v[2]) if len(v) > 2 else '')
        except Exception: pass  # noqa: BLE001
    out_p = os.path.join(fdir, 'layered.json')
    old = {}
    try:
        for x in json.load(open(out_p)).get('pairs') or []: old['+'.join(sorted(x['refs']))] = x
    except Exception: pass  # noqa: BLE001
    found = {}
    for f in sorted(glob.glob(os.path.join(fdir, 'US-*.json')) + glob.glob(os.path.join(fdir, 'US-*.json.gz'))):
        b = os.path.basename(f)
        if not re.match(r'US-[A-Z]{2}\.json', b): continue
        try: d = json.load(gzip.open(f, 'rt') if f.endswith('.gz') else open(f))
        except Exception: continue  # noqa: BLE001
        for s in d.get('spots') or []:
            st = str(s.get('status', ''))
            if not st.startswith(KEEP) or len(s.get('refs') or []) != 2: continue
            a, c = s['refs']
            fa = [r for r in (a, c) if r in P and FED.search(P[r][0] + ' ' + P[r][1])]
            sa = [r for r in (a, c) if r in P and r not in fa and STATE.search(P[r][0] + ' ' + P[r][1])]
            if not fa or not sa: continue
            k = '+'.join(sorted((a, c)))
            e = found.setdefault(k, old.get(k) or {'area': b[:5], 'refs': sorted((a, c)), 'names': {r: P[r][0] for r in (a, c)},
                                                   'federal': fa, 'state': sa, 'pota_type': {r: P[r][1] for r in (a, c)}, 'added': time.strftime('%Y-%m-%d')})
            e['rows'] = e.get('rows_seen', 0) + 1; e['rows_seen'] = e['rows']
            if st.startswith('candidate') or not e.get('status'): e['status'] = st[:90]
            e['acres'] = max(e.get('acres') or 0, s.get('acres') or 0); e['checked'] = s.get('checked') or e.get('checked')
            if not e.get('center') or st.startswith('candidate'): e['center'] = s.get('center')
    for e in found.values(): e.pop('rows_seen', None)
    filled = 0
    if os.environ.get('NET') == '1':
        t0 = time.time()
        for e in found.values():
            if e.get('pad_at_patch') is not None or not e.get('center') or time.time() - t0 > 60 * float(os.environ.get('MINUTES') or 40): continue
            rr = pad_at(e['center'][1], e['center'][0])
            if rr is None: continue
            e['pad_at_patch'] = [{k: a.get(k) for k in ('Unit_Nm', 'Own_Type', 'Own_Name', 'Mang_Type', 'Mang_Name', 'Des_Tp', 'Category')} for a in rr[:8]]
            own = {str(a.get('Own_Type')) for a in rr if a.get('Category') == 'Fee'}
            e['owner_at_patch'] = ' + '.join(sorted(own)) or 'no fee record'
            # Brandon Oct 29 10:10 AM: 'make sure that state land is not another park': every PAD-US unit at the patch is matched
            # to POTA's list; a POTA park other than the two in the pair = listed in 'other_parks_here' (a 3-fer to test, or the
            # land belongs to a different park)
            def _w(x): return {w for w in re.sub(r'[^a-z0-9 ]', ' ', str(x or '').lower()).split() if w not in ('state', 'park', 'national', 'forest', 'area', 'the', 'of', 'and', 'wildlife', 'management', 'recreation')}
            others = []
            for a in rr:
                wn = _w(a.get('Unit_Nm'))
                if not wn: continue
                hit = next((r for r, (nm, ty) in P.items() if r not in e['refs'] and _w(nm) == wn), None)
                if hit and hit not in [o[0] for o in others]: others.append([hit, P[hit][0], a.get('Unit_Nm'), a.get('Own_Type')])
            e['other_parks_here'] = others
            e['layered'] = 'FED owns (layered: R4 2-fer)' if own and all(o == 'FED' for o in own) else ('state owns (hard boundary: R4 not a 2-fer)' if own and all(o in ('STAT',) for o in own) else 'mixed / unknown: look')
            filled += 1
    json.dump({'about': "Layered-land list (federal x state POTA pairs, rule R4; chat 2 bot, from chat 8's list): new pairs appended each run, filled columns kept. 'layered' = PAD-US fee owner at the patch: FED owns = layered (2-fer), state owns = hard boundary. Not the verdict: the line decides.",
               'made': time.strftime('%Y-%m-%d'), 'pairs': sorted(found.values(), key=lambda e: (e['area'], e['refs']))}, open(out_p, 'w'), indent=1, ensure_ascii=False)
    oth = [e for e in found.values() if e.get('other_parks_here')]
    print(f"::notice title=Layered-land list::{len(found)} federal x state pairs ({len(set(found) - set(old))} new), {filled} filled from PAD-US at the patch; {len(oth)} have ANOTHER POTA park on the patch: " + '; '.join(f"{'+'.join(e['refs'])}: {', '.join(o[1] for o in e['other_parks_here'])}" for e in oth[:8]), flush=True)


if __name__ == '__main__':
    try: main(*sys.argv[1:3])
    except Exception as e: print(f'::notice title=Layered-land list::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
