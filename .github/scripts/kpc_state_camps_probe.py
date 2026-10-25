#!/usr/bin/env python3
"""Probe for the state camping bot (Brandon Oct 24 2026: 'yes' to build from his US_Camping_and_GIS_Directory.xlsx).

Manual, one-time-ish. For every state but Kentucky it asks, from GitHub's network (the session sandbox cannot reach these):
  1. the statewide GIS portal in data/campstate-sources.json: does it answer a catalog search for 'campground'
     (ArcGIS Hub, CKAN)? what datasets/layers come back?
  2. the agency's own ArcGIS Online account (org ids in data/state-gis.json): any Feature/Map services titled campground,
     cabin, recreation site?
  3. the state's reservation site: does it answer, what is its robots.txt rule for crawlers (so we do not read a site that
     asks us not to)?
Writes data/campstate/probe.json (plain facts, no guessing) and prints ONE summary notice. Never fails the workflow."""
import json, os, pathlib, re, sys, time, urllib.error, urllib.parse, urllib.request
import concurrent.futures as cf

UA = 'KPC-state-camps-probe/1.0 (Kentucky Portable Club; kentuckyportableclub.github.io)'
OUT = pathlib.Path('data/campstate'); OUT.mkdir(parents=True, exist_ok=True)
DEADLINE = time.time() + 25 * 60
STATES = (os.environ.get('STATES') or '').replace(',', ' ').upper().split()
CAMP = re.compile(r'camp|cabin|yurt|lodg|recreation site|rec site|overnight', re.I)


