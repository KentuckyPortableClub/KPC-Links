"""Shared offline harness for the Nov 12 pin-fill and Japan A10 crosswalk tests (KPC owner, 2026-11-12). Not a test file (the full suite runs
tests/test_*.py only). Every socket is refused before anything runs, in this process and in the builder it starts (zero network).
  ca_build(parks, recs, env, src=None)      the real kpc_ca_key.py (or a given source text) on a saved copy of `recs`, GEO_CACHE_MODE=only,
                                            in a temp folder; returns {relative path: bytes} of every file it wrote under data/
  world_build(countries, parks, recs, env, src=None, extra=None)   the same for kpc_world_key.py (parks / recs keyed by country)
  strip_hook(text, marker)                  the builder's source WITHOUT one of this patch's hooks (the 'build without this commit')
The fixtures are SYNTHETIC: real park refs and names, made-up rectangles near the official pins."""
import gzip, json, os, pathlib, shutil, socket, subprocess, sys, tempfile


def _no_net(*a, **k): raise RuntimeError('network refused in this test')


socket.socket.connect = _no_net; socket.create_connection = _no_net; socket.getaddrinfo = _no_net

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.github/scripts'
if str(SCRIPTS) not in sys.path: sys.path.insert(0, str(SCRIPTS))
FX = ROOT / 'tests/fixtures/official_pins_nov12'
PINS_FILE = FX / 'official-pins-nov12.json'
DATA = next((pathlib.Path(d) for d in (os.environ.get('KPC_DATA'), os.environ.get('DATA'), ROOT.parent / 'kpc-data', ROOT.parent / 'kpcdata', ROOT.parent / 'data')
             if d and (pathlib.Path(d) / 'data/parkinfo/CA.json').is_file()), None)
DEAD = 'http://127.0.0.1:9'
RUNNER = ("import socket, runpy, sys\n"
          "def _n(*a, **k): raise RuntimeError('network refused in this test')\n"
          "socket.socket.connect = _n; socket.create_connection = _n; socket.getaddrinfo = _n\n"
          "sys.path.insert(0, sys.argv[2]); sys.argv = [sys.argv[1]]; runpy.run_path(sys.argv[0], run_name='__main__')\n")


def ring(la, lo, d=.01):
    return [[lo - d, la - d], [lo + d, la - d], [lo + d, la + d], [lo - d, la + d], [lo - d, la - d]]


def strip_hook(text, start, end):
    """text without the lines from the one holding `start` to the one holding `end` (both included); the hook must be there once."""
    lines = text.split('\n')
    i = [n for n, l in enumerate(lines) if start in l]; j = [n for n, l in enumerate(lines) if end in l]
    if len(i) != 1 or len(j) != 1 or j[0] < i[0]: raise AssertionError(f'hook markers not found once: {start!r} {end!r}')
    return '\n'.join(lines[:i[0]] + lines[j[0] + 1:])


def _run(t, script_text, name, env):
    s = t / '.github/scripts'; s.mkdir(parents=True, exist_ok=True)
    for f in SCRIPTS.glob('*.py'):
        if f.name != name: shutil.copy(f, s / f.name)
    (s / name).write_text(script_text, encoding='utf-8')
    e = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', KPC_TRACT_STORE='0', HTTP_PROXY=DEAD, HTTPS_PROXY=DEAD, http_proxy=DEAD, https_proxy=DEAD,
             ALL_PROXY=DEAD, NO_PROXY='', no_proxy='', GITHUB_STEP_SUMMARY='', **env)
    for k in [k for k, v in e.items() if v is None]: e.pop(k)
    r = subprocess.run([sys.executable, '-B', '-c', RUNNER, str(s / name), str(s)], cwd=t, env=e, capture_output=True, text=True, timeout=600)
    out = {}
    for f in sorted((t / 'data').rglob('*')):
        if f.is_file() and 'parkinfo' not in f.parts: out[str(f.relative_to(t))] = f.read_bytes()
    return r, out


def ca_build(parks, recs, env, src=None, ca_files=None):
    t = pathlib.Path(tempfile.mkdtemp(prefix='kpc-pinfill-ca-'))
    try:
        (t / 'data/ca-key').mkdir(parents=True); (t / 'data/parkinfo').mkdir(parents=True); (t / 'cache/ca').mkdir(parents=True)
        pk = t / 'data/parkinfo/CA.json'; pk.write_text(json.dumps({'parks': parks}, ensure_ascii=False), encoding='utf-8')
        for rel, v in (ca_files or {}).items(): (t / rel).parent.mkdir(parents=True, exist_ok=True); (t / rel).write_text(v, encoding='utf-8')
        rows = [dict(r) for r in recs]
        with gzip.open(t / 'cache/ca/CA-ALL.json.gz', 'wt', encoding='utf-8') as f:
            json.dump({'saved': '2026-11-12', 'detail': 0.02, 'recs': rows}, f)
        before = pk.read_bytes()
        r, out = _run(t, src if src is not None else (SCRIPTS / 'kpc_ca_key.py').read_text(encoding='utf-8'), 'kpc_ca_key.py',
                      dict(env, GEO_CACHE_MODE='only', GEO_CACHE=str(t / 'cache/ca')))
        out['_parkinfo_unchanged'] = pk.read_bytes() == before
        return r, out
    finally:
        shutil.rmtree(t, ignore_errors=True)


def world_build(countries, parks, recs, env, src=None, extra=None):
    t = pathlib.Path(tempfile.mkdtemp(prefix='kpc-pinfill-w-'))
    try:
        (t / 'data/world-key').mkdir(parents=True); (t / 'data/parkinfo').mkdir(parents=True)
        for rel in ('data/retired-refs.json', 'data/world-key/extra-layers.json', 'data/world-key/sheet-countries.json', 'data/world-key/eea-designations.json',
                    'data/world-key/area-tables.json'):   # Nov 12 (stacked on D6): the per-country tables are a data file now
            if (ROOT / rel).is_file(): (t / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(ROOT / rel, t / rel)
        (t / 'data/world-key/overrides.json').write_text('{"parks": {}}', encoding='utf-8')
        for rel, v in (extra or {}).items(): (t / rel).parent.mkdir(parents=True, exist_ok=True); (t / rel).write_bytes(v if isinstance(v, bytes) else v.encode('utf-8'))
        before = {}
        for cc in countries:
            p = t / f'data/parkinfo/{cc}.json'; p.write_text(json.dumps({'parks': parks[cc]}, ensure_ascii=False), encoding='utf-8'); before[cc] = p.read_bytes()
            (t / 'cache/world').mkdir(parents=True, exist_ok=True)
            with gzip.open(t / f'cache/world/W-{cc}.json.gz', 'wt', encoding='utf-8') as f:
                json.dump({'cc': cc, 'saved': '2026-11-12', 'detail': 0.002, 'thin': 250, 'recs': recs[cc]}, f, ensure_ascii=False)
        r, out = _run(t, src if src is not None else (SCRIPTS / 'kpc_world_key.py').read_text(encoding='utf-8'), 'kpc_world_key.py',
                      dict(env, COUNTRIES=' '.join(countries), GEO_CACHE_MODE='only', GEO_CACHE=str(t / 'cache/world')))
        out['_parkinfo_unchanged'] = all((t / f'data/parkinfo/{cc}.json').read_bytes() == b for cc, b in before.items())
        return r, out
    finally:
        shutil.rmtree(t, ignore_errors=True)
