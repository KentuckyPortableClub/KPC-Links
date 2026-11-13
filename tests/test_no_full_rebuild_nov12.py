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

# format-only reuse: row parts are already short (12 chars), as stamp-rows stores them; decide() shortens the new parts only
op = {'data:pins': 'aaa000000000', 'version': 'ah2000000000', 'code:kpc_us_key.py': '111000000000'}
np = {'data:pins': 'aaa000000000XXXX', 'version': 'ah3000000000YYYY', 'code:kpc_us_key.py': '111000000000ZZZZ', 'data:trails': 'new0000000000'}
check('real_inputs_moved is false for a version bump and a newly recorded part', not AH.real_inputs_moved(op, AH.short(np)))
check('a previously recorded pin change IS a real input change', AH.real_inputs_moved(op, dict(AH.short(np), **{'data:pins': 'bbb000000000'})))

rows = {'DE': {'area_hash': 'old', 'area_parts': op, 'out_sha': 'x', 'rules': 'oldc', 'complete': True}}
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    (t / 'data/world-key').mkdir(parents=True)
    (t / 'data/world-key/DE.json').write_text('{}')
    import hashlib
    sha = hashlib.sha256((t / 'data/world-key/DE.json').read_bytes()).hexdigest()
    rows['DE']['out_sha'] = sha
    hashes = {'DE': 'newhash'}
    parts = {'DE': np}
    final, table, added, reused = AH.decide('world', ['DE'], hashes, parts, rows, 'newc', 'reuse', False, t)
    check(f'format-only DE is reused, not rebuilt (final={final}, reused={reused}, table={table})',
          final == [] and reused == ['DE'] and 'format or composition' in table[0][3])

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
check('world tonight mentions verify, not a forced full rebuild, when RULES_VERIFY=1', 'RULES_VERIFY' in wo and 'not a full rebuild' in wo)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
