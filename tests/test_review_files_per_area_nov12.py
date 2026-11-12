#!/usr/bin/env python3
"""Nov 12 (KPC owner, 2026-11-12), A0: the review files are merged PER COUNTRY / STATE / PROVINCE after the join check, on EVERY run.
kpc_join_check.py run() (main 52a51ddc :326-372) builds its rows only from the key files this run changed and writes join-check.json /
.csv and held-joins.json / .csv / -ledger.csv WHOLE; the world workflow put rows back only for the expected holds. So a perfectly green run
of some countries (countries=BE CH PT) dropped every other country's rows (the a6c493c wipe without a cancel), and a US states= run did the
same to every other state. Checked here (offline, temp folders): a green subset run of 3 countries leaves every other country's rows in
all five files byte-identical and REPLACES (never duplicates) the three countries' rows; expected holds, held / failed countries and a
country rebuilt to the same bytes keep their rows; a US states= run and a Canada run the same per state / province; the workflows call
the merge on every built run. Run: python3 -B tests/test_review_files_per_area_nov12.py"""
import contextlib, io, json, os, pathlib, re, subprocess, sys, tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.github/scripts'
sys.path.insert(0, str(SCRIPTS))
import kpc_world_key_join as J  # noqa: E402
import kpc_area_join as AJ  # noqa: E402
import kpc_join_check as JC  # noqa: E402
ok = True


def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name, flush=True)
    ok = ok and bool(cond)


def git(t, *a): return subprocess.run(['git', *a], cwd=t, capture_output=True, text=True)


def snapshot(t, sub='data'):
    return {str(p.relative_to(t)): p.read_bytes() for p in sorted((t / sub).rglob('*')) if p.is_file()}


