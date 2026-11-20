#!/usr/bin/env python3
"""Job 9 (R6; outside review F14, 'missing rule data means no rule'; DRAFT, switch KPC_HOLD_ON_PASS_ERROR, OFF): the US key builder
read each rule data file in a try that turned a missing file into 'no rule' (no saved joins or nos, no retired numbers, no
transfers, no state layers, new layer prefixes; the agency table only when KPC_AGENCY_TIE is on). Now run(st) first asks
kpc_key_rules.rule_data_missing for those files. Switch OFF = nothing changes (the run goes on as before). Switch ON = a missing
or unreadable file holds the state (kpc_key_rules.PassError: FAILED, no key file, saved copy kept).
Runs on INVENTED data (a scratch folder where each file is removed or broken in turn) and on REAL saved data (the files
committed on main, which must all read, so the switch held nothing today). No shapely.
Run:  python3 tests/test_hold_rule_data_missing_nov20.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import json, os, pathlib, shutil, sys, tempfile, textwrap
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

SRC = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check(hasattr(KR, 'rule_data_missing') and hasattr(KR, 'hold_state'), 'kpc_key_rules has rule_data_missing and hold_state')
r0 = SRC.index('def run(st):\n'); r1 = SRC.index("    try: P = json.load(open(f'data/parkinfo/US-{st}.json'))", r0)
head = SRC[r0:r1] + "    return 'went on'\n"
helper = ''
if 'def rule_data_files(' in SRC:
    h0 = SRC.index("OUTLINE_LAYERS = 'data/outlines/layers.json'\n"); helper = SRC[h0:r0]
check(bool(helper), 'the builder names its rule data files (rule_data_files)')
FILES = ['data/us-key/overrides.json', 'data/retired-refs.json', 'data/park-transfers.json', 'data/state-gis.json', 'data/us-key/layers.json', 'data/outlines/layers.json']

def ns(hold, tie=False):
    g = {'json': json, 'pathlib': pathlib, 'OUT': pathlib.Path('data/us-key'), 'CUR_ST': {}, 'KR': KR,
         '_kr': lambda n: (hold and n == 'KPC_HOLD_ON_PASS_ERROR') or (tie and n == 'KPC_AGENCY_TIE')}
    if helper: exec(compile(helper, 'kpc_us_key.py (rule data files)', 'exec'), g)
    exec(compile(head, 'kpc_us_key.py (run head)', 'exec'), g)
    return g

def run_in(folder, hold, tie=False):
    here = os.getcwd(); os.chdir(folder); KR._RULE_DATA.clear() if hasattr(KR, '_RULE_DATA') else None
    try:
        g = ns(hold, tie)
        try: return g['run']('NH'), None
        except Exception as x: return None, x  # noqa: BLE001
    finally: os.chdir(here)

# REAL saved data: every rule data file on main reads
r, x = run_in(ROOT, True, tie=True)
check(r == 'went on' and x is None, f'real files on main, switch ON (and the agency table asked for): all read, the state goes on ({x})')
if hasattr(KR, 'rule_data_missing'):
    KR._RULE_DATA.clear()
    miss = KR.rule_data_missing([str(ROOT / f) for f in FILES] + [KR.AGENCY_TABLE])
    check(miss == [], f'real files on main: none missing or unreadable ({miss})')

# INVENTED: a scratch folder, each file taken away or broken in turn
tmp = pathlib.Path(tempfile.mkdtemp(prefix='j9-', dir='/tmp/j9' if pathlib.Path('/tmp/j9').is_dir() else None))
for f in FILES: (tmp / f).parent.mkdir(parents=True, exist_ok=True); (tmp / f).write_text('{}')
for f in FILES:
    for how in ('missing', 'broken'):
        if how == 'missing': (tmp / f).unlink()
        else: (tmp / f).write_text('{not json')
        r, x = run_in(tmp, False)
        check(r == 'went on' and x is None, f'switch OFF, {f} {how}: the state goes on as before ({x})')
        r, x = run_in(tmp, True)
        check(isinstance(x, KR.PassError) and 'NH' in str(x) and f in str(x), f'switch ON, {f} {how}: the state is held and the file is named ({x})')
        (tmp / f).write_text('{}')
r, x = run_in(tmp, True)
check(r == 'went on' and x is None, f'switch ON, every file there: the state goes on (no agency table asked while KPC_AGENCY_TIE is off) ({x})')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed')
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(0 if n == len(RESULTS) else 1)
