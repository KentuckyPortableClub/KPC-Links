#!/usr/bin/env python3
"""Nov 11 r2 (KPC owner, 2026-11-11; Quality NO on #126, must-fix 1): every per-state output of the US key join is taken from the build
group that OWNS the state, and any conflict fails closed (exit 1, nothing written). Two-group cases for each output:
US-ST.json / tracts / index rows, data/us-key/layers.json rows, zip-<prefix>.json files, and the master raw-manifest rows."""
import json, pathlib, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_us_key_join as J
import kpc_master_cli as CLI

ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)

KEY = ROOT / '.github/scripts/kpc_us_key.py'
OWN = J.zip_owners(KEY)
check('zip layer owners are read from SZ_US without running the key', OWN.get('mszw') == {'MS'} and OWN.get('mszp') == {'MS'})


def snap(d):
    return {str(p.relative_to(d)): p.read_bytes() for p in sorted(pathlib.Path(d).rglob('*')) if p.is_file()}


def setup(t):
    out = t / 'us-key'; out.mkdir()
    (out / 'index.json').write_text(json.dumps({'states': {'MS': {'parks': 1}, 'TX': {'parks': 1}, 'AL': {'parks': 1}}}))
    (out / 'layers.json').write_text(json.dumps({'padus': ['u0', 'n', 'PAD-US'], 'mszw': ['file:data/us-key/zip-mszw.json', 'Unit_Nm', 'old']}))
    (out / 'zip-mszw.json').write_text('CHECKOUT'); (out / 'US-MS.json').write_text('{"old": 1}'); (out / 'US-TX.json').write_text('{"old": 1}')
    return out


def mkpart(t, i, states, files=None, layers=None, zips=None, index=True):
    d = t / 'parts' / f'us-key-part-{i}'; (d / 'tracts').mkdir(parents=True)
    (d / 'states.txt').write_text(' '.join(states) + '\n')
    if index: (d / 'index.json').write_text(json.dumps({'states': {s: {'parks': 2, 'from': i} for s in states}}))
    for st in states: (d / f'US-{st}.json').write_text(json.dumps({'new': i, 'st': st}))
    for name, body in (files or {}).items(): (d / name).parent.mkdir(parents=True, exist_ok=True); (d / name).write_text(body)
    (d / 'layers.json').write_text(json.dumps(layers if layers is not None else {'padus': ['u0', 'n', 'PAD-US']}))
    for name, body in (zips or {}).items(): (d / name).write_text(body)
    return d


def run(t, parts):
    import os
    here = os.getcwd(); os.chdir(t)   # kpc_save writes its status file under ./data/status: keep it in the temp dir
    try: return J.main([str(p) for p in parts] + ['--out', str(t / 'us-key'), '--key-src', str(KEY)])
    finally: os.chdir(here)


# 1) the good join: each state from its owner; a later part's stale checkout copies do not win
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); out = setup(t)
    p0 = mkpart(t, 0, ['MS'], files={'tracts/US-MS.json': '{"t": 0}'}, layers={'padus': ['u0', 'n', 'PAD-US'], 'mszw': ['file:data/us-key/zip-mszw.json', 'Unit_Nm', 'NEW']},
                zips={'zip-mszw.json': 'NEW_FROM_MS_GROUP'})
    p1 = mkpart(t, 1, ['TX'], layers={'padus': ['u0', 'n', 'PAD-US'], 'mszw': ['file:data/us-key/zip-mszw.json', 'Unit_Nm', 'old']})   # stale main copy of the MS row
    rc = run(t, [p0, p1])
    check('two groups join: exit 0', rc == 0)
    check('MS file from its owner, TX file from its owner', json.loads((out / 'US-MS.json').read_text()) == {'new': 0, 'st': 'MS'} and json.loads((out / 'US-TX.json').read_text()) == {'new': 1, 'st': 'TX'})
    check('tracts from the owner', (out / 'tracts/US-MS.json').read_text() == '{"t": 0}')
    idx = json.loads((out / 'index.json').read_text())['states']
    check('index rows from the owners; a state no part built keeps its row', idx['MS']['from'] == 0 and idx['TX']['from'] == 1 and idx['AL'] == {'parks': 1})
    check("zip: the MS group's new copy is kept", (out / 'zip-mszw.json').read_text() == 'NEW_FROM_MS_GROUP')
    lj = json.loads((out / 'layers.json').read_text())
    check("layers.json: a later part's stale main copy of a row does not undo the owner's change", lj['mszw'][2] == 'NEW')

# 2) zip: a part that does not own the zip layer's state sends it (Quality's proof: the stale checkout copy replaced the new one)
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); out = setup(t); before = snap(out)
    p0 = mkpart(t, 0, ['MS'], zips={'zip-mszw.json': 'NEW_FROM_MS_GROUP'})
    p1 = mkpart(t, 1, ['TX'], zips={'zip-mszw.json': 'CHECKOUT'})
    check('zip from a group that does not own MS = exit 1', run(t, [p0, p1]) == 1)
    check('zip conflict: nothing written', snap(out) == before)
    p2 = mkpart(t, 2, ['AL'], zips={'zip-xxzz.json': 'X'})
    check('a zip no key layer lists = exit 1', run(t, [p2]) == 1 and snap(out) == before)

