#!/usr/bin/env python3
"""Nov 12 (KPC owner, 2026-11-12): .github/scripts/kpc_area_hash.py (handoff part B; the Nov 11 prototype tools/kpc_area_hash.py moved
there and wired into the key plans in SHADOW mode). Part 1 is the prototype's own test (paths updated); part 2 the new plan / reuse /
proof-stamp / stamp-rows / sanity cases (handoff tests 6 and 7). Offline: a throwaway git repo in
/tmp holds a tiny copy of the rule files and data files; the real checkout is only read (its four rules hashes are compared with
kpc_key_freeze.py's own answer and checked again after the tool ran, and git status must not change)."""
import gzip, json, os, pathlib, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_area_hash as K  # noqa: E402

ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)


def run(*a, cwd=None):
    return subprocess.run(list(a), cwd=cwd, capture_output=True, text=True)


def sh(cwd, *a):
    r = run('git', '-c', 'user.name=t', '-c', 'user.email=t@t', *a, cwd=cwd)
    if r.returncode: raise SystemExit(f'git {a}: {r.stderr}')
    return r.stdout.strip()


# ---------------------------------------------------------------- the real checkout: hashes agree with kpc_key_freeze, nothing moves
REAL = {k: run(sys.executable, '-B', str(ROOT / K.FREEZE), 'rules', k, cwd=ROOT).stdout.strip() for k in ('us-key', 'ca-key', 'world-key', 'fers')}
status0 = run('git', 'status', '--porcelain', '--untracked-files=all', cwd=ROOT).stdout
t = K.Tree(ROOT)
check('the tool\'s region hashes = kpc_key_freeze.py rules (all four kinds, this checkout)', all(K.region_hash(t, k) == v for k, v in REAL.items()))
for kind in ('us', 'ca', 'world', 'fers'):
    hs, _ = K.compute(ROOT, None, kind)
    check(f'{kind}: a table of {len(hs)} areas, 12 hex each, the same twice', hs and all(len(h) == 12 for h in hs.values()) and hs == K.compute(ROOT, None, kind)[0])
check('the rules hashes did not move after the tool ran', REAL == {k: run(sys.executable, '-B', str(ROOT / K.FREEZE), 'rules', k, cwd=ROOT).stdout.strip() for k in REAL})
check('git status of the checkout is unchanged (no rule file touched, no __pycache__)', run('git', 'status', '--porcelain', '--untracked-files=all', cwd=ROOT).stdout == status0)

