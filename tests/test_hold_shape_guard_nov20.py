#!/usr/bin/env python3
"""Job 9 (R6; outside review F10, 'the shape guard fails a state only below half its shapes'; DRAFT, switch KPC_HOLD_ON_PASS_ERROR,
OFF): kpc_shape_guard.py compares a built state's shape count (counts.padus) with the last live key. Switch OFF = short only
under half, as before. Switch ON for a state = short under 97% (the workflow then refills that state from the saved outlines or
puts the live key file back and fails the job: held). Runs on INVENTED data: invented built files and live index, the real
guard run as a script. The switch is set by the environment variable of the same name (as the offline proofs do).
Run:  python3 tests/test_hold_shape_guard_nov20.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import json, os, pathlib, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

tmp = pathlib.Path(tempfile.mkdtemp(prefix='j9-', dir='/tmp/j9' if pathlib.Path('/tmp/j9').is_dir() else None))
(tmp / 'built').mkdir()
for st, n in (('NH', 60), ('VT', 96), ('ME', 98)):
    json.dump({'counts': {'padus': n}}, open(tmp / 'built' / f'US-{st}.json', 'w'))
json.dump({'states': {'NH': {'padus': 100}, 'VT': {'padus': 100}, 'ME': {'padus': 100}}}, open(tmp / 'index.json', 'w'))

def guard(on):
    env = {k: v for k, v in os.environ.items() if k != 'KPC_HOLD_ON_PASS_ERROR'}
    if on: env['KPC_HOLD_ON_PASS_ERROR'] = '1'
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_shape_guard.py'), '--built', str(tmp / 'built'),
                        '--live-index', str(tmp / 'index.json'), '--states', 'NH VT ME'], capture_output=True, text=True, env=env, cwd=str(tmp))
    return r.returncode, sorted(r.stdout.split('\n')[:-1])

rc, rows = guard(False)
check(rc == 0 and rows == [], f'switch OFF: 60, 96 and 98 of 100 all pass (only under half is short), as before ({rc}, {rows})')
rc, rows = guard(True)
check(rc == 2 and rows == ['NH 60 100', 'VT 96 100'], f'switch ON: 60 and 96 of 100 are short, 98 passes ({rc}, {rows})')
sw = json.load(open(ROOT / '.github/key-switches.json', encoding='utf-8'))['switches']
check(sw.get('KPC_HOLD_ON_PASS_ERROR') == {'on': []}, 'the committed switch is on for no state, so the guard reads as before at merge')
y = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
check('shape guard stopped (exit $sc)' in y, "the workflow fails the job on any other exit (3 = the switch file or live index not read)")
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed')
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(0 if n == len(RESULTS) else 1)
