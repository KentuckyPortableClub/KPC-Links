#!/usr/bin/env python3
"""Offline: a format/composition-only hash move is reused, not rebuilt; an undeclared rules change
is a VERIFY, not a silent whole-key full rebuild; key_order accepts every area row on the current
hash; US/CA workflows default to reuse; full=1 only for the monthly run or owner full_rebuild."""
import io, json, os, pathlib, sys, tempfile, contextlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_area_hash as AH  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402
import kpc_key_order as KO  # noqa: E402

ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)

check('CA is in freeze ROWS (provinces get per-row rules)', KF.ROWS.get('ca-key') == 'provinces')
check('stale_areas still returns [] when every row is stale (helper unchanged)',
      KF.stale_areas('us-key', {'states': {'TN': {}, 'OH': {}}}, 'abc') == [])
check('all_area_ids lists every row', KF.all_area_ids('us-key', {'states': {'OH': {}, 'TN': {}}}) == ['US-OH', 'US-TN'])

# Quality #179 M1/M2: an added or removed part (other than format-only / a declared composition migration) is moved.
# composition and the first appearance of rules-version are format-only; a rules-version *change* is real.
op = {'data:pins': 'aaa000000000', 'version': 'ah2000000000', 'code:kpc_us_key.py': '111000000000'}
np_fmt = {'data:pins': 'aaa000000000XXXX', 'version': 'ah2000000000YYYY', 'code:kpc_us_key.py': '111000000000ZZZZ',
          'composition': 'cccc00000000XXXX', 'rules-version': 'rrrr00000000XXXX'}
check('real_inputs_moved is false for the composition / rules-version split (first appearance) with the same real inputs',
      not AH.real_inputs_moved(op, AH.short(np_fmt), 'ah2'))
check('a previously recorded pin change IS a real input change',
      AH.real_inputs_moved(op, dict(AH.short(np_fmt), **{'data:pins': 'bbb000000000'}), 'ah2'))
check('a first override (undeclared new part) IS a real input change',
      AH.real_inputs_moved(op, dict(AH.short(np_fmt), **{'data:data/overrides/world/AE-0001.json': 'new000000000'}), 'ah2'))
check('a declared trails composition-migration first appearance is not a real input change',
      not AH.real_inputs_moved(op, dict(AH.short(np_fmt), **{'data:data/trails/*': 'trail00000000'}), 'ah2'))
op_ver = dict(op, **{'rules-version': 'aaaa00000000'})
np_ver = dict(AH.short(np_fmt), **{'rules-version': 'bbbb00000000'})
check('a key-rules-version bump IS a real input change', AH.real_inputs_moved(op_ver, np_ver, 'ah2'))

rows = {'DE': {'area_hash': 'old', 'area_parts': op, 'out_sha': 'x', 'rules': 'oldc', 'complete': True}}
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    (t / 'data/world-key').mkdir(parents=True)
    (t / 'data/world-key/DE.json').write_text('{}')
    import hashlib
    sha = hashlib.sha256((t / 'data/world-key/DE.json').read_bytes()).hexdigest()
    rows['DE']['out_sha'] = sha
    hashes = {'DE': 'newhash'}
    parts = {'DE': np_fmt}
    final, table, added, reused = AH.decide('world', ['DE'], hashes, parts, rows, 'newc', 'reuse', False, t)
    check(f'format-only DE is reused, not rebuilt (final={final}, reused={reused}, table={table})',
          final == [] and reused == ['DE'] and 'format or composition' in table[0][3])

# first override is rebuilt, not reused
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    (t / 'data/world-key').mkdir(parents=True)
    (t / 'data/world-key/AE.json').write_text('{}')
    import hashlib
    sha = hashlib.sha256((t / 'data/world-key/AE.json').read_bytes()).hexdigest()
    rows_ae = {'AE': {'area_hash': 'old', 'area_parts': op, 'out_sha': sha, 'rules': 'oldc', 'complete': True}}
    np_over = dict(np_fmt, **{'data:data/overrides/world/AE-0001.json': 'new000000000XXXX'})
    final, table, added, reused = AH.decide('world', ['AE'], {'AE': 'newhash'}, {'AE': np_over}, rows_ae, 'newc', 'reuse', False, t)
    check(f'first override AE is rebuilt, not reused (final={final}, reused={reused}, table={table})',
          final == ['AE'] and reused == [] and table and table[0][4] == 'rebuild')

# a rules-version bump is rebuilt (or requires proof_valid); it is not a plain restamp
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    (t / 'data/world-key').mkdir(parents=True)
    (t / 'data/world-key/DE.json').write_text('{}')
    import hashlib
    sha = hashlib.sha256((t / 'data/world-key/DE.json').read_bytes()).hexdigest()
    rows_v = {'DE': {'area_hash': 'old', 'area_parts': op_ver, 'out_sha': sha, 'rules': 'oldc', 'complete': True}}
    final, table, added, reused = AH.decide('world', ['DE'], {'DE': 'newhash'}, {'DE': np_ver}, rows_v, 'newc', 'reuse', False, t)
    check(f'rules-version bump DE is rebuilt, not restamped (final={final}, reused={reused}, table={table})',
          final == ['DE'] and reused == [])

