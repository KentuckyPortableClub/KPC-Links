#!/usr/bin/env python3
"""Pre-find official website and official map links for parks and candidates that have none on file
(Brandon Nov 8 2:49 PM CST, t753u/t754u: "search 1st and our program dont fine done offer them the search button").

  python3 .github/scripts/kpc_official_find.py KY            -> data/official-links/KY.json

Sources, in order (each link records its source and a confidence):
  1. our own files: data/ky-lands-seen.json (agency pages for KY lands), data/ky-official-maps.json, data/parkinfo-web.json
     (names matched after normalizing WMA / Wildlife Management Area, St. / State, punctuation);
  2. agency SITEMAPS only (listed in each site's robots.txt): a page whose URL slug carries the park's name words.
     robots.txt is read first with the honest KPC User-Agent; a disallowed path or an unreadable robots.txt = the source is skipped.
     60 s between requests to the same host (hub-portal crawl delay). Never: services*.arcgis.com, ncnhde.natureserve.org,
     maps.gov.bc.ca, services.arcgis.com/33TOOklri9xpic7U. Wikidata is NOT used: its robots.txt disallows /w/ and /sparql.
Nothing is guessed: a link is saved only when it is in our files or listed in the agency's own sitemap.
"""
import gzip, json, pathlib, re, sys, time, urllib.request, urllib.robotparser, urllib.parse, datetime as dt

UA = 'KPC-map-link-check/1.0 (+https://kentuckyportableclub.github.io/KPC-Links/)'
BANNED = re.compile(r'(^|\.)services\d*\.arcgis\.com$|^ncnhde\.natureserve\.org$|^maps\.gov\.bc\.ca$', re.I)
DELAY = 60
SITEMAPS = {   # state -> [(host, sitemap url, path filter, designation words the page fits)]
    'KY': [('parks.ky.gov', 'https://parks.ky.gov/sitemap/sitemap-index.xml', r'/(explore|parks?)/', r'state (park|historic site|resort)'),
           ('eec.ky.gov', 'https://eec.ky.gov/sitemap.xml', r'/Nature-Preserves/', r'nature preserve|natural area'),
           ('www.fws.gov', 'https://www.fws.gov/sitemap.xml', r'/refuge/', r'national wildlife refuge|nwr')],
}
STOP = {'the', 'of', 'and', 'at', 'a', 'state', 'park', 'parks', 'wildlife', 'management', 'area', 'wma', 'national', 'historic', 'site',
        'nature', 'preserve', 'natural', 'refuge', 'nwr', 'resort', 'recreation', 'forest', 'lake', 'dam', 'shrine', 'memorial'}


def norm(n):
    n = str(n or '').lower().replace('&', ' and ')
    n = re.sub(r'\bwma\b', 'wildlife management area', n)
    n = re.sub(r'\bst\.?\s', 'state ', n)
    n = re.sub(r"[.'’\"]", '', n)
    return re.sub(r'[^a-z0-9]+', ' ', n).strip()


def core(n):
    return [w for w in norm(n).split() if w not in STOP and len(w) > 1]


_last, _robots = {}, {}
def allowed(url):
    h = urllib.parse.urlsplit(url).hostname or ''
    if BANNED.search(h) or '33TOOklri9xpic7U' in url: return False
    if h not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            rp.parse(fetch(f'https://{h}/robots.txt', check=False).splitlines()); _robots[h] = rp
        except Exception as e:  # noqa: BLE001
            print(f'::warning title=robots::{h}: robots.txt unreadable ({e}); source skipped'); _robots[h] = None
    rp = _robots[h]
    return bool(rp and rp.can_fetch(UA, url))


def fetch(url, check=True):
    h = urllib.parse.urlsplit(url).hostname or ''
    if check and not allowed(url): raise PermissionError('robots.txt disallows ' + url)
    wait = DELAY - (time.time() - _last.get(h, 0))
    if h in _last and wait > 0: time.sleep(wait)
    _last[h] = time.time()
    b = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60).read()
    if url.endswith('.gz') or b[:2] == b'\x1f\x8b': b = gzip.decompress(b)
    return b.decode('utf-8', 'replace')


def sitemap_urls(url, depth=0, cap=6):
    try: t = fetch(url)
    except Exception as e:  # noqa: BLE001
        print(f'::warning title=sitemap::{url}: {str(e)[:120]}'); return []
    locs = re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', t)
    if '<sitemapindex' in t and depth < 2:
        out = []
        for u in locs[:cap]: out += sitemap_urls(u, depth + 1, cap)
        return out
    return locs


def match_url(name, urls):
    c = set(core(name))
    if not c: return None, None
    best = None
    for u in urls:
        slug = set(core(urllib.parse.unquote(urllib.parse.urlsplit(u).path).replace('/', ' ').replace('-', ' ').replace('_', ' ')))
        if c <= slug:
            extra = len(slug - c)
            if best is None or extra < best[1]: best = (u, extra)
    if not best: return None, None
    return best[0], ('high' if best[1] <= 2 else 'medium')


