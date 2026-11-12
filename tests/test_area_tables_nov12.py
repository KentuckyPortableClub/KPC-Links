#!/usr/bin/env python3
"""D6 'tables out of the rule scripts' (KPC owner, 2026-11-12; owner decision D6). Offline, zero network.

  1. no rule file of the US / Canada / world keys assigns a dict (or a set / list) keyed by area codes any more (AST), except the
     reasoned allow-list below; the same scan finds the tables in the OLD files (so the scan is not blind);
  2. the move changes nothing: the tables the builders load from data/us-key/area-tables.json and data/world-key/area-tables.json
     equal the old literals (the old rule files are read from git, commit OLD), in the order the code uses them;
  3. the loaders fail closed: a missing / malformed / empty table stops the builder (SystemExit), never an empty table; a builder
     run with no table file exits non-zero and writes no key file;
  4. byte-identical output: the OLD and NEW builders on the same saved copy (US: 4 states; world: France, the job 6 fixtures) under
     the same fake clock write the same bytes; the NEW builder under two different wall clocks with the same KPC_BUILD_DATE writes
     the same bytes (the brief's 'same inputs give byte-identical output');
  5. area hashes (kpc_area_hash.py on this tree): a table change for ONE area moves only that area's hash, for each kind; an entry
     shared by a state set moves exactly those states; a change to a code-valued shared entry moves every area; unattributable
     table data (an unknown area code, an entry with no areas, another shape, an unreadable file) moves every area (fail closed);
     header texts move nothing; the US / world composition is ah2, Canada / 2-fers keep ah1.
Prints PASS / FAIL lines; the last line is ALL PASS or SOME FAILED (exit 1). SKIP lines when commit OLD is not in a shallow clone."""
import ast, gzip, hashlib, json, os, pathlib, re, shutil, socket, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
S = ROOT / '.github/scripts'
sys.path.insert(0, str(S)); sys.path.insert(0, str(ROOT / 'tests'))
import kpc_area_hash as K  # noqa: E402
import kpc_key_freeze as F  # noqa: E402
OLD = '2cd7aa0'   # KPC-Links main before D6 ('New references', Nov 12): the rule files with the tables still in the code
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg, flush=True); ok = ok and bool(c)


def git(*a):
    return subprocess.run(['git', *a], cwd=ROOT, capture_output=True)


HAVE_OLD = git('cat-file', '-e', OLD + '^{commit}').returncode == 0
def old_src(rel): return git('show', f'{OLD}:{rel}').stdout.decode('utf-8')


# ================================================================ 1. AST: no per-area table in a rule file
AREAS = set(K.US_ALL) | {'KY'} | set(K.Kind(K.Tree(ROOT), 'ca').areas) | set(K.Kind(K.Tree(ROOT), 'world').areas)
def is_area(n):
    if not (isinstance(n, ast.Constant) and isinstance(n.value, str)): return False
    v = re.sub(r'^(US|CA|W)-', '', n.value)
    return v in AREAS and bool(re.fullmatch(r'(?:(?:US|CA|W)-)?[A-Z]{2}', n.value))


def scan(src):
    """[(line, target, why)] for every assignment whose target key is an area code or whose value holds a dict keyed by area codes or
    a set / list / tuple made only of area codes (lambdas and functions inside the value are code, not walked)."""
    out = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)) or getattr(node, 'value', None) is None: continue
        tg = node.targets if isinstance(node, ast.Assign) else [node.target]
        why = [f'assigns the area key {ast.unparse(t.slice)}' for t in tg if isinstance(t, ast.Subscript) and is_area(t.slice)]
        st = [node.value]
        while st and not why:
            x = st.pop()
            if isinstance(x, (ast.Lambda, ast.FunctionDef)): continue
            if isinstance(x, ast.Dict) and any(k is not None and is_area(k) for k in x.keys): why.append('a dict keyed by area codes')
            elif isinstance(x, (ast.Set, ast.List, ast.Tuple)) and x.elts and all(is_area(e) for e in x.elts): why.append('a set / list of area codes')
            st.extend(ast.iter_child_nodes(x))
        if why: out.append((node.lineno, ','.join(ast.unparse(t) for t in tg)[:40], why[0]))
    return out


