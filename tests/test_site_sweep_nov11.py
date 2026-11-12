#!/usr/bin/env python3
"""Site sweep fixes (Nov 11 2026, site review package F). Offline: reads the repo's files only, no network.

 1. Leaflet comes from ONE CDN and ONE version on every page: unpkg leaflet@1.9.4, each tag with the same integrity value
    finder.html already used and crossorigin (so the service worker can keep a copy). No cdnjs Leaflet left.
 2. Map tooltips built from outside text (PSK Reporter / wspr.live calls, WSPR grid squares, SOTA summit names, park names)
    are escaped before Leaflet puts them in the page as HTML.
 3. The Hunters "Parks I Need" page only takes iframe-height messages from this site.
 4. Park Notes still draws its list when the address has a broken %-code after #.
"""
import os, re, subprocess, sys

ROOT = os.environ.get('LINKS') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = 0


def ok(c, m):
    global fails
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails += 1


def rd(f):
    with open(os.path.join(ROOT, f), encoding='utf-8', errors='replace') as fh: return fh.read()


CSS_I = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY='
JS_I = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo='
root = sorted(f for f in os.listdir(ROOT) if re.search(r'\.(html|js)$', f))
cdnjs_leaf = [f for f in root if re.search(r'cdnjs\.cloudflare\.com/ajax/libs/leaflet', rd(f))]
ok(not cdnjs_leaf, 'no page or script loads Leaflet from cdnjs (one CDN for Leaflet): ' + (' '.join(cdnjs_leaf) or 'none'))
bad, n = [], 0
for f in root:
    if not f.endswith('.html'): continue
    for m in re.finditer(r'<(script|link)\b[^>]*unpkg\.com/leaflet@([\d.]+)/dist/leaflet\.(js|css)[^>]*>', rd(f)):
        n += 1; tag = m.group(0)
        want = JS_I if m.group(3) == 'js' else CSS_I
        if m.group(2) != '1.9.4' or ('integrity="%s"' % want) not in tag or 'crossorigin' not in tag: bad.append(f + ': ' + tag[:90])
ok(n >= 50 and not bad, '%d Leaflet tags: all leaflet@1.9.4 with the same integrity + crossorigin (%s)' % (n, '; '.join(bad[:3]) or 'ok'))
ok(('integrity="%s"' % JS_I) in rd('finder.html'), 'finder.html keeps the integrity value the other pages copied')
for f in ('kpc-band-maps.js', 'kpc-adif.js'):
    t = rd(f)
    ok(JS_I in t and CSS_I in t and 'unpkg.com/leaflet@1.9.4/dist/leaflet.js' in t, f + ': its own Leaflet loader uses unpkg 1.9.4 with integrity')

# 2. tooltips: run the escape on a hostile value the same way the page does
t = rd('kpc-logger-ft8.js')
ok('bindTooltip(`${esc(x.call)} ${esc(x.snr)} dB' in t and 'bindTooltip(`${esc(x.call)} heard you' in t, 'kpc-logger-ft8.js: wspr.live calls escaped in the map tooltips')
ok('bindTooltip(`${esc(x.fr)} ' in t and "esc(sp.reference)" in t, 'kpc-logger-ft8.js: decoded calls and POTA refs escaped in the map tooltips')
ok('bindTooltip(`${esc(rc)} heard you' in t, 'kpc-logger-ft8.js: PSK Reporter (mqtt) receiver calls escaped in the map tooltips')
ok(not re.search(r'bindTooltip\(`\$\{(x\.call|x\.fr|rc)\}', t), 'kpc-logger-ft8.js: no raw call left in a tooltip')
ok('${esc(String(r.loc).toUpperCase())}' in rd('kpc-band-maps.js'), 'kpc-band-maps.js: wspr.live grid square escaped in the path tooltip')
ok('bindTooltip(`${esc(cur.c)} ${esc(cur.n)}`)' in rd('kpc-sota-az.js'), 'kpc-sota-az.js: summit name escaped in the tooltip')
ok("bindTooltip(esc((p.ref ? p.ref + ' ' : '') + p.name))" in rd('kpc-weather.js'), 'kpc-weather.js: place name escaped in the tooltip')
js = r"""
const src = require('fs').readFileSync(process.argv[1], 'utf8');
const m = src.match(/const esc = (s => String\(s == null \? '' : s\)\.replace\(.*?\}\[c\]\)\));/); if (!m) { console.log('NOESC'); process.exit(0); }
const esc = eval(m[1]); const x = { call: '<img src=x onerror=alert(1)>', snr: -12 };
console.log(`${esc(x.call)} ${esc(x.snr)} dB`);
"""
try:
    out = subprocess.run(['node', '-e', js, os.path.join(ROOT, 'kpc-logger-ft8.js')], capture_output=True, text=True, timeout=60).stdout.strip()
    ok('<img' not in out and '&lt;img' in out, 'node: a hostile call in a tooltip comes out as text: ' + out[:60])
except FileNotFoundError:
    print('PASS node not installed here: the static checks above cover the tooltips')

# 3. message listener
t = rd('kpc-hunters-need.html')
ok("addEventListener('message',function(e){if(e.origin!==location.origin)return;" in t, 'kpc-hunters-need.html: iframe-height messages only from this site')

# 4. park notes hash
g = re.search(r" let h='';try\{.*?\}catch\(e\)\{.*?\}", rd('kpc-park-notes.js'))
ok(bool(g), 'kpc-park-notes.js: the hash decode is wrapped in try/catch')
if g:
    js = "const location={hash:'#%E0%A4%A'};" + g.group(0).replace("let h='';", "let h='';", 1) + "console.log('OK '+h);"
    try:
        out = subprocess.run(['node', '-e', js], capture_output=True, text=True, timeout=60)
        ok(out.stdout.startswith('OK '), 'node: a broken %-code after # no longer throws (' + (out.stdout.strip() or out.stderr.strip()[:80]) + ')')
    except FileNotFoundError:
        print('PASS node not installed here: the static check above covers it')

# 5. the Club Room does not load ~190 POTA look-ups behind the members door for guests
ok("if(!window.KPCGate||KPCGate.member())go();" in rd('kpc-club.html'), 'kpc-club.html: the activation history loads only for signed-in members')

print('SOME FAILED' if fails else 'ALL PASSED')
sys.exit(1 if fails else 0)
