#!/usr/bin/env python3
"""Offline (KPC owner, 2026-11-13; Quality regrade 4 LD): an ah3 composition migration is one-time. A state whose row has no
trails part is planned as format-only once; the next stamp (any key run on the plan's commit, even one that did not build it)
records its parts with no rebuild, so a later trail edit rebuilds it. Not recorded when the build used another commit."""
import json, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_area_hash as H  # noqa: E402

ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)

comp = H.composition('us')
old = {'code:x': 'c1', 'data:data/us-key/overrides.json': 'o1', 'version': 'v'}
new = dict(old, **{'composition': 'k', 'data:data/trails/index': 't1', 'data:data/trails/*': 'f1'})
check('before: the missing trails part reads as migration only', not H.real_inputs_moved(old, new, comp))

def run(plan_sha, built_sha):
    d = pathlib.Path(tempfile.mkdtemp())
    (d / 'data/us-key').mkdir(parents=True)
    kf = d / 'data/us-key/US-TN.json'; kf.write_text('{"tn": 1}')
    idx = d / 'data/us-key/index.json'
    idx.write_text(json.dumps({'states': {'TN': {'rules': 'r', 'area_hash': 'h0', 'area_parts': old, 'out_sha': H.sha_file(kf), 'built_sha': 'b0'},
                                          'KY': {'rules': 'r', 'area_hash': 'k0', 'area_parts': old, 'out_sha': 'x', 'built_sha': 'b0'}}}))
    plan = {'plan_sha': plan_sha, 'composition': comp, 'code_hash': 'r', 'hashes': {'TN': 'h1', 'KY': 'k1'}, 'parts': {'TN': new, 'KY': new}, 'reused': []}
    H.stamp_rows(d, 'us', idx, [], plan, built_sha)
    return json.loads(idx.read_text())['states']

rows = run('s1', 's1')
tn = rows['TN']
check('a run on the plan commit records TN parts without a rebuild (bytes, rules, built_sha kept)',
      tn['area_parts'] == new and tn['area_hash'] == 'h1' and tn['rules'] == 'r' and tn['built_sha'] == 'b0')
check('a row whose key file is not the recorded one is not restamped', rows['KY']['area_parts'] == old)
edited = dict(new, **{'data:data/trails/*': 'f2'})
check('after the one-time record, a trail edit is a real move (rebuilds)', H.real_inputs_moved(tn['area_parts'], edited, comp))
check('a build on another commit records nothing', run('s1', 's2')['TN']['area_parts'] == old)
sys.exit(0 if ok else 1)
