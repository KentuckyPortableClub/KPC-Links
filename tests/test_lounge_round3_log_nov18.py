#!/usr/bin/env python3
"""Lounge round stage 3 (Nov 18 2026), log items from the KPC app 0.9.x, in kpc-hunt.js (Hunters Lounge, VIP Lounge, beta room):
H23 the .adi file is plain ASCII, never FREQ 0, BAND from FREQ; N7 a damaged ADIF record is left out and counted;
H22 a red NOT SAVED line while the browser refuses to save. Runs the page's own adif() / parseAdif() in node.
Run: python3 tests/test_lounge_round3_log_nov18.py"""
import json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
src = (ROOT / 'kpc-hunt.js').read_text(encoding='utf-8')
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
def grab(pat):
    m = re.search(pat, src, re.S); check(bool(m), 'found ' + pat[:40]); return m.group(0) if m else ''
parts = [grab(r"  function rstFor\(m\).*?\n  function groupCalls\(s\).*?\n"), grab(r"  const BANDS = .*?\n  const bandOf = .*?\n"), grab(r"  const af = .*?\n"),
         grab(r"  function adMode\(m\).*?\n"), grab(r"  function adif\(L\) \{.*?\n  \}\n"), grab(r"  const u8 = .*?\n  function take\(.*?\n"), grab(r"  function parseAdif\(t\) \{.*?\n  \}\n")]
js = """const enc = new TextEncoder(), CALL = 'K4TEST', ST = {KY: 1}, myGrid = () => 'EM78', isQrt = s => !!s.qrt;
const progOf = r => /^[A-Z0-9]{1,4}-\\d{4,5}$/.test(r) ? 'POTA' : /FF-/.test(r) ? 'WWFF' : 'SOTA', nref = r => r;
let SP = [];
""" + ''.join(parts) + r"""
const out = {};
const a = adif([
  { id: 'a', call: 'K4TEST', f: '14.074', band: '40m', mode: 'FT8', ref: 'US-0001', d: '20261118', tm: '2200', rs: '-10', rr: '-12', on: 'José Müller', qth: 'Åre' },
  { id: 'b', call: 'W4KIDS', f: '0', band: '20m', mode: 'SSB', ref: '', d: '20261118', tm: '2201', rs: '59', rr: '59' },
  { id: 'c', call: 'K4TEST', f: '', band: '17m', mode: 'CW', ref: '', d: '20261118', tm: '2202', rs: '599', rr: '599' }]);
out.ascii = /^[\x20-\x7e\n]*$/.test(a); out.name = ((a.match(/<NAME:\d+>[^<]*/) || [''])[0]).trim(); out.qth = ((a.match(/<QTH:\d+>[^<]*/) || [''])[0]).trim();
out.freq = a.match(/<FREQ:\d+>[^ ]*/g) || []; out.band = a.match(/<BAND:\d+>[^ ]*/g) || [];
const back = parseAdif('<EOH>\n<CALL:6>K4TEST <QSO_DATE:8>20261118 <TIME_ON:4>2200 <BAND:3>20m <EOR>\n<CALL:6>W4KIDS <TIME_ON:4>2201 <EOR>\n<QSO_DATE:8>20261118 <EOR>\n');
out.back = back.length; out.bad = parseAdif.bad;
const one = parseAdif(a); out.round = one.length; out.roundBad = parseAdif.bad;
console.log(JSON.stringify(out));
"""
r = subprocess.run(['node', '-e', js], capture_output=True, text=True)
check(r.returncode == 0, 'the page code runs in node ' + r.stderr[-300:])
o = json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else {}
check(o.get('ascii') is True, 'H23: the whole .adi file is plain ASCII')
check(o.get('name') == '<NAME:11>Jose Muller' and o.get('qth') == '<QTH:3>Are', 'H23: accented letters go in plain, lengths match: %s / %s' % (o.get('name'), o.get('qth')))
check(o.get('freq') == ['<FREQ:6>14.074'], 'H23: FREQ only where it is known, never 0: %s' % o.get('freq'))
check(o.get('band') == ['<BAND:3>20m', '<BAND:3>20m', '<BAND:3>17m'], 'H23: BAND follows FREQ (14.074 saved as 40m goes out as 20m), else the saved band: %s' % o.get('band'))
check(o.get('back') == 1 and o.get('bad') == 2, 'N7: a record with no date or no call is left out and counted (1 read, 2 left out): %s / %s' % (o.get('back'), o.get('bad')))
check(o.get('round') == 3 and o.get('roundBad') == 0, 'the file the page writes reads back whole (3 contacts, none left out)')
check("damaged line${parseAdif.bad === 1 ? ' was' : 's were'} left out" in src and 'parseAdif.bad = 0;' in src, 'N7: the import message says how many lines were left out')
check('qSave.bad = !lsOk && !IDBok;' in src and 'NOT SAVED: this browser refused to save your log' in src, 'H22: a red NOT SAVED line while neither copy saves')
pages = ['kpc-hunt.html', 'kpc-hunters.html', 'kpc-hunt-need.html', 'kpc-hunters-need.html', 'kpc-beta-room.html', 'kpc-beta-need.html', '.claude/build/hunt/main.html']
check(all('kpc-hunt.js?v=20261119a' in (ROOT / p).read_text(encoding='utf-8') for p in pages), 'every Lounge page and the build source load kpc-hunt.js?v=20261119a')
m = re.search(r"  function fromSota\(x\) \{.*?\n  \}\n", src, re.S)
r2 = subprocess.run(['node', '-e', "const nref = r => r, toMs = t => 0;\n" + (m.group(0) if m else '') + "\nconsole.log(JSON.stringify([1296.2, 14.062, 7.032, 50.13].map(f => fromSota({ frequency: f, activatorCallsign: 'k4test', associationCode: 'W4K', summitCode: 'EC-001' }).khz)))"], capture_output=True, text=True)
check(r2.stdout.strip() == '[1296200,14062,7032,50130]', 'N11: SOTA spots are read as MHz, 23 cm too: ' + (r2.stdout.strip() or r2.stderr[-200:]))
check(subprocess.run(['node', '--check', str(ROOT / 'kpc-hunt.js')], capture_output=True).returncode == 0, 'node --check kpc-hunt.js')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
