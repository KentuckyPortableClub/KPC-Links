#!/usr/bin/env python3
"""Offline test (bots review, package E, Nov 11 2026): the club / info workflows that were touched still parse, keep their triggers, and
have the new save order. Reads files and `git show origin/main`; no network."""
import pathlib, re, subprocess, sys
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
WF = HERE / '.github/workflows'
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def load(name):
    d = yaml.safe_load((WF / name).read_text())
    on = d.get('on', d.get(True))
    return d, on


def main_version(name):
    r = subprocess.run(['git', 'show', f'origin/main:.github/workflows/{name}'], cwd=HERE, capture_output=True, text=True)
    return yaml.safe_load(r.stdout) if r.returncode == 0 else None


TOUCHED = ['kpc-community.yml', 'kpc-hunters.yml', 'kpc-park-notes.yml', 'kpc-pota-discord.yml', 'kpc-reports.yml', 'kpc-youtube.yml']
for n in TOUCHED:
    d, on = load(n)
    check(isinstance(d.get('jobs'), dict) and d['jobs'] and all(j.get('steps') for j in d['jobs'].values()), f'{n}: parses, has jobs, every job has steps (no zero-job start)')
    old = main_version(n)
    if old is not None:
        oon = old.get('on', old.get(True))
        check((on.get('schedule') if isinstance(on, dict) else on) == (oon.get('schedule') if isinstance(oon, dict) else oon), f'{n}: the schedule (cron lines) is exactly what main has')
        check(set(on) == set(oon), f'{n}: the trigger kinds are the same as main ({sorted(on)})')
        check(set(d['jobs']) == set(old['jobs']), f'{n}: the same jobs as main')
        check(d.get('concurrency') == old.get('concurrency'), f'{n}: the concurrency group is unchanged')

# hunters: the weekly post comes before the cache save, post step gets the force flag from the by-hand input only
d, _ = load('kpc-hunters.yml')
steps = next(iter(d['jobs'].values()))['steps']
names = [s.get('name', '') for s in steps]
ip = next(i for i, s in enumerate(steps) if 'weekly post' in s.get('name', '').lower())
ik = next(i for i, s in enumerate(steps) if 'cache/save' in str(s.get('uses', '')))
check(ip < ik, 'hunters: the weekly post step runs BEFORE the cache save (the "posted this week" mark is kept)')
check(steps[ik].get('if') == 'always()', 'hunters: the cache save still runs always()')
check('KPC_HUNTERS_FORCE' in steps[ip].get('env', {}) and 'workflow_dispatch' in steps[ip]['env']['KPC_HUNTERS_FORCE'], 'hunters: the force flag only comes from a by-hand run')
check('${{' not in next(s for s in steps if 'WHICH_SCHEDULE' in str(s.get('env', ''))).get('run', ''), 'hunters: no ${{ }} expression pasted into the shell script of the count step')

# pota-discord: uses the shared helper
t = (WF / 'kpc-pota-discord.yml').read_text()
check('kpc_save_overwrite.sh --copy' in t and 'pull -q --rebase' not in t, 'pota-discord: the state is saved with the shared helper, not pull --rebase')
check('kpc-pota-spot-state.json' in t.split('kpc_save_overwrite.sh')[1], 'pota-discord: the helper is given the state file')

# youtube: save before the red
t = (WF / 'kpc-youtube.yml').read_text()
check('|| fb_rc=$?' in t and 'exit "${fb_rc:-0}"' in t and '|| dv_rc=$?' in t and 'exit "${dv_rc:-0}"' in t, 'youtube: the Facebook and Discord steps save first and then end red if they failed')
for kind in ('fb_rc', 'dv_rc'):
    seg = t[t.index(f'|| {kind}=$?'):]
    check(seg.index('exit "${' + kind) > seg.index('|| ' + kind), f'youtube: {kind} is only used after it is set')

# community / park-notes / reports: PIL guard before pip
for n in ('kpc-community.yml', 'kpc-park-notes.yml', 'kpc-reports.yml'):
    t = (WF / n).read_text()
    check(re.search(r'import PIL|from PIL|python3 -c .*PIL', t) is not None and 'pip install' in t, f'{n}: the picture library is checked before pip is run')

# no secrets pasted in any club workflow touched: no webhook link, no token literal
for n in TOUCHED:
    t = (WF / n).read_text()
    check(not re.search(r'discord(app)?\.com/api/webhooks/\d+/\S+|EAA[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|ghp_[A-Za-z0-9]{20,}', t), f'{n}: no secret value in the text')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