# ---------------------------------------------------------------- a throwaway repo
td = pathlib.Path(tempfile.mkdtemp(prefix='kpc-area-hash-test-'))
try:
    R = td / 'repo'
    (R / '.github/scripts').mkdir(parents=True)
    shutil.copy(ROOT / K.FREEZE, R / K.FREEZE)   # the real freeze file: its RULE_FILES / SCOPE_FILES / rules_hash
    def w(rel, text):
        p = R / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text if isinstance(text, bytes) else (text if isinstance(text, str) else json.dumps(text, indent=1)).encode())
    w('.github/key-rules-version.json', {'us-key': 'v5b', 'ca-key': 'v5b', 'world-key': 'v5b', 'fers': 'v1'})
    US_KEY = '''"""US key (test copy)."""
import re
BOX_ADD = {'FL': (-83.2, 24.3, -80.0, 25.2), 'TN': (-90.0, 35.0, -81.6, 36.7)}
XS = [
    ('wld', 'https://wild.example.gov/MapServer/0/query', 'name', 'acres', {'wild'}, 'national'),
    ('vta', 'https://vt.example.gov/MapServer/1/query', '?', '?', set(), 'Vermont', 'STAT', {'VT'}),
]
def same(a, b):
    # a comment
    return re.sub(r'\\W', '', a.lower()) == re.sub(r'\\W', '', b.lower())
'''
    w('.github/scripts/kpc_us_key.py', US_KEY)
    for f in ('kpc_key_rules.py', 'kpc_match.py', 'kpc_key_facts.py', 'kpc_ca_key.py', 'kpc_ca_fill_bounds.py', 'kpc_ca_hardlook.py',
              'kpc_number_rules.py', 'kpc_fers.py', 'kpc_owned.py', 'kpc_fers_key_status.py', 'kpc_fers_guard.py', 'kpc_fers_count.py',
              'kpc_fers_ready.py', 'kpc_fers_preline.py', 'kpc_fers_far_hold.py', 'kpc_precheck.py'):
        w(f'.github/scripts/{f}', f'X = {f!r}\n')
    w('.github/scripts/kpc_world_key.py', "SRC = {'AU': [('CAPAD', 'arcgis', 'https://au.example.gov/MapServer/0')], 'GB': [('NE', 'arcgis', 'https://gb.example.org/MapServer/2')]}\nY = 1\n")
    w('.github/fers-ready-areas.json', {'areas': {'US-*': {}}})
    for f in ('us-key', 'ca-key', 'world-key'): w(f'.github/{f}-rule-scope.json', {'changes': []})
    w('.github/fers-rule-scope.json', {'changes': []})
    # host rules (kpc_master.live_ok over kpc_net_guard), as the real files do it
    w('.github/scripts/kpc_net_guard.py', "import urllib.parse\ndef host_of(u): return (urllib.parse.urlsplit(u).hostname or '').lower()\ndef host_ok(u): return (True, '')\ndef extra_hosts(): return set()\ndef install(): raise SystemExit('install must never run')\n")
    MASTER = "import kpc_net_guard\nkpc_net_guard.install()\nSAVED_ONLY_HOSTS = {'apps.example.gov'}\ndef live_ok(url):\n    h = kpc_net_guard.host_of(url)\n    if h in SAVED_ONLY_HOSTS: return False, f'{h}: saved copies only, no live read'\n    return kpc_net_guard.host_ok(url)\n"
    w('.github/scripts/kpc_master.py', MASTER)
    def key(st, parks): return {'st': st, 'parks': {r: {'g': 'official', 'm': [[1, 'x', 1, 'name']], 'read': '2026-11-01'} for r in parks}}
    w('data/us-key/US-TN.json', key('TN', ['US-0019', 'US-0034'])); w('data/us-key/US-FL.json', key('FL', ['US-0100']))
    w('data/us-key/US-GA.json', key('GA', ['US-0200'])); w('data/ca-key/CA-ON.json', key('ON', ['CA-0001']))
    w('data/us-key/overrides.json', {'note': 'x', 'blocked_ids': [], 'parks': {'US-0019': {'join': [3197]}, 'US-0100': {'no': [5]}}})
    w('data/state-gis.json', {'states': {'TN': [{'url': 'https://tn.example.gov/FeatureServer/0', 'nm': 'NAME'}], 'FL': [], 'ON': []}, 'portals': {}})
    box = lambda a, x0, y0, x1, y1: {'a': a, 'n': a, 'p': [[[[x0, y0], [x1, y0], [x1, y1], [x0, y1]]]]}
    w('kpc-us-states.json', [box('TN', -90, 35, -81.6, 36.7), box('GA', -85.6, 30.4, -80.8, 35), box('FL', -87.6, 25.1, -80, 31), box('AK', -170, 51, -130, 71)])
    w('locations.json', [['POTA', 'US-0019', 'Cumberland Gap', 36.6, -83.6, 'u'], ['WWFF', 'KFF-1', 'x', 1, 2, 'u']])
    w('data/world-key/AU.json', {'cc': 'AU', 'parks': {'AU-0001': {'g': 'official'}}}); w('data/world-key/GB.json', {'cc': 'GB', 'parks': {'GB-0001': {}}})
    w('data/world-key/extra-layers.json', {'countries': {'AU': [{'url': 'https://au2.example.gov/MapServer/1'}], 'GB': [{'url': 'https://apps2.example.gov/MapServer/3'}]},
                                           'dropped': {'about': 'not read', 'AU': []}})
    w('data/world-key/overrides.json', {'parks': {'AU-0001': {'join': ['x']}}})
    w('data/outlines/US-TN.geojson.gz', gzip.compress(b'{"features": []}'))
    sh(R, 'init', '-q'); sh(R, 'add', '-A'); sh(R, 'commit', '-q', '-m', 'base')
    def commit(msg): sh(R, 'add', '-A'); sh(R, 'commit', '-q', '-m', msg); return sh(R, 'rev-parse', 'HEAD')
    base = sh(R, 'rev-parse', 'HEAD')
    def moved(kind, a, b, level=3, reader='shared', data=None):
        _, pa = K.compute(R, a, kind, level, data, b, reader); _, pb = K.compute(R, b, kind, level, data, a, reader)
        return K.diff_parts(pa, pb)
    check('fixture: the tool\'s region hashes = the real kpc_key_freeze.py rules_hash run on the fixture (all four kinds)',
          all(K.region_hash(K.Tree(R, base), k) == run(sys.executable, '-B', str(R / K.FREEZE), 'rules', k, cwd=R).stdout.strip() for k in ('us-key', 'ca-key', 'world-key', 'fers')))

    # 1. a comment / blank-line / docstring edit: the region hash moves, no area hash does
    w('.github/scripts/kpc_us_key.py', US_KEY.replace('# a comment', '# a longer comment, Nov 11\n\n').replace('(test copy)', '(test copy, reworded)'))
    c1 = commit('comment only')
    check('comment-only edit: today\'s US region hash moves', K.region_hash(K.Tree(R, base), 'us-key') != K.region_hash(K.Tree(R, c1), 'us-key'))
    check('comment-only edit: level 1 (bytes, as today) moves every state', len(moved('us', base, c1, 1)) == 50)
    check('comment-only edit: level 2 / 3 (tokens) move no state', not moved('us', base, c1, 2) and not moved('us', base, c1, 3))

    # 2. one state's entry in a per-area table in the code
    w('.github/scripts/kpc_us_key.py', US_KEY.replace('-80.0, 25.2', '-79.8, 25.2'))
    c2 = commit('FL box')
    d = moved('us', c1, c2)
    # Nov 12 (KPC owner, 2026-11-12; D6 tables out) CHANGED: a per-area table left IN the rule code is shared code now (the tables are data in
    # data/<kind>/area-tables.json; tests/test_area_tables_nov12.py covers their slicing and fails a rule file that keeps one): every area moves
    check('BOX_ADD[FL] edit in the rule code: level 3 moves every state (fail closed)', len(d) == 50 and any(x.startswith('code:') for x in d['FL']))
    check('BOX_ADD[FL] edit: level 2 moves every state (the table is still code there)', len(moved('us', c1, c2, 2)) == 50)
    w('.github/scripts/kpc_us_key.py', US_KEY.replace('-80.0, 25.2', '-79.8, 25.2').replace("'Vermont', 'STAT', {'VT'}", "'Vermont ANR', 'STAT', {'VT'}"))
    c2b = commit('VT XS entry')
    # Nov 12 (KPC owner, 2026-11-12; D6 tables out) CHANGED: a per-area table left IN the rule code is shared code now (the tables are data in
    # data/<kind>/area-tables.json; tests/test_area_tables_nov12.py covers their slicing and fails a rule file that keeps one): every area moves
    check('an XS entry limited to {VT} in the rule code: level 3 moves every state (fail closed)', len(moved('us', c2, c2b)) == 50)

    # 3. data slices: an override row moves its park's state only; key order and spacing move nothing
    ov = json.loads((R / 'data/us-key/overrides.json').read_text()); ov['parks']['US-0019']['join'] = [3198]
    w('data/us-key/overrides.json', ov); c3 = commit('TN override')
    d = moved('us', c2b, c3)
    check('override of US-0019 (a TN park): only TN moves, reason data:overrides', set(d) == {'TN'} and any('overrides' in x for x in d['TN']))
    w('data/us-key/overrides.json', json.dumps(dict(reversed(list(ov.items()))), indent=4, sort_keys=True)); c3b = commit('reordered')
    check('the same overrides, other key order and spacing: nothing moves', not moved('us', c3, c3b))
    ov['parks']['US-9999'] = {'no': [1]}; w('data/us-key/overrides.json', ov); c4 = commit('override of a park in no key')
    check('an override of a park in no key file and no pin file given: every state moves (fail closed)', len(moved('us', c3b, c4)) == 50)
    sgis = json.loads((R / 'data/state-gis.json').read_text()); sgis['states']['ON'] = [{'url': 'https://on.example.ca/x'}]
    w('data/state-gis.json', sgis); c4b = commit('a Canada row in state-gis.json')
    check('a province row in state-gis.json moves no US state (the US key reads only its own states)', not moved('us', c4, c4b))
    w('data/state-gis.json', '{not json'); c5 = commit('broken state-gis')
    d = moved('us', c4b, c5)
    check('an unreadable state-gis.json moves every state, reason names it unreadable', len(d) == 50 and any('unreadable' in x for x in d['TN']))
    w('data/state-gis.json', sgis); c5b = commit('state-gis back')

    # 4. world: the dropped list is not read; one country's extra layers move that country only
    ex = json.loads((R / 'data/world-key/extra-layers.json').read_text()); ex['dropped']['AU'] = [{'url': 'https://dead.example.gov/MapServer/5'}]
    w('data/world-key/extra-layers.json', ex); c6 = commit('dropped list')
    check('world: an edit to extra-layers.json dropped (not read by the builder) moves nothing', not moved('world', c5b, c6))
    ex['countries']['AU'].append({'url': 'https://au3.example.gov/MapServer/9'}); w('data/world-key/extra-layers.json', ex); c7 = commit('AU layer')
    check('world: a new AU layer in extra-layers.json countries moves AU only', set(moved('world', c6, c7)) == {'AU'})
    w('.github/scripts/kpc_world_key.py', (R / '.github/scripts/kpc_world_key.py').read_text().replace("('NE', 'arcgis'", "('Natural England', 'arcgis'"))
    c7b = commit('GB source label')
    # Nov 12 (KPC owner, 2026-11-12; D6 tables out) CHANGED: a per-area table left IN the rule code is shared code now (the tables are data in
    # data/<kind>/area-tables.json; tests/test_area_tables_nov12.py covers their slicing and fails a rule file that keeps one): every area moves
    check('world: one country\'s SRC entry in the rule code moves every country (level 3, fail closed)', len(moved('world', c7, c7b)) == len(K.compute(R, c7b, 'world')[0]))

    # 5. host rules (the soundness hole): a saved-copy-only host added
    w('.github/scripts/kpc_master.py', MASTER.replace("{'apps.example.gov'}", "{'apps.example.gov', 'apps2.example.gov'}"))
    c8 = commit('host rule')
    check('host rule edit: today\'s four region hashes do not move (kpc_master.py is not a rule file)',
          all(K.region_hash(K.Tree(R, c7b), k) == K.region_hash(K.Tree(R, c8), k) for k in ('us-key', 'ca-key', 'world-key', 'fers')))
    check('host rule edit, step-1 composition (reader shared): every country moves', len(moved('world', c7b, c8, reader='shared')) == len(K.compute(R, c8, 'world')[0]))
    d = moved('world', c7b, c8, reader='verdict')
    check('host rule edit, verdict composition: only GB (its layer is on apps2.example.gov) moves, reason hosts', set(d) == {'GB'} and any(x.startswith('hosts') for x in d['GB']))
    w('.github/scripts/kpc_master.py', MASTER.replace("{'apps.example.gov'}", "{'apps.example.gov', 'apps2.example.gov'}").replace("saved copies only, no live read", "saved copy only (reworded)"))
    c8b = commit('host message reworded')
    check('host rule message reworded: verdict composition moves nothing', not moved('world', c8, c8b, reader='verdict'))
    check('the test never ran kpc_net_guard.install() (it would have exited)', True)

    # 6. 2-fers: a key rebuild that only re-dates parks moves nothing; a real join change moves the areas that read that state
    k2 = json.loads((R / 'data/us-key/US-TN.json').read_text())
    for p in k2['parks'].values(): p['read'] = '2026-11-11'
    w('data/us-key/US-TN.json', k2); c9 = commit('re-dated TN key')
    check('fers: a TN key file whose only change is the per-park read date moves no 2-fer area', not moved('fers', c8b, c9))
    k2['parks']['US-0034']['m'] = [[9, 'y', 1, 'name']]; w('data/us-key/US-TN.json', k2); c10 = commit('TN join changed')
    d = moved('fers', c9, c10)
    # Nov 12 CHANGED (part C alignment): the 2-fer unit is the state / province, not the chain area
    check('fers: a TN join change moves the unit US-TN (its own key)', 'US-TN' in d and any(x.startswith('up:key:US-TN') for x in d['US-TN']))
    check('fers: ... every other unit that moved moved only for TN as a neighbour (the fixture boxes only FL and TN, so every '
          'state counts as a neighbour: fail closed); never a Canada province',
          all(any('US-TN' in x for x in d[a]) for a in d) and not any(a.startswith('CA-') for a in d))


    # 7. the CLI: diff table, hashes, migrate
    r = run(sys.executable, '-B', str(ROOT / '.github/scripts/kpc_area_hash.py'), 'diff', 'us', c2b, c3, '--repo', str(R))
    check('diff prints one table: area | old hash | new hash | reason | action, TN rebuild, others reuse',
          'area | old hash | new hash | reason | action' in r.stdout and any(l.startswith('TN |') and l.endswith('| rebuild') for l in r.stdout.splitlines())
          and any(l.startswith('GA |') and l.endswith('| reuse') for l in r.stdout.splitlines()))
    r = run(sys.executable, '-B', str(ROOT / '.github/scripts/kpc_area_hash.py'), 'hashes', '--repo', str(R), '--rev', c10)
    check('hashes prints the four kinds', r.returncode == 0 and len(r.stdout.split('\n')) >= 4 and 'fers' in r.stdout)
    ix = {'states': {s: {'seconds': 10, 'rules': 'x'} for s in ('TN', 'FL', 'GA')}}
    w('data/us-key/index.json', ix); c11 = commit('a US build')
    ix['states']['TN']['seconds'] = 11; w('data/us-key/index.json', ix); c12 = commit('a TN-only build')
    rows = {x[0]: x for x in K.migrate(R, None, 'us', 'shared', window_h=0, quiet=True)}
    check('migrate: a state whose inputs at its last build equal HEAD is stamped (GA)', rows['GA'][3] == 'stamp')
    check('migrate: a state never built in the history is rebuilt (OH)', rows['OH'][3] == 'rebuild')
