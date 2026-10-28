#!/usr/bin/env python3
"""DATA ADDS PROBE (chat 9, Oct 27 2026; HQ first paste). TEMPORARY: delete with kpc-adds-probe.yml after use.
Chat sessions cannot reach state map servers, so a runner tests each candidate layer ONCE: does it answer, geometry, name
field, record count, samples, licence (service copyright + the ArcGIS Online item's licenceInfo when there is one), dates
(layer edit date, item modified, years in the description), the ownership field + values (rule 14) and the type /
category / manager field + values (so a mixed layer can be told apart). Searches ask ArcGIS Online who publishes a layer
and name the publishing organisation (publisher test). Reads .claude/build/research/ADDS/round5.json, writes
round5-tested.json next to it. Adds nothing to the live data. Never fails."""
import json, os, pathlib, re, sys, time, urllib.parse, urllib.request
UA = {'User-Agent': 'KPC park mapping (kentuckyportableclub.github.io; ham radio club)'}
CAND = pathlib.Path(os.environ.get('CAND') or '.claude/build/research/ADDS/round5.json')
OUT = CAND.with_name(CAND.stem + '-tested.json')
HELD = pathlib.Path('.claude/build/review/state-gis-SE.json')
OWNW = re.compile(r'owner|ownership|owncode|own_|manag|mang|agency|admin|title|tenure', re.I)
TYPW = re.compile(r'type|categ|class|desig|kind|unit_?ty|prop_?ty|status|access', re.I)
NAMEW = re.compile(r'name|nm$|label|title|site|unit|prop', re.I)


def notice(m): print('::notice title=Adds probe::' + str(m).replace('\n', ' ')[:900], flush=True)


def get(u, p=None, t=int(os.environ.get("PROBE_T") or 90)):
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
                'item_owner': j.get('owner'), 'item_org': org, 'item_title': (j.get('title') or '')[:80]}
    except Exception as e: return {'item_err': str(e)[:80]}


def distinct(lu, f, n=40):
    q = get(lu + '/query', {'where': '1=1', 'outFields': f, 'returnGeometry': 'false', 'returnDistinctValues': 'true', 'resultRecordCount': n}, t=120)
    return sorted({str((ft.get('attributes') or {}).get(f))[:40] for ft in q.get('features') or [] if (ft.get('attributes') or {}).get(f) not in (None, '')})[:30]


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
    with urllib.request.urlopen(urllib.request.Request(x['url'], headers=UA), timeout=60) as r:
        raw = r.read(); out['status'] = r.status; out['ctype'] = r.headers.get('Content-Type', '')
    out['bytes'] = len(raw)
    if x.get('json'):
        j = json.loads(raw.decode('utf-8', 'replace'))
        out['results'] = [{'title': p.get('title'), 'org': (p.get('organization') or {}).get('title'), 'licence': p.get('license_title'),
                           'modified': p.get('metadata_modified', '')[:10],
                           'links': [(rs.get('format'), rs.get('url')) for rs in p.get('resources') or [] if re.search(r'rest|zip|geojson|shp|kml', str(rs.get('url')) + str(rs.get('format')), re.I)][:6]}
                          for p in (j.get('result') or {}).get('results') or []][:40]
        return out
    if 'pdf' in out['ctype']: return out
    txt = ' '.join(re.sub(r'<script.*?</script>|<style.*?</style>|<[^>]+>', ' ', raw.decode('utf-8', 'replace'), flags=re.S | re.I).split())
    out['links'] = sorted(set(re.findall(r'https?://[^"\'\s<>]*(?:MapServer|FeatureServer|\.zip|\.kmz|\.geojson|arcgis\.com/[^"\'\s<>]*)', raw.decode('utf-8', 'replace'))))[:30]
    if x.get('look'):
        out['hits'] = [txt[max(0, m.start() - 150): m.end() + 150] for m in re.finditer(x['look'], txt, re.I)][:12]
    return out


def namequery(cfg):
    """BL18/19: how many unmatched western BLM park names are found in the BLM layers once POTA's suffix words are stripped."""
    P = cfg.get('namequery_parks') or {}
    names = []
    for st in P.get('states', []):
        try: pk = json.load(open(f'data/us-key/US-{st}.json'))['parks']
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
            q = get(x['url'] + '/query', {'where': x['where'], 'outFields': x.get('out', '*'), 'returnGeometry': 'false', 'resultRecordCount': 20}, t=60)
            r['rows'] = [{k: v for k, v in (f.get('attributes') or {}).items() if v not in (None, '') and not re.search(r'shape|globalid', k, re.I)} for f in q.get('features') or []][:20]
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


def main():
    cfg = json.load(open(CAND))
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
    if cfg.get('queries'): res['queries'] = queries(cfg)
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