def mkrepo(t, countries, extra_index=None):
    import csv
    wk = t / 'data/world-key'; (wk / 'review').mkdir(parents=True); (wk / 'tracts').mkdir(); (t / 'data/world-bounds').mkdir(parents=True)
    for c in countries:
        (wk / f'{c}.json').write_text(json.dumps({'parks': {f'{c}-0001': {'n': f'{c} park', 'm': [[1, 'x', 'L']], 'g': 'official', 'bk': [1, 0.2]},
                                                            f'{c}-0002': {'n': f'{c} far', 'g': 'pin', 'm': [], 'c': [[2, 'y', 'L', 'held: far']]}}}, separators=(',', ':')))
        (wk / 'tracts' / f'{c}.json').write_text('{"about":"t","area":"%s"}' % c); (wk / 'review' / f'{c}.md').write_text(f'review {c} main\n')
    idx = {'countries': {c: {'parks': 2, 'old': True} for c in countries}, 'build': 'W-1', 'built': '2026-11-11 00:00 UTC', 'rules': '487a51327b86'}
    idx.update(extra_index or {})
    (wk / 'index.json').write_text(json.dumps(idx, indent=1))
    held = [{'park': f'{c}-0002', 'area': c, 'name': f'{c} far – é', 'pin_km': 30.0, 'reason': 'far, "q"'} for c in countries]
    rows = [{'park': f'{c}-0001', 'area': c, 'name': f'{c}, park', 'pin_km': 16.0, 'suspect': 'far'} for c in countries]
    (wk / 'review/held-joins.json').write_text(json.dumps({'key': 'world', 'count': len(held), 'parks': held}, indent=1, ensure_ascii=False))
    (wk / 'review/join-check.json').write_text(json.dumps({'key': 'world', 'suspect': len(rows), 'held': len(held), 'rows': rows}, indent=1, ensure_ascii=False))
    for name, cols, data in (('held-joins.csv', list(held[0]), held), ('join-check.csv', list(rows[0]), rows),
                             ('held-joins-ledger.csv', ['park', 'kind', 'proposal'], [{'park': h['park'], 'kind': 'pile-enter', 'proposal': 'p\nmulti'} for h in held])):
        with open(wk / 'review' / name, 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(data)
    git(t, 'init', '-q'); git(t, 'add', '-A'); git(t, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'main')


def mkpart(t, i, countries, done=None, rc='0', short='', held=()):
    d = t / 'parts' / f'world-key-part-{i}'; (d / 'world-key' / 'review').mkdir(parents=True, exist_ok=True); (d / 'world-bounds').mkdir(exist_ok=True)
    done = list(countries if done is None else done)
    if short: done = [c for c in done]   # a gate-held country may still be built (the old AU shard) or not
    (d / 'countries.txt').write_text(' '.join(countries) + '\n'); (d / 'failed.txt').write_text(''.join(c + '\n' for c in countries if c not in done))
    (d / 'done.txt').write_text(''.join(c + '\n' for c in done)); (d / 'held.txt').write_text(''.join(c + '\n' for c in held))
    idx = {}
    for c in done:
        (d / 'world-key' / f'{c}.json').write_text(json.dumps({'parks': {f'{c}-0001': {'n': f'{c} park', 'm': [[1, 'x', 'L'], [3, 'z', 'L']], 'g': 'official', 'bk': [1, 0.1]}}}))
        (d / 'world-key' / 'review' / f'{c}.md').write_text(f'review {c} new')
        (d / 'world-bounds' / c).mkdir(); (d / 'world-bounds' / c / 'a.json').write_text('{}')
        idx[c] = {'parks': 1, 'new': i}
    (d / 'world-key' / 'index.json').write_text(json.dumps({'countries': idx}))
    (t / f'rc{i}').write_text(rc + '\n'); (t / f'short{i}').write_text(short)
    with contextlib.redirect_stdout(io.StringIO()):
        J.main_verdict(['verdict', '--part', str(d), '--countries', ' '.join(countries), '--rc-file', str(t / f'rc{i}'), '--short-file', str(t / f'short{i}')])
    return d


PARKS = {}   # park -> area, from every held-joins text seen (the ledger rows name only the park)


def rows_of(text, cc, name):
    if name.startswith('held-joins.'): PARKS.update(AJ.park_areas(text))
    if name.endswith('.json'):
        d = json.loads(text)
        return [json.dumps(r, sort_keys=True) for r in d.get('parks', d.get('rows', [])) if AJ.row_area(r, name, PARKS) == cc]
    return [raw for raw, r in AJ.csv_records(text)[1] if AJ.row_area(r, name, PARKS) == cc]


def mkrepo_jc(t, countries):
    """main as a real join check wrote it: each country has one far join (held) and one 16 km join (suspect)."""
    wk = t / 'data/world-key'; (wk / 'review').mkdir(parents=True); (wk / 'tracts').mkdir(); (t / 'data/world-bounds').mkdir(parents=True)
    for c in countries:
        (wk / f'{c}.json').write_text(json.dumps({'parks': {f'{c}-0001': {'n': f'{c} park', 'm': [[1, 'x', 'L']], 'g': 'official', 'bk': [1, 16.0]},
                                                            f'{c}-0002': {'n': f'{c} far', 'g': 'official', 'm': [[2, 'y', 'L']], 'bk': [2, 30.0]}}}))
        (wk / 'tracts' / f'{c}.json').write_text('{}'); (wk / 'review' / f'{c}.md').write_text(f'review {c}\n')
    (wk / 'index.json').write_text(json.dumps({'countries': {c: {'parks': 2} for c in countries}, 'build': 'W-1', 'built': 'x', 'rules': '487a51327b86'}, indent=1))
    with contextlib.redirect_stdout(io.StringIO()): JC.run({'KEY': 'world', 'ALL': '1', 'ANSWER_SHEET': str(t / 'none')}, root=str(t), plain=True)
    git(t, 'init', '-q'); git(t, 'add', '-A'); git(t, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'main')

ALL = ['AT', 'BE', 'CH', 'CZ', 'DE', 'FR', 'NL', 'PT']


def join_and_check(t, parts, groups, expected=''):
    import kpc_save
    cwd = os.getcwd(); os.chdir(t)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc = J.main([*map(str, parts), '--gate', '--held-out', str(t / 'held.txt'), '--out', str(t / 'data/world-key'), '--bounds', str(t / 'data/world-bounds'),
                         '--failed-out', str(t / 'failed.txt'), '--planned-groups', groups, '--expected', expected])
            JC.run({'KEY': 'world', 'ANSWER_SHEET': str(t / 'none')}, root=str(t), plain=True)
            wiped = {n: (t / 'data/world-key/review' / n).read_bytes().decode() for n in AJ.REVIEW_FILES}
            AJ.main(['keep-rows', '--unchanged', '--areas', expected, '--key-dir', str(t / 'data/world-key'), '--review', str(t / 'data/world-key/review')])
        kpc_save.flush_status()
    finally: os.chdir(cwd)
    return rc, wiped


# 1) the owner's case: a GREEN run of only BE CH PT (+ AU expected hold), every shard green
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo_jc(t, ALL + ['AU']); before = snapshot(t)
    # the three get a far join so the join check writes NEW rows for them (their old rows must be replaced, not kept twice)
    p0 = mkpart(t, 0, ['BE', 'CH', 'PT'])
    for c in ('BE', 'CH', 'PT'):   # this run's BE CH PT keys hold a new far join, so the join check writes NEW rows for them
        (p0 / f'world-key/{c}.json').write_text(json.dumps({'parks': {f'{c}-0009': {'n': f'{c} new far', 'g': 'official', 'm': [[9, 'z', 'L']], 'bk': [9, 50.0]}}}))
    with contextlib.redirect_stdout(io.StringIO()): J.main_verdict(['verdict', '--part', str(p0), '--countries', 'BE CH PT', '--rc-file', str(t / 'rc0'), '--short-file', str(t / 'short0')])
    rc, wiped = join_and_check(t, [p0], json.dumps([{'i': 0, 'countries': 'BE CH PT', 'cmin': ''}]), expected='AU')
    aft = snapshot(t)
    check('subset run BE CH PT: the join saves the three (exit 0)', rc == 0 and all(aft[f'data/world-key/{c}.json'] != before[f'data/world-key/{c}.json'] for c in ('BE', 'CH', 'PT')))
    check('(without the merge, the join check alone dropped the other countries\' rows: the wipe A0 closes)', 'FR-0002' not in wiped['held-joins.csv'] and 'FR-0001' not in wiped['join-check.csv'])
    for name in AJ.REVIEW_FILES:
        mt, nt = before[f'data/world-key/review/{name}'].decode(), aft[f'data/world-key/review/{name}'].decode()
        same = all(rows_of(mt, c, name) == rows_of(nt, c, name) and rows_of(mt, c, name) for c in ALL + ['AU'] if c not in ('BE', 'CH', 'PT'))
        check(f'review/{name}: every other country\'s rows (incl. the AU expected hold) byte-identical to main', same)
        rep = all(rows_of(nt, c, name) == rows_of(wiped[name], c, name) and not set(rows_of(mt, c, name)) & set(rows_of(nt, c, name)) for c in ('BE', 'CH', 'PT'))
        if name.startswith('held-joins'): rep = rep and all(len(rows_of(nt, c, name)) == 1 for c in ('BE', 'CH', 'PT'))
        check(f'review/{name}: BE CH PT rows are this run\'s (replaced, not duplicated)', rep)
    hj = json.loads(aft['data/world-key/review/held-joins.json'])
    check('held-joins.json count = its rows; no park listed twice', hj['count'] == len(hj['parks']) == len({r['park'] for r in hj['parks']}))
    idx, oidx = json.loads(aft['data/world-key/index.json']), json.loads(before['data/world-key/index.json'])
    check('index.json: the rows of the countries not in the run are untouched; previous_build is the old build',
          all(idx['countries'][c] == oidx['countries'][c] for c in ALL + ['AU'] if c not in ('BE', 'CH', 'PT')) and idx.get('previous_build') == 'W-1')

# 2) a country rebuilt to the SAME bytes keeps its rows (the join check did not read it)
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo_jc(t, ALL); before = snapshot(t)
    p = mkpart(t, 0, ['FR', 'NL'])
    (p / 'world-key/FR.json').write_bytes(before['data/world-key/FR.json'])   # FR rebuilt, identical
    (t / 'rc0').write_text('0\n'); (t / 'short0').write_text('')
    with contextlib.redirect_stdout(io.StringIO()): J.main_verdict(['verdict', '--part', str(p), '--countries', 'FR NL', '--rc-file', str(t / 'rc0'), '--short-file', str(t / 'short0')])
    rc, wiped = join_and_check(t, [p], json.dumps([{'i': 0, 'countries': 'FR NL', 'cmin': ''}]))
    aft = snapshot(t)
    check('a country rebuilt to the same bytes (FR) keeps its rows in all five files', all(rows_of(before[f'data/world-key/review/{n}'].decode(), 'FR', n) == rows_of(aft[f'data/world-key/review/{n}'].decode(), 'FR', n) for n in AJ.REVIEW_FILES))

# 3) US states= run and a Canada run: the same per state / province
for kind, key, codes, prefix in (('us', 'data/us-key', ['US-AL', 'US-TN', 'US-GA'], 'US'), ('ca', 'data/ca-key', ['CA-ON', 'CA-QC', 'CA-BC'], 'CA')):
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td); k = t / key; (k / 'review').mkdir(parents=True)
        for i, a in enumerate(codes):
            (k / f'{a}.json').write_text(json.dumps({'parks': {f'{prefix}-{i}001': {'n': 'far', 'g': 'official', 'm': [[1, 'x', 5, 'name']], 'c': [], 'bk': [1, 30.0]}}}))
        with contextlib.redirect_stdout(io.StringIO()): JC.run({'KEY': kind, 'ALL': '1', 'ANSWER_SHEET': str(t / 'none')}, root=str(t), plain=True)
        subprocess.run(['git', 'init', '-q'], cwd=t); subprocess.run(['git', 'add', '-A'], cwd=t); subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'm'], cwd=t)
        before = {n: (k / 'review' / n).read_bytes().decode() for n in AJ.REVIEW_FILES}
        a1 = codes[1]
        (k / f'{a1}.json').write_text(json.dumps({'parks': {f'{prefix}-1001': {'n': 'far', 'g': 'official', 'm': [[2, 'y', 5, 'name']], 'c': [], 'bk': [2, 40.0]}}}))
        with contextlib.redirect_stdout(io.StringIO()):
            JC.run({'KEY': kind, 'ANSWER_SHEET': str(t / 'none')}, root=str(t), plain=True)
            wiped = {n: (k / 'review' / n).read_bytes().decode() for n in AJ.REVIEW_FILES}
            AJ.main(['keep-rows', '--unchanged', '--key-dir', str(k), '--review', str(k / 'review')])
        after = {n: (k / 'review' / n).read_bytes().decode() for n in AJ.REVIEW_FILES}
        check(f'{kind}: (the join check alone kept only {a1}\'s rows)', codes[0] not in wiped['held-joins.csv'])
        keep_ok = all(rows_of(before[n], a, n) == rows_of(after[n], a, n) and rows_of(before[n], a, n) for n in ('held-joins.json', 'held-joins.csv', 'held-joins-ledger.csv', 'join-check.csv') for a in (codes[0], codes[2]))
        check(f'{kind}: a run of {a1} only leaves {codes[0]} and {codes[2]} rows byte-identical in the held / ledger / join-check files', keep_ok)
        check(f'{kind}: {a1}\'s rows are this run\'s, once', all(rows_of(after[n], a1, n) == rows_of(wiped[n], a1, n) and len(rows_of(after[n], a1, n)) == 1 for n in ('held-joins.json', 'held-joins.csv', 'held-joins-ledger.csv')))

