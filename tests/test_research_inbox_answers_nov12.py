#!/usr/bin/env python3
"""Offline test, KPC owner 2026-11-12 (handoff items 9 and 10), research inbox.
Item 9: a batch-shaped file under data/research-inbox/answers/ is read like a top-level batch; every other file there is listed as
"not a batch: <reason>" (never skipped in silence); a second run adds nothing; WDPA rows are still skipped; no key, pin or override is written.
Item 10: the owner short list names a brandon_flip park that has no `row` (park list, then ledger, then earlier results), and prints
"(name not found)" when no source has it. No network (every connect is refused; the reader is offline). Run: python3 -B tests/test_research_inbox_answers_nov12.py"""
import contextlib, csv, io, json, pathlib, re, socket, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / '.github/scripts'))
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(OSError('no network in this test'))
import kpc_research_inbox as RI  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402
ok = True
def check(c, m):
    global ok; print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)

def put(base, rel, text):
    p = base / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding='utf-8'); return p
def batch_csv(rows):
    s = io.StringIO(); w = csv.DictWriter(s, fieldnames=RI.COLS, lineterminator='\n'); w.writeheader(); w.writerows([{k: r.get(k, '') for k in RI.COLS} for r in rows]); return s.getvalue()

# ---- 1. the rule: what is a batch under answers/
T = pathlib.Path(tempfile.mkdtemp())
cases = {
    'a.csv': (batch_csv([{'pota_ref': 'US-1', 'park_name': 'A'}]), True),
    'b.json': (json.dumps({'rows': [{'pota_ref': 'US-1', 'park_name': 'A'}]}), True),
    'c.json': (json.dumps([{'pota_ref': 'US-1'}]), True),
    'ref.csv': ('ref,name,country\nUS-1,A,US\n', False),
    'ans.csv': ('ref,name,answer,official_source_url\nUS-1,A,match,http://x\n', False),
    'xwalk.csv': ('ref,pota_name,a10_005_join_key_or_official_ja_name\nJP-1,A,b\n', False),
    'src.csv': ('country,layer_name,url\nJP,x,http://x\n', False),
    'ledger.csv': ('ref,name,solved\nUS-1,A,yes\n', False),
    'neg.json': (json.dumps({'about': 'x', 'negatives': []}), False),
    'rows-no-ref.json': (json.dumps({'rows': [{'ref': 'US-1'}]}), False),
    'empty.csv': ('', False), 'bad.json': ('{not json', False), 'note.md': ('# notes', False),
}
for n, (txt, want) in cases.items(): put(T, n, txt)
for n, (txt, want) in cases.items():
    got, why = RI.batch_shape(T / n)
    check(got is want and bool(why), f'batch_shape({n}) = {want}: {why[:90]}')
check('crosswalk' in RI.batch_shape(T / 'xwalk.csv')[1] and 'ledger' in RI.batch_shape(T / 'ledger.csv')[1] and 'answers file' in RI.batch_shape(T / 'ans.csv')[1],
      'the reasons name the kind of file (crosswalk, ledger, answers file)')

# ---- 2. classify / inbox_files on a fixture root
root = pathlib.Path(tempfile.mkdtemp()); ib = root / 'data/research-inbox'
put(ib, 'top.csv', batch_csv([])); put(ib, 'top2.json', '{"rows": []}'); put(ib, 'needs-another-look.json', '{}'); put(ib, 'brandon-list.md', 'x'); put(ib, 'results/old.json', '{}')
put(ib, 'answers/nov12/new-batch.csv', batch_csv([{'pota_ref': 'US-100', 'park_name': 'Fed Twice Park'}, {'pota_ref': 'US-200', 'park_name': 'Solved Park'},
                                                  {'pota_ref': 'US-300', 'park_name': 'Wdpa Park', 'notes': 'from WDPA record 12345'}]))
