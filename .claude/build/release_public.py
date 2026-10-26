"""RELEASE NIGHT, step 11 (chat 1): what guests can open. NOT RUN until release night (Thu Oct 29 1:30 AM), after chat 2 (Map Room) and
chat 3 (Lounges). Source: 'FINAL RELEASE RUN SHEET' + 'RELEASE = GO, PLAN A' in .claude/notes/new-chat-starters.md.

  python3 .claude/build/release_public.py A            dry run, Plan A (the whole Lounge + all map tools public)
  python3 .claude/build/release_public.py B            dry run, Plan B (only the Lounge page + About our information)
  python3 .claude/build/release_public.py A --apply    do it

It (1) adds pages to PUBLIC in kpc-gate.js, (2) removes guest SWAPs / LABELs (Plan A), (3) drops the noindex tag from the newly public
pages, (4) Plan A: kentucky-parks.html becomes a small redirect to parks.html (stays public so old links work), (5) bumps kpc-gate.js?v=
on every page. Run menu_release.py --apply in the same pass. Spot Me, the Club Room, the new learning rooms, Map Rep, the 2-fer pages,
VIP, Logger, Top 50, Recap stay members-only (not touched here)."""
import glob, re, sys

PLAN = (sys.argv[1] if len(sys.argv) > 1 else '').upper()
APPLY = '--apply' in sys.argv
if PLAN not in ('A', 'B'): sys.exit('say A or B: python3 .claude/build/release_public.py A [--apply]')

B_PUBLIC = ['kpc-activators-lounge.html', 'kpc-about-info.html', 'find.html']   # find.html: Brandon Oct 26 6:45 PM (guests get the search icon)
A_PUBLIC = B_PUBLIC + [
    # all-states / world tools in the Lounge
    'kpc-rare.html', 'kpc-guide-top25.html', 'kpc-tracker.html', 'kpc-sota.html', 'kpc-sota-az.html', 'kpc-park-info.html',
    'kpc-in-park.html', 'kpc-kit.html', 'kpc-park-sheet.html', 'kpc-access-finder.html', 'kpc-weather.html', 'kpc-space-weather.html',
    'kpc-band-plan.html', 'kpc-rules-you-should-know.html', 'kpc-new-to-pota.html', 'kpc-new-to-wwff.html', 'kpc-new-to-sota.html',
    'kpc-pota-room.html', 'kpc-wwff-room.html', 'kpc-sota-room.html',
    # Kentucky map tools + the full Kentucky Parks page
    'finder.html', 'kpc-planner.html', 'kpc-lookup.html', 'kpc-checker.html', 'parks.html',
    # Brandon Oct 26 4:36 PM
    'kpc-activations.html', 'kpc-live.html',
    # retired Map Room = a pointer to the Lounge; public so old links land somewhere
    'kpc-map-room.html',
]
ADD = A_PUBLIC if PLAN == 'A' else B_PUBLIC
# Safety (HQ Oct 26): the Map Room pointer (chat 2, release step 9) must be in BEFORE anything goes public.
if 'EVERY MAP TOOL IN ONE PLACE' in open('kpc-map-room.html', encoding='utf-8').read():
    sys.exit('STOP: kpc-map-room.html is still the old Map Room. Chat 2 swaps in the pointer page first (release step 9), then run this again.')
SWAP_DROP = ['parks.html', 'finder.html', 'kpc-planner.html', 'kpc-map-room.html', 'kpc-live.html'] if PLAN == 'A' else []
NEWV = '20261029a'
log = []

# 1 + 2: kpc-gate.js
g = open('kpc-gate.js', encoding='utf-8').read(); g0 = g
m = re.search(r"var PUBLIC = \[(.*?)\];", g, re.S)
have = re.findall(r"'([^']+)'", m.group(1))
new = [p for p in ADD if p not in have]
if new:
    body = m.group(1).rstrip()
    body += ",\n    /* release Oct 29 2026 (Plan " + PLAN + ") */ " + ", ".join("'" + p + "'" for p in new)
    g = g[:m.start(1)] + body + g[m.end(1):]
log.append(f'PUBLIC +{len(new)}: {", ".join(new) or "nothing new"}')
for f in SWAP_DROP:
    g2 = re.sub(r"\s*'" + re.escape(f) + r"':\s*'[^']*',?", '', g)
    if g2 != g: log.append(f'SWAP/LABEL removed: {f}')
    g = g2
g = re.sub(r",(\s*\})", r"\1", g)          # no trailing comma left in SWAP / LABEL
if APPLY and g != g0: open('kpc-gate.js', 'w', encoding='utf-8').write(g)

# 3: noindex off the newly public pages
ROB = re.compile(r'<meta name="robots" content="noindex[^"]*">\n?')
for f in ADD:
    s = open(f, encoding='utf-8').read(); t = ROB.sub('', s)
    if t != s:
        log.append(f'noindex dropped: {f}')
        if APPLY: open(f, 'w', encoding='utf-8').write(t)

# 4: kentucky-parks.html -> parks.html (Plan A)
if PLAN == 'A':
    REDIR = ('<!DOCTYPE html>\n<html lang="en" data-kpc-public>\n<head>\n<meta charset="UTF-8">\n'
             '<title>Kentucky Parks | KPC</title>\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
             '<link rel="canonical" href="https://kentuckyportableclub.github.io/KPC-Links/parks.html">\n'
             '<meta http-equiv="refresh" content="0; url=parks.html">\n'
             '<script>location.replace("parks.html"+location.search+location.hash);</script>\n'
             '<style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#070707;color:#f3e6c8;font:16px Arial,sans-serif}a{color:#f0c96b}</style>\n'
             '</head>\n<body><p>Kentucky Parks has moved: <a href="parks.html">open Kentucky Parks</a>.</p></body>\n</html>\n')
    log.append('kentucky-parks.html -> redirect to parks.html')
    if APPLY: open('kentucky-parks.html', 'w', encoding='utf-8').write(REDIR)

# 5: cache-bust kpc-gate.js everywhere
n = 0
for f in glob.glob('*.html'):
    s = open(f, encoding='utf-8').read(); t = re.sub(r'kpc-gate\.js\?v=\w+', 'kpc-gate.js?v=' + NEWV, s)
    if t != s:
        n += 1
        if APPLY: open(f, 'w', encoding='utf-8').write(t)
log.append(f'kpc-gate.js?v={NEWV} on {n} pages')
print(('APPLIED' if APPLY else 'DRY RUN') + f' Plan {PLAN}:\n  ' + '\n  '.join(log))
