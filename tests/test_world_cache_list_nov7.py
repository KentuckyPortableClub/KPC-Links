#!/usr/bin/env python3
"""Offline test, Nov 7 world fix part A (hash-neutral). kpc-world-cache.yml's default list now holds every country the world key builds
(+ CO ZA CL and Brandon's sheet countries such as AX and DO), so a single-host country can get a saved copy for the source fallback.
A by-hand list is unchanged. Runs the list step's real Python. No network."""
import json, os, pathlib, re, subprocess, sys, tempfile
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


y = yaml.safe_load(open(HERE / '.github/workflows/kpc-world-cache.yml'))
steps = y['jobs']['prepare']['steps']
st = next(s for s in steps if s.get('id') == 'l')
code = re.search(r"<<'PY'[^\n]*\n(.*?)\n\s*PY\n", st['run'], re.S).group(1)


def lst(cwd, want=''):
    r = subprocess.run([sys.executable, '-B', '-c', code], cwd=cwd, env=dict(os.environ, WANT=want), capture_output=True, text=True)
    return json.loads(next(l for l in r.stdout.splitlines() if l.startswith('list='))[5:])


L = lst(HERE)
sheet = json.load(open(HERE / 'data/world-key/sheet-countries.json', encoding='utf-8'))['countries']
check(all(c in L for c in 'AU CH NO CO ZA CL AX DO'.split()) and all(c in L for c in sheet), 'the default list has the EEA, CO ZA CL and every sheet country')
check(L[-1] == 'CA' and len(L) == len(set(L)) and len(L) <= 256, 'CA last, no country twice, under the 256-job matrix limit')
with tempfile.TemporaryDirectory() as t:
    L0 = lst(t)
check('AU' in L0 and 'CL' in L0 and 'CA' in L0, 'with no sheet file the list still has the fixed countries')
check(lst(HERE, 'au, ax') == ['AU', 'AX'], 'a by-hand list is used as given')
ci = [i for i, s in enumerate(steps) if str(s.get('uses', '')).startswith('actions/checkout')]
check(ci and ci[0] < steps.index(st), 'the repo is checked out before the list is read')
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
