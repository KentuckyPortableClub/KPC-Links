#!/usr/bin/env python3
"""The D4 proof job's work (KPC owner, 2026-11-12): prove that a CODE-only change between two commits does not change a key's results,
and write the proof record that kpc_area_hash.proof_valid() reads. Run by hand only, through .github/workflows/kpc-key-proof.yml.

  sample  KIND --old SHA --new SHA [--areas "X Y"]       the sample and why each area is in it (deterministic; cannot be shrunk)
  run     KIND --old SHA --new SHA --inputs DIR --out DIR [--areas ...] [--kpc-data DIR]
          builds every sample area with the OLD and the NEW code, each in its own clean tree, from IDENTICAL inputs, with the network
          denied and counted, a fixed clock, fixed locale / TZ / hash seed and the same Python; compares the sha256 of every file the
          builds wrote; writes the UNSIGNED proof record (pass or fail). Exit 0 = PASS, 1 = FAIL, 2 = could not run (no record).
  check   KIND --record FILE                              what the plan's reader (proof_valid) would refuse in a record, besides the stamp
  shim    DIR                                             write the network / clock guard (sitecustomize.py) into DIR (for a look)

What "identical inputs" means: both trees are the NEW commit's files with only the CODE paths (CODE_PREFIXES, every *.py / *.sh, and
every rule file named in kpc_key_freeze.RULE_FILES) taken from the OLD commit. Everything else (data/, the overrides manifest and parts,
the research-inbox answers, the scope / version-free JSON) is the NEW commit's. KPC-Data (the moved park data of .github/kpc-moved.txt,
the pin fills in data/intake, the Recreation.gov copy) comes from ONE KPC-Data commit, and the saved copies from the boundary-cache
release; both are laid into both trees before any build. The sha256 of every input is recorded, and the digest of each prepared tree's
non-code files must be the same on both sides (else no proof: exit 2).

The claim is about SHARED code. An area whose OWN inputs moved between old and new (kpc_area_hash parts other than code: / version /
hosts:shared / reader:) is rebuilt by the plan anyway: it is built and compared here too, but it is not in the claim (record `excluded`).
If its only own moves are data (the same data is given to both sides here), a difference is the code's doing and FAILS the proof; if its
own per-area code table moved (`code-area:`), a difference is expected and only reported.

The job never signs: the record's stamp entry has approved_by / approved_date empty. The owner signs by adding the entry to
.github/no-result-change.json in a reviewed PR together with the record (the expected-holds pattern: a proposed file is never read).
Not a rule file (kpc_key_freeze.NOT_RULES): it decides no join."""
import argparse, datetime, hashlib, json, os, pathlib, random, re, shutil, subprocess, sys, tarfile, io

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
KINDS = {'us': 'us-key', 'ca': 'ca-key', 'world': 'world-key'}
WRITER = 'kpc_key_proof.py'
RECORD_FORMAT = 1
STAMP_FILE = '.github/no-result-change.json'
PROOF_DIR = 'data/status/no-result-change'
CA_PROVS = 'AB BC MB NB NL NS NT NU ON PE QC SK YT'.split()
# D4 (owner YES, Nov 12): the biggest and the weirdest areas of each kind, always in the sample
FIXED = {'us': {'CA': 'biggest', 'TX': 'biggest', 'FL': 'weirdest (its own box and hand files)', 'AK': 'weirdest (read in parts)',
                'HI': 'weirdest (islands)'},
         'world': {'AU': 'biggest', 'FR': 'biggest', 'CH': 'weirdest (federal shapefiles in LV95)', 'JP': 'weirdest (the A10 file, pin join)'},
         'ca': {'ON': 'biggest province', 'NB': 'weirdest province (the NB wildlife-zone layer is merged by hand rules)'}}
N_SEEDED = 3
# a floor under the recorded universe the seeded areas are drawn from (the reader refuses a record whose universe lacks one of these)
def universe_floor(kind):
    sys.path.insert(0, str(HERE)); import kpc_area_hash as K  # noqa: E401
    return {'us': list(K.US_ALL), 'world': list(K.WORLD_DEFAULT), 'ca': list(CA_PROVS)}[kind]

CODE_PREFIXES = ('.github/scripts/', 'tests/', '.github/key-rules-version.json')
CODE_SUFFIXES = ('.py', '.sh', '.js', '.mjs')
# inputs, the job's own scratch, and run bookkeeping (kpc_save's 'when did each file change' record) are never compared; an index file
# is compared row by row for the sample's areas (D6 DETERMINISM.md: the index carries run-level fields; under the clock guard they are
# fixed too, but the rows are what a later plan reuses)
NOT_COMPARED = ('cache/', '.git/', '.kpc-proof/', 'data/status/')
CACHE_DIR = {'us': 'cache/us', 'world': 'cache/world', 'ca': 'cache/ca'}
# KPC-Data paths a build reads besides the moved list (.github/kpc-moved.txt): the Recreation.gov saved copy (US build step) and the
# official pin fills (Nov 12). Each is laid in at the same path when the KPC-Data commit has it; its sha256 is recorded either way.
KPC_DATA_EXTRA = ['data/access-leads/keyed-pull-raw.json.gz', 'data/intake']
# the per-area outputs (also everything else the build wrote is compared: any changed file in the tree)
AREA_FILES = {'us': ['data/us-key/US-{a}.json', 'data/us-key/review/US-{a}.md', 'data/us-key/tracts/US-{a}.json'],
              'ca': ['data/ca-key/CA-{a}.json', 'data/ca-key/review/CA-{a}.md', 'data/ca-key/tracts/CA-{a}.json'],
              'world': ['data/world-key/{a}.json', 'data/world-key/review/{a}.md', 'data/world-key/tracts/{a}.json']}
