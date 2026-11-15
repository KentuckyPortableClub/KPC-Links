#!/usr/bin/env python3
"""Nov 14 (KPC owner, 2026-11-14): the join check writes every held park to review/held-parks-todo.csv, the keeper's to-do.
Offline, temp folders only. Checks: the columns, one row per held park (exempt joins not listed), run id + date + kind, DRY=1 writes
nothing, the five older review files are byte-identical to the join check without the to-do (git HEAD~ copy when there is one),
and kpc_area_join keep-rows merges the to-do per area like the other review files."""
import contextlib, csv, datetime, importlib.util, io, json, pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_join_check as JC
import kpc_area_join as AJ
import kpc_key_freeze as KZ
ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)
OLD = ['held-joins.json', 'held-joins.csv', 'held-joins-ledger.csv', 'join-check.json', 'join-check.csv']
COLS = ['ref', 'name', 'kind', 'area', 'reason', 'pin_km', 'outline_ids', 'todo_kind', 'source', 'run_id', 'date', 'rules_version']

def fixture(t, key='data/us-key', area='US-AA', pre='US'):
    k = t / key; k.mkdir(parents=True)
    parks = {f'{pre}-0001': {'n': 'Far', 'g': 'official', 'm': [[1, 'X', 100, 'name'], [2, 'Y', 5, 'name']], 'c': [], 'bk': [1, 22.0], 'ac': 100},
             f'{pre}-0002': {'n': 'Near', 'g': 'official', 'm': [[3, 'Z', 100, 'name']], 'c': [], 'bk': [3, 0.0]},
             f'{pre}-0004': {'n': 'Far but approved', 'g': 'official', 'm': [[44, 'Kept', 10, 'name']], 'c': [], 'bk': [44, 30.0]}}
    (k / f'{area}.json').write_text(json.dumps({'parks': parks}))
    (k / 'overrides.json').write_text(json.dumps({'parks': {f'{pre}-0004': {'join': ['44'], 'why': 'person'}}}))
    return k

def quiet(f, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()): return f(*a, **kw)

check('the join check and kpc_area_join are not rules files (no rules hash moves)',
      {'kpc_join_check.py', 'kpc_area_join.py'} <= KZ.NOT_RULES and not any(f.endswith(('kpc_join_check.py', 'kpc_area_join.py')) for v in KZ.RULE_FILES.values() for f in v))
check('to-do columns', JC.TODO_FIELDS == COLS)
check('the to-do is one of the per-area review files', 'held-parks-todo.csv' in AJ.REVIEW_FILES)

with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); k = fixture(t); before = (k / 'US-AA.json').read_bytes()
    rep = quiet(JC.run, {'KEY': 'us', 'ALL': '1', 'DRY': '1', 'ANSWER_SHEET': str(t / 'none'), 'GITHUB_RUN_ID': '77'}, root=str(t), plain=True)
    check('DRY=1: the hold is counted, nothing written (no review folder, key file unchanged)', rep['held'] == 1 and not (k / 'review').exists() and (k / 'US-AA.json').read_bytes() == before)
    quiet(JC.run, {'KEY': 'us', 'ALL': '1', 'ANSWER_SHEET': str(t / 'none'), 'GITHUB_RUN_ID': '77'}, root=str(t), plain=True)
    rd = list(csv.DictReader(open(k / 'review/held-parks-todo.csv', encoding='utf-8')))
    check('header line exactly the columns', open(k / 'review/held-parks-todo.csv', encoding='utf-8').readline().strip() == ','.join(COLS))
    check('one row: the held park only (the near one and the approved one are not listed)', [r['ref'] for r in rd] == ['US-0001'])
    r = rd[0]
    check('row fields', (r['name'], r['kind'], r['area'], r['pin_km'], r['outline_ids'], r['todo_kind'], r['source'], r['run_id'], r['rules_version'])
          == ('Far', 'us', 'US-AA', '22.0', '1;2', 'join_held', 'kpc_join_check', '77', ''))
    check("reason is the plain 'held: ...' reason of held-joins.csv", r['reason'] == 'held: ' + list(csv.DictReader(open(k / 'review/held-joins.csv')))[0]['reason'])
    check('date is today (UTC)', r['date'] == datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d'))

with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); k = fixture(t, 'data/world-key', 'FR', 'FR')
    quiet(JC.run, {'KEY': 'world', 'ALL': '1', 'ANSWER_SHEET': str(t / 'none')}, root=str(t), plain=True)
    rd = list(csv.DictReader(open(k / 'review/held-parks-todo.csv', encoding='utf-8')))
    check('world kind; no GITHUB_RUN_ID = blank run_id', [(x['ref'], x['kind'], x['area'], x['run_id']) for x in rd] == [('FR-0001', 'world', 'FR', '')])

