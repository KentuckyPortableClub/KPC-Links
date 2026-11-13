#!/usr/bin/env python3
"""Nov 12 (KPC owner, 2026-11-12; D4): the proof job. .github/scripts/kpc_key_proof.py (sample, frozen inputs, two clean trees, network
denied and counted, fixed clock, compare, the UNSIGNED record), the reader's extra checks (kpc_area_hash.proof_valid ->
kpc_key_proof.record_problems), the plan with a valid signed proof (rebuilds nothing; stamp-rows moves the reused rows to the new code
hash, naming the proof; US too, through the plan job's plan in the --part form) and .github/workflows/kpc-key-proof.yml. Offline: a throwaway git repo in /tmp with a small deterministic
stand-in world builder; the real checkout is only read (its rules hashes are computed before and after and must not move).
Run: python3 -B tests/test_key_proof_nov12.py"""
import datetime, gzip, json, os, pathlib, shutil, signal, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_area_hash as K  # noqa: E402
import kpc_key_proof as P  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402

ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)


def run(*a, cwd=None, env=None, timeout=600):
    return subprocess.run(list(a), cwd=cwd, capture_output=True, text=True, env=env, timeout=timeout)


def sh(cwd, *a):
    r = run('git', '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'commit.gpgsign=false', *a, cwd=cwd)
    if r.returncode: raise SystemExit(f'git {a}: {r.stderr}')
    return r.stdout.strip()


RULES = lambda: {k: run(sys.executable, '-B', str(ROOT / '.github/scripts/kpc_key_freeze.py'), 'rules', k, cwd=ROOT).stdout.strip() for k in ('us-key', 'ca-key', 'world-key', 'fers')}
RULES0 = RULES()
status0 = run('git', 'status', '--porcelain', '--untracked-files=all', cwd=ROOT).stdout
check('kpc_key_proof.py is listed as NOT a rule file, and is in no kind\'s rule files', 'kpc_key_proof.py' in KF.NOT_RULES
      and all('kpc_key_proof.py' not in ' '.join(v) for v in KF.RULE_FILES.values()))
check('the rules hashes of this checkout (computed, not written down) equal kpc_area_hash\'s region hashes',
      all(K.region_hash(K.Tree(ROOT), k) == v for k, v in RULES0.items()))

BUILDER = '''"""Stand-in world builder (test copy): a deterministic join of saved-copy records to the park list."""
import datetime, gzip, json, os, pathlib, sys, time
CC = os.environ['COUNTRIES'].split()
if os.environ.get('GEO_CACHE_MODE') != 'only': sys.exit(5)
T0 = time.time()
#NET
idx_p = pathlib.Path('data/world-key/index.json'); idx = json.loads(idx_p.read_text())
for cc in CC:
    cp = pathlib.Path(os.environ.get('GEO_CACHE') or 'cache/world') / f'W-{cc}.json.gz'
    if not cp.is_file(): print('no saved copy', cc); continue
    recs = json.loads(gzip.decompress(cp.read_bytes()))['recs']
    parks = json.loads(pathlib.Path(f'data/parkinfo/{cc}.json').read_text())['parks']
    out = {}
    for ref, name in sorted(parks.items()):
        m = sorted(r['id'] for r in recs if r['name'] == name)   #JOIN
        out[ref] = {'n': name, 'm': m, 'read': time.strftime('%Y-%m-%d')}
    #SLOW
    pathlib.Path(f'data/world-key/{cc}.json').write_text(json.dumps({'cc': cc, 'parks': out}, sort_keys=True, indent=1))
    pathlib.Path('data/world-key/review').mkdir(exist_ok=True)
    pathlib.Path(f'data/world-key/review/{cc}.md').write_text(f'# {cc}\\n' + ''.join(f'- {r} {p["n"]}: {len(p["m"])}\\n' for r, p in out.items()))
    pathlib.Path('data/world-key/tracts').mkdir(exist_ok=True)
    pathlib.Path(f'data/world-key/tracts/{cc}.json').write_text(json.dumps({'built': datetime.date.today().isoformat(), 'at': time.time(),
        'now': datetime.datetime.now().isoformat(), 'stamp': time.strftime('%H:%M:%S')}))
    b = pathlib.Path(f'data/world-bounds/{cc}'); b.mkdir(parents=True, exist_ok=True)
    with gzip.open(b / 'outlines.json.gz', 'wt') as f: json.dump(sorted(out), f)
    idx['countries'][cc] = {'parks': len(out), 'matched': sum(1 for p in out.values() if p['m']), 'seconds': round(time.time() - T0)}
idx_p.write_text(json.dumps(idx, indent=1, sort_keys=True))
'''
COUNTRIES = ['AU', 'CH', 'DE', 'FR', 'GB', 'JP', 'NL']
TODAY = datetime.date.today().isoformat()

td = pathlib.Path(tempfile.mkdtemp(prefix='kpc-key-proof-test-'))
try:
    R = td / 'repo'; (R / '.github/scripts').mkdir(parents=True)
    for f in ('kpc_key_freeze.py', 'kpc_area_hash.py', 'kpc_key_proof.py'): shutil.copy(ROOT / '.github/scripts' / f, R / '.github/scripts' / f)
    def w(rel, text, root=R):
        p = root / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text if isinstance(text, bytes) else (text if isinstance(text, str) else json.dumps(text, indent=1, sort_keys=True)).encode())
    w('.github/key-rules-version.json', {'us-key': 'v5b', 'ca-key': 'v5b', 'world-key': 'v5b', 'fers': 'v1'})
    w('.github/kpc-moved.txt', '# moved to KPC-Data\ndata/parkinfo\n')
    w('.github/scripts/kpc_world_key.py', BUILDER)
    w('data/world-key/index.json', {'countries': {c: {'parks': 2} for c in COUNTRIES}})
    for c in COUNTRIES: w(f'data/world-key/{c}.json', {'cc': c, 'parks': {f'{c}-0001': {'n': f'{c} park one', 'm': []}, f'{c}-0002': {'n': f'{c} park two', 'm': []}}})
    w('data/world-key/overrides.json', {'parks': {'DE-0001': {'no': ['x']}}})
    sh(R, 'init', '-q', '-b', 'main'); sh(R, 'add', '-A'); sh(R, 'commit', '-qm', 'A'); A = sh(R, 'rev-parse', 'HEAD')
    def commit(msg, edit, base=None):
        if base: sh(R, 'checkout', '-q', base)
        sh(R, 'checkout', '-q', '-B', 'b-' + msg)
        edit(); sh(R, 'add', '-A'); sh(R, 'commit', '-qm', msg); return sh(R, 'rev-parse', 'HEAD')
    src = lambda s: w('.github/scripts/kpc_world_key.py', s)
    # B: comments, a log line and a renamed variable only (a refactor): results must be identical
    B = commit('B', lambda: src(BUILDER.replace('#NET', '# a comment that moves the code hash\nprint("building", CC, flush=True)').replace('idx_p', 'index_path')), A)
    # C: one park's join changes in FR
    C = commit('C', lambda: src(BUILDER.replace('#JOIN', '\n        if cc == "FR" and ref.endswith("2"): m = []')), A)
    # D: equal outputs, but the new code tries the network (caught)
    D = commit('D', lambda: src(BUILDER.replace('#NET', 'import socket\ntry: socket.create_connection(("example.invalid", 80), timeout=1)\nexcept OSError: pass')), A)
    # E: B, then another code change after the proof
    E = commit('E', lambda: src(BUILDER.replace('#NET', '# a comment that moves the code hash\nprint("building", CC, flush=True)').replace('idx_p', 'index_path') + '# later\n'), B)
    # F: B plus a data change for DE only (its own part moves: built, compared, not claimed)
    F = commit('F', lambda: w('data/world-key/overrides.json', {'parks': {'DE-0001': {'no': ['y']}}}), B)
    # S: a slow build (for the cancel case)
    S = commit('S', lambda: src(BUILDER.replace('#SLOW', 'time.sleep(60)')), A)
    sh(R, 'checkout', '-q', 'main')
    # the frozen inputs: saved copies (the boundary-cache assets) and ONE KPC-Data commit (the moved park lists)
    INP = td / 'assets'; INP.mkdir()
    for c in COUNTRIES:
        with gzip.open(INP / f'W-{c}.json.gz', 'wt') as f: json.dump({'recs': [{'id': f'{c}r1', 'name': f'{c} park one'}, {'id': f'{c}r2', 'name': f'{c} park two'}]}, f)
    KD = td / 'kpcdata'
    for c in COUNTRIES: w(f'data/parkinfo/{c}.json', {'parks': {f'{c}-0001': f'{c} park one', f'{c}-0002': f'{c} park two'}}, KD)
    sh(KD, 'init', '-q'); sh(KD, 'add', '-A'); sh(KD, 'commit', '-qm', 'kd')
    HAVE = P.have_from_assets('world', [f.name for f in INP.iterdir()] + ['hand-US-x.geojson.gz', 'US-KY.json.gz'])
    check('the saved-copy list is read from the release asset names (world: W-<CC>.json.gz only)', HAVE == COUNTRIES)

    # ---------------------------------------------------------------- the sample
    s1 = P.make_sample(R, 'world', A, B, '', HAVE); s2 = P.make_sample(R, 'world', A, B, '', HAVE)
    check('S1 the sample is deterministic from (kind, old, new): the same twice', s1 == s2)
    check('S1 it holds the fixed biggest / weirdest world areas (AU FR CH JP) and 3 drawn from the commit shas',
          {'AU', 'FR', 'CH', 'JP'} <= set(s1['claimed']) and sum('chosen from the commit shas' in v for v in s1['why'].values()) == 3)
    s3 = P.make_sample(R, 'world', A, B, 'NL, GB', HAVE)
    check('S1 extras only ADD to the sample (never remove one)', set(s1['claimed']) <= set(s3['claimed']) and s3['extras'] == ['NL', 'GB'])
    try: P.make_sample(R, 'world', A, B, 'ZZ', HAVE); bad_extra = False
    except SystemExit as e: bad_extra = 'not an area' in str(e)
    check('S1 an unknown extra area stops the proof (never silently dropped)', bad_extra)
    r = run(sys.executable, '-B', str(R / '.github/scripts/kpc_key_proof.py'), 'sample', 'world', '--repo', str(R), '--old', A, '--new', B, '--exclude', 'AU')
    check('S1 the command line has no way to leave an area out (--exclude is refused)', r.returncode == 2)
    check('S1 the record names why each area is in the sample', all(s1['why'][a] for a in s1['claimed']))

    def proof(old, new, name, extras='', **kw):
        out = td / f'out-{name}'
        return P.run_proof(R, 'world', old, new, str(INP), str(KD), out, extras, td / f'work-{name}', 'r1', 5, False, str(td / f'sum-{name}.md'), HAVE), out

    # ---------------------------------------------------------------- VALID
    rec, out = proof(A, B, 'valid')
    check('V1 a comments / logging / refactor change: the code hash moves', rec['from'] != rec['to'] and rec['from'] == K.code_hash(td / 'work-valid/old', 'world'))
    check('V1 ... and the proof PASSES: every compared file byte-identical, 0 network attempts', rec['result'] == 'pass' and rec['network_attempts'] == 0
          and rec['files'] and all(a == b for a, b in rec['files'].values()))
    check('V1 the key file, review page, tracts file, world-bounds folder and index row of each claimed area are compared',
          all(f'data/world-key/{c}.json' in rec['files'] and f'data/world-key/tracts/{c}.json' in rec['files'] and f'data/world-bounds/{c}/' in rec['files']
              and f'data/world-key/index.json#countries.{c}' in rec['files'] for c in rec['sample']))
    check('V1 the record carries the evidence: inputs (sha256 each), the fixed instant, tool versions, the sample and why, the run id',
          rec['inputs'] and rec['inputs_id_old'] == rec['inputs_id_new'] and rec['fixed_instant'] and rec['tools'].get('python') and rec['why'] and rec['id'].endswith('-r1')
          and any(k.startswith('boundary-cache:W-AU') for k in rec['inputs']) and any(k.startswith('kpc-data:data/parkinfo/AU') for k in rec['inputs']))
    rp = out / P.PROOF_DIR / f"{rec['id']}.json"; entry = json.loads((out / 'stamp-entry.json').read_text())
    check('V1 the job writes the record and an UNSIGNED stamp entry (approved_by / approved_date empty: it never signs)',
          rp.is_file() and entry['approved_by'] == '' and entry['approved_date'] == '' and entry['proof'] == rec['id'] and entry['claim'] == 'no-result-change')
    check('V1 the record is under 1 MB and passes the reader\'s own record checks', rp.stat().st_size < 1_000_000 and P.record_problems(json.loads(rp.read_text()), 'world', K.COMPOSITION) == [])
    check('V1 the job summary says PASS and names the proof', '**PASS**' in (td / 'sum-valid.md').read_text() and rec['id'] in (td / 'sum-valid.md').read_text())

    # the main checkout after the owner's PR: the new commit's tree + the record + the signed stamp entry
    M = td / 'main'; P.export(R, B, M)
    (M / P.PROOF_DIR).mkdir(parents=True); shutil.copy(rp, M / P.PROOF_DIR / rp.name)
    for c in COUNTRIES: shutil.copy(td / 'work-valid/new/data/world-key' / f'{c}.json', M / 'data/world-key' / f'{c}.json') if (td / 'work-valid/new/data/world-key' / f'{c}.json').is_file() else None
    def stamp(**e):
        x = dict(entry, approved_by='Brandon (KZ4CP)', approved_date=TODAY); x.update(e)
        (M / '.github/no-result-change.json').write_text(json.dumps({'format': 1, 'stamps': [x]}))
    check('U1 UNSIGNED: the entry as the job wrote it is refused by the reader', (stamp(approved_by='', approved_date=''), K.proof_valid(M, 'world', rec['from'], rec['to']))[1][0] is False)
    check("U1 signed only 'KPC owner': refused", (stamp(approved_by='KPC owner'), K.proof_valid(M, 'world', rec['from'], rec['to']))[1][0] is False)
    stamp()
    v, pid = K.proof_valid(M, 'world', rec['from'], rec['to'])
    check('V2 once the owner signs it (a reviewed PR), the reader accepts it', v and pid == rec['id'])
    # the plan: rows recorded at the old commit (rules = old code hash), the code moved to the new hash, reuse on
    hA, pA = K.compute(R, A, 'world', 3, None, None, 'verdict'); hB, pB = K.compute(R, B, 'world', 3, None, None, 'verdict')
    rows = {c: {'rules': rec['from'], 'area_hash': hA[c], 'area_parts': K.short(pA[c]), 'out_sha': K.sha_file(M / f'data/world-key/{c}.json')} for c in COUNTRIES}
    want = sorted(COUNTRIES)
    # (the fixture's index lists only these countries; the other default countries of the world list have no row and are 'added' in
    # reuse mode, as on a real first run: only the planned areas count here)
    none_of = lambda f: not (set(f) & set(want)); all_of = lambda f: set(want) <= set(f)
    f, t, add, reu = K.decide('world', want, hB, pB, rows, rec['to'], 'reuse', False, M)
    check('V3 a shared-code-only change with a VALID signed proof rebuilds NOTHING in reuse mode', none_of(f) and reu == want
          and all(f"proven no result change ({rec['id']})" in x[3] for x in t if x[0] in want))
    f2, _, _, reu2 = K.decide('world', want, hB, pB, rows, rec['to'], 'shadow', False, M)
    check('V3 ... in shadow mode it is only reported (every area still built)', f2 == want and not reu2)
    idx = M / 'data/world-key/index.json'; d = json.loads(idx.read_text()); d['countries'] = {c: dict(d['countries'].get(c) or {}, **rows[c]) for c in COUNTRIES}
    idx.write_text(json.dumps(d, indent=1))
    plan = {'reused': reu, 'code_hash': rec['to'], 'hashes': hB, 'parts': {c: K.short(pB[c]) for c in pB}, 'plan_sha': B}
    K.stamp_rows(M, 'world', idx, [], plan, B)
    d = json.loads(idx.read_text())['countries']
    check('V4 stamp-rows moves every reused row to the new code hash WITHOUT a rebuild and names the proof (proved_by, proved_from)',
          all(d[c]['rules'] == rec['to'] and d[c]['proved_by'] == rec['id'] and d[c]['proved_from'] == rec['from'] and d[c]['area_hash'] == hB[c] for c in COUNTRIES))
    check('V4 ... the bytes and the commit they were really built from stay as recorded (out_sha unchanged, no built_sha claimed)',
          all(d[c]['out_sha'] == rows[c]['out_sha'] and 'built_sha' not in d[c] for c in COUNTRIES))
    f, t, _, reu = K.decide('world', want, hB, pB, d, rec['to'], 'reuse', False, M)
    check('V4 the next plan reuses them as "inputs and code unchanged" (no proof needed any more)', none_of(f) and all(x[3] == 'inputs and code unchanged' for x in t if x[0] in want))
    check('V4 the whole-key sanity check passes on the moved rows', K.sanity(M, 'world') == [] or all(not b.startswith(('2', '3', '5')) for b in K.sanity(M, 'world')))
    d2 = {c: dict(rows[c]) for c in COUNTRIES}; idx.write_text(json.dumps({'countries': d2}, indent=1)); stamp(approved_by='')
    K.stamp_rows(M, 'world', idx, [], plan, B)
    check('V4 with no valid proof at stamp time, stamp-rows moves nothing', all(json.loads(idx.read_text())['countries'][c]['rules'] == rec['from'] for c in COUNTRIES))
    stamp()

    # ---------------------------------------------------------------- MISSING
    (M / P.PROOF_DIR / rp.name).rename(td / 'kept.json')
    v, why = K.proof_valid(M, 'world', rec['from'], rec['to'])
    f, _, _, reu = K.decide('world', want, hB, pB, rows, rec['to'], 'reuse', False, M)
    check('M1 MISSING record: not valid, every area rebuilt', not v and 'missing' in why and all_of(f) and not reu)
    (td / 'kept.json').rename(M / P.PROOF_DIR / rp.name)
    (M / '.github/no-result-change.json').unlink()
    check('M1 MISSING stamp file: not valid', K.proof_valid(M, 'world', rec['from'], rec['to'])[0] is False)
    stamp()

    # ---------------------------------------------------------------- STALE
    P.export(R, E, td / 'eE'); hE = K.code_hash(td / 'eE', 'world')
    v, why = K.proof_valid(M, 'world', rec['from'], hE)
    f, _, _, reu = K.decide('world', want, hB, pB, rows, hE, 'reuse', False, M)
    check('T1 STALE: the code changes again after the proof (new hash): not valid, full rebuild', hE != rec['to'] and not v and all_of(f) and not reu)
    def tamper(fn, label, expect):
        r0 = json.loads(rp.read_text()); r1 = json.loads(rp.read_text()); fn(r1)
        (M / P.PROOF_DIR / rp.name).write_text(json.dumps(r1))
        v, why = K.proof_valid(M, 'world', rec['from'], rec['to'])
        f, _, _, reu = K.decide('world', want, hB, pB, rows, rec['to'], 'reuse', False, M)
        check(f'T1 STALE: {label}: not valid ({why[:90]}), full rebuild', not v and expect in why and all_of(f) and not reu)
        (M / P.PROOF_DIR / rp.name).write_text(json.dumps(r0))
    tamper(lambda r: r.update(tree_inputs_new='0' * 64, inputs_id_new='1' * 64), 'the two sides had different inputs', 'inputs differ')
    tamper(lambda r: r['inputs'].update({'boundary-cache:W-AU.json.gz': 'f' * 64}), 'an input sha256 changed after the run', 'inputs list')
    tamper(lambda r: r.update(composition='ah0'), 'the composition id differs', 'composition')
    tamper(lambda r: (r['sample'].remove('CH'), [r['files'].pop(k) for k in list(r['files']) if '/CH' in k or k.endswith('.CH')]), 'the sample is smaller than the rule (CH left out)', 'sample smaller')
    tamper(lambda r: r.update(universe=['AU', 'FR', 'CH', 'JP']), 'the universe was shrunk (the drawn areas would change)', 'universe')
    tamper(lambda r: r.update(writer='by hand'), 'a record not written by the proof job', 'not written by')
    check('T1 the untampered record is valid again', K.proof_valid(M, 'world', rec['from'], rec['to'])[0])

    # ---------------------------------------------------------------- FAILED
    recC, outC = proof(A, C, 'fail')
    check('F1 FAILED: one park\'s join changes in FR: result fail, the first differing file is FR\'s key file, the summary names the park',
          recC['result'] == 'fail' and any('data/world-key/FR.json' in p and 'FR-0002' in p for p in recC['problems']))
    check('F1 ... no stamp entry is written; the record (result fail) is kept as evidence', not (outC / 'stamp-entry.json').exists()
          and (outC / P.PROOF_DIR / f"{recC['id']}.json").is_file())
    check('F1 ... the job summary says FAIL and lists the problem', '**FAIL**' in (td / 'sum-fail.md').read_text() and 'FR-0002' in (td / 'sum-fail.md').read_text())
    shutil.copy(outC / P.PROOF_DIR / f"{recC['id']}.json", M / P.PROOF_DIR / f"{recC['id']}.json")
    (M / '.github/no-result-change.json').write_text(json.dumps({'format': 1, 'stamps': [dict(json.loads((td / 'out-valid/stamp-entry.json').read_text()), id=recC['id'],
                                                                     proof=recC['id'], to=recC['to'], approved_by='Brandon (KZ4CP)', approved_date=TODAY)]}))
    hC, pC = K.compute(R, C, 'world', 3, None, None, 'verdict')
    f, _, _, reu = K.decide('world', want, hC, pC, rows, recC['to'], 'reuse', False, M)
    check('F1 even if someone signed it, a failed record is no proof: the plan rebuilds every area', not K.proof_valid(M, 'world', recC['from'], recC['to'])[0] and all_of(f) and not reu)
    stamp()

    # ---------------------------------------------------------------- NETWORK DENIED
    recD, outD = proof(A, D, 'net')
    check('N1 NETWORK: the new code tries a connect (caught inside the build): the attempt is COUNTED and the proof FAILS, though every file is equal',
          recD['network_attempts'] >= 7 and recD['result'] == 'fail' and all(a == b for a, b in recD['files'].values()) and any('network' in p for p in recD['problems']))
    check('N1 ... the attempt was denied (the guard raises), never sent; the log names the call site', 'kpc_world_key.py' in (outD / 'build.log').read_text() or recD['network_attempts'] > 0)

    # ---------------------------------------------------------------- OWN PART MOVED (data, built and compared, not claimed)
    recF, outF = proof(B, F, 'own')
    check('O1 an area whose own data moved (DE) is built and compared but NOT in the claim; the rest PASS',
          recF['result'] == 'pass' and 'DE' in recF['excluded'] and 'DE' not in recF['sample'] and recF['excluded']['DE']['verdict'] == 'same')

    # ---------------------------------------------------------------- FIXED CLOCK (the guard alone, two wall-clock times)
    T = td / 'work-valid/new'; shim = P.write_shim(td / 'shim2')
    def build_once(fixed):
        e = P.build_env(T, 'world', shim, td / 'n.log', fixed, {'COUNTRIES': 'AU'})
        if fixed is None: e.pop('KPC_PROOF_FIXED'); e.pop('KPC_BUILD_DATE', None)
        r = run(sys.executable, '-B', '.github/scripts/kpc_world_key.py', cwd=T, env=e)
        return r.returncode, (T / 'data/world-key/tracts/AU.json').read_bytes(), (T / 'data/world-bounds/AU/outlines.json.gz').read_bytes()
    a1 = build_once(1762900000); time.sleep(1.2); a2 = build_once(1762900000)
    check('C1 FIXED CLOCK: two runs 1.2 s apart under the guard give identical bytes (date, time.time, datetime.now, strftime, gzip mtime)', a1[0] == 0 and a1 == a2)
    b1 = build_once(None); time.sleep(1.2); b2 = build_once(None)
    check('C1 ... and without the guard they differ (the stand-in reads the clock, as the builders do today)', b1[1] != b2[1])
    check('C1 the fixed instant is the new commit\'s committer time (recorded, reproducible)',
          rec['fixed_instant'] == datetime.datetime.fromtimestamp(int(sh(R, 'show', '-s', '--format=%ct', B)), datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))

    # ---------------------------------------------------------------- CANCELLED
    outS = td / 'out-cancel'
    p = subprocess.Popen([sys.executable, '-B', str(R / '.github/scripts/kpc_key_proof.py'), 'run', 'world', '--repo', str(R), '--old', A, '--new', S,
                          '--inputs', str(INP), '--kpc-data', str(KD), '--out', str(outS), '--work', str(td / 'work-cancel'), '--no-netns'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    for _ in range(300):
        if (td / 'work-cancel/old/.kpc-proof').is_dir(): break
        time.sleep(0.1)
    time.sleep(1.0); os.killpg(p.pid, signal.SIGTERM); p.wait(30)
    check('X1 a CANCELLED run (stopped mid-build) writes nothing: no record, no stamp entry, no result',
          not (outS / P.PROOF_DIR).exists() and not (outS / 'stamp-entry.json').exists() and not (outS / 'result.txt').exists())
finally:
    shutil.rmtree(td, ignore_errors=True)

# ---------------------------------------------------------------- US: reuse under a proof (Brandon, Nov 12 10:59 AM CT: wire the US too)
# The US join stamps each SAVED state from its own build part (--part); a state the PLAN JOB reused under a valid proof was built by no
# part, so stamp-rows now also takes the plan job's plan (--plan) and moves those rows (kpc_area_hash.move_reused), as world / Canada do.
import contextlib, io  # noqa: E402
_real_pv = K.proof_valid
OLDC, NEWC = 'c0de0000old0', 'c0de0000new0'


def us_fixture(t):
    t = pathlib.Path(t); d = t / 'data/us-key'; d.mkdir(parents=True)
    rows, hs, pt = {}, {}, {}
    for st in ('TN', 'FL', 'OR', 'KY'):
        (d / f'US-{st}.json').write_text(json.dumps({'st': st, 'parks': {}}))
        own = {'data:overrides': 'o' * 11 + st[0], 'code:.github/scripts/kpc_us_key.py': OLDC}
        rows[st] = {'parks': 1, 'rules': OLDC, 'area_hash': 'old-' + st, 'area_parts': dict(own), 'out_sha': K.sha_file(d / f'US-{st}.json')}
        pt[st] = dict(own, **{'code:.github/scripts/kpc_us_key.py': NEWC}); hs[st] = 'new-' + st
    (d / 'index.json').write_text(json.dumps({'states': rows}, indent=1))
    job = {'mode': 'reuse', 'code_hash': NEWC, 'plan_sha': 'abc', 'hashes': hs, 'parts': pt, 'reused': ['FL', 'OR', 'KY'], 'list': ['TN']}
    part = t / 'parts/us-key-part-0'; part.mkdir(parents=True)
    (part / 'states.txt').write_text('TN\n'); (part / 'built-sha.txt').write_text('abc\n')
    (part / 'area-plan.json').write_text(json.dumps(dict(job, mode='shadow', reused=[], hashes={'TN': hs['TN']}, parts={'TN': pt['TN']})))
    (t / 'plan-job.json').write_text(json.dumps(job))
    return t, d / 'index.json', job, part


try:
    with tempfile.TemporaryDirectory() as t:
        t, idx, job, part = us_fixture(t)
        (t / 'data/us-key/US-KY.json').write_text('{"edited": 1}')                      # KY: its key file is not the recorded bytes
        r0 = json.loads(idx.read_text())['states']
        f, tb, _, reu = K.decide('us', ['TN', 'FL', 'OR', 'KY'], job['hashes'], job['parts'], r0, NEWC, 'reuse', False, t, proof=lambda *a, **k: (True, 'p-us-1'))
        check('US1 the plan (kind us) reuses a state whose only move is shared code under a valid proof; a state whose key file was edited is rebuilt',
              sorted(reu) == ['FL', 'OR', 'TN'] and f == ['KY'] and all('proven no result change (p-us-1)' in x[3] for x in tb if x[0] in ('FL', 'OR', 'TN')))
        f2, _, _, reu2 = K.decide('us', ['TN', 'FL', 'OR', 'KY'], job['hashes'], job['parts'], r0, NEWC, 'shadow', False, t, proof=lambda *a, **k: (True, 'p-us-1'))
        check('US1 ... in shadow (the default) the US list is unchanged, nothing reused', not reu2 and sorted(f2) == ['FL', 'KY', 'OR', 'TN'])
        K.proof_valid = lambda *a, **k: (True, 'p-us-1')
        done, same = K.stamp_rows_parts(t, 'us', idx, ['TN'], [str(part)], reuse_plan=job)
        d = json.loads(idx.read_text()); s_ = d['states']
        check('US2 stamp-rows (US --part form) with the plan job\'s plan: FL and OR (reused under a valid proof) move to the new code hash, naming the proof, no rebuild',
              all(s_[x]['rules'] == NEWC and s_[x]['proved_by'] == 'p-us-1' and s_[x]['proved_from'] == OLDC and s_[x]['area_hash'] == 'new-' + x for x in ('FL', 'OR')))
        check('US2 ... their recorded bytes stay (out_sha unchanged, no built_sha claimed)', all(s_[x]['out_sha'] == r0[x]['out_sha'] and 'built_sha' not in s_[x] for x in ('FL', 'OR')))
        check('US2 ... KY (key file edited) is NOT moved; TN (saved) is stamped from its own part, not by the proof',
              s_['KY']['rules'] == OLDC and 'proved_by' not in s_['KY'] and done == ['TN'] and s_['TN']['area_hash'] == 'new-TN' and s_['TN']['built_sha'] == 'abc' and 'proved_by' not in s_['TN'])
        check('US2 ... areas_reused is FL/OR (moved under the proof) plus TN (byte-identical, verified-same); KY is not claimed; nothing was rebuilt', d['areas_reused'] == ['FL', 'OR', 'TN'] and d['areas_rebuilt'] == [])
    with tempfile.TemporaryDirectory() as t:
        t, idx, job, part = us_fixture(t)
        K.proof_valid = lambda *a, **k: (False, 'no valid proof')
        K.stamp_rows_parts(t, 'us', idx, ['TN'], [str(part)], reuse_plan=job)
        check('US3 no valid proof at stamp time: no US row moves', all(json.loads(idx.read_text())['states'][x]['rules'] == OLDC for x in ('FL', 'OR', 'KY')))
    with tempfile.TemporaryDirectory() as t:
        t, idx, job, part = us_fixture(t)
        job['parts']['OR'] = dict(job['parts']['OR'], **{'data:overrides': 'moved'}); (t / 'plan-job.json').write_text(json.dumps(job))
        K.proof_valid = lambda *a, **k: (True, 'p-us-1')
        K.stamp_rows_parts(t, 'us', idx, [], [str(part)], reuse_plan=job)
        s_ = json.loads(idx.read_text())['states']
        check('US3 a reused state whose OWN data moved is not moved (a proof covers shared code only); FL still moves', s_['OR']['rules'] == OLDC and s_['FL']['rules'] == NEWC)
        K.stamp_rows_parts(t, 'us', idx, [], [str(part)], reuse_plan=job)
        check('US3 running it again changes nothing (FL already on the new code hash)', json.loads(idx.read_text())['states'] == s_)
    for mode, writes in (('reuse', True), ('add', True), ('shadow', False), (None, False)):
        with tempfile.TemporaryDirectory() as t:
            t, idx, job, part = us_fixture(t); before = idx.read_bytes()
            K.proof_valid = lambda *a, **k: (True, 'p-us-1')
            args = ['stamp-rows', 'us', '--repo', str(t), '--index', str(idx), '--saved', 'TN', '--part', str(part), '--plan', str(t / 'plan-job.json'),
                    '--shadow-out', str(t / 'tmp/us.json')] + (['--mode', mode] if mode else [])
            env0 = os.environ.pop('KPC_AREA_HASH', None)
            with contextlib.redirect_stdout(io.StringIO()): rc = K.main(args)
            if env0 is not None: os.environ['KPC_AREA_HASH'] = env0
            s_ = json.loads(idx.read_text())['states']
            if writes:
                check(f'US4 CLI stamp-rows us --part ... --plan (mode {mode}): FL / OR moved under the proof, TN stamped', rc == 0 and s_['FL']['rules'] == NEWC and s_['OR']['proved_by'] == 'p-us-1' and s_['TN']['area_hash'] == 'new-TN')
            else:
                check(f'US4 CLI stamp-rows us --part ... --plan (mode {mode or "unset"}): shadow writes nothing, index.json byte for byte', rc == 0 and idx.read_bytes() == before)
    with tempfile.TemporaryDirectory() as t:
        t, idx, job, part = us_fixture(t); (t / 'plan-job.json').write_text('')      # the plan job had no plan (an empty output)
        K.proof_valid = lambda *a, **k: (True, 'p-us-1')
        with contextlib.redirect_stdout(io.StringIO()): rc = K.main(['stamp-rows', 'us', '--repo', str(t), '--index', str(idx), '--saved', 'TN', '--part', str(part), '--plan', str(t / 'plan-job.json'), '--mode', 'reuse'])
        s_ = json.loads(idx.read_text())
        check('US4 an empty plan-job plan: no crash, FL is not moved, TN is stamped from its part and counted reused (verified-same bytes)', rc == 0 and s_['states']['FL']['rules'] == OLDC and s_['states']['TN']['area_hash'] == 'new-TN' and s_['areas_reused'] == ['TN'] and s_['areas_rebuilt'] == [])
finally:
    K.proof_valid = _real_pv

import yaml as _y  # noqa: E402
_us_txt = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8'); _us = _y.safe_load(_us_txt)
_st = [s for s in _us['jobs']['join']['steps'] if 'kpc_area_hash.py stamp-rows us' in str(s.get('run', ''))]
check('US5 workflow: the plan job hands its per-state plan to the join (outputs.area_plan, printed by the plan step)',
      _us['jobs']['plan']['outputs'].get('area_plan') == '${{ steps.p.outputs.area_plan }}' and "print('area_plan=' + json.dumps(" in _us_txt)
check('US5 workflow: the join\'s stamp-rows passes --part per build part AND --plan (the plan job\'s plan), with AREA_MODE (default reuse)',
      len(_st) == 1 and '--plan "$RUNNER_TEMP/area-plan-job.json"' in _st[0]['run'] and 'printf \'%s\' "$AREA_PLAN" > "$RUNNER_TEMP/area-plan-job.json"' in _st[0]['run']
      and _st[0]['env'].get('AREA_PLAN') == '${{ needs.plan.outputs.area_plan }}' and _st[0]['env'].get('AREA_MODE', '').startswith("${{ vars.KPC_AREA_HASH || 'reuse' }}"))

# ---------------------------------------------------------------- the workflow
import yaml  # noqa: E402
WFP = ROOT / '.github/workflows/kpc-key-proof.yml'
txt = WFP.read_text(); wf = yaml.safe_load(txt); on = wf.get(True) or wf.get('on') or {}
check('W1 the workflow parses (PyYAML) and is started by hand only: workflow_dispatch, no schedule, no push, no workflow_run',
      isinstance(on, dict) and list(on) == ['workflow_dispatch'] and 'cron' not in txt)
inp = on['workflow_dispatch']['inputs']
check('W1 inputs: kind (us | ca | world), old, new, areas (extras), and nothing that can shrink the sample',
      inp['kind'].get('options') == ['us', 'ca', 'world'] and {'old', 'new', 'areas'} <= set(inp)
      and not any(k in inp for k in ('exclude', 'only', 'sample', 'skip', 'fixed')) and set(inp) <= {'kind', 'old', 'new', 'areas', 'data_ref'})
check('W1 permissions as narrow as possible: contents read (no write, no actions, no pull-requests)', wf.get('permissions') == {'contents': 'read'}
      and all((j.get('permissions') in (None, {'contents': 'read'})) for j in wf['jobs'].values()))
check('W1 one proof of a kind at a time (concurrency group by kind, not cancelled by a second start)',
      'inputs.kind' in str(wf.get('concurrency', {}).get('group')) and wf['concurrency'].get('cancel-in-progress') is False)
steps = [s for j in wf['jobs'].values() for s in j['steps']]
writes = [s for s in steps if 'upload-artifact' in str(s.get('uses', ''))]
check('W1 every step that writes (the artifact uploads) is guarded by !cancelled()', writes and all('!cancelled()' in str(s.get('if', '')) for s in writes))
check('W1 it never saves a key or outline file, never pushes, never dispatches a key run, never uploads to a release',
      'git push' not in txt and 'gh workflow run' not in txt and '/dispatches' not in txt and 'release upload' not in txt and 'kpc_save' not in txt)
check('W1 only GitHub is contacted for inputs (release assets of this repo, the two repos), before the build step',
      'boundary-cache' in txt and 'KentuckyPortableClub/KPC-Data' in txt and 'arcgis' not in txt and 'fs.usda' not in txt)
pv = [s for s in steps if s.get('id') == 'proof']
check('W1 the proof step runs kpc_key_proof.py run with the fetched inputs', pv and 'kpc_key_proof.py run' in pv[0]['run'])
check('W1 a G8 hidden-failures step closes the job', 'Report hidden failures' in (steps[-1].get('name') or ''))

check('the rules hashes did not move (computed before and after the test)', RULES() == RULES0)
check('git status of the checkout is unchanged', run('git', 'status', '--porcelain', '--untracked-files=all', cwd=ROOT).stdout == status0)
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