AREA_DIRS = {'us': [], 'ca': [], 'world': ['data/world-bounds/{a}']}
AREA_GLOBS = {'us': ['data/outlines/US-{a}.geojson.gz', 'data/outlines/US-{a}.p*.geojson.gz'], 'ca': [], 'world': []}
INDEX = {'us': ('data/us-key/index.json', 'states'), 'ca': ('data/ca-key/index.json', 'provinces'), 'world': ('data/world-key/index.json', 'countries')}
UNBUILT = '_kpc_proof_not_built'
# the per-province switch of kpc_ca_key.py, when a tree has it (the D6 follow-up may add one): both trees must have it, else whole Canada
CA_PROVINCE_ENV = ('KPC_CA_PROVINCES', 'KPC_CA_ONLY_PROVINCES', 'PROVINCES')
# the builders' own date-from-input switches (D6); passed through when set in the job's environment (the clock shim stays on regardless)
# KPC_BUILD_DATE (D6, DETERMINISM.md): the one date of a run where the input carries none; set to the fixed instant's date for both sides
DATE_ENV = ('SOURCE_DATE_EPOCH',)
EMPTY = hashlib.sha256(b'').hexdigest()
GONE = hashlib.sha256(b'<no file>').hexdigest()   # a compared path that one side did not write: never equal to a real file's sha


def H(b): return hashlib.sha256(b if isinstance(b, bytes) else str(b).encode()).hexdigest()
def canon(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def git(repo, *a, text=True):
    r = subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=text)
    if r.returncode: raise RuntimeError(f"git {' '.join(a[:3])}: {(r.stderr or '')[:300]}")
    return r.stdout


def full_sha(repo, rev):
    s = git(repo, 'rev-parse', '--verify', f'{rev}^{{commit}}').strip()
    if not re.fullmatch(r'[0-9a-f]{40}', s): raise RuntimeError(f'{rev!r} is not a commit')
    return s


# ================================================================ the sample
def seeded(kind, old, new, pool, n=N_SEEDED):
    """n areas drawn from pool, seeded from (kind, old, new): the same commits give the same areas, on any machine."""
    rng = random.Random(int(H(f'{KINDS[kind]}\0{old}\0{new}'), 16))
    pool = sorted(set(pool))
    return sorted(rng.sample(pool, min(n, len(pool))))


def rule_sample(kind, old, new, universe, ca_mode='whole'):
    """{area: why} the rule asks for (fixed + seeded). Canada built whole = every province (one build writes them all)."""
    if kind == 'ca' and ca_mode != 'province':
        return {a: 'Canada builds as one unit: one build writes every province' for a in sorted(set(universe) | set(CA_PROVS))}
    out = dict(FIXED[kind])
    for a in seeded(kind, old, new, [a for a in universe if a not in FIXED[kind]]): out[a] = f'chosen from the commit shas (seed {KINDS[kind]}:{old[:7]}:{new[:7]})'
    return out


def universe_of(repo, rev, kind):
    sys.path.insert(0, str(HERE)); import kpc_area_hash as K
    return sorted(set(K.Kind(K.Tree(repo, rev), kind).area_list()) | set(universe_floor(kind)))


def own_moves(repo, kind, old, new):
    """{area: [part, ...]} whose OWN (non shared-code) parts differ between old and new (kpc_area_hash, design composition)."""
    sys.path.insert(0, str(HERE)); import kpc_area_hash as K
    _, pa = K.compute(repo, old, kind, 3, None, new, 'verdict')
    _, pb = K.compute(repo, new, kind, 3, None, old, 'verdict')
    out = {}
    for a in sorted(set(pa) | set(pb)):
        x, y = pa.get(a) or {}, pb.get(a) or {}
        m = sorted(n for n in set(x) | set(y) if x.get(n) != y.get(n) and not n.startswith(K.CODE_PARTS))
        if m: out[a] = m
    return out


def ca_mode_of(trees):
    """'province' when every tree's kpc_ca_key.py honours a per-province switch (CA_PROVINCE_ENV), else 'whole'."""
    names = []
    for t in trees:
        p = pathlib.Path(t) / '.github/scripts/kpc_ca_key.py'
        src = p.read_text(encoding='utf-8', errors='replace') if p.is_file() else ''
        names.append({n for n in CA_PROVINCE_ENV if re.search(r"environ(?:\.get)?[\[(]\s*['\"]" + n + r"['\"]", src)})
    common = set.intersection(*names) if names else set()
    return ('province', sorted(common)[0]) if common else ('whole', '')


def ca_mode_at(repo, revs):
    with_files = []
    for r in revs:
        try: with_files.append(git(repo, 'show', f'{r}:.github/scripts/kpc_ca_key.py'))
        except RuntimeError: with_files.append('')
    names = [{n for n in CA_PROVINCE_ENV if re.search(r"environ(?:\.get)?[\[(]\s*['\"]" + n + r"['\"]", s)} for s in with_files]
    common = set.intersection(*names) if names else set()
    return ('province', sorted(common)[0]) if common else ('whole', '')


def have_from_assets(kind, names):
    """The areas with a saved copy, from the boundary-cache asset names (None when no list was given)."""
    if names is None: return None
    rx = {'us': r'^US-([A-Z]{2})\.json\.gz$', 'world': r'^W-([A-Z]{2})\.json\.gz$', 'ca': r'^(CA)-ALL\.json\.gz$'}[kind]
    return sorted({m.group(1) for n in names for m in [re.match(rx, n.strip())] if m})


def make_sample(repo, kind, old, new, extras='', have=None):
    """The whole sample: {'rule': {a: why}, 'own': {a: [parts]}, 'extras': [...], 'claimed': [...], 'excluded': [...], 'universe': [...],
    'ca_mode': ...}. extras only ADD; an unknown extra is an error (never silently dropped)."""
    old, new = full_sha(repo, old), full_sha(repo, new)
    uni = universe_of(repo, new, kind)
    if have is not None and kind != 'ca':   # draw only from areas that HAVE a saved copy (an area without one cannot be built offline)
        uni = sorted((set(uni) & set(have)) | set(FIXED[kind]))
    cam, cav = ca_mode_at(repo, [old, new]) if kind == 'ca' else ('', '')
    rule = rule_sample(kind, old, new, uni, cam or 'whole')
    ex = [x.strip().upper() for x in re.split(r'[\s,]+', extras or '') if x.strip()]
    ex = [x[3:] if kind in ('us', 'ca') and x[:3] in ('US-', 'CA-') else x for x in ex]
    bad = [x for x in ex if x not in uni and not (kind == 'ca' and x in CA_PROVS)]
    if bad: raise SystemExit(f'::error title=Proof sample::not an area of the {kind} key: {" ".join(bad)} (the sample can only grow; nothing was run)')
    own = own_moves(repo, kind, old, new)
    why = dict(rule)
    for x in ex: why.setdefault(x, 'asked for by the person who started the proof')
    for a in own: why[a] = (why.get(a, '') + '; ' if a in why else '') + 'its own inputs moved (' + ', '.join(own[a])[:160] + '): rebuilt by the plan anyway, NOT in the claim'
    if kind == 'ca' and cam != 'province' and own:   # one build for all of Canada: a province with its own move is still built (all are)
        pass
    excluded = sorted(a for a in why if a in own)
    claimed = sorted(a for a in why if a not in own)
    return {'kind': kind, 'old': old, 'new': new, 'rule': rule, 'own': own, 'extras': ex, 'why': why, 'claimed': claimed, 'excluded': excluded,
            'universe': uni, 'have': sorted(have) if have is not None else None, 'ca_mode': cam, 'ca_switch': cav}