check('two holds of one park in one area file are one row (reasons and ids joined)',
      [(x['ref'], x['outline_ids'], x['reason'].count('held: '), x['pin_km']) for x in JC.todo_rows(
          [{'park': 'CA-1', 'area': 'CA-ON', 'name': 'n', 'pin_km': None, 'held_ids': '5', 'reason': 'a'},
           {'park': 'CA-1', 'area': 'CA-ON', 'name': 'n', 'pin_km': 31.0, 'held_ids': '5 | 6', 'reason': 'b'},
           {'park': 'CA-1', 'area': 'CA-QC', 'name': 'n', 'pin_km': 2.0, 'held_ids': '7', 'reason': 'c'}], 'ca', {})]
      == [('CA-1', '5;6', 2, 31.0), ('CA-1', '7', 1, 2.0)])

# the five older review files: byte-identical to the join check before this change (the copy before the to-do came in, when git has it)
_add = subprocess.run(['git', 'log', '--format=%H', '-S', 'held-parks-todo', '--', '.github/scripts/kpc_join_check.py'], cwd=ROOT, capture_output=True, text=True).stdout.split()
_base = (_add[-1] + '~1') if _add else 'HEAD'   # the commit before the to-do came in (HEAD while it is not committed yet)
old_src = subprocess.run(['git', 'show', _base + ':.github/scripts/kpc_join_check.py'], cwd=ROOT, capture_output=True)
if old_src.returncode == 0 and b'held-parks-todo' not in old_src.stdout:
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td); (t / 'old.py').write_bytes(old_src.stdout)
        spec = importlib.util.spec_from_file_location('jc_old', t / 'old.py'); OJ = importlib.util.module_from_spec(spec); spec.loader.exec_module(OJ)
        a, b = t / 'a', t / 'b'; ka, kb = fixture(a), fixture(b)
        env = {'KEY': 'us', 'ALL': '1', 'ANSWER_SHEET': str(t / 'none'), 'GITHUB_RUN_ID': '9'}
        quiet(OJ.run, env, root=str(a), plain=True); quiet(JC.run, env, root=str(b), plain=True)
        same = all((ka / 'review' / n).read_bytes() == (kb / 'review' / n).read_bytes() for n in OLD) and (ka / 'US-AA.json').read_bytes() == (kb / 'US-AA.json').read_bytes()
        check('held-joins.json/.csv, the ledger, join-check.* and the key file: byte-identical to the join check without the to-do', same)
        check('only the to-do file is new', sorted(p.name for p in (kb / 'review').iterdir()) == sorted(OLD + ['held-parks-todo.csv']) and not (ka / 'review/held-parks-todo.csv').exists())
else:
    print('INFO the parent commit has no older join check: the byte check is skipped')

# keep-rows: a run of one area keeps the other areas' to-do rows from main, byte for byte
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); k = t / 'data/us-key'; (k / 'review').mkdir(parents=True)
    for i, a in enumerate(['US-AL', 'US-TN', 'US-GA']):
        (k / f'{a}.json').write_text(json.dumps({'parks': {f'US-{i}001': {'n': 'far', 'g': 'official', 'm': [[1, 'x', 5, 'name']], 'c': [], 'bk': [1, 30.0]}}}))
    quiet(JC.run, {'KEY': 'us', 'ALL': '1', 'ANSWER_SHEET': str(t / 'none'), 'GITHUB_RUN_ID': '1'}, root=str(t), plain=True)
    g = lambda *a: subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', *a], cwd=t, capture_output=True)
    g('init', '-q'); g('add', '-A'); g('commit', '-qm', 'm')
    main = (k / 'review/held-parks-todo.csv').read_text()
    (k / 'US-TN.json').write_text(json.dumps({'parks': {'US-1001': {'n': 'far', 'g': 'official', 'm': [[2, 'y', 5, 'name']], 'c': [], 'bk': [2, 40.0]}}}))
    quiet(JC.run, {'KEY': 'us', 'ANSWER_SHEET': str(t / 'none'), 'GITHUB_RUN_ID': '2'}, root=str(t), plain=True)
    wiped = (k / 'review/held-parks-todo.csv').read_text()
    quiet(AJ.main, ['keep-rows', '--unchanged', '--key-dir', str(k), '--review', str(k / 'review')])
    after = (k / 'review/held-parks-todo.csv').read_text()
    rows = lambda s: {r['area']: (r['run_id'], r['outline_ids']) for r in csv.DictReader(io.StringIO(s))}
    check('(the join check alone wrote only US-TN)', set(rows(wiped)) == {'US-TN'})
    ml = main.splitlines()
    check('keep-rows: US-AL and US-GA rows back from main byte for byte, US-TN from this run', rows(after) == {'US-AL': ('1', '1'), 'US-GA': ('1', '1'), 'US-TN': ('2', '2')}
          and all(ln in after.splitlines() for ln in ml if ',US-AL,' in ln or ',US-GA,' in ln))

print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
