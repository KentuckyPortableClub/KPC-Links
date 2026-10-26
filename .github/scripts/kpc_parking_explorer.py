#!/usr/bin/env python3
"""PARKING LAYER EXPLORER (chat 2, Oct 25 2026; Brandon via HQ: 'visit the official state servers already listed in
data/state-gis.json and list their POINT layers named like parking / trailhead / access / boat ramp / entrance / gate').

For every state server in data/state-gis.json (the agencies' own ArcGIS servers / accounts), this looks in the SAME folder
(and the same ArcGIS Online account) for point layers whose name says parking, trailhead, access point, boat ramp / launch,
entrance, gate or kiosk. Each lead gets its record count, its fields, a guess at the area-name and type fields and three
sample rows. Layers already in data/access-layers.json are marked 'known'.

Writes data/access-leads.json {about, states: {ST: [lead...]}} and data/access-leads.md (for a person to review). Chat 2
then adds the good ones to data/access-layers.json (kpc_us_access.py reads that). Nothing is added automatically.
Empty / thin states first. Time-limited (MINUTES, default 100), never fails (exit 0). Monthly: kpc-parking-explorer.yml."""
import json, os, pathlib, re, sys, time, urllib.parse, urllib.request
from kpc_save import save_json, save_text

UA = {'User-Agent': 'KPC parking layer explorer (kentuckyportableclub.github.io)'}
T0, LIMIT = time.time(), float(os.environ.get('MINUTES') or 100) * 60
FIRST = 'CA KS MS NM SD HI AZ MT UT VA'.split()
# Oct 25 (good bot's 'service roots' list, via HQ): the agencies' own ArcGIS accounts, searched FIRST for these states
ROOTS = {'VA': ['https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/ArcGIS/rest/services', 'https://services5.arcgis.com/lElo6Muu6AKbgOrY/ArcGIS/rest/services'],
         'CA': ['https://services2.arcgis.com/AhxrK3F6WM8ECvDi/ArcGIS/rest/services'],
         'UT': ['https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services', 'https://services.arcgis.com/ZzrwjTRez6FJiOq4/ArcGIS/rest/services'],
         'AZ': ['https://services2.arcgis.com/gdcQ6sUWKP8qwBmV/ArcGIS/rest/services']}
WANT = re.compile(r'park(ing)?\b(?! *(boundar|unit|name|area\b))|trail ?heads?|access (point|site|area)s?\b|boat(ing)? (ramp|access|launch)|'
                  r'\bramps?\b|launch|entrance|\bgates?\b|kiosk|fishing access|water access|put[- ]?in|carry[- ]?in|canoe|kayak', re.I)
NOT = re.compile(r'parcel|boundar|polygon|district|zone|county|census|road|route|lane|centerline|bridge|culvert|dam\b|toilet|'
                 r'restroom|building|tower|well|tank|pipeline|sign(?!.*kiosk)|grazing|allotment|survey|plss|section|township|'
                 r'park(s)? (boundar|polygon|area)|state park(s)?$|parks?$', re.I)
AREAF = re.compile(r'(area|wma|park|property|unit|site|facility|prop|land|loc)_?(name|nm)?$|^(name|sitename|propname|area_name|parkname)$', re.I)
TYPEF = re.compile(r'type|class|categ|use|feat|desc|kind|subtype|fac', re.I)


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', ' ')[:900]), flush=True)


def get(url, params=None, timeout=40):
    u = url + ('?' + urllib.parse.urlencode(params) if params else '')
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as r:
        j = json.loads(r.read().decode('utf-8', 'replace'))
    if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:120])
    return j


def roots(url):
    """(services root, folder) for an ArcGIS layer address; ArcGIS Online accounts are one folder-less root."""
    m = re.match(r'(https?://[^?]+?/rest/services)/(.+?)/(MapServer|FeatureServer)', url, re.I)
    if not m: return None, None
    base, path = m.group(1), m.group(2)
    folder = path.rsplit('/', 1)[0] if '/' in path else ''
    return base, folder


def services(base, folder):
    j = get(base + ('/' + folder if folder else ''), {'f': 'json'})
    out = [(s['name'], s['type']) for s in j.get('services', []) if s.get('type') in ('MapServer', 'FeatureServer')]
    # an ArcGIS Online account lists the same data as both: keep the FeatureServer
    names = {n for n, t in out if t == 'FeatureServer'}
    return [(n, t) for n, t in out if t == 'FeatureServer' or n not in names]


