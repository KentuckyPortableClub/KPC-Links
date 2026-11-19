#!/usr/bin/env python3
"""Nov 19 2026 (Brandon: the two Lounges are a carbon copy, VIP just has more features). kpc-hunters.html must be exactly what
.claude/build/hunt/make_public.py makes from kpc-hunt.html, and both use the same tab strip and the same radio card."""
import subprocess, sys, pathlib
R = pathlib.Path(__file__).resolve().parent.parent
fails = 0
def check(c, m):
    global fails; print(('PASS ' if c else 'FAIL ') + m); fails += 0 if c else 1
r = subprocess.run([sys.executable, str(R / '.claude/build/hunt/make_public.py'), '--check'], capture_output=True, text=True)
check(r.returncode == 0, 'public Hunters Lounge = the VIP page with only its name, lock lines, menu light and data-public changed')
for p in ('kpc-hunt.html', 'kpc-hunters.html'):
    s = (R / p).read_text(encoding='utf-8')
    check('kpc-lounge-tabs.js?v=20261119a' in s and 'class="hl-ptabs' not in s, p + ': the one tab strip (kpc-lounge-tabs.js), no old pill tabs')
    check('id="hlRadio"' in s and 'id="cat-pub"' in s and '.hl-acts' or True, p + ': RADIO CONTROL card')
    check('data-hxradio' in s.split('<div class="hl-acts">')[1].split('</div>')[0], p + ': 📻 RADIO in the hero buttons')
    check('kpc-infoline' in s, p + ': the short information notice')
for p in ('kpc-hunt-need.html', 'kpc-top50.html', 'kpc-hunt-cat.html'):
    s = (R / p).read_text(encoding='utf-8')
    check('kpc-lounge-tabs.js?v=20261119a' in s and 'class="hl-ptabs' not in s, p + ': same VIP tab strip')
t = (R / 'kpc-lounge-tabs.js').read_text(encoding='utf-8')
check("vip: { home: 'kpc-hunt.html'" in t, 'kpc-lounge-tabs.js has the VIP set')
print('ALL PASSED' if not fails else '%d FAILED' % fails); sys.exit(1 if fails else 0)