# What must stay, and why (file, assignment target): each is NOT a per-area table of results.
ALLOW = {
    ('kpc_us_key.py', 'DES'): 'PAD-US designation codes (SP state park, NF, NM national monument, WA wilderness area ...): the keys look like '
                              'state codes but are record types, the same for every state',
    ('kpc_us_key.py', 'SZ_US'): 'the two Mississippi zipped-shapefile layers: kpc_us_key_join.zip_owners reads SZ_US from the code as its '
                                'join-safety check, so it stays; kpc_area_hash.py counts it for MS only (TABLES)',
    ('kpc_ca_key.py', 'PROVS'): 'the whole province list (which state-gis.json rows are Canada\'s): the same for every province, no per-area value',
}
rule_py = sorted({f for k in ('us-key', 'ca-key', 'world-key') for f in F.RULE_FILES[k] if f.endswith('.py')})
left = []
for rel in rule_py:
    for ln, tg, why in scan((ROOT / rel).read_text(encoding='utf-8')):
        if (rel.split('/')[-1], tg) not in ALLOW: left.append(f'{rel}:{ln} {tg}: {why}')
check(not left, f'no US / Canada / world rule file assigns a table keyed by area codes ({len(rule_py)} files; allow-list {len(ALLOW)}): {left[:6]}')
check(all(any(rel.endswith('/' + f) for rel in rule_py) for f, _ in ALLOW), 'every allow-listed file is a rule file')
seen = {(rel.split('/')[-1], tg) for rel in rule_py for _, tg, _ in scan((ROOT / rel).read_text(encoding='utf-8'))}
check(set(ALLOW) <= seen, 'every allow-list entry still exists (a stale entry would hide nothing; remove it when the code goes)')
if HAVE_OLD:
    o = {tg for rel in ('.github/scripts/kpc_us_key.py', '.github/scripts/kpc_world_key.py') for _, tg, _ in scan(old_src(rel))}
    check({'BOX_ADD', 'XS', 'SRC', 'GEN', '_LOC', 'KINDS', 'SIDE_NOT', 'EU', 'NO_N2K'} <= o and "SRC['CH']" in o and "KINDS['CL']" in o,
          f'the scan finds the tables in the OLD rule files (it is not blind): {sorted(o)[:12]}')
else: print(f'SKIP old-file scan: commit {OLD} is not in this clone')


# ================================================================ 2. the loaded tables equal the old literals
def world_ns(src):
    g = {'__name__': 'kpc_world_key_prefix', '__file__': str(S / 'kpc_world_key.py')}
    cwd = os.getcwd(); os.chdir(ROOT)
    try: exec(compile(src[:src.index('\nfor cc in COUNTRIES:')], 'kpc_world_key.py', 'exec'), g)
    finally: os.chdir(cwd)
    return g


def us_ns(src):
    import types
    m = types.ModuleType('kpc_us_key_prefix'); m.__file__ = str(S / 'kpc_us_key.py')
    cwd = os.getcwd(); os.chdir(ROOT)
    try: exec(compile(src.split('\nidx = {}\n')[0], 'kpc_us_key.py', 'exec'), m.__dict__)
    finally: os.chdir(cwd)
    return m.__dict__


def same(a, b):
    """Deep equality with types (tuple is not list) and dict order."""
    if type(a) is not type(b): return False
    if isinstance(a, dict): return list(a) == list(b) and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)): return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


