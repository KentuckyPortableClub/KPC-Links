#!/usr/bin/env python3
"""Mapping Rep Tool Box: search, abbreviations, and the rules check.
Also checks rules hashes match origin/main and the key files are byte-unchanged, unless docs/key-rules-change.txt declares a rules change."""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True

def check(cond, msg):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)

file_check = r'''
const fs = require('fs');
const L = require('./kpc-maprep-logic.js');
const j = JSON.parse(fs.readFileSync('ky-hunting-areas.geojson', 'utf8'));
const names = j.features.map(f => (f.properties || {}).NAME).filter(Boolean);
const hits = L.searchNames('Blackford Oaks W.M.A.', names.map(n => ({name: n})));
if (!hits.some(h => h.name === 'Blackford Oaks WMA' && h.score >= 90)) {
  console.log('SOME FAILED blackford file');
  process.exit(1);
}
const muddy = L.searchNames('Muddygut WMA', L.WATCH);
if (!muddy.some(h => /Muddygut/.test(h.name))) {
  console.log('SOME FAILED muddygut watch');
  process.exit(1);
}
console.log('PASS saved Kentucky names');
'''
f = subprocess.run(['node', '-e', file_check], cwd=ROOT, capture_output=True, text=True, timeout=60)
check(f.returncode == 0 and 'PASS saved Kentucky names' in f.stdout, 'Blackford Oaks W.M.A. is in the Kentucky file and Muddygut WMA is on the watch list: ' + (f.stdout.strip() or f.stderr.strip() or '?'))

r = subprocess.run(['node', str(ROOT / 'kpc-maprep-logic.js')], cwd=ROOT, capture_output=True, text=True, timeout=60)
check(r.returncode == 0 and 'PASS maprep toolbox selftest' in r.stdout and 'SOME FAILED' not in r.stdout,
      'logic selftest: ' + (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or ['?'])[-1])

cat = json.loads((ROOT / 'data/maprep/catalog.json').read_text())
live = [s for s in cat['sources'] if s.get('live')]
check(any(s.get('region') == 'CA' and s.get('live') for s in live), 'a Canada source is live')
check(any(s.get('origin') == 'camp-layers' and s.get('place') == 'IA' for s in live), 'Iowa agency layer is live')
check(any(s.get('origin') == 'camp-layers' and s.get('place') == 'MN' for s in live), 'Minnesota agency layer is live')
check(any(s.get('origin') == 'camp-layers' and s.get('place') == 'WI' for s in live), 'Wisconsin agency layer is live')
check(all('33TOOklri9xpic7U' not in ((s.get('rest') or '') + (s.get('download') or '')) for s in cat['sources']), 'Grant County NM server is absent')
check(all(s.get('place') not in ('CO', 'TN') for s in live), 'Colorado and Tennessee are not queried live')
check(cat['regions']['US']['enabled'] and cat['regions']['CA']['enabled'] and not cat['regions']['AU']['enabled'], 'US and Canada on, other countries off')

import tempfile
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_key_freeze as KF

# Answer-key guard. Default on every branch, never a silent skip.
# (a) rules hashes equal origin/main (today us a066624520b4, ca 8feccbb7d9ee, world 1b50faf1dfe8).
# (b) data/us-key, data/ca-key, data/world-key and data/ky-answer-key.json are byte-unchanged vs origin/main.
# A branch that changes rules on purpose is exempt only when it adds or changes docs/key-rules-change.txt.
EXPECTED_RULES = {'us-key': 'a066624520b4', 'ca-key': '8feccbb7d9ee', 'world-key': '1b50faf1dfe8'}
KEY_PATHS = ['data/us-key', 'data/ca-key', 'data/world-key', 'data/ky-answer-key.json']
DECL_REL = 'docs/key-rules-change.txt'

def _git_show(rev, rel):
    r = subprocess.run(['git', 'show', f'{rev}:{rel}'], cwd=ROOT, capture_output=True, timeout=30)
    return r.stdout if r.returncode == 0 else None

def rules_hash_at(rev, kind):
    rels = list(KF.RULE_FILES[kind]) + [KF.VERSION_FILE]
    with tempfile.TemporaryDirectory() as td:
        base = pathlib.Path(td)
        for rel in rels:
            blob = _git_show(rev, rel)
            if blob is None:
                continue
            dest = base / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(blob)
        return KF.rules_hash(kind, base)

