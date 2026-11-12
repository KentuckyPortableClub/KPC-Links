#!/usr/bin/env python3
"""Logger (Nov 11 2026, owner): the beta stays the default; its Log files card links the old logger (offline save lives there for
now), the sync script keeps that link when the app is copied again, and the old logger / kit load package S's new script versions.
Offline, reads files only."""
import os, pathlib, re, sys
HERE = pathlib.Path(os.environ.get('LINKS') or pathlib.Path(__file__).resolve().parent.parent)
fails = 0
def ok(c, m):
    global fails
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails += 1
b = (HERE / 'logger-beta/kpc-logger-beta.html').read_text(encoding='utf-8')
i = b.find('<h2>Log files</h2>'); j = b.find('</section>', i)
card = b[i:j] if i > 0 else ''
ok('<a class="b" href="../kpc-logger.html?old=1">' in card and 'no signal lives in the old logger for now' in card, 'beta Log files card: OFFLINE / OLD LOGGER link to ../kpc-logger.html?old=1 with the one-line note')
ok((HERE / 'logger-beta/../kpc-logger.html').resolve() == (HERE / 'kpc-logger.html').resolve() and (HERE / 'kpc-logger.html').is_file(), 'the link resolves to kpc-logger.html from the logger-beta folder')
old = (HERE / 'kpc-logger.html').read_text(encoding='utf-8')
ok(re.search(r'if\(!/\[\?&\]old=1/\.test\(location\.se', old) is not None, 'kpc-logger.html still opens the beta unless ?old=1')
ok('kpc-logger.js?v=20261111s' in old, 'kpc-logger.html loads kpc-logger.js?v=20261111s')
ok('kpc-kit.js?v=20261111s' in (HERE / 'kpc-kit.html').read_text(encoding='utf-8'), 'kpc-kit.html loads kpc-kit.js?v=20261111s')
s = (HERE / '.claude/build/logger-beta/sync.sh').read_text(encoding='utf-8')
ok("kpc-logger.html?old=1" in s and "'kpc-logger.html?old=1' not in s" in s, 'sync.sh puts the link back after an app sync (once)')
print('SOME FAILED' if fails else 'ALL PASSED')
sys.exit(1 if fails else 0)