finally:
    shutil.rmtree(td, ignore_errors=True)

# ---------------------------------------------------------------- the 2-fer area list: both KPC-Data layouts (before and after part C)
with tempfile.TemporaryDirectory() as dd:
    D = pathlib.Path(dd)
    src, g = K.fers_area_groups(None)
    check('fers list, no KPC-Data given: the frozen copy, never a crash', src == 'frozen fallback' and 'southeast' in g)
    (D / '.github/scripts').mkdir(parents=True)
    (D / '.github/scripts/kpc_fers_chain_plan.py').write_text("R = {'southeast': 'US-TN US-GA', 'world': 'W-AU'}\n")
    src, g = K.fers_area_groups(D)
    check('fers list, old layout (chain R only, no fers-areas.json): R is read, world left out', src == 'chain R' and g == {'southeast': ['US-TN', 'US-GA']})
    (D / '.github/fers-areas.json').write_text(json.dumps({'areas': {'southeast': 'US-NC US-FL', 'canadaeast': 'CA-ON'}}))
    src, g = K.fers_area_groups(D)
    check('fers list, new layout (part C: fers-areas.json is the one list): fers-areas.json wins over R', src == 'fers-areas.json' and g['southeast'] == ['US-NC', 'US-FL'])
    check('fers units are the states / provinces of that list', K.fers_areas(D) == {'CA-ON': ['CA-ON'], 'US-FL': ['US-FL'], 'US-NC': ['US-NC']})
    (D / '.github/scripts/kpc_fers_chain_plan.py').unlink()
    check('fers list, R retired and fers-areas.json present: no crash, fers-areas.json', K.fers_area_groups(D)[0] == 'fers-areas.json')
    (D / '.github/fers-areas.json').write_text('{not json')
    check('fers list, both unreadable: the frozen copy, no crash', K.fers_area_groups(D)[0] == 'frozen fallback')

