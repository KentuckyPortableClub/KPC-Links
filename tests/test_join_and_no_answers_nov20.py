#!/usr/bin/env python3
"""Job 10b (Fable's 20 Nov jobs list; outside review R4, list S6b-297-join-and-no.csv): 15 parks held one record under both 'join'
and 'no' of their saved answer. Nine are settled with official evidence (evidence batch 05, first pass): five keep the later NO
and drop the old approximate join, four keep the join and lose a NO whose saved fingerprint was other land (the lake, or the
drawn outline). Six are left for a person, with the reason in the hand-back. This test fails while any of the nine still holds
one record under both lists, or when a new park starts to.
Run:  python3 tests/test_join_and_no_answers_nov20.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_overrides as K  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

P = K.load(ROOT / 'data/us-key/overrides.json')['parks']
ids = lambda v, k: {str(x) for x in (v or {}).get(k) or []}
DROP_JOIN = {'US-12708': '165883', 'US-12126': '190265', 'US-10914': '195379', 'US-10918': '195408', 'US-0697': '2441'}
LIFT_NO = {'US-1080': 'sgarb44', 'US-1093': 'sgarb27', 'US-1094': 'sgarb13', 'US-1773': 'sgmoa1495'}
LEFT = {'US-3703', 'US-8325', 'US-1208', 'US-11312', 'US-7145', 'US-5629'}
for ref, rid in DROP_JOIN.items():
    v = P.get(ref) or {}
    check(rid in ids(v, 'no') and rid not in ids(v, 'join') and rid not in (v.get('fp') or {}), f'{ref}: the NO on {rid} stands, its join and fingerprint are gone')
for ref, rid in LIFT_NO.items():
    v = P.get(ref) or {}
    check(rid in ids(v, 'join') and rid in (v.get('fp') or {}) and rid not in ids(v, 'no') and rid not in (v.get('nofp') or {}),
          f'{ref}: the join of {rid} stands, the NO and its fingerprint are gone')
for ref in list(DROP_JOIN) + list(LIFT_NO):
    v = P.get(ref) or {}
    ev = v.get('evidence') if isinstance(v.get('evidence'), dict) else {}
    check(str(v.get('decided_by') or '').startswith('evidence batch 05') and all(str(ev.get(k) or '').strip() for k in ('who', 'source', 'saw', 'date'))
          and all(s.strip().startswith('https://') for s in ev.get('source', '').split(' ; ')), f'{ref}: who, official source, what it shows and the date')
both = {r for r, v in P.items() if isinstance(v, dict) and ids(v, 'join') & ids(v, 'no')}
check(both == LEFT, f'one record under both join and no: only the {len(LEFT)} parks left for a person ({len(both)} now)')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
