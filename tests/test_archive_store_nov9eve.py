#!/usr/bin/env python3
"""Nov 9 evening: KPC-Archive is the store for saved outlines + saved 2-fer answers (kpc_archive.sh). Offline: a local bare repo
stands in for KPC-Archive's git index and a stand-in gh for its releases. Outlines are release assets (outside the 500 MB git cap); git keeps a small index. No token = exit 2 + a warning (the workflow falls back to the release copy, never fails);
put pushes to main; get reads back; a file over the git limit is left to the release; workflows pass the secret and fall back."""
import json, os, pathlib, subprocess, sys, tempfile
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
    # a stand-in 'gh' (releases kept in a folder) and a local bare repo for the git index
    rel = t / 'rel'; rel.mkdir(); bin_ = t / 'bin'; bin_.mkdir()
    (bin_ / 'gh').write_text("""#!/usr/bin/env python3
import os, shutil, sys, pathlib
R = pathlib.Path(os.environ['FAKE_REL']); a = sys.argv[1:]
open(R / 'calls.log', 'a').write(' '.join(a) + ' TOKEN=' + os.environ.get('GH_TOKEN', '') + '\\n')
if a[:2] == ['release', 'view']: sys.exit(0 if (R / a[2]).is_dir() else 1)
if a[:2] == ['release', 'create']: (R / a[2]).mkdir(); sys.exit(0)
if a[:2] == ['release', 'upload']:
    if not (R / a[2]).is_dir(): sys.exit(1)
    for f in a[3:]:
        if f.startswith('-'): break
        shutil.copy(f, R / a[2])
    sys.exit(0)
if a[:2] == ['release', 'download']:
    import fnmatch
    d = R / a[2]; pats = [a[i + 1] for i, x in enumerate(a) if x == '-p']; dest = pathlib.Path(a[a.index('-D') + 1])
    got = [f for f in (d.iterdir() if d.is_dir() else []) if any(fnmatch.fnmatch(f.name, p) for p in pats)]
    for f in got: shutil.copy(f, dest)
    sys.exit(0 if got else 1)
sys.exit(1)
""")
    (bin_ / 'gh').chmod(0o755)
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(t / 'arch.git')], check=True)
    seed = t / 'seed'; subprocess.run(['git', 'init', '-q', '-b', 'main', str(seed)], check=True)
    (seed / 'README.md').write_text('# KPC-Archive\n')
    g = ['git', '-C', str(seed), '-c', 'user.name=t', '-c', 'user.email=t@t']
    subprocess.run(g + ['add', '-A'], check=True); subprocess.run(g + ['commit', '-qm', 'init'], check=True)
    subprocess.run(g + ['push', '-q', str(t / 'arch.git'), 'main'], check=True)
    base = {'PATH': str(bin_) + os.pathsep + os.environ['PATH'], 'FAKE_REL': str(rel)}
    r = run(['get', 'saved-outlines', str(t / 'out'), 'US-*.json.gz'], dict(base, KPC_ARCHIVE_TOKEN=''))
    check(r.returncode == 2 and '::warning title=KPC-Archive::secret KPC_ARCHIVE_TOKEN is not set' in r.stdout, 'no token: exit 2 + a warning (fall back, not fail)')
    env = dict(base, KPC_ARCHIVE_TOKEN='tok', KPC_ARCHIVE_URL='file://' + str(t / 'arch.git'), GITHUB_RUN_ID='77')
    (t / 'US-KY.json.gz').write_bytes(b'ky' * 10); (t / 'CA-ALL.json.gz').write_bytes(b'ca' * 5)
    r = run(['put', 'saved-outlines', 'test save', str(t / 'US-KY.json.gz'), str(t / 'CA-ALL.json.gz')], env)
    check(r.returncode == 0 and (rel / 'saved-outlines/US-KY.json.gz').exists(), 'put: the outlines go to a RELEASE on KPC-Archive (made if missing), not into git')
    chk = t / 'chk'; subprocess.run(['git', 'clone', '-q', str(t / 'arch.git'), str(chk)], check=True)
    idx = json.loads((chk / 'index/saved-outlines.json').read_text())
    tracked = subprocess.run(['git', '-C', str(chk), 'ls-files'], capture_output=True, text=True).stdout.split()
    check(idx['files']['US-KY.json.gz']['bytes'] == 20 and idx['files']['US-KY.json.gz']['run'] == '77' and len(idx['files']['CA-ALL.json.gz']['sha256']) == 64
          and idx['total_bytes'] == 30 and not any(x.endswith('.json.gz') for x in tracked), 'git keeps only the small index (bytes, sha256, date, run); no outline file in git')
    check('TOKEN=tok' in (rel / 'calls.log').read_text(), 'the archive token is what gh uses (not the workflow token)')
    r = run(['get', 'saved-outlines', str(t / 'out'), 'US-*.json.gz'], env)
    check(r.returncode == 0 and (t / 'out/US-KY.json.gz').read_bytes() == b'ky' * 10, 'get: reads the release asset back')
    r = run(['put', 'saved-outlines', 'again', str(t / 'US-KY.json.gz')], env)
    check(r.returncode == 0 and ('unchanged' in r.stdout or 'saved' in r.stdout), 'a second put: same release, index updated or unchanged')
    r = run(['get', 'fers-saved-live', str(t / 'out2'), 'saved-live-x.json.gz'], env)
    check(r.returncode == 2, 'get of a missing release / file: exit 2 (fall back)')
W = HERE / '.github/workflows'
for f, need in (('kpc-us-key.yml', 'kpc_archive.sh put saved-outlines'), ('kpc-ca-key.yml', 'kpc_archive.sh put saved-outlines'), ('kpc-boundary-check.yml', 'kpc_archive.sh put saved-outlines')):
    s = (W / f).read_text(encoding='utf-8')
    check(need in s and 'KPC_ARCHIVE_TOKEN: ${{ secrets.KPC_ARCHIVE_TOKEN }}' in s, f'{f}: saves to KPC-Archive with the secret')
    check(s.count('kpc_archive.sh put') == s.count('kpc_archive.sh put saved-outlines') and all('|| ' in ln or '; then' in ln for ln in s.splitlines() if 'kpc_archive.sh put' in ln),
          f'{f}: an archive put never fails the job by itself (fallback on the same line)')
print('ALL PASS' if ok else 'FAILED'); sys.exit(0 if ok else 1)
