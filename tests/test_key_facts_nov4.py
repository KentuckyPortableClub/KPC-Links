#!/usr/bin/env python3
"""Offline test for links-10 (per Brandon via Super Head Bot (relayed), 7:13 AM CST Nov 4, answering 'Save pin distance and land
type in the keys during this rebuild?': "Yes, add distance and kind to the keys in this rebuild"): .github/scripts/kpc_key_facts.py,
its calls in the US / CA / world builders, its place in kpc_key_freeze RULE_FILES, and the DE WFS record-id fix (per Super Head
Bot's 7:20 AM CST Nov 4 relay: 670 of 677 DE review-pile rows shared 'joined row with no record id'). No network."""
import ast, importlib.util, json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S))
import kpc_key_facts as KF  # noqa: E402
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def mod(name):
    spec = importlib.util.spec_from_file_location(name, S / f'{name}.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


# 1. kind tags are the precheck's own (one rule, two copies: a change to one must change the other)
pc = (S / 'kpc_precheck.py').read_text(encoding='utf-8')
def lit(src, name):
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and any(getattr(t, 'id', '') == name for t in n.targets): return ast.literal_eval(n.value)
check(lit(pc, 'TAGS') == [tuple(x) for x in KF.TAGS] or lit(pc, 'TAGS') == KF.TAGS, 'TAGS are the same as kpc_precheck.TAGS')
check(lit(pc, 'SAME_PLACE') == KF.SAME_PLACE, 'SAME_PLACE is the same as kpc_precheck.SAME_PLACE')
check(KF.kind_ok('State Park', 'Big Bone Lick SP') == mod('kpc_precheck').kind_ok('State Park', 'Big Bone Lick SP') if hasattr(mod('kpc_precheck'), 'kind_ok') else True,
      'kind_ok agrees with the precheck on a state park')

# 2. distance: inside 0.0, outside about right and rounded to 0.01 km, none without rings
SQ = [[[-85.0, 38.0], [-84.9, 38.0], [-84.9, 38.1], [-85.0, 38.1], [-85.0, 38.0]]]
check(KF.km_to(38.05, -84.95, SQ) == 0.0, 'a pin inside the record is 0.0 km')
k = KF.km_to(38.05, -84.4, SQ)
check(k is not None and 43 < k < 45 and round(k, 2) == k, f'a pin 0.5 deg east is about 44 km, rounded to 0.01 ({k})')
check(KF.km_to(38.05, -84.95, None) is None and KF.km_to(38.05, -84.95, []) is None, 'no rings -> no distance')

# 3. bad pins: blank km with a reason, the pin itself is never changed
LOOK = lambda x: (SQ, 'State Park')  # noqa: E731
for pin, why in (((0, 0), 'pin00'), ((95.0, -84.9), 'pinbad'), (None, 'nopin'), ((None, -84.9), 'nopin')):
    p = {'m': [[1, 'Test SP', 'PAD-US', 'name']]}; before = json.dumps(pin)
    f = KF.fact(p, pin, LOOK, {})
    check(f[1] is None and f[4] == why and json.dumps(pin) == before, f'pin {pin}: blank km, reason {why}, pin unchanged')
check(KF.fact({}, (38.05, -84.95), LOOK, {}) == [None, None, '', '-', 'nocand'], 'no candidate at all -> nocand')
check(KF.fact({'m': [['trl123', 'Some Trail', 'trails', 'name']]}, (38.05, -84.95), LOOK, {})[4] == 'noshape', 'a trail line has no area -> noshape')
check(KF.fact({'c': [[7, 'Near SP', 'PAD-US', 'similar']]}, (38.05, -84.95), lambda x: (None, ''), {})[:2] == [7, None], 'a dropped park names its best candidate even with no outline')

# 4. kind: designation field first ('des'), else the precheck name tags ('nm'), else '-'
leg = {}
check(KF.kind_of('Big Bone Lick', 'State Park', leg) == ('SP', 'des'), 'designation State Park -> SP, des')
check(KF.kind_of('Big Bone Lick', 'SP', {}) == ('SP', 'des'), 'a short code stays itself')
check(KF.kind_of('Wolf Creek National Wildlife Refuge', '', leg) == ('refuge', 'nm'), 'no designation -> the precheck name tags (nm)')
check(KF.kind_of('Cassop Vale', '', leg) == ('', '-'), 'no designation and no kind word -> blank, src -')
c1 = KF.code('Provincial Park', leg); c2 = KF.code('Protected Park', leg)
check(c1 != c2 and leg[c1] == 'Provincial Park' and leg[c2] == 'Protected Park', f'colliding codes get a suffix ({c1}, {c2})')
check(len(KF.code('Wilderness Study Area', {})) <= 6, 'codes are short')

# 5. joined parks: the nearest joined piece wins
FAR = [[[-80.0, 30.0], [-79.9, 30.0], [-79.9, 30.1], [-80.0, 30.1], [-80.0, 30.0]]]
p = {'m': [[1, 'A', 's', 'x'], [2, 'B', 's', 'x']]}
f = KF.fact(p, (38.05, -84.95), lambda x: ((FAR if x[0] == 1 else SQ), ''), {})
check(f[0] == 2 and f[1] == 0.0, 'the joined piece holding the pin is the one recorded')
parks = {'X-1': {'m': [[1, 'Test State Park', 's', 'x']]}, 'X-2': {}}
legd, n = KF.stamp(parks, lambda r: (38.05, -84.95), lambda x: (SQ, 'State Park'))
check(n == {'parks': 2, 'km': 1, 'kind': 1} and parks['X-1']['bk'] == [1, 0.0, 'SP', 'des'], f'stamp writes bk on every park ({n})')
bad = {'X-1': {'m': [[1, 'A', 's', 'x']]}}
KF.stamp(bad, lambda r: (38.05, -84.95), lambda x: 1 / 0)
check(bad['X-1']['bk'][4] == 'noshape', 'one park failing never stops the stamp')

# 6. the builders call it before they save, and the DE WFS id fix
us = (S / 'kpc_us_key.py').read_text(encoding='utf-8'); ca = (S / 'kpc_ca_key.py').read_text(encoding='utf-8'); wd = (S / 'kpc_world_key.py').read_text(encoding='utf-8')
check('KF.stamp(' in us and us.rindex('_selfchk(st, parks, recs)') < us.index('KF.stamp(') < us.rindex("save_json(OUT / f'US-{st}.json'"), 'US builder runs its self check, then stamps bk, then saves (fix bundle 11a order)')
check("'bk_about': KF.ABOUT" in us and 'Des_Tp' in us[us.index('def _bklook'):us.index('def _bklook') + 400], 'US kind comes from PAD-US Des_Tp')
check('KF.stamp(' in ca and ca.index('KF.stamp(') < ca.rindex('for _pv, _o, _rp, _rt in PENDING'), 'CA builder stamps before its save loop')
check("r.get('src')" in ca[ca.index('def _bklook'):ca.index('def _bklook') + 500], "CA: designation only for CPCAD rows (no 'src'; others carry a label)")
check('KF.stamp(' in wd and wd.index('KF.stamp(') < wd.index("save_json(OUT / f'{cc}.json'"), 'world builder stamps before the per-country save')
src = wd[wd.index('WFS_IDF'):wd.index('def pull_wfs')]
ns = {}; exec(src, ns)
wfs_id = ns['wfs_id']
check(wfs_id({'id': 'Naturparke.1'}, {'ID': 'nrp_2106'}) == 'Naturparke.1', 'a feature id the layer gives is kept')
check(wfs_id({}, {'ID': 'nrp_2106', 'OBJECTID': 5}) == 'nrp_2106', "BfN: no top-level id -> the layer's own 'ID' field")
check(wfs_id({}, {'SITECODE': 'DE2520332'}) == 'DE2520332', 'else SITECODE (Natura 2000)')
check(wfs_id({}, {'NAME': 'Harz'}) is None and wfs_id({}, {}) is None, 'no id field -> None (an id is never made up)')
check("'id': wfs_id(f, p)" in wd and "'id': f.get('id')" not in wd, 'pull_wfs uses wfs_id')
check("r['id'] = wfs_id({}, r['_a'])" in wd, 'a saved copy from before the fix gets the same field on load')

# 7. rules: kpc_key_facts is a rule file of all three keys, so the hash moves once (one full rebuild, links-04 logic)
FR = mod('kpc_key_freeze')
check(all('.github/scripts/kpc_key_facts.py' in FR.RULE_FILES[k] for k in ('us-key', 'ca-key', 'world-key')), 'RULE_FILES lists kpc_key_facts.py for us, ca and world')
check('kpc_key_facts.py' not in FR.NOT_RULES, 'kpc_key_facts.py is not in NOT_RULES')
h = {k: FR.rules_hash(k, HERE) for k in ('us-key', 'ca-key', 'world-key')}
check(all(re.fullmatch(r'[0-9a-f]{12}', v) for v in h.values()), f'rules hashes {h}')
base = next((r for r in ('origin/main', 'main') if subprocess.run(['git', 'rev-parse', '-q', '--verify', r], cwd=HERE, capture_output=True).returncode == 0), None)
check(bool(KF.ABOUT) and 'km' in KF.ABOUT, 'bk_about explains the fields')
sys.exit(0 if ok else 1)
