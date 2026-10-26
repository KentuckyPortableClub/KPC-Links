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


PROV = [('AB', 'AB-|Alberta'), ('BC', 'BC '), ('MB', 'Manitoba'), ('NB', 'NB-|New Brunswic'), ('NS', 'NS-|Nova Scotia'), ('NU', 'NU-'),
        ('ON', 'ON-|Ontario'), ('PE', 'PE-'), ('QC', 'Québec'), ('SK', 'SK-|Saskatchewan'), ('YT', 'Yukon'), ('PC', 'Parks Canada')]


REC = re.compile(r'park|rec|tour|wild|fish|hunt|trail|outdoor|boat|conserv|land|crown|protect|forest|nature|camp|access|amenit|facilit', re.I)
DEEP_GROUPS = {'canada-deep-west': ['CA-BC', 'CA-AB', 'CA-SK', 'CA-MB', 'CA-YT', 'CA-NU', 'CA-PC'],
               'canada-deep-east': ['CA-ON', 'CA-QC', 'CA-NB', 'CA-NS', 'CA-PE']}


def folders(base, depth=2):
    """Oct 25 (Brandon: 'set one of the bots up' for the deeper Canada look): every folder on a server, likely ones first."""
    out, todo = [''], ['']
    for _ in range(depth):
        nxt = []
        for f in todo:
            try: j = get(base + ('/' + f if f else ''), {'f': 'json'})
            except Exception: continue  # noqa: E722
            for g in j.get('folders', []) or []:
                g = g if not f or g.startswith(f + '/') else f + '/' + g
                if g not in out: out.append(g); nxt.append(g)
        todo = nxt
    return sorted(out, key=lambda f: (f != '', not REC.search(f), f))


def canada_targets():
    """Oct 25 (Brandon: 'hit the easy Canada parks'): the provincial / Parks Canada map servers the Canada key already reads."""
    try: L = json.load(open('data/ca-key/layers.json'))
    except Exception: return {}  # noqa: E722
    out = {}
    for label, urls in L.items():
        code = next((c for c, rx in PROV if re.match(rx, label)), None)
        if not code: continue                       # 'cpcad' = the national database, no facilities
        for u in urls: out.setdefault('CA-' + code, []).append({'url': u})
    return out


def main():
    sg = dict(json.load(open('data/state-gis.json'))['states'])
    for k in [k for k in sg if k in ('AB', 'BC', 'MB', 'NB', 'NS', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT')]:
        sg.setdefault('CA-' + k, []).extend(sg.pop(k))   # provinces in state-gis.json share the letters of states (CA = California)
    for k, v in canada_targets().items(): sg.setdefault(k, []).extend(v)
    known = {L['url'].rstrip('/').lower() for L in json.load(open('data/access-layers.json')).get('layers', [])}
    # Oct 25 (Brandon: 'split it up between bots'): one file per state / province in data/access-leads/, and PART picks a
    # share of them, so several runs (the workflow's matrix jobs) can work at the same time without touching each other's files
    D = pathlib.Path('data/access-leads'); D.mkdir(parents=True, exist_ok=True)
    checked = {}
    for f in D.glob('*.json'):
        try: checked[f.stem] = json.load(open(f)).get('checked', '')
        except Exception: pass  # noqa: E722
    us = sorted(s for s in sg if not s.startswith('CA-')); ca = sorted(s for s in sg if s.startswith('CA-'))
    part = (os.environ.get('PART') or '').strip().lower()
    n3 = (len(us) + 2) // 3
    pick = {'us-a': us[:n3], 'us-b': us[n3:2 * n3], 'us-c': us[2 * n3:], 'canada': ca, **DEEP_GROUPS}.get(part, us + ca)
    deep = part.startswith('canada-deep')
    sg = {k: v for k, v in sg.items() if k in pick}
    rest = sorted((s for s in sg if s not in FIRST), key=lambda s: (checked.get(s, ''), s))   # never checked / oldest first
    sts = [s for s in FIRST if s in sg and not checked.get(s)] + rest + [s for s in FIRST if s in sg and checked.get(s)]
    today = time.strftime('%Y-%m-%d')
    leads, seen_svc, log = {}, set(), []
    for st in sts:
        if time.time() - T0 > LIMIT:
            log.append(f'stopped for time before {st}; earlier results kept')
            break
        got = []
        pairs = {roots(e.get('url', '')) for e in sg[st] if e.get('url')}
        first = [(r, '') for r in ROOTS.get(st, [])]
        todo = first + sorted(p for p in pairs if p[0] and p not in first)
        if deep:   # the WHOLE server of each of this province's map addresses, not just the one folder
            bases = list(dict.fromkeys(b for b, _ in todo))
            todo = [(b, f) for b in bases for f in folders(b)]
            todo.sort(key=lambda p: (not REC.search(p[1]), p))
        for base, folder in todo:
            key = (base, folder)
            if key in seen_svc: continue
            seen_svc.add(key)
            try:
                svcs = services(base, folder)
                svcs = sorted(svcs, key=lambda x: not REC.search(x[0]))[:200 if not deep else 400]
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
        if deep:   # keep what the shallow look found before
            try: old = json.load(open(D / f'{st}.json')).get('leads', [])
            except Exception: old = []  # noqa: E722
            have = {x['url'] for x in got}
            got += [x for x in old if x['url'] not in have]
        leads[st] = sorted(got, key=lambda x: (x['known'], -x['count']))
        save_json(D / f'{st}.json', {'st': st, 'checked': today, 'leads': leads[st]}, indent=1)
        log.append(f"{st}: {len(got)} point layers ({sum(1 for x in got if not x['known'])} new)")
    L = [f'# Parking layer leads ({part or "all"})', '', 'From kpc_parking_explorer.py. New = not yet in data/access-layers.json. Review, then add the good ones.', '']
    for st, xs in leads.items():
        new = [x for x in xs if not x['known']]
        if not new: continue
        L += [f'## {st} ({len(new)} new)', '']
        for x in new[:25]:
            L.append(f"- **{x['service']} / {x['layer']}** · {x['count']} points · area field `{x['area']}` · type field `{x['typef']}`  \n  {x['url']}")
        L.append('')
    if leads: save_text(D / f'leads-{part or "all"}.md', '\n'.join(L))
    for l in log[:40]: notice('Parking explorer', l)
    notice('Parking explorer', f"{sum(len(v) for v in leads.values())} point layers in {len(leads)} states, "
                               f"{sum(1 for v in leads.values() for x in v if not x['known'])} not yet used")


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        notice('Parking explorer', f'stopped: {e}')
    sys.exit(0)
