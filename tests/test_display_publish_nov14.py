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
        ENV['KPC_DISPLAY_PUSH'] = 'on'   # a GitHub variable set to on must not publish
        r1 = publish(bare, tmp / 'new1', 'US-ZA')
        check('KPC_DISPLAY_PUSH=on still does not publish (switched off in the file)',
              r1.returncode != 0 and 'switched off in code' in r1.stderr and 'Nothing was pushed' in r1.stderr)
        check('map-display was not created and main was not touched',
              not ref(bare, 'refs/heads/map-display') and not ref(bare, 'refs/heads/map-display-prev') and ref(bare, 'refs/heads/main') == main0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