def print_sample(s, out=sys.stdout):
    out.write(f"Proof sample, {s['kind']} key, {s['old'][:12]} -> {s['new'][:12]}"
              + (f", Canada built {'per province (' + s['ca_switch'] + ')' if s['ca_mode'] == 'province' else 'whole (one build, every province)'}" if s['kind'] == 'ca' else '')
              + f": {len(s['claimed'])} area(s) in the claim, {len(s['excluded'])} built but not claimed\n\n| area | in the claim | why |\n|---|---|---|\n")
    for a in sorted(s['why']): out.write(f"| {a} | {'yes' if a in s['claimed'] else 'no'} | {s['why'][a].replace('|', '/')} |\n")


# ================================================================ the guard: network denied and counted, fixed clock (sitecustomize)
SHIM = r'''# KPC proof guard (written by kpc_key_proof.py; never committed). Network DENIED and COUNTED, clock FIXED, random seeded.
import os, sys
_LOG = os.environ.get('KPC_PROOF_NET_LOG') or '/dev/null'
def _note(kind, what):
    try:
        import traceback
        st = ' < '.join(f'{os.path.basename(f.filename)}:{f.lineno}' for f in reversed(traceback.extract_stack()[:-2][-8:]))
        with open(_LOG, 'a', encoding='utf-8') as f: f.write(f'{kind}\t{what}\t{st}\n')
    except Exception: pass
import socket as _s
class _Denied(OSError): pass
def _deny(kind):
    def f(*a, **k):
        what = a[1] if kind == 'sock' and len(a) > 1 else (a[0] if a else '')
        if kind == 'sock' and getattr(a[0], 'family', None) == getattr(_s, 'AF_UNIX', -1): return _real_connect(*a, **k)
        _note(kind, repr(what)[:200]); raise _Denied(f'network denied in a KPC proof run ({kind} {str(what)[:80]})')
    return f
_real_connect = _s.socket.connect
_s.socket.connect = _deny('sock'); _s.socket.connect_ex = _deny('sock')
for _n in ('create_connection', 'getaddrinfo', 'gethostbyname', 'gethostbyname_ex', 'gethostbyaddr', 'getnameinfo'):
    if hasattr(_s, _n): setattr(_s, _n, _deny(_n))
try:
    _FIX = float(os.environ['KPC_PROOF_FIXED'])
except Exception:
    _FIX = None
if _FIX is not None:
    import time as _t, datetime as _d, calendar as _c
    _rl, _rg, _rs, _rc, _ra = _t.localtime, _t.gmtime, _t.strftime, _t.ctime, _t.asctime
    _t.time = lambda: _FIX
    _t.time_ns = lambda: int(_FIX * 1e9)
    _t.localtime = lambda s=None: _rl(_FIX if s is None else s)
    _t.gmtime = lambda s=None: _rg(_FIX if s is None else s)
    _t.strftime = lambda fmt, tt=None: _rs(fmt, _rl(_FIX) if tt is None else tt)
    _t.ctime = lambda s=None: _rc(_FIX if s is None else s)
    _t.asctime = lambda tt=None: _ra(_rl(_FIX) if tt is None else tt)
    _RD, _RDT = _d.date, _d.datetime
    class _M(type):
        def __instancecheck__(cls, o): return isinstance(o, cls._real)
        def __subclasscheck__(cls, c): return issubclass(c, cls._real)
    class date(_RD, metaclass=_M):
        _real = _RD
        @classmethod
        def today(cls): return _RD.fromtimestamp(_FIX)
    class datetime(_RDT, metaclass=_M):
        _real = _RDT
        @classmethod
        def now(cls, tz=None): return _RDT.fromtimestamp(_FIX, tz)
        @classmethod
        def utcnow(cls): return _RDT.fromtimestamp(_FIX, _d.timezone.utc).replace(tzinfo=None)
        @classmethod
        def today(cls): return _RDT.fromtimestamp(_FIX)
    _d.date, _d.datetime = date, datetime
import random as _r
_r.seed(0)
'''


def write_shim(d):
    d = pathlib.Path(d); d.mkdir(parents=True, exist_ok=True)
    (d / 'sitecustomize.py').write_text(SHIM, encoding='utf-8')
    return d


# ================================================================ the trees
def is_code(path, rule_files=()):
    return path.startswith(CODE_PREFIXES) or path.endswith(CODE_SUFFIXES) or path in rule_files


def rule_files_at(tree):
    """Every rule file of every kind, as the tree's own kpc_key_freeze lists them (a scope / ready-areas JSON is code here too)."""
    src = pathlib.Path(tree) / '.github/scripts/kpc_key_freeze.py'
    if not src.is_file(): return set()
    p = subprocess.run([sys.executable, '-I', '-B', '-c', 'import json,runpy,sys; g=runpy.run_path(sys.argv[1]); '
                        'print(json.dumps(sorted({f for v in g["RULE_FILES"].values() for f in v} | {g["VERSION_FILE"]})))', str(src)],
                       capture_output=True, text=True, cwd=str(tree))
    try: return set(json.loads(p.stdout))
    except Exception: return set()  # noqa: BLE001


