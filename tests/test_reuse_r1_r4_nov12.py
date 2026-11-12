#!/usr/bin/env python3
"""Nov 12 (KPC owner, 2026-11-12): Quality D4 reuse must-fixes R1-R4 (and two cheap extras).
R1 proof_valid takes an area and refuses a sample-only proof for an area it did not build; same-code-hash reuse still needs no proof.
R2 the signer list is the PROOF_PERSONS constant (KPC_PERSONS cannot widen it); no workflow or bot save list writes the stamp files.
R3 the monthly cron of each key workflow forces a full rebuild (live layers can go stale under reuse).
R4 reuse drops to add when the KPC-Data pins were not read.
Extras: US and CA workflow mode checks are case-insensitive; a plan over 1 MB warns.
Run: python3 -B tests/test_reuse_r1_r4_nov12.py"""
import io, json, os, pathlib, re, subprocess, sys, tempfile, contextlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_area_hash as K  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402
import kpc_key_proof as KP  # noqa: E402

ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)


def run(*a, cwd=None):
    return subprocess.run(list(a), cwd=cwd, capture_output=True, text=True)


RULES0 = {k: run(sys.executable, '-B', str(ROOT / K.FREEZE), 'rules', k, cwd=ROOT).stdout.strip() for k in ('us-key', 'ca-key', 'world-key', 'fers')}
status0 = run('git', 'status', '--porcelain', '--untracked-files=all', cwd=ROOT).stdout

# ---------------------------------------------------------------- R1 + R2 signer (a tiny valid stamp)
TODAY = __import__('datetime').date.today().isoformat()
CUR, OLD = 'c0de00000new', 'c0de00000old'


def write_stamp(repo, sample, approved_by='Brandon (KZ4CP)', approved_date=TODAY, extra_rec=None):
    (repo / '.github').mkdir(exist_ok=True)
    (repo / 'data/status/no-result-change').mkdir(parents=True, exist_ok=True)
    e = {'id': 'p1', 'kind': 'world-key', 'from': OLD, 'to': CUR, 'claim': 'no-result-change', 'proof': 'p1',
         'approved_by': approved_by, 'approved_date': approved_date}
    o40, n40, uni, tid = 'a' * 40, 'b' * 40, sorted(K.WORLD_DEFAULT), 'cd' * 32
    smp = list(sample)
    inp = {'boundary-cache:W-FR.json.gz': 'ab' * 32}
    r = {'format': 1, 'id': 'p1', 'kind': 'world-key', 'from': OLD, 'to': CUR, 'result': 'pass', 'old_commit': o40, 'new_commit': n40,
         'sample': smp, 'files': {f'data/world-key/{a}.json': ['ab' * 32, 'ab' * 32] for a in smp},
         'network_attempts': 0, 'writer': KP.WRITER, 'composition': K.COMPOSITION, 'universe': uni, 'inputs': inp,
         'inputs_id': KP.inputs_id(inp), 'inputs_id_old': KP.inputs_id(dict(inp, tree=tid)), 'inputs_id_new': KP.inputs_id(dict(inp, tree=tid)),
         'tree_inputs_old': tid, 'tree_inputs_new': tid, 'fixed_instant': '2026-11-12T00:00:00Z'}
    if extra_rec: r.update(extra_rec)
    (repo / '.github/no-result-change.json').write_text(json.dumps({'format': 1, 'stamps': [e]}))
    (repo / 'data/status/no-result-change/p1.json').write_text(json.dumps(r))
    return smp


