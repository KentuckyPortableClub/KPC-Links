#!/usr/bin/env python3
"""NO-BOUNDARY HUNT (chat 2, Oct 28 2026; Brandon 11:27 PM: 'look through the rest of the US that don't have boundaries, if they
are state park / WMA / nature preserve etc., look for slightly different names; make me a document with your findings').
For every US park in data/us-key with NO joined outline whose kind is a state / wildlife / preserve type (BLM, trails and
national units left out), asks around its POTA pin: (1) PAD-US (all categories) and (2) the state's own layers the key already
uses (data/us-key/layers.json 'sg<st>…'): which records hold the pin, which names lie within ~3 km. Names are compared with the
generic words taken out (state park / WMA / area / preserve …, SP/WMA/SRA abbreviations, Mt/Mount, St/Saint, Ft/Fort).
Writes .claude/build/research/nomatch-hunt.json (+ .md). Read only: nothing in the key changes. Never fails."""
import difflib, glob, json, os, pathlib, re, sys, time, urllib.parse, urllib.request

PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
UA = {'User-Agent': 'KPC park-map bot (kentuckyportableclub.github.io; ham radio club)'}
OUT = pathlib.Path('.claude/build/research')
KIND = re.compile(r'state|wildlife|nature|preserve|conservation|fishing lake|natural area|game|hatchery|refuge|wetland|heritage|historic site|recreation area|forest|park|sanctuary|marsh|management area|landing|access|harbor|beach|reserve', re.I)
SKIP = re.compile(r'\bBLM\b|Trail|National|Airstrip|Wild and Scenic', re.I)
GENERIC = ('state park preserve', 'state historic site', 'state historical site', 'state historical monument', 'state historical park', 'state recreation area',
           'state recreation site', 'state fishing lake', 'state fish hatchery', 'fish hatchery', 'state fish and wildlife area', 'fish and wildlife area',
           'wildlife management area', 'state wildlife area', 'state wildlife management area', 'state natural area', 'state nature preserve',
           'state conservation area', 'conservation area', 'state forest', 'state park', 'state beach', 'state harbor', 'state preserve', 'state reserve',
           'nature preserve', 'natural area', 'wildlife area', 'game land', 'game lands', 'state game land', 'state game lands', 'wetland management district',
           'recreation area', 'recreation site', 'historic site', 'nature park', 'nature reserve', 'wildlife refuge', 'management area', 'habitat',
           'unit', 'area', 'park', 'preserve', 'reserve', 'refuge', 'sanctuary', 'site', 'state', 'wma', 'sp', 'sra', 'sna', 'snp', 'shs', 'sf', 'wa', 'fwa', 'the', 'and', 'of')
ABBR = {'mt': 'mount', 'st': 'saint', 'ste': 'sainte', 'ft': 'fort', 'pt': 'point', 'lk': 'lake', 'cr': 'creek', 'ck': 'creek', 'is': 'island', 'isl': 'island',
        'r': 'river', 'riv': 'river', 'spgs': 'springs', 'spg': 'spring', 'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'hist': 'historic', 'mem': 'memorial'}


def core(name):
    t = re.sub(r"[’'`]s\b", 's', str(name or '').lower())
    t = ' '.join(ABBR.get(w, w) for w in re.sub(r'[^a-z0-9 ]', ' ', t).split())
    for g in sorted(GENERIC, key=len, reverse=True): t = re.sub(r'\b' + re.escape(g) + r'\b', ' ', t)
    return ' '.join(t.split())


def sim(a, b):
    ca, cb = core(a), core(b)
    if not ca or not cb: return 0.0, ca, cb
    if ca == cb: return 1.0, ca, cb
    ta, tb = set(ca.split()), set(cb.split())
    if ta <= tb or tb <= ta: return 0.92, ca, cb
    return round(difflib.SequenceMatcher(None, ca, cb).ratio(), 2), ca, cb


def get(url, params, tries=2):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url + '?' + urllib.parse.urlencode(params), headers=UA), timeout=60) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception:  # noqa: BLE001
            if k == tries - 1: return None
            time.sleep(3)


