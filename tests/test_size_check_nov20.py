#!/usr/bin/env python3
"""Size check (owner 20 Nov 2026, 4:52 AM: hold parks that do not pass). Invented parks only: no saved key, no acres list.
The measured outline is compared with an official size at 0.33x to 3x. Hold comes from the switch file, per state, and
only the size line holds. Run: python3 tests/test_size_check_nov20.py"""
import json, os, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
import kpc_area_hash as AH  # noqa: E402
R = []
# kpc_us_key.py runs the builder at import. Exec only the two helpers (same rule as test_us_layer_page_cap_nov10.py).
_src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
_ns = {'KR': KR, 'os': os, 'json': json, 'P_ALL': {}, 'notice': lambda *a, **k: None, '_tags': lambda t: set(), '_kr': lambda name: False}
exec(compile(_src[_src.find('ACRES_OFF = None'):_src.find('P_ALL = {}')], 'kpc_us_key.py', 'exec'), _ns)
_official_acres, _selfchk = _ns['_official_acres'], _ns['_selfchk']
def check(ok, what): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + what)

def park(ac, rows, **k):
    p = {'n': 'Invented Park', 't': 'State Park', 'm': rows, 'c': [], 'ac': ac}
    p.update(k)
    return p

row = lambda ac: [1, 'Invented record', ac, 'name']

# --- the band uses the measured outline, not the sum of the rows ---
inside = KR.self_checks('US-1', park(100, [row(1000), row(1000)]), None, 100)
check(not any(b.startswith('acres: measured') for b in inside), 'measured 100 vs official 100 is inside the band even when the rows add to 2,000')
low = KR.self_checks('US-1', park(32, [row(100)]), None, 100)
check(any('outside 0.33x-3x' in b and 'name and kind' in b for b in low), 'measured 32 vs official 100 (0.32x) is outside, and the reason says the size was matched by name and kind')
edge_lo = KR.self_checks('US-1', park(33, [row(1)]), None, 100)
edge_hi = KR.self_checks('US-1', park(300, [row(1)]), None, 100)
check(not any(b.startswith('acres: measured') for b in edge_lo + edge_hi), '0.33x and 3x exactly are inside the band')
high = KR.self_checks('US-1', park(301, [row(100)]), None, 100)
check(any(b.startswith('acres: measured') for b in high), 'measured 301 vs official 100 (3.01x) is outside')
no_size = KR.self_checks('US-1', park(10, [row(10)]), None, None)
no_ac = KR.self_checks('US-1', {'n': 'Invented Park', 't': 'State Park', 'm': [row(10000), row(10000)], 'c': []}, None, 100)
check(not any(b.startswith('acres: measured') for b in no_size), 'no official size: no size line (a park with no official size is not held)')
check(not any(b.startswith('acres: measured') for b in no_ac), 'no measured outline: the row sum is not used, so two layers of the same land are not a size failure')
kind = KR.self_checks('US-1', park(100, [row(100)]), None, 100, kind_ok=lambda t, nm: False)
check(any(b.startswith('layer kind:') for b in kind) and not any(b.startswith('acres: measured') for b in kind), 'a layer-kind note is still reported, and it is not a size line')

# --- hold is reachable from the switch file, per state; an environment value still wins ---
d = pathlib.Path(tempfile.mkdtemp()); f = d / 'sw.json'
f.write_text(json.dumps({'switches': {'KPC_SELF_CHECKS': {'on': ['US-OH'], 'hold': ['ZZ']}}}))
P = str(f)
check(KR.setting('KPC_SELF_CHECKS', env={}, area='ZZ', path=P) == 'hold', 'a state on the hold list reads as hold')
check(KR.setting('KPC_SELF_CHECKS', env={}, area='OH', path=P) == '1', 'a state on the on list still reads as report (1), not hold')
check(KR.setting('KPC_SELF_CHECKS', env={}, area='TN', path=P) == '0', 'a state on neither list is off')
check(KR.setting('KPC_SELF_CHECKS', env={}, path=P) == '0', 'calling setting() with no state does not turn hold on')
check(KR.setting('KPC_SELF_CHECKS', env={'KPC_SELF_CHECKS': 'report'}, area='ZZ', path=P) == 'report', 'an environment value still wins over the hold list')
check('KPC_SELF_CHECKS' in KR.areas_on('ZZ', path=P) and 'KPC_SELF_CHECKS' in KR.areas_on('OH', path=P), 'hold counts as on for that state (the area hash must see it)')
sl = AH.switch_slice(json.loads(f.read_text()), {'ZZ', 'OH', 'TN'})
check(sl == {'OH': ['KPC_SELF_CHECKS'], 'ZZ': ['KPC_SELF_CHECKS']}, f'the area hash slice treats hold as on, once ({sl})')
real = json.loads((ROOT / '.github/key-switches.json').read_text())
check(real['switches']['KPC_SELF_CHECKS']['hold'] == [] and real['switches']['KPC_SELF_CHECKS']['on'] == [], 'the committed size check is still off (empty hold list)')
b = d / 'bad-hold.json'; b.write_text('{"switches": {"KPC_SELF_CHECKS": {"on": [], "hold": "ZZ"}}}')
try: KR.switch_file(str(b)); ok = False
except KR.SwitchFileError: ok = True
check(ok, 'a hold list that is not a list of areas raises (the build stops)')

