#!/bin/sh
# Builds BOTH Hunters Lounge pages from main.html (run from the repo root):
#  kpc-hunt.html    = members room copy (noindex; POTA bookmark + hunting log)
#  kpc-hunters.html = public copy (data-public="1": no bookmark, no log, no Top 50)
set -e
python3 .claude/build/assemble.py .claude/build/hunt/main.html kpc-hunt.html "VIP Hunters Lounge | KPC" "Live POTA, WWFF, SOTA, DX and special-event spots for hunters: load your log, hide parks you've worked, new-to-you parks roll across the screen, and log contacts for QRZ."
python3 - <<'P'
s=open('kpc-hunt.html').read()
if 'noindex' not in s: s=s.replace('<meta charset="UTF-8">','<meta charset="UTF-8">\n<meta name="robots" content="noindex,nofollow">',1)
if 'kpc-vip.js' not in s: s=s.replace('<meta name="robots" content="noindex,nofollow">','<meta name="robots" content="noindex,nofollow">\n<script src="kpc-vip.js?v=20261018b"></script>',1)
open('kpc-hunt.html','w').write(s)
P
sed 's/<main id="hl" data-keep-light data-theme="lodge">/<main id="hl" data-keep-light data-theme="lodge" data-public="1">/' .claude/build/hunt/main.html > /tmp/kpc-hunters-main.html
grep -q 'data-public="1"' /tmp/kpc-hunters-main.html
python3 .claude/build/assemble.py /tmp/kpc-hunters-main.html kpc-hunters.html "Hunters Lounge | KPC" "Live POTA, WWFF and SOTA spots with the parks you've already worked tucked away, so the new-to-you ones light up."
# kpc-hunt-need.html = Parks I Need on its own page (members, noindex; Brandon Oct 17), same code with data-page="need"
sed 's/<main id="hl" data-keep-light data-theme="lodge">/<main id="hl" data-keep-light data-theme="lodge" data-page="need">/' .claude/build/hunt/main.html > /tmp/kpc-hunt-need-main.html
grep -q 'data-page="need"' /tmp/kpc-hunt-need-main.html
python3 .claude/build/assemble.py /tmp/kpc-hunt-need-main.html kpc-hunt-need.html "VIP Parks I Need | KPC" "KPC members: every POTA park you still need, state by state, with a satellite state map and the ones on the air right now."
python3 - <<'P'
for f in ('kpc-hunt-need.html',):
    s=open(f).read()
    if 'noindex' not in s: s=s.replace('<meta charset="UTF-8">','<meta charset="UTF-8">\n<meta name="robots" content="noindex,nofollow">',1)
    if 'kpc-vip.js' not in s: s=s.replace('<meta name="robots" content="noindex,nofollow">','<meta name="robots" content="noindex,nofollow">\n<script src="kpc-vip.js?v=20261018b"></script>',1)
    open(f,'w').write(s)
s=open('kpc-hunters.html').read()
# BETA lock (Brandon Oct 17) — remove these two lines when he releases it
if 'noindex' not in s: s=s.replace('<meta charset="UTF-8">','<meta charset="UTF-8">\n<meta name="robots" content="noindex,nofollow">',1)
if 'kpc-vip.js' not in s: s=s.replace('<meta name="robots" content="noindex,nofollow">','<meta name="robots" content="noindex,nofollow">\n<script src="kpc-vip.js?v=20261018b" data-lock="beta"></script>',1)
if 'href="kpc-hunters.html" aria-current' not in s: s=s.replace('href="kpc-hunters.html"','href="kpc-hunters.html" aria-current="page"',1)
open('kpc-hunters.html','w').write(s)
P
# kpc-hunt-cat.html = CAT (radio control) + QRZ auto-send settings (members, noindex; Brandon Oct 17), own source
python3 .claude/build/assemble.py .claude/build/hunt-cat/main.html kpc-hunt-cat.html "VIP Radio Control & QRZ | KPC" "KPC members: let the Hunters Lounge tune your radio when you click a spot, and send each contact to your QRZ logbook."
python3 - <<'P'
s=open('kpc-hunt-cat.html').read()
if 'noindex' not in s: s=s.replace('<meta charset="UTF-8">','<meta charset="UTF-8">\n<meta name="robots" content="noindex,nofollow">',1)
if 'kpc-vip.js' not in s: s=s.replace('<meta name="robots" content="noindex,nofollow">','<meta name="robots" content="noindex,nofollow">\n<script src="kpc-vip.js?v=20261018b"></script>',1)
open('kpc-hunt-cat.html','w').write(s)
P
