#!/usr/bin/env python3
"""Problem solver, Nov 14 2026 (Job 2, item 4a): who / when / run id on every written record; the name test on every proposed
candidate; a person's NO in the overrides always wins. Synthetic rows, temp folders, offline; nothing is written to the repo."""
import gzip, json, os, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_problem_solver as S

ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)

def sq(lo, la, d=0.01): return [[[lo - d, la - d], [lo + d, la - d], [lo + d, la + d], [lo - d, la + d], [lo - d, la - d]]]
PIN = (38.0, -86.0)

# ---------------------------------------------------------------- 2. the name test on solve()'s candidates
def land_wrong_case(other='Pine Creek Wildlife Refuge'):
    p = {'n': 'Pine Creek State Forest', 't': 'State Forest', 'm': [], 'g': 'pin', 'held': {'ids': ['h1'], 'why': 'far'}, 'bk': ['h1', 22.0],
         'c': [['h1', 'Pine Creek State Forest', 500, 'held'], ['o1', other, 400, 'at the pin']]}
    recs = {'h1': {'Unit_Nm': 'Pine Creek State Forest', '_r': sq(-86.0, 38.2)}, 'o1': {'Unit_Nm': other, '_r': sq(-86.0, 38.0)}}
    return p, recs

def no_gate(fn):   # the solver as it was before Nov 14: no name test, no person's-no gate of its own on these candidates
    a, b = S.candidate_name_fits, S.person_no
    S.candidate_name_fits = lambda *x: ''; S.person_no = lambda *x: ''
    try: return fn()
    finally: S.candidate_name_fits, S.person_no = a, b

p, recs = land_wrong_case()
before = no_gate(lambda: S.solve('US-1', p, PIN, recs, None, 'US-KY'))
now = S.solve('US-1', p, PIN, recs, None, 'US-KY')
check(before['verdict'] == 'land wrong' and 'o1' in before['recommend'], f"before: the same-core-name record at the pin was proposed ({before['verdict']}: {before['recommend']})")
check(now['verdict'] == 'needs a person' and now['not_proposed'][0]['id'] == 'o1' and now['not_proposed'][0]['why'].startswith('name does not fit'),
      f"now: a forest park is not re-pointed to a refuge: {now['not_proposed'][0]['why']}")
p2, recs2 = land_wrong_case('Pine Creek State Forest')   # a record that does fit
r2 = S.solve('US-1', p2, PIN, recs2, None, 'US-KY')
check(r2['verdict'] == 'land wrong' and 'not_proposed' not in r2, 'a candidate whose name fits is still proposed (land wrong)')

def new_id_case(cand='Pine Creek Wildlife Refuge'):
    p = {'n': 'Pine Creek State Forest', 't': 'State Forest', 'm': [], 'g': 'pin', 'bk': ['n1', 0.1], 'c': [['n1', cand, 100, 'at the pin']]}
    return p, {'n1': {'Unit_Nm': cand, '_r': sq(-86.0, 38.0)}}, {'join': ['old9']}
p, recs, ov = new_id_case()
before = no_gate(lambda: S.solve('US-1', p, PIN, recs, ov, 'US-KY'))
now = S.solve('US-1', p, PIN, recs, ov, 'US-KY')
check(before['verdict'] == 'same land new ID', f"before: the re-point candidate (picked by the key's best id) was proposed: {before['recommend']}")
check(now['verdict'] == 'needs a person' and 'name does not fit' in '; '.join(now['reasons']), 'now: same land new ID is not proposed when the kinds clash')
p, recs, ov = new_id_case('Pine Creek State Forest')
check(S.solve('US-1', p, PIN, recs, ov, 'US-KY')['verdict'] == 'same land new ID', 'a fitting re-point candidate is still proposed')

# ---------------------------------------------------------------- 2. the name test in check_candidate (the sure rule)
r = {'id': '9', 'name': 'Oak Hollow Preserve', 'rings': sq(-86, 38), 'acres': 100}
park = {'ref': 'US-1', 'name': 'Blue Lake Wildlife Management Area', 'pin': PIN, 'official_acres': 100}
a, S.sure_name_fits = S.sure_name_fits, lambda *x: ''
before = S.check_candidate(park, [r], official_acres=100); S.sure_name_fits = a
now = S.check_candidate(park, [r], official_acres=100)
check(before['verdict'] == 'YES', 'before: a record picked by position (pin inside, acres agree) was a YES whatever its name')
check(now['verdict'] == 'ONLY-PERSON' and now['signed_by'] is None and 'name does not fit' in now['why'] and now['not_proposed'][0]['id'] == '9',
      f"now: name does not fit, not proposed: {now['why'][-90:]}")
fit = S.check_candidate(park, [dict(r, name='Blue Lake WMA')], official_acres=100)
check(fit['verdict'] == 'YES' and 'not_proposed' not in fit, 'the same record with the park\'s name is still a YES')
check(S.check_candidate(park, [dict(r, name='')], official_acres=100)['verdict'] == 'ONLY-PERSON', 'a record with no name is not proposed')

