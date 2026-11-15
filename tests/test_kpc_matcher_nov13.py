#!/usr/bin/env python3
"""Offline tests for the shared park-to-outline matcher (KPC owner, 2026-11-13): .github/scripts/kpc_matcher.py.
Stage 1: the module is added alongside; no key or bot uses it yet, so no rules hash may move (checked below).
Runs the 'matcher_cases' of tests/match_cases.json (the survey's seven failure cases, the eight gaps, the owner's New Hampshire
cases US-2678 / US-2679, the key-record-ids-first order) plus checks of the small pure functions. No network: the socket module is
blocked before the matcher is imported, and the import must create no file."""
import ast, json, os, pathlib, shutil, socket, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = HERE / '.github' / 'scripts'
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


# ------------------------------------------------------------------ no network, no side effects on import
def _blocked(*a, **k): raise OSError('network blocked by test_kpc_matcher_nov13')
socket.socket.connect = _blocked; socket.create_connection = _blocked; socket.getaddrinfo = _blocked
before = sorted(p.name for p in SCRIPTS.iterdir())
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True
import kpc_matcher as M  # noqa: E402
check(sorted(p.name for p in SCRIPTS.iterdir()) == before, 'importing kpc_matcher creates no file')
src = (SCRIPTS / 'kpc_matcher.py').read_text(encoding='utf-8')
mods = {n.names[0].name.split('.')[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import)} | \
       {n.module.split('.')[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ImportFrom) and n.module}
check(mods <= {'math', 're', 'unicodedata'}, f'standard library only (imports: {sorted(mods)})')
check(not any(w in src for w in ('urllib', 'requests', 'open(', 'os.environ', 'subprocess')), 'no network, file or environment use in the module')
top = [n for n in ast.parse(src).body if not isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.Assign, ast.Expr, ast.AnnAssign))]
check(not top, 'module top level holds only imports, constants and functions (nothing runs on import)')
check(os.path.getsize(SCRIPTS / 'kpc_matcher.py') < 1_000_000, 'module under the 1 MB per-file cap')


# ------------------------------------------------------------------ the golden matcher cases
def sq(cx, cy, h): return [[[cx - h, cy - h], [cx + h, cy - h], [cx + h, cy + h], [cx - h, cy + h], [cx - h, cy - h]]]
def bx(b): return [[[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]], [b[0], b[1]]]]


CASES = json.loads((HERE / 'tests' / 'match_cases.json').read_text(encoding='utf-8'))
mc = CASES.get('matcher_cases') or []
check(len(mc) >= 40, f'{len(mc)} matcher cases in tests/match_cases.json')
for c in mc:
    cands = []
    for x in c['candidates']:
        y = {k: v for k, v in x.items() if k not in ('sq', 'box')}
        if 'sq' in x: y['rings'] = sq(*x['sq'])
        if 'box' in x: y['rings'] = bx(x['box'])
        cands.append(y)
    park = dict(c['park']); park0 = json.dumps(park, sort_keys=True)
    layer = c.get('layer') or {'source': 'test'}
    r = M.decide_with_key(park, c['key'], cands, layer, c.get('other_parks')) if c.get('key') else M.decide(park, cands, layer, c.get('other_parks'))
    e = c['expect']; bad = []
    if r['outcome'] != e['outcome']: bad.append(f"outcome {r['outcome']}")
    if 'likely' in e and r['likely'] != e['likely']: bad.append(f"likely {r['likely']}")
    if 'records' in e and sorted(map(str, r['records'])) != sorted(map(str, e['records'])): bad.append(f"records {r['records']}")
    if any(str(i) in map(str, r['records']) for i in e.get('not_records', [])): bad.append(f"took {e['not_records']}")
    if 'maybe' in e and not set(map(str, e['maybe'])) <= set(map(str, r['maybe'])): bad.append(f"maybe {r['maybe']}")
    if any(f not in r['flags'] for f in e.get('flags', [])): bad.append(f"flags {r['flags']}")
    if 'far_same_name' in e and sorted(sorted(map(str, x['ids'])) for x in r['far_same_name']) != sorted(sorted(map(str, x)) for x in e['far_same_name']): bad.append(f"far {r['far_same_name']}")
    if 'far_belongs_to' in e and not any(x.get('belongs_to') == e['far_belongs_to'] for x in r['far_same_name']): bad.append('belongs_to')
    if 'path' in e and r.get('path') != e['path']: bad.append(f"path {r.get('path')}")
    if 'auto_confirmed' in e and r['auto_confirmed'] != e['auto_confirmed']: bad.append(f"auto {r['auto_confirmed']}")
    if 'pin' in e and r['pin'] != e['pin']: bad.append(f"pin {r['pin']}")
    if 'private' in e and r.get('private') != e['private']: bad.append(f"private {r.get('private')}")
    if any(r['checks'].get(k) != v for k, v in (e.get('checks') or {}).items()): bad.append(f"checks {r['checks']}")
    if not (isinstance(r['reason'], str) and len(r['reason']) > 10): bad.append('no plain reason')
    if r['outcome'] == M.UNCLEAR and r['likely'] not in ('yes', 'no'): bad.append('UNCLEAR without likely')
    if json.dumps(park, sort_keys=True) != park0: bad.append('the park (pin) was changed')
    check(not bad, f"{c['id']}: {r['outcome']}{'/' + str(r['likely']) if r['likely'] else ''} {'; '.join(bad)} | {r['reason'][:110]}")

