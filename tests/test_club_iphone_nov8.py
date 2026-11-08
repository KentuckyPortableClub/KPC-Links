#!/usr/bin/env python3
"""Nov 8 (Brandon 11:00 AM CST: "make it where the club can use the iPhone remote"): Club Room card for the iPhone remote.
Way 1 same Wi-Fi (listen + control), way 2 Tailscale (talk, away from home), pair code + APPROVE, Add to Home Screen, the beta
site, KPC App 0.8.0 or newer on the PC. Every other Club Tools card stays."""
import pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
s = (ROOT / 'kpc-club.html').read_text(encoding='utf-8')
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
m = re.search(r'<div class="cr-app" id="crIphone">.*?</details>.*?</div>', s, re.S)
check(bool(m), 'iPhone card present')
c = m.group(0) if m else ''
check('Way 1' in c and 'same Wi-Fi' in c and ':8731/phone/' in c and "can't talk" in c, 'way 1: same Wi-Fi, listen and control, no talking')
check('Way 2' in c and 'Tailscale' in c and 'tailscale serve --bg 8731' in c and 'away from home' in c and 'TALK' in c, 'way 2: Tailscale, talk, away from home')
check('6-digit pair code' in c and '✓ APPROVE' in c, 'pair code + APPROVE')
check('Add to Home Screen' in c, 'Add to Home Screen')
check('KPC App 0.8.0 or newer on the PC' in c, 'needs KPC App 0.8.0 or newer on the PC')
check('https://kentuckyportableclub.github.io/KPC-iPhone-beta/' in c, 'links the beta site')
check(not re.search(r'\b(bot|agent|AI)\b', re.sub(r'<[^>]+>', ' ', c)), 'no bot wording')
check('id="crAppBeta"' in s and s.count('class="cr-app') >= 10, 'app beta card and the other cards kept')
for h in ['kpc-logger.html', 'kpc-adif.html', 'kpc-hunt.html', 'kpc-top50.html', 'kpc-recap.html', 'kpc-maprep.html', 'kpc-map-coverage.html', 'kpc-control.html']:
    check(h in s, 'kept: ' + h)
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