# ---------------------------------------------------------------- 3. a person's NO always wins
p, recs = land_wrong_case('Pine Creek State Forest')
for ov, bl, label in [({'no': ['o1']}, (), "overrides 'no' (id)"), ({'no': ['pine creek state forest ']}, (), "overrides 'no' (name)"),
                      ({'none': True}, (), 'overrides none: true'), ({}, {'o1'}, 'blocked_ids')]:
    x = S.solve('US-1', p, PIN, recs, ov, 'US-KY', ctx={'blocked_ids': bl})
    check(x['verdict'] == 'needs a person' and "blocked by a person's no" in '; '.join(x['reasons']), f'land wrong: {label} blocks the candidate')
x = S.solve('US-1', p, PIN, recs, {'no': ['zz9']}, 'US-KY')
check(x['verdict'] == 'land wrong', "a 'no' for another record does not block this one")
p, recs, ov = new_id_case('Pine Creek State Forest')
x = S.solve('US-1', p, PIN, recs, dict(ov, no=['n1']), 'US-KY')
check(x['verdict'] == 'needs a person' and "blocked by a person's no" in '; '.join(x['reasons']), 'same land new ID: a NO on the new id blocks the re-point')
fx = json.load(open(ROOT / 'tests/fixtures/problem-solver-17.json', encoding='utf-8'))['parks']
c = fx['US-4894']
x = S.solve('US-4894', c['row'], c['pin'], c['recs'], dict(c['override'], no=c['override']['no'] + ['sgnhc644']), c['state'])
y = S.solve('US-4894', c['row'], c['pin'], c['recs'], c['override'], c['state'])
check(y['verdict'] == 'pin wrong' and x['verdict'] == 'needs a person' and "blocked by a person's no" in x['reasons'][-1], 'pin wrong: a NO on the held record means it is never proposed to keep')
x = S.solve('US-4894', c['row'], c['pin'], c['recs'], c['override'], c['state'], ctx={'blocked_ids': {'sgnha990'}})
check(x['verdict'] == 'needs a person', 'pin wrong: a blocked_ids entry on any held record blocks the keep')

good = {'id': '7', 'name': 'Blue Lake Wildlife Management Area', 'rings': sq(-86, 38), 'acres': 100}
bad = dict(good, id='6')
v = S.check_candidate(park, [bad, good], official_acres=100, override={'no': ['6']})
check(v['verdict'] == 'YES' and v['record_id'] == '7' and v['not_proposed'][0]['id'] == '6' and "blocked by a person's no" in v['why'],
      'check_candidate: the blocked record is dropped, the unblocked one is still proposed')
v = S.check_candidate(park, [bad], official_acres=100, blocked={'6'})
check(v['verdict'] == 'NO' and "blocked by a person's no" in v['why'], 'check_candidate: only a blocked record left = NO, blocked by a person\'s no')
v = S.check_candidate(park, [bad], official_acres=100, earlier_no=None, page_html='<h1>Blue Lake Wildlife Management Area</h1><p>100 acres</p>', override={'none': True})
check(v['verdict'] == 'NO', 'check_candidate: new evidence never lifts a person\'s NO (none: true)')

# run_check: the overrides are read with kpc_overrides' own reader; missing / empty files change nothing
def run_check_in(tree_files):
    t = pathlib.Path(tempfile.mkdtemp(prefix='kpc-pn-')); (t / 'data/us-key').mkdir(parents=True)
    for rel, d in tree_files.items(): json.dump(d, open(t / rel, 'w'))
    json.dump({'rows': [{'ref': 'US-1', 'name': park['name'], 'pin': list(PIN), 'official_acres': 100, 'records': [bad, good]},
                        {'ref': 'US-2', 'name': park['name'], 'pin': list(PIN), 'official_acres': 100, 'records': [bad]}]}, open(t / 'c.json', 'w'))
    return S.run_check(t / 'c.json', out_dir=t / 'o', root=t, env={'GITHUB_RUN_ID': '777'}), t
base, _ = run_check_in({})
strip = lambda rows: [{k: v for k, v in x.items() if k not in S.STAMP_KEYS} for x in rows]   # noqa: E731
check([x['verdict'] for x in base] == ['YES', 'YES'] and [x['record_id'] for x in base] == ['6', '6'], 'run_check, no overrides file: both rows YES on record 6')
empty, _ = run_check_in({'data/us-key/overrides.json': {'parks': {}, 'blocked_ids': []}})
check(strip(empty) == strip(base), 'run_check, an empty overrides file changes nothing')
blk, t = run_check_in({'data/us-key/overrides.json': {'parks': {'US-1': {'no': ['6']}}, 'blocked_ids': [{'ref': 'US-2', 'id': '6', 'decided_by': 'a person'}]}})
check(blk[0]['verdict'] == 'YES' and blk[0]['record_id'] == '7' and blk[1]['verdict'] == 'NO' and "blocked by a person's no" in blk[1]['why'],
      "run_check: 'no' row drops record 6 (record 7 still YES), blocked_ids makes US-2 NO")
