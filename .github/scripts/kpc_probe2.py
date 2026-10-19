"""TEMPORARY probe (Oct 18 2026): fields/samples for Japan (MOE nps_all, MLIT A10 natural parks, Wikidata), Louisiana WMAs,
Switzerland (EEA CDDA designations, geo.admin.ch BAFU layers). Writes data/probe2.json. Never fails."""
import io, json, re, sys, time, urllib.parse, urllib.request, zipfile

UA = {'User-Agent': 'KPC (kentuckyportableclub.github.io) probe'}
OUT = {}


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', '%0A')[:3800]), flush=True)


def get(u, raw=False, timeout=90, n=6000000):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as r:
            b = r.read(n)
            return r.status, (b if raw else b.decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e: return e.code, ''
    except Exception as e: return 0, str(e)[:200]  # noqa: BLE001


def js(u):
    s, t = get(u)
    try: return json.loads(t)
    except Exception: return {'_status': s, '_text': t[:300]}  # noqa: BLE001


def step(name, fn):
    try:
        r = fn(); OUT[name] = r; notice(name, json.dumps(r, ensure_ascii=False)[:3500])
    except Exception as e:  # noqa: BLE001
        OUT[name] = {'error': str(e)}; notice(name + ' ERROR', str(e))


NPS = 'https://services.arcgis.com/wlVTGRSYTzAbjjiC/arcgis/rest/services/nps_all/FeatureServer/0'
def jp_nps():
    i = js(NPS + '?f=json'); f = [x['name'] for x in i.get('fields', [])]
    q = js(NPS + '/query?' + urllib.parse.urlencode({'where': '1=1', 'outFields': '*', 'returnGeometry': 'false', 'resultRecordCount': 6, 'f': 'json'}))
    d = {}
    for fn in f:
        if fn.lower() in ('objectid', 'fid', 'shape__area', 'shape__length'): continue
        r = js(NPS + '/query?' + urllib.parse.urlencode({'where': '1=1', 'outFields': fn, 'returnDistinctValues': 'true', 'returnGeometry': 'false', 'f': 'json'}))
        v = [list(a['attributes'].values())[0] for a in r.get('features', [])]
        d[fn] = [len(v), v[:60]]
    return {'fields': f, 'sample': [a['attributes'] for a in q.get('features', [])], 'distinct': d}


def jp_a10():
    s, page = get('https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A10-v3_1.html')
    links = sorted(set(re.findall(r"[\w./-]*A10-15_\d\d_GML\.zip", page)))
    res = {'status': s, 'links': links[:5], 'n': len(links)}
    if not links:
        res['other'] = sorted(set(re.findall(r"[\w./-]*A10[\w.-]*\.zip", page)))[:20]; return res
    u = urllib.parse.urljoin('https://nlftp.mlit.go.jp/ksj/gml/datalist/', links[30] if len(links) > 30 else links[0])
    s2, z = get(u, raw=True, timeout=180, n=200000000)
    res['zip'] = [u, s2, len(z) if isinstance(z, bytes) else z]
    if not isinstance(z, bytes): return res
    zf = zipfile.ZipFile(io.BytesIO(z)); res['files'] = zf.namelist()[:40]
    try:
        import shapefile  # pyshp
        shp = [n for n in zf.namelist() if n.lower().endswith('.shp')]
        for sp in shp[:3]:
            base = sp[:-4]
            for enc in ('cp932', 'utf-8'):
                try:
                    r = shapefile.Reader(shp=io.BytesIO(zf.read(sp)), dbf=io.BytesIO(zf.read(base + '.dbf')), shx=io.BytesIO(zf.read(base + '.shx')), encoding=enc)
                    res.setdefault('shp', []).append({'file': sp, 'enc': enc, 'fields': [f[0] for f in r.fields[1:]], 'n': len(r),
                                                       'recs': [list(x) for x in r.records()[:12]]})
                    break
                except Exception as e: res.setdefault('shperr', []).append(f'{sp} {enc} {e}')  # noqa: BLE001
    except Exception as e: res['pyshp'] = str(e)  # noqa: BLE001
    gj = [n for n in zf.namelist() if n.lower().endswith(('.geojson', '.json'))]
    if gj:
        t = zf.read(gj[0])[:3000].decode('utf-8', 'replace'); res['geojson_head'] = t
    return res


def jp_wd():
    out = {}
    for name in ('Daisen-Oki National Park', 'Ako Seaside Prefectural Park', 'Minami Alps National Park', 'Kenritsu Kurikoma', 'Hidaka-sanmyaku Erimo-Tokachi National Park'):
        r = js('https://www.wikidata.org/w/api.php?' + urllib.parse.urlencode({'action': 'wbsearchentities', 'search': name, 'language': 'en', 'limit': 5, 'format': 'json'}))
        hits = [h.get('id') for h in r.get('search', [])]
        info = []
        if hits:
            e = js('https://www.wikidata.org/w/api.php?' + urllib.parse.urlencode({'action': 'wbgetentities', 'ids': '|'.join(hits), 'props': 'labels|claims', 'languages': 'en|ja', 'format': 'json'}))
            for q, v in (e.get('entities') or {}).items():
                c = v.get('claims', {})
                p31 = [x['mainsnak'].get('datavalue', {}).get('value', {}).get('id') for x in c.get('P31', [])]
                p17 = [x['mainsnak'].get('datavalue', {}).get('value', {}).get('id') for x in c.get('P17', [])]
                info.append([q, (v.get('labels', {}).get('en') or {}).get('value'), (v.get('labels', {}).get('ja') or {}).get('value'), p31, p17])
        out[name] = info
        time.sleep(.5)
    # SPARQL: what P31 classes Japanese parks use, with counts
    sp = """SELECT ?c ?cl (COUNT(?i) AS ?n) WHERE { ?i wdt:P17 wd:Q17; wdt:P31 ?c. ?c rdfs:label ?cl FILTER(LANG(?cl)='en')
      FILTER(CONTAINS(LCASE(?cl),'park') || CONTAINS(LCASE(?cl),'nature')) } GROUP BY ?c ?cl ORDER BY DESC(?n) LIMIT 40"""
    r = js('https://query.wikidata.org/sparql?' + urllib.parse.urlencode({'query': sp, 'format': 'json'}))
    out['classes'] = [[b['c']['value'].split('/')[-1], b['cl']['value'], b['n']['value']] for b in (r.get('results') or {}).get('bindings', [])] or r
    return out


def la():
    out = {}
    for q in ('LDWF Wildlife Management Areas', 'Louisiana Wildlife Management Areas', 'LDWF WMA', 'Louisiana WMA boundaries'):
        r = js('https://www.arcgis.com/sharing/rest/search?' + urllib.parse.urlencode({'q': q + ' type:"Feature Service"', 'num': 12, 'f': 'json'}))
        out[q] = [[x.get('title'), x.get('owner'), x.get('url'), x.get('access')] for x in r.get('results', [])]
    s, t = get('https://services1.arcgis.com/6euNCaGPCgCzgAVF/arcgis/rest/services?f=json')
    out['org6euN'] = [s, t[:1500]]
    return out


def la_test():
    # try each candidate URL found: layer info + count
    res = {}
    for q, hits in OUT.get('la', {}).items():
        if not isinstance(hits, list): continue
        for h in hits:
            u = h[2]
            if not u or u in res or 'FeatureServer' not in u: continue
            i = js(u.rstrip('/') + '?f=json')
            lays = [(l.get('id'), l.get('name')) for l in i.get('layers', [])]
            first = u.rstrip('/') + ('' if re.search(r'/\d+$', u) else '/' + str(lays[0][0] if lays else 0))
            c = js(first + '/query?where=1%3D1&returnCountOnly=true&f=json')
            f = js(first + '?f=json')
            res[u] = {'owner': h[1], 'layers': lays[:8], 'count': c.get('count'), 'fields': [x['name'] for x in f.get('fields', [])][:30]}
            if len(res) > 10: return res
    return res


EEA = 'https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/CDDA_Dyna_WM/MapServer/4'
def ch_eea():
    f = js(EEA + '?f=json')
    r = js(EEA + '/query?' + urllib.parse.urlencode({'where': "countryCode='CH'", 'outFields': '*', 'returnGeometry': 'false', 'resultRecordCount': 3, 'f': 'json'}))
    d = js(EEA + '/query?' + urllib.parse.urlencode({'where': "countryCode='CH'", 'outFields': 'designationTypeCode', 'returnDistinctValues': 'true', 'returnGeometry': 'false', 'f': 'json'}))
    return {'fields': [x['name'] for x in f.get('fields', [])], 'sample': [a['attributes'] for a in r.get('features', [])],
            'codes': [a['attributes'] for a in d.get('features', [])]}


def ch_admin():
    out = {}
    s, t = get('https://data.geo.admin.ch/api/stac/v0.9/collections?limit=500')
    try: cols = [c['id'] for c in json.loads(t).get('collections', []) if 'bafu' in c['id'] and re.search(r'schutz|inventar|paerke|ramsar|reserv|bln|jagd|wald|natur|smaragd', c['id'])]
    except Exception: cols = [s, t[:300]]  # noqa: BLE001
    out['stac'] = cols
    for c in (cols if isinstance(cols, list) else [])[:25]:
        if not isinstance(c, str): continue
        s, t = get(f'https://data.geo.admin.ch/api/stac/v0.9/collections/{c}/items?limit=3')
        try:
            its = json.loads(t).get('features', [])
            out[c] = [[a.get('href'), a.get('type')] for it in its for a in it.get('assets', {}).values()][:8]
        except Exception: out[c] = [s, t[:200]]  # noqa: BLE001
    for lay in ('ch.bafu.bundesinventare-bln', 'ch.bafu.schutzgebiete-paerke_nationaler_bedeutung_perimeter', 'ch.bafu.schutzgebiete-ramsar'):
        r = js(f'https://api3.geo.admin.ch/rest/services/api/MapServer/{lay}?lang=en')
        out['meta ' + lay] = str(r)[:600]
    return out


step('jp_nps', jp_nps)
try:
    import subprocess; subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'pyshp'], check=False)
except Exception: pass  # noqa: BLE001
step('jp_a10', jp_a10)
step('jp_wd', jp_wd)
step('la', la)
step('la_test', la_test)
step('ch_eea', ch_eea)
step('ch_admin', ch_admin)
json.dump(OUT, open('data/probe2.json', 'w'), ensure_ascii=False, indent=1)