# ================================================================ part 2 (Nov 12): plan, reuse, the D4 proof stamp, stamp-rows, sanity
import datetime, hashlib as _hl
TODAY = datetime.date.today().isoformat()
CUR, OLD = 'c0de00000new', 'c0de00000old'


def mk_area(td, kind='world', areas=('FR', 'DE', 'GB')):
    """A tiny key on disk: one file per area (a deterministic 'build' of its input slice), rows with the recorded hashes."""
    R = pathlib.Path(td) / 'k'; d = R / 'data/world-key'; d.mkdir(parents=True)
    inputs = {a: {'layers': [f'{a}-layer'], 'overrides': {f'{a}-0001': {'no': ['x']}}} for a in areas}
    return R, d, inputs


def fake_build(inputs, a):
    """A deterministic stand-in builder: same inputs, same bytes (what the real builder must also give; not provable offline)."""
    return json.dumps({'parks': {f'{a}-0001': {'m': sorted(inputs[a]['layers'])}}, 'from': inputs[a]}, sort_keys=True, separators=(',', ':')).encode()


def parts_of(inputs, a, code=CUR):
    return {'code:.github/scripts/kpc_world_key.py': _hl.sha256(code.encode()).hexdigest(), 'version': _hl.sha256(b'v').hexdigest(),
            'data:layers': _hl.sha256(json.dumps(inputs[a], sort_keys=True).encode()).hexdigest()}


def hashes_of(P): return K.area_hashes(P)


