#!/usr/bin/env python3
"""Static checks for the Nov 18 2026 Lounge round, stage 2: the web logger beta (logger-beta/) re-synced from the KPC app 0.9.10 by
.claude/build/logger-beta/sync.sh, with the website's own bits. Browser half: tests/logger_beta_stage2_nov18_browser.js.
Run: python3 tests/test_logger_beta_stage2_nov18.py"""
import os, re, sys, glob, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(R)
fails = 0
def ok(c, m):
    global fails; print(('PASS ' if c else 'FAIL ') + m); fails += 0 if c else 1
rd = lambda p: open(p, encoding='utf-8').read()
L = 'logger-beta/'
ok('0.9.10' in rd(L + 'FROM-APP-COMMIT.txt'), 'FROM-APP-COMMIT.txt: app 0.9.10')
ok("const VER = '0.9.10'" in rd(L + 'kpc-app.js'), "kpc-app.js is the app's 0.9.10")
ok(not glob.glob(L + 'kpc-dv*') and not os.path.exists(L + 'kpc-remote.js') and not os.path.exists(L + 'capacitor.js'), 'no FreeDV, remote or Android bridge files (app only)')
ok(not os.path.exists(L + 'test.js') and not os.path.exists(L + 'radio-check.html'), "no builders' test screens")
h = rd(L + 'kpc-logger-beta.html')
ok(not re.search(r'<script src="(kpc-dv|kpc-dv-ui|kpc-remote|capacitor)\b', h), 'the page loads no FreeDV / remote / Android scripts')
g, p, a = h.find('../kpc-gate.js'), h.find('kpc-web-pre.js'), h.find('<script src="kpc-sec.js')
ok(0 <= g < p < a, 'kpc-web-pre.js runs in <head> after the members lock and before the app scripts')
ok('kpc-web.js?v=' in h and 'kpc-web.css?v=' in h and 'noindex' in h and 'kpc-logger.html?old=1' in h, 'website bits: kpc-web.js / .css, noindex, OFFLINE / OLD LOGGER link')
for f in ['kpc-web.js', 'kpc-web.css', 'kpc-web-pre.js']:
    ok(rd(L + f) == rd('.claude/build/logger-beta/' + f), f + ' matches .claude/build/logger-beta/')
pre = rd(L + 'kpc-web-pre.js')
ok("'kpcAppAutoSpot'" in pre and "o.ask = false" in pre and "'kpcAppDigi'" in pre and "o.showAuto = false" in pre and "o.vmon = false" in pre, 'kpc-web-pre.js turns off auto spot me, AUTO run / hunt / both, hear my processed voice')
css = rd(L + 'kpc-web.css')
ok(all(s in css for s in ['#stAutoSpot', '#dgRun', '#dgHunt', '#dgBoth', '#shShowAuto', '#stVmon', '#stLvlHelp', '[data-lvlh]']), 'kpc-web.css hides those switches and the level helper')
d = rd(L + 'kpc-dsp.js')
ok(not re.search(r'PskRx\s*=|function wsprDecode|const VARI', d), 'kpc-dsp.js: no PSK31 / WSPR code (licence hold)')
big = [f for f in glob.glob(L + '**', recursive=True) if os.path.isfile(f) and os.path.getsize(f) >= 1_000_000]
ok(not big, 'every web logger file is under 1 MB' + (': ' + ', '.join(big) if big else ''))
for f in sorted(glob.glob(L + '*.js')):
    if subprocess.run(['node', '--check', f], capture_output=True).returncode: ok(False, 'node --check ' + f)
ok(True, 'node --check every logger-beta/*.js')
print('\nALL PASS' if not fails else '\n%d FAIL' % fails); sys.exit(1 if fails else 0)