# --- hold moves only the size line; invented park, switch file names the state ---
old_sw, old_env = KR.SWITCH_FILE, os.environ.get('KPC_SELF_CHECKS')
os.environ.pop('KPC_SELF_CHECKS', None)
try:
    KR.SWITCH_FILE = P
    KR._SW.pop(P, None); KR._HOLD.pop(P, None)
    _ns['ACRES_OFF'] = {'US-1': 100.0, 'US-2': 100.0, 'US-3': 100.0}
    big = park(10, [row(10)])          # 0.10x: size line
    kind_only = park(100, [row(100)])  # inside the band: the join stays
    _selfchk('ZZ', {'US-1': big, 'US-2': kind_only}, [])
    check(big['m'] == [] and big['c'] and str(big['c'][0][3]).startswith('self-check: acres: measured outline'), 'hold: the size line moves the joined row to check')
    check(kind_only['m'] and not any(str(x[3]).startswith('self-check:') for x in kind_only['c']), 'hold: a park inside the band keeps its join')
    noted = park(100, [row(100)], la=0, lo=0)
    pin_bad = KR.self_checks('US-9', noted, (10, -10, 20, 10), 100)
    check(any('outside the state' in b for b in pin_bad) and not any(b.startswith('acres: measured') for b in pin_bad), 'a pin outside the state is a note, not a size line')
    oh = {'n': 'Invented Park', 't': 'State Park', 'm': [row(10)], 'c': [], 'ac': 10}
    _selfchk('OH', {'US-3': oh}, [])
    check(oh['m'] and oh.get('self') and any(str(b).startswith('acres: measured') for b in oh['self']), 'report (the on list): the size line is noted and the join stays')
    off = park(10, [row(10)])
    _selfchk('TN', {'US-1': off}, [])
    check(off['m'] and 'self' not in off, 'off: the check does not run, so nothing is noted and nothing is held')
finally:
    KR.SWITCH_FILE = old_sw
    KR._SW.pop(P, None); KR._HOLD.pop(P, None)
    if old_env is None: os.environ.pop('KPC_SELF_CHECKS', None)
    else: os.environ['KPC_SELF_CHECKS'] = old_env

# --- the builder finds the acres file the way key health does, and not in the waiting room ---
body = _src[_src.find('def _official_acres'):_src.find('def _selfchk')]
check('data/waiting' not in body and 'OFFICIAL_ACRES' in body and "os.environ.get('DATA')" in body, 'the builder looks at OFFICIAL_ACRES, data/acres.json and $DATA, and not at the waiting room')
check("setting('KPC_SELF_CHECKS', area=st)" in _src, 'the builder passes the state, so a hold list can name one state')
td = pathlib.Path(tempfile.mkdtemp())
(td / 'data').mkdir()
(td / 'data' / 'acres.json').write_text(json.dumps({'US-9': 40, 'parks': {'US-8': {'acres': 12}}}))
# a top-level 'parks' object wins, the same as key health (d.get('parks', d))
os.environ['OFFICIAL_ACRES'] = str(td / 'data' / 'acres.json')
_ns['ACRES_OFF'] = None
got = _official_acres()
check(got.get('US-8') == 12.0 and 'US-9' not in got, 'OFFICIAL_ACRES: a row object with acres is read (the parks object, same as key health)')
os.environ.pop('OFFICIAL_ACRES', None)
_ns['ACRES_OFF'] = None
os.environ['DATA'] = str(td)
# this checkout has no data/acres.json, so the $DATA copy is the one that is read
here = _official_acres()
check(here.get('US-8') == 12.0, '$DATA/data/acres.json is read when OFFICIAL_ACRES is unset and data/acres.json is not in the checkout')
os.environ.pop('DATA', None)
_ns['ACRES_OFF'] = None
check(_official_acres() == {}, 'with no file in those places the check has no official sizes (the held copy is not used)')

print('ALL PASS' if all(R) else f'{R.count(False)} FAILED')
sys.exit(0 if all(R) else 1)
