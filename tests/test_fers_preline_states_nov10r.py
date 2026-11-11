#!/usr/bin/env python3
"""2-fer pre-line check, per-state key test (owner rule, 2026-11-10). Offline. A state of the batch must be built green on the
current rules in the key build (its own index 'states' row); a partial build no longer holds every state, and a state that was
not built (no row, a row still marked not built, an old rules hash) is held."""
import json, pathlib, sys, tempfile, types
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_fers_preline as PL
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


idx = {'rules': 'old', 'states': {'OH': {'rules': 'cur'}, 'TN': {'rules': 'old'}, 'GA': {'rules': 'cur', '_not_built': 1}, 'AL': {}}}
check(PL.state_not_green(idx, 'US-OH', 'cur') == '', 'a state built green on the current rules passes in a partial build')
check('current rules' in PL.state_not_green(idx, 'US-TN', 'cur'), 'a state built on old rules is held')
check('not built' in PL.state_not_green(idx, 'US-GA', 'cur') and 'not built' in PL.state_not_green(idx, 'US-MS', 'cur'), 'a state not built (marked, or no row) is held')
check(PL.state_not_green(idx, 'US-AL', 'cur') != '' and PL.state_not_green({'rules': 'cur', 'states': {'AL': {}}}, 'US-AL', 'cur') == '', 'a row from before per-state rules follows the key-wide rules')
check(PL.state_not_green({'rules': 'cur'}, 'CA-ON', 'cur') == '' and PL.state_not_green({'rules': 'x'}, 'CA-ON', 'cur') != '', 'a key without rows: the full-build rules decide')

with tempfile.TemporaryDirectory() as t:
    Lk = pathlib.Path(t) / 'links'; D = pathlib.Path(t) / 'data'
    (Lk / 'data/us-key').mkdir(parents=True); (Lk / 'data/status/key-check').mkdir(parents=True); D.mkdir()
    json.dump({'build': 'US-9', 'rules': 'old', 'states': {'OH': {'rules': 'cur'}, 'TN': {'rules': 'old'}}}, open(Lk / 'data/us-key/index.json', 'w'))
    for st in ('OH', 'TN'): json.dump({'parks': {f'US-{st}1': {'m': [[1, 'x']]}}}, open(Lk / f'data/us-key/US-{st}.json', 'w'))
    json.dump({'build': 'US-9'}, open(Lk / 'data/status/key-check/last-us.json', 'w'))
    KF = types.ModuleType('kpc_key_freeze'); KF.rules_hash = lambda kind, root=None: 'cur'
    KF.graded_no = lambda *a: None; KF.verdict = lambda *a: None
    sys.modules['kpc_key_freeze'] = KF
    h_oh, _, _ = PL.check_state('US-OH', 'build', str(D), str(Lk))
    h_tn, _, _ = PL.check_state('US-TN', 'build', str(D), str(Lk))
    check(not any('rules' in h for h in h_oh), f'pre-line: OH (green in a partial build) is not held for the rules ({h_oh})')
    check(any('not built on the current rules' in h for h in h_tn), f'pre-line: TN (old rules) is held ({h_tn})')
print('ALL_OK' if ok else 'FAILED')
sys.exit(0 if ok else 1)