# 4) the workflows call the merge on every built run
W = yaml.safe_load((ROOT / '.github/workflows/kpc-world-key.yml').read_text(encoding='utf-8'))
kr = next(s for s in W['jobs']['join']['steps'] if s.get('id') == 'keep_rows')
check('world: keep_rows merges EVERY unchanged country (not only the expected holds) on every built run',
      'kpc_area_join.py keep-rows --unchanged --areas "$EXPECTED" --key-dir data/world-key' in kr['run'] and '[ -z "$EXPECTED" ] ||' not in kr['run'])
for wf, job, key in (('kpc-us-key.yml', 'join', 'data/us-key'), ('kpc-ca-key.yml', 'run', 'data/ca-key')):
    st = yaml.safe_load((ROOT / '.github/workflows' / wf).read_text(encoding='utf-8'))['jobs'][job]['steps']
    jc = next(i for i, s in enumerate(st) if s.get('name', '').startswith('Join check'))
    rv = next(i for i, s in enumerate(st) if f'keep-rows --unchanged --key-dir {key}' in str(s.get('run', '')))
    stp = next(i for i, s in enumerate(st) if 'kpc_key_freeze.py stamp' in str(s.get('run', '')))
    check(f'{wf}: the per-area merge runs after the join check and before the stamp / Save', jc < rv < stp)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