und, _ = run_check_in({'data/us-key/overrides.json': {'parks': {}, 'blocked_ids': [{'ref': 'US-2', 'id': '6'}]}})
check(und[1]['verdict'] == 'YES', 'a blocked_ids entry without decided_by does not count (the file\'s own rule)')

# ---------------------------------------------------------------- 1. who / when / run id
d = json.load(open(str(t / 'o') + '.json'))
row = d['parks'][0]
check(list(row)[-3:] == ['by', 'when', 'run_id'] and row['by'] == 'kpc_problem_solver:check' and row['run_id'] == '777' and row['when'].endswith('Z'),
      f"run_check rows end with by / when / run_id ({row['by']}, {row['when']}, {row['run_id']})")
check('(by kpc_problem_solver:check, ' in (pathlib.Path(str(t / 'o') + '.md')).read_text(), 'the check report lines name who / when / run')
t = pathlib.Path(tempfile.mkdtemp(prefix='kpc-run-')); (t / 'data/us-key').mkdir(parents=True); (t / 'pi').mkdir(); (t / 'cache').mkdir()
p, recs = land_wrong_case('Pine Creek State Forest')
json.dump({'parks': {'US-1': p, 'US-2': {'n': 'Lone Park', 't': 'State Park', 'm': [], 'g': 'pin', 'c': []}}}, open(t / 'data/us-key/US-KY.json', 'w'))
json.dump({'parks': {'US-1': ['x', 0, 0, 0, 0, PIN[0], PIN[1]]}}, open(t / 'pi/US-KY.json', 'w'))
json.dump({'recs': [dict(v, OBJECTID=k) for k, v in recs.items()]}, gzip.open(t / 'cache/US-KY.json.gz', 'wt'))
for env, want_id in [({}, ''), ({'GITHUB_RUN_ID': '4242'}, '4242')]:
    S.run(dict(env, OUT=str(t / 'o'), DATA='/nonexistent', PARKINFO=str(t / 'pi'), GEO_CACHE=str(t / 'cache')), root=t)
    d = json.load(open(t / 'o.json'))
    recs_out = d['parks'] + d['why']
    check(d['parks'][0]['verdict'] == 'land wrong' and all(list(x)[-3:] == list(S.STAMP_KEYS) and x['by'] == 'kpc_problem_solver:key' and x['run_id'] == want_id for x in recs_out),
          f'run(): every verdict and why row ends with by / when / run_id (run id {want_id or "blank"})')
md = (t / 'o.md').read_text()
check('| By | When | Run ID |' in md and '| kpc_problem_solver:key | ' in md, 'run(): the report tables gain By / When / Run ID columns at the end')
json.dump({'parks': {'US-1': {'no': ['o1']}}}, open(t / 'data/us-key/overrides.json', 'w'))
S.run({'OUT': str(t / 'o'), 'DATA': '/nonexistent', 'PARKINFO': str(t / 'pi'), 'GEO_CACHE': str(t / 'cache')}, root=t)
check(json.load(open(t / 'o.json'))['parks'][0]['verdict'] == 'needs a person', "run(): an overrides 'no' row (read by kpc_overrides) blocks the candidate")
json.dump({'parks': {}, 'blocked_ids': [{'ref': 'US-1', 'id': 'o1', 'decided_by': 'a person'}]}, open(t / 'data/us-key/overrides.json', 'w'))
S.run({'OUT': str(t / 'o'), 'DATA': '/nonexistent', 'PARKINFO': str(t / 'pi'), 'GEO_CACHE': str(t / 'cache')}, root=t)
check(json.load(open(t / 'o.json'))['parks'][0]['verdict'] == 'needs a person', 'run(): a blocked_ids entry blocks the candidate')

# --inbox: the rows of the results files this run wrote get the three fields; other files are left alone
t = pathlib.Path(tempfile.mkdtemp(prefix='kpc-inb-')); rd = t / 'data/research-inbox/results'; rd.mkdir(parents=True)
json.dump({'counts': {'SURE': 1}, 'rows': [{'pota_ref': 'US-1', 'status': 'SURE', 'reason': 'é'}]}, open(rd / 'a.json', 'w'), indent=1, ensure_ascii=False)
json.dump({'counts': {}, 'rows': [{'pota_ref': 'US-2', 'status': 'SURE'}]}, open(rd / 'old.json', 'w'), indent=1)
old = (rd / 'old.json').read_bytes()
S.stamp_inbox({'a': [{'pota_ref': 'US-1'}], 'retry': []}, t, env={'GITHUB_RUN_ID': '55'})
a = json.load(open(rd / 'a.json', encoding='utf-8'))
check(list(a['rows'][0]) == ['pota_ref', 'status', 'reason', 'by', 'when', 'run_id'] and a['rows'][0]['by'] == 'kpc_problem_solver:inbox' and a['rows'][0]['run_id'] == '55'
      and (rd / 'old.json').read_bytes() == old and 'é' in (rd / 'a.json').read_text(encoding='utf-8'), 'inbox results rows stamped; a file this run did not write is untouched')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
