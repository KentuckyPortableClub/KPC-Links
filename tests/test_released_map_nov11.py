#!/usr/bin/env python3
"""KPC owner, 2026-11-11: the public map reads data/released only. The release script copies one area's map files from one commit,
cuts a file over 1 MB into parts, lists every file with its own version, and writes nothing when anything is wrong. The four
loaders carry the same KPCREL block and no longer read the working outline / key files directly."""
import gzip, json, pathlib, re, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_release as R

ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)

def sh(d, *a): return subprocess.run(a, cwd=d, capture_output=True, text=True)
def gzj(doc): return R.gz(json.dumps(doc).encode())
def snap(d): return {str(p.relative_to(d)): p.read_bytes() for p in sorted(pathlib.Path(d).rglob('*')) if p.is_file()}

with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t); sh(d, 'git', 'init', '-q'); sh(d, 'git', 'config', 'user.name', 't'); sh(d, 'git', 'config', 'user.email', 't@t')
    (d / 'data/outlines').mkdir(parents=True); (d / 'data/us-key/tracts').mkdir(parents=True); (d / 'data/ca-key').mkdir(parents=True)
    feat = lambda i: {'type': 'Feature', 'properties': {'ref': f'US-{i}'}, 'geometry': {'type': 'Point', 'coordinates': [i, i]}}
    (d / 'data/outlines/US-FL.geojson.gz').write_bytes(gzj({'type': 'FeatureCollection', 'kpc': {'area': 'US-FL'}, 'features': [feat(i) for i in range(3)]}))
    (d / 'data/outlines/US-FL.sgfla.geojson.gz').write_bytes(b'a layer file')
    (d / 'data/outlines/layers.json').write_text('{}')
    (d / 'data/us-key/US-FL.json').write_text(json.dumps({'st': 'FL', 'parks': {'US-1': {'g': 'official'}}}))
    big = {'st': 'WI', 'parks': {f'US-{i:04d}': {'g': 'official', 'm': ['x' * 900]} for i in range(60)}}
    (d / 'data/us-key/US-WI.json').write_text(json.dumps(big))
    for n in ('layers.json', 'overrides.json', 'index.json'): (d / 'data/us-key' / n).write_text('{"a":1}')
    (d / 'data/us-key/tracts/US-FL.json').write_text('{}')
    (d / 'data/ca-key/CA-ON.json').write_text('{"parks":{}}'); (d / 'data/ca-key/refs.json').write_text('{}')
    sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', 'one'); sha1 = sh(d, 'git', 'rev-parse', 'HEAD').stdout.strip()
    R.CAP = 20_000                                                          # a small limit so the test file is cut
    r = R.release(d, 'US', sha1, run='77', now='T1'); idx = json.loads((d / 'data/released/RELEASED.json').read_text()); rel = d / 'data/released'
    check('US: only the map files are released (no layer file, tracts, overrides or index)',
          sorted(idx['files']) == ['outlines/US-FL.geojson.gz', 'us-key/US-FL.json', 'us-key/US-WI.json', 'us-key/layers.json'] and r['files'] == 4)
    check('a file under the limit is the same bytes as the working file (git stores it once)',
          (rel / 'outlines/US-FL.geojson.gz').read_bytes() == (d / 'data/outlines/US-FL.geojson.gz').read_bytes())
    parts = idx['files']['us-key/US-WI.json']; got = {}
    for p, v in parts: got.update(json.loads((rel / p).read_text())['parks'])
    check('a file over the limit is cut into parts under it, and the parts hold every park once',
          len(parts) > 1 and all((rel / p).stat().st_size <= R.CAP for p, _ in parts) and got == big['parks'] and not (rel / 'us-key/US-WI.json').exists() and r['cut'] == ['us-key/US-WI.json'])
    check('each file has its own version (sha256 of the released bytes)', all(re.fullmatch(r'[0-9a-f]{12}', v) for ps in idx['files'].values() for _, v in ps)
          and idx['files']['us-key/US-FL.json'][0][1] == __import__('hashlib').sha256((rel / 'us-key/US-FL.json').read_bytes()).hexdigest()[:12])
    check('the area row names the commit, the time and the run', idx['areas'] == {'US': {'sha': sha1, 'time': 'T1', 'run': '77', 'files': 4}})
    # main moves on: FL changes, WI shrinks under the limit, a new state appears
    (d / 'data/us-key/US-FL.json').write_text(json.dumps({'st': 'FL', 'parks': {'US-1': {'g': 'pin'}}}))
    (d / 'data/us-key/US-WI.json').write_text('{"parks":{}}'); (d / 'data/us-key/US-GA.json').write_text('{"parks":{}}')
    sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', 'two'); sha2 = sh(d, 'git', 'rev-parse', 'HEAD').stdout.strip()
    v_out = idx['files']['outlines/US-FL.geojson.gz'][0][1]; v_fl = idx['files']['us-key/US-FL.json'][0][1]
    check('the working copy moving does not change what is released', json.loads((rel / 'us-key/US-FL.json').read_text())['parks']['US-1']['g'] == 'official')
    R.release(d, 'CA', sha2, now='T2'); idx = json.loads((rel / 'RELEASED.json').read_text())
    check('releasing Canada leaves the US files and versions alone', idx['files']['us-key/US-FL.json'][0][1] == v_fl and idx['areas']['US']['sha'] == sha1 and 'ca-key/CA-ON.json' in idx['files'])
    r = R.release(d, 'US', sha2, now='T3'); idx = json.loads((rel / 'RELEASED.json').read_text())
    check('a new US release: the changed file gets a new version, the unchanged one keeps its version',
          idx['files']['us-key/US-FL.json'][0][1] != v_fl and idx['files']['outlines/US-FL.geojson.gz'][0][1] == v_out and 'us-key/US-GA.json' in idx['files'])
    check('old parts are removed when the file fits again', r['removed'] == len(parts) and not list((rel / 'us-key').glob('US-WI.p*')) and (rel / 'us-key/US-WI.json').exists())
    before = snap(rel)
    for area, sha, why in (('US', sha2[:12], 'a short sha'), ('US', 'f' * 40, 'a commit that does not exist'), ('fers', sha2, 'an area that is not released here')):
        rc = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_release.py'), '--repo', str(d), '--area', area, '--sha', sha], capture_output=True, text=True)
        check(f'{why}: exit 1 and nothing written', rc.returncode == 1 and 'Nothing was released' in rc.stdout and snap(rel) == before)
    (d / 'data/us-key/US-WI.json').write_text(json.dumps({'parks': {'US-1': {'m': ['x' * 50_000]}}}))
    sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', 'three'); sha3 = sh(d, 'git', 'rev-parse', 'HEAD').stdout.strip()
    try: R.release(d, 'US', sha3); bad = False
    except R.ReleaseError: bad = True
    check('a file that cannot be cut under the limit: an error and nothing written', bad and snap(rel) == before)
    # outline files are cut by features
    R.CAP = 150; ps = R.cut('outlines/US-AK.geojson.gz', gzj({'type': 'FeatureCollection', 'kpc': {'area': 'US-AK'}, 'features': [feat(i) for i in range(40)]}))
    refs = [f['properties']['ref'] for _, b in ps for f in json.loads(gzip.decompress(b))['features']]
    check('an outline file over the limit is cut by features: every outline once, names US-AK.pN.geojson.gz',
          len(ps) > 1 and refs == [f'US-{i}' for i in range(40)] and all(re.fullmatch(r'outlines/US-AK\.p\d+\.geojson\.gz', p) and len(b) <= 150 for p, b in ps))
