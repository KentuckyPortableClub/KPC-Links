#!/usr/bin/env python3
"""Nov 8 (Brandon 4:12 PM CST, t762u): "A, B" in the call box = one log line per call; LOG QSO on every spot opens a quick log
with 59 (phone) / 599 (CW, RTTY, digital) / -10 (FT8, FT4) filled in and editable; ops at the same park within about 1 kHz go in
together ("N4BWD, KQ4HZK"). Same code (kpc-hunt.js) runs the public Hunters Lounge and the VIP Lounge; nothing taken away."""
import json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
src = (ROOT / 'kpc-hunt.js').read_text(encoding='utf-8')
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
def grab(pat):
    m = re.search(pat, src, re.S); check(bool(m), 'found ' + pat[:40]); return m.group(0) if m else ''
parts = [grab(r"  function rstFor\(m\).*?\n  function groupCalls\(s\).*?\n"), grab(r"  const af = .*?\n"), grab(r"  function adMode\(m\).*?\n"), grab(r"  function adif\(L\) \{.*?\n  \}\n")]
js = """const enc = new TextEncoder(), CALL = 'KZ4CP', ST = {KY: 1}, myGrid = () => 'EM78', isQrt = s => !!s.qrt;
const progOf = r => /^[A-Z0-9]{1,4}-\\d{4,5}$/.test(r) ? 'POTA' : /FF-/.test(r) ? 'WWFF' : 'SOTA';
let SP = [];
""" + ''.join(parts) + r"""
const out = {};
out.split = [splitCalls('n4bwd, kq4hzk'), splitCalls('N4BWD,KQ4HZK'), splitCalls(' a1aa ,, A1AA ; k4x '), splitCalls('')];
out.rec = splitRec({ id: 'x', call: 'N4BWD, KQ4HZK', f: '7.2', band: '40m', mode: 'SSB', ref: 'US-5656', d: '20261108', tm: '2215', rs: '57', rr: '59', st: 'KY', name: 'Test Park' });
const a = adif([{ id: 'x', call: 'N4BWD, KQ4HZK', f: '7.2', band: '40m', mode: 'SSB', ref: 'US-5656', d: '20261108', tm: '2215', rs: '57', rr: '59' }, { id: 'y', call: 'W1AW', f: '14.062', band: '20m', mode: 'CW', ref: '', d: '20261108', tm: '2216', rs: '599', rr: '599' }]);
out.adif = { recs: (a.match(/<CALL:\d+>[^ ]+/g) || []), eor: (a.match(/<EOR>/gi) || []).length, pota: (a.match(/<POTA_REF:\d+>US-5656/g) || []).length };
out.rst = ['SSB', 'USB', 'LSB', 'AM', 'FM', 'CW', 'RTTY', 'PSK31', 'JS8', 'FT8', 'FT4'].map(m => m + '=' + rstFor(m));
SP = [{ call: 'N4BWD', khz: 7200, ref: 'US-5656' }, { call: 'KQ4HZK', khz: 7200.6, ref: 'us-5656' }, { call: 'W9ZZ', khz: 7203, ref: 'US-5656' },
      { call: 'K4OT', khz: 7200, ref: 'US-1111' }, { call: 'N0QR', khz: 7200, ref: 'US-5656', qrt: 1 }, { call: 'N4BWD', khz: 7200, ref: 'US-5656' }];
out.grp = [groupCalls(SP[0]), groupCalls(SP[1]), groupCalls(SP[2]), groupCalls(SP[3]), groupCalls({ call: 'DX1A', khz: 14000, ref: '' })];
console.log(JSON.stringify(out));
"""
r = subprocess.run(['node', '-e', js], capture_output=True, text=True, timeout=30)
check(r.returncode == 0, 'node ran the logger code ' + r.stderr[:300])
o = json.loads(r.stdout or '{}')
check(o['split'] == [['N4BWD', 'KQ4HZK'], ['N4BWD', 'KQ4HZK'], ['A1AA', 'K4X'], []], 'comma split: trimmed, upper case, blanks and repeats dropped')
rec = o['rec']
check([x['call'] for x in rec] == ['N4BWD', 'KQ4HZK'] and len({x['id'] for x in rec}) == 2, 'one line per call, each its own id')
check(all(x[k] == rec[0][k] for x in rec for k in ('f', 'band', 'mode', 'ref', 'd', 'tm', 'rs', 'rr', 'st', 'name')), 'every line keeps the same freq, band, mode, park, time and reports')
check(o['adif']['recs'] == ['<CALL:5>N4BWD', '<CALL:6>KQ4HZK', '<CALL:4>W1AW'] and o['adif']['eor'] == 3 and o['adif']['pota'] == 2, 'ADIF: one record per call (old "A, B" lines too)')
check(o['rst'] == ['SSB=59', 'USB=59', 'LSB=59', 'AM=59', 'FM=59', 'CW=599', 'RTTY=599', 'PSK31=599', 'JS8=599', 'FT8=-10', 'FT4=-10'], 'default reports per mode')
check(o['grp'] == ['N4BWD, KQ4HZK', 'KQ4HZK, N4BWD', 'W9ZZ', 'K4OT', 'DX1A'], 'same park within 1 kHz grouped; other park, 3 kHz away, QRT and repeats left out')
# wiring
check(src.count('data-lq=') == 2, 'LOG QSO button on spot cards and table rows')
check("openSheet(Object.assign({}, s, { call: groupCalls(s) }), null, true)" in src, 'LOG QSO opens the quick log with the grouped calls')
check("if (!x && !quick && DOCKON())" in src, 'quick log opens even where a spot tap fills the dock')
check("const CS = splitCalls(call);" in src and "more.forEach(m => Q.q.push(m))" in src, 'log sheet saves one line per call')
check("const CS = splitCalls($('dCall').value);" in src and "for (const call of CS) {" in src, 'the log dock saves one line per call')
check("Q.q = Q.q.flatMap(splitRec)" in src, 'old "A, B" lines in a saved log are split on load')
check("return out.flatMap(splitRec);" in src, 'RESTORE from an ADIF splits "A, B" too')
check("L = (L || []).flatMap(splitRec);" in src, 'download, backup file and QRZ upload all go through the split ADIF')
for f in ['kpc-hunters.html', 'kpc-hunt.html', 'kpc-hunters-need.html', 'kpc-hunt-need.html', 'kpc-beta-room.html', 'kpc-beta-need.html', '.claude/build/hunt/main.html']:
    check('kpc-hunt.js?v=20261108q' in (ROOT / f).read_text(encoding='utf-8'), f + ': new kpc-hunt.js version')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
