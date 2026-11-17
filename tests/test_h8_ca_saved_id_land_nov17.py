#!/usr/bin/env python3
"""Handoff 8 fix 6 (switch KPC_CA_SAVED_ID_LAND, reviewer B3): a Canada hand join saved as a bare record id keeps the LAND it stood
for (name + hectares + the source's own stable id, CPCAD ZONE_ID = the tract row's 'sid'). The test RENUMBERS a saved copy:
 - today's copy: the saved id still points at the right land -> the same join, switch on or off;
 - renumbered: the id now points at another record and the land has a new id -> OFF joins the wrong record (today's silent bug),
   ON finds the land again by its ZONE_ID;
 - renumbered and the land gone -> ON joins nothing by that id and the park goes to a person (check B3);
 - must NOT: a saved id with no saved land (no tract row) and a park joined by name are unchanged.
Runs the real kpc_ca_key.py offline on a small saved copy (tests/kpc_pinfill_fixture.py, no network). Park and record names, ids
and ZONE_IDs are the real CA-3297 ones (overrides join '21900', tract sid 700100100); the shapes are made up at the pin.
Run:  python3 tests/test_h8_ca_saved_id_land_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests')); sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_pinfill_fixture as H  # noqa: E402  (refuses every socket on import)
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

LA, LO = 51.2803, -128.859
HEC = 'Hecate Strait and Queen Charlotte Sound Glass Sponge Reefs Marine Protected Areas'
PARKS = {'CA-3297': ['Queen Charlotte Sound Glass Sponge Reefs Marine Protected Area', '', 'Marine Protected Area', '', '', LA, LO, 0, 0, 0, 'BC'],
         'CA-0304': ['Mississagi Provincial Park', '', 'Provincial Park', '', '', 46.5787, -82.724, 0, 0, 0, 'ON'],
         'CA-9001': ['Test Saved Id Park', '', 'Park', '', '', 50.0, -120.0, 0, 0, 0, 'BC']}
def rec(oid, n, la, lo, ha, zone, ty='Marine Protected Area'):
    return {'oid': oid, 'n': n, 'nf': '', 'ty': ty, 'ow': 'Government of Canada', 'mg': '', 'ha': ha, '_r': [H.ring(la, lo, .01)], '_k': [],
            'SA': {'ZONE_ID': zone}}
MISS = rec(31001, 'Mississagi Provincial Park', 46.5787, -82.724, 4900, '31001', 'Provincial Park')
OTHER9001 = rec(55555, 'Some Old Reserve', 50.0, -120.0, 50, '555550')
OVR = {'parks': {'CA-3297': {'join': ['21900'], 'approx': True, 'why': 'hand review'},
                 'CA-9001': {'join': ['55555'], 'why': 'test: a saved id with no saved land'}}}
TRACTS = {'parks': {'CA-3297': [{'rid': 21900, 'sid': '700100100', 'name': HEC, 'ac': 371243.6, 'layer': 'CPCAD', 'src': 'cpcad', 'how': 'reviewed-approx'}]}}
FILES = {'data/ca-key/overrides.json': json.dumps(OVR), 'data/ca-key/tracts/CA-BC.json': json.dumps(TRACTS)}
TODAY = [rec(21900, HEC, LA, LO, 150237, '700100100'), MISS, OTHER9001]
RENUM = [rec(21900, 'Scott Islands Marine National Wildlife Area', LA, LO, 1165000, '700200200', 'National Wildlife Area'),
         rec(30000, HEC, LA, LO, 150237, '700100100'), MISS, OTHER9001]
GONE = [rec(21900, 'Scott Islands Marine National Wildlife Area', LA, LO, 1165000, '700200200', 'National Wildlife Area'), MISS, OTHER9001]

def build(recs, sw):
    r, out = H.ca_build(PARKS, recs, {'KPC_CA_SAVED_ID_LAND': sw}, ca_files=FILES)
    k = {}
    for f, b in out.items():
        if f.startswith('data/ca-key/CA-') and f.endswith('.json') and '/' not in f[len('data/ca-key/'):]: k.update(json.loads(b).get('parks') or {})
    return r, k
ids = lambda k, ref: [str(x[0]) for x in (k.get(ref) or {}).get('m') or []]
runs = {(n, sw): build(rs, sw) for n, rs in (('today', TODAY), ('renum', RENUM), ('gone', GONE)) for sw in ('0', '1')}
check(all(r.returncode == 0 for r, _ in runs.values()), 'all six offline builds ran' + ''.join(f' | {k}: ' + (r.stderr or r.stdout)[-300:] for k, (r, _) in runs.items() if r.returncode))
k = {key: v[1] for key, v in runs.items()}
check(ids(k['today', '0'], 'CA-3297') == ids(k['today', '1'], 'CA-3297') == ['21900'], "today's copy: the saved id 21900 still points at Hecate Strait: the same join, on or off")
check('Handoff 8 fix 6' not in runs['today', '1'][0].stdout, "today's copy: nothing flagged")
check(ids(k['renum', '0'], 'CA-3297') == ['21900'] and (k['renum', '0']['CA-3297']['m'][0][1]).startswith('Scott Islands'),
      'renumbered, OFF: joins whatever now has id 21900 (Scott Islands) - the silent bug')
check(ids(k['renum', '1'], 'CA-3297') == ['30000'] and 'found again by its saved land' in k['renum', '1']['CA-3297']['m'][0][3],
      'renumbered, ON: finds Hecate Strait again by its CPCAD ZONE_ID 700100100 (new id 30000)')
check(ids(k['gone', '1'], 'CA-3297') == [] and any('check (B3)' in q[3] and q[0] in (21900, '21900') for q in k['gone', '1']['CA-3297']['c']),
      'renumbered and the land gone, ON: no join by that id; a check (B3) row goes to a person')
check('saved record id(s) no longer point' in runs['gone', '1'][0].stdout and 'CA-3297' in runs['gone', '1'][0].stdout, 'the run names the park')
check(all(ids(k[key], 'CA-9001') == ['55555'] for key in k), 'must NOT: a saved id with no saved land (no tract row) joins as before')
check(all(ids(k[key], 'CA-0304') == ['31001'] for key in k), 'must NOT: a park joined by name is unchanged')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