# freeze undeclared -> VERIFY
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    env = t / 'env'; env.write_text('')
    (t / 'data/us-key').mkdir(parents=True)
    json.dump({'build': 'US-1', 'rules': 'old', 'states': {'TN': {'rules': 'old'}, 'OH': {'rules': 'old'}}}, open(t / 'data/us-key/index.json', 'w'))
    old = (KF.ROOT, KF.load_index, KF.gh_json, os.environ.get('GITHUB_ENV'))
    KF.ROOT = t
    KF.load_index = lambda k, cwd=None: json.loads((t / 'data/us-key/index.json').read_text())
    KF.gh_json = lambda *a, **k: {}
    os.environ['GITHUB_ENV'] = str(env)
    os.environ['FORCE'] = 'yes'
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            KF.check('us-key')
    finally:
        KF.ROOT, KF.load_index, KF.gh_json = old[0], old[1], old[2]
        if old[3] is None: os.environ.pop('GITHUB_ENV', None)
        else: os.environ['GITHUB_ENV'] = old[3]
        os.environ.pop('FORCE', None)
    e = env.read_text()
    check('undeclared change (all rows stale) sets RULES_VERIFY=1, not a silent whole-key full rebuild',
          'RULES_CHANGED=1' in e and 'RULES_VERIFY=1' in e and 'US-OH' in e and 'US-TN' in e)

# key_order: every row current, no top-level stamp
st = {'build': 'US-9', 'rules': '', 'states': {'TN': {'rules': 'CUR'}, 'OH': {'rules': 'CUR'}}}
# monkeypatch
real_idx, real_hash = KO._index, KF.rules_hash
KO._index = lambda kind, root='.': st if kind == 'us-key' else {}
# on_current imports KF.rules_hash - patch on the module it uses
import kpc_key_order as KO2
# We'll just call the logic by patching
class F:
    ROWS = KF.ROWS
    @staticmethod
    def rules_hash(kind, root='.'):
        return 'CUR'
# Temporarily
import kpc_key_freeze as KFmod
_rh = KFmod.rules_hash
KFmod.rules_hash = lambda kind, root='.': 'CUR' if True else _rh(kind, root)
try:
    # _index still needs to return st
    _ix = KO._index
    KO._index = lambda kind, root='.': st
    good, why = KO.on_current('us-key', '.')
    check(f'on_current is true when every area row is on the current hash ({why})', good)
finally:
    KFmod.rules_hash = _rh
    KO._index = _ix

us = (ROOT / '.github/workflows/kpc-us-key.yml').read_text()
ca = (ROOT / '.github/workflows/kpc-ca-key.yml').read_text()
wo = (ROOT / '.github/workflows/kpc-world-key.yml').read_text()
check('US and CA default AREA_MODE is reuse', "vars.KPC_AREA_HASH || 'reuse'" in us and "vars.KPC_AREA_HASH || 'reuse'" in ca)
check("US plan prints full=1 only for the monthly run or owner full_rebuild", "print('full=' + ('1' if _monthly else '0'))" in us)
check('CA stamp does not set KPC_FULL_BUILD=1 on every green run', 'Canada always builds the whole key: it is FULL unless' not in ca)
check('CA stamp exports KPC_PLANNED_AREAS (the built provinces) before stamp ca-key',
      'export KPC_PLANNED_AREAS=' in ca and 'stamp ca-key' in ca
      and ca.index('export KPC_PLANNED_AREAS=') < ca.index('stamp ca-key')
      and 'A green run still writes per-province rules' not in ca)
check('world tonight mentions verify, not a forced full rebuild, when RULES_VERIFY=1', 'RULES_VERIFY' in wo and 'not a full rebuild' in wo)
check('US, CA and world plan jobs honour REBUILD_LEVEL',
      all('REBUILD_LEVEL' in wf and 'kpc_rebuild_level.py' in wf for wf in (us, ca, wo)))

# Quality #179 M3: a green non-monthly CA stamp with KPC_PLANNED_AREAS writes rules on every province row
CA_CUR = KF.rules_hash('ca-key')
PROVS = 'AB BC MB NB NL NS NT NU ON PE QC SI SK SP YT'.split()

def stamp_ca(tmp, idx, env):
    cwd = os.getcwd(); os.chdir(tmp); old = dict(os.environ)
    try:
        os.makedirs('data/ca-key', exist_ok=True)
        json.dump(idx, open('data/ca-key/index.json', 'w'))
        for k in ('KPC_BUILD_FAILED_FILE', 'KPC_FULL_BUILD', 'KPC_PLANNED_AREAS', 'GITHUB_WORKFLOW_REF'):
            os.environ.pop(k, None)
        os.environ.update(env); os.environ['GITHUB_RUN_ID'] = '4242'
        with contextlib.redirect_stdout(io.StringIO()):
            KF.stamp('ca-key')
        return json.load(open('data/ca-key/index.json'))
    finally:
        os.chdir(cwd); os.environ.clear(); os.environ.update(old)

with tempfile.TemporaryDirectory() as t:
    rows = {c: {'parks': 1} for c in PROVS}
    d = stamp_ca(t, {'rules': 'f' * 12, 'provinces': rows},
                 {'KPC_PLANNED_AREAS': ' '.join(PROVS), 'KPC_FULL_BUILD': '0'})
    stamped = [c for c, r in (d.get('provinces') or {}).items() if r.get('rules') == CA_CUR]
    check(f'green non-monthly CA stamp writes rules on every province row ({len(stamped)}/{len(PROVS)})',
          len(stamped) == len(PROVS) and set(stamped) == set(PROVS))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
