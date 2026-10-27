"""RELEASE NIGHT, step 11 (chat 1): the SHORT information line on every tool, guide and map page that shows boundaries, pins, access
points, closures, campgrounds or park details (CLAUDE.md 'SITE-WIDE INFORMATION NOTICE'). It links to kpc-about-info.html, which only
goes public at release, so this runs on release night together with menu_release.py and release_public.py. NOT RUN before then.

  python3 .claude/build/info_line_release.py            dry run
  python3 .claude/build/info_line_release.py --apply    write

Where it goes: inside the page's existing yellow 'We're volunteers…' box (kpc-disclaim) when it has one, otherwise as the same kind
of box just above the footer. Pages that already carry the line are skipped, so it is safe to run twice. Overlap pages need the
2-fer notice IN ADDITION (not added here). NEW pages that show park info must carry the line from the start."""
import os, re, sys

APPLY = '--apply' in sys.argv
LINE = ('ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go. '
        '<a href="kpc-about-info.html" style="color:#1d5a3a;font-weight:700">About our information</a>')
MARK = 'Maps and park info are a planning aid'
PAGES = [
    # Kentucky Parks + Kentucky map tools
    'parks.html', 'kentucky-parks.html', 'finder.html', 'kpc-planner.html', 'kpc-park-control.html', 'kpc-lookup.html', 'kpc-checker.html',
    # all-states / world tools (Activators Lounge doors)
    'kpc-planner-us.html', 'kpc-in-park.html', 'kpc-kit.html', 'kpc-park-info.html', 'kpc-park-sheet.html', 'kpc-access-finder.html',
    'kpc-access-finder-classic.html', 'kpc-rare.html', 'kpc-tracker.html', 'kpc-sota.html', 'kpc-sota-az.html', 'kpc-activators-lounge.html',
    # guides
    'kpc-guide-pota.html', 'kpc-guide-sota.html', 'kpc-guide-wwff.html', 'kpc-guide-top25.html', 'kpc-rules-you-should-know.html',
    # park details from members, camping, owners, activations
    'kpc-park-notes.html', 'kpc-park-notes-us.html', 'kpc-campgrounds.html', 'kpc-activations.html', 'kpc-ky-pva.html',
    # Brandon Oct 26 5:50 PM: the New-to guides and On The Air Now (the program rooms carry it from make_rooms.py)
    'kpc-new-to-pota.html', 'kpc-new-to-wwff.html', 'kpc-new-to-sota.html', 'kpc-spots.html', 'kpc-pota-room.html', 'kpc-wwff-room.html', 'kpc-sota-room.html',
    # members' maps
    'kpc-multi-park-spots.html', 'kpc-club.html',
    # Brandon/chat 8 Oct 26: Find It lists park tools, so it carries the line too
    'find.html',
]
BOX = ('<aside class="kpc-disclaim kpc-info" role="note" style="max-width:1160px;margin:18px auto;padding:0 16px;box-sizing:border-box">'
       '<div style="background:#fff8e6;border:1px solid #d5a63a;border-left:5px solid #d5a63a;border-radius:8px;padding:12px 16px;'
       'color:#1c1c1c;font:14px/1.55 Arial,Helvetica,sans-serif">' + LINE + '</div></aside>\n')
done, skip, miss, how = [], [], [], {}
for f in PAGES:
    if not os.path.exists(f): miss.append(f); continue
    s = open(f, encoding='utf-8').read()
    if MARK in s: skip.append(f); continue
    if 'http-equiv="refresh"' in s: skip.append(f + ' (redirect)'); continue
    m = re.search(r'(<aside class="kpc-disclaim"[^>]*><div[^>]*>)(.*?)(</div></aside>)', s, re.S)
    if m:
        t = s[:m.end(2)] + '<br>' + LINE + s[m.end(2):]; how[f] = 'in box'
    else:
        i = s.find('<footer')
        if i < 0: i = s.rfind('</body>')
        if i < 0: miss.append(f); continue
        t = s[:i] + BOX + s[i:]; how[f] = 'new box'
    done.append(f)
    if APPLY: open(f, 'w', encoding='utf-8').write(t)
print(('APPLIED' if APPLY else 'DRY RUN') + f': {len(done)} pages ' + ', '.join(f'{f} ({how[f]})' for f in done))
print(f'already had it: {", ".join(skip) or "none"}; missing file / no spot: {", ".join(miss) or "none"}')
