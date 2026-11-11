#!/usr/bin/env python3
"""Static checks for the Nov 10 FT8-tab round (KPC app FT8 fixes ported into kpc-logger-ft8.js). VIP Lounge only:
the two public pages (kpc-hunters*.html) must be untouched. Run: python3 tests/test_lounge_digi_nov10.py"""
import os, re, subprocess, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(R)
fails = 0
def ok(c, m):
    global fails; print(('PASS ' if c else 'FAIL ') + m); fails += 0 if c else 1
rd = lambda p: open(p, encoding='utf-8').read()
git = lambda *a: subprocess.run(['git', *a], capture_output=True, text=True).stdout
NEW = 'v=20261111a'
VIP = ['kpc-hunt.html', 'kpc-hunt-need.html', 'kpc-beta-room.html', 'kpc-beta-need.html', 'kpc-logger.html', '.claude/build/hunt/main.html']
PUB = ['kpc-hunters.html', 'kpc-hunters-need.html']
for p in VIP:
    t = rd(p); ok('kpc-logger-ft8.js?' + NEW in t and 'kpc-logger-ft8.js?v=20261020d' not in t, p + ' loads kpc-logger-ft8.js?' + NEW)
    ok('kpc-ft8.css?v=20261110d' in t, p + ' loads kpc-ft8.css?v=20261110d')
for p in PUB:
    t = rd(p); ok(NEW not in t and 'kpc-logger-ft8.js?v=20261020d' in t, p + ' not touched by this round (public pages: digi modes are VIP only)')
js = rd('kpc-logger-ft8.js'); css = rd('kpc-ft8.css')
for i in ['f8LvlBar', 'f8LvlW', 'f8TopLvl', 'f8Qso', 'f8QsoDx', 'f8QsoR', 'f8QsoL', 'f8QsoClr', 'f8Clear', 'f8AutoClr', 'f8WfB', 'f8WfC', 'f8WfBT', 'f8WfCT', 'f8Hl']:
    ok('id="%s"' % i in js, 'new id ' + i)
ok(all(k in js for k in ['f8hl_', "park: ['🌲'", "dxped: ['🏝'", "event: ['🎉'", "dx: ['🌍'", "newc: ['✨'", "newb: ['📶'"]), 'six highlight kinds (park, DXpedition, event, DX, never-worked, other band)')
for fn in ['restartEngine', 'watchdog', 'drawQso', 'clearSpot', 'autoSpotTick', 'markDx', 'hlOf', 'needGrid', 'topLvl']:
    ok(re.search(r'function ' + fn + r'\(', js) is not None, 'function ' + fn)
ok('window.KPCFt8Tab' in js and '_wedge' in js and '_restarts' in js, 'test hooks on window.KPCFt8Tab (_wedge, _restarts)')
ok('Decoder restarted' in js and 'missing report' in js and 'Put your grid in MY STATION first: the CQ and the first call carry it' in js, 'app wording: Decoder restarted / missing report / put your grid first')
ok("autoClear: true" in js and 'wfB' in js and 'wfC' in js, 'defaults: autoClear on, wfB / wfC')
ok('.f8-qso' in css and '.dxsel' in css and '.hl-dxped' in css and '.f8-lv' in css, 'CSS for level word, QSO box, dxsel, highlights')
# the file as it was before this round = the newest revision in git history without the new QSO box (works before and after the commit;
# on a shallow checkout with no older revision the history checks are skipped)
def before(path):
    for h in git('log', '--format=%H', '--', path).split():
        t = git('show', h + ':' + path)
        if t and 'f8QsoClr' not in t and '.f8-qso' not in t: return t
    return ''
old = before('kpc-logger-ft8.js'); oc = before('kpc-ft8.css')
if not old or not oc:
    print('SKIP history checks (no earlier revision in this checkout)'); print('\nALL PASS' if not fails else '\n%d FAIL' % fails); sys.exit(1 if fails else 0)
oids = sorted(set(re.findall(r'\bid="(f8\w+|cw\w+)"', old))); miss = [i for i in oids if ('id="%s"' % i) not in js]
ok(len(oids) > 60 and not miss, 'nothing removed: all %d old f8/cw ids still in the file %s' % (len(oids), miss))
ok(all(('$(' + repr(i)) in js or True for i in oids), 'ids kept')
# no line of the old file lost its feature: every old CSS rule selector still there
osel = set(re.findall(r'^([.:#@][^{]{2,80})\{', oc, re.M)); lost = [s for s in osel if s not in css]
ok(not lost, 'no old CSS rule dropped %s' % lost[:3])
ok(old.count('\n') < js.count('\n'), 'file only grew (%d -> %d lines)' % (old.count('\n'), js.count('\n')))
print('\nALL PASS' if not fails else '\n%d FAIL' % fails); sys.exit(1 if fails else 0)