with tempfile.TemporaryDirectory() as td:
    R, d, inp = mk_area(td)
    P = {a: parts_of(inp, a) for a in inp}; HS = hashes_of(P)
    for a in inp: (d / f'{a}.json').write_bytes(fake_build(inp, a))
    rows = {a: {'rules': CUR, 'area_hash': HS[a], 'area_parts': K.short(P[a]), 'out_sha': K.sha_file(d / f'{a}.json')} for a in inp}
    want = ['DE', 'FR', 'GB']
    f, t, add, reu = K.decide('world', want, HS, P, rows, CUR, 'shadow', False, R)
    check('B1 shadow (the default): the list is unchanged, nothing added or reused; the table says "would reuse"', f == want and not add and not reu
          and all('would reuse' in r[4] for r in t))
    f, t, add, reu = K.decide('world', want, HS, P, rows, CUR, 'reuse', False, R)
    check('B6 reuse on, nothing changed: every area reused (nothing built), reason "inputs and code unchanged"', f == [] and reu == want and all(r[4] == 'reuse' for r in t))
    f, t, add, reu = K.decide('world', want, HS, P, rows, CUR, 'reuse', True, R)
    check('B6 force full rebuild (full_rebuild=yes): reuse off, every area built', f == want and not reu)
    # byte-identical: the reused area's file (main's bytes) == what a full rebuild of the same inputs writes; a 1-area run == an all-area run
    reused_bytes = (d / 'FR.json').read_bytes()
    full = {a: fake_build(inp, a) for a in inp}; one = fake_build(inp, 'FR')
    check('B6 an unchanged area: its reused bytes == a full rebuild\'s bytes == a 1-area run\'s bytes (deterministic stand-in builder)', reused_bytes == full['FR'] == one)
    inp2 = json.loads(json.dumps(inp)); inp2['FR']['layers'].append('FR-new'); P2 = {a: parts_of(inp2, a) for a in inp2}; HS2 = hashes_of(P2)
    f, t, add, reu = K.decide('world', ['DE', 'FR', 'GB'], HS2, P2, rows, CUR, 'reuse', False, R)
    check('B6 one FR layer added: FR rebuilt (reason names data:layers), DE GB reused', f == ['FR'] and reu == ['DE', 'GB'] and 'data:layers' in dict((r[0], r[3]) for r in t)['FR'])
    f, t, add, reu = K.decide('world', ['DE'], HS2, P2, rows, CUR, 'add', False, R)
    check('B-step1 add mode: a nightly list of DE also gets FR (its inputs moved), nothing removed', f == ['DE', 'FR'] and add == ['FR'] and not reu)
    f, t, add, reu = K.decide('world', ['DE'], HS2, P2, rows, CUR, 'shadow', False, R)
    check('B-step1 shadow: FR is only reported ("would add"), the list stays DE', f == ['DE'] and dict((r[0], r[4]) for r in t)['FR'] == 'would add (shadow)')
    f, t, add, reu = K.decide('world', ['DE'], HS, P, {}, CUR, 'add', False, R)
    check('B-step1 no area hash recorded anywhere (the switch-over): add mode adds every area (that is the D7 cost)', sorted(f) == ['DE', 'FR', 'GB'])
    f, t, add, reu = K.decide('world', want, HS, P, {}, CUR, 'reuse', False, R)
    check('reuse, no area hash recorded: every area rebuilt, none reused', sorted(f) == ['DE', 'FR', 'GB'] and not reu
          and all('no area hash recorded' in r[3] for r in t if r[0] in want))
    f, t, add, reu = K.decide('world', want, HS, P, {'DE': rows['DE']}, CUR, 'reuse', False, R)
    check('reuse, only DE has a recorded hash: DE reused, FR and GB rebuilt', reu == ['DE'] and sorted(f) == ['FR', 'GB'])
    (d / 'GB.json').write_bytes(b'hand edit')
    f, t, add, reu = K.decide('world', want, HS, P, rows, CUR, 'reuse', False, R)
    check('B6 a file that is not the recorded bytes (out_sha differs): rebuilt, not reused', 'GB' in f and 'GB' not in reu)
    (d / 'GB.json').write_bytes(fake_build(inp, 'GB'))
    rows2 = dict(rows, DE=dict(rows['DE'], complete=False))
    f, t, add, reu = K.decide('world', want, HS, P, rows2, CUR, 'reuse', False, R)
    check('B6 a row marked partial (complete false): rebuilt', 'DE' in f)

    # 7: a shared-code change rebuilds every area unless a VALID proof stamp covers OLD -> CUR
    Pn = {a: parts_of(inp, a, CUR) for a in inp}; HSn = hashes_of(Pn)
    Po = {a: parts_of(inp, a, OLD) for a in inp}; HSo = hashes_of(Po)
    rows_old = {a: {'rules': OLD, 'area_hash': HSo[a], 'area_parts': K.short(Po[a]), 'out_sha': K.sha_file(d / f'{a}.json')} for a in inp}
    f, t, add, reu = K.decide('world', want, HSn, Pn, rows_old, CUR, 'reuse', False, R)
    check('B7 shared code moved, no proof stamp file: every area rebuilt', f == want and not reu and all('no proof stamp file' in r[3] for r in t))
    def stamp(entry=None, rec=None):
        (R / '.github').mkdir(exist_ok=True); (R / 'data/status/no-result-change').mkdir(parents=True, exist_ok=True)
        e = {'id': 'p1', 'kind': 'world-key', 'from': OLD, 'to': CUR, 'claim': 'no-result-change', 'proof': 'p1', 'approved_by': 'Brandon (KZ4CP)', 'approved_date': TODAY}
        e.update(entry or {})
        r = {'format': 1, 'id': 'p1', 'kind': 'world-key', 'from': OLD, 'to': CUR, 'result': 'pass', 'old_commit': 'a', 'new_commit': 'b', 'sample': ['FR', 'DE'],
             'files': {'data/world-key/FR.json': ['ab' * 32, 'ab' * 32]}, 'network_attempts': 0}
        # Nov 12 D4 (KPC owner, 2026-11-12) CHANGED: the reader also runs the proof job's own record checks (kpc_key_proof.record_problems),
        # so a valid record carries what the job writes: writer, composition, full shas, the whole sample rule, inputs, the fixed clock
        import kpc_key_proof as KP
        o40, n40, uni, tid = 'a' * 40, 'b' * 40, sorted(K.WORLD_DEFAULT), 'cd' * 32
        smp = sorted(set(KP.rule_sample('world', o40, n40, uni)) | {'FR', 'DE'}); inp = {'boundary-cache:W-FR.json.gz': 'ab' * 32}
        r.update({'old_commit': o40, 'new_commit': n40, 'sample': smp, 'files': {f'data/world-key/{a}.json': ['ab' * 32, 'ab' * 32] for a in smp},
                  'writer': KP.WRITER, 'composition': K.COMPOSITION, 'universe': uni, 'inputs': inp, 'inputs_id': KP.inputs_id(inp),
                  'inputs_id_old': KP.inputs_id(dict(inp, tree=tid)), 'inputs_id_new': KP.inputs_id(dict(inp, tree=tid)), 'tree_inputs_old': tid,
                  'tree_inputs_new': tid, 'fixed_instant': '2026-11-12T00:00:00Z'})
        r.update(rec or {})
        (R / '.github/no-result-change.json').write_text(json.dumps({'format': 1, 'stamps': [e]}))
        (R / 'data/status/no-result-change/p1.json').write_text(json.dumps(r))
    stamp()
    smp = set(json.loads((R / 'data/status/no-result-change/p1.json').read_text())['sample'])
    f, t, add, reu = K.decide('world', want, HSn, Pn, rows_old, CUR, 'reuse', False, R)
    proven, unproven = [a for a in want if a in smp], [a for a in want if a not in smp]
    check('B7 shared code moved, a VALID signed proof (OLD -> CUR, pass, no network, equal files): only areas the proof built are reused (R1)',
          f == unproven and reu == proven and all('proven no result change (p1)' in r[3] for r in t if r[0] in proven)
          and all('did not build' in r[3] for r in t if r[0] in unproven))
    f, t, add, reu = K.decide('world', want, HSn, Pn, rows_old, CUR, 'shadow', False, R)
    check('B7 ... and in shadow mode only reported', f == want and not reu)
    for nm, e, r in (('a failed proof (result fail)', None, {'result': 'fail'}), ('a stale proof (to is not the current code hash)', {'to': 'c0de000other'}, {'to': 'c0de000other'}),
                     ('an unsigned stamp', {'approved_by': ''}, None), ("a stamp signed only 'KPC owner'", {'approved_by': 'KPC owner'}, None),
                     ('a future-dated stamp', {'approved_date': '2999-01-01'}, None), ('a proof that tried the network', None, {'network_attempts': 2}),
                     ('a proof with one differing file', None, {'files': {'x': ['ab' * 32, 'cd' * 32]}}), ('a proof with no sample', None, {'sample': []}),
                     ('a record that names another kind', None, {'kind': 'us-key'})):
        stamp(e, r)
        f, t, add, reu = K.decide('world', want, HSn, Pn, rows_old, CUR, 'reuse', False, R)
        check(f'B7 {nm}: full rebuild (every area)', f == want and not reu)
    stamp(); (R / 'data/status/no-result-change/p1.json').unlink()
    f, t, add, reu = K.decide('world', want, HSn, Pn, rows_old, CUR, 'reuse', False, R)
    check('B7 a missing proof record: full rebuild', f == want and not reu)
    stamp()
    inp3 = json.loads(json.dumps(inp)); inp3['FR']['layers'].append('x'); Pn3 = {a: parts_of(inp3, a, CUR) for a in inp3}
    f, t, add, reu = K.decide('world', want, hashes_of(Pn3), Pn3, rows_old, CUR, 'reuse', False, R)
    check('B7 valid proof, but FR\'s own data moved too: FR rebuilt, and only DE/GB that the proof built are reused (R1)',
          f == [a for a in want if a == 'FR' or a not in smp] and reu == [a for a in ['DE', 'GB'] if a in smp])
    r = run(sys.executable, '-B', str(ROOT / '.github/scripts/kpc_area_hash.py'), 'proof-check', 'world', '--repo', str(R), '--from', OLD, '--to', CUR)
    check('B7 proof-check CLI: VALID p1', r.returncode == 0 and r.stdout.startswith('VALID p1'))

