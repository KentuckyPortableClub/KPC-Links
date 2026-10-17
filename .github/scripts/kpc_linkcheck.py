"""Weekly broken-link check for the KPC site.

Checks every link and image on every page:
  - links to our own pages and files (does the file exist? does the #section exist?)
  - links to other websites (does the page still load?)
  - pictures named in our CSS and JavaScript files (does the picture exist?)
  - pictures bigger than 800 KB and pages heavier than 4 MB (they make phones slow)
Results go into one GitHub issue labelled "link-check", which closes itself when everything is fine.
"""
import collections
import concurrent.futures as cf
import datetime as dt
import html
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from kpc_issue import report  # noqa: E402

ROOT = pathlib.Path('.')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 KPC-link-check'
SITE = 'https://kentuckyportableclub.github.io/KPC-Links/'
# Sites that block automated checks; listed separately instead of as broken.
NO_BOTS = ('facebook.com', 'instagram.com', 'x.com', 'twitter.com', 'linkedin.com', 'photos.google.com', 'photos.app.goo.gl',
           'tiktok.com', 'reddit.com', 'qrz.com', 'fs.usda.gov', 'groups.io')
# #hashes that the page's own JavaScript handles (not real section ids)
JS_HASHES = {'listen', 'hunt', 'act', 'drill', 'free', 'qrq', 'chat', 'sprint', 'games', 'keyer', 'gaunt', 'learn', 'efhw', '9to1', 'choke', '4to1', 'j', 'sj', 'sjl', 'roll', 'gp', 'whip', 'top', ''}
try:  # photo album ids (photos.html#album-id)
    import json
    JS_HASHES |= {a.get('id') for a in json.load(open('kpc-photos.json')).get('albums', []) if a.get('id')}
except Exception:  # noqa: BLE001
    pass

pages = sorted(p for p in ROOT.glob('*.html'))
ids = {}
refs = collections.defaultdict(set)  # url -> set(pages)
for p in pages:
    t = p.read_text(encoding='utf-8', errors='replace')
    ids[p.name] = set(re.findall(r'\bid="([^"]+)"', t))
    no_script = re.sub(r'(?is)<script\b.*?</script>', ' ', t)
    for u in re.findall(r'(?:href|src)="([^"]+)"', no_script):
        u = html.unescape(u.strip())
        if not u or '${' in u or u.startswith(('mailto:', 'tel:', 'javascript:', 'data:', 'sms:', 'geo:')):
            continue
        refs[u].add(p.name)

# Links lists kept as data (Tools & Essential Links, Founders' Favorites) are drawn by kpc-guide-links.js
try:
    gl = json.loads((ROOT / 'kpc-guide-links.json').read_text(encoding='utf-8'))
    for key, pg in gl.get('pages', {}).items():
        page = {'tools': 'kpc-guide-tools-links.html', 'founders': 'kpc-guide-founders-favorites.html'}.get(key, 'kpc-guide-links.json')
        for u in re.findall(r'"url":\s*"([^"]+)"', json.dumps(pg)):
            refs[u].add(page)
except Exception:
    pass

# Campground, cabin and lodge links (drawn on kpc-campgrounds.html by kpc-campgrounds.js)
try:
    cg = json.loads((ROOT / 'kpc-campgrounds.json').read_text(encoding='utf-8'))
    for p in cg.get('parks', []):
        for x in p.get('campgrounds', []) + p.get('lodging', []):
            for k in ('url', 'map', 'reserve'):
                if x.get(k): refs[x[k]].add('kpc-campgrounds.html')
except Exception:
    pass

broken, anchors, blocked = [], [], []

# ---- our own files
for u, where in sorted(refs.items()):
    if re.match(r'(?i)https?://', u) and not u.startswith(SITE):
        continue
    local = u[len(SITE):] if u.startswith(SITE) else u
    if local.startswith('#'):
        for pg in where:
            h = local[1:]
            if h not in ids.get(pg, set()) and h not in JS_HASHES:
                anchors.append((pg + local, [pg]))
        continue
    path, _, frag = local.partition('#')
    path = urllib.parse.unquote(path.split('?')[0])
    if not path or path.startswith('//'):
        continue
    target = ROOT / path
    if not target.exists():
        broken.append((u, 'file not found', sorted(where)))
    elif frag and target.suffix == '.html' and frag not in ids.get(target.name, set()) and frag not in JS_HASHES:
        anchors.append((u, sorted(where)))


# ---- other websites
def check(u):
    host = urllib.parse.urlparse(u).netloc.lower()
    if any(host == d or host.endswith('.' + d) for d in NO_BOTS):
        return u, 'skip', 'site blocks automated checks'
    last = ''
    for method in ('HEAD', 'GET', 'GET'):
        try:
            req = urllib.request.Request(u, method=method, headers={'User-Agent': UA, 'Accept': '*/*', 'Accept-Language': 'en-US'})
            with urllib.request.urlopen(req, timeout=25) as r:
                return u, 'ok', r.status
        except urllib.error.HTTPError as e:
            last = 'HTTP %s' % e.code
            if e.code in (401, 403, 429, 999):
                return u, 'skip', last
            if e.code in (404, 410) and method == 'GET':
                return u, 'bad', last
        except Exception as e:  # noqa: BLE001
            last = type(e).__name__ + ': ' + str(e)[:80]
        time.sleep(2)
    return u, 'bad', last


