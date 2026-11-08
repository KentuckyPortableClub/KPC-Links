#!/usr/bin/env python3
"""Nov 8 (Brandon 8:29 AM CST): the PARK / REF box takes a comma list (two-fers) end to end, and the VIP Lounge gets the
public Hunters Lounge tabs it was missing (Activation Board, Radio Conditions, Happening Now). Nothing taken away."""
import json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
src = (ROOT / 'kpc-hunt.js').read_text(encoding='utf-8')
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
m = re.search(r"  const nref = r => \{.*?\n  \};\n  const progOf = .*?\n.*?  window\.KPCRefs = .*?\n", src, re.S)
check(bool(m), 'nref / progOf / refList found')
js = "const toast = () => {}, window = {};\n" + m.group(0) + """
const L = s => refList(s);
console.log(JSON.stringify({two: L('us-1234,US-5678'), sp: L(' K-1234 ,  US-1234 VE-0042'), mix: L('US-1234, KFF-1234, W4K/EC-001'),
 bad: L('US-1234, PARK, US-12'), empty: L('')}));
"""
r = subprocess.run(['node', '-e', js], capture_output=True, text=True, timeout=30)
check(r.returncode == 0, 'node ran refList ' + r.stderr[:200])
o = json.loads(r.stdout or '{}')
check(o['two']['s'] == 'US-1234, US-5678' and not o['two']['bad'], 'comma list kept, upper-cased, joined with ", "')
check(o['sp']['s'] == 'US-1234, CA-0042' and not o['sp']['bad'], 'K-/VE- cleaned, repeats dropped, spaces ok')
check(o['mix']['ok'] == ['US-1234', 'KFF-1234', 'W4K/EC-001'], 'POTA, WWFF and SOTA refs all pass')
check(o['bad']['bad'] == ['PARK', 'US-12'] and o['bad']['ok'] == ['US-1234'], 'each ref checked; bad ones named')
check(o['empty']['s'] == '' and not o['empty']['bad'], 'empty box = no ref, no warning')
check(src.count("if (refBad(RL, $('fRef'))) return;") == 1 and src.count("if (refBad(RL, $('dRef'))) return;") == 1, 'both log forms stop on a bad ref')
check("ref: refList(o.ref).s" in src, 'spot / CAT quick log uses the same list')
check("af('POTA_REF', pota.join(','))" in src and "af('SIG_INFO', pota.join(','))" in src, 'ADIF (download and QRZ upload) carry every POTA ref')
check(src.count("ref.split(/[ ,]+/).filter(Boolean).forEach(r => { if (!WK.has(r))") == 2, 'every listed park is credited on save')
# lounges in line
tabs = ['kpc-activations.html', 'kpc-space-weather.html', 'kpc-hunt.html#live']
for f in ['kpc-hunt.html', 'kpc-hunt-need.html', 'kpc-hunt-cat.html', 'kpc-top50.html']:
    t = (ROOT / f).read_text(encoding='utf-8'); nav = re.search(r'<nav class="hl-ptabs.*?</nav>', t, re.S).group(0)
    check(all(x in nav for x in tabs + ['kpc-hunt-need.html', 'kpc-top50.html', 'kpc-hunt-cat.html']), f + ': VIP tabs = old ones + board, conditions, live')
v = (ROOT / 'kpc-hunt.html').read_text(encoding='utf-8')
check('<section id="hlLive" hidden></section>' in v and 'id="kpc-vip-live"' in v and 'kpc-live.html?embed=1' in v, 'VIP Happening Now panel')
check('kpc-vip.js' in v, 'VIP lock kept')
pub = (ROOT / 'kpc-hunters.html').read_text(encoding='utf-8')
for s in ['kpc-lounge-tabs.js', 'id="hlRadio"', 'id="hlLive"', 'id="kpc-rel"', 'kpc-nr.js']:
    check(s in pub, 'public Hunters Lounge keeps ' + s)
for f in ['kpc-hunt.html', 'kpc-hunt-need.html', 'kpc-hunters.html', 'kpc-hunters-need.html']:
    _v = re.search(r'kpc-hunt\.js\?v=(\w+)', (ROOT / f).read_text(encoding='utf-8'))   # Nov 8 PM: any version from 20261108b on
    check(bool(_v) and _v.group(1) >= '20261108b', f + ' loads the new kpc-hunt.js')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