def export(repo, rev, dest):
    """The commit's files as a plain folder (no .git: both sides alike)."""
    dest = pathlib.Path(dest); dest.mkdir(parents=True)
    data = subprocess.run(['git', '-C', str(repo), 'archive', '--format=tar', rev], capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as t: t.extractall(dest, filter='tar') if hasattr(tarfile, 'data_filter') else t.extractall(dest)  # noqa: S202


def tree_map(root, skip_code=True, rule_files=()):
    """{relpath: sha256} of the files of a prepared tree (code paths left out when skip_code)."""
    root = pathlib.Path(root); out = {}
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.is_symlink(): continue
        rel = p.relative_to(root).as_posix()
        if rel.startswith(('.kpc-proof/',)) or '/__pycache__/' in '/' + rel: continue
        if skip_code and is_code(rel, rule_files): continue
        out[rel] = H(p.read_bytes())
    return out


def lay_inputs(tree, kind, inputs, kpc_data):
    """Saved copies into the cache folder, KPC-Data's moved paths and extras at their paths. Returns {input name: sha256}."""
    tree, rec = pathlib.Path(tree), {}
    cdir = tree / CACHE_DIR[kind]; cdir.mkdir(parents=True, exist_ok=True)
    src = pathlib.Path(inputs) if inputs else None
    if src and src.is_dir():
        for f in sorted(src.rglob('*')):
            if f.is_file():
                rel = f.relative_to(src).as_posix(); (cdir / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, cdir / rel); rec[f'boundary-cache:{rel}'] = H(f.read_bytes())
    if kpc_data:
        kd = pathlib.Path(kpc_data)
        moved = [l.strip() for l in (tree / '.github/kpc-moved.txt').read_text().splitlines()] if (tree / '.github/kpc-moved.txt').is_file() else []
        for p in [x for x in moved if x and not x.startswith('#')] + KPC_DATA_EXTRA:
            s = kd / p
            if s.is_dir():
                if (tree / p).exists(): shutil.rmtree(tree / p) if (tree / p).is_dir() else (tree / p).unlink()
                shutil.copytree(s, tree / p)
                for f in sorted(s.rglob('*')):
                    if f.is_file(): rec[f'kpc-data:{f.relative_to(kd).as_posix()}'] = H(f.read_bytes())
            elif s.is_file():
                (tree / p).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(s, tree / p); rec[f'kpc-data:{p}'] = H(s.read_bytes())
            else: rec[f'kpc-data:{p}'] = GONE
    return rec


def prepare(repo, work, old, new, kind, inputs, kpc_data):
    """Two plain trees: NEW = the new commit + inputs; OLD = a copy of NEW with every code path taken from the old commit."""
    work = pathlib.Path(work); tn, to = work / 'new', work / 'old'
    for t in (tn, to):
        if t.exists(): shutil.rmtree(t)
    export(repo, new, tn)
    rec = lay_inputs(tn, kind, inputs, kpc_data)
    shutil.copytree(tn, to, symlinks=True)
    rf = rule_files_at(tn) | rule_files_at_rev(repo, old)
    old_files = set(git(repo, 'ls-tree', '-r', '--name-only', '-z', old).split('\0')) - {''}
    new_files = set(git(repo, 'ls-tree', '-r', '--name-only', '-z', new).split('\0')) - {''}
    for p in sorted(new_files - old_files):
        if is_code(p, rf): (to / p).unlink(missing_ok=True)
    for p in sorted(old_files):
        if not is_code(p, rf): continue
        b = subprocess.run(['git', '-C', str(repo), 'show', f'{old}:{p}'], capture_output=True, check=True).stdout
        (to / p).parent.mkdir(parents=True, exist_ok=True); (to / p).write_bytes(b)
    return tn, to, rec, rf


def rule_files_at_rev(repo, rev):
    with __import__('tempfile').TemporaryDirectory() as td:
        try: b = git(repo, 'show', f'{rev}:.github/scripts/kpc_key_freeze.py')
        except RuntimeError: return set()
        (pathlib.Path(td) / '.github/scripts').mkdir(parents=True); (pathlib.Path(td) / '.github/scripts/kpc_key_freeze.py').write_text(b)
        return rule_files_at(td)


# ================================================================ building
def build_env(tree, kind, shim, netlog, fixed, extra=None):
    home = pathlib.Path(tree) / '.kpc-proof/home'; home.mkdir(parents=True, exist_ok=True)
    e = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(home), 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC',
         'PYTHONHASHSEED': '0', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(shim), 'PYTHONNOUSERSITE': '1',
         'KPC_PROOF_NET_LOG': str(netlog), 'KPC_PROOF_FIXED': str(fixed),
         # saved-copy-only, offline: the builders' own switch (GEO_CACHE_MODE=only = never the network, saved copies only)
         'GEO_CACHE_MODE': 'only', 'GEO_CACHE': CACHE_DIR[kind], 'KPC_MASTER_OWNS': '1', 'KPC_WORLD_PARTS': '0', 'KPC_HOST_GAP': '0',
         'http_proxy': 'http://127.0.0.1:9', 'https_proxy': 'http://127.0.0.1:9', 'HTTP_PROXY': 'http://127.0.0.1:9', 'HTTPS_PROXY': 'http://127.0.0.1:9',
         'NO_PROXY': '', 'GIT_TERMINAL_PROMPT': '0', 'PIP_NO_INDEX': '1'}
    e['KPC_BUILD_DATE'] = datetime.datetime.fromtimestamp(float(fixed), datetime.timezone.utc).strftime('%Y-%m-%d') if fixed not in (None, '', '-') else ''
    if kind == 'us': e.update({'GEO_DETAIL': '0.001', 'GEO_PAGE': '200', 'MINUTES': '600'})
    if kind == 'world': e.update({'PIN_JOIN': 'JP'})
    if kind == 'ca': e.update({'KPC_CA_HAND': 'cache/ca/hand'})   # the hand files (hand-CA.*.geojson.gz) are laid in with the saved copy
    for k in DATE_ENV + ('KPC_SAVED_ONLY_HOSTS',):
        if os.environ.get(k): e[k] = os.environ[k]
    e.update(extra or {})
    return e


def builder_steps(kind, area, ca_switch=''):
    py = sys.executable
    if kind == 'us':
        return [([py, '-B', '.github/scripts/kpc_us_key.py'], {'STATES': area}),
                ([py, '-B', '.github/scripts/kpc_outlines_from_key.py', '--cache', CACHE_DIR['us'], '--states', area], {}, 'optional')]
    if kind == 'world': return [([py, '-B', '.github/scripts/kpc_world_key.py'], {'COUNTRIES': area})]
    return [([py, '-B', '.github/scripts/kpc_ca_key.py'], {ca_switch: area} if ca_switch else {})]


def netns_prefix():
    """['unshare', '-rn'] when this machine lets us put the build in a namespace with no network at all (a second guard; the shim
    still counts). [] otherwise."""
    try:
        if subprocess.run(['unshare', '-rn', 'true'], capture_output=True, timeout=20).returncode == 0: return ['unshare', '-rn']
    except Exception: pass  # noqa: BLE001
    return []