# 3) US-ST.json: one state in two groups, or a file for a state the group does not own
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); out = setup(t); before = snap(out)
    p0 = mkpart(t, 0, ['MS', 'TX']); p1 = mkpart(t, 1, ['TX'])
    check('one state in the states of two groups = exit 1', run(t, [p0, p1]) == 1)
    check('dual owner: nothing written', snap(out) == before)
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); out = setup(t); before = snap(out)
    p0 = mkpart(t, 0, ['MS']); p1 = mkpart(t, 1, ['TX'], files={'US-MS.json': '{"stale": 1}'})
    check('a group carrying US-MS.json it does not own = exit 1', run(t, [p0, p1]) == 1 and snap(out) == before)
    shutil.rmtree(p1); p1 = mkpart(t, 1, ['TX'], files={'tracts/US-MS.json': '{}'})
    check('a group carrying tracts/US-MS.json it does not own = exit 1', run(t, [p0, p1]) == 1 and snap(out) == before)

# 4) layers.json: two groups change one prefix differently (Quality: was '::error ... the first is kept' and a green save)
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); out = setup(t); before = snap(out)
    p0 = mkpart(t, 0, ['MS'], layers={'padus': ['u1', 'n', 'PAD-US']}); p1 = mkpart(t, 1, ['TX'], layers={'padus': ['u2', 'n', 'PAD-US']})
    check('one layers.json prefix written differently by two groups = exit 1', run(t, [p0, p1]) == 1)
    check('layers.json conflict: nothing written', snap(out) == before)
    shutil.rmtree(p1); p1 = mkpart(t, 1, ['TX'], layers={'padus': ['u1', 'n', 'PAD-US']})
    check('the same change from two groups is not a conflict', run(t, [p0, p1]) == 0 and json.loads((out / 'layers.json').read_text())['padus'][0] == 'u1')

# 5) a red group (no index.json) is skipped, as before
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); out = setup(t)
    p0 = mkpart(t, 0, ['MS']); p1 = mkpart(t, 1, ['MS'], index=False)
    check('a red group without index.json does not count as a second owner', run(t, [p0, p1]) == 0)

# 6) master raw-manifest rows: a state's row only from its owner; a shared row written differently = conflict
def mpart(t, i, states, raw):
    d = t / f'p{i}' / 'outlines'; d.mkdir(parents=True)
    (d / 'states.txt').write_text(' '.join(states) + '\n')
    (d / 'layers.json').write_text(json.dumps({'format': 1, 'layers': {}, 'caches': {}}))
    (d / 'raw-manifest.json').write_text(json.dumps({'format': 1, 'files': raw}))
    return d
def mroot(t):
    r = t / 'root'; r.mkdir(); (r / 'layers.json').write_text(json.dumps({'format': 1, 'layers': {}, 'caches': {}}))
    (r / 'raw-manifest.json').write_text(json.dumps({'format': 1, 'files': []})); return r
row = lambda n, sha: {'name': n, 'size': 1, 'sha256': sha, 'source': 's', 'date': '2026-11-11'}
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); r = mroot(t); before = snap(r)
    a = mpart(t, 0, ['MS'], [row('hand-US-MS.sgide.geojson.gz', 'a')]); b = mpart(t, 1, ['TX'], [row('hand-US-MS.sgide.geojson.gz', 'stale')])
    check('raw: a group writing the row of a state it does not own = exit 1', CLI.main(['collect', str(a), str(b), '--root', str(r)]) == 1 and snap(r) == before)
    shutil.rmtree(b.parent); b = mpart(t, 1, ['TX'], [row('usace-all-states.geojson', 'x')]); shutil.rmtree(a.parent); a = mpart(t, 0, ['MS'], [row('usace-all-states.geojson', 'y')])
    check('raw: a shared row written differently by two groups = exit 1', CLI.main(['collect', str(a), str(b), '--root', str(r)]) == 1 and snap(r) == before)
    shutil.rmtree(b.parent); b = mpart(t, 1, ['TX'], [row('US-TX.sgtxa.geojson.gz', 't')])
    check('raw: each group its own rows = exit 0', CLI.main(['collect', str(a), str(b), '--root', str(r)]) == 0
          and {x['name'] for x in json.loads((r / 'raw-manifest.json').read_text())['files']} == {'usace-all-states.geojson', 'US-TX.sgtxa.geojson.gz'})
import kpc_master_fill as F
check("part(): another state's raw row is not sent", F._raw_state('hand-US-MS.sgide.geojson.gz') == 'MS' and F._raw_state('US-HI.sgaki.geojson.gz') == 'HI' and F._raw_state('usace.geojson') is None)

# 7) the workflow uses all of it
wf = (ROOT / '.github/workflows/kpc-us-key.yml').read_text()
check('workflow: a build part sends only the zip copies it wrote (newer than its build start)',
      'touch "$RUNNER_TEMP/key-t0"' in wf and "-name 'zip-*.json' -newer \"$RUNNER_TEMP/key-t0\"" in wf and 'cp data/us-key/zip-*.json part/' not in wf)
check('workflow: the join is kpc_us_key_join.py and a conflict saves nothing',
      'kpc_us_key_join.py parts/us-key-part-* --out data/us-key' in wf and wf.count('/tmp/kpc-key-join-bad') >= 2 and 'the first is kept' not in wf)

if 'kpc_save' in sys.modules: sys.modules['kpc_save']._changed.clear()   # the temp files' change dates are not the repo's status
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