def declaration_exemption(root, main_rev='origin/main'):
    """The first line when this root adds or changes docs/key-rules-change.txt, else None."""
    path = pathlib.Path(root) / DECL_REL
    if not path.is_file():
        return None
    lines = [ln.strip() for ln in path.read_text(encoding='utf-8').splitlines() if ln.strip()]
    if not lines:
        return None
    main_blob = _git_show(main_rev, DECL_REL)
    if main_blob is not None and main_blob == path.read_bytes():
        return None
    return lines[0]

def answer_key_guard(root, main_rev='origin/main'):
    """(passed, message). Hash and key-file bytes, unless a declaration file was added or changed."""
    first = declaration_exemption(root, main_rev)
    if first:
        line = 'EXEMPT: key rules change declared in docs/key-rules-change.txt: ' + first
        print(line)
        return True, line
    problems = []
    for kind, exp in EXPECTED_RULES.items():
        here = KF.rules_hash(kind, root)
        there = rules_hash_at(main_rev, kind)
        if here != there or here != exp:
            problems.append(f'{kind} rules hash {here} != origin/main {there} (expected {exp})')
    if pathlib.Path(root).resolve() == ROOT.resolve():
        diff = subprocess.run(['git', 'diff', '--name-only', main_rev, '--', *KEY_PATHS],
                              cwd=ROOT, capture_output=True, text=True, timeout=30)
        names = [ln for ln in diff.stdout.splitlines() if ln.strip()]
        other = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard', '--', *KEY_PATHS],
                               cwd=ROOT, capture_output=True, text=True, timeout=30)
        names += [ln for ln in other.stdout.splitlines() if ln.strip()]
        if diff.returncode != 0:
            problems.append('could not compare key files to origin/main')
        elif names:
            problems.append('key files changed vs origin/main: ' + ', '.join(names[:8]))
    if problems:
        return False, '; '.join(problems)
    return True, 'rules hashes match origin/main and key files are byte-unchanged'

have = subprocess.run(['git', 'rev-parse', '--verify', 'origin/main'], cwd=ROOT, capture_output=True, text=True, timeout=20)
if have.returncode != 0:
    fetch = subprocess.run(['git', 'fetch', 'origin', 'main'], cwd=ROOT, capture_output=True, text=True, timeout=60)
    check(fetch.returncode == 0, 'fetched origin/main: ' + ((fetch.stderr or fetch.stdout or 'fetch failed').strip().splitlines() or ['?'])[-1])
check(not (ROOT / DECL_REL).exists(), '#49 does not add docs/key-rules-change.txt')
passed, msg = answer_key_guard(ROOT)
check(passed, 'this branch passes the real answer-key guard (' + msg + ')')

def scratch_rules_root():
    td = tempfile.TemporaryDirectory()
    base = pathlib.Path(td.name)
    rels = {KF.VERSION_FILE}
    for kind in EXPECTED_RULES:
        rels.update(KF.RULE_FILES[kind])
    for rel in rels:
        dest = base / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / rel).read_bytes())
    rules = base / '.github/scripts/kpc_key_rules.py'
    rules.write_bytes(rules.read_bytes() + b'\n# scratch rules edit for the guard test\n')
    return td, base

_td, scratch = scratch_rules_root()
passed, msg = answer_key_guard(scratch)
check(not passed and not msg.startswith('EXEMPT:'), 'scratch rules edit with no declaration fails the guard (' + msg + ')')
(scratch / 'docs').mkdir(parents=True, exist_ok=True)
(scratch / DECL_REL).write_text('PR 44: rules change on purpose, tract store\n', encoding='utf-8')
passed, msg = answer_key_guard(scratch)
check(passed and msg == 'EXEMPT: key rules change declared in docs/key-rules-change.txt: PR 44: rules change on purpose, tract store',
      'scratch declaration exempts the same rules edit (' + msg + ')')
_td.cleanup()
ag = json.loads((ROOT / 'data/maprep/agencies.json').read_text())
NEED = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY AB BC MB NB NL NT NS NU ON PE QC SK YT'.split()
missing_place = [c for c in NEED if not (ag.get('places', {}).get(c) or {}).get('agencies')]
check(not missing_place, 'every state and province has an agency row' + ((' missing ' + ', '.join(missing_place)) if missing_place else ''))
check('33TOOklri9xpic7U' not in json.dumps(ag), 'agency directory does not list the banned server')
gaps = ROOT / 'docs/maprep-agency-gaps.txt'
check(gaps.exists() and gaps.stat().st_size > 40, 'gap list for the outside researcher exists')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
