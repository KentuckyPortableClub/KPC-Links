#!/usr/bin/env python3
"""LINK HARVESTER (chat 2, Oct 26 2026; Brandon via HQ 'BOTS FOR THE GAPS'): official park pages + official map links,
pulled from sources that are official by nature, into data/parkinfo-web.json (never over a hand-checked value).

  1. The outline layers the answer keys already read (data/us-key/layers.json): many agency layers carry a website /
     URL / link field for each area. One query per 100 joined areas, attributes only.
  2. The National Park Service API (secret NPS_API_KEY): each NPS unit's official page; its map page
     nps.gov/<code>/planyourvisit/maps.htm is added only when it answers.
  3. Recreation.gov RIDB recreation areas (secret RIDB_API_KEY): the agency's own links (Forest Service, Corps, BLM…),
     matched by name and within 40 km of the POTA pin.

A bot value is written as {'web' or 'map': url, 'by': 'bot: <source>'}; a value a person filled in (no 'by', or not a
bot) is never changed. Data only (hidden until used). Monthly, time-limited, never fails. Keys are never printed."""
import json, math, os, pathlib, re, sys, time, urllib.error, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from kpc_save import save_json

T0, LIMIT = time.time(), float(os.environ.get('MINUTES') or 150) * 60
UA = {'User-Agent': 'KPC park links (kentuckyportableclub.github.io)'}
NPS_KEY = (os.environ.get('NPS_API_KEY') or '').strip()
RIDB_KEY = (os.environ.get('RIDB_API_KEY') or '').strip()
WEB = pathlib.Path('data/parkinfo-web.json')
LOG = []


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', ' ')[:900]), flush=True)
def late(): return time.time() - T0 > LIMIT
def low(x): return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', str(x or '').lower().replace('&', ' and ')).split())
KINDW = re.compile(r'\b(national|state|park|parks|forest|wildlife|management|area|refuge|recreation|recreational|historic|historical|site|preserve|'
                   r'natural|nature|monument|memorial|scenic|and|the|of|lake|project|recreation area|nwr|sp|wma|unit|corps|engineers|blm|usfs)\b')
def core(x): return ' '.join(KINDW.sub(' ', low(x)).split())


def get(url, params=None, headers=None, timeout=60, raw=False):
    u = url + ('?' + urllib.parse.urlencode(params) if params else '')
    req = urllib.request.Request(u, headers=dict(UA, **(headers or {})))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
        return b if raw else json.loads(b.decode('utf-8', 'replace'))


def alive(url):
    try:
        req = urllib.request.Request(url, headers=UA, method='GET')
        with urllib.request.urlopen(req, timeout=30) as r: return r.status < 400
    except Exception: return False  # noqa: BLE001


def km(a, b, c, d):
    r = math.radians
    return 6371 * 2 * math.asin(math.sqrt(math.sin(r(c - a) / 2) ** 2 + math.cos(r(a)) * math.cos(r(c)) * math.sin(r(d - b) / 2) ** 2))


def parks():
    P = {}
    for f in pathlib.Path('data/parkinfo').glob('US-*.json'):
        for r, v in json.load(open(f))['parks'].items(): P[r] = v
    try:
        for r, v in json.load(open('data/parkinfo/CA.json'))['parks'].items(): P[r] = v
    except Exception: pass  # noqa: BLE001
    return P


URLF = re.compile(r'web|url|link|site|page|href|info', re.I)
NOTF = re.compile(r'photo|image|img|thumb|icon|logo|shape|globalid|editor', re.I)


def from_layers(P, found):
    L = json.load(open('data/us-key/layers.json'))
    want = {}
    for f in pathlib.Path('data/us-key').glob('US-*.json'):
        for ref, p in json.load(open(f))['parks'].items():
            for x in p.get('m') or []:
                m = re.fullmatch(r'([a-z]+)(\d+)', str(x[0]))
                if m and m.group(1) in L:
                    want.setdefault(m.group(1), {}).setdefault(int(m.group(2)), set()).add(ref)
    n = 0
    for pre, ids in sorted(want.items()):
        if late(): LOG.append('layers: stopped for time'); break
        url = L[pre][0]
        oids = sorted(ids)
        for k in range(0, len(oids), 100):
            try:
                j = get(url, {'objectIds': ','.join(map(str, oids[k:k + 100])), 'outFields': '*', 'returnGeometry': 'false', 'f': 'json'})
            except Exception as e:  # noqa: BLE001
                LOG.append(f'{pre}: not read ({str(e)[:60]})'); break
            if j.get('error'): LOG.append(f"{pre}: {str(j['error'])[:80]}"); break
            oidf = j.get('objectIdFieldName') or 'OBJECTID'
            for ft in j.get('features') or []:
                a = ft.get('attributes') or {}
                o = a.get(oidf) if a.get(oidf) is not None else a.get('OBJECTID') or a.get('objectid')
                for fld, v in a.items():
                    if not isinstance(v, str) or not re.match(r'https?://', v.strip()) or NOTF.search(fld) or not URLF.search(fld): continue
                    v = v.strip().split()[0]
                    kind = 'map' if re.search(r'map|brochure', fld + ' ' + v, re.I) else 'web'
                    for ref in ids.get(int(o) if o is not None else -1, []):
                        found.setdefault(ref, {}).setdefault(kind, (v, f"bot: {L[pre][2][:60]} ({fld} field)")); n += 1
            time.sleep(.3)
    return n


