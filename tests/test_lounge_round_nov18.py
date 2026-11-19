#!/usr/bin/env python3
"""Static checks for the Nov 18 2026 Lounge round, stage 1: the KPC app 0.9.10 FT8 decoder (kpc-ft8.js + kpc-ft8-wasm.js + kpc-ft8.wasm),
PSK31 and WSPR off the website (licence hold), the app's noise filter (kpc-nr.js) and the licence notices folder.
The browser half is tests/lounge_round_nov18_browser.js. Run: python3 tests/test_lounge_round_nov18.py"""
import os, re, subprocess, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(R)
fails = 0
def ok(c, m):
    global fails; print(('PASS ' if c else 'FAIL ') + m); fails += 0 if c else 1
rd = lambda p: open(p, encoding='utf-8').read()
NEW = 'v=20261118a'
FT8 = ['kpc-hunt.html', 'kpc-hunt-need.html', 'kpc-beta-room.html', 'kpc-beta-need.html', 'kpc-hunters.html', 'kpc-hunters-need.html', 'kpc-logger.html',
       '.claude/build/hunt/main.html', '.claude/build/logger/main.html']
NR = ['kpc-hunt.html', 'kpc-hunt-need.html', 'kpc-hunt-cat.html', 'kpc-beta-room.html', 'kpc-beta-need.html', 'kpc-beta-cat.html', 'kpc-hunters.html',
      'kpc-hunters-need.html', '.claude/build/hunt/main.html']
PUB = ['kpc-hunters.html', 'kpc-hunters-need.html']
for p in FT8:
    t = rd(p)
    w, f = t.find('kpc-ft8-wasm.js?' + NEW), t.find('kpc-ft8.js?' + NEW)
    ok(0 <= w < f and 'kpc-ft8.js?v=20261017a' not in t, p + ': kpc-ft8-wasm.js then kpc-ft8.js, both ?' + NEW)
    ok('kpc-digi.js?' + NEW in t and 'kpc-digi-ui.js?' + NEW in t and 'v=20261018h' not in t, p + ': kpc-digi.js and kpc-digi-ui.js ?' + NEW)
    if p in PUB:
        ok('kpc-logger-ft8.js?v=20261020d' in t and 'kpc-logger-ft8.js?' + NEW not in t, p + ': public page keeps kpc-logger-ft8.js?v=20261020d')
    else:
        ok(re.search(r'kpc-logger-ft8\.js\?v=20261118[a-z]', t) is not None, p + ': kpc-logger-ft8.js?v=20261118a or newer')
for p in NR:
    t = rd(p); ok('kpc-nr.js?' + NEW in t and 'kpc-nr.js?v=20261107a' not in t, p + ': kpc-nr.js?' + NEW)
# PSK31 and WSPR: not on the website
d = rd('kpc-digi.js')
ok(not re.search(r'PskRx|pskTx|VARI\b|wsprDecode|wsprEncode|wsprTx|function fano|function unpack', d), 'kpc-digi.js has no PSK31 / WSPR code')
ok('GPL' not in d.split('(function (G)')[1], 'kpc-digi.js: no GPL code left (only the header says what was taken out)')
r = subprocess.run(['node', '-e', "const D=require('./kpc-digi.js');console.log(Object.keys(D).join(' '))"], capture_output=True, text=True)
ks = r.stdout.split()
ok(r.returncode == 0 and all(k in ks for k in ['RttyRx', 'rttyTx', 'SstvRx', 'sstvTx', 'HellRx', 'hellTx']) and not any(re.search('psk|wspr', k, re.I) for k in ks),
   'kpc-digi.js loads in node: ' + ' '.join(ks))
lf = rd('kpc-logger-ft8.js')
ok('data-f8m="PSK31"' not in lf and 'data-f8m="WSPR"' not in lf, 'kpc-logger-ft8.js: no PSK31 / WSPR mode buttons')
ok("const isDG = () => /^(RTTY|HELL|SSTV)$/.test(S.mode);" in lf, 'kpc-logger-ft8.js: digital screens are RTTY, HELL and SSTV only')
ok("if (/^(PSK31|WSPR)$/.test(S.mode)) S.mode = 'FT8';" in lf and "if (/^(PSK31|WSPR)$/.test(m)) m = 'FT8';" in lf, 'kpc-logger-ft8.js: a saved or asked-for PSK31 / WSPR lands on FT8')
ok("kpc-ft8.wasm?" + NEW in lf, 'kpc-logger-ft8.js asks for kpc-ft8.wasm?' + NEW)
ui = rd('kpc-digi-ui.js')
ok("MODE = /^(RTTY|HELL|SSTV)$/.test(m) ? m : '';" in ui and 'if (!D.PskRx) { psk = null; return; }' in ui, 'kpc-digi-ui.js: PSK31 / WSPR screens never open; no PSK31 decoder needed')
# decoder files from the app
ok(os.path.getsize('kpc-ft8.wasm') == 34085 and 'KPC_FT8_WASM_B64' in rd('kpc-ft8-wasm.js') and 'viaText' in rd('kpc-ft8.js'), 'app 0.9.10 decoder files (kpc-ft8.wasm 34085 bytes, embedded copy, kpc-ft8.js loads it)')
ok('abLevel' in rd('kpc-nr.js'), "kpc-nr.js is the app's (abLevel)")
ok(os.path.isfile('.claude/build/ft8/kpcdx.inc') and os.path.isfile('.claude/build/ft8/build.sh'), '.claude/build/ft8 is the app tools/ft8 (with kpcdx.inc)')
# licence notices
ok(os.path.isfile('notices/README.txt') and os.path.isfile('notices/ft8_lib-MIT.txt') and 'Karlis Goba' in rd('notices/ft8_lib-MIT.txt') + rd('notices/README.txt'), 'notices/ folder with the ft8_lib MIT licence')
ok('href="notices/README.txt"' in lf, 'the FT8 help line links to notices/README.txt')
for p in ['kpc-ft8.js', 'kpc-ft8.wasm', 'kpc-ft8-wasm.js', 'kpc-nr.js', 'kpc-digi.js', 'kpc-digi-ui.js', 'kpc-logger-ft8.js']:
    ok(os.path.getsize(p) < 1_000_000, p + ' is under 1 MB')
for p in ['kpc-digi.js', 'kpc-digi-ui.js', 'kpc-logger-ft8.js', 'kpc-ft8.js', 'kpc-ft8-wasm.js', 'kpc-nr.js']:
    ok(subprocess.run(['node', '--check', p], capture_output=True).returncode == 0, 'node --check ' + p)
print('\nALL PASS' if not fails else '\n%d FAIL' % fails); sys.exit(1 if fails else 0)
