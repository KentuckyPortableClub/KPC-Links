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


def get(u, p=None, t=90):
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
    OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n')
    notice(f'wrote {OUT}: {len(res["layers"])} layers, {len(res["searches"])} searches')


if __name__ == '__main__':
    try: main()
    except Exception as e: notice(f'stopped: {e}')
    sys.exit(0)
