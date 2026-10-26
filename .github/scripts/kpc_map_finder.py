#!/usr/bin/env python3
"""MAP FINDER (chat 2, Oct 26 2026; Brandon via HQ 'BOTS FOR THE GAPS'): for parks with an official page and no
official map link yet, open that page (one at a time, slowly) and list the links on it named like map / brochure /
park guide / PDF. SUGGESTIONS ONLY: they go to data/map-leads.json for a quick check by a person or the outside bot,
never straight into the park data.

Polite: only the park's own official page (the website in data/parkinfo or parkinfo-web.json) and links on the same
site or another government site; 1.5 s between pages; busiest parks first; MAX pages a run (default 600), the next
run carries on where this one stopped (rotation by the 'checked' date). Monthly, never fails."""
import html, json, os, pathlib, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from kpc_save import save_json

T0, LIMIT = time.time(), float(os.environ.get('MINUTES') or 150) * 60
MAX = int(os.environ.get('MAX') or 600)
UA = {'User-Agent': 'KPC map finder (kentuckyportableclub.github.io; one page at a time)', 'Accept': 'text/html,application/xhtml+xml'}
OUT = pathlib.Path('data/map-leads.json')
WORDS = re.compile(r'\bmaps?\b|brochure|park guide|visitor guide|trail guide|site guide|area guide|boundary|\bpdf\b', re.I)
NOTW = re.compile(r'google\.com/maps|maps\.google|maps\.apple|bing\.com/maps|site ?map|sitemap|directions|mapquest|waze|facebook|twitter|instagram|'
                  r'youtube|privacy|accessibility|newsletter|login|sign ?in|donate|shop|store|jobs|careers', re.I)
GOV = re.compile(r'(\.gov|\.mil|\.us|\.gc\.ca|\.gov\.[a-z]{2}\.ca|ontarioparks\.(com|ca)|bcparks\.ca|albertaparks\.ca|sepaq\.com|parks\.canada\.ca|'
                 r'\.state\.[a-z]{2}\.us)$', re.I)


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', ' ')[:900]), flush=True)


def links(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        if 'html' not in (r.headers.get('Content-Type') or 'html'): return [], r.geturl()
        body = r.read(1_500_000).decode('utf-8', 'replace'); base = r.geturl()
    out = []
    for m in re.finditer(r'<a\b[^>]*?href\s*=\s*["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', body, re.I | re.S):
        href, text = m.group(1).strip(), html.unescape(re.sub(r'<[^>]+>', ' ', m.group(2)))
        text = ' '.join(text.split())[:120]
        u = urllib.parse.urljoin(base, href)
        if not u.startswith('http'): continue
        if not (WORDS.search(text) or re.search(r'map|brochure|guide', urllib.parse.urlparse(u).path, re.I) and u.lower().endswith('.pdf')): continue
        if NOTW.search(text + ' ' + u): continue
        out.append([text or u.rsplit('/', 1)[-1], u])
    return out, base


def main():
    P = {}
    for f in list(pathlib.Path('data/parkinfo').glob('US-*.json')) + [pathlib.Path('data/parkinfo/CA.json')]:
        try: P.update(json.load(open(f))['parks'])
        except Exception: pass  # noqa: BLE001
    try: W = json.load(open('data/parkinfo-web.json'))['parks']
    except Exception: W = {}  # noqa: BLE001
    try: old = json.load(open(OUT))
    except Exception: old = {'parks': {}}  # noqa: BLE001
    leads = old.get('parks', {})
    todo = []
    for ref, v in P.items():
        if (W.get(ref) or {}).get('map'): continue                    # has an official map link already
        page = v[1] or (W.get(ref) or {}).get('web')
        if not page or not page.startswith('http'): continue
        todo.append((leads.get(ref, {}).get('checked', ''), -(v[7] or 0) if len(v) > 7 and isinstance(v[7], int) else 0, ref, page))
    todo.sort()
    n = got = 0
    for checked, _, ref, page in todo:
        if n >= MAX or time.time() - T0 > LIMIT: break
        n += 1
        host = urllib.parse.urlparse(page).netloc.lower()
        e = {'checked': time.strftime('%Y-%m-%d'), 'page': page, 'name': P[ref][0]}
        try:
            ls, base = links(page)
            bh = urllib.parse.urlparse(base).netloc.lower()
            keep, seen = [], set()
            for text, u in ls:
                h = urllib.parse.urlparse(u).netloc.lower()
                if not (h == host or h == bh or GOV.search(h)) or u in seen: continue
                seen.add(u); keep.append([text, u])
            e['suggest'] = keep[:8]
            if keep: got += 1
        except Exception as ex:  # noqa: BLE001
            e['error'] = str(ex)[:80]
        leads[ref] = e
        time.sleep(1.5)
    save_json(OUT, {'about': 'MAP FINDER suggestions (kpc_map_finder.py, monthly): links named map / brochure / guide / PDF on each park\'s '
                             'official page. NOT checked: a person (or the outside bot) confirms one before it goes into parkinfo-web.json as map.',
                    'parks': leads}, indent=1)
    notice('Map finder', f'{n} pages read, {got} with map-like links; {sum(1 for x in leads.values() if x.get("suggest"))} parks with suggestions in all; {max(0, len(todo) - n)} pages left for next time')


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        notice('Map finder', f'stopped: {e}')
    sys.exit(0)