put(ib, 'answers/nov12/answers-x.csv', 'ref,name,answer\nUS-100,Fed Twice Park,match\n'); put(ib, 'answers/nov12/crosswalk.csv', 'ref,pota_name,a10_join_key\nJP-1,A,b\n')
put(ib, 'answers/NOTES.md', 'notes'); put(ib, 'answers/lists/x.json', json.dumps({'rows': [{'ref': 'US-1'}]}))
batches, notb = RI.classify_inbox(root)
names = [str(pathlib.Path(b).relative_to(ib)) for b in batches]
check(names == ['top.csv', 'top2.json', 'answers/nov12/new-batch.csv'], f'top-level batches unchanged (a plain file stays a batch), then the batch under answers/: {names}')
check(sorted(f for f, _ in notb) == ['answers/NOTES.md', 'answers/lists/x.json', 'answers/nov12/answers-x.csv', 'answers/nov12/crosswalk.csv'], 'every other file under answers/ is in the not-a-batch list')
check(RI.inbox_files(root) == batches and RI.batch_stem(batches[2], root) == 'answers-nov12-new-batch' and RI.batch_stem(batches[0], root) == 'top',
      'inbox_files = the batches; results stem is answers-<folders>-<name> (a top-level file keeps its stem)')
check(not any('results' in n or 'needs-another-look' in n or 'brandon-list' in n for n in names), 'results/, the retry list and the owner list are never batches')

# ---- 3. the real repo: nothing silently skipped, nothing force-fed
real_b, real_n = RI.classify_inbox(HERE)
real_all = sorted(str(f.relative_to(HERE / 'data/research-inbox')) for f in (HERE / 'data/research-inbox/answers').rglob('*') if f.is_file())
seen_all = sorted([str(pathlib.Path(b).relative_to(HERE / 'data/research-inbox')) for b in real_b if '/answers/' in b] + [f for f, _ in real_n])
check(real_all and seen_all == real_all, f'every file under answers/ ({len(real_all)}) is either read as a batch or listed as not a batch')
check([pathlib.Path(b).name for b in real_b if '/answers/' not in b] and all(pathlib.Path(b).name.startswith('nov9-') for b in real_b), f'the real inbox still reads only the two Nov 9 batches: {[pathlib.Path(b).name for b in real_b]}')
jp = [w for f, w in real_n if f.endswith('JP_A10_crosswalk.csv')]
check(jp and 'crosswalk' in jp[0], f'the Japan crosswalk is listed as not a batch, not fed to the checker: {jp[0][:80] if jp else None}')
check(any(f.endswith('MYSTERY_PARKS_NOV11_NOTES.md') for f, _ in real_n) and any(f.endswith('answers-nov11.csv') for f, _ in real_n), 'the Nov 11 notes and answers file are listed too')

# ---- 4. run(): batch under answers/ is checked; not-a-batch lines are printed and written; a second run adds nothing; WDPA skipped; no key/pin write
nal0 = {'about': 'x', 'parks': {'US-100': {'status': 'needs another look', 'reason': 'fed by 159', 'row': {'pota_ref': 'US-100', 'park_name': 'Fed Twice Park'}, 'wait_on': 'person', 'since': '2026-11-10 10:00', 'last': '2026-11-10 10:00'}}}
put(ib, 'needs-another-look.json', json.dumps(nal0))
(root / 'kd').mkdir(); put(root, 'data/us-key/overrides.json', '{"parks": {}}'); put(root, 'data/parkinfo-sentinel.json', '{}')
ledger = {'US-200': {'name': 'Solved Park', 'solved': 'yes', 'solved_basis': 'padus', 'official_id': 'P1'}}
def snap_keys(): return {str(f.relative_to(root)): f.read_bytes() for f in root.rglob('*') if f.is_file() and ('-key/' in str(f) or 'parkinfo' in str(f) or 'pins' in f.name.lower())}
keys0 = snap_keys()
def go():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): res = RI.run(RI.inbox_files(root), root=root, kpcdata=root / 'kd', cache=root / 'cache', offline=True, retry=True, ledger=ledger)
    return res, buf.getvalue()
def norm(o):
    return json.loads(re.sub(r'"(checked|last)": "[^"]*"', r'"\1": "T"', json.dumps(o, sort_keys=True)))
