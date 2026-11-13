#!/usr/bin/env python3
"""Nov 11 2026 (KPC owner): the hand map placer page (kpc-map-placer.html / .js / -math.js). Offline, no browser:
  - the maths in node (tests/map_placer_math_nov11.js: known similarity recovered, residuals, leave-one-out, points on a line /
    bunched / mirrored / 2 points refused, round trips, the shared fixture tests/fixtures/hand-place-cases.json);
  - the page is members only (kpc-gate.js, not on the PUBLIC list, noindex), linked from nowhere, uses only hosts the site already
    uses, places points only on the USGS (government) layers, never moves the pin and sends nothing anywhere.
The real-browser walk-through is tests/map_placer_nov11_browser.py (needs Chrome + playwright; run by hand)."""
import pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True


def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m)
    ok = ok and bool(c)


r = subprocess.run(['node', str(ROOT / 'tests/map_placer_math_nov11.js')], capture_output=True, text=True, timeout=120)
for line in r.stdout.splitlines():
    if line.startswith('FAIL'):
        print('  ' + line)
check(r.returncode == 0 and r.stdout.rstrip().endswith('ALL PASS'), 'node tests/map_placer_math_nov11.js: ' + (r.stdout.strip().splitlines() or ['no output'])[-1])

html = (ROOT / 'kpc-map-placer.html').read_text(encoding='utf-8')
js = (ROOT / 'kpc-map-placer.js').read_text(encoding='utf-8')
mjs = (ROOT / 'kpc-map-placer-math.js').read_text(encoding='utf-8')
head = html[:html.index('</head>')]
gate = (ROOT / 'kpc-gate.js').read_text(encoding='utf-8')
pub = re.search(r'var PUBLIC = \[(.*?)\];', gate, re.S).group(1)
check(re.search(r'<script[^>]+src="kpc-gate\.js', head) and 'kpc-map-placer.html' not in pub, 'members only: kpc-gate.js in the head, not on the PUBLIC list')
check('<meta name="robots" content="noindex,nofollow">' in head, 'noindex, nofollow (members-only page)')
check("if (window.KPCGate && !KPCGate.member()) return;" in js, 'the page builds nothing for a non-member')
others = [p for p in list(ROOT.glob('*.html')) + list(ROOT.glob('*.js')) + list(ROOT.glob('*.json')) + list(ROOT.glob('.claude/build/**/*.html'))
          if p.name not in ('kpc-map-placer.html', 'kpc-map-placer.js', 'kpc-map-placer-math.js')]
links_to = [p.name for p in others if 'kpc-map-placer' in p.read_text(encoding='utf-8', errors='replace')]
check(not links_to, f'not linked from any menu, page, search list or site file: {links_to}')
check(html.index('kpc-map-placer-math.js?v=') < html.index('kpc-map-placer.js?v='), 'the maths loads before the page script (both with a ?v= stamp)')

HOST = re.compile(r'https?://([a-z0-9.-]+\.[a-z]{2,})', re.I)
mine = set(HOST.findall(html + js + mjs))
site = set()
for p in others:
    if p.suffix in ('.html', '.js'):
        site |= set(HOST.findall(p.read_text(encoding='utf-8', errors='replace')))
check(mine and mine <= site, f'no new host: every address host is already used by the site: {sorted(mine)}')
check(not re.search(r'services\d*(-[a-z0-9]+)?\.arcgis\.com|apps\.fs\.usda\.gov|ncnhde|33TOOklri9xpic7U|arcgisonline|protectedplanet|wdpa', html + js + mjs, re.I),
      'no never-contact host, no Esri tiles, nothing from WDPA / Protected Planet')
check("raw.githubusercontent.com/KentuckyPortableClub/KPC-Data/picture-maps/" in js and "KPC.dataUrl" in js, 'pictures from the public picture-maps branch, park pins through KPC.dataUrl (the site\'s own data path)')
bm = re.findall(r"'(usgs-[a-z-]+)': \{ name: '([^']+)', url: '([^']+)'", mjs)
check(len(bm) == 2 and all(u.startswith('https://basemap.nationalmap.gov/') for _, _, u in bm), 'points may be clicked only on USGS The National Map layers (government basemaps)')
check("if (!M.BASEMAPS[S.base]) { say('Points can only be placed on a USGS map" in js and "look only" in js, 'OpenStreetMap is offered for looking only: a click on it places no point')
check("radius: 7, color: '#c00'" in js and 'interactive: false' in js and 'draggable: true' not in js.split('POTA pin (never moved)')[0].split('L.circleMarker(S.park.pin')[-1],
      'the POTA pin is drawn, never draggable, never written back')
check(not re.search(r"fetch\([^)]*method\s*:\s*['\"](POST|PUT)|XMLHttpRequest|navigator\.sendBeacon|api\.github\.com", js + mjs), 'the page sends nothing anywhere (no POST, beacon or GitHub API)')
check("a.download = S.ref + '.clicks.json'" in js and 'intake-files' in html and 'hand-placer/' in html, 'SAVE downloads <ref>.clicks.json; the page says where it goes')
check('Not the official boundary' in html and "bindTooltip('Approximate: not the official boundary')" in js, 'the not-official note is on the page and on the placed outline')
check(not re.search(r'\b[AKNW][A-Z]?\d[A-Z]{1,3}\b', html + js + mjs), 'no callsign-like text')
print('ALL PASS' if ok else 'SOME FAILED')
raise SystemExit(0 if ok else 1)