ext = [] if os.getenv('KPC_OFFLINE') else sorted(u for u in refs if re.match(r'(?i)https?://', u) and not u.startswith(SITE))
print('Checking', len(ext), 'outside links and', len(refs) - len(ext), 'site links on', len(pages), 'pages')
with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for u, state, info in ex.map(check, ext):
        if state == 'bad':
            broken.append((u, info, sorted(refs[u])))
        elif state == 'skip':
            blocked.append((u, info, sorted(refs[u])))

# ---- pictures named in CSS / JavaScript (backgrounds, heroes) and file sizes
IMG = re.compile(r'''(?<![\w./-])((?:[\w-]+/)*[\w.-]+\.(?:jpe?g|png|gif|webp|svg))(?=[\s'"\)?#,])''', re.I)
PIC_EXT = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')
BIG_PIC, HEAVY_PAGE = 800_000, 4_000_000
pics = collections.defaultdict(set)
for f in list(ROOT.glob('*.html')) + list(ROOT.glob('*.css')) + list(ROOT.glob('*.js')):
    for m in IMG.findall(f.read_text(encoding='utf-8', errors='replace')):
        if m.startswith(('-', 'images/')):  # pieces of names built in code; Leaflet's own icons
            continue
        pics[m].add(f.name)
missing_pics = sorted((u, sorted(w)) for u, w in pics.items() if not (ROOT / u).exists() and not any(u == b[0] for b in broken))
big_pics = sorted(((u, (ROOT / u).stat().st_size, sorted(w)) for u, w in pics.items() if (ROOT / u).is_file() and (ROOT / u).stat().st_size > BIG_PIC), key=lambda x: -x[1])
heavy = []
for p in pages:
    t = p.read_text(encoding='utf-8', errors='replace')
    tot, seen = p.stat().st_size, set()
    for u in re.findall(r'(?:src|href)="([^"#?]+)', t) + IMG.findall(t):
        if u in seen or u.startswith(('http', '//', '-')):
            continue
        seen.add(u)
        f = ROOT / urllib.parse.unquote(u)
        if f.is_file() and f.suffix.lower() in PIC_EXT + ('.css', '.js'):
            tot += f.stat().st_size
    if tot > HEAVY_PAGE:
        heavy.append((p.name, tot))

problems = len(broken) + len(anchors) + len(missing_pics) + len(big_pics) + len(heavy)
when = dt.datetime.now(dt.timezone.utc).strftime('%b %d, %Y')
lines = ['_Checked %s: %d pages, %d outside links._' % (when, len(pages), len(ext)), '']
if broken:
    lines += ['## Broken links (%d)' % len(broken), '', '| Link | Problem | On page(s) |', '|---|---|---|']
    lines += ['| %s | %s | %s |' % (u.replace('|', '%7C'), info, ', '.join(w[:4]) + (' …' if len(w) > 4 else '')) for u, info, w in broken]
    lines.append('')
if anchors:
    lines += ['## Links to a section that doesn\'t exist (%d)' % len(anchors), '', 'The page loads, but the `#section` part points nowhere.', '']
    lines += ['- `%s` on %s' % (u, ', '.join(w[:4])) for u, w in anchors]
    lines.append('')
if missing_pics:
    lines += ['## Missing pictures (%d)' % len(missing_pics), '', 'A style or script file names a picture that is not in the site.', '']
    lines += ['- `%s` in %s' % (u, ', '.join(w[:4])) for u, w in missing_pics]
    lines.append('')
if big_pics:
    lines += ['## Big pictures that slow phones down (%d)' % len(big_pics), '', 'Over %d KB. Ask Claude to shrink them (same look, smaller file).' % (BIG_PIC // 1000), '']
    lines += ['- `%s` %d KB, used by %s' % (u, n // 1024, ', '.join(w[:4])) for u, n, w in big_pics]
    lines.append('')
if heavy:
    lines += ['## Heavy pages (%d)' % len(heavy), '', 'The page plus its pictures, styles and scripts add up to more than %d MB.' % (HEAVY_PAGE // 1_000_000), '']
    lines += ['- %s: %.1f MB' % (n, t / 1e6) for n, t in heavy]
    lines.append('')
if blocked:
    lines += ['<details><summary>Couldn\'t check automatically (%d). These sites block robots; click through now and then.</summary>' % len(blocked), '']
    lines += ['- %s (%s)' % (u, info) for u, info, _ in blocked]
    lines += ['', '</details>']
lines += ['', 'This issue updates every Sunday and closes itself when everything checks out. Run it any time: Actions → KPC Link Check → Run workflow.']
body = '\n'.join(lines)
print(body)
title = '🔗 Broken links & pictures: %d to fix (%s)' % (problems, when)
if os.getenv('GITHUB_ACTIONS'):
    report('link-check', title, body, problems)
