#!/usr/bin/env python3
"""TEMP (chat 2, Oct 27; Brandon: 'search the state park name, the Explore tab offers many maps' on parks.ky.gov): opens each park's
page in a real browser (the site is built by script), clicks Explore / Maps tabs, lists every map / PDF link. Writes
.claude/build/research/ky-parkmaps-probe.json. Deleted after one run. Never fails."""
import json, re, sys
from playwright.sync_api import sync_playwright
PAGES = {'US-1286': 'https://parks.ky.gov/explore/natural-bridge-state-resort-park-7796', 'US-1259': 'https://parks.ky.gov/explore/green-river-lake-state-park-7814',
         'US-1257': 'https://parks.ky.gov/explore/general-burnside-island-state-park-7812', 'US-1253': 'https://parks.ky.gov/explore/dawkins-line-rail-trail-7831',
         'US-3787': 'search:White Hall', 'US-3789': 'search:William Whitley', 'US-1264': 'search:Levi Jackson', 'US-3781': 'https://parks.ky.gov/explore/breaks-interstate-park-7829'}
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    for ref, u in PAGES.items():
        r = {'page': u}
        try:
            if u.startswith('search:'):
                q = u[7:]
                pg.goto('https://parks.ky.gov/', timeout=60000); pg.wait_for_timeout(3000)
                links = pg.eval_on_selector_all('a', 'as => as.map(a => [a.innerText.trim(), a.href])')
                hit = [h for t, h in links if q.lower() in t.lower() and '/explore/' in h]
                if not hit:
                    pg.goto('https://parks.ky.gov/search?q=' + q.replace(' ', '+'), timeout=60000); pg.wait_for_timeout(4000)
                    links = pg.eval_on_selector_all('a', 'as => as.map(a => [a.innerText.trim(), a.href])')
                    hit = [h for t, h in links if '/explore/' in h and any(w.lower() in (t + h).lower() for w in q.split())]
                r['found'] = hit[:5]
                if not hit: out[ref] = r; continue
                u = hit[0]
            pg.goto(u, timeout=60000); pg.wait_for_timeout(4000)
            for lab in ('Explore', 'Maps', 'Park Maps', 'Map'):
                try:
                    el = pg.get_by_text(lab, exact=True).first
                    if el.count(): el.click(timeout=3000); pg.wait_for_timeout(2000)
                except Exception: pass  # noqa: BLE001
            links = pg.eval_on_selector_all('a', 'as => as.map(a => [a.innerText.trim(), a.href])')
            r['maps'] = [[t, h] for t, h in links if re.search(r'\.pdf|map', h + ' ' + t, re.I) and 'google' not in h][:40]
        except Exception as e: r['error'] = str(e)[:200]  # noqa: BLE001
        out[ref] = r
        print(f'::notice title=park maps {ref}::{json.dumps(r)[:800]}', flush=True)
    b.close()
json.dump(out, open('.claude/build/research/ky-parkmaps-probe.json', 'w'), indent=1)