def own_files(state):
    out = {}
    if state == 'KY':
        for f, get in (('data/ky-lands-seen.json', lambda d: [(n, u, None, 'ky-lands-seen (' + a + ')') for a, v in d.get('lists', {}).items() for n, u in v.items()]),
                       ('data/ky-official-maps.json', lambda d: [(n, v.get('page'), (v.get('maps') or [[None, None]])[0][1], 'ky-official-maps') for n, v in d.get('items', {}).items()])):
            p = pathlib.Path(f)
            if p.exists():
                for n, page, mp, src in get(json.loads(p.read_text(encoding='utf-8'))):
                    page = page if re.match(r'https?://', str(page or '')) else None   # some lands-file rows are a label, not a link
                    mp = mp if re.match(r'https?://', str(mp or '')) else None
                    if page or mp: out.setdefault(norm(n), {'name': n, 'site': page, 'map': mp, 'src': src})
    return out


def candidates(state):
    p = pathlib.Path(f'data/{state.lower()}-answer-key.json')
    web = json.loads(pathlib.Path('data/parkinfo-web.json').read_text(encoding='utf-8')).get('parks', {}) if pathlib.Path('data/parkinfo-web.json').exists() else {}
    rows = []
    if p.exists():
        for ref, k in json.loads(p.read_text(encoding='utf-8')).get('parks', {}).items():
            w = web.get(ref) or {}
            rows.append({'ref': ref, 'name': k.get('n', ''), 'web': w.get('web'), 'map': w.get('map')})
    return rows


def main(state):
    state = state.upper()
    own = own_files(state)
    rows = candidates(state)
    need = [r for r in rows if not r['web'] or not r['map']]
    srcs, pages = [], {}
    for host, sm, pf, des in SITEMAPS.get(state, []):
        ok = allowed(sm)
        st = {'host': host, 'sitemap': sm, 'robots': 'allowed' if ok else 'disallowed or unreadable: skipped', 'urls': 0}
        if ok:
            urls = [u for u in sitemap_urls(sm) if re.search(pf, u, re.I)]
            pages[host] = (urls, des); st['urls'] = len(urls)
        srcs.append(st); print(f'::notice title=Source::{host}: {st["robots"]}, {st["urls"]} pages in the sitemap')
    out, found = {}, 0
    for r in need:
        e = {'ref': r['ref'], 'name': r['name']}
        o = own.get(norm(r['name']))
        if o and o.get('site') and not r['web']: e.update(site=o['site'], site_src=o['src'], site_conf='high')
        if o and o.get('map') and not r['map']: e.update(map=o['map'], map_src=o['src'], map_conf='high')
        if not e.get('site') and not r['web']:
            for host, (urls, des) in pages.items():
                if not re.search(des, norm(r['name'])): continue
                u, conf = match_url(r['name'], [x for x in urls if not re.search(r'map', x, re.I)])
                if u: e.update(site=u, site_src=host + ' sitemap', site_conf=conf); break
        if not e.get('map') and not r['map']:
            for host, (urls, des) in pages.items():
                if not re.search(des, norm(r['name'])): continue
                u, conf = match_url(r['name'], [x for x in urls if re.search(r'map', x, re.I)])
                if u: e.update(map=u, map_src=host + ' sitemap', map_conf=conf); break
        if e.get('site') or e.get('map'): found += 1; out[norm(r['name'])] = e
    rep = {'about': f'{state}: official website / map links pre-found for parks with none on file (kpc_official_find.py). The Tool Box reads this after what is on file.',
           'built': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'), 'ua': UA, 'sources': srcs,
           'counts': {'parks': len(rows), 'needed': len(need), 'found': found}, 'links': out}
    pathlib.Path('data/official-links').mkdir(parents=True, exist_ok=True)
    pathlib.Path(f'data/official-links/{state}.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'::notice title=Official links::{state}: {found} of {len(need)} parks without a site or map now have one')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        assert norm('Fishtrap Lake WMA') == norm('Fishtrap Lake Wildlife Management Area')
        assert match_url('Carter Caves State Park', ['https://parks.ky.gov/explore/carter-caves-state-resort-park-7', 'https://parks.ky.gov/explore/caves'])[0].endswith('park-7')
        assert match_url('Natural Bridge State Park', ['https://parks.ky.gov/explore/carter-caves'])[0] is None
        assert BANNED.search('services6.arcgis.com') and BANNED.search('ncnhde.natureserve.org')
        print('selftest ok'); sys.exit(0)
    main(sys.argv[1] if len(sys.argv) > 1 else 'KY')