NEW_W = world_ns((S / 'kpc_world_key.py').read_text(encoding='utf-8'))
NEW_U = us_ns((S / 'kpc_us_key.py').read_text(encoding='utf-8'))
if HAVE_OLD:
    OW = world_ns(old_src('.github/scripts/kpc_world_key.py')); OU = us_ns(old_src('.github/scripts/kpc_us_key.py'))
    for name in ('SRC', 'EU', 'GEN', '_LOC', 'SIDE_NOT', 'EXTRA_URLS', 'LAYER_NAMEF', 'SHEET_URLS', 'COUNTRIES'):
        check(same(OW[name], NEW_W[name]), f'world {name}: the loaded table equals the old one (deep, with types and order)')
    check(OW['KINDS'] == NEW_W['KINDS'] and all(same(OW['KINDS'][c], NEW_W['KINDS'][c]) for c in OW['KINDS']),
          'world KINDS: every country\'s list equals the old one (deep, with types and order)')
    # KINDS dict ORDER differs (the old code put CL after the sheet countries); the code only looks a country up: KINDS[cc] / setdefault
    _wk = (S / 'kpc_world_key.py').read_text(encoding='utf-8')
    uses = [n for n in ast.walk(ast.parse(_wk)) if isinstance(n, ast.Name) and n.id == 'KINDS']
    parents = {id(c): p for p in ast.walk(ast.parse(_wk)) for c in ast.iter_child_nodes(p)}
    tree = ast.parse(_wk); pmap = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    kinds_uses = [pmap[n] for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == 'KINDS']
    check(all(isinstance(p, ast.Subscript) or (isinstance(p, ast.Attribute) and p.attr == 'setdefault') or isinstance(p, ast.Assign) for p in kinds_uses),
          'world KINDS is only looked up by country (KINDS[cc], setdefault), never iterated: its dict order does not count')
    check(set(NEW_W['TYPE_PREFER']) == {'CH'} and same(OW['CHPREF'], NEW_W['TYPE_PREFER']['CH']), 'world CHPREF = TYPE_PREFER[CH] (and only CH has one)')
    check(NEW_W['SPLIT_LAYERS'] == {'AU': (frozenset(OW['QLD_LAYERS']), OW['QLD_REST'])}, 'world QLD_LAYERS / QLD_REST = SPLIT_LAYERS[AU]')
    lab = lambda g: {x[0]: x[2] for v in g['SRC'].values() for x in v if len(x) > 2}
    check(lab(OW) == lab(NEW_W), 'world: the label -> address maps the builder makes from SRC (tracts, layers.json) are the same')
    check(same(OU['BOX_ADD'], NEW_U['BOX_ADD']), 'US BOX_ADD: the loaded table equals the old one (tuples, order)')
    check(same(OU['XS'], NEW_U['XS']) and len(NEW_U['XS']) == len(OU['XS']), f'US XS: the list equals the old one entry by entry, in the same order, with the same types ({len(NEW_U["XS"])} entries incl. state-gis.json)')
    check(same(OU['SZ_US'], NEW_U['SZ_US']), 'US SZ_US (left in the code) unchanged')
else: print(f'SKIP table equality: commit {OLD} is not in this clone')


# ================================================================ 3. the loaders fail closed
td = pathlib.Path(tempfile.mkdtemp(prefix='kpc-d6-'))
try:
    good_w = json.loads((ROOT / 'data/world-key/area-tables.json').read_text(encoding='utf-8'))
    good_u = json.loads((ROOT / 'data/us-key/area-tables.json').read_text(encoding='utf-8'))
    def stops(fn, data, raw=None):
        p = td / 'tables.json'
        if raw is not None: p.write_text(raw)
        elif data is None: p.unlink(missing_ok=True)
        else: p.write_text(json.dumps(data))
        try: fn(p); return False
        except SystemExit: return True
    import copy
    def mut(d, f): d = copy.deepcopy(d); f(d); return d
    check(not stops(NEW_W['area_tables'], good_w), 'world loader: the shipped file loads')
    for why, d, raw in (('missing', None, None), ('not JSON', None, '{not json'), ('format 2', mut(good_w, lambda d: d.update(format=2)), None),
                        ('SRC empty', mut(good_w, lambda d: d.update(SRC={})), None), ('GEN missing', mut(good_w, lambda d: d.pop('GEN')), None),
                        ('a bad regex', mut(good_w, lambda d: d['GEN'].update(AU='(')), None), ('a source of 2 fields', mut(good_w, lambda d: d['SRC']['DE'].append(['x', 'y'])), None),
                        ('a lower-case country key', mut(good_w, lambda d: d['SIDE_NOT'].update(fr=['sur'])), None), ('an EU country with no LOC', mut(good_w, lambda d: d['LOC'].pop('PL')), None)):
        check(stops(NEW_W['area_tables'], d, raw), f'world loader stops (never an empty table) on: {why}')
    check(not stops(NEW_U['area_tables'], good_u), 'US loader: the shipped file loads')
    for why, d, raw in (('missing', None, None), ('not JSON', None, '[1,'), ('XS empty', mut(good_u, lambda d: d.update(XS=[])), None),
                        ('BOX_ADD of 3 numbers', mut(good_u, lambda d: d['BOX_ADD'].update(FL=[1, 2, 3])), None), ('BOX_ADD of a non-state', mut(good_u, lambda d: d['BOX_ADD'].update(ZZ=[1, 2, 3, 4])), None),
                        ('an XS entry with no label', mut(good_u, lambda d: d['XS'][0].pop('label')), None), ('an XS entry with no states', mut(good_u, lambda d: d['XS'][0].update(areas=[])), None),
                        ('a prefix listed twice', mut(good_u, lambda d: d['XS'].append(dict(d['XS'][1]))), None), ('an unknown field', mut(good_u, lambda d: d['XS'][0].update(extra=1)), None)):
        check(stops(NEW_U['area_tables'], d, raw), f'US loader stops (never an empty table) on: {why}')
    try: NEW_U['with_state_layers'](NEW_U['XS'][:3], [dict(good_u['XS'][0], after='nope')]); bad_after = False
    except SystemExit: bad_after = True
    check(bad_after, "US: an XS 'after' that names no national layer stops the build")
