#!/usr/bin/env python3
"""kpc_key_offline.py: run a key script with NO network at all (KPC owner, 2026-11-15; keys in store mode).

In store mode (repo variable KPC_KEY_SOURCE=store) a key run only keeps the park-to-record joins up to date. Its whole-layer saved
copies are downloaded from this repo's boundary-cache release by the workflow BEFORE the key step; the key step itself must not
open any connection. GEO_CACHE_MODE=only already keeps the map reads off; this runner makes every other path fail closed too:

  python3 .github/scripts/kpc_key_offline.py .github/scripts/kpc_us_key.py [args]

- every socket connect (except a local AF_UNIX socket), socket.create_connection and every DNS lookup is refused (OSError), so a
  caller's ordinary 'read failed' path applies and nothing is read;
- a child process that would reach the network is refused: curl, wget, gh, ssh, pip / pip3 (and python -m pip), and git clone /
  fetch / pull / push / ls-remote / submodule / remote (local git show / ls-tree / status are allowed);
- every refusal is written to the log (KPC_OFFLINE_LOG, default $RUNNER_TEMP/kpc-offline-refused.txt) and printed as ::error;
- when anything was refused the run exits 89 (even when the script itself ended 0), so the step goes red and the
  workflow keeps that area's previous key (fail closed). A refusal never becomes a key.

Not a rule file: it decides no join (kpc_key_freeze.NOT_RULES). Standard library only.
  python3 .github/scripts/kpc_key_offline.py --selftest
"""
import os, runpy, socket, subprocess, sys

EXIT_REFUSED = 89
NET_TOOLS = {'curl', 'wget', 'gh', 'ssh', 'scp', 'sftp', 'rsync', 'nc', 'ncat', 'pip', 'pip3', 'apt', 'apt-get'}
GIT_NET = {'clone', 'fetch', 'pull', 'push', 'ls-remote', 'submodule', 'remote', 'archive'}
REFUSED = []


def _log_path():
    return os.environ.get('KPC_OFFLINE_LOG') or os.path.join(os.environ.get('RUNNER_TEMP') or '/tmp', 'kpc-offline-refused.txt')


def refuse(what):
    REFUSED.append(what)
    try:
        with open(_log_path(), 'a', encoding='utf-8') as f: f.write(what + '\n')
    except OSError: pass
    print(f'::error title=Store mode (no network)::refused: {what[:200]}', file=sys.stderr, flush=True)
    raise OSError(f'store mode, no network: {what[:200]}')


def _argv(args):
    if isinstance(args, (list, tuple)): return [str(a) for a in args]
    return str(args).split()


def net_command(args):
    """True when a child process command line would reach the network."""
    a = _argv(args)
    if not a: return False
    tool = os.path.basename(a[0])
    if tool in NET_TOOLS: return True
    if tool.startswith('python') and len(a) > 2 and a[1] == '-m' and a[2] in ('pip', 'pip3', 'ensurepip'): return True
    if tool == 'git':
        rest = [x for x in a[1:] if not x.startswith('-')]
        i = 0
        while i < len(a) - 1 and a[i + 1] in ('-C', '-c'):   # git -C dir / -c k=v take a value
            i += 2
        sub = next((x for x in a[i + 1:] if not x.startswith('-')), rest[0] if rest else '')
        return sub in GIT_NET
    return False


def install():
    """Process-wide, idempotent."""
    if getattr(socket, '_kpc_offline', False): return
    real_connect, real_connect_ex = socket.socket.connect, socket.socket.connect_ex

    def connect(self, addr):
        if getattr(self, 'family', None) == getattr(socket, 'AF_UNIX', object()): return real_connect(self, addr)
        refuse(f'connect {addr!r}')

    def connect_ex(self, addr):
        if getattr(self, 'family', None) == getattr(socket, 'AF_UNIX', object()): return real_connect_ex(self, addr)
        refuse(f'connect {addr!r}')
    socket.socket.connect, socket.socket.connect_ex = connect, connect_ex
    socket.create_connection = lambda address, *a, **k: refuse(f'create_connection {address!r}')
    socket.getaddrinfo = lambda host, *a, **k: refuse(f'DNS lookup {host!r}')
    socket.gethostbyname = lambda host: refuse(f'DNS lookup {host!r}')
    socket.gethostbyname_ex = lambda host: refuse(f'DNS lookup {host!r}')
    real_popen_init = subprocess.Popen.__init__

    def popen_init(self, args, *a, **k):
        if net_command(args): refuse(f"child process {' '.join(_argv(args))[:160]}")
        return real_popen_init(self, args, *a, **k)
    subprocess.Popen.__init__ = popen_init
    real_system = os.system

    def system(cmd):
        if net_command(cmd): refuse(f'child process {str(cmd)[:160]}')
        return real_system(cmd)
    os.system = system
    socket._kpc_offline = True


