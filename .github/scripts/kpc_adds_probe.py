#!/usr/bin/env python3
"""DATA ADDS PROBE (chat 9, Oct 27 2026; HQ first paste). TEMPORARY: delete with kpc-adds-probe.yml after use.
Chat sessions cannot reach state map servers, so a runner tests each candidate layer ONCE: does it answer, geometry, name
field, record count, samples, licence (service copyright + the ArcGIS Online item's licenceInfo when there is one), dates
(layer edit date, item modified, years in the description), the ownership field + values (rule 14) and the type /
category / manager field + values (so a mixed layer can be told apart). Searches ask ArcGIS Online who publishes a layer
and name the publishing organisation (publisher test). Reads .claude/build/research/ADDS/round5.json, writes
round5-tested.json next to it. Adds nothing to the live data. Never fails."""
import json, os, pathlib, re, sys, time, urllib.parse, urllib.request, urllib.error
UA = {'User-Agent': 'KPC park mapping (kentuckyportableclub.github.io; ham radio club)'}
CAND = pathlib.Path(os.environ.get('CAND') or '.claude/build/research/ADDS/round5.json')
OUT = CAND.with_name(CAND.stem + '-tested.json')
HELD = pathlib.Path('.claude/build/review/state-gis-SE.json')
OWNW = re.compile(r'owner|ownership|owncode|own_|manag|mang|agency|admin|title|tenure', re.I)
TYPW = re.compile(r'type|categ|class|desig|kind|unit_?ty|prop_?ty|status|access', re.I)
NAMEW = re.compile(r'name|nm$|label|title|site|unit|prop', re.I)


def notice(m): print('::notice title=Adds probe::' + str(m).replace('\n', ' ')[:900], flush=True)


_LAST = {}


def get(u, p=None, t=int(os.environ.get("PROBE_T") or 90)):
    h = urllib.parse.urlparse(u).netloc   # Oct 29: kpc_manners pace, 1 request / 2 s per host
    w = 2.0 - (time.time() - _LAST.get(h, 0))
    if w > 0: time.sleep(w)
    _LAST[h] = time.time()
    q = dict(p or {}); q.setdefault('f', 'json')
    err = None
    for i in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(u + ('&' if '?' in u else '?') + urllib.parse.urlencode(q), headers=UA), timeout=t) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:140])
            return j
        except Exception as e: err = e; time.sleep(3)
    raise err


def day(ms):
    try: return time.strftime('%Y-%m-%d', time.gmtime(int(ms) / 1000))
    except Exception: return ''


def item(iid):
    try:
        j = get(f'https://www.arcgis.com/sharing/rest/content/items/{iid}')
        org = ''
        if j.get('orgId'):
            try: org = (get(f"https://www.arcgis.com/sharing/rest/portals/{j['orgId']}").get('name') or '')[:60]
            except Exception: pass
        return {'item_licence': re.sub(r'<[^>]+>', ' ', j.get('licenseInfo') or '').strip()[:300], 'item_modified': day(j.get('modified')),
                'item_owner': j.get('owner'), 'item_org': org, 'item_title': (j.get('title') or '')[:80],
                'item_credits': re.sub(r'<[^>]+>', ' ', j.get('accessInformation') or '').strip()[:300],
                'item_about': ' '.join(re.sub(r'<[^>]+>', ' ', (j.get('description') or '') + ' ' + (j.get('snippet') or '')).split())[:600]}
    except Exception as e: return {'item_err': str(e)[:80]}


def distinct(lu, f, n=40):
    q = get(lu + '/query', {'where': '1=1', 'outFields': f, 'returnGeometry': 'false', 'returnDistinctValues': 'true', 'resultRecordCount': n}, t=120)
    return sorted({str((ft.get('attributes') or {}).get(f))[:40] for ft in q.get('features') or [] if (ft.get('attributes') or {}).get(f) not in (None, '')})[:max(30, n if n > 40 else 30)]