def mark(tree, kind, areas, on):
    ip, rk = INDEX[kind]; p = pathlib.Path(tree) / ip
    if not p.is_file(): return list(areas) if not on else None
    raw = p.read_bytes()
    d = json.loads(raw); rows = d.setdefault(rk, {}); out = []
    for a in areas:
        if on: rows[a] = dict(rows.get(a) or {}, **{UNBUILT: 1})
        else:
            r = rows.get(a)
            if not isinstance(r, dict) or r.pop(UNBUILT, None) is not None: out.append(a)
            if r == {}: rows.pop(a)
    p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding='utf-8')
    return out


def build_side(tree, kind, units, shim, fixed, log, ns, ca_switch='', minutes=360):
    """Build each unit in this tree. units = [(label, [rows marked before and checked after], area given to the builder)].
    {label: {'rc', 'attempts', 'not_built'}}: a marked row the builder did not rewrite = not built."""
    res = {}
    for u, areas, arg in units:
        netlog = pathlib.Path(tree) / '.kpc-proof' / f'net-{u.replace(" ", "_")}.log'; netlog.parent.mkdir(parents=True, exist_ok=True); netlog.write_text('')
        rcs = []
        mark(tree, kind, areas, True)
        for step in builder_steps(kind, arg, ca_switch):
            cmd, env_x = step[0], step[1]
            if len(step) > 2 and not (pathlib.Path(tree) / cmd[2]).is_file(): continue
            env = build_env(tree, kind, shim, netlog, fixed, env_x)
            try:
                r = subprocess.run(ns + cmd, cwd=str(tree), env=env, capture_output=True, timeout=minutes * 60)
                rc = r.returncode; outb = r.stdout + r.stderr
            except subprocess.TimeoutExpired as e:
                rc = 124; outb = (e.stdout or b'') + (e.stderr or b'')
            with open(log, 'ab') as f: f.write(f'\n===== {pathlib.Path(tree).name} {u} {" ".join(cmd[2:])} exit {rc}\n'.encode() + outb[-200000:])
            rcs.append(rc)
        nb = mark(tree, kind, areas, False)
        att = [l for l in netlog.read_text(encoding='utf-8', errors='replace').splitlines() if l.strip()]
        res[u] = {'rc': max(rcs) if rcs else 2, 'rcs': rcs, 'attempts': len(att), 'attempt_lines': att[:5], 'not_built': nb}
    return res


# ================================================================ comparing
def area_paths(tree, kind, a):
    t = pathlib.Path(tree); out = [f.format(a=a) for f in AREA_FILES[kind]]
    for g in AREA_GLOBS[kind]:
        out += [p.relative_to(t).as_posix() for p in sorted(t.glob(g.format(a=a)))]
    return out


def dir_digest(root, rel):
    d = pathlib.Path(root) / rel
    if not d.is_dir(): return None
    return H(b''.join(p.relative_to(d).as_posix().encode() + b'\0' + H(p.read_bytes()).encode() + b'\n' for p in sorted(d.rglob('*')) if p.is_file()))


def file_sha(root, rel):
    p = pathlib.Path(root) / rel
    return H(p.read_bytes()) if p.is_file() else None


def outputs(tree, before, rule_files):
    """Every non-code path the builds changed, added or removed (inputs and scratch left out)."""
    now = tree_map(tree, True, rule_files)
    ch = {p for p in set(now) | set(before) if now.get(p) != before.get(p)}
    return {p for p in ch if not p.startswith(NOT_COMPARED) and not p.endswith('.log')}


def park_diff(to, tn, rel, limit=10):
    """Which parks differ between two key files (a short summary for the job summary)."""
    try:
        a = json.loads((pathlib.Path(to) / rel).read_text(encoding='utf-8')); b = json.loads((pathlib.Path(tn) / rel).read_text(encoding='utf-8'))
    except Exception: return ''  # noqa: BLE001
    pa, pb = (a.get('parks') or {}) if isinstance(a, dict) else {}, (b.get('parks') or {}) if isinstance(b, dict) else {}
    refs = sorted(r for r in set(pa) | set(pb) if pa.get(r) != pb.get(r))
    top = sorted(k for k in set(a) | set(b) if k != 'parks' and a.get(k) != b.get(k)) if isinstance(a, dict) and isinstance(b, dict) else []
    s = f'{len(refs)} park(s) differ' + (f": {' '.join(refs[:limit])}" + (' ...' if len(refs) > limit else '') if refs else '')
    return s + (f"; other fields: {' '.join(top[:8])}" if top else '')


def compare(to, tn, kind, areas, before_o, before_n, rf, area_only=False):
    """{path: [old sha, new sha]} for the areas' files (+ every other changed file unless area_only); folders as one digest."""
    files = {}
    for a in areas:
        for rel in sorted(set(area_paths(to, kind, a)) | set(area_paths(tn, kind, a))):
            files[rel] = [file_sha(to, rel) or GONE, file_sha(tn, rel) or GONE]
        for d in AREA_DIRS[kind]:
            rel = d.format(a=a)
            x, y = dir_digest(to, rel), dir_digest(tn, rel)
            if x or y: files[rel + '/'] = [x or GONE, y or GONE]
    ip, rk = INDEX[kind]
    if not area_only:
        dirs = tuple(d.format(a=a) + '/' for a in areas for d in AREA_DIRS[kind])
        for rel in sorted(outputs(to, before_o, rf) | outputs(tn, before_n, rf)):
            if rel in files or rel.startswith(dirs) or rel == ip: continue
            files[rel] = [file_sha(to, rel) or GONE, file_sha(tn, rel) or GONE]
    if True:   # the areas' own index rows (canonical JSON of the row)
        for a in areas:
            rows = []
            for t in (to, tn):
                try: rows.append(H(canon(((json.loads((pathlib.Path(t) / ip).read_text(encoding='utf-8')).get(rk) or {}).get(a)))))
                except Exception: rows.append(GONE)  # noqa: BLE001
            files[f'{ip}#{rk}.{a}'] = rows
    return files