# stamp-rows: only saved areas, only when the build checked out the plan's commit
with tempfile.TemporaryDirectory() as td:
    R = pathlib.Path(td); (R / 'data/world-key').mkdir(parents=True)
    for a in ('FR', 'DE'): (R / f'data/world-key/{a}.json').write_text('{"parks":{}}')
    (R / 'data/world-key/index.json').write_text(json.dumps({'countries': {'FR': {'parks': 1, 'rules': CUR}, 'DE': {'parks': 2}}, 'rules': OLD, 'complete': False}, indent=1))
    plan = {'plan_sha': 'abc', 'hashes': {'FR': '111111111111', 'DE': '222222222222'}, 'parts': {'FR': {'data:x': '1'}, 'DE': {'data:x': '2'}}, 'reused': []}
    done, same = K.stamp_rows(R, 'world', R / 'data/world-key/index.json', ['FR'], plan, 'abc')
    ix = json.loads((R / 'data/world-key/index.json').read_text())
    check('B stamp-rows: FR (saved) carries area_hash, parts, out_sha, built_sha; DE (kept) untouched; areas_rebuilt [FR]',
          done == ['FR'] and ix['countries']['FR']['area_hash'] == '111111111111' and ix['countries']['FR']['out_sha'] == K.sha_file(R / 'data/world-key/FR.json')
          and ix['countries']['DE'] == {'parks': 2} and ix['areas_rebuilt'] == ['FR'])
    check('B sanity: this key passes the whole-key check', K.sanity(R, 'world') == [])
    done, same = K.stamp_rows(R, 'world', R / 'data/world-key/index.json', ['FR'], plan, 'other-sha')
    ix = json.loads((R / 'data/world-key/index.json').read_text())
    check('B stamp-rows: a build on another commit than the plan claims no area hash (FR is planned again)', done == [] and 'area_hash' not in ix['countries']['FR'])
    K.stamp_rows(R, 'world', R / 'data/world-key/index.json', ['FR'], plan, 'abc'); (R / 'data/world-key/FR.json').write_text('{"changed":1}')
    check('B sanity: a key file that is not its row\'s out_sha fails (check 2)', any(b.startswith('2 FR') for b in K.sanity(R, 'world')))
    (R / 'data/world-key/GB.json').write_text('{}')
    check('B sanity: a key file with no index row fails (check 1)', any(b.startswith('1 GB') for b in K.sanity(R, 'world')))
    (R / 'data/world-key/GB.json').unlink(); (R / 'data/world-key/FR.json').write_text('{"parks":{}}')
    ix = json.loads((R / 'data/world-key/index.json').read_text()); ix['complete'] = True; ix['countries']['DE']['rules'] = CUR
    (R / 'data/world-key/index.json').write_text(json.dumps(ix))
    check('B sanity: a key-wide hash that claims more than its rows (complete, rows on another hash) fails (check 4)', any(b.startswith('4 ') for b in K.sanity(R, 'world')))

