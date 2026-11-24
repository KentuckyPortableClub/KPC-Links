#!/usr/bin/env python3
"""24 Nov 2026 (owner's settled-joins ruling S4: records a saved answer names are REQUIRED, never trimmed): the state-layer reader
keeps a record a person's saved answer names even when PAD-US has the same name on the same ground. No network."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


start = src.index('_SAVED_NAMED = []'); end = src.index('def _dup(have, key, bb):')
ns = {'OVR': {'US-9001': {'join': ['sgzza533'], 'fp': {'sgzza534': ['Invented Point', 10]}, 'nofp': {'sgzzb7': ['Invented Bay', 5]}},
              'US-9002': {'no': ['sgzza999']}}}
exec(src[start:end], ns)
got = ns['saved_named']()
check('join, fp and nofp ids are all named', {'sgzza533', 'sgzza534', 'sgzzb7'} <= got)
check("a person's NO is not a saved join", 'sgzza999' not in got)
check('the copy check skips a named record', "not in saved_named() and _dup(have" in src)
check('only the copy check changed: the name and easement filters stay', "if not nm: continue" in src and "re.search(r'easement', nm, re.I)" in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
