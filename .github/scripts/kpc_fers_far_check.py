#!/usr/bin/env python3
"""FAR-SPOT PARCEL CHECK (chat 2, Oct 29 2026; Brandon 8:07 AM on the held far rows: 'check make sure parcels are correct ...
some parks are huge, Daniel Boone example ... are the maps correct? does it overlap in a spot somewhere? if so yes').
For every row the far-spot hold set to NOT SURE, ask the OFFICIAL map which of the far park's joined records holds the
spot (a point query by record id). RELEASE (status back to what it was) when a record that carries the park's own name
holds the spot = the park really owns a tract there, so the overlap is real. KEEP HELD (with the reason) when none of the
park's records holds the spot, the record holding it carries another name, or the map did not answer. Writes
<fers dir>/far-check.json (one line per row: verdict + record) and a notice. Usage: kpc_fers_far_check.py [fers dir] [KPC-Links dir]."""
import glob, gzip, json, os, re, sys, time, urllib.parse, urllib.request

UA = {'User-Agent': 'KPC park-map bot (kentuckyportableclub.github.io; ham radio club)'}
PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0'
CPCAD = 'https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0'
HELD = 'not sure: this spot is '
GEN = {'state', 'park', 'forest', 'wildlife', 'management', 'area', 'wma', 'game', 'land', 'lands', 'preserve', 'nature', 'natural', 'the', 'of', 'and',
       'provincial', 'reserve', 'conservation', 'recreation', 'site', 'historic', 'protected', 'national', 'environmental', 'fish', 'refuge', 'unit'}
LAST = {}


def get(url, params):
    host = urllib.parse.urlparse(url).netloc
    for k in range(3):
        w = 2 - (time.time() - LAST.get(host, 0))
        if w > 0: time.sleep(w)
        try:
            LAST[host] = time.time()
            with urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), headers=UA), timeout=90) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if 'error' in j: raise RuntimeError(str(j['error'])[:80])
            return j
        except Exception:  # noqa: BLE001
            if k == 2: return None
            time.sleep(5 * (k + 1))


def words(x): return {w for w in re.sub(r'[^a-z0-9 ]', ' ', str(x or '').lower()).split() if w not in GEN and len(w) > 1}


def same_name(a, b):
    wa, wb = words(a), words(b)
    if not wa or not wb: return False
    return wa <= wb or wb <= wa or len(wa & wb) >= max(1, min(len(wa), len(wb)) - 0)


def holds(url, oids, lon, lat):
    """{oid: attrs} of these records that contain the point; None = the map did not answer."""
    j = get(url.rstrip('/') + '/query', {'objectIds': ','.join(map(str, oids)), 'geometry': f'{lon},{lat}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326,
                                         'spatialRel': 'esriSpatialRelIntersects', 'outFields': '*', 'returnGeometry': 'false', 'f': 'json'})
    if j is None or 'features' not in j: return None
    oidf = j.get('objectIdFieldName') or 'OBJECTID'
    return {str((f.get('attributes') or {}).get(oidf)): f.get('attributes') or {} for f in j['features']}


def main(fdir='data/fers', links='.'):
    key, layers = {}, {}
    for pat, lf in (('data/us-key/US-??.json', 'data/us-key/layers.json'), ('data/ca-key/CA-??.json', 'data/ca-key/layers.json')):
        for f in glob.glob(os.path.join(links, pat)):
            try: key.update(json.load(open(f))['parks'])
            except Exception: pass  # noqa: BLE001
        try:
            L = json.load(open(os.path.join(links, lf)))
            for k, v in L.items(): layers[k] = v if isinstance(v, list) else [v[0]] if isinstance(v, (list, tuple)) else [v]
        except Exception: pass  # noqa: BLE001
    rep, rel, kept = [], 0, 0
    for f in sorted(glob.glob(os.path.join(fdir, '*-*.json')) + glob.glob(os.path.join(fdir, '*-*.json.gz'))):
        b = os.path.basename(f)
        if not re.match(r'(US|CA)-[A-Z]{2}\.json', b): continue
        gz = f.endswith('.gz')
        try: d = json.load(gzip.open(f, 'rt') if gz else open(f))
        except Exception: continue  # noqa: BLE001
        changed = False
        for s in d.get('spots') or []:
            st = str(s.get('status', ''))
            if not st.startswith(HELD) or not s.get('was'): continue
            m = re.search(r"km from (.+?)'s POTA pin", st); far = m.group(1) if m else ''
            la, lo = s['center']
            ref = next((r for r in s['refs'] if (key.get(r) or {}).get('n') and same_name((key[r] or {}).get('n'), far)), None) or next((r for r in s['refs']), None)
            mm = (key.get(ref) or {}).get('m') or []
            groups = {}
            for x in mm:
                rid = str(x[0])
                if rid.isdigit(): groups.setdefault(CPCAD if ref.startswith('CA-') else PADUS, []).append((rid, x[1]))
                else:
                    pre, _, n = rid.rpartition(':')
                    if not pre:   # US state-layer ids are '<key><objectid>' ('sgflf329'): the key's layers.json maps the letters
                        mt = re.match(r'([a-z]+)(\d+)$', rid); pre, n = (mt.group(1), mt.group(2)) if mt else ('', '')
                    urls = layers.get(pre) or []
                    u = urls[0] if urls and isinstance(urls[0], str) else None
                    if u and n.isdigit(): groups.setdefault(u, []).append((n, x[1]))
            found, answered, why = [], True, ''
            for url, items in groups.items():
                h = holds(url, [i for i, _ in items], lo, la)
                if h is None: answered = False; continue
                for i, nm in items:
                    if i in h: found.append((i, nm))
            ok = [x for x in found if same_name(x[1], (key.get(ref) or {}).get('n') or far)]
            if ok:
                s['status'] = s.pop('was'); s['far_check'] = f"released {time.strftime('%Y-%m-%d')}: the official record '{ok[0][1]}' ({ok[0][0]}) of {far} holds this spot"
                rel += 1; changed = True; verdict = 'released'
            else:
                why = ('the map did not answer' if not answered and not found else
                       f"the record holding the spot is '{found[0][1]}', not {far}" if found else
                       f"none of {far}'s official records holds this spot (our saved outline did): a wrong piece")
                s['far_check'] = f"kept on hold {time.strftime('%Y-%m-%d')}: {why}"; kept += 1; changed = True; verdict = 'held'
            rep.append({'file': b, 'id': s['id'], 'park': far, 'ref': ref, 'verdict': verdict, 'why': s['far_check']})
        if changed:
            txt = json.dumps(d, indent=1, ensure_ascii=False)
            try:
                sys.path.insert(0, os.path.join(links, '.github/scripts')); from kpc_save import canon
                txt = canon(d, 1)
            except Exception: pass  # noqa: BLE001
            if gz:
                with gzip.open(f, 'wt', encoding='utf-8') as fh: fh.write(txt)
            else: open(f, 'w').write(txt if txt.endswith('\n') else txt + '\n')
    json.dump({'date': time.strftime('%Y-%m-%d'), 'released': rel, 'kept': kept, 'rows': rep}, open(os.path.join(fdir, 'far-check.json'), 'w'), indent=1)
    print(f"::notice title=2-fer far-spot check::{rel} released (the park's own official record holds the spot), {kept} kept on hold · "
          + '; '.join(f"{x['park']}: {x['verdict']}" for x in rep[:12]), flush=True)


if __name__ == '__main__':
    try: main(*sys.argv[1:3])
    except Exception as e: print(f'::notice title=2-fer far-spot check::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