finally:
    shutil.rmtree(td, ignore_errors=True)


# ================================================================ 4. byte-identical builder output
RUNNER = r'''
import sys, time, datetime, socket, runpy
def _off(*a, **k): raise OSError('network disabled in this test')
socket.socket.connect = _off; socket.create_connection = _off; socket.getaddrinfo = _off
FAKE = float(sys.argv[1]); _real = time.time; _start = _real()
def ftime(): return FAKE + (_real() - _start)
_lt, _gt, _sf = time.localtime, time.gmtime, time.strftime
time.time = ftime; time.localtime = lambda s=None: _lt(ftime() if s is None else s); time.gmtime = lambda s=None: _gt(ftime() if s is None else s)
time.strftime = lambda fmt, t=None: _sf(fmt, time.localtime() if t is None else t)
class D(datetime.datetime):
    @classmethod
    def now(cls, tz=None): return cls.fromtimestamp(ftime(), tz)
    @classmethod
    def utcnow(cls): return cls.utcfromtimestamp(ftime())
    @classmethod
    def today(cls): return cls.fromtimestamp(ftime())
class DD(datetime.date):
    @classmethod
    def today(cls): return cls.fromtimestamp(ftime())
datetime.datetime = D; datetime.date = DD
sys.argv = [sys.argv[2]]; runpy.run_path(sys.argv[0], run_name='__main__')
'''
T = pathlib.Path(tempfile.mkdtemp(prefix='kpc-d6-run-'))
CLOCK_A, CLOCK_B = '1762000000', '1770000000'   # 2025-11-01 and 2026-02-01


def outputs(work):
    """{relative path: bytes} of every file the builder wrote under data/ (the kpc_save status file left out: run-level)."""
    return {str(p.relative_to(work)): p.read_bytes() for p in sorted((work / 'data').rglob('*')) if p.is_file()
            and not str(p.relative_to(work)).startswith(('data/status/', 'data/parkinfo/')) and p.name != 'overrides.json'}


def run(script, work, clock, env_add=None):
    (T / 'runner.py').write_text(RUNNER)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('KPC_', 'GEO_', 'STATES', 'COUNTRIES'))}
    dead = 'http://127.0.0.1:9'
    env.update(GEO_CACHE_MODE='only', TZ='America/Chicago', PYTHONDONTWRITEBYTECODE='1', HTTP_PROXY=dead, HTTPS_PROXY=dead, http_proxy=dead, https_proxy=dead, no_proxy='', NO_PROXY='')
    env.update(env_add or {})
    return subprocess.run([sys.executable, '-B', str(T / 'runner.py'), clock, str(script)], cwd=work, env=env, capture_output=True, text=True, timeout=600)