# ------------------------------------------------------------------ the 53 old golden name cases, through the new matcher
# The old cases still test kpc_us_key.join_how (tests/run_match_tests.py, unchanged). Here: which answers would CHANGE under the
# new matcher; the list must be exactly the one recorded in match_cases.json 'matcher_us_names_changes'.
changed = []
for c in CASES['us_names']:
    r = M.decide({'name': c['a'], 'type': '', 'lat': 38.0, 'lon': -85.0}, [{'id': 1, 'name': c['b'], 'name2': c.get('loc'), 'rings': sq(-85.0, 38.0, 0.02)}],
                 {'source': 'test', 'padus': True})
    if (r['outcome'] == M.MATCH) != c['same']: changed.append((c['a'], c['b']))
want = [(x['a'], x['b']) for x in CASES.get('matcher_us_names_changes') or []]
check(changed == want, f'old US golden name cases whose answer changes under the new matcher: {changed} (recorded: {want})')
p = subprocess.run([sys.executable, '-B', str(HERE / 'tests' / 'run_match_tests.py')], capture_output=True, text=True, cwd=HERE,
                   env={k: v for k, v in os.environ.items() if 'proxy' not in k.lower()})
check(p.returncode == 0 and '53 of 53 golden cases right' in p.stdout, 'the existing 53 golden cases still pass unchanged (run_match_tests.py)')

# ------------------------------------------------------------------ small pure functions
check(M.kinds_of('Cedar SP')[0] == {'sp'} and M.kinds_of('Cedar NP')[0] == {'nps'} and M.kinds_of('Cedar NF')[0] == {'nf'}, 'gap 1: SP / NP / NF short forms are kinds')
check(M.kinds_of('Cedar WA')[0] == {'wma'} and M.kinds_of('Cedar Wildlife Area')[0] == {'wma'} and M.kinds_of('Cedar SRA')[0] == {'sp'}, 'gap 1: WA / Wildlife Area / SRA are kinds')
check(M.kinds_of('Cedar Refuge')[0] == {'nwr'} and M.kinds_of('Refuge Cove')[0] == set(), "gap 1: 'Refuge' is a kind, but not as the first word (golden Refuge Cove)")
check(M.kinds_of('Cedar') == (set(), False) and M.kinds_of('Lake Z National') == (set(), True), 'bare name: no kind; a leftover kind-ish word: unknown kind')
check(M.kinds_agree({'sp'}, {'sp'}) == 'agree' and M.kinds_agree({'sp'}, {'sf'}) == 'clash' and M.kinds_agree({'sp'}, set()) == 'unknown'
      and M.kinds_agree(set(), set()) == 'unknown' and M.kinds_agree({'wild'}, {'wsa'}) == 'agree', 'kinds_agree: agree only when both sides state a kind (US_COMPAT pairs kept)')
check(M.name_relation('Big Woods Beach State Park', 'Big Woods State Park') == 'park_longer' and
      M.name_relation('Big Woods State Park', 'Big Woods Beach State Park') == 'record_longer', 'name_relation sees the bigger / smaller place (gap 4)')
check(M.name_relation('World War I Memorial', 'World War II Memorial') is None and M.name_relation('Pishkun Reservoir WMA', 'Pishkin Reservoir WMA') == 'exact',
      'World War I stays apart from II; a one-letter typo in a long word is the same name')
check(M.name_relation('Yates Lake WMA', 'Yates Lake West WMA') == 'side_differs', 'side words: side_differs, never exact')
check(M.norm('Cedar SP') == M.norm('Cedar State Park') == 'cedar', 'norm() reads SP as the generic State Park words')
check(abs(M.pin_tolerance_km(40) - 0.25) < 1e-9 and abs(M.pin_tolerance_km(1000) - 0.5 * M.size_km(1000)) < 1e-9 and M.pin_tolerance_km(1e8) == 15.0,
      'pin tolerance: max(0.25 km, half the width), never over 15 km (kpc_match / kpc_join_check numbers)')
check(M.pin_class(0, 100) == 'inside' and M.pin_class(0.2, 40) == 'edge' and M.pin_class(0.5, 40) == 'near' and M.pin_class(2, 40) == 'far' and M.pin_class(30, 40) == 'very_far'
      and M.pin_class(None, 40) == 'unknown', 'pin_class bands')
