#!/usr/bin/env python3
"""PER-LAYER NAMES DUMP for chat 8 (chat 2, Oct 29 2026; chat 8's ask + Brandon 'add them to your list'): every record of every
layer the US answer key already reads (data/us-key/layers.json), as [name, lat, lon, acres], so the parks with no outline can be
matched by hand against the layers' OWN names. Read only. Writes .claude/build/research/layer-names/<group>.json.gz
(group = the state for 'sg<st>…' layers, else 'other') + index.json (layer key, label, records, status). Never fails."""
import gzip, json, math, os, pathlib, sys, time, urllib.parse, urllib.request

UA = {'User-Agent': 'KPC park-map bot (kentuckyportableclub.github.io; ham radio club)'}
OUT = pathlib.Path('.claude/build/research/layer-names')


def get(url, params):
    for k in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url + '?' + urllib.parse.urlencode(params), headers=UA), timeout=120) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception:  # noqa: BLE001
            time.sleep(5 * (k + 1))
    return None


def ring_area_ac(r, lat):
    kx, ky = 111320 * math.cos(math.radians(lat)), 110574
    return abs(sum((a[0] * kx) * (b[1] * ky) - (b[0] * kx) * (a[1] * ky) for a, b in zip(r, r[1:] + r[:1]))) / 2 / 4046.86


def main():
    L = json.load(open('data/us-key/layers.json')); OUT.mkdir(parents=True, exist_ok=True)
    groups, index, t0 = {}, {}, time.time()
    for key, val in L.items():
        if time.time() - t0 > float(os.environ.get('MINUTES') or 150) * 60: index[key] = {'status': 'not read (out of time)'}; continue
        url, nf, label = (list(val) + ['', '', ''])[:3]
        if not isinstance(url, str) or not url.endswith('/query'): index[key] = {'status': 'not a map query (zip or other)', 'label': label}; continue
        g = key[2:4].upper() if key.startswith('sg') else 'other'
        recs, off, ok = [], 0, True
        while True:
            j = get(url, {'where': '1=1', 'outFields': nf, 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': .001, 'geometryPrecision': 5,
                          'resultOffset': off, 'resultRecordCount': 1000, 'f': 'json'})
            if not j or 'error' in j or 'features' not in j: ok = False; break
            fs = j['features']
            for f in fs:
                gm = f.get('geometry') or {}; nm = (f.get('attributes') or {}).get(nf)
                rings = gm.get('rings') or ([[[gm['x'], gm['y']]]] if 'x' in gm else []) or gm.get('paths') or []
                pts = [p for r in rings for p in r]
                if not pts: continue
                la = sum(p[1] for p in pts) / len(pts); lo = sum(p[0] for p in pts) / len(pts)
                ac = round(sum(ring_area_ac(r, la) for r in (gm.get('rings') or []) if len(r) > 2), 1)
                recs.append([nm, round(la, 5), round(lo, 5), ac])
            if not fs or not j.get('exceededTransferLimit'): ok = True; break
            off += len(fs)
            if off > 60000: break
        for r in recs: r.append(key)
        groups.setdefault(g, []).extend(recs)
        index[key] = {'label': label, 'name_field': nf, 'records': len(recs), 'status': 'read' if ok else 'did not answer / partly read'}
        print(f'{key}: {len(recs)} records ({index[key]["status"]})', flush=True)
        time.sleep(.5)
    for g, recs in groups.items():
        (OUT / f'{g}.json.gz').write_bytes(gzip.compress(json.dumps({'cols': ['name', 'lat', 'lon', 'acres', 'layer'], 'rows': recs}, separators=(',', ':')).encode(), 9))
    json.dump({'about': "Names in every layer the US key reads (chat 2 for chat 8, Oct 29): rows [name, lat, lon, acres (outline area), layer key]; lat/lon = the outline's mean point. Read only.",
               'date': time.strftime('%Y-%m-%d'), 'layers': index}, open(OUT / 'index.json', 'w'), indent=1)
    print(f"::notice title=Layer names::{sum(len(v) for v in groups.values())} records from {sum(1 for v in index.values() if v.get('records'))} layers in {len(groups)} files", flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Layer names::stopped: {str(e)[:200]}', flush=True)  # noqa: BLE001
    sys.exit(0)
