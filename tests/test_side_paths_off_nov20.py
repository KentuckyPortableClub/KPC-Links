#!/usr/bin/env python3
"""R11 / F17 (20 Nov). Two side paths to public files are switched off in the code.
A GitHub variable set to on does not open either one. Invented files only, no network.
  1. The display copy (KPC_DISPLAY_PUSH=on) does not publish and is not copied onto the site.
  2. The keeper's asks (KPC_LR_CHANGED_READ=whole) do not plan a public fetch.
"""
import os, pathlib, subprocess, sys, tempfile
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what)
    if not ok: FAILS.append(what)


# 1. display copy. A GitHub variable cannot publish.
with tempfile.TemporaryDirectory() as t:
    td = pathlib.Path(t)
    bare = td / 'remote.git'
    subprocess.run(['git', 'init', '-q', '--bare', str(bare)], check=True)
    new = td / 'new' / 'US-ZZ'
    new.mkdir(parents=True)
    (new / 'INDEX.json').write_text('{"made": "test"}\n')
    env = dict(os.environ, KPC_DISPLAY_PUSH='on', GIT_TERMINAL_PROMPT='0')
    r = subprocess.run(['bash', str(ROOT / 'tools' / 'kpc_display_publish.sh'), str(bare), str(td / 'new'), 'US-ZZ'],
                       capture_output=True, text=True, env=env)
    refs = subprocess.run(['git', '--git-dir', str(bare), 'show-ref'], capture_output=True, text=True)
    check(r.returncode != 0 and 'switched off in code' in r.stderr and 'map-display' not in refs.stdout,
          'display copy: KPC_DISPLAY_PUSH=on does not publish')

    wf = yaml.safe_load((ROOT / '.github/workflows/pages-deploy.yml').read_text(encoding='utf-8'))
    step = next(s for s in wf['jobs']['build']['steps'] if str(s.get('name', '')).startswith('Display copy'))
    summ = td / 'sum.md'
    summ.write_text('')
    r = subprocess.run(['bash', '-e', '-c', step['run']], cwd=td, capture_output=True, text=True,
                       env=dict(env, GITHUB_STEP_SUMMARY=str(summ), KPC_DISPLAY_MAX_MB='300'))
    check(r.returncode == 0 and 'switched off in code' in summ.read_text() and not (td / '_site' / 'data' / 'display').exists(),
          'display copy: the public site step adds nothing when the variable is on')

# 2. keeper's asks. The ruled knob cannot open a public fetch.
wf = yaml.safe_load((ROOT / '.github/workflows/kpc-geo-cache.yml').read_text(encoding='utf-8'))
step = next(s for s in wf['jobs']['prepare']['steps'] if s.get('id') == 'g')
with tempfile.TemporaryDirectory() as t:
    td = pathlib.Path(t)
    out = td / 'out.txt'
    out.write_text('')
    env = dict(os.environ, FROM_REQUESTS='true', KPC_LR_CHANGED_READ='whole', KPC_LR_WHO='keeper+hand',
               GITHUB_OUTPUT=str(out), GITHUB_STEP_SUMMARY=str(td / 'sum.md'), RUNNER_TEMP=str(td / 'rt'),
               GH_TOKEN='not-a-token', GITHUB_REPOSITORY='KentuckyPortableClub/KPC-Links')
    (td / 'sum.md').write_text('')
    (td / 'rt').mkdir()
    r = subprocess.run(['bash', '-e', '-c', step['run']], cwd=ROOT, capture_output=True, text=True, env=env)
    got = out.read_text()
    check(r.returncode == 0 and 'groups=[]' in got and 'switched off in code' in (td / 'sum.md').read_text()
          and 'gh ' not in r.stdout and 'layer-requests' not in r.stdout,
          f'keeper asks: a ruled knob does not plan a public fetch ({got.strip()!r})')

print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
