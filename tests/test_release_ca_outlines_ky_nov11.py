#!/usr/bin/env python3
"""KPC owner, 2026-11-11 (job 3, first half): the release script also freezes the Canada park outlines (data/canada-bounds, area CA,
in its own sub-index) and Kentucky (new area KY: data/ky-answer-key.json + the reviewed root ky-*.geojson list, released as ky/<name>).
The page loaders are NOT switched yet (that half waits for the site review): this test also proves that a RELEASED.json with the
new subs / KY rows changes nothing a page does today. Offline: temp repos and node with a stub fetch only.
KPC_COMPAT_BLOCKS=<file>[:<file>...] runs the compatibility check against other copies of the KPCREL block too (e.g. a review stack)."""
import gzip, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_release as R

ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)

def sh(d, *a): return subprocess.run(a, cwd=d, capture_output=True, text=True)
def snap(d): return {str(p.relative_to(d)): p.read_bytes() for p in sorted(pathlib.Path(d).rglob('*')) if p.is_file()} if pathlib.Path(d).exists() else {}
def commit(d, m): sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', m); return sh(d, 'git', 'rev-parse', 'HEAD').stdout.strip()
def fc(feats, **head): return dict({'type': 'FeatureCollection', 'features': feats}, **head)
def poly(i, n=4): return [[[i, 0], [i + 1, 0], [i + 1, 1], [i, 1], [i, 0]]] * n

# ---- 1. the file lists come from the pages and the folders, not from a guess
pages = {p.name: p.read_text(encoding='utf-8', errors='replace') for p in sorted(ROOT.glob('*.js')) + sorted(ROOT.glob('*.html'))}
fetched = {m for s in pages.values() for m in re.findall(r'ky-[a-z0-9-]+\.geojson', s)}
check('the reviewed KY list is exactly the root ky-*.geojson files the pages name (a new Kentucky layer cannot be forgotten)',
      set(R.KY_LAYERS) == fetched and len(R.KY_LAYERS) == len(set(R.KY_LAYERS)) and sorted(R.KY_LAYERS) == list(R.KY_LAYERS))
check('every listed KY layer is a root file of this repo', all((ROOT / n).is_file() for n in R.KY_LAYERS))
check('ky-overlaps.geojson is on the list; kpc-ky-data.json is not released (the owner keeps it as it is for now)',
      'ky-overlaps.geojson' in R.KY_LAYERS and not any('kpc-ky-data' in str(s[1]) for s in R.AREAS['KY']))
check('KY = the answer key + the layer list, both released under ky/', R.sources('KY') == [('data', ('ky-answer-key.json',), 'ky'), ('', R.KY_LAYERS, 'ky')])
cb = sorted(p.name for p in (ROOT / 'data/canada-bounds').glob('*.json'))
pat = dict((f, p) for f, p, _ in R.sources('CA'))['data/canada-bounds']
parks = [n for n in cb if re.fullmatch(pat, n)]
check(f'the Canada outline pattern takes every park file CA-<digits>.json ({len(parks)}) and no bot file',
      parks == [n for n in cb if re.fullmatch(r'CA-\d+\.json', n)] and 'index.json' not in parks and 'refine-report.json' not in parks and len(parks) > 2000)
check('no page reads data/canada-bounds/index.json or refine-report.json (so neither is released)',
      not any(re.search(r'canada-bounds/(index|refine-report)\.json', s) for s in pages.values()))
check('the CA key sources are as before (the 17 released ca-key files)', R.sources('CA')[0] == ('data/ca-key', r'CA-[A-Z]{2}\.json|refs\.json|layers\.json', 'ca-key'))
check('world is untouched', R.sources('world') == [('data/world-key', r'[A-Z]{2}\.json|layers\.json', 'world-key')] and R.SUBS == {'canada-bounds/': ('CA', 'canada-bounds/INDEX.json')})

