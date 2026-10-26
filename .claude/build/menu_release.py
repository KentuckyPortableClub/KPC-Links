"""RELEASE-NIGHT MENU (chat 1). Replaces the See More drop-down on every page with the new menu from
.claude/notes/new-chat-starters.md ('SITE REORGANIZATION PLAN' + 'DECIDED Oct 26'). NOT RUN until Brandon says go.

  python3 .claude/build/menu_release.py            dry run: counts what it would change, writes nothing
  python3 .claude/build/menu_release.py --apply    rewrites the menu block in every page

Menu (top bar is untouched):
  OPERATING  Activators Lounge, Hunters Lounge, Campgrounds & Cabins, Weather, Radio Conditions   (Map Room retires into the Activators Lounge)
  LEARNING   Antenna & Power Room, POTA / WWFF / SOTA Rooms (one row of 3 links), Learning Room, Kids Room, Library, Videos
  CLUB       News, Community, Guestbook / Members (one row of 2 links), About, Join, Contact
  small      Tool Box, Find It, Privacy   (one row)
Pages found in the new menu get aria-current="page" on their own item. Needs the .nav-multi rules in kpc-nav.css
(already added, harmless until the menu uses them). Run it from the repo root, then bump nothing: the menu is plain HTML."""
import glob, re, sys

APPLY = '--apply' in sys.argv

# (label, [(emoji codes, text, href)...])  -- an entry with a list of (text, href) pairs is a row of small links
MENU = [
    ('Operating', [
        ('&#127890;', 'Activators Lounge', 'kpc-activators-lounge.html'),
        ('&#127919;', 'Hunters Lounge', 'kpc-hunters.html'),
        ('&#127957;', 'Campgrounds &amp; Cabins', 'kpc-campgrounds.html'),
        ('&#127783;', 'Weather', 'kpc-weather.html'),
        ('&#128246;', 'Radio Conditions', 'kpc-space-weather.html'),
    ]),
    ('Learning', [
        ('&#128251;', 'Antenna &amp; Power Room', 'antennas.html'),
        ('&#127794;', [('POTA', 'kpc-pota-room.html'), ('WWFF', 'kpc-wwff-room.html'), ('SOTA', 'kpc-sota-room.html')], 'Rooms'),
        ('&#127891;', 'Learning Room', 'kpc-learning.html'),
        ('&#129490;', 'Kids Room', 'kpc-kids.html'),
        ('&#128218;', 'Library', 'resources.html'),
        ('&#127909;', 'Videos', 'videos.html'),
    ]),
    ('Club', [
        ('&#128240;', 'News', 'news.html'),
        ('&#129309;', 'Community', 'kpc-community.html'),
        ('&#9997;&#65039;', [('Guestbook', 'kpc-guestbook.html'), ('Members', 'members.html')], ''),
        ('&#128075;', 'About KPC', 'about.html'),
        ('&#9993;', 'Join KPC', 'join.html'),
        ('&#128172;', 'Contact', 'contact.html'),
    ]),
    ('', [   # small links, one row, no heading
        ('', [('Tool Box', 'toolbox.html'), ('Find It', 'find.html'), ('Privacy', 'kpc-privacy.html')], ''),
    ]),
]


def block(page):
    def cur(h): return ' aria-current="page"' if h == page else ''
    out = ['<div class="nav-dropdown" role="menu">']
    for label, items in MENU:
        out.append('          <div class="nav-drop-section">')
        if label:
            out.append(f'            <div class="nav-drop-label">{label}</div>')
        for it in items:
            if isinstance(it[1], list):
                icon, links, tail = it
                a = ''.join(f'<a href="{h}" role="menuitem"{cur(h)}>{t}</a>' for t, h in links)
                ico = f'<span class="ni">{icon}</span>' if icon else ''
                tl = f'<span class="nm-tail">{tail}</span>' if tail else ''
                out.append(f'            <div class="nav-multi">{ico}{a}{tl}</div>')
            else:
                icon, text, href = it
                out.append(f'            <a href="{href}" role="menuitem"{cur(href)}><span class="ni">{icon}</span>{text}</a>')
        out.append('          </div>')
    out.append('        </div>')
    return '\n'.join(out)


PAT = re.compile(r'<div class="nav-dropdown" role="menu">.*?\n        </div>(?=\n      </div>\n    </nav>)', re.S)
done = skipped = same = 0
odd = []
for f in sorted(glob.glob('*.html')):
    s = open(f, encoding='utf-8').read()
    ms = PAT.findall(s)
    if len(ms) != 1:
        skipped += 1; odd.append(f); continue
    new = PAT.sub(lambda m: block(f), s, count=1)
    if new == s: same += 1; continue
    done += 1
    if APPLY: open(f, 'w', encoding='utf-8').write(new)
print(('APPLIED' if APPLY else 'DRY RUN'), f'- menu rewritten on {done} pages, unchanged {same}, no standard menu block on {len(odd)}: {", ".join(odd) or "none"}')