def main():
    sg = json.load(open('data/state-gis.json'))['states']
    known = {L['url'].rstrip('/').lower() for L in json.load(open('data/access-layers.json')).get('layers', [])}
    try: old = json.load(open('data/access-leads.json')).get('states', {})
    except Exception: old = {}  # noqa: E722
    sts = [s for s in FIRST if s in sg] + sorted(s for s in sg if len(s) == 2 and s not in FIRST)
    leads, seen_svc, log = {}, set(), []
    for st in sts:
        if time.time() - T0 > LIMIT:
            log.append(f'stopped for time before {st}; earlier results kept')
            for s in sts[sts.index(st):]:
                if s in old: leads[s] = old[s]
            break
        got = []
        pairs = {roots(e.get('url', '')) for e in sg[st] if e.get('url')}
        first = [(r, '') for r in ROOTS.get(st, [])]
        for base, folder in first + sorted(p for p in pairs if p[0] and p not in first):
            key = (base, folder)
            if key in seen_svc: continue
            seen_svc.add(key)
            try: svcs = services(base, folder)[:200]
            except Exception as e:  # noqa: BLE001
                log.append(f'{st}: {base}/{folder} not listed ({str(e)[:60]})'); continue
            for name, typ in svcs:
                if time.time() - T0 > LIMIT: break
                su = f'{base}/{name}/{typ}'
                try: info = get(su, {'f': 'json'})
                except Exception: continue  # noqa: E722
                for L in info.get('layers', []) or []:
                    lname = L.get('name') or ''
                    full = f'{name} {lname}'
                    if not WANT.search(full) or NOT.search(lname): continue
                    lu = f"{su}/{L.get('id')}"
                    try:
                        li = get(lu, {'f': 'json'})
                        if 'Point' not in str(li.get('geometryType', '')): continue
                        cnt = get(lu + '/query', {'where': '1=1', 'returnCountOnly': 'true', 'f': 'json'}).get('count')
                        flds = [f['name'] for f in li.get('fields', []) if f.get('type') == 'esriFieldTypeString']
                        smp = get(lu + '/query', {'where': '1=1', 'outFields': ','.join(flds[:12]) or '*', 'returnGeometry': 'false',
                                                  'resultRecordCount': 3, 'f': 'json'}).get('features', [])
                    except Exception:  # noqa: BLE001
                        continue
                    if not cnt: continue
                    got.append({'url': lu, 'service': name, 'layer': lname, 'count': cnt,
                                'area': next((f for f in flds if AREAF.search(f)), ''), 'typef': next((f for f in flds if TYPEF.search(f)), ''),
                                'fields': flds[:20], 'sample': [{k: v for k, v in (x.get('attributes') or {}).items() if v not in (None, '')} for x in smp],
                                'known': lu.rstrip('/').lower() in known, 'agency': (info.get('copyrightText') or '')[:80]})
                time.sleep(.2)
        if got: leads[st] = sorted(got, key=lambda x: (x['known'], -x['count']))
        log.append(f"{st}: {len(got)} point layers ({sum(1 for x in got if not x['known'])} new)")
    save_json('data/access-leads.json', {'about': 'Leads for parking / trailhead / access / ramp / entrance point layers on the state servers in '
                                         'state-gis.json (kpc_parking_explorer.py, monthly). A person (chat 2) reviews them and adds the good ones '
                                         'to data/access-layers.json; known = already there.', 'states': leads}, indent=1)
    L = ['# Parking layer leads', '', 'From kpc_parking_explorer.py (monthly). New = not yet in data/access-layers.json. Review, then add the good ones.', '']
    for st, xs in leads.items():
        new = [x for x in xs if not x['known']]
        if not new: continue
        L += [f'## {st} ({len(new)} new)', '']
        for x in new[:25]:
            L.append(f"- **{x['service']} / {x['layer']}** · {x['count']} points · area field `{x['area']}` · type field `{x['typef']}`  \n  {x['url']}")
        L.append('')
    save_text('data/access-leads.md', '\n'.join(L))
    for l in log[:40]: notice('Parking explorer', l)
    notice('Parking explorer', f"{sum(len(v) for v in leads.values())} point layers in {len(leads)} states, "
                               f"{sum(1 for v in leads.values() for x in v if not x['known'])} not yet used")


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        notice('Parking explorer', f'stopped: {e}')
    sys.exit(0)
