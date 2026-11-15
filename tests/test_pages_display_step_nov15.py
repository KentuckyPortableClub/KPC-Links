#!/usr/bin/env python3
"""Pages deploy, the display-copy step (KPC owner, 2026-11-15). Offline: the step's own script (read from
.github/workflows/pages-deploy.yml) is run in a throwaway checkout whose origin is a LOCAL bare repository, after a stand-in
_site. Made-up display data only (tests/display_copy_fixture.py). Checks:
  - no map-display branch: exit 0, nothing added, the site as built;
  - origin cannot be read: exit 0, nothing added;
  - a branch with a good area and a bad one: only the good area (that passes check --public) lands in _site/data/display/;
  - the step is continue-on-error and sits between the Jekyll build and the upload.
Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED."""
import os, pathlib, shutil, socket, subprocess, sys, tempfile
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))


def _no_net(*a, **k): raise OSError('network blocked in this test')


socket.socket.connect = _no_net
socket.create_connection = _no_net
import kpc_display_copy as K  # noqa: E402
from display_copy_fixture import circle, record, park, write_store  # noqa: E402

FAILS = []


def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: FAILS.append(name)


ENV = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', HOME=tempfile.mkdtemp(prefix='kpc-home-'), GIT_TERMINAL_PROMPT='0',
           GIT_AUTHOR_NAME='KPC owner', GIT_AUTHOR_EMAIL='KentuckyPortableClub@users.noreply.github.com',
           GIT_COMMITTER_NAME='KPC owner', GIT_COMMITTER_EMAIL='KentuckyPortableClub@users.noreply.github.com')


def git(*a, cwd=None):
    return subprocess.run(['git', '-c', 'commit.gpgsign=false', '-c', 'init.defaultBranch=main', *a], cwd=cwd, env=ENV,
                          capture_output=True, text=True)


wf = yaml.safe_load((ROOT / '.github/workflows/pages-deploy.yml').read_text(encoding='utf-8'))
steps = wf['jobs']['build']['steps']
idx = [i for i, s in enumerate(steps) if str(s.get('name', '')).startswith('Display copy from the map-display branch')]
check('pages-deploy.yml has ONE display-copy step', len(idx) == 1)
st = steps[idx[0]]
uses = [s.get('uses', '') for s in steps]
check('it runs after the Jekyll build and before the upload', idx[0] > next(i for i, u in enumerate(uses) if 'jekyll-build-pages' in u)
      and idx[0] < next(i for i, u in enumerate(uses) if 'upload-pages-artifact' in u))
check('it can never fail the deploy (continue-on-error)', st.get('continue-on-error') is True)
check('it re-checks every area with check --public', 'kpc_display_copy.py check --out' in st['run'] and '--public' in st['run'])
check('it asks for no secret and no write permission', 'secrets.' not in st['run'] and 'env' not in st)
SCRIPT = st['run']

tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-pages-step-'))
try:
    bare = tmp / 'origin.git'; git('init', '-q', '--bare', str(bare))
    work = tmp / 'work'; git('init', '-q', str(work)); (work / 'index.html').write_text('site\n')
    git('add', '-A', cwd=work); git('commit', '-q', '-m', 'site', cwd=work)
    git('remote', 'add', 'origin', str(bare), cwd=work); git('push', '-q', 'origin', 'HEAD:refs/heads/main', cwd=work)
    (work / 'tools').symlink_to(ROOT / 'tools')

    def run_step(origin_ok=True):
        site = work / '_site'
        if site.exists(): shutil.rmtree(site)
        (site / 'data').mkdir(parents=True); (site / 'index.html').write_text('site\n')
        summ = tmp / 'summary.md'; summ.write_text('')
        if not origin_ok: git('remote', 'set-url', 'origin', str(tmp / 'no-such.git'), cwd=work)
        r = subprocess.run(['bash', '-e', '-c', SCRIPT], cwd=work, env=dict(ENV, GITHUB_STEP_SUMMARY=str(summ)), capture_output=True, text=True, timeout=300)
        if not origin_ok: git('remote', 'set-url', 'origin', str(bare), cwd=work)
        return r, site, summ.read_text()

    r, site, summ = run_step()
    check('no map-display branch: exit 0 and nothing added', r.returncode == 0 and not (site / 'data' / 'display').exists()
          and 'no map-display branch yet' in summ)
    r, site, summ = run_step(origin_ok=False)
    check('origin cannot be read: exit 0 and nothing added', r.returncode == 0 and not (site / 'data' / 'display').exists())

    # a made-up display copy: US-ZA good, US-ZB broken (a file not listed in its INDEX), plus a stray top-level folder
    stg = tmp / 'store'
    write_store(stg, 'US-ZA', [park('US-0201', [record('a1', 'lay1', [circle(0.1, 0.1, 0.01, 120)])])])
    write_store(stg, 'US-ZB', [park('US-0202', [record('b1', 'lay1', [circle(0.3, 0.1, 0.01, 120)])])])
    out = tmp / 'out'
    K.build(stg, ['US-ZA'], out, log=lambda *a: None); K.build(stg, ['US-ZB'], out, log=lambda *a: None)
    (out / 'US-ZB' / 'extra.geojson.gz').write_bytes(b'x')
    (out / 'notes').mkdir(); (out / 'notes' / 'x.txt').write_text('x')
    pub = tmp / 'pub'; git('init', '-q', str(pub)); shutil.copytree(out, pub, dirs_exist_ok=True)
    git('add', '-A', cwd=pub); git('commit', '-q', '-m', 'display', cwd=pub); git('push', '-q', str(bare), 'HEAD:refs/heads/map-display', cwd=pub)
    r, site, summ = run_step()
    d = site / 'data' / 'display'
    check('a branch with a good and a bad area: exit 0', r.returncode == 0)
    check('the good area is copied whole', (d / 'US-ZA' / 'INDEX.json').is_file() and K.check(d.parent / 'display', 'US-ZA', public=True) == [])
    check('the area that fails check --public is left out, and so is a folder that is not an area',
          not (d / 'US-ZB').exists() and not (d / 'notes').exists() and 'US-ZB' in summ)
    check('the rest of the site is untouched', (site / 'index.html').read_text() == 'site\n')
    check('the checkout itself is not changed (only _site)', git('status', '--porcelain', '--untracked-files=no', cwd=work).stdout.strip() == '')
finally:
    shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(ENV['HOME'], ignore_errors=True)
print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
