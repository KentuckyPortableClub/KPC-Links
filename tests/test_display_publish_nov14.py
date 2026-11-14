#!/usr/bin/env python3
"""tools/kpc_display_publish.sh against a LOCAL bare repository, end to end (KPC owner, 2026-11-14). Synthetic display copies
built in a temporary folder; no network (only local paths); nothing outside the temporary folder is touched.
Checks: first publish (branch missing), a second publish keeps the other areas and moves map-display-prev to the old commit in
the same atomic push, an unreadable remote stops with nothing pushed, a failing area stops with nothing pushed, a missing area
folder stops, a private preview is refused, another branch is never touched. Prints PASS / FAIL lines, ends ALL PASS or SOME FAILED."""
import json, os, pathlib, shutil, socket, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))


def _no_net(*a, **k): raise OSError('network blocked in this test')


socket.socket.connect = _no_net
socket.create_connection = _no_net
import kpc_display_copy as K  # noqa: E402
from display_copy_fixture import circle, record, park, write_store  # noqa: E402

FAILS = []
ENV = {k: v for k, v in os.environ.items() if 'proxy' not in k.lower()}
ENV.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_TERMINAL_PROMPT': '0', 'PYTHON': sys.executable})


def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: FAILS.append(name)


def git(*a, cwd=None):
    return subprocess.run(['git', *a], capture_output=True, text=True, cwd=cwd, env=ENV)


def ref(bare, name):
    r = git('--git-dir', str(bare), 'rev-parse', '--verify', '-q', name)
    return r.stdout.strip() if r.returncode == 0 else ''


def tree_files(bare, name):
    r = git('--git-dir', str(bare), 'ls-tree', '-r', '--name-only', name)
    return set(r.stdout.split()) if r.returncode == 0 else set()


def publish(remote, new, *areas):
    return subprocess.run(['bash', str(ROOT / 'tools' / 'kpc_display_publish.sh'), str(remote), str(new), *areas],
                          capture_output=True, text=True, env=ENV, timeout=300)


tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-display-publish-'))
try:
    if not shutil.which('git') or not shutil.which('bash'):
        print('SKIP: git or bash is not installed here')
    else:
        bare = tmp / 'remote.git'
        git('init', '-q', '--bare', str(bare))
        seed = tmp / 'seed'; git('init', '-q', str(seed))
        (seed / 'README').write_text('main\n')
        git('-C', str(seed), 'add', '-A'); git('-C', str(seed), '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'main')
        git('-C', str(seed), 'push', '-q', str(bare), 'HEAD:refs/heads/main')
        main0 = ref(bare, 'refs/heads/main')
        st = tmp / 'store'
        write_store(st, 'US-ZA', [park('US-0101', [record('a1', 'lay1', [circle(0.1, 0.1, 0.01, 60)])])])
        write_store(st, 'US-ZB', [park('US-0102', [record('b1', 'lay1', [circle(1.1, 0.1, 0.01, 60)])])])
        K.build(st, ['US-ZA'], tmp / 'new1', log=lambda *a: None)
        r1 = publish(bare, tmp / 'new1', 'US-ZA')
        c1 = ref(bare, 'refs/heads/map-display')
        check('first publish (branch missing): map-display is created with US-ZA, no map-display-prev yet',
              r1.returncode == 0 and c1 and 'US-ZA/INDEX.json' in tree_files(bare, c1) and not ref(bare, 'refs/heads/map-display-prev'))
        K.build(st, ['US-ZB'], tmp / 'new2', log=lambda *a: None)
        r2 = publish(bare, tmp / 'new2', 'US-ZB')
        c2 = ref(bare, 'refs/heads/map-display')
        files2 = tree_files(bare, c2)
        check('second publish keeps the other area (US-ZA) and adds US-ZB', r2.returncode == 0 and 'US-ZA/INDEX.json' in files2 and 'US-ZB/INDEX.json' in files2)
        check('...map-display-prev is the old commit (pushed from the repository that holds it: no "bad object")', ref(bare, 'refs/heads/map-display-prev') == c1)
        check('...map-display is one commit with no history', git('--git-dir', str(bare), 'rev-list', '--count', c2).stdout.strip() == '1')
        check('...main is never touched', ref(bare, 'refs/heads/main') == main0)
        r3 = publish(tmp / 'no-such-remote.git', tmp / 'new2', 'US-ZB')
        check('an unreadable remote stops with nothing pushed (never a tree missing the other areas)',
              r3.returncode != 0 and 'STOP' in r3.stderr and ref(bare, 'refs/heads/map-display') == c2)
        bad = tmp / 'new3'; shutil.copytree(tmp / 'new2', bad)
        idx = json.loads((bad / 'US-ZB' / 'INDEX.json').read_text()); idx['parts'][0][1] = '000000000000'
        (bad / 'US-ZB' / 'INDEX.json').write_text(json.dumps(idx))
        r4 = publish(bare, bad, 'US-ZB')
        check('an area that fails its public check stops the publish; the remote is unchanged',
              r4.returncode != 0 and 'fails its check' in r4.stderr and ref(bare, 'refs/heads/map-display') == c2 and ref(bare, 'refs/heads/map-display-prev') == c1)
        miss = tmp / 'new4'; shutil.copytree(tmp / 'new2', miss)
        idx = json.loads((miss / 'US-ZB' / 'INDEX.json').read_text()); idx['mid'] = {'US-0102': ['mid/US-0102.geojson.gz', 'aaaaaaaaaaaa', 1, 10]}
        (miss / 'US-ZB' / 'INDEX.json').write_text(json.dumps(idx))
        r5 = publish(bare, miss, 'US-ZB')
        check('an index that points at a file that is not there stops the publish', r5.returncode != 0 and ref(bare, 'refs/heads/map-display') == c2)
        r6 = publish(bare, tmp / 'new2', 'US-ZC')
        check('an area folder missing from the build stops the publish', r6.returncode != 0 and ref(bare, 'refs/heads/map-display') == c2)
        K.build(st, ['US-ZB'], tmp / 'prev', preview=True, log=lambda *a: None)
        r7 = publish(bare, tmp / 'prev', 'US-ZB')
        check('a private preview is never published', r7.returncode != 0 and ref(bare, 'refs/heads/map-display') == c2)
        r8 = publish(bare, tmp / 'new1', 'US-ZA')
        check('a later good publish works again and moves map-display-prev to the commit it replaced',
              r8.returncode == 0 and ref(bare, 'refs/heads/map-display-prev') == c2 and 'US-ZB/INDEX.json' in tree_files(bare, 'refs/heads/map-display'))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