res1, out1 = go()
b = {r['pota_ref']: r for r in res1.get('answers-nov12-new-batch', [])}
check(set(b) == {'US-100', 'US-200'} and b['US-200']['status'] == 'SOLVED' and b['US-100']['status'] == 'NEEDS PERSON', f'the answers/ batch was checked like a top-level one: {({k: v["status"] for k, v in b.items()})}')
lines = [l for l in out1.splitlines() if 'not a batch:' in l]
check(len(lines) == 4 and any('crosswalk.csv' in l and 'crosswalk' in l for l in lines) and any('NOTES.md' in l for l in lines), f'the run prints one "not a batch: <file>: <reason>" line per unread file under answers/ ({len(lines)})')
nb = (ib / 'results/not-batches.md').read_text(encoding='utf-8')
check(nb.count('- not a batch:') == 4 and '- batch: answers/nov12/new-batch.csv' in nb, 'results/not-batches.md carries the same list')
allout = out1 + ''.join(f.read_text(encoding='utf-8') for f in (ib / 'results').glob('*')) + (ib / 'needs-another-look.json').read_text(encoding='utf-8') + (ib / 'brandon-list.md').read_text(encoding='utf-8')
check('US-300' not in allout.replace('WDPA / Protected Planet row(s) skipped', '') and 'Wdpa Park' not in allout and '12345' not in allout, 'the WDPA row is skipped: its ref, name and id appear nowhere in the output files')
check('WDPA / Protected Planet row(s) skipped' in out1, 'the WDPA skip line is printed')
nal1 = json.load(open(ib / 'needs-another-look.json'))
check(set(nal1['parks']) == {'US-100'} and nal1['parks']['US-100']['since'] == '2026-11-10 10:00', 'the park already on the retry list stays ONE entry and keeps its since date')
snap1 = {str(f.relative_to(ib)): norm(json.loads(f.read_text())) if f.suffix == '.json' else re.sub(r'\d{4}-\d\d-\d\d \d\d:\d\d', 'T', f.read_text()) for f in sorted(ib.rglob('*')) if f.is_file()}
res2, out2 = go()
snap2 = {str(f.relative_to(ib)): norm(json.loads(f.read_text())) if f.suffix == '.json' else re.sub(r'\d{4}-\d\d-\d\d \d\d:\d\d', 'T', f.read_text()) for f in sorted(ib.rglob('*')) if f.is_file()}
check(snap1 == snap2, 'SECOND RUN adds nothing: every inbox file is the same apart from time stamps')
check(sorted(json.load(open(ib / 'needs-another-look.json'))['parks']) == ['US-100'], 'second run: the retry list is still the one park')
check(snap_keys() == keys0 and not (root / 'data/us-key/overrides.json').read_text() != '{"parks": {}}', 'no key, override or parkinfo file was written')
check(not (ib / 'answers/nov12/new-batch.csv').read_text(encoding='utf-8').startswith('X') and (ib / 'answers/nov12/answers-x.csv').read_text() == 'ref,name,answer\nUS-100,Fed Twice Park,match\n', 'the answers/ files themselves are not changed by a run')

# ---- 5. no answers/ folder: no report, no new file (older checkouts keep working)
r2 = pathlib.Path(tempfile.mkdtemp()); put(r2, 'data/research-inbox/needs-another-look.json', json.dumps({'about': 'x', 'parks': {}}))
with contextlib.redirect_stdout(io.StringIO()) as o: RI.run([], root=r2, kpcdata=r2 / 'kd', cache=r2 / 'c', offline=True, retry=True, ledger={})
check(not (r2 / 'data/research-inbox/results/not-batches.md').exists() and 'not a batch' not in o.getvalue(), 'no answers/ folder = no report file')