def us_fixture(work, dated):
    """4 states (NH, FL with its Keys box, HI with the akht trail corridor, MI), synthetic parks and records, a saved copy."""
    if work.exists(): shutil.rmtree(work)
    for d in ('data/parkinfo', 'data/us-key', 'cache/us'): (work / d).mkdir(parents=True)
    sq = lambda la, lo, d: [[[lo - d, la - d], [lo + d, la - d], [lo + d, la + d], [lo - d, la + d], [lo - d, la - d]]]
    def rec(oid, name, ac, la, lo, d, own, label, k, rd=None):
        r = {'OBJECTID': oid, 'Unit_Nm': name, 'Loc_Nm': '', 'Own_Type': own, 'Mang_Type': own, 'Mang_Name': str(oid)[:4].upper(), 'Loc_Mang': label,
             'Des_Tp': '', 'GIS_Acres': ac, 'Category': 'Fee', '_r': sq(la, lo, d), '_k': k}
        if rd and dated: r['rd'] = rd
        return r
    P = {'NH': {'US-99001': ['Example Pond State Park', '', 'State Park', '', '', 43.5, -71.5, 0, 0, 0], 'US-99002': ['Bear Hill State Forest', '', 'State Forest', '', '', 43.7, -71.7, 0, 0, 0]},
         'FL': {'US-99011': ['Long Key State Park', '', 'State Park', '', '', 24.82, -80.82, 0, 0, 0], 'US-99012': ['Pine Hollow Wildlife Management Area', '', 'Wildlife Management Area', '', '', 28.5, -81.9, 0, 0, 0]},
         'HI': {'US-99021': ['Ala Kahakai National Historic Trail', '', 'National Historic Trail', '', '', 19.6, -155.99, 0, 0, 0]},
         'MI': {'US-99031': ['Cedar River State Game Area', '', 'State Game Area', '', '', 44.0, -85.3, 0, 0, 0]}}
    R = {'NH': [rec('sgnhx1', 'Example Pond State Park', 300, 43.5, -71.5, .01, 'STAT', 'Example state parks (state GIS table)', ['sp'], '2026-10-01'),
                rec(123456, 'Bear Hill State Forest', 900, 43.7, -71.7, .02, 'STAT', 'NH', ['sf'])],
         'FL': [rec('fnl7', 'Long Key State Park', 965, 24.82, -80.82, .01, 'STAT', 'Florida Natural Areas Inventory conservation lands', ['sp'], '2026-11-01'),
                rec(223344, 'Pine Hollow Wildlife Management Area', 5000, 28.5, -81.9, .03, 'STAT', 'FL', ['wma'])],
         'HI': [rec('akht1', 'Ala Kahakai National Historic Trail', 0, 19.6, -155.99, .05, 'FED', 'NPS Ala Kahakai National Historic Trail corridor (official)', [], '2026-09-15')],
         'MI': [rec('mid9', 'Cedar River State Game Area', 2000, 44.0, -85.3, .02, 'STAT', 'Michigan DNR project boundaries', ['wma'])]}
    (work / 'data/us-key/overrides.json').write_text(json.dumps({'parks': {}}))
    for st, pk in P.items():
        (work / f'data/parkinfo/US-{st}.json').write_text(json.dumps({'parks': pk, 'state': st}))
        blob = dict({'recs': R[st], 'seen': len(R[st]), 'detail': 0.01}, **({'saved': '2026-10-20'} if dated else {}))
        with gzip.GzipFile(work / f'cache/us/US-{st}.json.gz', 'wb', mtime=0) as z: z.write(json.dumps(blob).encode())
    return {'STATES': ' '.join(P)}


