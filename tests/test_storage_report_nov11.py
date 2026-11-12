#!/usr/bin/env python3
"""tools/kpc_storage_report.py (KPC owner, 2026-11-11): the read-only storage report. Offline: builds throwaway git repos in a temp
folder (file:// only), runs the tool on them, checks what it prints and the CSVs it writes OUTSIDE the repo, and that it changes
nothing: no file in the measured repo, no git objects fetched (a blobless clone stays blobless), no network."""
import csv, os, pathlib, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools' / 'kpc_storage_report.py'
fails = 0


def check(name, ok, extra=''):
    global fails
    print(('PASS' if ok else 'FAIL') + ': ' + name + (f' ({extra})' if extra and not ok else ''))
    fails += 0 if ok else 1


ENV = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.invalid', GIT_COMMITTER_NAME='t',
           GIT_COMMITTER_EMAIL='t@example.invalid', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_ALLOW_PROTOCOL='file')


def git(cwd, *a):
    r = subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True, env=ENV)
    if r.returncode: raise RuntimeError(f'git {a}: {r.stderr}')
    return r.stdout


def run(*a, cwd=None):
    r = subprocess.run([sys.executable, '-B', str(TOOL), *map(str, a)], capture_output=True, text=True, cwd=cwd, timeout=120)
    return r.returncode, r.stdout + r.stderr


def rows(path):
    with open(path, newline='', encoding='utf-8') as fh: return list(csv.DictReader(fh))


def status(repo):
    return subprocess.run(['git', 'status', '--porcelain', '--untracked-files=all', '--ignored'], cwd=repo, capture_output=True, text=True, env=ENV).stdout


tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-storage-test-'))
try:
    src = tmp / 'src'; src.mkdir()
    git(src, 'init', '-q', '-b', 'main')
    git(src, 'config', 'uploadpack.allowFilter', 'true'); git(src, 'config', 'uploadpack.allowAnySHA1InWant', 'true')
    w = lambda rel, data: ((src / rel).parent.mkdir(parents=True, exist_ok=True), (src / rel).write_bytes(data if isinstance(data, bytes) else data.encode()))
    import gzip
    w('index.html', '<script src="app.js"></script><img src="img/logo.png"><a href="data/keys/">keys</a>')
    w('app.js', "fetch('data/keys/' + st + '.json'); fetch('data/big.json'); var bg = 'bg-' + k + '.jpg';")
    w('img/logo.png', b'\x89PNG' + b'L' * 5000)
    w('old-banner.png', b'\x89PNG' + b'O' * 7000)
    w('img/folder-only.png', b'\x89PNG' + b'F' * 6000)
    w('bg-forest.jpg', b'\xff\xd8' + b'J' * 3000)
    w('about-mobile.png', b'\x89PNG' + b'M' * 9000)
    w('about.png', b'\x89PNG' + b'A' * 4000)
    w('data/big.json', '{"x": "' + 'b' * 3000 + '"}')          # over a 2,000-byte cap
    w('data/near.json', '{"x": "' + 'n' * 1880 + '"}')         # within 90 % of it
    w('data/keys/US-KY.json', '{"k": "' + 'k' * 6000 + '"}')
    w('data/copy/US-KY.json', '{"k": "' + 'k' * 6000 + '"}')    # same content, other path
    w('data/released/a.json', '{"r": "' + 'r' * 5000 + '"}'); w('data/work/a.json', '{"r": "' + 'r' * 5000 + '"}')
    w('data/x.json', '{"a": 1}'); w('data/x.json.gz', gzip.compress(b'{"a": 1}', mtime=0))
    w('notes-nov7.md', 'dated one-off')
    w('.claude/notes/a.md', 'note')
    w('.github/workflows/w.yml', 'on: push\njobs: {}\n')
    git(src, 'add', '-A'); git(src, 'commit', '-qm', 'first')
    for i in range(3):   # the .gz and a JSON file are saved three more times
        w('data/x.json.gz', gzip.compress(('{"a": %d}' % (i + 2)).encode() * 50, mtime=0))
        w('data/keys/US-KY.json', '{"k": "' + 'k' * 6000 + str(i) + '"}')
        git(src, 'add', '-A'); git(src, 'commit', '-qm', f'save {i}')

    out = tmp / 'report'
    before = status(src)
    rc, text = run(src, '--cap', 2000, '--since', '10 years ago', '--out', out)
    check('runs on a git checkout (exit 0)', rc == 0, text[-300:])
    check('the measured repo is unchanged (git status, ignored files too)', status(src) == before)
    check('prints the total and the folder table', 'tracked:' in text and 'by top-level folder' in text)
    for f in ('by_folder', 'by_data_subfolder', 'by_type', 'biggest', 'over_and_near_cap', 'duplicates', 'near_duplicates',
              'unreferenced_candidates', 'churn'):
        check(f'writes {f}.csv outside the repo', (out / f'{f}.csv').is_file())
    check('writes summary.txt', (out / 'summary.txt').is_file())
    cap = {r['path']: r['state'] for r in rows(out / 'over_and_near_cap.csv')}
    check('a file over the cap is listed as over', cap.get('data/big.json') == 'over', cap)
    check('a file within 90 % of the cap is listed as near', cap.get('data/near.json') == 'near', cap)
    dup = rows(out / 'duplicates.csv')
    check('the same content at two paths is one duplicate group', any(set(r['paths'].split(' | ')) == {'data/released/a.json', 'data/work/a.json'} for r in dup), dup)
    # the working key changed after the first commit, so at HEAD the two copies differ: the group must NOT be there
    check('a copy that has since changed is not a duplicate any more', not any('data/keys/US-KY.json' in r['paths'] for r in dup), dup)
    nd = rows(out / 'near_duplicates.csv')
    kinds = {(r['kind'], r['path']) for r in nd}
    check('x.json next to x.json.gz is a near-duplicate', ('plain and .gz copy', 'data/x.json.gz') in kinds, kinds)
    check('a -mobile picture is a near-duplicate with its twin', any(r['kind'] == 'mobile picture' and r['twin'] == 'about.png' for r in nd))
    check('a dated file name is listed', ('dated file name', 'notes-nov7.md') in kinds)
    check('.claude/ is listed as a whole folder', any(r['kind'].startswith('.claude/') for r in nd))
    cand = {r['path'] for r in rows(out / 'unreferenced_candidates.csv')}
    check('a picture nothing names (not even its folder) is an unreferenced candidate', 'old-banner.png' in cand, cand)
    check('a picture a page names is not a candidate', 'img/logo.png' not in cand)
    check('a picture in a folder a page names is folder-referenced, not a candidate (heuristic)', 'img/folder-only.png' not in cand)
    check("a name built from a prefix ('bg-' + k) is not a candidate", 'bg-forest.jpg' not in cand)
    check('a file in a folder the code names is not a candidate', 'data/keys/US-KY.json' not in cand)
    ch = {r['path']: r for r in rows(out / 'churn.csv')}
    check('churn counts real saves only (the first commit is not a save)', ch.get('data/x.json.gz', {}).get('saves') == '3', ch.get('data/x.json.gz'))
    check('a .gz churner is flagged as compressed', ch.get('data/x.json.gz', {}).get('git_delta', '').startswith('maybe'))
    check('the real history cost of a top churner is measured (git pack-objects --stdout)', (ch.get('data/x.json.gz', {}).get('measured_bytes_per_save') or '').isdigit(), ch.get('data/x.json.gz'))
    check('a JSON churner is marked as delta-friendly', ch.get('data/keys/US-KY.json', {}).get('git_delta', '').startswith('yes'))

    # never writes into the tree
    rc, text = run(src, '--out', src / 'report-here')
    check('--out inside the repo is refused (exit 2)', rc == 2 and 'refused' in text, text[-200:])
    check('... and nothing was written', not (src / 'report-here').exists() and status(src) == before)
    rc, text = run(src, '--no-refs')
    check('without --out nothing is written and it says so', rc == 0 and 'nothing written' in text and status(src) == before)

    # a shallow clone: the cut-off end lists every file, it must not count as a save; the report says the history is short
    sh = tmp / 'shallow'
    git(tmp, 'clone', '-q', '--depth', '2', (src.as_uri()), str(sh))
    rc, text = run(sh, '--since', '10 years ago', '--out', tmp / 'r-sh')
    check('runs on a shallow clone', rc == 0, text[-300:])
    check('says the clone is shallow', 'SHALLOW' in text and 'shallow clone' in text)
    ch = {r['path']: r for r in rows(tmp / 'r-sh' / 'churn.csv')}
    check('the shallow cut-off commit is not counted as a save', ch.get('data/x.json.gz', {}).get('saves') == '1' and 'img/logo.png' not in ch, ch)

    # a blobless --no-checkout clone with --rev: measures from git, never fetches a missing blob
    bl = tmp / 'blobless'
    git(tmp, 'clone', '-q', '--filter=blob:none', '--no-checkout', src.as_uri(), str(bl))
    count = lambda: git(bl, 'count-objects', '-v')
    c0 = count()
    rc, text = run(bl, '--rev', 'HEAD', '--since', '10 years ago', '--out', tmp / 'r-bl')
    check('runs on a blobless --no-checkout clone with --rev', rc == 0, text[-300:])
    check('says it is a partial clone and some sizes are unknown', 'partial' in text and 'unknown' in text, text[:600])
    check('fetched NO object (count-objects unchanged)', count() == c0, c0 + ' / ' + count())
    check('a blobless clone measures no history cost (the versions are not local) and does not fail', all(r.get('measured_bytes_per_save') == '' for r in rows(tmp / 'r-bl' / 'churn.csv')) and count() == c0)
    full = tmp / 'nocheckout'
    git(tmp, 'clone', '-q', '--no-checkout', src.as_uri(), str(full))
    rc, text = run(full, '--rev', 'HEAD', '--cap', 2000, '--out', tmp / 'r-nc')
    cap = {r['path']: r['state'] for r in rows(tmp / 'r-nc' / 'over_and_near_cap.csv')}
    check('--rev on a --no-checkout clone measures the commit (over-cap file found)', rc == 0 and cap.get('data/big.json') == 'over', text[-200:])
    check('... and reads page text from git for the reference scan', 'old-banner.png' in {r['path'] for r in rows(tmp / 'r-nc' / 'unreferenced_candidates.csv')})

    # a plain folder (not git): sha1 for files over --hash-min, --all hashes every file, --compare finds same content in another checkout
    plain = tmp / 'plain'; shutil.copytree(src, plain, ignore=shutil.ignore_patterns('.git'))
    (plain / 'data' / 'dup-small.txt').write_text('tiny'); (plain / 'data' / 'dup-small2.txt').write_text('tiny')
    rc, text = run(plain, '--out', tmp / 'r-pl')
    check('runs on a folder that is not a git checkout', rc == 0 and 'not a git checkout' in text, text[-300:])
    d = rows(tmp / 'r-pl' / 'duplicates.csv')
    check('small files are not hashed by default', not any('dup-small' in r['paths'] for r in d))
    rc, text = run(plain, '--all', '--out', tmp / 'r-pl2')
    check('--all hashes small files too (the tiny pair is found)', any('dup-small.txt' in r['paths'] for r in rows(tmp / 'r-pl2' / 'duplicates.csv')))
    rc, text = run(src, '--compare', full, '--compare-rev', 'HEAD', '--out', tmp / 'r-cmp', '--no-refs')
    cmp_rows = rows(tmp / 'r-cmp' / 'compare.csv')
    check('--compare lists files with the same content at the same path in both', rc == 0 and any(r['kind'] == 'same path' and r['path_in_other'] == 'index.html' for r in cmp_rows), text[-300:])
    rc, text = run(src, '--history-objects', '--out', tmp / 'r-ho', '--no-refs')
    check('--history-objects lists the biggest objects of all local history', rc == 0 and (tmp / 'r-ho' / 'history_by_path.csv').is_file() and 'history objects:' in text)
    src_txt = TOOL.read_text(encoding='utf-8')
    check('the tool imports no network module', not any(m in src_txt for m in ('import urllib', 'import socket', 'import http', 'import requests', 'urlopen(')))
    check('the tool runs no git command that writes or talks to a remote', not any(f"'{c}'" in src_txt for c in ('fetch', 'pull', 'push', 'commit', 'add', 'gc', 'repack', 'checkout', 'reset', 'prune')))
    check("pack-objects is only ever used with --stdout (nothing written)", src_txt.count("'pack-objects'") == 1 and "'pack-objects', '--stdout'" in src_txt)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('ALL PASSED' if not fails else f'SOME FAILED ({fails})')
sys.exit(1 if fails else 0)