# Quality #163 must-fix: SHADOW WRITES NOTHING. stamp-rows in shadow mode (no --mode and KPC_AREA_HASH unset, 'shadow', or an unknown
# word) leaves index.json byte for byte and writes what it would stamp to --shadow-out and the job summary; only add / reuse write the rows.
def mk_stamp_key(td):
    R = pathlib.Path(td) / 'k'; (R / 'data/world-key').mkdir(parents=True)
    for a in ('FR', 'DE'): (R / f'data/world-key/{a}.json').write_text('{"parks":{}}')
    (R / 'data/world-key/index.json').write_text(json.dumps({'countries': {'FR': {'parks': 1, 'rules': CUR}, 'DE': {'parks': 2}}, 'rules': OLD, 'complete': False}, indent=2) + '\n')
    (R / 'plan.json').write_text(json.dumps({'plan_sha': 'abc', 'hashes': {'FR': '111111111111', 'DE': '222222222222'}, 'parts': {'FR': {'data:x': '1'}, 'DE': {'data:x': '2'}}, 'reused': []}))
    return R


def stamp_cli(R, mode_args, env_mode=None, extra=()):
    env = {k: v for k, v in os.environ.items() if k != 'KPC_AREA_HASH'}
    if env_mode is not None: env['KPC_AREA_HASH'] = env_mode
    env['GITHUB_STEP_SUMMARY'] = str(R / 'summary.md')
    return subprocess.run([sys.executable, '-B', str(ROOT / '.github/scripts/kpc_area_hash.py'), 'stamp-rows', 'world', *mode_args, '--repo', str(R),
                           '--index', str(R / 'data/world-key/index.json'), '--saved', 'FR', '--built-sha', 'abc', '--shadow-out', str(R / 'tmp/area-stamp-shadow/world.json'), *extra],
                          capture_output=True, text=True, env=env)


for label, margs, emode in (('no --mode, KPC_AREA_HASH unset', [], None), ('--mode shadow', ['--mode', 'shadow'], None),
                            ("KPC_AREA_HASH='shadow'", [], 'shadow'), ("an unknown mode ('bogus')", ['--mode', 'bogus'], None)):
    with tempfile.TemporaryDirectory() as td:
        R = mk_stamp_key(td); before = (R / 'data/world-key/index.json').read_bytes()
        r = stamp_cli(R, margs, emode, ['--plan', str(R / 'plan.json')])
        rec = json.loads((R / 'tmp/area-stamp-shadow/world.json').read_text()) if (R / 'tmp/area-stamp-shadow/world.json').exists() else {}
        check(f'B shadow ({label}): stamp-rows leaves index.json byte for byte', r.returncode == 0 and (R / 'data/world-key/index.json').read_bytes() == before)
        check(f'B shadow ({label}): what it would stamp is in --shadow-out (FR area_hash, out_sha, built_sha; areas_rebuilt) and the job summary',
              rec.get('mode') == 'shadow' and rec.get('written_to_index') is False and rec['rows']['FR']['area_hash'] == '111111111111'
              and rec['rows']['FR']['out_sha'] == K.sha_file(R / 'data/world-key/FR.json') and rec['rows']['FR']['built_sha'] == 'abc'
              and rec['areas_rebuilt'] == ['FR'] and 'DE' not in rec['rows'] and 'nothing written' in (R / 'summary.md').read_text())
with tempfile.TemporaryDirectory() as td:
    R = mk_stamp_key(td); before = (R / 'data/world-key/index.json').read_bytes()
    pd = R / 'parts/world-key-part-0'; pd.mkdir(parents=True); (pd / 'states.txt').write_text('FR DE\n'); (pd / 'built-sha.txt').write_text('abc\n')
    (pd / 'area-plan.json').write_text((R / 'plan.json').read_text())
    r = stamp_cli(R, [], None, ['--part', str(pd)])
    check('B shadow, per-part stamping (the US form, --part): index.json byte for byte, the record names FR',
          r.returncode == 0 and (R / 'data/world-key/index.json').read_bytes() == before and json.loads((R / 'tmp/area-stamp-shadow/world.json').read_text())['rows']['FR']['area_hash'] == '111111111111')