# ---- 6. item 10: the owner short list never prints a blank park name
SIX = ['US-10823', 'US-12978', 'US-12981', 'CA-4773', 'CA-4779', 'CA-4780']
r3 = pathlib.Path(tempfile.mkdtemp()); i3 = r3 / 'data/research-inbox'
flip = {r: {'status': RI.SFN, 'reason': 'r', 'earlier_no': {'date': '2026-10-22', 'decision': 'no outline'}, 'record_id': str(i), 'record_name': f'Rec {i}', 'layer_url': 'https://x.gov/MapServer/0', 'last': 'l'} for i, r in enumerate(SIX)}
flip['US-11820'] = {'status': RI.SFN, 'reason': 'r', 'earlier_no': {}, 'record_id': '1', 'record_name': 'n', 'row': {'pota_ref': 'US-11820', 'park_name': 'Miller Own Row'}}
put(i3, 'needs-another-look.json', json.dumps({'about': 'x', 'parks': {}, 'brandon_flip': flip}))
put(r3, 'kd/data/parkinfo/US-OR.json', json.dumps({'parks': {'US-12978': ['Willamette State Fish Hatchery', 'http://x', 'Hatchery', '', '', 44.1, -122.1], 'US-12981': ['Oak Springs State Fish Hatchery', '', '', '', '', 45.1, -121.1]}}))
put(r3, 'kd/data/parkinfo/CA.json', json.dumps({'parks': {'CA-4773': ['Banff Park Museum National Historic Site', '', '', '', '', 51.1, -115.5, 0, 0, 0, 'AB']}}))
put(i3, 'results/earlier.json', json.dumps({'counts': {}, 'rows': [{'pota_ref': 'CA-4779', 'park_name': 'Jasper House National Historic Site', 'status': 'NEEDS PERSON'}]}))
led3 = {'US-10823': {'name': 'Dubois State Fish Hatchery', 'solved': 'no'}}
with contextlib.redirect_stdout(io.StringIO()): RI.run([], root=r3, kpcdata=r3 / 'kd', cache=r3 / 'c', offline=True, retry=True, ledger=led3)
bl = (i3 / 'brandon-list.md').read_text(encoding='utf-8'); L = {re.match(r'- \*\*(\S+)\*\*', l).group(1): l for l in bl.splitlines() if l.startswith('- **')}
check(set(L) == set(SIX) | {'US-11820'}, 'all seven short-list entries are printed')
check(not [l for l in L.values() if re.match(r'- \*\*\S+\*\* ?:', l)], 'no line has a blank park name')
check('Willamette State Fish Hatchery' in L['US-12978'] and 'Oak Springs State Fish Hatchery' in L['US-12981'] and 'Banff Park Museum' in L['CA-4773'], 'name from the park list (KPC-Data parkinfo, first field)')
check('Dubois State Fish Hatchery' in L['US-10823'], 'name from the answers ledger when the park list has none')
check('Jasper House National Historic Site' in L['CA-4779'], 'name from an earlier results file when the park list and ledger have none')
check(L['CA-4780'].startswith('- **CA-4780** (name not found):'), f'no name anywhere: the reference with "(name not found)": {L["CA-4780"][:60]}')
check(L['US-11820'].startswith('- **US-11820** Miller Own Row:'), 'an entry that has its own row keeps the row name')
rn = RI.park_names(SIX, HERE, HERE / 'nokpcdata', {})
check(set(rn) == set(SIX), f'on the real needs-another-look entries the six refs are all found from the repo\'s own results files: {len(rn)} of 6')

# ---- 7. hard limits: not a rule file; four hashes unchanged; no WDPA data in tracked files; problem solver wiring unchanged
nr = {f for fs in KF.RULE_FILES.values() for f in fs}
check('kpc_research_inbox.py' in KF.NOT_RULES and not any(f.endswith('kpc_research_inbox.py') for f in nr), 'kpc_research_inbox.py is on the NOT_RULES list and in no RULE_FILES')
h = {k: KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key', 'fers')}
check(h == {'us-key': '46ef34a04ab0', 'ca-key': '4b4176190334', 'world-key': '889d37136cf8', 'fers': 'cef323de4c9a'}, f'rules hashes unchanged: {h}')
ps = (HERE / '.github/scripts/kpc_problem_solver.py').read_text(encoding='utf-8')
check('RI.inbox_files(ROOT)' in ps, 'the problem solver --inbox still uses inbox_files')
src = (HERE / '.github/scripts/kpc_research_inbox.py').read_text(encoding='utf-8')
check(not re.search(r"open\([^)]*(overrides|parkinfo|layers\.json)[^)]*'w'", src), 'the inbox script opens no override, parkinfo or layer file for writing')

print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
