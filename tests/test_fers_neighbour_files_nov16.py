#!/usr/bin/env python3
"""KPC owner, 2026-11-16: a run named for some areas (STATES) writes only those areas' 2-fer files. Pass 1 also holds the
neighbours' parks (border pairs) and used to rewrite each neighbour's file as a pass-1 file; passes 2 to 5 take only the run's
own areas, so a neighbour's finished rows were reset and never finished again (W-AT after a W-CH run: 57 candidates -> 53).
Offline, on the made-up store fixture of tests/test_fers_proof_of_work_nov16.py."""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
src = (HERE / 'test_fers_proof_of_work_nov16.py').read_text()
exec(compile(src.split('\nif not HAVE:')[0], 'proof-of-work helpers', 'exec'))   # layout, go, store_env, check
FAILS.clear()

bot = (SCR / 'kpc_fers.py').read_text()
check('if ONLY and not (st in ONLY or st[3:] in ONLY): continue' in bot, 'pass 1 saves only the areas the run is named for')

if not HAVE:
    print('SKIP the end-to-end part: numpy / cv2 not installed')
else:
    NB = {'st': 'US-DE', 'pass1': '2026-11-01', 'pass2': '2026-11-01', 'pass3': '2026-11-01', 'pass5': '2026-11-01', 'marker': 'the neighbour run\'s own file',
          'spots': [{'id': 'US-99101+US-99102@area@39.000,-75.500', 'refs': ['US-99101', 'US-99102'], 'kind': 'area', 'passes': [1, 1, 1],
                     'status': 'candidate', 'center': [39.0, -75.5], 'box': [-75.51, 38.99, -75.49, 39.01]}]}
    def neighbour(t):   # a Delaware park whose POTA pin lies inside this run's area box: pass 1 keeps it for the border pairs
        layout(t, extra_area='US-DE', old={'US-DE': NB})
        (t / 'data/parkinfo/US-DE.json').write_text(json.dumps({'parks': {'US-99101': ['Test Far Park', '', 'State Park', '', '', 41.65, -71.55]}}))
        return t / 'data/fers/US-DE.json'
    for name, env in (('store run', store_env), ('run that reads the saved copies', env_for)):
        t = TMP / ('nb-' + name.split()[0]); t.mkdir(); f = neighbour(t); before = f.read_bytes()
        rc, out = go(t, env(t, PASS='1', STATES='US-RI'))
        check('filed under another state' in out or 'US-99101' in out or rc == 0, f'{name}: pass 1 ran ({rc})')
        check((t / 'data/fers/US-RI.json').is_file(), f'{name}: the run writes its own area')
        check(f.read_bytes() == before, f"{name}: the neighbour area's file is byte for byte as it was (rows, statuses, pass dates)")

print('ALL PASS' if not FAILS else f'{len(FAILS)} FAILED: ' + '; '.join(FAILS))
sys.exit(1 if FAILS else 0)