def fetch(url, timeout=25, limit=400000):
    if time.time() > DEADLINE: return {'status': 0, 'err': 'deadline'}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json, text/html;q=0.8, */*;q=0.5'}), timeout=timeout) as r:
            body = r.read(limit).decode('utf-8', 'replace')
            return {'status': r.status, 'final': r.geturl(), 'ctype': r.headers.get('content-type', '')[:50], 'text': body}
    except urllib.error.HTTPError as e:
        return {'status': e.code, 'err': f'HTTP {e.code}'}
    except Exception as e:  # noqa: BLE001
        return {'status': 0, 'err': str(e)[:90]}


def jget(url):
    r = fetch(url)
    try: r['json'] = json.loads(r.get('text') or '')
    except Exception: r['json'] = None  # noqa: E722
    return r


def hub_items(j):
    """Dataset titles + links from an ArcGIS Hub (OGC records or v3) or CKAN answer."""
    out = []
    if not isinstance(j, dict): return out
    for f in (j.get('features') or [])[:25]:                      # Hub search/v1
        p = f.get('properties') or {}
        out.append({'t': p.get('title') or p.get('name'), 'u': p.get('url') or p.get('landingPage') or '', 'k': p.get('type')})
    for d in (j.get('data') or [])[:25]:                          # Hub v3
        a = d.get('attributes') or {}
        out.append({'t': a.get('name') or a.get('title'), 'u': a.get('url') or '', 'k': a.get('type')})
    for d in ((j.get('result') or {}).get('results') or [])[:25]:   # CKAN
        res = [x for x in d.get('resources', []) if x.get('format', '').upper() in ('CSV', 'XLSX', 'GEOJSON', 'JSON', 'ZIP', 'SHP', 'ARCGIS GEOSERVICES REST API')]
        out.append({'t': d.get('title'), 'u': (res[0].get('url') if res else '') or '', 'k': ','.join(sorted({x.get('format', '') for x in d.get('resources', [])}))[:60]})
    return [o for o in out if o.get('t') and CAMP.search(o['t'] + ' ' + (o.get('u') or ''))][:12]


def probe_gis(portal):
    res = {'portal': portal, 'tried': {}}
    if not portal: return res
    p = urllib.parse.urlparse(portal); base = f'{p.scheme}://{p.netloc}'
    for label, path in (('hub_v1', '/api/search/v1/collections/dataset/items?q=campground&limit=25'),
                        ('hub_v3', '/api/v3/datasets?q=campground&page%5Bsize%5D=25'),
                        ('ckan', '/api/3/action/package_search?q=campground&rows=25')):
        r = jget(base + path)
        items = hub_items(r['json']) if r['status'] == 200 else []
        res['tried'][label] = {'status': r['status'], 'err': r.get('err', ''), 'hits': items}
        if items: break
    return res


def org_ids(st):
    ids = set()
    try:
        for l in json.load(open('data/state-gis.json'))['states'].get(st, []):
            m = re.search(r'services\d*\.arcgis\.com/([A-Za-z0-9]{16})/', l.get('url', ''))
            if m: ids.add(m.group(1))
    except Exception: pass  # noqa: E722
    return sorted(ids)


def probe_org(oid):
    q = urllib.parse.urlencode({'q': f'(campground OR cabin OR "recreation sites" OR camping) AND orgid:{oid}', 'num': 25, 'f': 'json'})
    r = jget('https://www.arcgis.com/sharing/rest/search?' + q)
    hits = []
    if r['json']:
        for x in r['json'].get('results', []):
            if x.get('type') in ('Feature Service', 'Map Service', 'Feature Layer', 'Table'):
                hits.append({'t': x.get('title'), 'k': x.get('type'), 'u': x.get('url'), 'owner': x.get('owner')})
    return {'org': oid, 'status': r['status'], 'err': r.get('err', ''), 'hits': hits[:12]}


def robots_rule(text):
    """What robots.txt says to a generic crawler: 'allowed', 'blocked' (Disallow: /) or 'partly' (some paths)."""
    agent_star, dis = False, []
    for line in (text or '').splitlines():
        line = line.split('#')[0].strip()
        if not line: continue
        k, _, v = line.partition(':'); k, v = k.strip().lower(), v.strip()
        if k == 'user-agent': agent_star = v == '*'
        elif k == 'disallow' and agent_star and v: dis.append(v)
    if '/' in dis: return 'blocked'
    return 'partly' if dis else 'allowed'


def probe_reserve(url):
    res = {'url': url}
    if not url: return res
    p = urllib.parse.urlparse(url); base = f'{p.scheme}://{p.netloc}'
    r = fetch(url, limit=60000)
    res.update({'status': r['status'], 'err': r.get('err', ''), 'final': r.get('final', '')[:160]})
    m = re.search(r'<title[^>]*>(.*?)</title>', r.get('text') or '', re.I | re.S)
    res['title'] = re.sub(r'\s+', ' ', m.group(1)).strip()[:90] if m else ''
    rb = fetch(base + '/robots.txt', limit=60000)
    res['robots'] = robots_rule(rb['text']) if rb['status'] == 200 and 'text' in rb and '<html' not in rb['text'][:200].lower() else ('none' if rb['status'] in (404, 410) else f"unknown ({rb['status']})")
    res['vendor'] = 'reserveamerica' if 'reserveamerica.com' in p.netloc else ('goingtocamp' if 'goingtocamp' in p.netloc else '')
    return res


def do_state(st, src):
    return st, {'name': src.get('name'), 'gis': probe_gis(src.get('gis')), 'orgs': [probe_org(o) for o in org_ids(st)],
                'reserve': probe_reserve(src.get('reserve'))}


def main():
    src = json.load(open('data/campstate-sources.json'))['states']
    todo = [s for s in sorted(src) if not STATES or s in STATES]
    out = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for st, r in ex.map(lambda s: do_state(s, src[s]), todo):
            out[st] = r
    (OUT / 'probe.json').write_text(json.dumps({'updated': time.strftime('%Y-%m-%d'), 'states': out}, separators=(',', ':')) + '\n', encoding='utf-8')
    hub = [s for s, r in out.items() if any(t['hits'] for t in r['gis']['tried'].values())]
    answer = [s for s, r in out.items() if any(t['status'] == 200 for t in r['gis']['tried'].values())]
    org = [s for s, r in out.items() if any(o['hits'] for o in r['orgs'])]
    ok = [s for s, r in out.items() if r['reserve'].get('status') == 200]
    blocked = [s for s, r in out.items() if r['reserve'].get('robots') == 'blocked']
    ra = [s for s, r in out.items() if r['reserve'].get('vendor') == 'reserveamerica']
    print('::notice title=State camps probe::' + (f'{len(out)} states. GIS catalog found camp datasets: {" ".join(hub)} | portal answered a catalog search: {len(answer)} | '
          f'agency ArcGIS account has camp services: {" ".join(org)} | reservation site answered: {len(ok)} of {len(out)} (robots blocks all crawlers: {" ".join(blocked) or "none"}) | '
          f'ReserveAmerica sites: {" ".join(ra)}')[:900], flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=State camps probe::stopped early: {type(e).__name__}: {e}')
    sys.exit(0)