def ask(url, fields, lon, lat, d):
    """Records holding the pin, and records within d degrees (names only)."""
    base = {'outFields': fields, 'returnGeometry': 'false', 'f': 'json', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects', 'resultRecordCount': 60}
    a = get(url, dict(base, geometry=f'{lon},{lat}', geometryType='esriGeometryPoint')) or {}
    b = get(url, dict(base, geometry=f'{lon - d},{lat - d},{lon + d},{lat + d}', geometryType='esriGeometryEnvelope')) or {}
    return [f.get('attributes') or {} for f in a.get('features') or []], [f.get('attributes') or {} for f in b.get('features') or []], ('error' in a or 'error' in b or not a)


def pins():
    P = {}
    for f in glob.glob('data/parkinfo/US-*.json'):
        for r, v in json.load(open(f))['parks'].items():
            if v[5] is not None: P[r] = (v[0], v[5], v[6])
    return P


def main():
    P = pins(); L = json.load(open('data/us-key/layers.json'))
    todo = []
    for f in sorted(glob.glob('data/us-key/US-??.json')):
        st = f[-7:-5]
        for r, v in json.load(open(f))['parks'].items():
            if v.get('m'): continue
            ty = v.get('t') or ''
            if SKIP.search(ty) or not KIND.search(ty + ' ' + (v.get('n') or '')): continue
            if r in P: todo.append((st, r, v.get('n') or P[r][0], ty, P[r][1], P[r][2], v.get('c') or []))
    print(f'::notice title=No-boundary hunt::{len(todo)} state / wildlife / preserve parks with no outline to look at', flush=True)
    res, t0 = [], time.time()
    for k, (st, r, nm, ty, la, lo, keyc) in enumerate(todo):
        if time.time() - t0 > float(os.environ.get('MINUTES') or 150) * 60: print('out of time', flush=True); break
        found = []
        srcs = [('PAD-US', PADUS, 'Unit_Nm,Loc_Nm,Category,Own_Name,Mang_Name,GIS_Acres,Des_Tp', ('Unit_Nm', 'Loc_Nm'))]
        for key, (url, nf, label) in L.items():
            if key.startswith('sg' + st.lower()) and isinstance(url, str): srcs.append((label[:60], url, '*', (nf,)))
        for label, url, fields, nfs in srcs:
            inside, near, bad = ask(url, fields, lo, la, .03)
            if bad and not inside and not near: found.append({'src': label, 'error': 'did not answer'}); continue
            seen = set()
            for where, recs in (('pin inside', inside), ('within ~3 km', near)):
                for a in recs:
                    for nf in nfs:
                        n2 = a.get(nf)
                        if not n2 or (label, n2) in seen: continue
                        seen.add((label, n2))
                        s, c1, c2 = sim(nm, n2)
                        found.append({'src': label, 'name': n2, 'where': where, 'score': s, 'core': [c1, c2],
                                      'acres': a.get('GIS_Acres'), 'cat': a.get('Category'), 'owner': a.get('Own_Name') or a.get('Mang_Name')})
        named = sorted([x for x in found if x.get('score') is not None], key=lambda x: (-x['score'], x['where'] != 'pin inside'))
        best = named[0] if named else None
        inside_any = [x for x in named if x['where'] == 'pin inside']
        if best and best['score'] >= .9: cls = 'STRONG: same name with small differences'
        elif best and best['score'] >= .75: cls = 'LIKELY: close name'
        elif inside_any: cls = 'PIN INSIDE another record (different name: maybe the park is part of it)'
        elif any('error' in x for x in found) and not named: cls = 'NOT CHECKED: the map did not answer'
        else: cls = 'NOTHING NEAR: no record with a similar name within ~3 km'
        res.append({'st': st, 'ref': r, 'name': nm, 'type': ty, 'pin': [la, lo], 'class': cls, 'best': named[:4], 'key_candidates': keyc[:3],
                    'errors': [x['src'] for x in found if 'error' in x]})
        if k % 50 == 0: print(f'{k}/{len(todo)} {st} {r} {nm[:40]}: {cls[:20]}', flush=True)
        time.sleep(.2)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump({'about': "No-boundary hunt (chat 2, Oct 28 2026): state / wildlife / preserve parks with no joined outline, names near their POTA pin in PAD-US + the state's own layers. Read only.",
               'date': time.strftime('%Y-%m-%d'), 'parks': res}, open(OUT / 'nomatch-hunt.json', 'w'), indent=1)
    from collections import Counter
    c = Counter(x['class'].split(':')[0] for x in res)
    print('::notice title=No-boundary hunt::' + ' · '.join(f'{k} {v}' for k, v in c.most_common()), flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=No-boundary hunt::stopped: {str(e)[:200]}', flush=True)  # noqa: BLE001
    sys.exit(0)
