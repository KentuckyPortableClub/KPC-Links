#!/usr/bin/env python3
"""kpc_us_key.py PAD-US state read (owner rule, 2026-11-10): it runs under the same per-layer time limit as every other layer
read (kpc_master.LAYER_MINUTES = KPC_LAYER_MINUTES, default 60). Past the limit the state fails closed with a clear message
(the run's state loop notes FAILED and writes nothing for it, so the last key file stays). Offline, with a fake clock."""
import pathlib, sys, types

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


NOW = [0.0]
PAD = [{'attributes': {'OBJECTID': i}} for i in range(1, 1001)]
ns = {'time': types.SimpleNamespace(sleep=lambda s: None, monotonic=lambda: NOW[0]), 'KMASTER': types.SimpleNamespace(LAYER_MINUTES=60.0),
      'NAME_KEEP': False, '_passes_load': lambda a: True, '_shape': lambda a, f: a, 'keep_names': lambda P, st: ({}, {}),
      'notice': lambda t, m: None, 'NAME_KEEP_HIT': [], 'Q': 'https://padus.example.gov/query', 'count_query': lambda url, q, box=True: len(PAD)}
exec(compile(SRC[SRC.index('def pad_state(st, P=None):'):SRC.index('SAVED_HIT = []')], 'kpc_us_key.py', 'exec'), ns)
PAGES = []


def slow(st, off):   # each page takes 10 fake minutes
    PAGES.append(off); NOW[0] += 600
    return {'features': PAD[off:off + 100]}


ns['page'] = slow
try: ns['pad_state']('VT'); err = None
except RuntimeError as e: err = e
check(f'a PAD-US state read past its 60-minute limit fails closed with a clear message ({err})',
      err is not None and '60-minute layer limit' in str(err) and 'KPC_LAYER_MINUTES' in str(err) and 'last key stays' in str(err))
check(f'... and stops asking (pages asked: {len(PAGES)} of 10)', len(PAGES) == 7)
NOW[0] = 0.0; PAGES.clear(); ns['KMASTER'].LAYER_MINUTES = 200.0
recs, n = ns['pad_state']('VT')
check(f'the same read under a 200-minute limit (KPC_LAYER_MINUTES=200) finishes ({n} records)', n == len(PAD))
check('the limit is kpc_master.LAYER_MINUTES (one env var for every layer read)', 'KMASTER.LAYER_MINUTES' in SRC[SRC.index('def pad_state('):SRC.index('SAVED_HIT = []')])
check("a failed state is not written: the state loop catches the error and goes on (the last key file stays)",
      "        c = run(st)\n    except Exception as e:  # noqa: BLE001\n        notice(f'US key {st}', f'FAILED: {e}'); continue" in SRC)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