def run(script, args):
    install()
    sys.argv = [script] + list(args)
    sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
    code = 0
    try:
        runpy.run_path(script, run_name='__main__')
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    if REFUSED:
        print(f'::error title=Store mode (no network)::{len(REFUSED)} connection(s) refused while running {os.path.basename(script)}: '
              f'this run is red and its result is not used (see {_log_path()})', file=sys.stderr, flush=True)
        return code or EXIT_REFUSED
    return code


def selftest():
    import tempfile, pathlib
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)
    for cmd, want in ((['curl', 'https://x'], True), (['gh', 'release', 'download'], True), ('wget -q x', True),
                      (['git', 'show', 'HEAD:x'], False), (['git', '-C', 'd', 'fetch', 'origin'], True), (['git', 'clone', 'u'], True),
                      (['git', 'ls-tree', 'HEAD'], False), ([sys.executable, '-m', 'pip', 'install', 'x'], True), (['python3', 'x.py'], False),
                      (['/usr/bin/pip3', 'install'], True), (['ls'], False)):
        check(f'net_command({cmd!r}) == {want}', net_command(cmd) == want)
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        s = t / 'k.py'
        s.write_text("import socket, urllib.request, subprocess, sys\n"
                     "n = 0\n"
                     "for f in (lambda: urllib.request.urlopen('http://127.0.0.1:9/', timeout=2), lambda: socket.create_connection(('127.0.0.1', 9), 2),\n"
                     "          lambda: socket.getaddrinfo('example.org', 443), lambda: subprocess.run(['curl', '-s', 'http://127.0.0.1:9/'])):\n"
                     "    try: f()\n"
                     "    except OSError: n += 1\n"
                     "print('refused', n)\n"
                     "print(subprocess.run(['git', '--version'], capture_output=True, text=True).returncode)\n")
        log = t / 'log.txt'
        r = subprocess.run([sys.executable, __file__, str(s)], capture_output=True, text=True, env=dict(os.environ, KPC_OFFLINE_LOG=str(log)))
        check(f'four network paths refused inside the script (got {r.stdout.split()[:2]})', 'refused 4' in r.stdout)
        check('a local git command still runs', r.stdout.strip().endswith('0'))
        check(f'any refusal = exit {EXIT_REFUSED} (got {r.returncode})', r.returncode == EXIT_REFUSED)
        check('every refusal is logged', log.exists() and len(log.read_text().splitlines()) == 4)
        q = t / 'q.py'; q.write_text("import json, sys\nprint(json.dumps({'a': 1}))\nsys.exit(3)\n")
        r = subprocess.run([sys.executable, __file__, str(q)], capture_output=True, text=True, env=dict(os.environ, KPC_OFFLINE_LOG=str(t / 'l2')))
        check(f"a script with no network keeps its own exit code (3, got {r.returncode})", r.returncode == 3 and '"a": 1' in r.stdout)
        z = t / 'z.py'; z.write_text("print(__name__, __file__.endswith('z.py'))\n")
        r = subprocess.run([sys.executable, __file__, str(z)], capture_output=True, text=True, env=dict(os.environ, KPC_OFFLINE_LOG=str(t / 'l3')))
        check(f"the script runs as __main__ with its own __file__ (got {r.stdout.strip()!r}, exit {r.returncode})", r.stdout.strip() == '__main__ True' and r.returncode == 0)
    print('SELFTEST PASS' if ok else 'SELFTEST FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    if sys.argv[1:2] == ['--selftest']: sys.exit(selftest())
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    sys.exit(run(sys.argv[1], sys.argv[2:]))