def owner_of(rel, kind, areas):
    for a in areas:
        if rel in [f.format(a=a) for f in AREA_FILES[kind]] or any(re.fullmatch(g.format(a=a).replace('.', r'\.').replace('*', '.*'), rel) for g in AREA_GLOBS[kind]) \
                or any(rel.startswith(d.format(a=a) + '/') for d in AREA_DIRS[kind]) or rel.endswith(f'#{INDEX[kind][1]}.{a}'):
            return a
    return 'shared'


# ================================================================ the record
def inputs_id(inputs): return H(canon(inputs))


def record_problems(rec, kind, composition, code_hash_now=None):
    """What a VALID record must also satisfy, besides kpc_area_hash.proof_valid()'s own checks (called from there; any problem = no
    proof = full rebuild). [] = none. kind = us | ca | world (or the key name)."""
    bad = []
    kind = {v: k for k, v in KINDS.items()}.get(kind, kind)
    if not isinstance(rec, dict): return ['not a record']
    if kind not in KINDS: return [f'no proof job for kind {kind}']
    if rec.get('writer') != WRITER: bad.append(f'not written by {WRITER}')
    if rec.get('composition') != composition: bad.append(f"composition {rec.get('composition')!r} is not the current {composition!r} (stale)")
    old, new = str(rec.get('old_commit') or ''), str(rec.get('new_commit') or '')
    if not (re.fullmatch(r'[0-9a-f]{40}', old) and re.fullmatch(r'[0-9a-f]{40}', new)): bad.append('old / new commit not recorded as full shas')
    uni = rec.get('universe') if isinstance(rec.get('universe'), list) else []
    have = rec.get('have')
    floor = set(universe_floor(kind)) & (set(have) if isinstance(have, list) and kind != 'ca' else set(universe_floor(kind)))
    lack = sorted((floor | (set(FIXED[kind]) if kind != 'ca' else set())) - set(uni))
    if lack: bad.append(f"universe lacks {' '.join(lack[:8])}")
    if kind != 'ca' and len(set(uni) - set(FIXED[kind])) < N_SEEDED: bad.append(f'universe too small to draw {N_SEEDED} areas from the commit shas')
    mode = 'province' if kind == 'ca' and rec.get('ca_mode') == 'province' else 'whole'
    covered = set(rec.get('sample') or []) | set(rec.get('excluded') or {})
    need = set(rule_sample(kind, old, new, uni, mode)) if not bad else set()
    short = sorted(need - covered)
    if short: bad.append(f"sample smaller than the rule: {' '.join(short[:10])} missing")
    inp = rec.get('inputs')
    if not isinstance(inp, dict) or not inp or not all(re.fullmatch(r'[0-9a-f]{64}', str(v)) for v in inp.values()): bad.append('no inputs recorded')
    elif rec.get('inputs_id') != inputs_id(inp): bad.append('the inputs list does not match its id (the record was changed)')
    elif not (rec.get('inputs_id_old') == inputs_id(dict(inp, tree=rec.get('tree_inputs_old'))) and rec.get('inputs_id_new') == inputs_id(dict(inp, tree=rec.get('tree_inputs_new')))
              and rec.get('inputs_id_old') == rec.get('inputs_id_new') and re.fullmatch(r'[0-9a-f]{64}', str(rec.get('tree_inputs_old') or ''))):
        bad.append('inputs differ (old and new were not given the same inputs)')
    files = rec.get('files') if isinstance(rec.get('files'), dict) else {}
    for a in rec.get('sample') or []:
        k = AREA_FILES[kind][0].format(a=a)
        if k not in files or GONE in files[k]: bad.append(f'{a}: its key file was not written by both builds'); break
    if any(GONE in (v or []) for v in files.values()): bad.append('a compared file was written by one build only')
    if not isinstance(rec.get('fixed_instant'), str) or not rec.get('fixed_instant'): bad.append('no fixed clock recorded')
    if rec.get('network_attempts') != 0 or any((x or {}).get('attempts') for x in (rec.get('builds') or {}).values()): bad.append('a build tried the network')
    if code_hash_now and rec.get('to') != code_hash_now: bad.append('to is not the current code hash (stale)')
    return bad


def proof_id(kind, frm, to, run_id):
    return re.sub(r'[^A-Za-z0-9._-]', '-', f"{kind}-{frm}-{to}-{run_id or 'local'}")[:80]