try:
    old_root = T / 'old'
    if HAVE_OLD:
        old_root.mkdir(); tar = git('archive', OLD, '.github/scripts').stdout
        subprocess.run(['tar', '-x', '-C', str(old_root)], input=tar, check=True)
    # --- US
    for dated in (True, False):
        tag = 'dated copy' if dated else 'copy without dates'
        if HAVE_OLD:
            e = us_fixture(T / 'uo', dated); ro = run(old_root / '.github/scripts/kpc_us_key.py', T / 'uo', CLOCK_A, e)
            e = us_fixture(T / 'un', dated); rn = run(S / 'kpc_us_key.py', T / 'un', CLOCK_A, e)
            a, b = outputs(T / 'uo'), outputs(T / 'un')
            check(ro.returncode == 0 and rn.returncode == 0 and a == b and any(k.endswith('US-FL.json') for k in a) and len(a) >= 12,
                  f'US ({tag}): OLD and NEW builders write byte-identical files under the same clock ({len(a)} files: keys, reviews, tracts, index, layers)')
        else: print('SKIP US old vs new: no OLD commit')
    e = us_fixture(T / 'u1', False); r1 = run(S / 'kpc_us_key.py', T / 'u1', CLOCK_A, dict(e, KPC_BUILD_DATE='2026-01-01'))
    e = us_fixture(T / 'u2', False); r2 = run(S / 'kpc_us_key.py', T / 'u2', CLOCK_B, dict(e, KPC_BUILD_DATE='2026-01-01'))
    a, b = outputs(T / 'u1'), outputs(T / 'u2')
    fl = json.loads(a.get('data/us-key/US-FL.json', b'{}'))
    check(r1.returncode == 0 and a == b and {p.get('read') for p in (fl.get('parks') or {}).values()} == {'2026-01-01'},
          'US: same inputs + same KPC_BUILD_DATE under two wall clocks (2025-11-01, 2026-02-01): byte-identical files; a park read from a copy with no date gets KPC_BUILD_DATE')
    e = us_fixture(T / 'u3', True); r3 = run(S / 'kpc_us_key.py', T / 'u3', CLOCK_A, e)
    e = us_fixture(T / 'u4', True); r4 = run(S / 'kpc_us_key.py', T / 'u4', CLOCK_B, e)
    k3 = json.loads(outputs(T / 'u3').get('data/us-key/US-FL.json', b'{}'))
    check(r3.returncode == 0 and {k: v for k, v in outputs(T / 'u3').items() if '/tracts/' not in k} == {k: v for k, v in outputs(T / 'u4').items() if '/tracts/' not in k}
          and {r: p.get('read') for r, p in (k3.get('parks') or {}).items()} == {'US-99011': '2026-11-01', 'US-99012': '2026-10-20'},
          "US: a dated copy, NO KPC_BUILD_DATE, two wall clocks: the key files are byte-identical; read = the record's rd, else the copy's saved")
    e = us_fixture(T / 'u5', True); r5 = run(S / 'kpc_us_key.py', T / 'u5', CLOCK_A, dict(e, KPC_BUILD_DATE='2026-13-40'))
    check(r5.returncode != 0 and not list((T / 'u5/data/us-key').glob('US-*.json')), 'US: a malformed KPC_BUILD_DATE stops the build, no key file written')
    # no table file next to the builder: copy the scripts without the data file
    nt = T / 'notables'; shutil.copytree(S, nt / '.github/scripts', ignore=shutil.ignore_patterns('__pycache__'))
    e = us_fixture(T / 'u6', True); r6 = run(nt / '.github/scripts/kpc_us_key.py', T / 'u6', CLOCK_A, e)
    check(r6.returncode != 0 and 'area-tables.json' in (r6.stdout + r6.stderr) and not list((T / 'u6/data/us-key').glob('US-*.json')),
          'US: no data/us-key/area-tables.json in the builder\'s checkout: exit non-zero, no key file written (fail closed)')
    # --- world (France, the job 6 fixtures)
    import kpc_fr_patrinat_fixture as H
    g = H.load_prefix(); recs = H.records(g, True); park_doc, _ = H.parks()
    def w_fixture(work):
        if work.exists(): shutil.rmtree(work)
        (work / 'data/world-key').mkdir(parents=True); (work / 'data/parkinfo').mkdir(parents=True); (work / 'cache').mkdir()
        json.dump(park_doc, open(work / 'data/parkinfo/FR.json', 'w', encoding='utf-8'), ensure_ascii=False)
        for rel in ('data/world-key/overrides.json', 'data/retired-refs.json', 'data/world-key/extra-layers.json', 'data/world-key/sheet-countries.json', 'data/world-key/eea-designations.json'):
            if (ROOT / rel).is_file(): shutil.copy(ROOT / rel, work / rel)
        rows = []
        for r in recs:
            o = {k: v for k, v in r.items() if k != '_k'}
            o['_r'] = [[[round(pt[0], 5), round(pt[1], 5)] for pt in ring if len(pt) >= 2] for ring in (r.get('_r') or [])]
            rows.append(o)
        blob = {'cc': 'FR', 'saved': '2026-10-20', 'detail': g['DETAIL'], 'thin': g['THIN_N'], 'recs': rows}
        with gzip.GzipFile(work / 'cache/W-FR.json.gz', 'wb', mtime=0) as z: z.write(json.dumps(blob, separators=(',', ':'), default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else str(o)).encode())
        return {'COUNTRIES': 'FR', 'GEO_CACHE': str(work / 'cache')}
    if HAVE_OLD:
        e = w_fixture(T / 'wo'); ro = run(old_root / '.github/scripts/kpc_world_key.py', T / 'wo', CLOCK_A, e)
        e = w_fixture(T / 'wn'); rn = run(S / 'kpc_world_key.py', T / 'wn', CLOCK_A, e)
        a, b = outputs(T / 'wo'), outputs(T / 'wn')
        check(ro.returncode == 0 and rn.returncode == 0 and a == b and 'data/world-key/FR.json' in a and any('/world-bounds/' in k for k in a),
              f'world (FR): OLD and NEW builders write byte-identical files under the same clock ({len(a)} files: key, review, tracts, index, layers, world-bounds)')
    else: print('SKIP world old vs new: no OLD commit')
    e = w_fixture(T / 'w1'); r1 = run(S / 'kpc_world_key.py', T / 'w1', CLOCK_A, dict(e, KPC_BUILD_DATE='2026-01-01'))
    e = w_fixture(T / 'w2'); r2 = run(S / 'kpc_world_key.py', T / 'w2', CLOCK_B, dict(e, KPC_BUILD_DATE='2026-01-01'))
    a = outputs(T / 'w1')
    check(r1.returncode == 0 and a == outputs(T / 'w2') and json.loads(a['data/world-key/tracts/FR.json'])['built'] == '2026-01-01',
          'world (FR): same inputs + same KPC_BUILD_DATE under two wall clocks: byte-identical files (tracts built = KPC_BUILD_DATE)')
finally:
    shutil.rmtree(T, ignore_errors=True)


