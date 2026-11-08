#!/usr/bin/env python3
"""Nov 8 (Brandon 9:30 AM CST): Club Room card for the KPC App beta, linking to the app-beta-0.7.9 release and its Android /
Windows files. iPhone and Mac come later. The other Club Tools cards stay."""
import pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
s = (ROOT / 'kpc-club.html').read_text(encoding='utf-8')
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
B = 'https://github.com/KentuckyPortableClub/KPC-Links/releases'
m = re.search(r'<div class="cr-app cr-tap" id="crAppBeta">.*?</div>', s)
check(bool(m), 'app beta card present')
c = m.group(0) if m else ''
check(B + '/tag/app-beta-0.7.9' in c, 'links the release page')
check(B + '/download/app-beta-0.7.9/KPC-App-beta-android-0.7.9.apk' in c and B + '/download/app-beta-0.7.9/KPC-App-beta-windows-0.7.9-setup.exe' in c, 'direct Android and Windows files')
check('iPhone and Mac come later' in c and 'beta' in c.lower(), 'beta + iPhone / Mac later')
for h in ['kpc-logger.html', 'kpc-adif.html', 'kpc-hunt.html', 'kpc-top50.html', 'kpc-maprep.html', 'kpc-overlap-finder.html']:
    check(h in s, 'kept: ' + h)
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
