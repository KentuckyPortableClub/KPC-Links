"""Tests the outline leads in data/state-gis-leads-oct24.json (Brandon's sheet, Oct 24) from GitHub, because Claude's
sessions cannot reach the state map servers. For each lead: does the service answer, which of its layers are outlines
(polygons), which field holds the name, how many areas, three sample names, and does it hold the park named on the
sheet (a name search for that park's longest word). Writes data/state-gis-leads-tested.json for the mapping chat to read.
Never fails. Leads whose service is already in data/state-gis.json are marked 'already in' and not fetched."""
import json, re, time, urllib.parse, urllib.request, pathlib

UA = {'User-Agent': 'KPC (kentuckyportableclub.github.io)'}
OUT = pathlib.Path('data/state-gis-leads-tested.json')
GEN = r"state|park|parks|natural|nature|preserve|area|areas|recreation|historic|site|forest|wildlife|management|reserve|national|the|of|and|lake|river"


def get(u, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as r:
        j = json.loads(r.read().decode('utf-8', 'replace'))
    if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:160])
    return j


def name_field(flds):
    strs = [f['name'] for f in flds if f.get('type') == 'esriFieldTypeString']
    good = [f for f in strs if re.search(r'name|nm|facility|label|site|unit|prop', f, re.I)
            and not re.search(r'admin|state|county|office|agency|own|mgr|manag|type|desig|file|url|link|city|region|district', f, re.I)]
    return good[0] if good else (strs[0] if strs else '')


def test_layer(lu, park):
    L = get(lu + '?f=json')
    out = {'url': lu, 'name': L.get('name'), 'geom': L.get('geometryType')}
    if 'Polygon' not in str(L.get('geometryType', '')): return out
    flds = L.get('fields') or []
    nf = name_field(flds); out['nameField'] = nf
    out['fields'] = [f['name'] for f in flds][:40]
    try: out['count'] = get(lu + '/query?' + urllib.parse.urlencode({'where': '1=1', 'returnCountOnly': 'true', 'f': 'json'})).get('count')
    except Exception as e: out['countErr'] = str(e)[:120]  # noqa: BLE001
    if nf:
        try:
            j = get(lu + '/query?' + urllib.parse.urlencode({'where': '1=1', 'outFields': nf, 'returnGeometry': 'false', 'resultRecordCount': 3, 'f': 'json'}))
            out['sample'] = [(f.get('attributes') or {}).get(nf) for f in j.get('features', [])]
        except Exception as e: out['sampleErr'] = str(e)[:120]  # noqa: BLE001
        words = sorted((w for w in re.findall(r"[A-Za-z]+", park or '') if len(w) > 3 and not re.fullmatch(GEN, w, re.I)), key=len, reverse=True)
        if words:
            w = words[0]
            for where in (f"UPPER({nf}) LIKE '%{w.upper()}%'", f"{nf} LIKE '%{w}%'", f"{nf} LIKE '%{w.upper()}%'"):
                try:
                    j = get(lu + '/query?' + urllib.parse.urlencode({'where': where, 'outFields': nf, 'returnGeometry': 'false', 'resultRecordCount': 5, 'f': 'json'}))
                    hits = [(f.get('attributes') or {}).get(nf) for f in j.get('features', [])]
                    out['parkWord'] = w; out['parkHits'] = hits
                    if hits: break
                except Exception as e: out['parkErr'] = str(e)[:120]  # noqa: BLE001
    return out


def main():
    leads = json.load(open('data/state-gis-leads-oct24.json'))['states']
    try: have = {str(l.get('url') or '').rsplit('/', 1)[0].rstrip('/') for v in json.load(open('data/state-gis.json'))['states'].values() for l in v}
    except Exception: have = set()  # noqa: BLE001
    res = {}
    for st, rows in sorted(leads.items()):
        for row in rows:
            link = str(row.get('link') or '').strip().split('?')[0].rstrip('/')
            r = {'park': row.get('park'), 'ref': row.get('ref'), 'link': link, 'layers': []}
            res.setdefault(st, []).append(r)
            m = re.match(r'(.*/(?:MapServer|FeatureServer))(?:/(\d+))?$', link)
            if not m: r['status'] = 'not a map service address (portal / item page)'; continue
            svc, lid = m.group(1), m.group(2)
            if svc.rstrip('/') in have: r['status'] = 'already in state-gis.json'; continue
            try:
                lays = [f'{svc}/{lid}'] if lid else [f"{svc}/{l['id']}" for l in (get(svc + '?f=json').get('layers') or []) if not l.get('subLayerIds')][:15]
            except Exception as e:  # noqa: BLE001
                r['status'] = f'service did not answer: {str(e)[:120]}'; continue
            for lu in lays:
                try: r['layers'].append(test_layer(lu, row.get('park')))
                except Exception as e: r['layers'].append({'url': lu, 'err': str(e)[:120]})  # noqa: BLE001
                time.sleep(.3)
            poly = [x for x in r['layers'] if 'Polygon' in str(x.get('geom'))]
            r['status'] = ('GOOD: outlines + the sheet\'s park found' if any(x.get('parkHits') for x in poly) else
                           'outlines, but the sheet\'s park was not found by name' if poly else 'no outline layers')
            print(f"{st}: {r['status']} ({link})", flush=True)
    OUT.write_text(json.dumps({'tested': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()), 'states': res}, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    tally = {}
    for v in res.values():
        for r in v: tally[r['status'].split(':')[0]] = tally.get(r['status'].split(':')[0], 0) + 1
    print('::notice title=Outline leads tested::' + '; '.join(f'{k}: {n}' for k, n in sorted(tally.items())), flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Outline leads::stopped early: {e}', flush=True)  # noqa: BLE001