with tempfile.TemporaryDirectory(prefix='kpc-reuse-r14-') as td:
    R = pathlib.Path(td)
    o40, n40, uni = 'a' * 40, 'b' * 40, sorted(K.WORLD_DEFAULT)
    smp = sorted(set(KP.rule_sample('world', o40, n40, uni)) | {'FR', 'DE'})
    write_stamp(R, smp)
    v, pid = K.proof_valid(R, 'world', OLD, CUR)
    check('R1 with no area argument a valid stamp is still accepted', v is True and pid == 'p1')
    inside = next(a for a in smp)
    v, pid = K.proof_valid(R, 'world', OLD, CUR, area=inside)
    check('R1 an area the proof built is accepted', v is True and pid == 'p1')
    outsider = next(a for a in ('ZZ', 'XX', 'GB', 'US', 'IE') if a not in smp)
    v, why = K.proof_valid(R, 'world', OLD, CUR, area=outsider)
    check('R1 an area the proof did not build is refused, and the reason names it',
          v is False and why == f'proof p1 did not build {outsider}')
    # decide: only sample areas reused across a shared-code move
    d = R / 'data/world-key'; d.mkdir(parents=True, exist_ok=True)
    want = ['DE', 'FR', outsider]
    inp = {a: {'layers': [f'{a}-layer']} for a in want}
    def parts(a):
        return {'code:.github/scripts/kpc_world_key.py': __import__('hashlib').sha256(CUR.encode()).hexdigest(),
                'version': __import__('hashlib').sha256(b'v').hexdigest(),
                'data:layers': __import__('hashlib').sha256(json.dumps(inp[a], sort_keys=True).encode()).hexdigest()}
    Pn = {a: parts(a) for a in want}; HSn = K.area_hashes(Pn)
    for a in want:
        (d / f'{a}.json').write_text(json.dumps({'parks': {f'{a}-0001': {}}}))
        # rewrite parts with OLD on the row, CUR on the new side
    Po = {a: dict(Pn[a], **{'code:.github/scripts/kpc_world_key.py': __import__('hashlib').sha256(OLD.encode()).hexdigest()}) for a in want}
    HSo = K.area_hashes(Po)
    rows = {a: {'rules': OLD, 'area_hash': HSo[a], 'area_parts': K.short(Po[a]), 'out_sha': K.sha_file(d / f'{a}.json')} for a in want}
    f, t, add, reu = K.decide('world', want, HSn, Pn, rows, CUR, 'reuse', False, R)
    check('R1 decide: only areas in the proof sample are reused; the outsider is rebuilt',
          outsider in f and outsider not in reu and 'DE' in reu and 'FR' in reu
          and any(f'did not build {outsider}' in r[3] for r in t if r[0] == outsider))
    # same-code-hash reuse needs no proof (even for an area that is not in any sample, and with no stamp)
    (R / '.github/no-result-change.json').unlink()
    rows_same = {a: {'rules': CUR, 'area_hash': HSn[a], 'area_parts': K.short(Pn[a]), 'out_sha': K.sha_file(d / f'{a}.json')} for a in want}
    f, t, add, reu = K.decide('world', want, HSn, Pn, rows_same, CUR, 'reuse', False, R)
    check('R1 same-code-hash reuse needs no proof: every unchanged area is reused, including one no proof built',
          f == [] and reu == want and all(r[3] == 'inputs and code unchanged' for r in t if r[0] in want))

    # R2: KPC_PERSONS cannot add a signer
    write_stamp(R, smp, approved_by='Eve')
    ev = os.environ.get('KPC_PERSONS')
    os.environ['KPC_PERSONS'] = 'Eve,Brandon,KZ4CP'
    try:
        v, why = K.proof_valid(R, 'world', OLD, CUR)
        check('R2 a stamp signed only by a name in KPC_PERSONS (not in PROOF_PERSONS) is refused',
              v is False and 'not signed' in why)
        check('R2 PROOF_PERSONS is the constant Brandon, KZ4CP', tuple(K.PROOF_PERSONS) == ('Brandon', 'KZ4CP'))
        # and the env did not leak into the default
        src = (ROOT / '.github/scripts/kpc_area_hash.py').read_text(encoding='utf-8')
        check('R2 kpc_area_hash.py no longer reads KPC_PERSONS for the proof signer list',
              'os.environ.get(\'KPC_PERSONS\')' not in src and 'PROOF_PERSONS' in src)
    finally:
        if ev is None: os.environ.pop('KPC_PERSONS', None)
        else: os.environ['KPC_PERSONS'] = ev
    write_stamp(R, smp, approved_by='Brandon (KZ4CP)')
    v, pid = K.proof_valid(R, 'world', OLD, CUR)
    check('R2 a stamp signed by Brandon is still accepted', v is True and pid == 'p1')

# ---------------------------------------------------------------- R2 guard: no workflow or bot save list writes the stamp files
STAMP = '.github/no-result-change.json'
PROOFD = 'data/status/no-result-change'
# mentions in comments / notices / artifact names, or the proof job writing an UNSIGNED record to its --out folder, are fine.
# A git add / kpc_save path list, or a bot writing those paths into the repo, is not.


