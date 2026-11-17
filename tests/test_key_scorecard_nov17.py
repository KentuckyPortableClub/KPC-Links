#!/usr/bin/env python3
"""The scorecard (KPC owner, 2026-11-17; matching plan section 4, handoff 8 part 1): .github/scripts/kpc_key_scorecard.py.
1. Its counting, on a made-up state (tests/fixtures/scorecard_nov17: 7 parks, known answers): FOUND / WRONG / EXTRA, the activation
   weights, a NO typed as a name, the bad-id block list (a block with no decided_by does not count), the wetland-district rule rows
   left out of the answer sheet, a person's none: true, and KPC_NO_BY_NAME (a renumbered record caught by its saved name + acres).
2. The whole run on a tiny made-up checkout whose key builder is a stand-in: the two scratch copies (the hidden one has an empty
   override set, no part files, no person row in its old key file), the fixed offline settings on both runs, a --set switch on both
   runs, a stray switch in the caller's shell NOT passed, nothing written in the checkout, the report outside data/, --out inside
   data/ refused, a state with no saved copy refused, a state the builder skips reported NOT GRADED (exit 1).
Run:  python3 tests/test_key_scorecard_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_scorecard as S  # noqa: E402
import kpc_overrides as KOVR  # noqa: E402
FX = ROOT / 'tests/fixtures/scorecard_nov17'
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)
J = lambda p: json.loads(pathlib.Path(p).read_text())

# ---------------------------------------------------------------- 1. the counting
today, hidden = J(FX / 'US-ZZ-today.json')['parks'], J(FX / 'US-ZZ-hidden.json')['parks']
ovr = S.overrides_with_blocks(J(FX / 'overrides.json'))
act = S.activations(J(FX / 'parkinfo-US-ZZ.json')['parks'])
check(act == {'US-9001': 100, 'US-9002': 50, 'US-9004': 30, 'US-9005': 10, 'US-9006': 5, 'US-9007': 7}, 'activations = parkinfo field 7; a park with none is left out (US-9003)')
check(ovr['US-9006']['no'] == ['602'] and ovr['US-9001']['no'] == ['199'], 'the block list counts as a NO only with decided_by (602 yes, 103 no)')
g = S.grade(today, hidden, ovr, act, {})
h, t = g['hidden'], g['today']
check((h['found'], h['yes'], h['found_pct'], h['found_w_pct']) == (2, 3, 66.7, 75.0),
      f"FOUND 2 of 3 person-YES = 66.7%, by activations 150/200 = 75.0% (got {h['found']}/{h['yes']} {h['found_pct']} {h['found_w_pct']})")
check((h['yes_parks'], h['found_parks'], h['found_parks_all'], h['found_parks_pct'], h['found_parks_w_pct']) == (2, 2, 1, 100.0, 100.0),
      'FOUND by park: both parks with a person-YES get at least one of their records, only Alpha gets all (Beta misses zzb202)')
check([x[:2] for x in h['lists']['missed']] == [['US-9002', 'zzb202']], 'the missed person-YES record is listed (Beta zzb202, a reviewed-approx row)')
check((h['wrong'], h['wrong_parks'], h['no_hit'], h['no'], h['wrong_pct'], h['wrong_w_pct']) == (4, 3, 3, 5, 60.0, 34.0),
      f"WRONG 4 records on 3 parks, 3 of 5 NO entries hit = 60.0%, by activations 55/162 = 34.0% (got {h['wrong']} {h['wrong_parks']} {h['no_hit']}/{h['no']} {h['wrong_pct']} {h['wrong_w_pct']})")
check(sorted((x[0], str(x[1])) for x in h['lists']['wrong']) == [('US-9002', '299'), ('US-9003', '301'), ('US-9003', '302'), ('US-9006', '602')],
      'WRONG rows: a NO by id (299), a NO typed as a name catches both records of that name (301, 302, any case), a blocked id (602)')
check((h['extra'], h['extra_parks'], h['joins_on_reviewed'], h['extra_pct'], h['extra_w_pct']) == (5, 3, 7, 71.4, 71.7),
      f"EXTRA 5 records on 3 reviewed parks of 7 joins there = 71.4%, by activations 380/530 = 71.7% (got {h['extra']} {h['extra_parks']} {h['joins_on_reviewed']} {h['extra_pct']} {h['extra_w_pct']})")
check((h['extra_other'], h['extra_other_parks'], h['extra_same_name'], h['extra_copy'], h['extra_none_park']) == (1, 1, 2, 1, 1),
      'EXTRA kinds: other land 1 (Alpha Lake 103), same name 2 (Alpha SP 102 = the park name; BETA WMA zzc203 = the chosen name),'
      ' same size as the chosen record 1 (Alpha 104: 510 vs 500 acres), on a none: true park 1 (Delta 401)')
check([(x[0], str(x[1]), x[6]) for x in h['lists']['extra_top']] == [('US-9001', '103', 'other'), ('US-9001', '102', 'same-name'), ('US-9002', 'zzc203', 'same-name'),
                                                                   ('US-9004', '401', 'none-park'), ('US-9001', '104', 'copy')],
      'EXTRA list: other land first, then same name, none-park, same size; busiest park first inside each; a park nobody reviewed adds none (Zeta 601)')
check(S.name_words('Adams Lake SP') == S.name_words('Adams Lake State Park') and S.name_words('Beaver Creek SF') != S.name_words('Beaver Creek State Park')
      and S.name_words('CLARK LAKE (ClarkLakeWA)') == S.name_words('CLARK LAKE'), 'name words: short forms written out (SP = State Park), SP vs SF still differ, brackets dropped')
check(g['reviewed_parks'] == 3 and g['rule_rows_left_out'] == 1 and not any(x[0] == 'US-9005' for k in ('found', 'missed', 'extra') for x in h['lists'][k]),
      'the wetland-district rule row is not a person answer: left out of FOUND and EXTRA (Epsilon)')
check((t['found_pct'], t['wrong'], t['extra'], t['person_rows_in_run'], h['person_rows_in_run']) == (100.0, 0, 1, 3, 0),
      'the today run grades 100% FOUND, 0 WRONG, 1 EXTRA (Alpha SP 102); the hidden run carries no person row')
check(g['parks'] == 7 and g['parks_with_activations'] == 6, 'the line can say how many parks have an activation count (6 of 7)')
gb = S.grade(today, hidden, ovr, act, {'KPC_NO_BY_NAME': '1'})['hidden']
check((gb['wrong'], gb['no_hit'], gb['wrong_pct'], gb['wrong_w_pct']) == (5, 4, 80.0, 38.3),
      'KPC_NO_BY_NAME=1: the renumbered record (Eta 702, same name, acres within 10%) is WRONG too: 4 of 5 = 80.0%, by activations 38.3%')
ln = S.line('ZZ', g)
check(ln.startswith('ZZ  FOUND 2 of 3 person-YES records = 66.7% (by activations 75.0%); by park 2 of 2 = 100.0% get at least one, 1 get all (by activations 100.0%) | WRONG 4 records on 3 parks, hitting 3 of 5 person-NO entries = 60.0%')
      and 'EXTRA 5 records on 3 of 3 reviewed parks = 71.4%' in ln and 'other land 1 on 1 parks, same name 2, same size as the person\'s record 1, on none-parks 1' in ln and 'activations known for 6 of 7 parks' in ln, 'the printed line carries the counts')
with tempfile.TemporaryDirectory() as td:
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_key_scorecard.py'), 'compare', '--today', str(FX / 'US-ZZ-today.json'),
                        '--hidden', str(FX / 'US-ZZ-hidden.json'), '--overrides', str(FX / 'overrides.json'), '--parkinfo', str(FX / 'parkinfo-US-ZZ.json'),
                        '--state', 'ZZ', '--json', f'{td}/zz.json'], capture_output=True, text=True)
    check(r.returncode == 0 and r.stdout.startswith(ln) and J(f'{td}/zz.json')['states']['ZZ']['hidden']['found'] == 2, 'compare (two key files already built) prints the same line and writes the JSON')
vs = S.vs_lines({'states': {'ZZ': g}}, {'states': {'ZZ': S.grade(today, today, ovr, act, {})}})
check(len(vs) == 1 and 'FOUND went DOWN' in vs[0] and 'WRONG went UP' in vs[0], '--vs flags a state whose FOUND went down or WRONG went up')
for bad in (['KPC_KEY_REMATCH_IDS=0'], ['STATES=OH'], ['oops']):
    try: S.parse_sets(bad); check(False, f'--set {bad[0]} is refused')
    except SystemExit: check(True, f'--set {bad[0]} is refused (fixed by the scorecard, or not NAME=VALUE)')
import kpc_key_proof as KP  # noqa: E402
import kpc_key_freeze as KZ  # noqa: E402
check('kpc_key_scorecard.py' in KZ.NOT_RULES and not any(f.endswith('kpc_key_scorecard.py') for v in KZ.RULE_FILES.values() for f in v),
      'the scorecard is listed as not a rule file and is in no rules hash')
check(S.KPC_DATA_EXTRA == KP.KPC_DATA_EXTRA, "the KPC-Data extras laid in are the proof job's (Recreation.gov saved copy, pin fills)")
check(S.parse_sets(['KPC_ONE_RECORD_ONE_PARK=1 KPC_NO_BY_NAME=1']) == {'KPC_ONE_RECORD_ONE_PARK': '1', 'KPC_NO_BY_NAME': '1'}, '--set takes several switches')

# ---------------------------------------------------------------- 2. the whole run, stand-in builder
STUB = r'''
import json, os, pathlib, sys
st = os.environ['STATES']
k = pathlib.Path('data/us-key')
if st == 'YY': print('::notice title=US key YY::FAILED: made up'); sys.exit(0)
ov = json.loads((k / 'overrides.json').read_text())
side = 'today' if ov.get('parks') else 'hidden'
old = json.loads((k / f'US-{st}.json').read_text())
seen = {'side': side, 'env': {x: os.environ.get(x) for x in ('KPC_KEY_REMATCH_IDS', 'GEO_CACHE_MODE', 'KPC_KEY_OFFLINE', 'KPC_MASTER_OWNS', 'GEO_DETAIL',
        'GEO_PAGE', 'KPC_ANSWER_SHEET', 'KPC_BUILD_DATE', 'KPC_ONE_RECORD_ONE_PARK', 'KPC_PIECE_NAME', 'PYTHONHASHSEED')},
        'parts': sorted(p.name for p in k.glob('overrides-parks-*.json')), 'cache': sorted(p.name for p in pathlib.Path('cache/us').glob('*')),
        'parkinfo': pathlib.Path('data/parkinfo/US-ZZ.json').is_file(), 'ridb': pathlib.Path('data/access-leads/keyed-pull-raw.json.gz').is_file(),
        'old_person_rows': sum(1 for p in old['parks'].values() for x in p.get('m') or [] if str(x[3]).startswith('reviewed'))}
pathlib.Path(f'seen-{st}.json').write_text(json.dumps(seen))
src = pathlib.Path(os.environ['STUB_FX']) / f'US-ZZ-{side}.json'
(k / f'US-{st}.json').write_text(src.read_text())
print(f'{st}: 7 parks, 1 joined, 0 to check, 0 nothing found, 0 places with no POTA park, 0 s')
'''
def tree_sha(p):
    h = hashlib.sha256()
    for f in sorted(pathlib.Path(p).rglob('*')):
        if f.is_file() and '.git' not in f.parts: h.update(str(f.relative_to(p)).encode()); h.update(f.read_bytes())
    return h.hexdigest()
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td); repo, kd, cache, out = td / 'repo', td / 'kpcdata', td / 'cache', td / 'out'
    (repo / '.github/scripts').mkdir(parents=True); (repo / 'data/us-key').mkdir(parents=True)
    (repo / '.github/scripts/kpc_us_key.py').write_text(STUB)
    (repo / '.github/kpc-moved.txt').write_text('# moved\ndata/parkinfo\n')
    shutil.copyfile(FX / 'US-ZZ-today.json', repo / 'data/us-key/US-ZZ.json'); shutil.copyfile(FX / 'US-ZZ-today.json', repo / 'data/us-key/US-YY.json')
    ovd = J(FX / 'overrides.json'); part = {'US-9004': ovd['parks'].pop('US-9004')}   # a park with no 'no' list lives in a part file
    ovd['parts'] = ['overrides-parks-01.json']; ovd['parts_sha256'] = {'overrides-parks-01.json': KOVR.canon_sha(part)}
    (repo / 'data/us-key/overrides.json').write_text(json.dumps(ovd)); (repo / 'data/us-key/overrides-parks-01.json').write_text(json.dumps({'parks': part}))
    check(KOVR.load(repo / 'data/us-key/overrides.json')['parks'].get('US-9004', {}).get('none') is True, 'the made-up checkout keeps an override in a part file')
    (repo / 'img').mkdir(); (repo / 'img/big.png').write_bytes(b'x')
    g_ = lambda *a: subprocess.run(['git', '-C', str(repo), '-c', 'user.name=t', '-c', 'user.email=t@t', *a], capture_output=True, check=True)
    g_('init', '-q'); g_('add', '-A'); g_('commit', '-qm', 'fixture')
    (kd / 'data/parkinfo').mkdir(parents=True); shutil.copyfile(FX / 'parkinfo-US-ZZ.json', kd / 'data/parkinfo/US-ZZ.json')
    (kd / 'data/access-leads').mkdir(parents=True); (kd / 'data/access-leads/keyed-pull-raw.json.gz').write_bytes(b'r')
    cache.mkdir(); (cache / 'US-ZZ.json.gz').write_bytes(b'not read by the stand-in'); (cache / 'hand-US-ZZ.sgide.geojson.gz').write_bytes(b'h')
    (cache / 'US-YY.json.gz').write_bytes(b'y')
    before = tree_sha(repo)
    env = dict(os.environ, STUB_FX=str(FX), KPC_PIECE_NAME='1')   # a stray switch in the caller's shell
    cmd = [sys.executable, str(ROOT / '.github/scripts/kpc_key_scorecard.py'), 'run', '--repo', str(repo), '--states', 'ZZ', '--cache', str(cache),
           '--kpc-data', str(kd), '--out', str(out), '--set', 'KPC_ONE_RECORD_ONE_PARK=1', '--label', 'd9', '--date', '2026-11-17', '--keep']
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    check(r.returncode == 0, f'the run ends 0 ({r.returncode}; {r.stderr[-300:]})')
    sc = out / 'scratch-d9'
    st_, sh_ = J(sc / 'today/seen-ZZ.json'), J(sc / 'hidden/seen-ZZ.json')
    fixed = {'KPC_KEY_REMATCH_IDS': '1', 'GEO_CACHE_MODE': 'only', 'KPC_KEY_OFFLINE': '1', 'KPC_MASTER_OWNS': '1', 'GEO_DETAIL': '0.001', 'GEO_PAGE': '200',
             'KPC_ANSWER_SHEET': 'off', 'KPC_BUILD_DATE': '2026-11-17', 'PYTHONHASHSEED': '0'}
    check(st_['side'] == 'today' and sh_['side'] == 'hidden', 'one build saw the overrides, the other an empty set')
    check(all(s['env'][k] == v for s in (st_, sh_) for k, v in fixed.items()), 'both builds: rematch saved ids, saved copies only, offline, master owns, fixed date, answer sheet off')
    check(st_['env']['KPC_ONE_RECORD_ONE_PARK'] == sh_['env']['KPC_ONE_RECORD_ONE_PARK'] == '1', 'the --set switch goes to both builds')
    check(st_['env']['KPC_PIECE_NAME'] is None and sh_['env']['KPC_PIECE_NAME'] is None, "a switch left in the caller's shell is not passed (only --set)")
    check(st_['parts'] == ['overrides-parks-01.json'] and sh_['parts'] == [], 'the hidden copy has no override part file (the today copy keeps it)')
    check(st_['old_person_rows'] == 4 and sh_['old_person_rows'] == 0, "the hidden copy's old key file has no person row left (4 in the today copy)")
    check(J(sc / 'hidden/data/us-key/overrides.json')['parks'] == {} and J(sc / 'hidden/data/us-key/overrides.json')['blocked_ids'] == [], 'the hidden override set is empty, block list too')
    check(st_['cache'] == ['US-ZZ.json.gz', 'hand-US-ZZ.sgide.geojson.gz'] and st_['parkinfo'] and sh_['parkinfo'] and st_['ridb'] and sh_['ridb'],
      "the state's saved copy (+ hand file), KPC-Data's parkinfo and the Recreation.gov saved copy are laid in")
    check(not (sc / 'today/img/big.png').exists(), 'pictures are not copied into the scratch copy')
    rep = J(out / 'scorecard-d9.json')
    gz = rep['states']['ZZ']['hidden']
    check((gz['found'], gz['wrong'], gz['no_hit'], gz['extra']) == (2, 4, 3, 5), 'the run grades the stand-in state as the counting test does (2 / 4 / 3 / 5)')
    check(rep['switches']['KPC_ONE_RECORD_ONE_PARK'] == '1' and rep['switches']['KPC_PIECE_NAME'] == '0' and rep['set'] == {'KPC_ONE_RECORD_ONE_PARK': '1'}, 'the JSON records every switch as the builds saw it')
    txt = (out / 'scorecard-d9.txt').read_text()
    check('ZZ  FOUND 2 of 3' in txt and 'ZZ EXTRA, top 5 of 5' in txt and 'KPC_ONE_RECORD_ONE_PARK=1' in txt, 'the text report has the line, the EXTRA list and the switch')
    check(tree_sha(repo) == before, 'nothing in the checkout was written (data/ untouched)')
    r2 = subprocess.run(cmd[:cmd.index('--out') + 1] + [str(repo / 'data/score')] + cmd[cmd.index('--out') + 2:], capture_output=True, text=True, env=env)
    check(r2.returncode != 0 and 'never inside' in (r2.stderr + r2.stdout) and not (repo / 'data/score').exists(), '--out inside data/ is refused')
    r3 = subprocess.run(cmd[:cmd.index('ZZ')] + ['WV'] + cmd[cmd.index('ZZ') + 1:], capture_output=True, text=True, env=env)
    check(r3.returncode != 0 and 'no saved copy for WV' in (r3.stderr + r3.stdout), 'a state with no saved copy is refused before anything is built')
    r4 = subprocess.run(cmd[:cmd.index('ZZ')] + ['YY'] + cmd[cmd.index('ZZ') + 1:-1], capture_output=True, text=True, env=env)
    check(r4.returncode == 1 and 'YY  NOT GRADED' in r4.stdout and not (out / 'scratch-d9').exists(), 'a state the builder skips is NOT GRADED (exit 1); no --keep = scratch removed')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
