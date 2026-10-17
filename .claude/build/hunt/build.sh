#!/bin/sh
# Builds BOTH Hunters Lounge pages from main.html (run from the repo root):
#  kpc-hunt.html    = members room copy (noindex; POTA bookmark + hunting log)
#  kpc-hunters.html = public copy (data-public="1": no bookmark, no log, no Top 50)
set -e
python3 .claude/build/assemble.py .claude/build/hunt/main.html kpc-hunt.html "Hunters Lounge | KPC" "Live POTA, WWFF, SOTA, DX and special-event spots for hunters: load your log, hide parks you've worked, new-to-you parks roll across the screen, and log contacts for QRZ."
python3 - <<'P'
s=open('kpc-hunt.html').read()
if 'noindex' not in s: s=s.replace('<meta charset="UTF-8">','<meta charset="UTF-8">\n<meta name="robots" content="noindex,nofollow">',1)
open('kpc-hunt.html','w').write(s)
P
sed 's/<main id="hl" data-keep-light data-theme="lodge">/<main id="hl" data-keep-light data-theme="lodge" data-public="1">/' .claude/build/hunt/main.html > /tmp/kpc-hunters-main.html
grep -q 'data-public="1"' /tmp/kpc-hunters-main.html
python3 .claude/build/assemble.py /tmp/kpc-hunters-main.html kpc-hunters.html "Hunters Lounge | KPC" "Live POTA, WWFF and SOTA spots with the parks you've already worked tucked away, so the new-to-you ones light up."