def code_only(line):
    """Strip a YAML/shell/Python comment, ignoring # inside quotes, roughly."""
    out, q = [], None
    i = 0
    while i < len(line):
        c = line[i]
        if q:
            out.append(c)
            if c == q and (q != '"' or line[i - 1:i] != '\\'): q = None
        elif c in ('"', "'"):
            q = c; out.append(c)
        elif c == '#':
            break
        else:
            out.append(c)
        i += 1
    return ''.join(out)


bad_writes = []
# workflows: a git add or kpc_save_overwrite argument list that names the stamp file or the proof-record directory
for wf in sorted((ROOT / '.github/workflows').glob('*.y*ml')):
    for n, line in enumerate(wf.read_text(encoding='utf-8').splitlines(), 1):
        s = code_only(line)
        if STAMP not in s and PROOFD not in s:
            continue
        if re.search(r'\bgit\s+add\b|\bkpc_save_overwrite|\bkpc_save\.py\b', s):
            bad_writes.append(f'{wf.name}:{n}')

# bot / helper scripts: a write of those paths, except kpc_key_proof.py which writes only under its --out folder (the artifact)
SCRIPTS = ROOT / '.github/scripts'
for py in sorted(SCRIPTS.glob('kpc_*.py')):
    if py.name in ('kpc_key_proof.py', 'kpc_area_hash.py'):
        continue   # proof job writes the artifact; the reader only reads
    txt = py.read_text(encoding='utf-8', errors='replace')
    if STAMP not in txt and PROOFD not in txt and 'no-result-change' not in txt:
        continue
    # a write_text / open-for-write / Path write that names the stamp paths
    if re.search(r'(write_text|write_bytes|open\([^)]*[\'"]w)[^;\n]*no-result-change', txt):
        bad_writes.append(py.name)

check('R2 no workflow git add / save list writes the stamp file or data/status/no-result-change/',
      not bad_writes, )
# check() takes (name, cond) — fix if I passed a trailing comma only; bad_writes in the name:
if bad_writes:
    # already printed FAIL with empty reason; print the hits
    print('  hits: ' + ', '.join(bad_writes))

# rewrite the last check with hits in the name for a clean report
# (the check() above already recorded ok). Fine.

# kpc-key-proof.yml must still tell a person to add the files in a reviewed PR, and must not save them itself
prf = (ROOT / '.github/workflows/kpc-key-proof.yml').read_text(encoding='utf-8')
check('R2 the proof workflow never git-adds or kpc_saves the stamp; it only hands the artifact over',
      'git add' not in prf and 'kpc_save' not in prf and 'reviewed PR' in prf)

# ---------------------------------------------------------------- R3 monthly full rebuild
MONTHLY = {'kpc-us-key.yml': '37 9 1 * *', 'kpc-ca-key.yml': '43 10 2 * *', 'kpc-world-key.yml': '17 11 3 * *'}
import yaml
for wf, cron in MONTHLY.items():
    txt = (ROOT / '.github/workflows' / wf).read_text(encoding='utf-8')
    W = yaml.safe_load(txt)
    on = W.get(True) or W.get('on') or {}
    crons = [c.get('cron') if isinstance(c, dict) else c for c in (on.get('schedule') or [])]
    check(f'R3 {wf} still has its existing monthly cron {cron!r} (no new cron added)', cron in crons)
    want = "FULL_REBUILD: ${{ inputs.full_rebuild || ((github.event.schedule || inputs.as_schedule) == '%s' && 'yes') || '' }}" % cron
    check(f'R3 {wf} forces a full rebuild on that monthly schedule (and only that string)', want in txt)
    # the same monthly string is the one in the schedule, not a made-up one
    check(f'R3 {wf} FULL_REBUILD cron string equals the schedule entry exactly',
          txt.count(cron) >= 2)

# ---------------------------------------------------------------- extras: case-insensitive mode checks (US, CA)
us = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
check('extra: US plan compares AREA_MODE case-insensitively (.strip().lower())',
      "(os.environ.get('AREA_MODE') or 'shadow').strip().lower() not in ('add', 'reuse')" in us)
ca = (ROOT / '.github/workflows/kpc-ca-key.yml').read_text(encoding='utf-8')
check('extra: CA plan lowercases AREA_MODE before comparing it to add / reuse',
      "MODE=$(printf '%s' \"$AREA_MODE\" | tr '[:upper:]' '[:lower:]')" in ca
      and '[ "$MODE" = add ] || [ "$MODE" = reuse ]' in ca)