# ---- 2. the ONE part scheme learns plain .geojson; .geojson.gz and .json behave as before
check('part names: .geojson.gz and .json as before, .geojson the same way',
      [R.part_name('outlines/US-AK.geojson.gz', 2), R.part_name('us-key/US-WI.json', 3), R.part_name('ky/ky-usace.geojson', 2), R.part_name('ky/ky-usace.geojson', 1)]
      == ['outlines/US-AK.p2.geojson.gz', 'us-key/US-WI.p3.json', 'ky/ky-usace.p2.geojson', 'ky/ky-usace.geojson'])
check('PART_RE knows a .geojson part; an area file is still not a part',
      R.PART_RE.match('ky-usace.p2.geojson').groups() == ('ky-usace', '2', '.geojson') and R.PART_RE.match('US-AK.p2.geojson.gz').groups() == ('US-AK', '2', '.geojson.gz')
      and not R.PART_RE.match('US-AK.geojson.gz') and not R.PART_RE.match('ky-usace.geojson'))
R.CAP = 3_000
big = fc([{'type': 'Feature', 'properties': {'NAME': f'WMA {i}', 'n': i}, 'geometry': {'type': 'MultiPolygon', 'coordinates': [poly(i)]}} for i in range(40)], name='KY test')
raw = json.dumps(big).encode()
ps = R.cut('ky/ky-hunting-areas.geojson', raw)
check('a .geojson over the cap is cut by features: names, kpc_part [i, N, tag], each part under the cap, plain JSON (not gzip)',
      len(ps) > 1 and [p for p, _ in ps] == ['ky/ky-hunting-areas.geojson'] + [f'ky/ky-hunting-areas.p{i}.geojson' for i in range(2, len(ps) + 1)]
      and all(len(b) <= R.CAP and b[:1] == b'{' for _, b in ps)
      and [json.loads(b)['kpc_part'][:2] for _, b in ps] == [[i, len(ps)] for i in range(1, len(ps) + 1)] and len({json.loads(b)['kpc_part'][2] for _, b in ps}) == 1)
j = R.join([json.loads(b) for _, b in ps])
check('the parts put back together = the original FeatureCollection (same features in order, header kept, same content hash)',
      R.canon(j) == R.canon(big) and [f['properties']['n'] for f in j['features']] == list(range(40)) and j['name'] == 'KY test')
one = fc([{'type': 'Feature', 'properties': {'NAME': 'Big lake'}, 'geometry': {'type': 'MultiPolygon', 'coordinates': [poly(i, 2) for i in range(60)]}}])
ps1 = R.cut('ky/ky-usace.geojson', json.dumps(one).encode())
check('one feature that alone does not fit is cut by its polygons (kpc_piece) and joins back to the same geometry',
      len(ps1) > 1 and all('kpc_piece' in f for _, b in ps1 for f in json.loads(b)['features']) and R.canon(R.join([json.loads(b) for _, b in ps1])) == R.canon(one))
two = fc([one['features'][0], dict(one['features'][0], properties={'NAME': 'Other lake'})])
try: R.cut('ky/ky-usace.geojson', json.dumps(two).encode()); two_bad = False
except R.ReleaseError: two_bad = True
check('two ref-less features that both need pieces: an error (never a wrong join)', two_bad)
small = b'{"type":"FeatureCollection","features":[]}  \n'
check('a .geojson under the cap is released byte for byte', R.cut('ky/ky-kpc-drawn.geojson', small) == [('ky/ky-kpc-drawn.geojson', small)])
psg = R.cut('outlines/US-AK.geojson.gz', R.gz(json.dumps(fc([{'type': 'Feature', 'properties': {'ref': f'US-{i}', 'h': ''.join(hashlib.sha256(f'{i}-{k}'.encode()).hexdigest() for k in range(8))}, 'geometry': None} for i in range(30)])).encode()))
check('a .geojson.gz is still cut into gzip parts', len(psg) > 1 and all(b[:2] == b'\x1f\x8b' for _, b in psg))
R.CAP = 1_000_000

