#!/usr/bin/env python3
"""Handoff 8 fix 5 (switch KPC_CA_NONE_KEPT): in Canada a park a person marked 'none' (a different place, no outline of its own) takes
no NAME join until a person clears it. Runs the real kpc_ca_key.py offline on a small saved copy (tests/kpc_pinfill_fixture.py, no
network): real park refs, names, pins and record names / layers from the Nov 17 offline run; made-up rectangles at the pins.
Run:  python3 tests/test_h8_ca_none_kept_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests')); sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_pinfill_fixture as H  # noqa: E402  (refuses every socket on import)
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

def park(n, ty, la, lo, pv): return [n, '', ty, '', '', la, lo, 0, 0, 0, pv]
PARKS = {'CA-0485': park('Trout Brook Provincial Park', 'Provincial Park', 46.0957, -61.141, 'NS'),
         'CA-6371': park('Cedar Creek Conservation Area', 'Conservation Area', 42.0288, -82.824, 'ON'),
         'CA-5201': park('Ministers Island National Historic Site', 'National Historic Site', 45.0986, -67.0343, 'NB'),
         'CA-0304': park('Mississagi Provincial Park', 'Provincial Park', 46.5787, -82.724, 'ON'),
         'CA-0879': park('Union Corner Provincial Park', 'Provincial Park', 46.6, -64.0, 'PE')}
def rec(oid, n, ty, la, lo, src, ha=10.0):
    r = {'oid': oid, 'n': n, 'nf': '', 'ty': ty, 'ow': '', 'mg': '', 'ha': ha, '_r': [H.ring(la, lo, .005)], '_k': [], 'src': src}
    return r
RECS = [rec('NS NS_Lands_:1', 'Trout Brook Provincial Park', 'Provincial Park', 46.0957, -61.141, 'NS NS_Lands_Proposed_or_Pending_Protection', 5.7),
        rec('ON-ERCA Esse:7', 'Cedar Creek', 'Conservation Area', 42.0288, -82.824, 'ON-ERCA Essex Region Conservation Authority', 375),
        rec('NB-PP Govern:20', "Minister's Island", 'Provincial Park', 45.0986, -67.0343, 'NB-PP Government of New Brunswick (GeoNB)', 207),
        rec(31001, 'Mississagi Provincial Park', 'Provincial Park', 46.5787, -82.724, None, 4900),
        rec('PE-PP Govern:33', 'UNION CORNER', 'Provincial Park', 46.6, -64.0, 'PE-PP Government of Prince Edward Island')]
for r in RECS:
    if r['src'] is None: r.pop('src')
WHY = 'a different place, not this park (hand review Oct 22)'
OVR = {'parks': {'CA-0485': {'none': True, 'why': WHY}, 'CA-6371': {'none': True, 'why': WHY}, 'CA-5201': {'none': True, 'why': WHY},
                 'CA-0879': {'none': True, 'join': ['PE-PP Govern:33'], 'why': 'test: a person joined it by hand'}}}
FILES = {'data/ca-key/overrides.json': json.dumps(OVR)}
def build(sw):
    r, out = H.ca_build(PARKS, RECS, {'KPC_CA_NONE_KEPT': sw}, ca_files=FILES)
    k = {}
    for f, b in out.items():
        if f.startswith('data/ca-key/CA-') and f.endswith('.json') and '/' not in f[len('data/ca-key/'):]: k.update(json.loads(b).get('parks') or {})
    return r, k
r0, off = build('0'); r1, on = build('1')
check(r0.returncode == 0 and r1.returncode == 0, f'both offline builds ran (exit {r0.returncode} / {r1.returncode})' + ('' if r1.returncode == 0 else ': ' + (r1.stderr or r1.stdout)[-400:]))
ids = lambda k, ref: [str(x[0]) for x in (k.get(ref) or {}).get('m') or []]
for ref in ('CA-0485', 'CA-6371', 'CA-5201'):
    check(ids(off, ref) and not ids(on, ref), f"{ref} {PARKS[ref][0]}: OFF joined by name {ids(off, ref)} (today's bug); ON no join (the person's 'none' holds)")
check(ids(off, 'CA-0304') == ids(on, 'CA-0304') == ['31001'], 'must NOT: CA-0304 Mississagi PP (no none) keeps its name join')
check(ids(on, 'CA-0879') == ['PE-PP Govern:33'], "must NOT: a person's own join on a 'none' park stands")
check("kept no name join" in r1.stdout and 'CA-0485' in r1.stdout, 'the run says which parks were held')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