def from_nps(P, found):
    if not NPS_KEY: LOG.append('NPS_API_KEY not set'); return 0
    units, start = [], 0
    while not late():
        try: j = get('https://developer.nps.gov/api/v1/parks', {'limit': 200, 'start': start, 'fields': 'url'}, headers={'X-Api-Key': NPS_KEY})
        except Exception as e:  # noqa: BLE001
            LOG.append(f'NPS API: {str(e)[:80]}'); break
        d = j.get('data') or []
        units += d; start += len(d)
        if not d or start >= int(j.get('total') or 0): break
    by = {}
    for u in units: by.setdefault(core(u.get('fullName')), []).append(u)
    n = 0
    for ref, v in P.items():
        if late(): break
        if not ref.startswith('US-') or 'national' not in low(v[2]) and 'nps' not in low(v[2]): continue
        cand = by.get(core(v[0]), [])
        cand = [u for u in cand if v[5] is None or not u.get('latitude') or km(v[5], v[6], float(u['latitude']), float(u['longitude'])) < 150]
        if len(cand) != 1: continue
        u = cand[0]
        if u.get('url'): found.setdefault(ref, {}).setdefault('web', (u['url'], 'bot: National Park Service API'))
        mp = f"https://www.nps.gov/{u.get('parkCode')}/planyourvisit/maps.htm"
        if u.get('parkCode') and alive(mp): found.setdefault(ref, {}).setdefault('map', (mp, 'bot: National Park Service (maps page answered)')); n += 1
        time.sleep(.2)
    return n


def from_ridb(P, found):
    if not RIDB_KEY: LOG.append('RIDB_API_KEY not set'); return 0
    areas, off = [], 0
    while not late():
        try: j = get('https://ridb.recreation.gov/api/v1/recareas', {'limit': 50, 'offset': off, 'full': 'true'}, headers={'apikey': RIDB_KEY})
        except Exception as e:  # noqa: BLE001
            LOG.append(f'RIDB: {str(e)[:80]}'); break
        R = j.get('RECDATA') or []
        areas += R; off += len(R)
        if not R or off >= int((j.get('METADATA') or {}).get('RESULTS', {}).get('TOTAL_COUNT', 0)): break
        time.sleep(.25)
    by = {}
    for a in areas: by.setdefault(core(a.get('RecAreaName')), []).append(a)
    n = 0
    for ref, v in P.items():
        if not ref.startswith('US-') or v[5] is None: continue
        for a in by.get(core(v[0]), []):
            try: la, lo = float(a.get('RecAreaLatitude') or 0), float(a.get('RecAreaLongitude') or 0)
            except Exception: continue  # noqa: BLE001
            if not la or km(v[5], v[6], la, lo) > 40: continue
            for l in a.get('LINK') or []:
                u = str(l.get('URL') or '').strip(); t = str(l.get('Title') or '') + ' ' + str(l.get('LinkType') or '')
                if not re.match(r'https?://', u) or not re.search(r'\.(gov|mil|us)(/|$)', urllib.parse.urlparse(u).netloc + '/'): continue
                kind = 'map' if re.search(r'\bmaps?\b|brochure', t + ' ' + u, re.I) else 'web'
                found.setdefault(ref, {}).setdefault(kind, (u, 'bot: Recreation.gov RIDB (agency link)')); n += 1
            break
    return n


def main():
    P = parks()
    found = {}
    counts = {'layers': from_layers(P, found), 'nps': from_nps(P, found), 'ridb': from_ridb(P, found)}
    d = json.load(open(WEB)) if WEB.exists() else {'about': '', 'parks': {}}
    added = {'web': 0, 'map': 0}
    for ref, kinds in found.items():
        e = d['parks'].setdefault(ref, {})
        for kind, (url, by) in kinds.items():
            if kind == 'web' and P.get(ref) and P[ref][1]: continue          # the park already has its page
            if e.get(kind) and not str(e.get(kind + '_by', '')).startswith('bot:'): continue   # a person's value wins
            if e.get(kind) != url: added[kind] += 1
            e[kind] = url; e[kind + '_by'] = by
        if not e: d['parks'].pop(ref, None)
    if 'link harvester' not in d.get('about', ''):
        d['about'] += " Oct 26: the LINK HARVESTER (kpc_link_harvest.py, monthly) adds 'web' / 'map' from official sources with '<kind>_by': 'bot: …'; a value without a bot tag was filled by a person and is never changed."
    save_json(WEB, d, indent=1)
    notice('Link harvester', f"found {json.dumps(counts)}; new or changed: {added['web']} pages, {added['map']} maps")
    for l in LOG[:8]: notice('Link harvester note', l)


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        notice('Link harvester', f'stopped: {e}')
    sys.exit(0)
