"""Go-live step for the Campgrounds & Cabins page (run by kpc-go-live.yml on Oct 21, 2026, before the announcement).
Until then kpc-campgrounds.html is hidden (noindex, not linked). This script:
  1. removes the noindex line from kpc-campgrounds.html
  2. adds it to the See More menu on every page (after Park Notes)
  3. adds it to kpc-search.js (and bumps the search script version on every page), find.html, toolbox.html
Safe to run twice: each step checks whether it was already done."""
import glob, re, datetime

PAGE = 'kpc-campgrounds.html'
done = []

s = open(PAGE, encoding='utf-8').read()
n = re.sub(r'<meta name="robots" content="noindex"><!-- KPC-GOLIVE:[^>]*-->', '', s)
if n != s: open(PAGE, 'w', encoding='utf-8').write(n); done.append('noindex removed')

MENU_AFTER = re.compile(r'(<a href="kpc-park-notes\.html" role="menuitem">.*?</a>)')
MENU = '\n            <a href="kpc-campgrounds.html" role="menuitem"><span class="ni">&#127957;</span>Campgrounds &amp; Cabins</a>'
menus = 0
for f in sorted(glob.glob('*.html')):
    t = open(f, encoding='utf-8').read()
    if 'href="kpc-campgrounds.html" role="menuitem"' in t or not MENU_AFTER.search(t): continue
    t = MENU_AFTER.sub(lambda m: m.group(1) + MENU, t, count=1)
    open(f, 'w', encoding='utf-8').write(t); menus += 1
if menus: done.append(f'menu on {menus} pages')

js = open('kpc-search.js', encoding='utf-8').read()
if '"kpc-campgrounds.html"' not in js:
    row = ('["kpc-campgrounds.html", "Campgrounds & Cabins", "Campgrounds, cabins and lodges inside Kentucky POTA parks, with POTA, WWFF and SOTA on one card, '
           'campground maps, booking links and reviews.", "STAY", "campground campgrounds camping camp cabins cabin cottage lodge resort rv hookups electric '
           'tent reserve reservation campground map stay overnight reviews rating pota sota kff wwff kentucky"],')
    js = js.replace('const TOOLS=[', 'const TOOLS=[' + row, 1)
    open('kpc-search.js', 'w', encoding='utf-8').write(js); done.append('search')
    v = datetime.date.today().strftime('%Y%m%d') + 'g'
    for f in glob.glob('*.html'):
        t = open(f, encoding='utf-8').read()
        u = re.sub(r'kpc-search\.js\?v=[0-9a-z]+', 'kpc-search.js?v=' + v, t)
        if u != t: open(f, 'w', encoding='utf-8').write(u)

def add(f, anchor, html, mark):
    t = open(f, encoding='utf-8').read()
    if mark in t or anchor not in t: return
    open(f, 'w', encoding='utf-8').write(t.replace(anchor, html + anchor, 1)); done.append(f)

add('find.html', '<a class="fi-item" href="kpc-park-notes.html"',
    '<a class="fi-item" href="kpc-campgrounds.html" data-k="campgrounds campground camping cabins cottages lodge resort rv hookups reserve campground map stay overnight reviews kpc-campgrounds.html"><span class="fi-t">Campgrounds &amp; Cabins</span><span class="fi-d">Places to stay inside Kentucky POTA parks, with POTA, WWFF and SOTA on one card, campground maps, booking links and reviews.</span></a>',
    'class="fi-item" href="kpc-campgrounds.html"')
add('toolbox.html', '<a class="card" href="kpc-park-notes.html">',
    '<a class="card" href="kpc-campgrounds.html"><div class="card-top"><div class="card-num">STAY &amp; ACTIVATE</div><h3>Campgrounds &amp; Cabins</h3><span class="cov cov-ky">&#128205; KENTUCKY ONLY</span><p>Campgrounds, cabins and lodges inside Kentucky POTA parks, with every program at that park on one card, campground maps, booking links and reviews.</p></div><span class="btn">OPEN CAMPGROUNDS →</span></a>',
    'class="card" href="kpc-campgrounds.html"')
print('::notice title=Campgrounds go-live::' + (', '.join(done) or 'already live'))
