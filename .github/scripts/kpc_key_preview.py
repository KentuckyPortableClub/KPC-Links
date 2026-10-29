#!/usr/bin/env python3
"""KEY PREVIEW for Brandon (chat 2, Oct 29 2026; Brandon 5:20 PM 'Let me see it 1st' before the new key is released).
Compares the key the SITE reads today (KPC-Data data/us-key, OLD) with the new Rule G key (KPC-Links data/us-key, NEW):
per state = parks newly outlined, outline lost, pieces added / removed, grade changes; and ~30 SAMPLE parks (a spread of
states and kinds of change) whose outlines are fetched from the official layers at 3 m (R-G6) for an old-vs-new picture.
  python3 kpc_key_preview.py compare OLD_DIR NEW_DIR OUT.json      (offline: counts + the sample list)
  python3 kpc_key_preview.py fetch OUT.json NEW_DIR GEO.json        (network: the sample outlines, old + new)
Read only; never fails."""
import glob, json, os, re, sys, time, urllib.parse, urllib.request

PAD = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0'
FWS = 'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0'
UA = {'User-Agent': 'KPC park-map bot (kentuckyportableclub.github.io; ham radio club)'}
MUST = ['US-12255', 'US-12271', 'US-8692', 'US-12189', 'US-10681', 'US-5707', 'US-11025', 'US-0425', 'US-0430', 'US-0063', 'US-0150', 'US-4476',
        'US-8188', 'US-3030', 'US-7610', 'US-6848', 'US-13409', 'US-10790', 'US-4374', 'US-2028']


def load(d):
    out = {}
    for f in glob.glob(os.path.join(d, 'US-??.json')):
        st = os.path.basename(f)[3:5]
        try:
            for r, p in json.load(open(f))['parks'].items(): out[(st, r)] = p
        except Exception: pass  # noqa: BLE001
    return out


def ids(p): return [str(x[0]) for x in (p or {}).get('m') or []]


def compare(old_d, new_d, out_p):
    O, N = load(old_d), load(new_d)
    per, changed = {}, []
    for k in sorted(set(O) | set(N)):
        st, r = k; o, n = O.get(k) or {}, N.get(k) or {}
        c = per.setdefault(st, {'parks': 0, 'new outline': 0, 'outline lost': 0, 'pieces added': 0, 'pieces removed': 0, 'grade changed': 0, 'same': 0})
        c['parks'] += 1
        a, b = set(ids(o)), set(ids(n))
        if b and not a: c['new outline'] += 1
        if a and not b: c['outline lost'] += 1
        c['pieces added'] += len(b - a); c['pieces removed'] += len(a - b)
        og = o.get('g') or ('pin' if not a else 'official'); ng = n.get('g') or ('pin' if not b else 'official')
        if og != ng: c['grade changed'] += 1
        if a == b: c['same'] += 1
        else: changed.append({'st': st, 'ref': r, 'n': n.get('n') or o.get('n'), 'old': [x[:4] for x in o.get('m') or []], 'new': [x[:4] for x in n.get('m') or []],
                              'old_g': og, 'new_g': ng, 'check': [x[:4] for x in n.get('c') or [] if re.search(r'R-G8|G-1', str(x[3]))][:4]})
    # samples: the named ones + a spread (one per state, biggest change first)
    byref = {c['ref']: c for c in changed}
    pick = [byref[r] for r in MUST if r in byref]
    seen = {c['st'] for c in pick}
    for c in sorted(changed, key=lambda c: -abs(len(c['new']) - len(c['old'])) - (5 if not c['old'] else 0)):
        if len(pick) >= 34: break
        if c['st'] in seen or c in pick: continue
        if sum(len(x) for x in (c['old'], c['new'])) > 60: continue   # keep the picture readable
        pick.append(c); seen.add(c['st'])
    tot = {k: sum(v[k] for v in per.values()) for k in next(iter(per.values()))}
    json.dump({'made': time.strftime('%Y-%m-%d %H:%M'), 'totals': tot, 'per_state': per, 'changed_count': len(changed), 'samples': pick}, open(out_p, 'w'), indent=1)
    print(f"::notice title=Key preview::{len(changed)} parks changed; totals {tot}; {len(pick)} samples", flush=True)


def get(url, params):
    for k in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url + '?' + urllib.parse.urlencode(params), headers=UA), timeout=90) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception:  # noqa: BLE001
            time.sleep(4 * (k + 1))
    return {}


def where(rid, L):
    if rid.isdigit(): return PAD, rid
    m = re.match(r'([a-z]+)(\d+)$', rid)
    if not m: return None, None
    pre, n = m.groups()
    if pre == 'fws': return FWS, n
    u = (L.get(pre) or [None])[0]
    if not u or u.startswith('file:'): return None, None
    return u.rsplit('/query', 1)[0], n


def fetch(out_p, new_d, geo_p):
    S = json.load(open(out_p))['samples']
    L = json.load(open(os.path.join(new_d, 'layers.json')))
    res, last = {}, {}
    for s in S:
        for side in ('old', 'new'):
            feats = []
            for x in s[side][:40]:
                url, n = where(str(x[0]), L)
                if not url: continue
                host = urllib.parse.urlparse(url).netloc
                w = 1.5 - (time.time() - last.get(host, 0))
                if w > 0: time.sleep(w)
                last[host] = time.time()
                j = get(url + '/query', {'objectIds': n, 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.00003, 'geometryPrecision': 6, 'outFields': '', 'f': 'json'})
                for f in j.get('features') or []:
                    rings = (f.get('geometry') or {}).get('rings') or (f.get('geometry') or {}).get('paths') or []
                    if rings: feats.append({'id': str(x[0]), 'name': x[1], 'rings': rings})
            res[f"{s['ref']}|{side}"] = feats
    json.dump(res, open(geo_p, 'w'))
    print(f"::notice title=Key preview shapes::{sum(1 for v in res.values() if v)} of {len(res)} old/new sides have shapes", flush=True)


if __name__ == '__main__':
    try:
        if sys.argv[1] == 'compare': compare(*sys.argv[2:5])
        elif sys.argv[1] == 'fetch': fetch(*sys.argv[2:5])
    except Exception as e: print(f'::notice title=Key preview::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