check(M.ACRE_TOL == 0.15 and M.ACRE_RATIO == (0.5, 2.0) and M.NEST_SHARE == 0.9 and M.JOIN_AT == 4 and M.MARGIN == 2, 'thresholds are the repo\'s existing ones')
a = M.acres_of(sq(-85, 38, 0.02))
check(3500 < a < 4200, f'acres_of a 0.04 degree square at 38N: {a:,.0f} acres')
check(M.nested_share(sq(-85, 38, 0.01), sq(-85, 38, 0.1)) == 1.0 and M.nested_share(sq(-85, 38, 0.1), sq(-85, 38, 0.01)) < 0.5, 'nested_share (90% rule input)')
check(M.park_wdpa_id({'web': 'https://www.protectedplanet.net/en/sites/12345'}) == 12345 and M.park_wdpa_id({'wdpa_id': '77'}) == 77
      and M.park_wdpa_id({'web': 'https://parks.ky.gov'}) is None, 'park_wdpa_id: from the field or a Protected Planet address')
check(M.rec_wdpa_ids({'id': 5, 'WDPAID': 9, 'attrs': {'WDPA_PID': '10_A'}}) == {9, 10} and M.rec_wdpa_ids({'id': 5, 'name': 'x'}) == set(),
      "rec_wdpa_ids: the record's own WDPAID / WDPA_PID fields, never its record id")
check(M.agency_from_web('https://www.nps.gov/x') == 'NPS' and M.agency_from_web('https://parks.ky.gov/x') is None, 'agency from an official page host: federal hosts only')
check(M.agencies_agree('NPS', 'FED') is True and M.agencies_agree('NPS', 'STAT') is False and M.agencies_agree(None, 'FED') is None, 'agencies_agree levels')
check(M.review_state(['1'], {'outcome': 'UNCLEAR', 'records': []}) == 'KEEP-FLAGGED' and M.review_state(['1'], {'outcome': 'NO', 'records': []}) == 'KEEP-FLAGGED'
      and M.review_state(['1'], {'outcome': 'MATCH', 'records': [1]}) == 'UNCHANGED' and M.review_state(['1'], {'outcome': 'MATCH', 'records': [2]}) == 'DIFFERENT-RECORD'
      and M.review_state([], {'outcome': 'MATCH', 'records': [2]}) == 'NEW-MATCH' and M.review_state([], {'outcome': 'MATCH', 'records': [2], 'auto_confirmed': True}) == 'AUTO-CONFIRMED',
      'review_state: a doubtful existing join is KEEP-FLAGGED, never removed')
r = M.decide({'name': 'Cedar State Park', 'type': 'State Park', 'lat': 38, 'lon': -85}, [], {})
check(r['outcome'] == M.NO and r['records'] == [], 'no candidates: NO')
check(M.to_rings({'type': 'MultiPolygon', 'coordinates': [sq(0, 0, 1), sq(5, 5, 1)]}) == sq(0, 0, 1) + sq(5, 5, 1) and M.to_rings({'rings': sq(0, 0, 1)}) == sq(0, 0, 1),
      'to_rings reads GeoJSON and ArcGIS geometries')

# ------------------------------------------------------------------ stage boundary: nothing uses it, no rules hash moves
import kpc_key_freeze as KF  # noqa: E402
check(not any('kpc_matcher' in f for v in KF.RULE_FILES.values() for f in v), 'kpc_matcher.py is in no RULE_FILES list')
check('kpc_matcher.py' in KF.NOT_RULES, 'kpc_matcher.py is listed in NOT_RULES (stage 1: it decides no join yet)')
users = subprocess.run(['git', 'grep', '-l', 'kpc_matcher', '--', '.github', '*.py', '*.yml', '*.js'], cwd=HERE, capture_output=True, text=True).stdout.split()
check(set(users) <= {'.github/scripts/kpc_matcher.py', '.github/scripts/kpc_key_freeze.py', 'tests/test_kpc_matcher_nov13.py'} or not users,
      f'no bot, key or workflow imports kpc_matcher (files naming it: {users})')
base = next((b for b in ('origin/main', 'main') if subprocess.run(['git', 'rev-parse', '-q', '--verify', b], cwd=HERE, capture_output=True).returncode == 0), None)
if base:
    with tempfile.TemporaryDirectory() as t:
        allf = {f for v in KF.RULE_FILES.values() for f in v} | {KF.VERSION_FILE}
        for f in allf:
            g = subprocess.run(['git', 'show', f'{base}:{f}'], cwd=HERE, capture_output=True)
            if g.returncode == 0:
                (pathlib.Path(t) / f).parent.mkdir(parents=True, exist_ok=True); (pathlib.Path(t) / f).write_bytes(g.stdout)
        for k in KF.RULE_FILES:
            check(KF.rules_hash(k) == KF.rules_hash(k, root=t), f'{k} rules hash unchanged against {base} ({KF.rules_hash(k)})')
else:
    print('SKIP-NOTE no main ref in this clone: rules hash comparison not run')
sys.path.insert(0, str(SCRIPTS))
import kpc_rebuild_level as RL  # noqa: E402
lv, why = RL.auto_level(['.github/scripts/kpc_matcher.py', 'tests/test_kpc_matcher_nov13.py', 'tests/match_cases.json', '.github/scripts/kpc_key_freeze.py'])
check(lv == 1, f'rebuild level of this change: {lv} ({why})')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