# ---- 3. the release on a temp repo
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t) / 'r'; d.mkdir(); sh(d, 'git', 'init', '-q'); sh(d, 'git', 'config', 'user.name', 't'); sh(d, 'git', 'config', 'user.email', 't@t')
    for f in ('data/outlines', 'data/us-key', 'data/ca-key', 'data/canada-bounds', 'data/world-key'): (d / f).mkdir(parents=True)
    (d / 'data/outlines/US-FL.geojson.gz').write_bytes(R.gz(json.dumps(fc([])).encode()))
    (d / 'data/us-key/US-FL.json').write_text('{"parks":{"US-1":{"g":"official"}}}')
    for n in ('CA-ON.json', 'refs.json', 'layers.json'): (d / 'data/ca-key' / n).write_text('{"parks":{}}' if n.startswith('CA') else '{}')
    for i in (1001, 1002, 12345): (d / f'data/canada-bounds/CA-{i}.json').write_text(json.dumps({'type': 'Feature', 'properties': {'ref': f'CA-{i}'}, 'geometry': {'type': 'Point', 'coordinates': [1, 2]}}, indent=2))
    (d / 'data/canada-bounds/index.json').write_text('{"found":{}}'); (d / 'data/canada-bounds/refine-report.json').write_text('{}')
    (d / 'data/world-key/FR.json').write_text('{}')
    (d / 'data/ky-answer-key.json').write_text('{"parks":{"US-1":{}}}  ')
    for n in R.KY_LAYERS: (d / n).write_text(json.dumps(fc([{'type': 'Feature', 'properties': {'NAME': n}, 'geometry': None}]), indent=1))
    (d / 'ky-usace.geojson').write_bytes(json.dumps(fc([{'type': 'Feature', 'properties': {'NAME': f'L{i}', 'x': 'y' * 300}, 'geometry': {'type': 'MultiPolygon', 'coordinates': [poly(i, 20)]}} for i in range(60)], name='USACE'), indent=1).encode())
    (d / 'ky-not-on-the-list.geojson').write_text('{}'); (d / 'kpc-ky-data.json').write_text('{}')
    sha1 = commit(d, 'one'); rel = d / 'data/released'; ip = rel / 'RELEASED.json'
    R.CAP = 40_000
    R.release(d, 'US', sha1, run='1', now='T1')
    # Canada: the key AND the park outlines; the outline rows go to the sub-index
    rc = R.release(d, 'CA', sha1, run='2', now='T2'); idx = json.loads(ip.read_text()); sub = rel / 'canada-bounds/INDEX.json'
    sb = sub.read_bytes(); si = json.loads(sb)
    check('CA: the key files and the 3 park outlines are released; index.json / refine-report.json are not',
          rc['files'] == 6 and sorted(p.name for p in (rel / 'canada-bounds').iterdir()) == ['CA-1001.json', 'CA-1002.json', 'CA-12345.json', 'INDEX.json'])
    check('CA: the outline files are byte-identical to the working files', all((rel / f'canada-bounds/CA-{i}.json').read_bytes() == (d / f'data/canada-bounds/CA-{i}.json').read_bytes() for i in (1001, 1002, 12345)))
    check('RELEASED.json keeps the key rows and NO canada-bounds row; subs names the sub-index with its own version',
          sorted(k for k in idx['files'] if k.startswith('ca')) == ['ca-key/CA-ON.json', 'ca-key/layers.json', 'ca-key/refs.json']
          and idx['subs'] == {'canada-bounds/': {'area': 'CA', 'file': 'canada-bounds/INDEX.json', 'v': hashlib.sha256(sb).hexdigest()[:12], 'files': 3}})
    check('the sub-index: same row shape as files, the release sha / time / run of areas.CA, one row per line',
          si['files'] == {f'canada-bounds/CA-{i}.json': [[f'canada-bounds/CA-{i}.json', hashlib.sha256((rel / f'canada-bounds/CA-{i}.json').read_bytes()).hexdigest()[:12]]] for i in (1001, 1002, 12345)}
          and (si['area'], si['prefix'], si['sha'], si['time'], si['run']) == ('CA', 'canada-bounds/', sha1, 'T2', '2') == ('CA', 'canada-bounds/', idx['areas']['CA']['sha'], idx['areas']['CA']['time'], idx['areas']['CA']['run'])
          and sb.decode().count('\n') == 3 + 2)
    check('the area row keeps its form {files, run, sha, time}', idx['areas']['CA'] == {'sha': sha1, 'time': 'T2', 'run': '2', 'files': 6})
    s_ca = snap(rel); i_ca = idx
    # dry run: lists, writes nothing
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_release.py'), '--repo', str(d), '--area', 'KY', '--sha', sha1, '--dry-run'], capture_output=True, text=True)
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith('would write')]
    check('--dry-run lists the KY files with sizes and writes nothing',
          r.returncode == 0 and 'Nothing was written' in r.stdout and snap(rel) == s_ca and any(ln.split()[-1] == 'data/released/ky/ky-answer-key.json' and ln.split()[3] == '23' for ln in lines)
          and sum(1 for ln in lines if '/ky/' in ln) == len(R.KY_LAYERS) + 1 and any('RELEASED.json' in ln for ln in lines))
    R.CAP = 40_000
    plan = R.release(d, 'CA', sha1, run='2', now='T2', dry_run=True)
    check('dry run of CA lists the key, the outlines and INDEX.json', {p for p, _, _ in plan['plan']} >= {'canada-bounds/INDEX.json', 'canada-bounds/CA-1001.json', 'ca-key/refs.json', 'RELEASED.json'} and snap(rel) == s_ca)
    # Kentucky
    rk = R.release(d, 'KY', sha1, run='3', now='T3'); idx = json.loads(ip.read_text()); s_ky = snap(rel)
    check('KY: the answer key and every listed layer are released under ky/; the unlisted file and kpc-ky-data.json are not',
          rk['files'] == len(R.KY_LAYERS) + 1 and sorted(k for k in idx['files'] if k.startswith('ky/')) == sorted(['ky/ky-answer-key.json'] + [f'ky/{n}' for n in R.KY_LAYERS])
          and not (rel / 'ky/ky-not-on-the-list.geojson').exists() and not list(rel.rglob('kpc-ky-data.json')))
    check('KY: files under the cap are byte-identical to the working files', (rel / 'ky/ky-answer-key.json').read_bytes() == (d / 'data/ky-answer-key.json').read_bytes()
          and all((rel / 'ky' / n).read_bytes() == (d / n).read_bytes() for n in R.KY_LAYERS if n != 'ky-usace.geojson'))
    up = idx['files']['ky/ky-usace.geojson']
    check('KY: a layer over the cap is cut (part 1 keeps its name, .p2.geojson ...), each part under the cap, and joins back to the original',
          rk['cut'] == ['ky/ky-usace.geojson'] and len(up) > 1 and up[1][0] == 'ky/ky-usace.p2.geojson' and all((rel / p).stat().st_size <= R.CAP for p, _ in up)
          and R.canon(R.join([json.loads((rel / p).read_bytes()) for p, _ in up])) == R.canon(json.loads((d / 'ky-usace.geojson').read_bytes())))
    check('KY: US and CA rows, areas, subs and every one of their files are byte-identical',
          all(s_ky[k] == v for k, v in s_ca.items() if k != 'RELEASED.json') and {k: v for k, v in idx['files'].items() if not k.startswith('ky/')} == i_ca['files']
          and {a: idx['areas'][a] for a in ('US', 'CA')} == {a: i_ca['areas'][a] for a in ('US', 'CA')} and idx['subs'] == i_ca['subs'] and idx['areas']['KY']['files'] == len(R.KY_LAYERS) + 1)
    # CA again from the same commit: stable
    R.release(d, 'CA', sha1, run='4', now='T4'); i2 = json.loads(ip.read_text()); s2 = snap(rel)
    check('CA twice: the same rows and versions, the same files; only INDEX.json (its sha / time / run) and its v change',
          i2['files'] == idx['files'] and json.loads((rel / 'canada-bounds/INDEX.json').read_bytes())['files'] == si['files']
          and all(s2[k] == v for k, v in s_ky.items() if k not in ('RELEASED.json', 'canada-bounds/INDEX.json')) and set(s2) == set(s_ky)
          and i2['subs']['canada-bounds/']['v'] == hashlib.sha256(s2['canada-bounds/INDEX.json']).hexdigest()[:12])
    # main moves: a park outline goes, one changes; a KY layer shrinks under the cap
    (d / 'data/canada-bounds/CA-1002.json').unlink(); (d / 'data/canada-bounds/CA-1001.json').write_text('{"type":"Feature","properties":{},"geometry":null}')
    (d / 'ky-usace.geojson').write_text('{"type":"FeatureCollection","features":[]}')
    sha2 = commit(d, 'two'); s_before = snap(rel)
    r2 = R.release(d, 'CA', sha2, now='T5'); i3 = json.loads(ip.read_text()); si3 = json.loads((rel / 'canada-bounds/INDEX.json').read_text())
    check('a park outline no longer on main is removed from the release and the sub-index; a changed one gets a new version',
          r2['removed'] == 1 and not (rel / 'canada-bounds/CA-1002.json').exists() and sorted(si3['files']) == ['canada-bounds/CA-1001.json', 'canada-bounds/CA-12345.json']
          and si3['files']['canada-bounds/CA-1001.json'] != si['files']['canada-bounds/CA-1001.json'] and si3['files']['canada-bounds/CA-12345.json'] == si['files']['canada-bounds/CA-12345.json']
          and i3['subs']['canada-bounds/']['files'] == 2 and all(snap(rel)[k] == v for k, v in s_before.items() if k.startswith(('ky/', 'us-key/', 'outlines/'))))
    r3 = R.release(d, 'KY', sha2, now='T6'); i4 = json.loads(ip.read_text())
    check('a KY layer that fits again: its old parts are removed, the CA sub-index is left alone',
          r3['removed'] == len(up) - 1 and not list((rel / 'ky').glob('ky-usace.p*')) and i4['files']['ky/ky-usace.geojson'][0][0] == 'ky/ky-usace.geojson' and i4['subs'] == i3['subs'])
    # fail closed
    def refused(area, sha, why):
        before = snap(rel)
        try: R.release(d, area, sha, now='TX'); bad = False
        except R.ReleaseError: bad = True
        check(f'{why}: an error and nothing written', bad and snap(rel) == before)
    (d / 'ky-dawkins.geojson').unlink(); sha3 = commit(d, 'three')
    refused('KY', sha3, 'a file of the reviewed KY list missing at the commit')
    sh(d, 'git', 'checkout', '-q', sha2, '--', 'ky-dawkins.geojson'); shutil.rmtree(d / 'data/canada-bounds'); sha4 = commit(d, 'four')
    refused('CA', sha4, 'data/canada-bounds gone at the commit while outlines from it are released')
    good_sub = (rel / 'canada-bounds/INDEX.json').read_bytes(); (rel / 'canada-bounds/INDEX.json').write_text('{not json');
    refused('CA', sha2, 'the last sub-index cannot be read')
    (rel / 'canada-bounds/INDEX.json').write_bytes(good_sub)
    R.CAP = 120
    refused('CA', sha2, 'a sub-index or RELEASED.json that would be over the cap')
    R.CAP = 1_000_000
    rc = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_release.py'), '--repo', str(d), '--area', 'ky', '--sha', sha2], capture_output=True, text=True)
    check('an unknown area name: exit 1, nothing released', rc.returncode == 1 and 'Nothing was released' in rc.stdout)