def layer(x):
    out = {k: x[k] for k in ('st', 'kind', 'ag', 'url', 'note') if k in x}
    j = get(x['url'])
    out['answers'] = True
    out['service'] = (j.get('name') or j.get('mapName') or (j.get('documentInfo') or {}).get('Title') or '')[:70]
    out['licence'] = re.sub(r'<[^>]+>', ' ', str(j.get('copyrightText') or (j.get('documentInfo') or {}).get('Copyright') or '')).strip()[:300]
    desc = re.sub(r'<[^>]+>', ' ', str(j.get('serviceDescription') or j.get('description') or ''))
    out['years_in_text'] = sorted(set(re.findall(r'\b(?:19|20)\d{2}\b', desc[:6000])))[-4:]
    out['description'] = ' '.join(desc.split())[:400]
    if j.get('serviceItemId'): out.update(item(j['serviceItemId']))
    else:   # Oct 28: agency servers keep their item terms at <service>/info/iteminfo (Nevada State Parks' licence was there)
        try:
            svc = re.sub(r'/\d+/?$', '', x['url'].rstrip('/'))
            ii = get(svc + '/info/iteminfo')
            out['item_licence'] = re.sub(r'<[^>]+>', ' ', ii.get('licenseInfo') or '').strip()[:300]
            out['item_credits'] = re.sub(r'<[^>]+>', ' ', ii.get('accessInformation') or '').strip()[:300]
            out['item_about'] = ' '.join(re.sub(r'<[^>]+>', ' ', (ii.get('description') or '') + ' ' + (ii.get('snippet') or '')).split())[:500]
        except Exception: pass
    lays = j.get('layers')
    if lays is None and 'geometryType' in j: lays = [{'id': None}]
    if not lays and re.search(r'(Map|Feature)Server/?$', x['url']):      # round 6: MARIS roots list no layers: ask /layers, then ids 0-12
        try: lays = [{'id': l.get('id'), 'name': l.get('name')} for l in get(x['url'].rstrip('/') + '/layers').get('layers') or []]
        except Exception: lays = []
        if not lays:
            for i in range(13):
                try: d0 = get(f"{x['url'].rstrip('/')}/{i}", t=40); lays.append({'id': i, 'name': d0.get('name')})
                except Exception: pass
        out['found_ids'] = [f"{l.get('id')}:{l.get('name')}" for l in lays]
    if x.get('only'): lays = [l for l in lays or [] if l.get('id') is None or re.search(x['only'], str(l.get('name')), re.I)]
    rows = []
    for L in (lays or [])[:14]:
        if L.get('subLayerIds'): continue
        lu = x['url'].rstrip('/') if L.get('id') is None else f"{x['url'].rstrip('/')}/{L['id']}"
        try: d = j if L.get('id') is None else get(lu)
        except Exception as e: rows.append({'id': L.get('id'), 'error': str(e)[:70]}); continue
        flds = [f['name'] for f in d.get('fields') or []]
        strs = [f['name'] for f in d.get('fields') or [] if f.get('type') == 'esriFieldTypeString']
        nm = x.get('nm') or next((f for f in strs if NAMEW.search(f) and not re.search(r'own|mang|manag|agency|type|county|url|link', f, re.I)), '')
        own = next((f for f in strs if OWNW.search(f)), '')
        typ = next((f for f in strs if TYPW.search(f) and f != own), '')
        ed = (d.get('editingInfo') or {})
        row = {'id': L.get('id'), 'name': (d.get('name') or '')[:60], 'geom': (d.get('geometryType') or '').replace('esriGeometry', ''),
               'nameField': nm, 'ownerField': own, 'typeField': typ, 'fields': flds[:40],
               'last_edit': day(ed.get('lastEditDate') or ed.get('dataLastEditDate') or 0), 'layer_copyright': re.sub(r'<[^>]+>', ' ', str(d.get('copyrightText') or '')).strip()[:200]}
        if d.get('serviceItemId') and 'item_licence' not in out: out.update(item(d['serviceItemId']))
        try: row['records'] = get(lu + '/query', {'where': '1=1', 'returnCountOnly': 'true'}, t=150).get('count')
        except Exception as e: row['countErr'] = str(e)[:60]
        if nm:
            try:
                q = get(lu + '/query', {'where': '1=1', 'outFields': nm, 'returnGeometry': 'false', 'resultRecordCount': 8}, t=120)
                row['sample'] = [str((ft.get('attributes') or {}).get(nm))[:40] for ft in q.get('features') or []][:8]
            except Exception as e: row['sampleErr'] = str(e)[:60]
        for f, k in ((own, 'owner_values'), (typ, 'type_values')):
            if f:
                try: row[k] = distinct(lu, f)
                except Exception as e: row[k + 'Err'] = str(e)[:60]
        rows.append(row)
        time.sleep(.5)
    out['layers'] = rows
    return out


def search(x):
    out = {k: x[k] for k in ('st', 'q', 'why') if k in x}
    j = get('https://www.arcgis.com/sharing/rest/search', {'q': x['q'] + ' AND (type:"Feature Service" OR type:"Map Service")', 'num': 30, 'sortField': 'numviews', 'sortOrder': 'desc'})
    rows, orgs = [], {}
    for it in j.get('results') or []:
        oid = it.get('orgId') or ''
        if oid and oid not in orgs:
            try: orgs[oid] = (get(f'https://www.arcgis.com/sharing/rest/portals/{oid}').get('name') or '')[:60]
            except Exception: orgs[oid] = ''
        rows.append({'title': (it.get('title') or '')[:80], 'org': orgs.get(oid, ''), 'owner': it.get('owner'), 'url': (it.get('url') or '')[:170],
                     'modified': day(it.get('modified')), 'licence': re.sub(r'<[^>]+>', ' ', it.get('licenseInfo') or '').strip()[:120]})
    out['found'] = rows[:25]
    return out


def org(x):
    """List every service on a server / ArcGIS account; with walk, also the folders; keep names that match."""
    out = {k: x[k] for k in ('st', 'url', 'note') if k in x}
    j = get(x['url'])
    names = [f"{s.get('name')} ({s.get('type')})" for s in j.get('services') or []]
    for f in (j.get('folders') or [])[:25]:
        try: names += [f"{s.get('name')} ({s.get('type')})" for s in get(f"{x['url']}/{f}").get('services') or []]
        except Exception: pass
    out['folders'] = (j.get('folders') or [])[:40]
    out['n_services'] = len(names)
    out['matching'] = [n for n in names if re.search(x.get('match') or '.', n, re.I)][:80]
    return out


def hub(x):
    """Find a hub dataset's service URL (dataset id, hub page or search), or list a hub's datasets."""
    out = {k: x[k] for k in ('st', 'q', 'note', 'dataset') if k in x}
    if x.get('items'):
        j = get(x['items'])
        feats = j.get('features') or []
        out['datasets'] = [{'title': (f.get('properties') or {}).get('title'), 'type': (f.get('properties') or {}).get('type'),
                            'url': (f.get('properties') or {}).get('url'), 'licence': re.sub(r'<[^>]+>', ' ', str((f.get('properties') or {}).get('licenseInfo') or ''))[:100],
                            'modified': (f.get('properties') or {}).get('modified')} for f in feats][:100]
        return out
    ids = []
    d = x.get('dataset') or ''
    m = re.search(r'([0-9a-f]{32})', d)
    if m: ids.append(m.group(1))
    if not ids and x.get('q'):
        s = get('https://www.arcgis.com/sharing/rest/search', {'q': f'title:"{x["q"]}"', 'num': 10})
        ids = [it['id'] for it in s.get('results') or []][:5]
        out['search_hits'] = [f"{it.get('title')} [{it.get('owner')}] {it.get('type')} {it.get('url') or ''}"[:200] for it in s.get('results') or []][:10]
    out['items'] = []
    for i in ids[:5]:
        it = item(i)
        try:
            j = get(f'https://www.arcgis.com/sharing/rest/content/items/{i}')
            it['url'] = j.get('url'); it['type'] = j.get('type')
        except Exception as e: it['err'] = str(e)[:80]
        out['items'].append(it)
    # a service found this way gets the normal layer read
    for it in out['items']:
        if it.get('url') and re.search(r'(Feature|Map)Server', str(it['url'])):
            try: it['layer_read'] = layer({'st': x['st'], 'url': it['url'], 'kind': '?'})
            except Exception as e: it['layer_err'] = str(e)[:100]
    return out


