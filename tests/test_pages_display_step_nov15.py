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
check('it asks for no secret and no write permission', 'secrets.' not in st['run'] and set(st.get('env') or {}) == {'KPC_DISPLAY_MAX_MB'})
check('it has a time limit and a size cap', 0 < int(st.get('timeout-minutes') or 0) <= 15 and 0 < int(st['env']['KPC_DISPLAY_MAX_MB']) <= 500)
SCRIPT = st['run']

tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-pages-step-'))
try:
    bare = tmp / 'origin.git'; git('init', '-q', '--bare', str(bare))
    work = tmp / 'work'; git('init', '-q', str(work)); (work / 'index.html').write_text('site\n')
    git('add', '-A', cwd=work); git('commit', '-q', '-m', 'site', cwd=work)
    git('remote', 'add', 'origin', str(bare), cwd=work); git('push', '-q', 'origin', 'HEAD:refs/heads/main', cwd=work)
    (work / 'tools').symlink_to(ROOT / 'tools')

    def run_step(origin_ok=True, cap=None):
        site = work / '_site'
        if site.exists(): shutil.rmtree(site)
        (site / 'data').mkdir(parents=True); (site / 'index.html').write_text('site\n')
        summ = tmp / 'summary.md'; summ.write_text('')
        if not origin_ok: git('remote', 'set-url', 'origin', str(tmp / 'no-such.git'), cwd=work)
        r = subprocess.run(['bash', '-e', '-c', SCRIPT], cwd=work, env=dict(ENV, GITHUB_STEP_SUMMARY=str(summ), KPC_DISPLAY_PUSH='on', KPC_DISPLAY_MAX_MB=str(cap if cap is not None else st['env']['KPC_DISPLAY_MAX_MB'])), capture_output=True, text=True, timeout=300)
        if not origin_ok: git('remote', 'set-url', 'origin', str(bare), cwd=work)
        return r, site, summ.read_text()

    r, site, summ = run_step()
    check('no map-display branch: exit 0 and nothing added', r.returncode == 0 and not (site / 'data' / 'display').exists()
          and 'switched off in code' in summ)
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
    check('a good display branch with KPC_DISPLAY_PUSH=on still adds nothing', r.returncode == 0 and not d.exists() and 'switched off in code' in summ)
    check('the rest of the site is untouched', (site / 'index.html').read_text() == 'site\n')
    check('the checkout itself is not changed (only _site)', git('status', '--porcelain', '--untracked-files=no', cwd=work).stdout.strip() == '')
    r, site, summ = run_step(cap=0)
    check('a size cap cannot turn the copy back on: exit 0 and nothing added', r.returncode == 0 and not (site / 'data' / 'display').exists() and 'switched off in code' in summ)

    # grade fix: links and odd names. Each case is a branch of its own: US-ZA good + one bad thing.
    outside = tmp / 'outside-secret'; outside.mkdir(); (outside / 'secret.txt').write_text('private')

    def publish(fn):
        pb = tmp / ('pub-' + fn.__name__); shutil.rmtree(pb, ignore_errors=True)
        git('init', '-q', str(pb)); shutil.copytree(out / 'US-ZA', pb / 'US-ZA'); shutil.copytree(out / 'US-ZA', pb / 'US-ZC')
        fn(pb)
        git('add', '-A', cwd=pb); git('commit', '-q', '-m', 'display', cwd=pb)
        return git('push', '-q', '-f', str(bare), 'HEAD:refs/heads/map-display', cwd=pb)
    def dir_link(pb): (pb / 'US-ZC' / 'zzdir').symlink_to(outside, target_is_directory=True)
    def file_link(pb): (pb / 'US-ZC' / 'mid').mkdir(exist_ok=True); (pb / 'US-ZC' / 'mid' / 'x.geojson.gz').symlink_to(outside / 'secret.txt')
    def top_link(pb): (pb / 'US-ZD').symlink_to(outside, target_is_directory=True)
    def nl_area_file(pb): (pb / 'US-ZC' / 'a\n::error title=x::injected').write_text('x')
    def nl_top(pb): (pb / 'x\n::error title=x::injected').mkdir(); (pb / 'x\n::error title=x::injected' / 'f').write_text('x')
    for fn, what in ((dir_link, 'a folder link inside an area'), (file_link, 'a file link inside an area'),
                     (top_link, 'a top-level link named like an area'), (nl_area_file, 'a file name with a newline inside an area'),
                     (nl_top, 'a top-level name with a newline')):
        publish(fn)
        r, site, summ = run_step()
        d = site / 'data' / 'display'
        links = [q for q in d.rglob('*') if q.is_symlink()] if d.exists() else []
        leaked = 'private' in ''.join(q.read_text(errors='ignore') for q in d.rglob('*') if q.is_file()) if d.exists() else False
        bad_area = 'US-ZD' if fn is top_link else 'US-ZC'
        check(f'{what}: exit 0, nothing added, no link and nothing from outside in _site',
              r.returncode == 0 and not d.exists() and not links and not leaked)
        log = r.stdout + r.stderr + summ
        check(f'{what}: no name read from the branch reaches the log or the summary (no injected workflow command)',
              'injected' not in log and not any(ln.startswith('::error') for ln in log.splitlines()))
    check('nothing was added under _site/data/display', not (site / 'data' / 'display').exists())
finally:
    shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(ENV['HOME'], ignore_errors=True)
print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
