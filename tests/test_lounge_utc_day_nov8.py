#!/usr/bin/env python3
"""Nov 8 (Brandon 7:43 AM CST): Hunter's Lounge park states by UTC day: today (greyed, HUNTED TODAY (UTC)),
worked before (normal card, WORKED BEFORE), never worked (NEW PARK). The date is worked out on every render."""
import json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
src = (ROOT / 'kpc-hunt.js').read_text(encoding='utf-8')
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
m = re.search(r"  const parkState = .*?\n  const psCls = .*?\n  const psBadge = .*?: '';\n", src, re.S)
check(bool(m), 'parkState / psCls / psBadge found')
u = re.search(r"  const utc = d => .*?\n", src)
js = """
const hasLog = () => true, WK = new Set(['US-0001']);
const Q = {q: [{d: '20261108', ref: 'US-0002', call: 'K4A'}, {d: '20261107', ref: 'US-0003,US-0004', call: 'K4B'}, {d: '20261108', ref: 'us-0005 US-0006', call: 'K4C'}]};
""" + u.group(0) + m.group(0) + """
const at = new Date(Date.UTC(2026, 10, 8, 23, 59)), nx = new Date(Date.UTC(2026, 10, 9, 0, 0, 5)), S = r => ({ref: r});
console.log(JSON.stringify({
 today: parkState(S('US-0002'), at), multi: parkState(S('US-0006'), at), lower: parkState(S('US-0005'), at),
 rolled: parkState(S('US-0002'), nx), before_wk: parkState(S('US-0001'), at), before_log: parkState(S('US-0004'), at),
 neu: parkState(S('US-9999'), at), noref: parkState({}, at), cls_t: psCls('today'), cls_b: psCls('before'), b_t: psBadge('today'), b_b: psBadge('before'), b_n: psBadge('new')}));
"""
r = subprocess.run(['node', '-e', js], capture_output=True, text=True, timeout=30)
check(r.returncode == 0, 'node ran the helpers ' + r.stderr[:200])
o = json.loads(r.stdout or '{}')
check(o.get('today') == 'today', 'a park logged today (UTC) is HUNTED TODAY')
check(o.get('multi') == 'today' and o.get('lower') == 'today', 'multi-park and lower-case refs count')
check(o.get('rolled') == 'before', 'after 0000 UTC the same park is WORKED BEFORE (no reload: date read per call)')
check(o.get('before_wk') == 'before' and o.get('before_log') == 'before', 'POTA list or an older log entry = WORKED BEFORE')
check(o.get('neu') == 'new' and o.get('noref') == '', 'never worked = NEW PARK; no ref = no state')
check(' worked' in o.get('cls_t', '') and 'worked' not in o.get('cls_b', ''), 'only today is greyed (worked class)')
check('HUNTED TODAY (UTC)' in o.get('b_t', '') and 'WORKED BEFORE' in o.get('b_b', '') and 'NEW PARK' in o.get('b_n', ''), 'badge texts')
check(src.count('parkState(s)') == 3, 'card, row and list rows all use parkState')
check('utcRollover' in src and 'atno' in src and 'const isNew = s =>' in src, 'UTC rollover redraw; ATNO and new-to-me logic kept')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