def page(x):
    out = {k: x[k] for k in ('st', 'url', 'note') if k in x}
    try:
        with urllib.request.urlopen(urllib.request.Request(x['url'], headers=UA), timeout=60) as r:
            raw = r.read(); out['status'] = r.status; out['ctype'] = r.headers.get('Content-Type', '')
            out['final_url'] = r.geturl()   # Oct 28: a short map link resolves to the agency's pinned coordinate
    except urllib.error.HTTPError as e:   # Oct 29: keep the server's own error text (NL CKAN 400)
        out['error'] = f'HTTP {e.code}'; out['body'] = e.read()[:400].decode('utf-8', 'replace'); return out
    out['bytes'] = len(raw)
    if x.get('json'):
        j = json.loads(raw.decode('utf-8', 'replace'))
        out['results'] = [{'title': p.get('title'), 'org': (p.get('organization') or {}).get('title'), 'licence': p.get('license_title'),
                           'modified': p.get('metadata_modified', '')[:10],
                           'links': [(rs.get('format'), rs.get('url')) for rs in p.get('resources') or [] if re.search(r'rest|zip|geojson|shp|kml', str(rs.get('url')) + str(rs.get('format')), re.I)][:6]}
                          for p in (j.get('result') or {}).get('results') or []][:40]
        return out
    if 'pdf' in out['ctype']: return out
    txt = raw.decode('utf-8', 'replace') if x.get('raw') else ' '.join(re.sub(r'<script.*?</script>|<style.*?</style>|<[^>]+>', ' ', raw.decode('utf-8', 'replace'), flags=re.S | re.I).split())
    out['links'] = sorted(set(re.findall(r'https?://[^"\'\s<>]*(?:MapServer|FeatureServer|\.zip|\.kmz|\.geojson|arcgis\.com/[^"\'\s<>]*)', raw.decode('utf-8', 'replace'))))[:30]
    if x.get('look'):
        out['hits'] = ([m.group(0)[:200] for m in re.finditer(x['look'], txt, re.I)][:80] if x.get('raw') else [txt[max(0, m.start() - 150): m.end() + 150] for m in re.finditer(x['look'], txt, re.I)][:12])
    return out


def namequery(cfg):
    """BL18/19: how many unmatched western BLM park names are found in the BLM layers once POTA's suffix words are stripped."""
    P = cfg.get('namequery_parks') or {}
    names = []
    for st in P.get('states', []):
        try: pk = json.load(open(f'data/us-key/US-{st}.json'))['parks']
        except Exception:   # Oct 29: the keys moved to KPC-Data
            try: pk = get(f'https://raw.githubusercontent.com/KentuckyPortableClub/KPC-Data/main/data/us-key/US-{st}.json')['parks']
            except Exception: continue
        for r, v in pk.items():
            if not v.get('m') and re.search(P['type'], v.get('t', '')):
                core = ' '.join(re.sub(P['strip'], ' ', v.get('n', ''), flags=re.I).split())
                if core: names.append((st, r, v.get('n'), core))
    res = []
    for x in cfg.get('namequery') or []:
        out = {k: x[k] for k in ('st', 'url', 'note')}
        try:
            meta = get(x['url'])
            flds = x.get('fields') or [f['name'] for f in meta.get('fields') or [] if f.get('type') == 'esriFieldTypeString' and re.search(r'name|nm', f['name'], re.I)][:3]
            out['fields'] = flds; out['geom'] = meta.get('geometryType'); hits = []
            for st, r, full, core in names:
                w = ' OR '.join(f"UPPER({f}) LIKE '%{core.upper().replace(chr(39), chr(39) * 2)}%'" for f in flds)
                try:
                    q = get(x['url'] + '/query', {'where': w, 'outFields': ','.join(flds), 'returnGeometry': 'false', 'resultRecordCount': 3}, t=60)
                    f0 = q.get('features') or []
                    if f0: hits.append([st, r, full, [list((a.get('attributes') or {}).values())[:2] for a in f0[:2]]])
                except Exception: pass
                time.sleep(.15)
            out['tried'] = len(names); out['found'] = len(hits); out['hits'] = hits
        except Exception as e: out['error'] = str(e)[:120]
        res.append(out)
        notice(f"namequery {x['url'][-50:]}: {out.get('found')} of {out.get('tried')}")
    return res


def queries(cfg):
    out = []
    for x in cfg.get('queries') or []:
        r = {k: x[k] for k in ('st', 'url', 'where', 'note') if k in x}
        try:
            q = get(x['url'] + '/query', {'where': x['where'], 'outFields': x.get('out', '*'), 'returnGeometry': 'true' if x.get('geom') else 'false', 'outSR': 4326, 'resultRecordCount': x.get('n', 20)}, t=60)
            r['rows'] = []
            for f in (q.get('features') or [])[:x.get('n', 20)]:
                row = {k: v for k, v in (f.get('attributes') or {}).items() if v not in (None, '') and not re.search(r'shape|globalid', k, re.I)}
                g = f.get('geometry') or {}
                if x.get('geom') and 'x' in g: row['_pt'] = [round(g['y'], 6), round(g['x'], 6)]   # Oct 28: a point's own lat/lon
                r['rows'].append(row)
        except Exception as e: r['error'] = str(e)[:140]
        out.append(r)
    return out


def browse(cfg):
    """Rows 31-33: open other people's map sites in a real browser, observe only (title + where the page gets its data). Copies nothing."""
    out = []
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e: return [{'error': f'no playwright: {e}'}]
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for x in cfg.get('browse') or []:
            r = {k: x[k] for k in ('st', 'url', 'note') if k in x}; reqs = []
            try:
                pg = b.new_page(user_agent=UA['User-Agent'])
                pg.on('request', lambda q: reqs.append(q.url) if q.resource_type in ('xhr', 'fetch') else None)
                pg.goto(x['url'], timeout=60000); pg.wait_for_timeout(int(x.get('wait', 8000)))
                r['title'] = pg.title()[:120]
                r['data_requests'] = sorted({re.sub(r'\?.*$', '', u)[:160] for u in reqs})[:60]
                r['text_hits'] = [m for m in re.findall(r'[^.\n]{0,80}(?:outline|boundar|polygon|licen|copyright|source)[^.\n]{0,80}', pg.inner_text('body')[:20000], re.I)][:10]
                pg.close()
            except Exception as e: r['error'] = str(e)[:160]
            out.append(r)
        b.close()
    return out


