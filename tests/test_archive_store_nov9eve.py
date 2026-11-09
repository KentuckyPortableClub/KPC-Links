#!/usr/bin/env python3
"""Nov 9 evening: KPC-Archive is the store for saved outlines + saved 2-fer answers (kpc_archive.sh). Offline: a local bare repo
stands in for KPC-Archive (KPC_ARCHIVE_URL). No token = exit 2 + a warning (the workflow falls back to the release copy, never fails);
put pushes to main; get reads back; a file over the git limit is left to the release; workflows pass the secret and fall back."""
import os, pathlib, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent.parent
SH = str(HERE / '.github/scripts/kpc_archive.sh')
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
def run(args, env):
    e = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', **env)
    return subprocess.run(['bash', SH] + args, capture_output=True, text=True, env=e, timeout=120)
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(t / 'arch.git')], check=True)
    seed = t / 'seed'; subprocess.run(['git', 'init', '-q', '-b', 'main', str(seed)], check=True)
    (seed / 'README.md').write_text('# KPC-Archive\n')
    g = ['git', '-C', str(seed), '-c', 'user.name=t', '-c', 'user.email=t@t']
    subprocess.run(g + ['add', '-A'], check=True); subprocess.run(g + ['commit', '-qm', 'init'], check=True)
    subprocess.run(g + ['push', '-q', str(t / 'arch.git'), 'main'], check=True)
    r = run(['get', 'outlines', str(t / 'out'), 'US-*.json.gz'], {'KPC_ARCHIVE_TOKEN': ''})
    check(r.returncode == 2 and '::warning title=KPC-Archive::secret KPC_ARCHIVE_TOKEN is not set' in r.stdout, 'no token: exit 2 + a warning (fall back, not fail)')
    env = {'KPC_ARCHIVE_TOKEN': 'x', 'KPC_ARCHIVE_URL': 'file://' + str(t / 'arch.git'), 'KPC_ARCHIVE_MAX': '1000'}
    (t / 'US-KY.json.gz').write_bytes(b'ky' * 10); (t / 'W-DE.json.gz').write_bytes(b'x' * 2000)
    r = run(['put', 'outlines', 'test save', str(t / 'US-KY.json.gz'), str(t / 'W-DE.json.gz')], env)
    check(r.returncode == 0 and 'too big for git' in r.stdout and 'W-DE.json.gz' in r.stdout, 'put: pushed; a file over the limit is left to the release (named)')
    r = run(['get', 'outlines', str(t / 'out'), 'US-*.json.gz', 'W-*.json.gz'], env)
    check(r.returncode == 0 and (t / 'out/US-KY.json.gz').read_bytes() == b'ky' * 10 and not (t / 'out/W-DE.json.gz').exists(), 'get: reads back what was put')
    r = run(['put', 'outlines', 'again', str(t / 'US-KY.json.gz')], env)
    check(r.returncode == 0 and 'nothing new' in r.stdout, 'put of an unchanged file: no empty commit')
    r = run(['get', 'fers', str(t / 'out2'), 'saved-live-x.json.gz'], env)
    check(r.returncode == 2, 'get of a missing file: exit 2 (fall back)')
    r = run(['get', 'outlines', str(t / 'o3'), '*'], dict(env, KPC_ARCHIVE_URL='file:///nonexistent.git'))
    check(r.returncode == 2 and 'could not read' in r.stdout, 'archive not reachable: exit 2 + warning')
W = HERE / '.github/workflows'
for f, need in (('kpc-us-key.yml', 'kpc_archive.sh put outlines'), ('kpc-ca-key.yml', 'kpc_archive.sh put outlines'), ('kpc-boundary-check.yml', 'kpc_archive.sh put outlines')):
    s = (W / f).read_text(encoding='utf-8')
    check(need in s and 'KPC_ARCHIVE_TOKEN: ${{ secrets.KPC_ARCHIVE_TOKEN }}' in s, f'{f}: saves to KPC-Archive with the secret')
    check(s.count('kpc_archive.sh put') == s.count('kpc_archive.sh put outlines') and all('|| ' in ln or '; then' in ln for ln in s.splitlines() if 'kpc_archive.sh put' in ln),
          f'{f}: an archive put never fails the job by itself (fallback on the same line)')
print('ALL PASS' if ok else 'FAILED'); sys.exit(0 if ok else 1)