# ---------------------------------------------------------------- R4: missing pins drop reuse to add
real_compute, real_code, real_decide = K.compute, K.code_hash, K.decide
try:
    K.compute = lambda *a, **k: ({}, {})
    K.code_hash = lambda *a, **k: 'c0de'
    seen = []
    def dec(kind, wanted, hashes, parts, rows, cur, mode, force_full, repo):
        seen.append(mode)
        return [], [], [], []
    K.decide = dec
    with tempfile.TemporaryDirectory(prefix='kpc-r4-') as t4:
        r4 = pathlib.Path(t4)
        (r4 / 'data/world-key').mkdir(parents=True)
        (r4 / 'data/world-key/index.json').write_text('{}')
        subprocess.run(['git', 'init', '-q'], cwd=r4, check=True, capture_output=True)
        subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '--allow-empty', '-qm', 'x'],
                       cwd=r4, check=True, capture_output=True)
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rec, _ = K.run_plan(r4, 'world', ['FR'], r4 / 'data/world-key/index.json', 'reuse', False, data=None)
        err = buf.getvalue()
        check('R4 reuse with no pins: mode passed to decide is add, and the plan record says add / pins false',
              seen == ['add'] and rec['mode'] == 'add' and rec['pins'] is False)
        check('R4 ... and a warning says the pins were not read, so no reuse this run',
              '::warning title=Area hashes::KPC-Data pins not read: no reuse this run' in err)
        seen.clear()
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rec, _ = K.run_plan(r4, 'world', ['FR'], r4 / 'data/world-key/index.json', 'REUSE', False, data=None)
        check('R4 mode REUSE (any case) also drops to add when pins are missing', seen == ['add'] and rec['mode'] == 'add')
        seen.clear()
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rec, _ = K.run_plan(r4, 'world', ['FR'], r4 / 'data/world-key/index.json', 'reuse', False, data=str(r4 / 'pins'))
        check('R4 reuse with pins present: mode stays reuse, pins true, no drop warning',
              seen == ['reuse'] and rec['mode'] == 'reuse' and rec['pins'] is True
              and 'no reuse this run' not in buf.getvalue())
        seen.clear()
        rec, _ = K.run_plan(r4, 'world', ['FR'], r4 / 'data/world-key/index.json', 'add', False, data=None)
        check('R4 add mode with no pins stays add (not an error)', seen == ['add'] and rec['mode'] == 'add')

        # plan size warning (extra)
        fat = 'x' * (K.PLAN_WARN_BYTES + 8)
        real_dumps = K.json.dumps
        K.json.dumps = lambda *a, **k: fat
        try:
            outp = r4 / 'plan.json'
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                K.run_plan(r4, 'world', ['FR'], r4 / 'data/world-key/index.json', 'add', False, data=None, out_json=str(outp))
            check('extra: a plan over 1 MB prints a size warning',
                  outp.stat().st_size > K.PLAN_WARN_BYTES
                  and '::warning title=Area hashes::plan is ' in buf.getvalue()
                  and 'over 1 MB' in buf.getvalue())
            # under the limit: no warning
            K.json.dumps = lambda *a, **k: '{}'
            outp2 = r4 / 'plan-small.json'
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                K.run_plan(r4, 'world', ['FR'], r4 / 'data/world-key/index.json', 'add', False, data=None, out_json=str(outp2))
            check('extra: a small plan does not warn about size',
                  outp2.stat().st_size <= K.PLAN_WARN_BYTES and 'over 1 MB' not in buf.getvalue())
        finally:
            K.json.dumps = real_dumps
finally:
    K.compute, K.code_hash, K.decide = real_compute, real_code, real_decide

# ---------------------------------------------------------------- hashes and checkout are untouched
check('kpc_area_hash.py and kpc_key_proof.py stay in NOT_RULES',
      'kpc_area_hash.py' in KF.NOT_RULES and 'kpc_key_proof.py' in KF.NOT_RULES)
RULES1 = {k: run(sys.executable, '-B', str(ROOT / K.FREEZE), 'rules', k, cwd=ROOT).stdout.strip() for k in RULES0}
check('the four rules hashes did not move', RULES0 == RULES1)
check('git status of the checkout is unchanged by the test (no leftover files)',
      run('git', 'status', '--porcelain', '--untracked-files=all', cwd=ROOT).stdout == status0)

print('ALL PASSED' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
