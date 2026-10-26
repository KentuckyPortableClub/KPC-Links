#!/usr/bin/env python3
"""OUTLINE LEAD TESTER (chat 2, Oct 26 2026): the outline layer explorer (kpc_parking_explorer.py KIND=outline) lists
park polygon layers we do not read yet (data/outline-leads/). This asks each one: how many parks that still have NO
outline (data/us-key, data/ca-key) have an area of the same name in this layer, near the POTA pin? Layers are ranked by
that number -> data/outline-leads/tested.json; chat 2 adds the useful ones to data/state-gis.json. Adds nothing itself.
Time-limited, never fails."""
import json, math, os, pathlib, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from kpc_save import save_json

T0, LIMIT = time.time(), float(os.environ.get('MINUTES') or 150) * 60
UA = {'User-Agent': 'KPC outline lead tester (kentuckyportableclub.github.io)'}
D = pathlib.Path('data/outline-leads')
KINDW = re.compile(r'\b(national|state|provincial|park|parks|forest|wildlife|management|area|areas|refuge|recreation|recreational|historic|historical|'
                   r'site|preserve|reserve|natural|nature|monument|memorial|scenic|and|the|of|unit|tract|wma|sp|sra|nwr|conservation|trail|'
                   r'public|land|lands|game|fish|hunting|access|county|regional|municipal|city|provincial park|parc|de|du|la|le|des)\b')


def low(x): return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', str(x or '').lower().replace('&', ' and ')).split())
def core(x): return ' '.join(KINDW.sub(' ', low(x)).split())
def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', ' ')[:900]), flush=True)


def get(url, p):
    req = urllib.request.Request(url + '?' + urllib.parse.urlencode(p), headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r: j = json.loads(r.read().decode('utf-8', 'replace'))
    if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:100])
    return j


def missing():
    """{ST: [(ref, name core, lat, lon)]} parks with no outline yet."""
    P = {}
    for f in pathlib.Path('data/parkinfo').glob('US-*.json'):
        for r, v in json.load(open(f))['parks'].items(): P[r] = v
    try: P.update(json.load(open('data/parkinfo/CA.json'))['parks'])
    except Exception: pass  # noqa: BLE001
    out = {}
    for f in list(pathlib.Path('data/us-key').glob('US-*.json')) + list(pathlib.Path('data/ca-key').glob('CA-*.json')):
        if not re.fullmatch(r'(US|CA)-[A-Z]{2}', f.stem): continue
        st = f.stem[3:] if f.stem.startswith('US-') else f.stem
        for ref, p in json.load(open(f))['parks'].items():
            v = P.get(ref)
            if p.get('m') or not v or v[5] is None or not core(v[0]): continue
            out.setdefault(st, []).append((ref, core(v[0]), v[5], v[6], v[7] if len(v) > 7 and isinstance(v[7], int) else 0))
    return out


def main():
    MISS = missing()
    try: old = json.load(open(D / 'tested.json')).get('layers', {})
    except Exception: old = {}  # noqa: BLE001
    leads = []
    for f in sorted(D.glob('*.json')):
        if f.name == 'tested.json': continue
        d = json.load(open(f))
        for x in d.get('leads', []):
            if not x.get('known') and x.get('count', 0) <= 30000: leads.append((d['st'], x))
    leads.sort(key=lambda t: (t[1]['url'] in old, -len(MISS.get(t[0], []))))
    res = dict(old)
    n = 0
    for st, x in leads:
        if time.time() - T0 > LIMIT: break
        parks = MISS.get(st, [])
        if not parks: continue
        u = x['url'].rstrip('/') + '/query'
        flds = [x['area']] if x.get('area') else []
        flds += [f for f in x.get('fields', []) if re.search(r'name|nm$|title|label|site|park|unit|area', f, re.I) and f not in flds][:3]
        if not flds: continue
        hits, off, seen = {}, 0, 0
        try:
            while seen < 30000:
                j = get(u, {'where': '1=1', 'outFields': ','.join(flds), 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.01,
                            'geometryPrecision': 3, 'resultOffset': off, 'resultRecordCount': 1000, 'f': 'json'})
                fs = j.get('features') or []
                for ft in fs:
                    rs = (ft.get('geometry') or {}).get('rings') or []
                    pts = [p for r in rs for p in r]
                    if not pts: continue
                    bb = [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]
                    names = {core(v) for v in (ft.get('attributes') or {}).values() if isinstance(v, str) and core(v)}
                    for ref, c, la, lo, acts in parks:
                        if c in names and bb[0] - .3 <= lo <= bb[2] + .3 and bb[1] - .3 <= la <= bb[3] + .3: hits[ref] = acts
                seen += len(fs); off += len(fs)
                if not fs or not j.get('exceededTransferLimit'): break
                time.sleep(.3)
        except Exception as e:  # noqa: BLE001
            res[x['url']] = {'st': st, 'layer': x['layer'], 'error': str(e)[:80]}; continue
        n += 1
        res[x['url']] = {'st': st, 'service': x['service'], 'layer': x['layer'], 'name_fields': flds, 'records': x.get('count'),
                         'parks_it_would_give': len(hits), 'activations_covered': sum(hits.values()), 'parks': sorted(hits)[:60],
                         'agency': x.get('agency', ''), 'tested': time.strftime('%Y-%m-%d')}
    ranked = dict(sorted(res.items(), key=lambda kv: -(kv[1].get('parks_it_would_give') or 0)))
    save_json(D / 'tested.json', {'about': 'Outline leads tested: parks with NO outline yet that have a same-name area in the layer near their pin. '
                                           'Chat 2 adds the good layers to data/state-gis.json (the keys then join by their own rules).', 'layers': ranked}, indent=1)
    good = [(v['st'], v.get('parks_it_would_give'), v.get('layer')) for v in ranked.values() if v.get('parks_it_would_give')]
    notice('Outline lead tester', f'{n} layers tested this run; {len(good)} would give parks; top: {good[:12]}')


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        notice('Outline lead tester', f'stopped: {e}')
    sys.exit(0)
