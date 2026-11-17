#!/usr/bin/env python3
"""Handoff 8 fix 2 (switch KPC_FS_RIVER_NAMES): Forest Service wild and scenic river names, and the record's second name field.
The records are the real ones from the saved copies (id, name, second name, layer, kind); the test calls join_how(), the one
function run() asks. The pin is next to the record (close=True), as in the saved copies.
Run:  python3 tests/test_h8_fs_rivers_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import os, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests')); sys.path.insert(0, str(ROOT / '.github/scripts'))
os.chdir(ROOT)
import run_match_tests as RMT  # noqa: E402
US = RMT._load('kpc_us_key.py', '\nidx = {}\n')
KR = US.KR
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)
FWSR = 'Forest Service Wild and Scenic River corridor (official boundary)'
def rec(oid, nm, loc='', lm=FWSR, k=None): return {'OBJECTID': oid, 'Unit_Nm': nm, 'Loc_Nm': loc, 'Loc_Mang': lm, '_k': US.kinds(nm) if k is None else k}
def how(park, a, sw, close=True):
    old = os.environ.get('KPC_FS_RIVER_NAMES'); os.environ['KPC_FS_RIVER_NAMES'] = sw
    try: return US.join_how(park, US.kinds(park), a, close)
    finally:
        if old is None: os.environ.pop('KPC_FS_RIVER_NAMES', None)
        else: os.environ['KPC_FS_RIVER_NAMES'] = old
MUST = [('US-12792', 'Manistee National Wild and Scenic River', rec('fwsr44', 'Manistee, Michigan National Wild and Scenic River')),
        ('US-12798', 'Sturgeon (Hiawatha) National Wild and Scenic River', rec('fwsr61', 'Sturgeon, Michigan (Hiawatha NF) National Wild and Scenic River')),
        ('US-12798', 'Sturgeon (Hiawatha) National Wild and Scenic River', rec('fwsr163', 'Sturgeon, Michigan (Hiawatha NF) National Wild and Scenic River')),
        ('US-12234', 'Allegheny National Wild and Scenic River', rec('fwsr1', 'Allegheny, Pennsylvania National Wild and Scenic River')),
        ('US-10709', 'Klickitat National Wild and Scenic River', rec('fwsr35', 'Klickitat, Washington National Wild and Scenic River'))]
for ref, park, a in MUST:
    h = how(park, a, '1')
    check(h == 'name (Forest Service river: state and forest dropped)', f'ON: {ref} {park} joins {a["OBJECTID"]} {a["Unit_Nm"]!r} by name ({h})')
    check(how(park, a, '0') != h, f'OFF: {ref} is not joined this way (today: {how(park, a, "0")!r})')
oz = rec(255603, 'Cumberland Trail', 'Ozone Falls', 'Tennessee Department of Environment and Conservation', {'sp'})
check(how('Ozone Falls State Natural Area', oz, '1') == 'name (second name field)', "ON: US-6259 Ozone Falls SNA joins 'Cumberland Trail' by its second name field 'Ozone Falls'")
check(how('Ozone Falls State Natural Area', oz, '0') is None, 'OFF: US-6259 Ozone Falls SNA does not join (the record kind State Park blocks the second name)')
check(how('Ozone Falls State Natural Area', oz, '1', close=False) is None,
      'the second name joins only near the pin (close=False: no join)')
# must NOT
check(how('Klickitat National Wild and Scenic River', rec(271381, 'Klickitat Wildlife Area Complex', 'Klickitat', lm='Unknown', k={'wma'}), '1') is None,
      "must NOT: US-10709 does not join WA 271381 'Klickitat Wildlife Area Complex' by its second name 'Klickitat' (the first name says another kind)")
check(how('Sturgeon (Hiawatha) National Wild and Scenic River', rec('fwsr164', 'Sturgeon, Michigan (Ottawa NF) National Wild and Scenic River'), '1') is None,
      "a park that names its forest (Hiawatha) does not take the other forest's river record (Ottawa NF)")
check(how('Klickitat National Wild and Scenic River', rec('fsod124', 'Klickitat, Washington Wild And Scenic River Study Area', lm='Forest Service national designated areas'), '1') is None,
      'a wild and scenic river STUDY area is not the river')
check(how('Little Manistee National Wild and Scenic River', rec('fwsr44', 'Manistee, Michigan National Wild and Scenic River'), '1') is None,
      'Little Manistee is not the Manistee')
check(how('Manistee River State Game Area', rec('fwsr44', 'Manistee, Michigan National Wild and Scenic River'), '1') is None,
      'a state game area is not the river (kinds still must agree)')
check(KR.fs_river_name('Rio Grande, New Mexico National Wild and Scenic River')[0] == 'Rio Grande National Wild and Scenic River'
      and KR.fs_river_name('Sturgeon, Michigan (Hiawatha NF) National Wild and Scenic River') == ('Sturgeon National Wild and Scenic River', 'hiawatha'),
      'the cleaner: two-word states and the forest bracket')
check(not KR.on('KPC_FS_RIVER_NAMES', {}), 'the switch is OFF unless set')
# a person's NO still wins: the four rivers carry one today (overrides, decided Nov 9): the name now matches, the NO keeps them out
ov = {'no': ['fwsr44'], 'nofp': {'fwsr44': ['Manistee, Michigan National Wild and Scenic River', 8919]}}
check(KR.is_no(ov, 'fwsr44', 'Manistee, Michigan National Wild and Scenic River', 8918.7), "a person's NO on fwsr44 (US-12792 today) still keeps it out")
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