def run_proof(repo, kind, old, new, inputs, kpc_data, out, extras='', work=None, run_id=None, minutes=360, use_ns=True, summary=None, have=None):
    sys.path.insert(0, str(HERE)); import kpc_area_hash as K
    repo = pathlib.Path(repo).resolve(); out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    s = make_sample(repo, kind, old, new, extras, have)
    old, new = s['old'], s['new']
    work = pathlib.Path(work or (out.parent / '.kpc-proof-work')); work.mkdir(parents=True, exist_ok=True)
    tn, to, inp_rec, rf = prepare(repo, work, old, new, kind, inputs, kpc_data)
    frm, tohash = K.code_hash(to, kind), K.code_hash(tn, kind)
    before_o, before_n = tree_map(to, True, rf), tree_map(tn, True, rf)
    tid_o, tid_n = H(canon(before_o)), H(canon(before_n))
    if tid_o != tid_n:
        raise SystemExit(f'::error title=Proof inputs::the two prepared trees do not hold the same non-code files ({len(set(before_o.items()) ^ set(before_n.items()))} differ): no proof')
    if s['kind'] == 'ca' and s['ca_mode'] == 'province': cam, cav = 'province', s['ca_switch']
    elif kind == 'ca': cam, cav = 'whole', ''
    else: cam, cav = '', ''
    if kind == 'ca':   # what the trees really honour (the same answer as ca_mode_at, read from the prepared files)
        cam2, cav2 = ca_mode_of([to, tn])
        if (cam2, cav2) != (cam, cav): raise SystemExit('::error title=Proof sample::the Canada build mode differs between the git view and the prepared trees: no proof')
    claimed, excluded = s['claimed'], s['excluded']
    units = (['ALL'] if kind == 'ca' and cam != 'province' else claimed)
    fixed = int(git(repo, 'show', '-s', '--format=%ct', new).strip())
    fixed_iso = datetime.datetime.fromtimestamp(fixed, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    shim = write_shim(work / 'shim'); ns = netns_prefix() if use_ns else []
    log = out / 'build.log'; log.write_bytes(b'')
    if kind == 'ca' and cam != 'province':   # whole Canada: one build; every province row it should rewrite is marked
        rows = sorted(set(json.loads((tn / INDEX['ca'][0]).read_text(encoding='utf-8')).get('provinces') or {})) if (tn / INDEX['ca'][0]).is_file() else []
        u = [('CA-ALL', rows, '')]
    else: u = [(a, [a], a) for a in claimed]
    b_o = build_side(to, kind, u, shim, fixed, log, ns, cav, minutes); b_n = build_side(tn, kind, u, shim, fixed, log, ns, cav, minutes)
    files = compare(to, tn, kind, claimed, before_o, before_n, rf)
    builds = {}
    for u in b_o:
        builds[u] = {'old_exit': b_o[u]['rc'], 'new_exit': b_n[u]['rc'], 'attempts': b_o[u]['attempts'] + b_n[u]['attempts'],
                     'not_built': sorted(set(b_o[u]['not_built'] or []) | set(b_n[u]['not_built'] or []))}
    # the areas whose own inputs moved: built after the claim was compared (so they cannot touch it); data-only moves are strict
    ex_rec = {}
    if excluded and not (kind == 'ca' and cam != 'province'):
        u2 = [(a, [a], a) for a in excluded]
        bo2 = build_side(to, kind, u2, shim, fixed, log, ns, cav, minutes); bn2 = build_side(tn, kind, u2, shim, fixed, log, ns, cav, minutes)
        for a in excluded:
            f2 = compare(to, tn, kind, [a], before_o, before_n, rf, area_only=True)
            code_moved = any(p.startswith('code-area:') for p in s['own'].get(a, []))
            same = all(x == y for x, y in f2.values())
            ex_rec[a] = {'why': s['why'][a], 'moved': s['own'][a], 'files': f2, 'same': same, 'attempts': bo2[a]['attempts'] + bn2[a]['attempts'],
                         'old_exit': bo2[a]['rc'], 'new_exit': bn2[a]['rc'],
                         'verdict': 'same' if same else ('differs: expected, its own code table moved' if code_moved else 'differs with the same inputs: the shared code changed it')}
    elif excluded:
        for a in excluded: ex_rec[a] = {'why': s['why'][a], 'moved': s['own'][a], 'verdict': 'built in the one Canada build; its files are not in the claim'}
        for a in excluded:
            for rel in list(files):
                if owner_of(rel, kind, [a]) == a: ex_rec[a].setdefault('files', {})[rel] = files.pop(rel)
    attempts = sum(b['attempts'] for b in builds.values()) + sum(x.get('attempts', 0) for x in ex_rec.values())
    problems = []
    if attempts: problems.append(f'{attempts} network attempt(s): a proof run must make none (see build.log / the attempts below)')
    for u, b in sorted(builds.items()):
        if b['old_exit'] or b['new_exit']: problems.append(f"{u}: a build stopped (old exit {b['old_exit']}, new exit {b['new_exit']})")
        if b['not_built']: problems.append(f"{u}: not built by one side ({' '.join(b['not_built'])}): no saved copy, or the build skipped it")
    for a in claimed:
        k = AREA_FILES[kind][0].format(a=a)
        if GONE in files.get(k, [GONE]): problems.append(f'{a}: its key file was not written by both builds')
    diff = {p: v for p, v in files.items() if v[0] != v[1]}
    for p in sorted(diff)[:30]:
        problems.append(f"differs: {p} (area {owner_of(p, kind, claimed)})" + (f" - {park_diff(to, tn, p)}" if p.endswith('.json') and owner_of(p, kind, claimed) != 'shared' else ''))
    for a, x in sorted(ex_rec.items()):
        if x.get('verdict', '').startswith('differs with the same inputs'): problems.append(f'{a} (own data moved, not claimed): {x["verdict"]}')
    result = 'pass' if not problems else 'fail'
    pid = proof_id(kind, frm, tohash, run_id or os.environ.get('GITHUB_RUN_ID'))
    tools = {'python': sys.version.split()[0], 'platform': sys.platform}
    for m in ('shapely', 'pyproj', 'shapefile', 'pykakasi'):
        p = subprocess.run([sys.executable, '-I', '-c', f'import {m}; print(getattr({m}, "__version__", "?"))'], capture_output=True, text=True)
        tools[m] = p.stdout.strip() if p.returncode == 0 else 'not installed'
    kd_commit = ''
    if kpc_data and (pathlib.Path(kpc_data) / '.git').exists():
        try: kd_commit = git(kpc_data, 'rev-parse', 'HEAD').strip()
        except RuntimeError: kd_commit = ''
    inp = dict(sorted(inp_rec.items()))
    inp['kpc-data-commit'] = H(kd_commit or 'none'); inp['links-new-commit'] = H(new)
    iid = inputs_id(inp)
    # each side's inputs = the recorded inputs + the digest of that side's prepared non-code files (cache folder included): equal ids
    # mean both code versions were given the same bytes
    iid_o, iid_n = inputs_id(dict(inp, tree=tid_o)), inputs_id(dict(inp, tree=tid_n))
    rec = {'format': RECORD_FORMAT, 'id': pid, 'kind': KINDS[kind], 'from': frm, 'to': tohash, 'result': result,
           'old_commit': old, 'new_commit': new, 'sample': claimed, 'excluded': ex_rec, 'why': {a: s['why'][a] for a in sorted(s['why'])},
           'rule_sample': sorted(s['rule']), 'extras': s['extras'], 'universe': s['universe'], 'have': s['have'], 'ca_mode': cam or None, 'ca_switch': cav or None,
           'files': files, 'network_attempts': attempts, 'builds': builds, 'problems': problems,
           'composition': K.COMPOSITION, 'writer': WRITER, 'inputs': inp, 'inputs_id': iid, 'inputs_id_old': iid_o, 'inputs_id_new': iid_n,
           'tree_inputs_old': tid_o, 'tree_inputs_new': tid_n, 'kpc_data_commit': kd_commit,
           'fixed_instant': fixed_iso, 'fixed_from': 'the new commit\'s committer time', 'clock_shim': 'time.time/time_ns/localtime/gmtime/strftime/ctime/asctime, datetime.date.today, datetime.datetime.now/utcnow/today; random.seed(0)',
           'clock_not_patched': 'time.monotonic / perf_counter (deadlines and pacing only); file mtimes (os.stat); C code outside Python; other processes (no builder starts one but pip, which the network guard stops)',
           'env': {k: v for k, v in build_env(work / 'x', kind, shim, '-', fixed).items() if k not in ('PATH', 'HOME', 'PYTHONPATH', 'KPC_PROOF_NET_LOG')},
           'netns': bool(ns), 'tools': tools,
           'run': {'id': os.environ.get('GITHUB_RUN_ID'), 'attempt': os.environ.get('GITHUB_RUN_ATTEMPT'), 'repository': os.environ.get('GITHUB_REPOSITORY'),
                   'workflow_sha': os.environ.get('GITHUB_SHA'), 'actor': os.environ.get('GITHUB_ACTOR')},
           'written': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'signing': 'UNSIGNED. Counts only after the owner adds the stamp entry (stamp-entry.json, with approved_by and approved_date) to .github/no-result-change.json in a reviewed PR together with this file.'}
    if result == 'pass':
        bad = record_problems(rec, kind, K.COMPOSITION)
        if bad: rec['result'] = result = 'fail'; rec['problems'] = problems = [f'record check: {b}' for b in bad]
    # written last and whole (a run stopped before this line leaves no record)
    rp = out / PROOF_DIR / f'{pid}.json'; rp.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(rec, indent=1, sort_keys=True, ensure_ascii=False) + '\n'
    if len(body.encode()) > 1_000_000: raise SystemExit('::error title=Proof record::over 1 MB: not written')
    tmp = rp.with_suffix('.tmp'); tmp.write_text(body, encoding='utf-8'); tmp.replace(rp)
    if result == 'pass':
        entry = {'id': pid, 'kind': KINDS[kind], 'from': frm, 'to': tohash, 'claim': 'no-result-change', 'proof': pid, 'approved_by': '', 'approved_date': '',
                 'old_commit': old, 'new_commit': new}
        (out / 'stamp-entry.json').write_text(json.dumps(entry, indent=1) + '\n', encoding='utf-8')
    (out / 'result.txt').write_text(f'{result}\n{pid}\n', encoding='utf-8')
    t = summary_md(rec, s)
    (out / 'summary.md').write_text(t, encoding='utf-8')
    dest = summary or os.environ.get('GITHUB_STEP_SUMMARY')
    if dest: open(dest, 'a', encoding='utf-8').write(t + '\n')
    return rec


def summary_md(rec, s):
    L = [f"## Key proof ({rec['kind']}): **{rec['result'].upper()}**", '',
         f"Code hash {rec['from']} -> {rec['to']} (commits {rec['old_commit'][:12]} -> {rec['new_commit'][:12]}); proof id `{rec['id']}`; "
         f"fixed clock {rec['fixed_instant']}; network attempts {rec['network_attempts']}" + ('; builds ran in a namespace with no network' if rec['netns'] else '; no network namespace on this runner (the in-Python guard alone)') + '.', '']
    if rec['result'] == 'pass':
        L += [f"Every compared file is byte-identical ({len(rec['files'])} files, {len(rec['sample'])} areas in the claim). The record is UNSIGNED: "
              'the owner signs by adding stamp-entry.json (approved_by, approved_date) to .github/no-result-change.json, with the record, in a reviewed PR.', '']
    else:
        L += ['No valid stamp: the plan rebuilds every area of this key after this change. First problems:', ''] + [f'- {p}' for p in rec['problems'][:15]] + ['']
    L += ['| area | in the claim | why |', '|---|---|---|'] + [f"| {a} | {'yes' if a in rec['sample'] else 'no'} | {str(w).replace('|', '/')} |" for a, w in sorted(rec['why'].items())]
    return '\n'.join(L) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', choices=['sample', 'run', 'check', 'shim'])
    ap.add_argument('args', nargs='*')
    ap.add_argument('--repo', default=str(REPO)); ap.add_argument('--old', default=''); ap.add_argument('--new', default='')
    ap.add_argument('--areas', default='', help='extra areas to ADD to the sample (never removes one)')
    ap.add_argument('--inputs', default=None, help='run: the saved copies (boundary-cache assets), laid into the cache folder')
    ap.add_argument('--kpc-data', default=None, help='run: a KPC-Data checkout at ONE commit (moved paths, pin fills)')
    ap.add_argument('--out', default=None); ap.add_argument('--work', default=None); ap.add_argument('--json', default=None)
    ap.add_argument('--assets', default=None, help='a file with the boundary-cache asset names (one per line): seeded areas come only from areas with a saved copy')
    ap.add_argument('--minutes', type=int, default=360); ap.add_argument('--no-netns', action='store_true'); ap.add_argument('--record', default=None)
    a = ap.parse_args(argv)
    if a.cmd == 'shim':
        print(write_shim(a.args[0] if a.args else '.') / 'sitecustomize.py'); return 0
    kind = (a.args[0] if a.args else '').strip().lower()
    if kind not in KINDS: ap.error('KIND must be us, ca or world'); return 2
    if a.cmd == 'check':
        sys.path.insert(0, str(HERE)); import kpc_area_hash as K
        rec = json.loads(pathlib.Path(a.record).read_text(encoding='utf-8'))
        bad = record_problems(rec, kind, K.COMPOSITION)
        for b in bad: print(f'PROBLEM {b}')
        print('record check: ' + ('OK' if not bad else f'{len(bad)} problem(s)')); return 1 if bad else 0
    if not a.old or not a.new: ap.error('--old and --new are needed'); return 2
    have = have_from_assets(kind, pathlib.Path(a.assets).read_text().split()) if a.assets else None
    if a.cmd == 'sample':
        s = make_sample(a.repo, kind, a.old, a.new, a.areas, have)
        print_sample(s)
        if a.json: pathlib.Path(a.json).write_text(json.dumps(s, indent=1, sort_keys=True), encoding='utf-8')
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f: print_sample(s, f)
        return 0
    if a.cmd == 'run':
        if not a.out: ap.error('--out is needed'); return 2
        rec = run_proof(a.repo, kind, a.old, a.new, a.inputs, a.kpc_data, a.out, a.areas, a.work, None, a.minutes, not a.no_netns, None, have)
        print(f"PROOF {rec['result'].upper()} {rec['id']}: {len(rec['sample'])} area(s), {len(rec['files'])} file(s), {rec['network_attempts']} network attempt(s)")
        for p in rec['problems'][:20]: print(f'::error title=Key proof::{p}')
        return 0 if rec['result'] == 'pass' else 1
    return 2


if __name__ == '__main__':
    sys.exit(main())
