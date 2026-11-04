#!/usr/bin/env python3
"""Offline test, Nov 4 PM fix bundle item 5 (Brandon's yes relayed via Super Head Bot, 4:53 PM CST Nov 4): in kpc-world-key.yml a SLOW
country (default AU) gets a job of its own with its own limit (default 300 min), so W-41895532587's AU stop (100 min, shared job of
27 countries) does not keep the world key from being a full build. Runs the plan step's real Python. No network."""
import json, os, pathlib, re, subprocess, sys, tempfile
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


y = yaml.safe_load(open(HERE / '.github/workflows/kpc-world-key.yml'))
st = next(s for s in y['jobs']['plan']['steps'] if s.get('id') == 'p')
code = re.search(r"<<'PY'[^\n]*\n(.*?)\n\s*PY\n", st['run'], re.S).group(1)
code = '\n'.join(l[0:] for l in code.splitlines())
ALL = 'AU DE GB JP PL ES FR CH AT NL PT SE CZ SI NO RO IT BE DK FI HU SK HR IE LT LV EE LU CO ZA CL BS CV NC'


def plan(**env):
    with tempfile.TemporaryDirectory() as t:
        e = dict(os.environ, **dict({'ALL': ALL}, **env))
        r = subprocess.run([sys.executable, '-B', '-c', code], cwd=t, env=e, capture_output=True, text=True)
        g = next(l for l in r.stdout.splitlines() if l.startswith('groups='))
        return json.loads(g[7:]), r.stdout


G, out = plan(SLOW='AU', SLOW_MIN='300')
au = [x for x in G if 'AU' in x['countries'].split()]
check(len(au) == 1 and au[0]['countries'] == 'AU' and au[0]['cmin'] == '300', 'AU has a job of its own with a 300-min limit')
check(len(G) == 4 and sorted(c for x in G for c in x['countries'].split()) == sorted(ALL.split()), 'every country is built exactly once (3 shared jobs + AU)')
check(all(x['cmin'] == '' for x in G if x is not au[0]), 'the shared jobs keep the old limit (KPC_WORLD_COUNTRY_MIN, default 100)')
G, _ = plan(SLOW='', SLOW_MIN='300')
check(len(G) == 3 and all(x['cmin'] == '' for x in G), 'KPC_WORLD_SLOW empty = the old split (3 jobs)')
G, _ = plan(SLOW='AU DE JP', SLOW_MIN='250')
check(len([x for x in G if x['cmin']]) == 2, 'at most two slow countries get their own job')
G, _ = plan(SLOW='AU', ALL='AU')
check(G == [{'i': 0, 'countries': 'AU', 'cmin': '300'}], 'a by-hand AU-only run is one AU job')
G, _ = plan(SLOW='AU', ALL='DE GB')
check(len(G) == 2 and all(not x['cmin'] for x in G), 'a run without AU is unchanged')
b = next(s for s in y['jobs']['build']['steps'] if s.get('id') == 'kept_green_b')
check(b['env']['CMIN'].startswith('${{ matrix.g.cmin ||') and int(b['timeout-minutes']) > 300 + 2, "the build step uses the job's own limit, and 300 min + kill time stays under the step's 335")
check(st['env'].get('SLOW') == "${{ vars.KPC_WORLD_SLOW || 'AU' }}" and st['env'].get('SLOW_MIN') == "${{ vars.KPC_WORLD_SLOW_MIN || '300' }}", 'the slow list and limit are repo variables (KPC_WORLD_SLOW default AU, KPC_WORLD_SLOW_MIN default 300)')
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