NRHP = 'https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/1'
NRF = 'RESNAME,State,STATUS,ResType,Is_NHL,MAP_METHOD,SRC_SCALE,SRC_ACCU,BND_TYPE,EDIT_DATE,NRIS_Refnum'
TYPEW = set('state national historic historical site sites park parks battlefield memorial monument area preservation heritage the of and at'.split())


def _words(s): return {w for w in re.sub(r'[^a-z0-9 ]', ' ', str(s).lower().replace("'", '')).split() if len(w) > 2 and w not in TYPEW}


def _acres(rings, la):
    import math
    kx, ky = 111320 * math.cos(math.radians(la)), 110570
    tot = 0.0
    for r in rings:
        a = sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1)) / 2
        tot += a
    return round(abs(tot) * kx * ky / 4046.86, 1)


def _inside(la, lo, rings):
    c = False
    for r in rings:
        for i in range(len(r) - 1):
            (x1, y1), (x2, y2) = r[i][:2], r[i + 1][:2]
            if (y1 > la) != (y2 > la) and lo < (x2 - x1) * (la - y1) / ((y2 - y1) or 1e-12) + x1: c = not c
    return c


def nrhp(cfg):
    """Oct 28 (HQ, chat 8's KPC_HistoricSites_desk.md): National Register polygons vs POTA historic sites. Read only."""
    X = cfg['nrhp']; out = {'tests': [], 'count': {}}
    pins = {r[1]: (r[3], r[4], r[2]) for r in json.load(open('locations.json')) if r[0] == 'POTA' and r[3] is not None}
    def q(where=None, la=None, lo=None):
        p = {'outFields': NRF, 'returnGeometry': 'true', 'outSR': 4326, 'f': 'json'}
        if where: p['where'] = where
        else: p.update({'geometry': f'{lo},{la}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects', 'where': '1=1'})
        return get(NRHP + '/query', p, t=90).get('features') or []
    for x in X.get('tests') or []:
        r = dict(x); la, lo, nm = pins.get(x['ref'], (None, None, ''))
        try:
            fs = q(where=f"RESNAME LIKE '%{x['word']}%' AND State = '{x['state']}'")
            r['found'] = [{**{k: v for k, v in (f.get('attributes') or {}).items() if v not in (None, '')},
                           'acres': _acres((f.get('geometry') or {}).get('rings') or [], la or 37), 'pin_inside': bool(la) and _inside(la, lo, (f.get('geometry') or {}).get('rings') or [])} for f in fs][:8]
        except Exception as e: r['error'] = str(e)[:140]
        out['tests'].append(r); time.sleep(.5)
    for ref in X.get('pin_tests') or []:
        la, lo, nm = pins.get(ref, (None, None, ''))
        r = {'ref': ref, 'park': nm}
        try:
            fs = q(la=la, lo=lo) if la is not None else []
            r['found'] = [{**{k: v for k, v in (f.get('attributes') or {}).items() if v not in (None, '')}, 'acres': _acres((f.get('geometry') or {}).get('rings') or [], la)} for f in fs][:6]
        except Exception as e: r['error'] = str(e)[:140]
        out['tests'].append(r); time.sleep(.5)
    rx = re.compile(X['types'], re.I)
    parks = []
    import glob
    for f in sorted(glob.glob('data/us-key/US-*.json')):
        for ref, p in json.load(open(f))['parks'].items():
            if not p.get('m') and rx.search(p.get('t') or '') and ref in pins: parks.append((ref, p.get('n'), p.get('t'), f[-7:-5]))
    C = {'checked': 0, 'polygon_holds_pin': 0, 'same_name': 0, 'sure_by_rule': 0, 'nps_units': 0, 'removed': 0, 'errors': 0}
    rows = []
    for ref, n, ty, st in parks:
        la, lo, _ = pins[ref]; C['checked'] += 1
        nps = bool(re.search(r'^national|national (historic(al)? (site|park)|battlefield|memorial|monument)', ty or '', re.I))
        try: fs = q(la=la, lo=lo)
        except Exception: C['errors'] += 1; continue
        fs = [f for f in fs if (f.get('geometry') or {}).get('rings')]
        live = [f for f in fs if 'remov' not in str((f.get('attributes') or {}).get('STATUS', '')).lower()]
        C['removed'] += len(fs) - len(live)
        if not live: time.sleep(.3); continue
        C['polygon_holds_pin'] += 1
        pw = _words(n); best = None
        for f in live:
            a = f.get('attributes') or {}; rw = _words(a.get('RESNAME'))
            same = bool(pw) and pw <= rw
            cand = {'ref': ref, 'park': n, 'type': ty, 'st': st, 'resname': a.get('RESNAME'), 'status': a.get('STATUS'), 'nhl': a.get('Is_NHL'),
                    'map_method': a.get('MAP_METHOD'), 'bnd_type': a.get('BND_TYPE'), 'acres': _acres(f['geometry']['rings'], la), 'same_name': same, 'nps_unit': nps}
            if same and (best is None or not best['same_name']): best = cand
            elif best is None: best = cand
        if best['same_name']:
            C['same_name'] += 1
            if nps: C['nps_units'] += 1
            else: C['sure_by_rule'] += 1
        rows.append(best); time.sleep(.3)
    out['count'] = C
    out['note'] = ("size check: POTA gives no park area, so 'size within ~20%' needs the park's published acres: polygon acres are shown for "
                   "chat 8 to compare. sure_by_rule = pin inside + same name, not an NPS unit (NPS boundary first); size still to confirm.")
    out['rows'] = sorted(rows, key=lambda r: (not r['same_name'], r['nps_unit'], r['st']))
    return out