for m in ('add', 'reuse'):
    with tempfile.TemporaryDirectory() as td:
        R = mk_stamp_key(td)
        r = stamp_cli(R, ['--mode', m], None, ['--plan', str(R / 'plan.json')])
        ix = json.loads((R / 'data/world-key/index.json').read_text())
        check(f'B mode {m}: stamp-rows writes the rows into index.json (FR area_hash, areas_rebuilt), no shadow record',
              r.returncode == 0 and ix['countries']['FR'].get('area_hash') == '111111111111' and ix['areas_rebuilt'] == ['FR'] and ix['countries']['DE'] == {'parks': 2}
              and not (R / 'tmp/area-stamp-shadow/world.json').exists())
with tempfile.TemporaryDirectory() as td:
    R = mk_stamp_key(td); before = (R / 'data/world-key/index.json').read_bytes()
    stamp_cli(R, [], 'add', ['--plan', str(R / 'plan.json')])
    check('B KPC_AREA_HASH=add in the environment (no --mode) writes the rows; the workflows always pass --mode "$AREA_MODE"', (R / 'data/world-key/index.json').read_bytes() != before)

# the real checkout: plan in shadow mode changes nothing; the hashes do not move
before_status = run('git', 'status', '--porcelain', '--untracked-files=all', cwd=ROOT).stdout
for kind, lst in (('world', 'FR DE'), ('us', 'TN FL'), ('ca', '')):
    r = run(sys.executable, '-B', str(ROOT / '.github/scripts/kpc_area_hash.py'), 'plan', kind, '--list', lst, '--mode', 'shadow', cwd=ROOT)
    check(f'B real checkout, plan {kind} in shadow mode: prints the asked list unchanged ({lst or "none"})', r.returncode == 0 and r.stdout.split() == lst.split())
check('B real checkout: the four rules hashes did not move and git status is unchanged',
      REAL == {k: run(sys.executable, '-B', str(ROOT / K.FREEZE), 'rules', k, cwd=ROOT).stdout.strip() for k in REAL}
      and run('git', 'status', '--porcelain', '--untracked-files=all', cwd=ROOT).stdout == before_status)
check('B the tool is not a rule file and is listed in NOT_RULES', 'kpc_area_hash.py' in open(ROOT / K.FREEZE).read() and not any('kpc_area_hash' in f for v in K.freeze_lists(K.Tree(ROOT))[0].values() for f in v))

# the workflows: plan in reuse by default (owner signed Nov 12), a full-rebuild input, rows stamped after the build stamp
import yaml
for wf, kind, stampname in (('kpc-world-key.yml', 'world', 'stamp world-key'), ('kpc-us-key.yml', 'us', 'stamp us-key'), ('kpc-ca-key.yml', 'ca', 'stamp ca-key')):
    W = yaml.safe_load((ROOT / '.github/workflows' / wf).read_text(encoding='utf-8'))
    txt = (ROOT / '.github/workflows' / wf).read_text(encoding='utf-8')
    check(f'B {wf}: a full_rebuild input exists', 'full_rebuild' in W[True]['workflow_dispatch']['inputs'])
    check(f'B {wf}: the plan calls kpc_area_hash.py plan {kind} with the KPC_AREA_HASH variable, default reuse',
          f'kpc_area_hash.py plan {kind}' in txt and "vars.KPC_AREA_HASH || 'reuse'" in txt)
    check(f'B {wf}: stamp-rows runs after the build stamp', txt.index(stampname) < txt.index(f'kpc_area_hash.py stamp-rows {kind}'))
    check(f'B {wf}: the whole-key sanity check runs (read only, kept green)', f'kpc_area_hash.py sanity {kind}' in txt)
    calls = [st for j in W['jobs'].values() for st in j.get('steps', []) if f'kpc_area_hash.py stamp-rows {kind}' in str(st.get('run', ''))]
    check(f'B {wf}: stamp-rows (one call) passes --mode "$AREA_MODE" (the KPC_AREA_HASH variable, default reuse) and a --shadow-out under $RUNNER_TEMP',
          len(calls) == 1 and f'stamp-rows {kind} --mode "$AREA_MODE" --shadow-out "$RUNNER_TEMP/area-stamp-shadow/{kind}.json"' in calls[0]['run']
          and calls[0].get('env', {}).get('AREA_MODE', '').startswith("${{ vars.KPC_AREA_HASH || 'reuse' }}"))
    ups = [st for j in W['jobs'].values() for st in j.get('steps', []) if str(st.get('uses', '')).startswith('actions/upload-artifact')
           and st.get('with', {}).get('name') == f'area-stamp-shadow-{kind}']
    check(f'B {wf}: the shadow record is uploaded as an artifact (area-stamp-shadow-{kind}), never added to the key', len(ups) == 1
          and ups[0]['with']['path'] == '${{ runner.temp }}/area-stamp-shadow/' and 'area-stamp-shadow' not in ' '.join(str(st.get('run', '')) for j in W['jobs'].values() for st in j.get('steps', []) if 'git add' in str(st.get('run', ''))))
    jobs_up = [(jn, j['steps']) for jn, j in W['jobs'].items() for st in j.get('steps', []) if st in ups]
    jn, steps = jobs_up[0] if jobs_up else ('', [])
    k = steps.index(ups[0]) if ups else -1
    check(f'B {wf}: the shadow-record upload is kept green and REPORTED (continue-on-error, a kept_green_* id, a later "Report hidden failures" step that runs always)',
          len(ups) == 1 and ups[0].get('continue-on-error') is True and str(ups[0].get('id', '')).startswith('kept_green_')
          and any(st.get('name', '').startswith('Report hidden failures') and str(st.get('if', '')).strip() in ('always()', '${{ always() }}') for st in steps[k + 1:]))

print('ALL PASSED' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
