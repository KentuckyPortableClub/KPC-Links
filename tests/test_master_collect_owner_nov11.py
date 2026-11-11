#!/usr/bin/env python3
"""Nov 11 (Quality CONFIRMED must-fix; KPC owner, 2026-11-11): each US key build part holds only its own states, and the join takes
each state from its owning part. Before: every part carried the whole master root, collect copied parts in name order and the last
write won, so part 2's stale checkout copy of US-HI (and MD MN MO NV UT) replaced part 1's new outlines in run 42956018092.
Nothing here contacts any server."""
import json, pathlib, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M  # noqa: E402
import kpc_master_cli as CLI  # noqa: E402
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def rec(ref, n):
    g = {'type': 'Polygon', 'coordinates': [[[0, 0], [n, 0], [n, n], [0, 0]]]}
    return M.make_record(ref, ref, 'official', g, 'a', 'file:x', ['r%d' % n], n, '2026-11-11', '', 'id')


def root_with(d, recs, layers=None, raw=None):
    d.mkdir(parents=True, exist_ok=True)
    for area, rs in recs.items(): M.save_area(area, {r['ref']: r for r in rs}, d)
    M.save_layers({'format': 1, 'layers': layers or {}, 'caches': {}}, d)
    M.raw_manifest_path(d).write_text(json.dumps({'format': 1, 'files': raw or []}))


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    base = t / 'base'
    root_with(base, {'US-HI': [rec('US-1', 1)], 'US-AL': [rec('US-2', 2)]}, {'US-HI.sghia': {'source_count': 70}, 'US-AL.x': {'source_count': 1}},
              [{'name': 'US-HI.sghia.geojson.gz', 'sha256': 'old'}])
    # group 1 owns HI and adds an outline + a layer row + a raw row; group 2 owns AL and touches nothing of HI
    r1 = t / 'r1'; shutil.copytree(base, r1)
    have = M.load_area('US-HI', r1); have['US-3'] = rec('US-3', 3); M.save_area('US-HI', have, r1)
    d = M.load_layers(r1); d['layers']['US-HI.sgaki'] = {'source_count': 2}; M.save_layers(d, r1)
    M.raw_manifest_path(r1).write_text(json.dumps({'format': 1, 'files': [{'name': 'US-HI.sghia.geojson.gz', 'sha256': 'old'}, {'name': 'US-HI.sgaki.geojson.gz', 'sha256': 'new'}]}))
    (r1 / 'solver-queue').mkdir(); (r1 / 'solver-queue' / 'US-HI.sgaki.csv').write_text('ref\n')
    r2 = t / 'r2'; shutil.copytree(base, r2)
    p1, p2 = t / 'parts/us-key-part-1/outlines', t / 'parts/us-key-part-2/outlines'
    check('part 1 written', CLI.main(['part', '--root', str(r1), '--base', str(base), '--states', 'HI MD', '--out', str(p1)]) == 0)
    check('part 2 written', CLI.main(['part', '--root', str(r2), '--base', str(base), '--states', 'AL', '--out', str(p2)]) == 0)
    check('a part holds only its own states\' outline files', sorted(x.name for x in p1.glob('US-*.geojson.gz')) == ['US-HI.geojson.gz'] and sorted(x.name for x in p2.glob('US-*.geojson.gz')) == ['US-AL.geojson.gz'])
    check('a part carries only the layer rows that changed, of its own states', set(json.loads((p1 / 'layers.json').read_text())['layers']) == {'US-HI.sgaki'} and json.loads((p2 / 'layers.json').read_text())['layers'] == {})
    check('a part carries only changed raw rows', [r['name'] for r in json.loads((p1 / 'raw-manifest.json').read_text())['files']] == ['US-HI.sgaki.geojson.gz'])
    check('states.txt names the owner', (p1 / 'states.txt').read_text().split() == ['HI', 'MD'])
    join = t / 'join'; shutil.copytree(base, join)
    check('collect joins per state', CLI.main(['collect', str(p1), str(p2), '--root', str(join)]) == 0)
    check('the later part did NOT put a stale HI over part 1\'s new outline', 'US-3' in M.load_area('US-HI', join))
    check('layer row and raw row of HI reached the join; old rows kept', 'US-HI.sgaki' in M.load_layers(join)['layers'] and 'US-AL.x' in M.load_layers(join)['layers']
          and {r['name'] for r in json.loads(M.raw_manifest_path(join).read_text())['files']} == {'US-HI.sghia.geojson.gz', 'US-HI.sgaki.geojson.gz'})
    check('solver queue file of the owning part copied', (join / 'solver-queue' / 'US-HI.sgaki.csv').is_file())
    # the old bug, rebuilt: a part that carries a state it does not own is a conflict, and nothing is written
    bad = t / 'parts/us-key-part-3/outlines'; shutil.copytree(p2, bad); shutil.copy(base / 'US-HI.geojson.gz', bad / 'US-HI.geojson.gz')
    (bad / 'states.txt').write_text('WY\n')
    j2 = t / 'join2'; shutil.copytree(base, j2); before = (j2 / 'US-HI.geojson.gz').read_bytes()
    check('a part carrying another state\'s file = conflict, exit 1', CLI.main(['collect', str(p1), str(bad), '--root', str(j2)]) == 1)
    check('... and nothing was written', (j2 / 'US-HI.geojson.gz').read_bytes() == before and 'US-HI.sgaki' not in M.load_layers(j2)['layers'])
    dup = t / 'parts/us-key-part-4/outlines'; dup.mkdir(parents=True); (dup / 'states.txt').write_text('HI\n')
    check('two parts owning one state = conflict', CLI.main(['collect', str(p1), str(dup), '--root', str(j2)]) == 1)
    lr = t / 'parts/us-key-part-5/outlines'; lr.mkdir(parents=True); (lr / 'states.txt').write_text('AK\n')
    (lr / 'layers.json').write_text(json.dumps({'layers': {'US-HI.sgaki': {'source_count': 9}}}))
    check('a layer row of a state the part does not own = conflict', CLI.main(['collect', str(p1), str(lr), '--root', str(j2)]) == 1)
    rr = t / 'parts/us-key-part-6/outlines'; rr.mkdir(parents=True); (rr / 'states.txt').write_text('AK\n')
    (rr / 'raw-manifest.json').write_text(json.dumps({'files': [{'name': 'US-HI.sgaki.geojson.gz', 'sha256': 'other'}]}))
    check('two parts writing one raw row differently = conflict', CLI.main(['collect', str(p1), str(rr), '--root', str(j2)]) == 1)
    old = t / 'parts/us-key-part-7/outlines'; old.mkdir(parents=True); shutil.copy(base / 'US-HI.geojson.gz', old / 'US-HI.geojson.gz')
    check('an old-style part (no states.txt) is refused', CLI.main(['collect', str(old), '--root', str(j2)]) == 1)

wf = (ROOT / '.github/workflows/kpc-us-key.yml').read_text()
check('workflow: the build writes its part with `part` (own states only), not a copy of the whole root',
      'kpc_master_cli.py part --root .master/root --base data/outlines --states "$STATES" --out part/outlines' in wf and 'cp .master/root/US-*.geojson.gz' not in wf)
check('workflow: a failed collect keeps data/outlines out of the save and goes red', 'Master collect::the parts did not join per state' in wf and wf.count('touch /tmp/kpc-outlines-bad') >= 2)
check('workflow: data/us-key/layers.json is joined per prefix, not whole-file', 'LJ.update(' not in wf and 'kpc_us_key_join.py parts/us-key-part-*' in wf)
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
