#!/usr/bin/env python3
"""Offline test (owner rule, 2026-11-10): kpc_master_cli.py save-check refuses a saved copy that fails the gate baseline or holds
fewer records (in total or for any layer) than the release copy, and allows a first copy only with --first-ok when the release
really has no such asset. Every workflow upload of saved copies (cache/... --clobber, kpc_archive.sh put) runs save-check first.
Temp dirs and made-up copies only."""
import gzip, json, os, pathlib, re, subprocess, sys, tempfile
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
CLI = str(HERE / '.github/scripts/kpc_master_cli.py')
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def copy(path, layers):
    recs = [{'OBJECTID': f'{lay}{i}'} for lay, n in layers.items() for i in range(n)]
    with gzip.open(path, 'wt', encoding='utf-8') as f: json.dump({'recs': recs}, f)


def run(args):
    return subprocess.run([sys.executable, CLI, 'save-check', *args], capture_output=True, text=True)


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); root = t / 'outlines'; root.mkdir(); ag = t / 'against'; ag.mkdir(); new = t / 'new'; new.mkdir()
    (root / 'layers.json').write_text(json.dumps({'format': 1, 'layers': {}, 'caches': {'US-TN': {'expected_count': 10}, 'US-OH': {'expected_count': 5}, 'US-WI': {'expected_count': 3}}}))
    copy(ag / 'US-TN.json.gz', {'': 10, 'tn': 4})
    copy(new / 'US-TN.json.gz', {'': 12, 'tn': 4}); r = run(['--root', str(root), '--against', str(ag), str(new / 'US-TN.json.gz')])
    check(r.returncode == 0, 'a bigger copy that passes the baseline is allowed')
    copy(new / 'US-TN.json.gz', {'': 14, 'tn': 1}); r = run(['--root', str(root), '--against', str(ag), str(new / 'US-TN.json.gz')])
    check(r.returncode != 0 and 'US-TN' in r.stdout and 'tn' in r.stdout, 'a copy that lost a layer (saved-copy-only host) is refused, naming it, even with more records in total')
    copy(new / 'US-TN.json.gz', {'': 9, 'tn': 9}); r = run(['--root', str(root), '--against', str(ag), str(new / 'US-TN.json.gz')])
    check(r.returncode != 0, 'a copy with fewer PAD-US records than the release copy is refused')
    copy(new / 'US-TN.json.gz', {'': 8}); r = run(['--root', str(root), '--against', str(ag), str(new / 'US-TN.json.gz')])
    check(r.returncode != 0 and 'SHORT' in r.stdout.upper(), 'a copy under the gate baseline is refused')
    copy(new / 'US-OH.json.gz', {'': 6})
    r = run(['--root', str(root), '--against', str(ag), str(new / 'US-OH.json.gz')])
    check(r.returncode != 0, 'no release copy and no --first-ok: refused')
    (t / 'assets.txt').write_text('US-TN.json.gz\n')
    r = run(['--root', str(root), '--against', str(ag), '--assets', str(t / 'assets.txt'), '--first-ok', str(new / 'US-OH.json.gz')])
    check(r.returncode == 0, 'a first copy (the release has no such asset) is allowed with --first-ok')
    (t / 'assets.txt').write_text('US-TN.json.gz\nUS-OH.json.gz\n')
    r = run(['--root', str(root), '--against', str(ag), '--assets', str(t / 'assets.txt'), '--first-ok', str(new / 'US-OH.json.gz')])
    check(r.returncode != 0 and 'download failed' in r.stdout, 'the release HAS the copy but it was not downloaded: refused (never a first copy)')
    r = run(['--root', str(root), '--against', str(ag), '--assets', str(t / 'none.txt'), '--first-ok', str(new / 'US-OH.json.gz')])
    check(r.returncode != 0, 'the asset list could not be read: a missing release copy is refused (fail closed)')
    copy(new / 'US-XX.json.gz', {'': 6}); copy(new / 'US-TN.json.gz', {'': 12, 'tn': 4})
    r = run(['--root', str(root), '--against', str(ag), '--first-ok', '--assets', str(t / 'assets.txt'), '--ok-list', str(t / 'ok.txt'), str(new / 'US-TN.json.gz'), str(new / 'US-XX.json.gz')])
    check(r.returncode != 0 and (t / 'ok.txt').read_text().split() == [str(new / 'US-TN.json.gz')], 'no baseline = refused; --ok-list holds only the files that may be uploaded')

# --- every upload of saved copies in a workflow runs save-check first, in the same step
UP = re.compile(r'gh release upload boundary-cache\s+(?!\.mneeds|\.prev)[^\n]*--clobber|kpc_archive\.sh put saved-outlines')
for wf in ('kpc-us-key.yml', 'kpc-ca-key.yml', 'kpc-world-key.yml', 'kpc-geo-cache.yml', 'kpc-world-cache.yml', 'kpc-boundary-check.yml'):
    y = yaml.safe_load(open(HERE / '.github/workflows' / wf))
    for jn, j in y['jobs'].items():
        for s in j.get('steps') or []:
            run_ = str(s.get('run') or '')
            for m in UP.finditer(run_):
                check('save-check' in run_[:m.start()], f'{wf} {jn} / {s.get("name", "?")[:50]}: save-check runs before "{m.group(0)[:50]}"')
ca = (HERE / '.github/workflows/kpc-ca-key.yml').read_text()
check("grep -q 'stopped early" not in ca and '/tmp/ca-key-stopped ]' in ca, 'kpc-ca-key.yml: the upload guard uses the stop marker, not a log line that is never written')
us = (HERE / '.github/workflows/kpc-us-key.yml').read_text()
check('download-held.txt' in us and '--states "$FILL_STATES"' in us, 'kpc-us-key.yml: a release copy that failed to download holds its state (not filled from live)')
for wf in ('kpc-geo-cache.yml', 'kpc-world-cache.yml'):
    s = (HERE / '.github/workflows' / wf).read_text()
    check(s.index('release download') < s.index('kpc_us_key.py' if 'geo' in wf else 'kpc_world_key.py'), f'{wf}: the release copies are downloaded before the refresh read')
uy = yaml.safe_load(us)
fill = next(s for s in uy['jobs']['build']['steps'] if s.get('id') == 'master_fill')['run']
check('if [ "$kpc_rc" = 4 ]' in fill and 'exit 4' in fill, 'kpc-us-key.yml master step: a licence block (exit 4) is red, not a warning')
js = uy['jobs']['join']['steps']; names = [s.get('name', '') for s in js]
mc = next(i for i, s in enumerate(js) if 'kpc_master_cli.py check' in str(s.get('run', '')))
sv = next(i for i, s in enumerate(js) if s.get('name') == 'Save')
check(mc < sv and 'kpc-outlines-bad' in js[mc]['run'] and 'git checkout -q HEAD -- data/outlines' in js[mc]['run'],
      'kpc-us-key.yml join: a failed master check of the joined outlines keeps data/outlines out of the save')
check(any('kpc-outlines-bad' in str(s.get('run', '')) and 'exit 1' in str(s.get('run', '')) and 'always()' in str(s.get('if', '')) for s in js[sv:]), 'kpc-us-key.yml join: and the job goes red')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