# outlines made from the key (kpc_outlines_from_key.py, not a rule file): date_read = the park's read date in the key, else the copy's saved
import kpc_outlines_from_key as FK  # noqa: E402
_ug = FK.union_geometry
FK.union_geometry = lambda rs: ({'type': 'Polygon', 'coordinates': [[[0, 0], [0.01, 0], [0.01, 0.01], [0, 0.01], [0, 0]]]}, '')   # shapely-free stand-in
ot = pathlib.Path(tempfile.mkdtemp(prefix='kpc-d6-ol-'))
try:
    for d_ in ('key', 'out', 'cache'): (ot / d_).mkdir()
    (ot / 'key/US-NH.json').write_text(json.dumps({'st': 'NH', 'parks': {'US-99001': {'n': 'A', 'g': 'official', 'm': [['sgnhx1', 'A', 1, 'name']], 'read': '2026-11-01'},
                                                                        'US-99002': {'n': 'B', 'g': 'official', 'm': [[123456, 'B', 1, 'name']]}}}))
    with gzip.open(ot / 'cache/US-NH.json.gz', 'wt') as f_: json.dump({'st': 'NH', 'saved': '2026-10-20', 'recs': [{'OBJECTID': 'sgnhx1', '_r': []}, {'OBJECTID': 123456, '_r': []}]}, f_)
    added, _ = FK.build_state('NH', ot / 'cache', root=ot / 'out', key_dir=ot / 'key', say=lambda *a: None)
    check({r['ref']: r['date_read'] for r in added} == {'US-99001': '2026-11-01', 'US-99002': '2026-10-20'},
          "outlines from the key: date_read = the park's read date in the key, else the saved copy's date (never the clock)")
finally:
    FK.union_geometry = _ug; shutil.rmtree(ot, ignore_errors=True)


# ================================================================ 5. area hashes on this tree
class Patched(K.Tree):
    """This checkout's files, with some replaced (bytes) or removed (None)."""
    def __init__(self, patches):
        super().__init__(ROOT, None); self.p = patches
    def oid(self, path):
        if path in self.p: return None if self.p[path] is None else 'patched:' + hashlib.sha256(self.p[path]).hexdigest()
        return super().oid(path)
    def read(self, path):
        return self.p[path] if path in self.p else super().read(path)


def moved(kind, patches):
    base = K.Kind(K.Tree(ROOT, None), kind, 3).parts()
    new = K.Kind(Patched(patches), kind, 3).parts()
    return K.diff_parts(base, new)


UF, WF = 'data/us-key/area-tables.json', 'data/world-key/area-tables.json'
U0, W0 = json.loads((ROOT / UF).read_text(encoding='utf-8')), json.loads((ROOT / WF).read_text(encoding='utf-8'))
def uj(f): d = json.loads(json.dumps(U0)); f(d); return {UF: json.dumps(d, indent=1).encode()}
def wj(f): d = json.loads(json.dumps(W0)); f(d); return {WF: json.dumps(d, indent=1).encode()}
def xs(d, pre): return next(e for e in d['XS'] if e['prefix'] == pre)
N_US, N_W = len(K.Kind(K.Tree(ROOT), 'us').areas), len(K.Kind(K.Tree(ROOT), 'world').areas)

d = moved('us', uj(lambda d: d['BOX_ADD']['FL'].__setitem__(2, -79.7)))
check(set(d) == {'FL'} and d['FL'] == [f'data:{UF}:BOX_ADD changed'], f'US: BOX_ADD[FL] edited -> only FL moves, reason data:...:BOX_ADD ({d})')
d = moved('us', uj(lambda d: xs(d, 'vta').update(label='Vermont ANR lands (renamed)')))
check(set(d) == {'VT'} and d['VT'] == [f'data:{UF}:XS changed'], f'US: the XS entry of VT edited -> only VT moves ({sorted(d)})')
d = moved('us', uj(lambda d: xs(d, 'odw').update(areas=['KS', 'OK'])))
check(set(d) == {'KS', 'OK'}, f'US: an XS entry widened to the state set KS + OK -> exactly KS and OK move ({sorted(d)})')
d = moved('us', uj(lambda d: d['XS'].append({'areas': ['NV', 'UT'], 'prefix': 'zzz', 'url': 'https://x.example.gov/FeatureServer/0/query', 'name_field': 'N',
                                             'acres_field': '', 'kinds': [], 'label': 'two-state layer', 'owner': 'STAT'})))
