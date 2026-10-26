"""RELEASE NIGHT, step 11 (chat 1): new header + menu + footer link on EVERY page. NOT RUN until release night (Thu Oct 29 1:30 AM,
after chat 2 + chat 3). Source: 'FINAL RELEASE RUN SHEET' in .claude/notes/new-chat-starters.md. Same menu for Plan A and Plan B:
kpc-gate.js decides what guests see (locked links hide themselves, empty sections and rows too).

  python3 .claude/build/menu_release.py            dry run: says what it would change, writes nothing
  python3 .claude/build/menu_release.py --apply    rewrites every page

What it does to each page:
  1. HEADER = news.html's header with: top bar 'Parks' -> 'KY Parks' (parks.html), the new See More menu below, aria-current on the
     page's own link. The 3 beta-room pages keep their Hunters Lounge link pointing at kpc-beta-room.html.
  2. FOOTER: 'ABOUT OUR INFORMATION' (kpc-about-info.html) before PRIVACY in the footer link row.
Pages without the standard header/footer (contact-card.html, kpc-maprep.html, finder.html footer) are listed for a hand check.
Map Rep is never in the menu (Brandon Oct 26 4:40 PM: it lives only in the Club Room).
Brandon Oct 26 6:35 PM: top-bar Photos keeps its Google Photos link (the header is copied from news.html, untouched); Videos is in Club;
Weather (Activators Lounge) and Radio Conditions (both Lounges) are not in See More."""
import glob, re, sys

APPLY = '--apply' in sys.argv

# (icon, text, href) or (icon, [(text, href), ...], tail) = one row of small links
MENU = [
    ('Operating', [
        ('&#127890;', 'Activators Lounge', 'kpc-activators-lounge.html'),
        ('&#127919;', 'Hunters Lounge', 'kpc-hunters.html'),
        ('&#127957;', 'Campgrounds &amp; Cabins', 'kpc-campgrounds.html'),
    ]),
    ('Learning', [
        ('&#128251;', 'Antenna &amp; Power Room', 'antennas.html'),
        ('&#127794;', [('POTA', 'kpc-pota-room.html'), ('WWFF', 'kpc-wwff-room.html'), ('SOTA', 'kpc-sota-room.html')], 'Rooms'),
        ('&#127891;', 'Learning Room', 'kpc-learning.html'),
        ('&#129490;', 'Kids Room', 'kpc-kids.html'),
        ('&#128218;', 'Library', 'resources.html'),
    ]),
    ('Club', [
        ('&#128240;', 'News', 'news.html'),
        ('&#129309;', 'Community', 'kpc-community.html'),
        ('&#127909;', 'Videos', 'videos.html'),
        ('&#9997;&#65039;', 'Guestbook', 'kpc-guestbook.html'),
        ('&#127969;', 'Club Room (members)', 'kpc-club.html'),
        ('&#128075;', 'About KPC', 'about.html'),
        ('&#9993;', 'Join KPC', 'join.html'),
        ('&#128172;', 'Contact', 'contact.html'),
    ]),
    ('', [('', [('Tool Box', 'toolbox.html'), ('Find It', 'find.html'), ('About our information', 'kpc-about-info.html')], '')]),
]


def dropdown():
    out = ['<div class="nav-dropdown" role="menu">']
    for label, items in MENU:
        out.append('          <div class="nav-drop-section">')
        if label:
            out.append(f'            <div class="nav-drop-label">{label}</div>')
        for icon, b, c in items:
            if isinstance(b, list):
                ico = f'<span class="ni">{icon}</span>' if icon else ''
                links = ''.join(f'<a href="{h}" role="menuitem">{t}</a>' for t, h in b)
                tail = f'<span class="nm-tail">{c}</span>' if c else ''
                out.append(f'            <div class="nav-multi">{ico}{links}{tail}</div>')
            else:
                out.append(f'            <a href="{c}" role="menuitem"><span class="ni">{icon}</span>{b}</a>')
        out.append('          </div>')
    out.append('        </div>')
    return '\n'.join(out)


H = re.compile(r'<header class="site-nav">.*?</header>', re.S)
DD = re.compile(r'<div class="nav-dropdown" role="menu">.*?\n        </div>(?=\n      </div>\n    </nav>)', re.S)
news = open('news.html', encoding='utf-8').read()
base = H.search(news).group(0).replace(' aria-current="page"', '')
if '<a href="parks.html">KY Parks</a>' in base:
    print('news.html already has the new header: the release menu has been applied. Nothing to do.'); sys.exit(0)
assert '<a href="parks.html">Parks</a>' in base and len(DD.findall(base)) == 1, 'news.html header is not the expected one'
CANON = DD.sub(lambda m: dropdown(), base.replace('<a href="parks.html">Parks</a>', '<a href="parks.html">KY Parks</a>'))


def header_for(page):
    h = CANON
    if page.startswith('kpc-beta-'):
        h = h.replace('href="kpc-hunters.html" role="menuitem"', 'href="kpc-beta-room.html" role="menuitem"')
    # aria-current on the page's own links (top bar + menu)
    return re.sub(r'<a href="' + re.escape(page) + r'"(?=[ >])', lambda m: m.group(0) + ' aria-current="page"', h)


FOOT_OLD = '<a href="kpc-privacy.html">PRIVACY</a>'
FOOT_NEW = '<a href="kpc-about-info.html">ABOUT OUR INFORMATION</a><a href="kpc-privacy.html">PRIVACY</a>'
nf = 0; no_h = []; no_f = []
for f in sorted(glob.glob('*.html')):
    s = open(f, encoding='utf-8').read(); t = s
    if len(H.findall(t)) == 1: t = H.sub(lambda m: header_for(f), t, count=1)
    else: no_h.append(f)
    if 'kpc-about-info.html">ABOUT OUR INFORMATION' not in t:
        fa = re.search(r'<div class="footer-actions">.*?</div>', t, re.S)
        if fa and FOOT_OLD in fa.group(0):
            t = t[:fa.start()] + fa.group(0).replace(FOOT_OLD, FOOT_NEW) + t[fa.end():]
        elif fa and 'kpc-privacy.html' in fa.group(0):   # kpc-maprep.html: its PRIVACY link has target=_blank
            t = t[:fa.start()] + fa.group(0).replace('<a href="kpc-privacy.html"', '<a href="kpc-about-info.html">ABOUT OUR INFORMATION</a><a href="kpc-privacy.html"', 1) + t[fa.end():]
        else: no_f.append(f)
    if t != s:
        nf += 1
        if APPLY: open(f, 'w', encoding='utf-8').write(t)
print(('APPLIED' if APPLY else 'DRY RUN') + f': {nf} pages changed. No standard header (check by hand): {", ".join(no_h) or "none"}. '
      f'No footer link row (check by hand): {", ".join(no_f) or "none"}.')