def pointq(cfg):
    """Oct 28: which polygons hold (or lie within dist m of) given points, on every polygon layer of the given services."""
    out = []
    for x in cfg.get('pointq') or []:
        r = {k: x[k] for k in ('st', 'url', 'note') if k in x}; r['hits'] = []
        try:
            u = x['url'].rstrip('/')
            lays = [u] if re.search(r'/\d+$', u) else [f"{u}/{l['id']}" for l in (get(u).get('layers') or []) if not l.get('subLayerIds')]
            for lu in lays[:20]:
                try:
                    m = get(lu)
                    if 'Polygon' not in str(m.get('geometryType')):   # Oct 29 (chat 2): say so; WY's layer 0 was skipped without a word
                        r['hits'].append({'layer': f"{lu.rsplit('/', 1)[-1]} {m.get('name')}", 'skipped': f"not a polygon layer ({m.get('geometryType') or m.get('type') or m.get('error') or 'no geometry'})"}); continue
                    for la, lo in x['points']:
                        q = get(lu + '/query', {'geometry': f'{lo},{la}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                                                'distance': x.get('dist', 0), 'units': 'esriSRUnit_Meter', 'where': '1=1', 'outFields': '*', 'returnGeometry': 'false'}, t=90)
                        time.sleep(2)   # kpc_manners: 1 request per 2 s per host
                        if not (q.get('features') or []): r['hits'].append({'layer': f"{lu.rsplit('/', 1)[-1]} {m.get('name')}", 'point': [la, lo], 'nohit': True})
                        for f in (q.get('features') or [])[:10]:
                            r['hits'].append({'layer': f"{lu.rsplit('/', 1)[-1]} {m.get('name')}", 'point': [la, lo],
                                              'attrs': {k: v for k, v in (f.get('attributes') or {}).items() if v not in (None, '', ' ') and not re.search(r'shape|globalid|objectid', k, re.I)}})
                except Exception as e: r['hits'].append({'layer': lu, 'error': str(e)[:100]})
        except Exception as e: r['error'] = str(e)[:140]
        out.append(r)
    return out


def _hit(url, la, lo):
    """Point query two ways (plain 'x,y' and JSON geometry with its spatial reference); returns (hits, how)."""
    out = {}
    for how, g in (('plain', f'{lo},{la}'), ('json', json.dumps({'x': lo, 'y': la, 'spatialReference': {'wkid': 4326}}))):
        try:
            q = get(url + '/query', {'geometry': g, 'geometryType': 'esriGeometryPoint', 'inSR': 4326, 'outSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                                     'where': '1=1', 'outFields': '*', 'returnGeometry': 'false'}, t=90)
            out[how] = [{k: v for k, v in (f.get('attributes') or {}).items() if v not in (None, '', ' ') and re.search(r'own|int|status|tract|name|unit|facil|type|lands|prop', k, re.I)} for f in q.get('features') or []][:4]
        except Exception as e: out[how] = 'error ' + str(e)[:80]
        time.sleep(2)
    return out


def _inside(la, lo, rings):
    c = False
    for r in rings:
        for i in range(len(r) - 1):
            (x1, y1), (x2, y2) = r[i][:2], r[i + 1][:2]
            if (y1 > la) != (y2 > la) and lo < (x2 - x1) * (la - y1) / ((y2 - y1) or 1e-12) + x1: c = not c
    return c


def _interior(rings):
    """a point surely inside the polygon: the ring's vertex average if inside, else the first inside point of a 25 x 25 grid"""
    if not rings: return None
    r = max(rings, key=len)
    xs = [v[0] for v in r]; ys = [v[1] for v in r]
    c = (round(sum(ys) / len(ys), 6), round(sum(xs) / len(xs), 6))
    if _inside(c[0], c[1], rings): return c
    for i in range(1, 25):
        for j in range(1, 25):
            la = min(ys) + (max(ys) - min(ys)) * i / 25; lo = min(xs) + (max(xs) - min(xs)) * j / 25
            if _inside(la, lo, rings): return (round(la, 6), round(lo, 6))
    return None


NHD = 'https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer'


def rivertest(cfg):
    """Oct 28 (chat 8's regrade): CONTROL point first (dry owned land: must HIT, else the query is wrong), then river points taken
    from the USGS NHD flowline of the named river INSIDE the unit's own boundary polygon (never picked by hand)."""
    res = []
    for x in cfg.get('rivertest') or []:
        r = {'test': x['note'], 'layer': x['layer'], 'control': None, 'water': [], 'notes': []}
        if x.get('control'):
            la, lo = x['control']; r['control'] = {'point': [la, lo], 'result': _hit(x['layer'], la, lo)}
        if x.get('control_auto'):   # Oct 29 (v3): the control comes from INSIDE one of the layer's own polygons, never by hand
            try:
                c = x['control_auto']
                q = get(c.get('url', x['layer']) + '/query', {'where': c['where'], 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326, 'resultRecordCount': 3}, t=120)
                pt = None
                for f in q.get('features') or []:
                    pt = _interior((f.get('geometry') or {}).get('rings') or [])
                    if pt: r['control_from'] = {k: v for k, v in (f.get('attributes') or {}).items() if v not in (None, '') and re.search(r'name|tract|unit|int|own|status', k, re.I)}; break
                if pt: r['control'] = {'point': list(pt), 'auto': True, 'result': _hit(x['layer'], *pt)}
                else: r['notes'].append(f"control_auto: no polygon ({len(q.get('features') or [])} records)")
            except Exception as e: r['notes'].append('control_auto: ' + str(e)[:100])
        pts = [tuple(p) for p in x.get('points') or []]
        if x.get('unit'):
            try:
                u = x['unit']
                q = get(u['url'] + '/query', {'where': u['where'], 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326, 'resultRecordCount': 5}, t=120)
                rings = [rg for f in q.get('features') or [] for rg in (f.get('geometry') or {}).get('rings') or []]
                xs = [p[0] for rg in rings for p in rg]; ys = [p[1] for rg in rings for p in rg]
                r['notes'].append(f"unit polygon: {len(q.get('features') or [])} records, {len(rings)} rings")
                if rings and x.get('river'):
                    env = f'{min(xs)},{min(ys)},{max(xs)},{max(ys)}'
                    got = []
                    for lid in (6, 5, 4, 3, 2):
                        try:
                            fq = get(f'{NHD}/{lid}/query', {'where': f"GNIS_NAME = '{x['river']}'", 'geometry': env, 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
                                                         'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'GNIS_NAME', 'returnGeometry': 'true', 'outSR': 4326, 'resultRecordCount': 50}, t=120)
                            for f in fq.get('features') or []:
                                for path in (f.get('geometry') or {}).get('paths') or []:
                                    for v in path[::max(1, len(path) // 6)]: got.append((round(v[1], 6), round(v[0], 6)))
                            if got: r['notes'].append(f'NHD layer {lid}: {len(got)} river vertices'); break
                        except Exception as e: r['notes'].append(f'NHD {lid}: {str(e)[:60]}')
                        time.sleep(2)
                    ins = [p for p in got if _inside(p[0], p[1], rings)]
                    r['notes'].append(f'{len(ins)} river vertices inside the unit polygon')
                    k = x.get('npts', 3); step = max(1, len(ins) // k)
                    pts += ins[::step][:k]
            except Exception as e: r['notes'].append('unit: ' + str(e)[:100])
        for la, lo in pts[:x.get('npts', 3) + 1]:
            r['water'].append({'point': [la, lo], 'result': _hit(x['layer'], la, lo)})
        res.append(r)
        notice('river test ' + x['note'][:40] + ': control ' + ('HIT' if r['control'] and any(v for v in r['control']['result'].values() if isinstance(v, list)) else 'NO HIT/none'))
    return res


PINRX = [r'@(-?\d{1,2}\.\d{3,}),(-?\d{1,3}\.\d{3,})', r'!3d(-?\d{1,2}\.\d{3,})!4d(-?\d{1,3}\.\d{3,})',
         r'[?&](?:q|ll|daddr|destination|center|query)=(-?\d{1,2}\.\d{3,})(?:,|%2C)\s*(-?\d{1,3}\.\d{3,})',
         r'lat(?:itude)?["\']?\s*[:=]\s*["\']?(-?\d{1,2}\.\d{3,})["\']?\s*,\s*["\']?(?:lng|lon|longitude)["\']?\s*[:=]\s*["\']?(-?\d{1,3}\.\d{3,})',
         r'(3[6-9]\.\d{4,})\s*[,/ ]\s*(-8[1-9]\.\d{4,})']


def _pins(txt):
    out = []
    for rx in PINRX:
        for a, b in re.findall(rx, txt, re.I):
            v = [round(float(a), 6), round(float(b), 6)]
            if 30 < v[0] < 45 and -95 < v[1] < -75 and v not in out: out.append(v)
    return out[:12]


def pinhunt(cfg):
    """Oct 29 (KY camp points): open each page in a real browser, read every lat/lon it carries (map links, embedded maps,
    'latitude' text), resolve short Google-Maps links, and follow links whose text matches one of the camp names (one level).
    Observe only; copies nothing but the coordinates and where each came from."""
    out = []
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e: return [{'error': f'no playwright: {e}'}]
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(user_agent=UA['User-Agent'])

        def read(url, wait=6000):
            r = {'url': url}
            pg = ctx.new_page()
            try:
                pg.goto(url, timeout=60000); pg.wait_for_timeout(wait)
                r['final'] = pg.url[:200]; r['title'] = pg.title()[:120]
                html = pg.content()
                links = pg.eval_on_selector_all('a[href]', 'e => e.map(a => [a.innerText.trim().slice(0,80), a.href])')
                frames = [f.url for f in pg.frames if f.url and f.url != pg.url]
                txt = html + ' ' + ' '.join(h for _, h in links) + ' ' + ' '.join(frames)
                r['pins'] = _pins(txt + ' ' + pg.url)
                r['maplinks'] = sorted({h for _, h in links if re.search(r'maps\.app\.goo\.gl|goo\.gl/maps|google\.[a-z.]+/maps|maps\.google', h)})[:10]
                r['frames'] = [f[:200] for f in frames if re.search(r'map', f, re.I)][:5]
                body = pg.inner_text('body')[:30000]
                r['text_hits'] = re.findall(r'[^\n]{0,60}(?:latitude|longitude|GPS|coordinates|directions)[^\n]{0,100}', body, re.I)[:6]
                r['_links'] = links
            except Exception as e: r['error'] = str(e)[:160]
            pg.close()
            return r

        for x in cfg.get('pinhunt') or []:
            r = read(x['url'], x.get('wait', 6000))
            links = r.pop('_links', None) or []
            for m in list(r.get('maplinks') or [])[:6]:
                if 'goo.gl' in m:
                    q = read(m, 4000); q.pop('_links', None)
                    r.setdefault('resolved', []).append({'link': m, 'final': q.get('final'), 'pins': q.get('pins'), 'error': q.get('error')})
            names = x.get('names') or []
            if names:
                r['follow'] = []
                seen = set()
                for t, h in links:
                    hit = next((n for n in names if n.lower() in (t + ' ' + h.replace('-', ' ')).lower()), None)
                    if not hit or h in seen or h.split('#')[0] == x['url']: continue
                    seen.add(h)
                    if len(seen) > 30: break
                    q = read(h, 5000); q.pop('_links', None)
                    for m in list(q.get('maplinks') or [])[:3]:
                        if 'goo.gl' in m:
                            z = read(m, 4000); z.pop('_links', None)
                            q.setdefault('resolved', []).append({'link': m, 'final': z.get('final'), 'pins': z.get('pins')})
                    r['follow'].append({'name': hit, 'text': t, **q})
            r.update({k: x[k] for k in ('id', 'note') if k in x})
            notice(f"pin {x.get('id', '')}: {len(r.get('pins') or [])} pins, {len(r.get('follow') or [])} followed {r.get('error', '')}")
            out.append(r)
        b.close()
    return out


def nearq(cfg):
    """Oct 29 (chat 8 river / BOR rows): what each layer holds within a small box around a point (lines never contain a point)."""
    out = []
    for x in cfg.get('nearq') or []:
        for la, lo, label in x['points']:
            d = x.get('d', 0.01)
            r = {'url': x['url'], 'at': label, 'pt': [la, lo]}
            try:
                q = get(x['url'] + '/query', {'geometry': f'{lo-d},{la-d},{lo+d},{la+d}', 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
                                             'spatialRel': 'esriSpatialRelIntersects', 'where': '1=1', 'outFields': x.get('out', '*'),
                                             'returnGeometry': 'false', 'resultRecordCount': 8, 'f': 'json'}, t=90)
                if q.get('error'): r['error'] = str(q['error'])[:160]
                r['rows'] = [{k: v for k, v in (f.get('attributes') or {}).items() if v not in (None, '') and not re.search(r'shape|globalid|objectid', k, re.I)}
                             for f in (q.get('features') or [])][:8]
            except Exception as e: r['error'] = str(e)[:160]
            out.append(r)
            time.sleep(1)
    return out


def zipnames(cfg):
    """Oct 29 (chat 8 Source Book 2): download an agency ZIP (shapefile), list its files, read the .dbf fields, record count and the names."""
    import io, zipfile, struct
    out = []
    for x in cfg.get('zipnames') or []:
        r = {'url': x['url'], 'note': x.get('note')}
        try:
            with urllib.request.urlopen(urllib.request.Request(x['url'], headers=UA), timeout=120) as f: raw = f.read(60_000_000)
            r['bytes'] = len(raw)
            z = zipfile.ZipFile(io.BytesIO(raw)); r['files'] = z.namelist()[:30]
            dbf = next((n for n in z.namelist() if n.lower().endswith('.dbf')), None)
            if dbf:
                b = z.read(dbf); n, hl, rl = struct.unpack('<IHH', b[4:12])
                fields, off = [], 32
                while b[off] != 0x0D:
                    fields.append((b[off:off + 11].split(b'\0')[0].decode('latin-1'), b[off + 16])); off += 32
                r['records'] = n; r['fields'] = [f for f, _ in fields]
                nf = next((f for f, _ in fields if re.search(x.get('name', r'name|nm$|label|title'), f, re.I)), None)
                names = []
                if nf:
                    pos = 1 + sum(l for f, l in fields[:[f for f, _ in fields].index(nf)]); ln = dict(fields)[nf]
                    for i in range(min(n, 400)):
                        rec = b[hl + i * rl: hl + (i + 1) * rl]
                        names.append(rec[pos:pos + ln].decode('latin-1').strip())
                r['nameField'] = nf; r['names'] = names
            prj = next((n for n in z.namelist() if n.lower().endswith('.prj')), None)
            if prj: r['prj'] = z.read(prj)[:160].decode('latin-1')
        except Exception as e: r['error'] = str(e)[:160]
        out.append(r)
        notice(f"zip {x['url'][-50:]}: {r.get('records')} records, name field {r.get('nameField')} {r.get('error', '')}")
    return out


STN = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
       'FL': 'Florida', 'GA': 'Georgia', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana',
       'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana',
       'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina',
       'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
       'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
       'WI': 'Wisconsin', 'WY': 'Wyoming'}


def lakehunt(cfg):
    """Oct 29 (HQ 11:18 AM, Brandon 11:17): for every US park whose park IS a lake, look for the managing DEPARTMENT's own
    boundary / property polygon at the park's pin: (1) the state department layers we already know (data/state-gis.json),
    (2) up to 3 new department layers per state from an ArcGIS search (fishing lakes / wildlife areas / property).
    Per hit: layer, the polygon's name, its acres, and the USGS lake polygon's acres at the pin, so 'includes shore land'
    = polygon acres clearly bigger than the lake. ArcGIS REST only; read only; never fails."""
    L = cfg['lakehunt']
    sg = json.load(open('data/state-gis.json'))['states']
    out = {'parks': [], 'layers': {}}
    by = {}
    for r in L['parks']: by.setdefault(r[0], []).append(r)
    for st, rows in sorted(by.items()):
        lays = [{'url': l['url'], 'nm': l.get('nm') or '', 'from': 'state-gis (known)', 'ag': l.get('ag', '')} for l in sg.get(st, [])
                if l.get('kind') in ('park', 'wild', 'land', 'preserve', 'forest') and re.search(r'/\d+$', l['url'])][:5]
        try:
            j = get('https://www.arcgis.com/sharing/rest/search', {'q': f'({STN.get(st, st)}) AND ("fishing lake" OR "fishing lakes" OR "state lakes" OR "public fishing" OR "wildlife area" OR "wildlife management area" OR "department lands" OR "property boundaries") AND (type:"Feature Service" OR type:"Map Service")', 'num': 12, 'sortField': 'numviews', 'sortOrder': 'desc'})
            for it in (j.get('results') or [])[:12]:
                u = (it.get('url') or '').rstrip('/')
                if not u or any(u in x['url'] for x in lays): continue
                try:
                    m = get(u)
                    for l in (m.get('layers') or [])[:6]:
                        if 'olygon' in str(l.get('geometryType') or '') or not l.get('geometryType'):
                            lays.append({'url': f"{u}/{l['id']}", 'nm': '', 'from': f"search: {it.get('title', '')[:60]} (owner {it.get('owner')})",
                                         'licence': re.sub(r'<[^>]+>', ' ', it.get('licenseInfo') or '').strip()[:120]})
                except Exception: pass
                if sum(1 for x in lays if x['from'].startswith('search')) >= 3: break
        except Exception as e: out['layers'][st + ' search error'] = str(e)[:100]
        lays = lays[:7]
        out['layers'][st] = lays
        for st_, ref, name, la, lo in rows:
            r = {'st': st, 'ref': ref, 'n': name, 'pin': [la, lo], 'hits': []}
            if la is None: r['note'] = 'no pin'; out['parks'].append(r); continue
            try:
                q = get(f'{NHD}/12/query', {'geometry': f'{lo},{la}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                                            'distance': 150, 'units': 'esriSRUnit_Meter', 'where': '1=1', 'outFields': 'GNIS_NAME,AREASQKM', 'returnGeometry': 'false'}, t=60)
                w = [(f['attributes'].get('GNIS_NAME') or f['attributes'].get('gnis_name'), f['attributes'].get('AREASQKM') or f['attributes'].get('areasqkm')) for f in q.get('features') or []]
                w = [x for x in w if x[1]]
                if w: big = max(w, key=lambda x: x[1] or 0); r['lake'] = {'name': big[0], 'acres': round(float(big[1]) * 247.105, 1)}
            except Exception as e: r['lake_error'] = str(e)[:60]
            for l in lays:
                try:
                    q = get(l['url'] + '/query', {'geometry': f'{lo},{la}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                                                  'distance': 150, 'units': 'esriSRUnit_Meter', 'where': '1=1', 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326,
                                                  'maxAllowableOffset': 0.0005, 'resultRecordCount': 3}, t=60)
                    for f in (q.get('features') or [])[:3]:
                        a = f.get('attributes') or {}
                        nm = a.get(l['nm']) if l['nm'] else next((v for k, v in a.items() if isinstance(v, str) and re.search(r'name|label|unit|area|site|prop', k, re.I) and len(v) > 3), '')
                        rings = (f.get('geometry') or {}).get('rings') or []
                        ac = _acres(rings, la) if rings else None
                        r['hits'].append({'layer': l['url'], 'from': l['from'], 'name': str(nm)[:80], 'acres': ac,
                                          'shore': (None if not ac or not r.get('lake') else ac > 1.15 * r['lake']['acres'])})
                except Exception as e: r['hits'].append({'layer': l['url'], 'error': str(e)[:60]})
            out['parks'].append(r)
        notice(f"lakehunt {st}: {len(rows)} parks, {len(lays)} layers, {sum(1 for p in out['parks'] if p['st'] == st and any(h.get('name') is not None and not h.get('error') for h in p['hits']))} with a department polygon at the pin")
        try: OUT.with_name(OUT.stem + '-partial.json').write_text(json.dumps(out, ensure_ascii=False) + '\n')   # Oct 29: a save after every state, so a timeout loses at most one state
        except Exception: pass
    return out


def main():
    cfg = json.load(open(CAND))
    notice('commit ' + os.popen('git rev-parse --short HEAD').read().strip() + ' round ' + str(CAND))
    held = {}
    try:
        for st, v in json.load(open(HELD))['states'].items():
            held.setdefault(st, [l for l in v if l.get('read')])
    except Exception: pass
    todo = []
    for x in cfg.get('layers') or []:
        if str(x['url']).startswith('HELD:'):
            for l in held.get(x['url'][5:], []): todo.append({**x, 'url': l['url'], 'nm': l.get('nm') or ''})
        else: todo.append(x)
    res = {'about': cfg.get('about', ''), 'date': time.strftime('%Y-%m-%d'), 'layers': [], 'searches': []}
    for x in todo:
        try: r = layer(x)
        except Exception as e: r = {k: x.get(k) for k in ('st', 'kind', 'url')}; r['answers'] = False; r['error'] = str(e)[:140]
        res['layers'].append(r)
        b = next((l for l in r.get('layers') or [] if l.get('records')), {})
        notice(f"{r['st']} {r.get('kind', '')} {r['url'][-60:]}: " + (f"OK {b.get('records')} {b.get('geom')}, name={b.get('nameField')}, lic={(r.get('item_licence') or r.get('licence') or 'NONE')[:50]}"
               if r.get('answers') else 'NO ANSWER ' + r.get('error', '')))
    for x in cfg.get('searches') or []:
        try: r = search(x)
        except Exception as e: r = dict(x); r['error'] = str(e)[:140]
        res['searches'].append(r)
    for key, fn in (('orgs', org), ('hubs', hub), ('pages', page)):
        res[key] = []
        for x in cfg.get(key) or []:
            try: r = fn(x)
            except Exception as e: r = dict(x); r['error'] = str(e)[:140]
            res[key].append(r)
            notice(f"{key} {x.get('st')} {x.get('note', '')[:40]}: " + (r.get('error') or 'ok'))
    if cfg.get('nrhp'):
        try: res['nrhp'] = nrhp(cfg)
        except Exception as e: res['nrhp'] = {'error': str(e)[:200]}
        notice('NRHP: ' + json.dumps((res['nrhp'] or {}).get('count') or res['nrhp'].get('error'))[:500])
    if cfg.get('queries'): res['queries'] = queries(cfg)
    if cfg.get('pointq'): res['pointq'] = pointq(cfg)
    if cfg.get('rivertest'): res['rivertest'] = rivertest(cfg)
    if cfg.get('nearq'):
        try: res['nearq'] = nearq(cfg)
        except Exception as e: res['nearq'] = [{'error': str(e)[:140]}]
    if cfg.get('distinct'):   # Oct 29 (chat 8 v3 grade): what unit codes / names a layer really holds
        res['distinct'] = []
        for x in cfg['distinct']:
            r = {'url': x['url'], 'values': {}}
            for f in x['fields']:
                try: r['values'][f] = distinct(x['url'], f, x.get('n', 2000))
                except Exception as e: r['values'][f] = 'error ' + str(e)[:80]
                time.sleep(2)
            res['distinct'].append(r)
    if cfg.get('lakehunt'):
        try: res['lakehunt'] = lakehunt(cfg)
        except Exception as e: res['lakehunt'] = {'error': str(e)[:140]}
    if cfg.get('zipnames'):
        try: res['zipnames'] = zipnames(cfg)
        except Exception as e: res['zipnames'] = [{'error': str(e)[:140]}]
    if cfg.get('pinhunt'):
        try: res['pinhunt'] = pinhunt(cfg)
        except Exception as e: res['pinhunt'] = [{'error': str(e)[:140]}]
    if cfg.get('browse'):
        try: res['browse'] = browse(cfg)
        except Exception as e: res['browse'] = [{'error': str(e)[:140]}]
    if cfg.get('namequery'):
        try: res['namequery'] = namequery(cfg)
        except Exception as e: res['namequery'] = [{'error': str(e)[:140]}]
    OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n')
    notice(f'wrote {OUT}: {len(res["layers"])} layers, {len(res["searches"])} searches')


if __name__ == '__main__':
    try: main()
    except Exception as e: notice(f'stopped: {e}')
    sys.exit(0)