check(set(d) == {'NV', 'UT'}, f'US: a new XS entry stored once for NV + UT -> exactly NV and UT move ({sorted(d)})')
for why, f in (('an entry for an unknown state code', lambda d: d['XS'].append(dict(xs(d, 'vta'), prefix='zzy', areas=['ZZ']))),
               ('an entry with no areas', lambda d: d['XS'].append({k: v for k, v in xs(d, 'vta').items() if k != 'areas'})),
               ('a BOX_ADD key that is no state', lambda d: d['BOX_ADD'].update(ZZ=[0, 0, 1, 1])),
               ('a new table of another shape', lambda d: d.update(NEW='x'))):
    d = moved('us', uj(f))
    check(len(d) == N_US and any('#unattributed' in x for x in d['AL']), f'US: {why} -> every state moves (fail closed, shared part)')
d = moved('us', {UF: b'{not json'})
check(len(d) == N_US and any('area-tables.json!unreadable' in x for x in d['AL']), 'US: an unreadable table file -> every state moves')
d = moved('us', {UF: None})
check(len(d) == N_US, 'US: a missing table file -> every state moves')
d = moved('us', uj(lambda d: (d['notes'].update(FL=['reworded']), d.update(about='reworded'))))
check(not d, 'US: an edit to the header texts (about, notes) moves nothing')
src = (S / 'kpc_us_key.py').read_text(encoding='utf-8')
d = moved('us', {'.github/scripts/kpc_us_key.py': src.replace("'National Wilderness Preservation System (Forest Service map)'", "'National Wilderness Preservation System (renamed)'", 1).encode()})
check(len(d) == N_US and all(x.startswith('code:') for x in d['FL']), 'US: a national XS layer (a code-valued shared entry) edited -> every state moves')
d = moved('us', {'.github/scripts/kpc_us_key.py': src.replace("'mszp', ", "'mszq', ", 1).encode()})
check(set(d) == {'MS'}, f'US: the Mississippi zip layers left in the code (SZ_US) still count for MS only ({sorted(d)})')

for name, cc, f in (('SRC', 'DE', lambda d: d['SRC']['DE'][0].__setitem__(0, 'BfN renamed')), ('GEN', 'AU', lambda d: d['GEN'].update(AU=d['GEN']['AU'] + '|bushland')),
                    ('LOC', 'FR', lambda d: d['LOC'].update(FR=d['LOC']['FR'] + '|ile')), ('KINDS', 'CL', lambda d: d['KINDS']['CL'].append(['x', 'x'])),
                    ('SIDE_NOT', 'NO', lambda d: d['SIDE_NOT']['NO'].append('nord')), ('TYPE_PREFER', 'CH', lambda d: d['TYPE_PREFER']['CH'].update(X=['y'])),
                    ('SPLIT_LAYERS', 'AU', lambda d: d['SPLIT_LAYERS']['AU'].update(rest_where='1=1')), ('EU', 'LU', lambda d: d['EU'].update(LU=False))):
    d = moved('world', wj(f))
    check(set(d) == {cc} and d[cc] == [f'data:{WF}:{name} changed'], f'world: {name}[{cc}] edited -> only {cc} moves ({sorted(d)})')
d = moved('world', wj(lambda d: d['SRC'].update(ZZ=[['x', 'arcgis', 'https://x.example.org/MapServer/0']])))
check(len(d) == N_W, 'world: a table entry for a code that is no country of the key -> every country moves (fail closed)')
d = moved('world', wj(lambda d: d['notes'].update(CH=['reworded'])))
check(not d, 'world: an edit to the notes moves nothing')
wsrc = (S / 'kpc_world_key.py').read_text(encoding='utf-8')
d = moved('world', {'.github/scripts/kpc_world_key.py': wsrc.replace('_EN = (r"natura 2000|', '_EN = (r"natura 2000|natura|', 1).encode()})
check(len(d) == N_W, 'world: the shared English words (_EN, code) edited -> every country moves')
check(K.composition('us') == 'ah2' and K.composition('world') == 'ah2' and K.composition('ca') == 'ah1' and K.composition('fers') == 'ah1',
      'composition: US and world ah2 (their parts changed with D6), Canada and 2-fers ah1 (unchanged)')
check(not any(k.startswith('code-area:') for p in K.Kind(K.Tree(ROOT), 'world').parts().values() for k in p),
      'world: no code-area part is left (every per-country table is a data part)')
check(not any(k.startswith('shared:') and 'area-tables' in k for k in K.Kind(K.Tree(ROOT), 'us').parts()['AL'])
      and not any(k.startswith('shared:') and 'area-tables' in k for k in K.Kind(K.Tree(ROOT), 'world').parts()['DE']),
      'the shipped table files have nothing unattributable (no shared part from them)')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