R.CAP = 1_000_000

# ---- 4. compatibility: today's pages with a RELEASED.json that has subs, KY and ky/ rows (the loader half is on hold)
node = shutil.which('node')
blk = lambda s: s[s.index('/* >>> kpc_released'):s.index('/* <<< kpc_released */')] + '/* <<< kpc_released */'
blocks = {'main': blk((ROOT / 'kpc-bounds.js').read_text(encoding='utf-8'))}
for i, f in enumerate(x for x in os.environ.get('KPC_COMPAT_BLOCKS', '').split(':') if x):
    blocks[f'extra{i + 1}:{pathlib.Path(f).name}'] = blk(pathlib.Path(f).read_text(encoding='utf-8'))
old_idx = json.loads((ROOT / 'data/released/RELEASED.json').read_text()) if (ROOT / 'data/released/RELEASED.json').exists() else None
if node and old_idx:
    new_idx = json.loads(json.dumps(old_idx))
    new_idx['areas']['CA'] = dict(new_idx['areas']['CA'], files=new_idx['areas']['CA']['files'] + 2952, run='9', time='2026-11-12T00:00:00Z')
    new_idx['areas']['KY'] = {'sha': 'f' * 40, 'time': '2026-11-12T00:05:00Z', 'run': '10', 'files': 19}
    for n in ('ky-answer-key.json',) + R.KY_LAYERS: new_idx['files'][f'ky/{n}'] = [[f'ky/{n}', 'abcabcabcabc']]
    new_idx['files']['ky/ky-usace.geojson'] = [['ky/ky-usace.geojson', 'a1'], ['ky/ky-usace.p2.geojson', 'a2']]
    new_idx['subs'] = {'canada-bounds/': {'area': 'CA', 'file': 'canada-bounds/INDEX.json', 'v': '0123456789ab', 'files': 2952}}
    us = next(k for k in old_idx['files'] if k.startswith('us-key/US-')); uo = next(k for k in old_idx['files'] if k.startswith('outlines/'))
    asks = [['data/' + us, 0], ['data/' + uo, 0], ['data/ca-key/CA-ON.json', 0], ['data/ca-key/refs.json', 1], ['data/ca-key/layers.json', 0],
            ['data/us-key/US-ZZ.json', 0], ['data/world-key/FR.json', 1], ['data/us-key/tracts/US-FL.json', 1],
            ['data/canada-bounds/CA-1001.json', 0], ['data/canada-bounds/CA-1001.json', 1], ['canada-bounds/CA-1001.json', 0],
            ['data/ky-answer-key.json', 0], ['data/ky-answer-key.json', 1], ['ky-usace.geojson', 0], ['ky-usace.geojson', 1], ['ky/ky-usace.geojson', 0], ['ky/ky-answer-key.json', 1],
            ['data/' + us, 2], ['data/canada-bounds/CA-1001.json', 2], ['ky-usace.geojson', 2]]   # 0 = KPCREL.get(p), 1 = with the caller's own fetch, 2 = Map Rep (KPC_WORKING_COPY)
    js = r"""
const IDX = %s, ASKS = %s;
globalThis.window = globalThis; const store = {}; let asked = [], maxLS = 0;
window.localStorage = { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { maxLS = Math.max(maxLS, String(v).length); if (String(v).length > 4e6) throw new Error('quota'); store[k] = String(v); } };
const body = u => u === 'data/released/RELEASED.json' ? JSON.stringify(IDX) : JSON.stringify({ from: u.split('?')[0], parks: {}, features: [] });
window.fetch = (u, o) => { asked.push(u); const b = body(u);
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(JSON.parse(b)), arrayBuffer: () => Promise.resolve(new TextEncoder().encode(b).buffer), text: () => Promise.resolve(b) }); };
%s
(async () => {
  const out = [];
  for (const [p, how] of ASKS) {
    asked = []; let got, threw = null;
    window.KPC_WORKING_COPY = how === 2;
    try { got = how === 1 ? await KPCREL.get(p, q => window.fetch('OWN:' + q)) : await KPCREL.get(p); } catch (e) { threw = String(e); }
    let u = null; try { u = await KPCREL.urls(p); } catch (e) { threw = threw || String(e); }
    out.push({ p, how, got, threw, urls: u, asked: asked.filter(x => x.indexOf('RELEASED.json') < 0) });
  }
  window.KPC_WORKING_COPY = false;
  console.log(JSON.stringify({ out, maxLS }));
})().catch(e => console.log(JSON.stringify({ fatal: String(e) })));
"""
    def run(block, idx):
        with tempfile.TemporaryDirectory() as t:
            p = pathlib.Path(t) / 'c.js'; p.write_text(js % (json.dumps(idx), json.dumps(asks), block))
            r = subprocess.run([node, str(p)], capture_output=True, text=True, timeout=60)
        try: return json.loads(r.stdout.strip().splitlines()[-1])
        except Exception: return {'fatal': r.stdout[-300:] + r.stderr[-300:]}
    for name, block in blocks.items():
        a, b = run(block, old_idx), run(block, new_idx)
        check(f'[{name}] nothing throws with the old or the new RELEASED.json', 'fatal' not in a and 'fatal' not in b and not any(x['threw'] for x in a['out'] + b['out']))
        if 'fatal' in a or 'fatal' in b: continue
        same = [x == y for x, y in zip(a['out'], b['out'])]
        check(f'[{name}] US / CA key and outline requests: the same answers and the same fetches', all(same[:6]) and all(x['urls'] for x in a['out'][:5]))
        # Nov 11 (job 3, loader half): the block now knows canada-bounds/ (CA, sub-index) and ky/ (KY). With KY released a public page
        # reads the released ky/ copy, without it nothing; never a working canada-bounds / ky path (the stub has no real INDEX: nothing).
        pub = lambda o: [x for x in o['out'] if x['how'] != 2 and x['p'].startswith(('data/canada-bounds/', 'canada-bounds/', 'data/ky-', 'ky-', 'ky/'))]
        work = lambda x: [u for u in x['asked'] if not u.startswith('data/released/')]
        check(f'[{name}] world, tracts and Map Rep reads: unchanged by the new index',
              all(x == y for x, y in zip(a['out'], b['out']) if x['how'] == 2 or not x['p'].startswith(('data/canada-bounds/', 'canada-bounds/', 'data/ky-', 'ky-', 'ky/'))))
        check(f'[{name}] a public page never reads a working Canada outline or Kentucky file (old index: nothing; new: released ky/ or nothing)',
              all(not work(x) for x in pub(a) + pub(b))
              and all((x['urls'] or [''])[0].startswith('data/released/ky/') if 'KY' in ix['areas'] else x['urls'] == []
                      for o, ix in ((a, old_idx), (b, new_idx)) for x in pub(o) if 'ky' in x['p']))
        check(f'[{name}] the kept copy of RELEASED.json stays small (under 64 KB; the Canada rows are in the sub-index)', b['maxLS'] < 65_536 and len(json.dumps(new_idx)) < 65_536)
else: print('SKIP node not installed or no data/released/RELEASED.json: the compatibility run')

# ---- 5. what this half does not touch
src = (ROOT / '.github/scripts/kpc_release.py').read_text(encoding='utf-8')
check('the script reads git only (no network) and never writes the working folders', not re.search(r'urllib|requests|http\.client|socket', src) and "root = repo / 'data' / 'released'" in src)
from kpc_key_freeze import RULE_FILES
check('kpc_release.py is not a rules file (no rules hash moves)', not any(f.endswith('kpc_release.py') for fs in RULE_FILES.values() for f in fs))
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
