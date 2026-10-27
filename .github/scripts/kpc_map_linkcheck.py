#!/usr/bin/env python3
"""MAP LINK CHECK (chat 2, Oct 26 2026; research desk + HQ: 'before the site shows any map link, have a bot check every URL
loads'). Opens every map / map_page / agency_map link in data/parkinfo-web.json (slowly, one at a time) and records
map_check = {map: status, map_page: status, agency_map: status, date}. A link that answers 200-399 with a real page or
file is 'ok'. A park with map_hold keeps the hold until ALL its links load; then the hold is cleared (map_hold_cleared).
Tools must show a map link only when map_check says 'ok' for it and the park has no map_hold. Monthly (official-links
workflow) + by hand. Never fails."""
import json, os, pathlib, re, sys, time, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from kpc_save import save_json

T0, LIMIT = time.time(), float(os.environ.get('MINUTES') or 120) * 60
P = pathlib.Path('data/parkinfo-web.json')
UA = {'User-Agent': 'Mozilla/5.0 (compatible; KPC map link check; kentuckyportableclub.github.io)', 'Accept': '*/*'}
KINDS = ('map', 'map_page', 'agency_map')


def status(url):
    for method in ('HEAD', 'GET'):
        try:
            req = urllib.request.Request(url, headers=dict(UA, **({'Range': 'bytes=0-2047'} if method == 'GET' else {})), method=method)
            with urllib.request.urlopen(req, timeout=40) as r:
                code = r.status
                if method == 'GET':
                    body = r.read(2048).decode('utf-8', 'replace').lower()
                    if re.search(r'page (not|cannot be) found|404 not found|no longer available', body): return 'gone (page says not found)'
                return 'ok' if code < 400 else f'HTTP {code}'
        except urllib.error.HTTPError as e:
            if method == 'HEAD' and e.code in (403, 405, 400, 404, 500, 501): continue   # many servers refuse HEAD: try GET
            if e.code == 403: return browser_like(url)
            return f'HTTP {e.code}'
        except Exception as e:  # noqa: BLE001
            if method == 'HEAD': continue
            return 'no answer (' + str(e)[:40] + ')'
    return 'no answer'


def browser_like(url):
    """Oct 27 (research-bots review #8): many agency PDFs refuse robots (403) but open in any browser. One honest retry with
    browser-like Accept headers (same User-Agent, never pretending to be a person); still 403 = 'blocked (opens in a browser)'."""
    try:
        req = urllib.request.Request(url, headers=dict(UA, **{'Accept': 'text/html,application/pdf,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.9', 'Range': 'bytes=0-2047'}))
        with urllib.request.urlopen(req, timeout=40) as r: return 'ok' if r.status < 400 else f'HTTP {r.status}'
    except urllib.error.HTTPError as e:
        return 'blocked (opens in a browser)' if e.code == 403 else f'HTTP {e.code}'
    except Exception as e:  # noqa: BLE001
        return 'no answer (' + str(e)[:40] + ')'


def main():
    d = json.load(open(P))
    today = time.strftime('%Y-%m-%d')
    todo = sorted(d['parks'].items(), key=lambda kv: (not kv[1].get('map_hold'), (kv[1].get('map_check') or {}).get('date', '')))
    n = ok = bad = cleared = 0
    cache = {}
    for ref, e in todo:
        if time.time() - T0 > LIMIT: break
        links = {k: e[k] for k in KINDS if str(e.get(k, '')).startswith('http')}
        if not links: continue
        chk = {'date': today}
        for k, u in links.items():
            if u not in cache:
                cache[u] = status(u); time.sleep(1.0)
            chk[k] = cache[u]
            n += 1; ok += cache[u] == 'ok'; bad += cache[u] != 'ok'
        e['map_check'] = chk
        # research-bots review #8: a map link gone (404 / page says not found) is looked for again on the park's own page by the
        # map finder (its next run takes these parks first); the link stays hidden until found or a person checks it
        if any(str(chk.get(k, '')).startswith(('HTTP 404', 'gone')) for k in links): e['map_refind'] = e.get('map_refind') or today
        elif e.get('map_refind') and all(chk[k] == 'ok' for k in links): e.pop('map_refind')
        if e.get('map_hold') and all(chk[k] == 'ok' for k in links):
            e['map_hold_cleared'] = f"{today}: every link loads ({e.pop('map_hold')})"; cleared += 1
    save_json(P, d, indent=1)
    print(f'::notice title=Map link check::{n} links checked: {ok} load, {bad} do not; {cleared} held parks cleared; '
          f"{sum(1 for x in d['parks'].values() if x.get('map_hold'))} still held", flush=True)
    bads = [f"{ref} {k}: {v}" for ref, e in d['parks'].items() for k, v in (e.get('map_check') or {}).items() if k != 'date' and v != 'ok']
    for i in range(0, min(len(bads), 160), 20): print('::notice title=Maps not loading::' + ' | '.join(bads[i:i + 20])[:900], flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=Map link check::stopped: {e}', flush=True)
    sys.exit(0)