R.CAP = 1_000_000

# ---- the loaders
names = ['kpc-bounds.js', 'kpc-padus-layer.js', 'kpc-us-planner.js', 'kpc-gps.js']; src = {n: (ROOT / n).read_text(encoding='utf-8') for n in names}
blk = lambda s: s[s.index('/* >>> kpc_released'):s.index('/* <<< kpc_released */')]
check('the four loaders carry the same KPCREL block', len({blk(s) for s in src.values()}) == 1 and "fetch('data/released/RELEASED.json', { cache: 'no-cache' })" in blk(src[names[0]]))
direct = re.compile(r"fetch\(\s*['\"]data/(us-key/US-|us-key/layers|ca-key/(CA-|refs|layers)|world-key/(['\"]|layers))")
body = {n: s[s.index('/* <<< kpc_released */'):] for n, s in src.items()}
check('no loader fetches a key file directly any more', not any(direct.search(b) for b in body.values()))
check('outline files come through KPCREL in both map layers', all("KPCREL.get('data/outlines/US-' + st + '.geojson.gz')" in body[n] for n in names[:2]))
check('tracts and the Map Rep tools still read the working copy', "'data/us-key/tracts/US-' + code + '.json'" in body['kpc-bounds.js']
      and 'KPCREL' not in (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8'))
check('the helper leaves a review page on the working copy', "w.KPC_WORKING_COPY === true ||" in blk(src[names[0]]))
for h in ('kpc-maprep.html', 'kpc-maprep-reps.html'):
    hs = (ROOT / h).read_text(encoding='utf-8', errors='replace'); first = min(hs.index(x) for x in ('kpc-bounds.js', 'kpc-padus-layer.js'))
    check(f'{h} sets KPC_WORKING_COPY before the boundary scripts', 'window.KPC_WORKING_COPY=true' in hs and hs.index('window.KPC_WORKING_COPY=true') < first)
pub = [p.name for p in ROOT.glob('*.html') if 'KPC_WORKING_COPY' in p.read_text(encoding='utf-8', errors='replace')]
check('only the two Map Rep pages set it', sorted(pub) == ['kpc-maprep-reps.html', 'kpc-maprep.html'])
pf = (ROOT / '.github/scripts/kpc_preflight.py').read_text()
check('preflight: a new or newly grown file over 1 MB fails; one already over on the base only warns', "old_big = [f for f in over if (_was(f) or 0) > 1_000_000]" in pf and "big = [f for f in over if f not in old_big]" in pf)
html = ''.join(p.read_text(encoding='utf-8', errors='replace') for p in ROOT.glob('*.html'))
check('every page loads the new loader files (version stamp bumped)', not re.search(r'kpc-(bounds|padus-layer|us-planner|gps)\.js\?v=(?!20261111rel2)', html))

# ---- the helper itself, run in node with a fake fetch
node = shutil.which('node')
if node:
    js = r"""
const files = %s;
let asked = [];
globalThis.window = globalThis;
const real = { ok: true };
window.fetch = (u, o) => { asked.push([u, (o || {}).cache]); const k = u.split('?')[0]; const b = files[k];
  return Promise.resolve(b === undefined ? { ok: false } : { ok: true, json: () => Promise.resolve(JSON.parse(b)), arrayBuffer: () => Promise.resolve(new TextEncoder().encode(b).buffer) }); };
%s
(async () => {
  const out = {};
  out.one = await KPCREL.get('data/us-key/US-FL.json');
  out.parts = await KPCREL.get('data/us-key/US-WI.json');
  out.feat = await KPCREL.get('data/outlines/US-AK.geojson.gz');
  out.notReleased = await KPCREL.get('data/us-key/US-GA.json');
  out.halfMissing = await KPCREL.get('data/us-key/US-TX.json');
  out.workingArea = await KPCREL.get('data/ca-key/CA-ON.json');
  // a caller's own fetch whose answer has json() only (no arrayBuffer): the working file must still be read, as before
  out.plain = await KPCREL.get('data/ca-key/CA-BC.json', p => Promise.resolve({ ok: true, json: () => Promise.resolve({ parks: { plain: {} } }) }));
  out.plain404 = await KPCREL.get('data/ca-key/CA-QC.json', p => Promise.resolve({ ok: false }));
  window.KPC_WORKING_COPY = true; out.review = await KPCREL.get('data/us-key/US-GA.json'); window.KPC_WORKING_COPY = false;
  out.asked = asked;
  console.log(JSON.stringify(out));
})();
"""
    files = {
        'data/released/RELEASED.json': json.dumps({'areas': {'US': {'sha': 'x'}}, 'files': {
            'us-key/US-FL.json': [['us-key/US-FL.json', 'aaa']], 'us-key/US-WI.json': [['us-key/US-WI.p1.json', 'b1'], ['us-key/US-WI.p2.json', 'b2']],
            'outlines/US-AK.geojson.gz': [['outlines/US-AK.p1.geojson.gz', 'c1'], ['outlines/US-AK.p2.geojson.gz', 'c2']],
            'us-key/US-TX.json': [['us-key/US-TX.p1.json', 'd1'], ['us-key/US-TX.p2.json', 'd2']]}}),
        'data/released/us-key/US-FL.json': '{"parks":{"US-1":{"g":"official"}}}',
        'data/released/us-key/US-WI.p1.json': '{"st":"WI","kpc_part":[1,2],"parks":{"US-1":{}}}', 'data/released/us-key/US-WI.p2.json': '{"st":"WI","kpc_part":[2,2],"parks":{"US-2":{}}}',
        'data/released/outlines/US-AK.p1.geojson.gz': '{"features":[{"id":1}]}', 'data/released/outlines/US-AK.p2.geojson.gz': '{"features":[{"id":2}]}',
        'data/released/us-key/US-TX.p1.json': '{"parks":{"US-9":{}}}',
        'data/us-key/US-GA.json': '{"parks":{"working":{}}}', 'data/ca-key/CA-ON.json': '{"parks":{"CA-1":{}}}',
    }
    with tempfile.TemporaryDirectory() as t:
        p = pathlib.Path(t) / 'h.js'; p.write_text(js % (json.dumps(files), blk(src['kpc-bounds.js']) + '/* <<< kpc_released */'))
        r = subprocess.run([node, str(p)], capture_output=True, text=True); o = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else {}
    asked = o.get('asked') or []
    check('helper: a released file is read from data/released with its own version, cached', ['data/released/us-key/US-FL.json?v=aaa', 'force-cache'] in asked and o.get('one') == {'parks': {'US-1': {'g': 'official'}}})
    check('helper: RELEASED.json is asked for once, never from the cache', [a for a in asked if 'RELEASED.json' in a[0]] == [['data/released/RELEASED.json', 'no-cache']])
    check('helper: key parts are put together', o.get('parts') == {'st': 'WI', 'parks': {'US-1': {}, 'US-2': {}}})
    check('helper: outline parts are put together', o.get('feat') == {'features': [{'id': 1}, {'id': 2}]})
    check('helper: a file not in a released area is NOT read from the working copy', o.get('notReleased') is None)
    check('helper: a missing part = nothing (never half a file)', o.get('halfMissing') is None)
    check('helper: a review page (KPC_WORKING_COPY) reads the working file even for a released area', o.get('review') == {'parks': {'working': {}}})
    check('helper: with nothing released the caller\'s own response is read with json() as before (no arrayBuffer needed)', o.get('plain') == {'parks': {'plain': {}}} and o.get('plain404') is None)
    check('helper: an area never released reads the working file as before', o.get('workingArea') == {'parks': {'CA-1': {}}})
else: print('SKIP node not installed: the helper run')

wf = (ROOT / '.github/workflows/kpc-release.yml').read_text()
import yaml
y = yaml.safe_load(wf); on = y.get('on') or y.get(True)
check('only an account in KPC_RELEASE_ACTORS may release; an empty list releases nothing', 'ALLOWED: ${{ vars.KPC_RELEASE_ACTORS }}' in wf and wf.index('KPC_RELEASE_ACTORS. Nothing was released') < wf.index('kpc_release.py --area'))
check('the release workflow is by hand only, one commit, and takes a commit on main', list(on) == ['workflow_dispatch'] and wf.count('git commit') == 1
      and 'merge-base --is-ancestor "$SOURCE_SHA" origin/main' in wf and on['workflow_dispatch']['inputs']['area']['options'] == ['US', 'CA', 'world'])
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
