#!/usr/bin/env python3
"""Job 9 (R6; outside review F10, 'a state read up to 3% short of the last one is accepted'; DRAFT, switch KPC_HOLD_ON_PASS_ERROR,
OFF): after a full read in which a layer read FAILED, the US key builder used to build (and save) the state from that read when
there was no saved copy, or when the read was under 3% short of it. Switch OFF = exactly that, as before. Switch ON = the state
is held (kpc_key_rules.PassError: FAILED, no key file, saved copy kept). A read more than 3% short still falls back to the saved
copy either way (nothing dropped), and a read with no failed layer is untouched.
Runs on INVENTED data: the builder's own lines, taken from the source, with invented record lists. No shapely.
Run:  python3 tests/test_hold_failed_read_nov20.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import pathlib, sys, textwrap
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

SRC = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
a = SRC.index('        old = load_cache(st) if st in FAILED_READ else None\n')
b = SRC.index('save_cache(st, recs, seen)\n', SRC.index("        elif CMODE in ('use', 'refresh')", a)) + len('save_cache(st, recs, seen)\n')
code = 'def f():\n    recs, seen, used_detail = RECS, {}, 1\n' + textwrap.indent(textwrap.dedent(SRC[a:b]), '    ') + '    return recs\n'

def run(hold, n_read, n_saved, failed=True):
    out, saved = [], []
    g = {'st': 'NH', 'FAILED_READ': {'NH'} if failed else set(), 'RECS': list(range(n_read)), 'CMODE': 'refresh', 'CACHE_USED': [],
         'load_cache': lambda s: (list(range(n_saved)), {}, 1) if n_saved else None, 'save_cache': lambda s, r, se: saved.append(len(r)),
         'cache_file': lambda s: type('P', (), {'exists': lambda self: bool(n_saved)})(), 'notice': lambda t, m: out.append(m),
         'KR': KR, '_kr': lambda n: hold and n == 'KPC_HOLD_ON_PASS_ERROR'}
    exec(compile(code, 'kpc_us_key.py (failed read)', 'exec'), g)
    try: r = g['f'](); return len(r), saved, out, None
    except Exception as x: return None, saved, out, x  # noqa: BLE001

for hold in (False, True):
    w = 'ON' if hold else 'OFF'
    r, s, o, x = run(hold, 980, 1000)
    if hold: check(isinstance(x, KR.PassError) and 'NH' in str(x) and s == [], f'{w}: a failed read 2% short of the saved copy holds the state, nothing saved ({x})')
    else: check(x is None and r == 980 and s == [980], f'{w}: a failed read 2% short is built from and saved, as before ({r}, {s})')
    r, s, o, x = run(hold, 500, 0)
    if hold: check(isinstance(x, KR.PassError) and 'no saved copy' in str(x) and s == [], f'{w}: a failed read with no saved copy holds the state ({x})')
    else: check(x is None and r == 500 and s == [500], f'{w}: a failed read with no saved copy is built from and saved, as before ({r}, {s})')
    r, s, o, x = run(hold, 900, 1000)
    check(x is None and r == 1000 and s == [] and any('saved copy was used' in m for m in o), f'{w}: a failed read 10% short falls back to the saved copy (nothing dropped) ({r}, {o})')
    r, s, o, x = run(hold, 980, 1000, failed=False)
    check(x is None and r == 980 and s == [980], f'{w}: no failed layer = no change ({r}, {s})')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
