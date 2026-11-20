#!/usr/bin/env python3
"""Job 9 (R6; outside review F10, 'a missing layer is only a notice', about line 1070; DRAFT, switch KPC_HOLD_ON_PASS_ERROR, OFF):
(1) a zipped-shapefile layer that cannot be read (zip_state's except, the review's line) and (2) a map layer the builder cannot
find (resolve() raises). Switch OFF = the same notice, word for word, and the next layer is read; switch ON = the state is held
(kpc_key_rules.PassError, so run() fails for it: FAILED, no key file, saved copy kept).
Runs on INVENTED data: the builder's own zip_state, and its resolve lines, taken from the source, with stand-ins that raise
(an unreadable download; a layer that answers 404). No shapely, no network.
Run:  python3 tests/test_hold_layer_not_found_nov20.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import pathlib, sys, textwrap
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

SRC = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
a = SRC.index('            try: url, nf, af, oidf = resolve(pre, url, nf, af)\n')
b = SRC.index("layer not found ({e})'); continue\n", a) + len("layer not found ({e})'); continue\n")
body = textwrap.dedent(SRC[a:b])
code = 'def f():\n    for pre in LAYERS:\n        url, nf, af = "u", "n", ""\n' + textwrap.indent(body, '        ') + '        DONE.append(pre)\n'

def run(hold):
    out, done = [], []
    class StubKR:
        PassError = KR.PassError
        hold_state = staticmethod(getattr(KR, 'hold_state', lambda *a: None))
        @staticmethod
        def on(name, env=None, area=None, path=None): return hold and name == 'KPC_HOLD_ON_PASS_ERROR' and area == 'NH'
    def resolve(pre, url, nf, af):
        if pre == 'sgnhz': raise RuntimeError('HTTP 404')
        return url, nf, af, 'OBJECTID'
    g = {'LAYERS': ['sgnha', 'sgnhz', 'sgnhb'], 'DONE': done, 'notice': lambda t, m: out.append((t, m)), 'st': 'NH',
         'label': 'NH test layer', 'resolve': resolve, 'KR': StubKR}
    exec(compile(code, 'kpc_us_key.py (layer not found)', 'exec'), g)
    try: g['f'](); return out, done, None
    except Exception as x: return out, done, x  # noqa: BLE001

o, d, x = run(False)
check(x is None and o == [('US key NH', 'NH test layer layer not found (HTTP 404)')] and d == ['sgnha', 'sgnhb'],
      f'switch OFF: the same notice as before and the other layers are still read ({o}, {d})')
o, d, x = run(True)
check(isinstance(x, KR.PassError) and 'NH' in str(x) and 'layer not found' in str(x) and d == ['sgnha'],
      f'switch ON: the state is held (PassError names the state and the layer), nothing after it is read ({x})')
check(issubclass(KR.PassError, Exception), "PassError is an Exception: the builder's per-state except names the state FAILED and keeps its saved copy")

# (1) zip_state, the function itself from the source, with a stand-in download that fails for one layer
z0 = SRC.index('def zip_state(st, have):\n'); z1 = SRC.index('\nLAYERS_ZIP = {}', z0)
def run_zip(hold):
    out = []
    class StubKR:
        PassError = KR.PassError
        hold_state = staticmethod(getattr(KR, 'hold_state', lambda *a: None))
        @staticmethod
        def on(name, env=None, area=None, path=None): return hold and name == 'KPC_HOLD_ON_PASS_ERROR' and area == 'NH'
    def opener(req, t): raise OSError('download failed')
    import urllib.request
    g = {'SZ_US': [('zpa', 'https://gis.example.gov/a.zip', ['NAME'], [], 'NH zip layer', 'STAT', {'NH'}, {})],
         'saved_only': lambda u: False, 'ZIPC': {}, 'checked_open': opener, 'urllib': urllib, 'notice': lambda t, m: out.append((t, m)),
         'SAVED_ONLY_SKIPPED': {}, 'KR': StubKR}
    exec(compile(SRC[z0:z1], 'kpc_us_key.py (zip_state)', 'exec'), g)
    try: return g['zip_state']('NH', {}), out, None
    except Exception as x: return None, out, x  # noqa: BLE001
try: import shapefile, pyproj  # noqa: F401
except ImportError: shapefile = None
r, o, x = run_zip(False)
check(x is None and r == [] and len(o) == 1 and o[0][1].startswith('NH zip layer not read ('), f'zip, switch OFF: the same notice as before, no raise ({o})')
r, o, x = run_zip(True)
check(isinstance(x, KR.PassError) and 'NH' in str(x) and 'NH zip layer not read' in str(x) and o == [], f'zip, switch ON: the state is held, no notice ({x})')
print('note: pyshp / pyproj ' + ('present: the download failed' if shapefile else 'missing here: the import failed') + ', both reach the same except', flush=True)

n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
