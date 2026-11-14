#!/usr/bin/env python3
"""The layer intake bot (kpc_layer_intake.py, KPC owner, 2026-11-11): one raw layer in, the original stored untouched and a trimmed
copy in the existing formats. Zero network: every DNS lookup and socket is refused and counted, gh is a stand-in that records its
calls, and the layers are fixtures built here. The repo's own data files are never written (temp copies only)."""
import gzip, json, os, pathlib, shutil, socket, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
S = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(S))
os.environ.pop('KPC_SAVED_ONLY_HOSTS', None)
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


DIALS = []
def _no(kind):
    def f(*a, **k):
        DIALS.append((kind, a[0] if a else None)); raise OSError('test: no network')
    return f
socket.getaddrinfo, socket.create_connection = _no('dns'), _no('tcp')

import kpc_master as M          # noqa: E402
import kpc_master_cli as CLI    # noqa: E402
import kpc_layer_intake as I    # noqa: E402

REPO_FILES = ['data/outlines/layers.json', 'data/outlines/world-baselines.proposed.json', 'data/outlines/world-baselines.approved.json',
              'data/outlines/raw-manifest.json', 'data/outlines/download-sources.json']
before = {f: (ROOT / f).read_bytes() for f in REPO_FILES}


class FakeGh:
    """Records every call. assets: {tag: set of names} (None = the release cannot be read). files: {(tag, name): bytes}."""
    def __init__(self, assets=None, files=None):
        self.calls, self.assets_map, self.files = [], assets or {}, files or {}

    def assets(self, tag, repo):
        self.calls.append(('assets', tag, repo)); a = self.assets_map.get(tag, set())
        return None if a is None else set(a)

    def download(self, tag, asset, dest, repo):
        self.calls.append(('download', tag, asset, repo)); p = pathlib.Path(dest); p.mkdir(parents=True, exist_ok=True)
        if (tag, asset) not in self.files: raise I.Refused(f'{tag}/{asset}: not there')
        (p / asset).write_bytes(self.files[(tag, asset)]); return p / asset

    def upload(self, tag, paths, repo):
        self.calls.append(('upload', tag, [pathlib.Path(x).name for x in paths], repo))
        for x in paths:
            n = pathlib.Path(x).name
            if n in self.assets_map.setdefault(tag, set()): raise I.Refused(f'{n} exists (no --clobber)')
            self.assets_map[tag].add(n); self.files[(tag, n)] = pathlib.Path(x).read_bytes()


def box(x0, y0, x1, y1): return {'type': 'Polygon', 'coordinates': [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}
def feat(oid, name, g, **p): return {'type': 'Feature', 'properties': dict({'OBJECTID': oid, 'NAME': name}, **p), 'geometry': g}


# Bahamas fixture: A by name + pin, B ambiguous (inside two outlines whose names both fit), C by name + pin, D by the layer's id
# field, E inside an outline whose name does not fit, F3 a record no park is near.
BS = [feat(900001, 'Blue Hole', box(-76.10, 24.00, -76.00, 24.10)),
      feat(900002, 'Blue Hole North', box(-76.04, 24.06, -76.01, 24.09)),
      feat(900003, 'Pine Cay Reserve', box(-77.60, 24.90, -77.40, 25.10)),
      feat(900004, 'Far Away Reserve', box(-74.10, 21.90, -73.90, 22.10)),
      feat(900005, 'Other Land', box(-78.60, 26.40, -78.40, 26.60)),
      feat(900006, 'Delta Land', box(-75.10, 22.90, -74.90, 23.10), POTA_REF='BS-9004')]
BS_PARKS = [['POTA', 'BS-9001', 'Blue Hole', 24.02, -76.08, 'u'], ['POTA', 'BS-9002', 'Blue Hole North Park', 24.08, -76.02, 'u'],
            ['POTA', 'BS-9003', 'Pine Cay', 25.0, -77.5, 'u'], ['POTA', 'BS-9004', 'Delta Park', 30.0, -70.0, 'u'],
            ['POTA', 'BS-9005', 'Echo Park', 26.5, -78.5, 'u'], ['POTA', 'US-99001', 'Test Lake Wildlife Management Area', 37.50, -85.00, 'u']]
SIDE = {'area': 'W-BS', 'layer': 'bspa', 'label': 'Protected_Areas_of_The_Bahamas', 'source_url': 'https://example.org/bs/protected_areas.geojson',
        'license': 'test licence', 'expected': 6, 'name_fields': ['NAME'], 'id_fields': ['POTA_REF'], 'record_id_field': 'OBJECTID'}


def setup(tag='t'):
    t = pathlib.Path(tempfile.mkdtemp(prefix=f'kpc-intake-{tag}-'))
    root = t / 'outlines'; root.mkdir()
    for f in ('layers.json', 'world-baselines.proposed.json', 'world-baselines.approved.json', 'raw-manifest.json', 'download-sources.json'):
        shutil.copy(ROOT / 'data' / 'outlines' / f, root / f)
    pr = json.loads((root / 'world-baselines.proposed.json').read_text(encoding='utf-8')); pr['baselines'].pop('W-BS', None)   # a country not proposed yet
    (root / 'world-baselines.proposed.json').write_text(json.dumps(pr, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    (t / 'inbox').mkdir()
    parks = t / 'parks.json'; parks.write_text(json.dumps(BS_PARKS))
    return t, root, parks


def layer(t, feats, name='bs_protected_areas.geojson'):
    p = t / name; p.write_text(json.dumps({'type': 'FeatureCollection', 'features': feats})); return p


def args(t, root, parks, src, side, **kw):
    import argparse
    return argparse.Namespace(source=str(src), sidecar=json.dumps(side), parks=str(parks), out=str(t / kw.pop('out', 'out')), root=str(root),
                              inbox=str(t / 'inbox'), write=kw.pop('write', False), upload_hand=kw.pop('upload_hand', False),
                              upload_first_world=kw.pop('upload_first_world', False))


def snap(d): return {str(p.relative_to(d)): p.read_bytes() for p in sorted(pathlib.Path(d).rglob('*')) if p.is_file()}


# ---- 1) dry run (the default): built in --out, nothing in the repo or on a release ------------------------------------------------
t, root, parks = setup('dry'); src = layer(t, BS); r0, p0 = snap(root), parks.read_bytes(); gh = FakeGh()
rc, rep = I.run(args(t, root, parks, src, SIDE), gh)
out = t / 'out'
check('dry run: exit 0', rc == 0)
check('dry run: no gh call at all (no release read or written)', gh.calls == [])
check('dry run: the outlines folder (layers.json, proposed, approved, raw-manifest, queue) is byte for byte unchanged', snap(root) == r0)
check('dry run: the inbox folder is untouched', not any((t / 'inbox').iterdir()))
check('dry run: the pins file is untouched', parks.read_bytes() == p0)
check('dry run: parks A, C (name + pin) and D (id field) matched; B (ambiguous) and E (no name fits) queued',
      rep['match']['parks'] == 3 and rep['match']['by_id'] == 1 and rep['match']['queue'] == 2)
hf = out / 'hand-W-BS.bspa.geojson.gz'
check('dry run: the checked hand file is in --out, named for fill', hf.is_file() and M.parse_hand_name(hf.name) == ('W-BS', 'bspa'))
check("dry run: fill's own hand-file check passes it", M.hand_file_problem(hf, 'W-BS', 'bspa') == '')
meta, hfe = M.read_layer_file(hf)
ids = sorted(f['properties']['OBJECTID'] for f in hfe)
check('trimmed: the park-relevant records only (the record no park is near is left out); B\'s rival outline is kept',
      ids == [900001, 900002, 900003, 900005, 900006])
check('trimmed: the hand file says trimmed, its full count and its original', meta.get('trimmed') is True and meta.get('count_full') == 6
      and meta['raw']['sha256'] == M.sha256_file(src) and meta['count_expected'] == 5)
check('the original facts are recorded (sha256, size, count, source, licence, date)', rep['original']['sha256'] == M.sha256_file(src)
      and rep['original']['count'] == 6 and rep['original']['license'] == 'test licence' and rep['original']['parts'] == [rep['original']['asset']])
bp = out / 'W-BS.json.gz'
blob = M.load_saved(bp)
check('world bundle: W-BS.json.gz in the world key\'s saved-copy form (cc, saved, detail, thin, recs with src = the key\'s label)',
      blob['cc'] == 'BS' and {r['src'] for r in blob['recs']} == {'Protected_Areas_of_The_Bahamas'} and len(blob['recs']) == 5)
wc = (ROOT / '.github' / 'workflows' / 'kpc-world-cache.yml').read_text(encoding='utf-8')
check('world bundle: saved at the detail kpc-world-cache.yml saves the release copies at (not the coarse live default)',
      f"GEO_DETAIL: '{I.WORLD_DETAIL}'" in wc and f"GEO_THIN: '{I.WORLD_THIN}'" in wc and blob['detail'] == float(I.WORLD_DETAIL) and blob['thin'] == int(I.WORLD_THIN))
check("world bundle: every record carries the world key's own source id (sid), as a live read's records do",
      {r.get('sid') for r in blob['recs']} == {I.world_key_ns()['src_id'](I.world_source('BS', SIDE['label']))})
check('the detail setting does not leak into the environment', 'GEO_DETAIL' not in os.environ and 'GEO_THIN' not in os.environ)
check('world bundle: names from the world key\'s own field rules', sorted(r['n'] for r in blob['recs'])[0] == 'Blue Hole')
check('world bundle: the manifest is stamped and checks', CLI.main(['bundle-manifest', str(bp), '--check']) == 0 and M.is_trimmed(blob)
      and blob['manifest']['made_by'] == 'KPC owner' and blob['manifest']['source_full'] == {'Protected_Areas_of_The_Bahamas': 6})
cache = t / 'cache'; cache.mkdir(); shutil.copy(bp, cache / bp.name)
check('world gate --allow-trimmed takes the bundle (checked against its own manifest)', CLI.main(['gate', '--cache', str(cache), '--root', str(root), '--allow-trimmed']) == 0)
shutil.rmtree(cache); cache.mkdir(); shutil.copy(bp, cache / bp.name)
check('the gate without --allow-trimmed (US / CA) refuses it', CLI.main(['gate', '--cache', str(cache), '--root', str(root)]) == 7)
against = t / 'against'; against.mkdir()
check('save-check refuses the trimmed bundle (a bot never uploads one over a release copy)', CLI.save_check(str(bp), str(against), {}, assets=set(), first_ok=True) != '')
inbox = (out / 'layer-intake-W-BS.bspa.csv').read_text()
check('leftovers: research-inbox rows for B (both rival records) and E, in the inbox format, with record ids',
      inbox.splitlines()[0] == ','.join(I.INBOX_FIELDS) and inbox.count('BS-9002,') == 2 and inbox.count('BS-9005,') == 1 and ',900002,' in inbox)
check('dry run: the proposal row is only reported', any('would be added' in s for s in rep['steps']))
fresh = t / 'fresh'; fresh.mkdir(); bsparks = t / 'bsparks.json'; bsparks.write_text(json.dumps([p for p in BS_PARKS if p[1].startswith('BS-')]))
check("fill's step (trim of the hand file, as check_other runs it) passes", CLI.main(['trim', '--layer-key', 'W-BS.bspa', '--input', str(hf), '--expected', '5',
                                                                                  '--parks', str(bsparks), '--area', 'W-BS', '--root', str(fresh), '--name-fields', 'NAME', '--id-fields', 'POTA_REF']) == 0)
check('... and joins the same parks as the full read', sorted(M.load_area('W-BS', fresh)) == ['BS-9001', 'BS-9003', 'BS-9004'])

# ---- 2) why the rival outline is kept: the matched records alone would settle B by omission --------------------------------------
pk = I.area_parks(CLI.read_parks(parks), 'W-BS'); cfg = I.trim_cfg(I.check_sidecar(SIDE, {}), 'u'); fs = CLI.read_file(src)[0]
_, _, matched = I.indexed_trim(pk, fs, cfg)
only = sorted({i for ix in matched.values() for i in ix})
check('matched records alone: a re-trim would join B to the wrong outline (caught)', I.same_trim(pk, fs, cfg, only, matched) != '')
check('park-relevant records: a re-trim joins exactly the same', I.same_trim(pk, fs, cfg, I.relevant(pk, fs, cfg, matched), matched) == '')

# ---- 3) write: the original first (KPC-Archive layer-originals, no clobber, sidecar last), then the repo files ---------------------
t, root, parks = setup('write'); src = layer(t, BS); approved0 = (root / 'world-baselines.approved.json').read_bytes()
caches0 = json.loads((root / 'layers.json').read_text())['caches']
gh = FakeGh(assets={'layer-originals': set(), 'boundary-cache': {'W-BS.json.gz'}})
rc, rep = I.run(args(t, root, parks, src, SIDE, write=True, upload_hand=True, upload_first_world=True), gh)
check('write: exit 0', rc == 0)
ups = [c for c in gh.calls if c[0] == 'upload']
check('write: the original goes to KPC-Archive layer-originals, the sidecar after it', ups[0][1] == 'layer-originals' and ups[0][3] == I.ARCHIVE
      and ups[1][2] == [rep['original']['asset'] + '.json'])
side = json.loads(gh.files[('layer-originals', rep['original']['asset'] + '.json')])
check('write: the stored original is byte for byte the input', gh.files[('layer-originals', rep['original']['asset'])] == src.read_bytes()
      and side['sha256'] == M.sha256_file(src))
check('write: the hand file goes to boundary-cache (none there yet)', ('upload', 'boundary-cache', ['hand-W-BS.bspa.geojson.gz'], I.LINKS) in gh.calls)
check('write: W-BS.json.gz is NOT uploaded: boundary-cache has one (never replaced by a bot)', not any(c[0] == 'upload' and 'W-BS.json.gz' in c[2] for c in gh.calls))
check('write: the approved baselines file is untouched', (root / 'world-baselines.approved.json').read_bytes() == approved0)
prop = json.loads((root / 'world-baselines.proposed.json').read_text())['baselines'].get('W-BS') or {}
check('write: a proposal row (kind trimmed, the bundle\'s count and sha256)', prop.get('kind') == 'trimmed' and prop.get('expected_count') == 5
      and prop.get('copy_sha256') == rep['bundle']['sha256'])
check('write: layers.json caches (the full-copy baselines) unchanged', json.loads((root / 'layers.json').read_text())['caches'] == caches0)
L = json.loads((root / 'layers.json').read_text())['layers']['W-BS.bspa']
check("write: the layer's own baseline is the FULL count (trim of the full read), not the trimmed count", L['expected_count'] == 6 and L['source_count'] == 6)
check('write: master records from trim', sorted(M.load_area('W-BS', root)) == ['BS-9001', 'BS-9003', 'BS-9004'])
raw = json.loads((root / 'raw-manifest.json').read_text())['files']
row = next((x for x in raw if x['name'] == rep['original']['asset']), {})
check('write: raw-manifest facts only (no licence text)', row.get('sha256') == M.sha256_file(src) and row.get('count') == 6 and 'license' not in row)
check('write: the solver queue CSV (by trim) and the inbox rows', (root / 'solver-queue' / 'W-BS.bspa.csv').is_file() and (t / 'inbox' / 'layer-intake-W-BS.bspa.csv').is_file())
again = I.run(args(t, root, parks, src, SIDE, write=True, out='out2'), gh)
check('write again: same sha256 on layer-originals = not uploaded again; the proposal is not changed',
      again[0] == 0 and sum(1 for c in gh.calls if c[0] == 'upload') == len(ups) and any('already proposed' in s for s in again[1]['steps']))
t4, root4, parks4 = setup('kept'); shutil.copy(ROOT / 'data' / 'outlines' / 'world-baselines.proposed.json', root4 / 'world-baselines.proposed.json')
p4 = (root4 / 'world-baselines.proposed.json').read_bytes(); src4 = layer(t4, BS)
rc4, rep4 = I.run(args(t4, root4, parks4, src4, SIDE, write=True), FakeGh(assets={'layer-originals': set()}))
check("an entry a person already proposed (the real W-BS) is never changed", rc4 == 0 and (root4 / 'world-baselines.proposed.json').read_bytes() == p4)
gh2 = FakeGh(assets={'layer-originals': set(), 'boundary-cache': set()})
t2, root2, parks2 = setup('first'); src2 = layer(t2, BS)
I.run(args(t2, root2, parks2, src2, SIDE, write=True, upload_first_world=True), gh2)
check('first copy + the owner\'s OK: W-BS.json.gz uploaded (no copy on boundary-cache yet)', any(c[0] == 'upload' and c[2] == ['W-BS.json.gz'] for c in gh2.calls))
gh3 = FakeGh(assets={'layer-originals': set(), 'boundary-cache': None})
t3, root3, parks3 = setup('noassets'); src3 = layer(t3, BS)
I.run(args(t3, root3, parks3, src3, SIDE, write=True, upload_first_world=True, upload_hand=True), gh3)
check('boundary-cache list unreadable: nothing uploaded there (a first copy cannot be told from a failed read)',
      not any(c[0] == 'upload' and c[1] == 'boundary-cache' for c in gh3.calls))

# ---- 4) the original is stored first, fail closed ---------------------------------------------------------------------------------
t, root, parks = setup('clash'); src = layer(t, BS); r0 = snap(root)
asset, _ = I.original_plan(src, {'name': src.name, 'size': src.stat().st_size, 'sha256': M.sha256_file(src), 'date': '2026-11-11'}, I.check_sidecar(SIDE, {}), 6)
gh = FakeGh(assets={'layer-originals': {asset + '.json'}}, files={('layer-originals', asset + '.json'): json.dumps({'sha256': 'f' * 64}).encode()})
rc, _ = I.run(args(t, root, parks, src, SIDE, write=True), gh)
check('another file under the name on layer-originals: refused (exit 1), nothing in the repo changed', rc == 1 and snap(root) == r0)
gh = FakeGh(assets={'layer-originals': None})
rc, _ = I.run(args(t, root, parks, src, SIDE, write=True), gh)
check('layer-originals cannot be read: refused, nothing in the repo changed', rc == 1 and snap(root) == r0)
big = I.original_plan(src, {'name': 'x.gdb.zip', 'size': 5 * 1024 ** 3, 'sha256': 'a' * 64, 'date': '2026-11-11'}, I.check_sidecar(SIDE, {}), 6)[1]
check('an original over 2 GB is listed in parts under 2 GB', len(big['parts']) == 3 and all(p.endswith(f'.part0{i + 1}') for i, p in enumerate(big['parts'])))
cap = I.PART_SIZE, I.ASSET_CAP
I.PART_SIZE, I.ASSET_CAP = 600, 1000
pl = I.original_plan(src, {'name': src.name, 'size': src.stat().st_size, 'sha256': M.sha256_file(src), 'date': 'd'}, I.check_sidecar(SIDE, {}), 6)[1]
w = t / 'split'; w.mkdir(); pieces = I.split(src, pl, w)
check('parts join back to the original (sha256)', b''.join(p.read_bytes() for p in pieces) == src.read_bytes() and len(pieces) == len(pl['parts']) > 1)
I.PART_SIZE, I.ASSET_CAP = cap

# ---- 5) refusals: WDPA, never-contact hosts, live layers, short reads, no count ---------------------------------------------------
t, root, parks = setup('refuse'); src = layer(t, BS); r0 = snap(root)
for side, why in ((dict(SIDE, label='WDPA Bahamas'), 'label'), (dict(SIDE, source_url='https://www.protectedplanet.net/x'), 'source'),
                  (dict(SIDE, license='Protected Planet terms'), 'licence')):
    gh = FakeGh(); rc, _ = I.run(args(t, root, parks, src, side, write=True), gh)
    check(f'WDPA ({why}): exit 4, nothing fetched, stored or written', rc == 4 and gh.calls == [] and snap(root) == r0 and not (t / 'out' / 'hand-W-BS.bspa.geojson.gz').exists()
          and not (t / 'out' / 'W-BS.json.gz').exists())
wd = layer(t, BS, 'WDPA_Nov2026_BS.geojson'); gh = FakeGh(); rc, _ = I.run(args(t, root, parks, wd, SIDE, write=True), gh)
check('WDPA (file name): exit 4, nothing stored', rc == 4 and gh.calls == [] and snap(root) == r0)
for u in ('https://services1.arcgis.com/abc/arcgis/rest/services/x/FeatureServer/0/query', 'https://services.arcgis.com/33TOOklri9xpic7U/x.zip',
          'https://services-eu1.arcgis.com/x.geojson', 'https://services5.arcgis.com/arcx/rest/x.zip', 'https://ncnhde.natureserve.org/x.zip',
          'https://example.org/arcgis/rest/services/x/MapServer/3'):
    gh = FakeGh(); rc, _ = I.run(args(t, root, parks, u, SIDE, write=True), gh)
    check(f'refused before any request (exit 5): {u[:60]}', rc == 5 and gh.calls == [])
gh = FakeGh(); rc, _ = I.run(args(t, root, parks, 'release:some-other-tag/x.geojson', SIDE), gh)
check('a release this bot does not read: refused', rc == 1 and gh.calls == [])
gh = FakeGh(); rc, _ = I.run(args(t, root, parks, src, dict(SIDE, expected=7), write=True), gh)
check('a short read (6 of 7): exit 2, nothing stored', rc == 2 and gh.calls == [] and snap(root) == r0)
gh = FakeGh(); s2 = dict(SIDE); s2.pop('expected'); rc, _ = I.run(args(t, root, parks, src, s2, write=True), gh)
check('no expected count: exit 3 (a read that cannot be checked is refused)', rc == 3 and gh.calls == [])
rc, _ = I.run(args(t, root, parks, src, dict(SIDE, label='Not a world key source')), FakeGh())
check('a label the world key does not have: no bundle (the hand file still made)', rc == 0 and not (t / 'out' / 'W-BS.json.gz').exists() and (t / 'out' / 'hand-W-BS.bspa.geojson.gz').exists())
lj = json.loads((root / 'layers.json').read_text()); lj['layers']['W-BS.bspa'] = {'redistribute': 'no', 'url': SIDE['source_url']}
(root / 'layers.json').write_text(json.dumps(lj, indent=1, sort_keys=True) + '\n'); gh = FakeGh()
rc, _ = I.run(args(t, root, parks, src, SIDE, write=True), gh)
check('redistribute=no: exit 4, nothing stored (KPC-Archive is public)', rc == 4 and gh.calls == [])

# ---- 6) a US area: the state box, no US hand file upload, no raw-manifest row, a shrink held ------------------------------------
US = [feat(1, 'Test Lake WMA', box(-85.05, 37.45, -84.95, 37.55)), feat(2, 'Somewhere Else', box(-81.5, 27.5, -81.4, 27.6))]
US_SIDE = {'area': 'US-KY', 'layer': 'tstl', 'label': 'test layer', 'source_url': 'https://example.org/ky.geojson', 'license': 'public domain (test)', 'expected': 2,
           'name_fields': ['NAME'], 'record_id_field': 'OBJECTID'}
t, root, parks = setup('us'); src = layer(t, US, 'ky.geojson'); raw0 = (root / 'raw-manifest.json').read_bytes()
gh = FakeGh(assets={'layer-originals': set(), 'boundary-cache': set()})
rc, rep = I.run(args(t, root, parks, src, US_SIDE, write=True, upload_hand=True), gh)
check('US: exit 0, the park matched inside the state box', rc == 0 and rep['match']['parks'] == 1 and rep['match']['of'] == 1)
check('US: the hand file is never uploaded to boundary-cache (fill would hold it or record the trimmed count)', not any(c[0] == 'upload' and c[1] == 'boundary-cache' for c in gh.calls))
check('US: the original is still stored on KPC-Archive', any(c[0] == 'upload' and c[1] == 'layer-originals' for c in gh.calls))
check('US: raw-manifest.json not written (the master step records a US original when it merges a hand file)', (root / 'raw-manifest.json').read_bytes() == raw0)
check('US: master records written for US-KY', 'US-99001' in M.load_area('US-KY', root))
t, root, parks = setup('usshrink'); src = layer(t, US, 'ky.geojson')
lj = json.loads((root / 'layers.json').read_text()); lj['layers']['US-KY.tstl'] = {'expected_count': 500, 'url': 'https://example.org/ky'}
(root / 'layers.json').write_text(json.dumps(lj, indent=1, sort_keys=True) + '\n')
rc, _ = I.run(args(t, root, parks, src, US_SIDE), FakeGh())
check('US: a layer whose baseline is far bigger: held as a shrink (exit 6), as trim holds it', rc == 6)

# ---- 7) review fixes (Nov 11): the count must agree, nothing stored before a refusal, raw rows, record ids, many-source countries ----
t, root, parks = setup('count'); src = layer(t, BS); r0 = snap(root); gh = FakeGh(assets={'layer-originals': set()})
rc, _ = I.run(args(t, root, parks, src, dict(SIDE, expected=2), write=True), gh)
check('a count that is too low (2 for a 6-record file): exit 3, nothing stored, no baseline written', rc == 3 and gh.calls == [] and snap(root) == r0)

t, root, parks = setup('shrinkw'); src = layer(t, BS)
lj = json.loads((root / 'layers.json').read_text()); lj['layers']['W-BS.bspa'] = {'expected_count': 500}
(root / 'layers.json').write_text(json.dumps(lj, indent=1, sort_keys=True) + '\n'); r0 = snap(root); gh = FakeGh(assets={'layer-originals': set()})
rc, _ = I.run(args(t, root, parks, src, SIDE, write=True), gh)
check('write, a shrink held (exit 6): stopped BEFORE the original is stored; the repo unchanged', rc == 6 and not any(c[0] == 'upload' for c in gh.calls) and snap(root) == r0)

t, root, parks = setup('rawname'); d1, d2 = t / 'd1', t / 'd2'; d1.mkdir(); d2.mkdir(); gh = FakeGh(assets={'layer-originals': set()})
s1 = layer(d1, BS, 'data.geojson'); s2 = layer(d2, BS[:5] + [feat(900009, 'Other Thing', box(-70.0, 20.0, -69.9, 20.1))], 'data.geojson')
ra = I.run(args(t, root, parks, s1, SIDE, write=True), gh); rb = I.run(args(t, root, parks, s2, dict(SIDE, layer='bsp2', label='not a key label'), write=True, out='o2'), gh)
names = {x['name']: x['sha256'] for x in json.loads((root / 'raw-manifest.json').read_text())['files']}
check('two layers whose files share a name: two raw-manifest rows (named as the assets), neither overwritten',
      ra[0] == 0 and rb[0] == 0 and names.get(ra[1]['original']['asset']) == M.sha256_file(s1) and names.get(rb[1]['original']['asset']) == M.sha256_file(s2))

t, root, parks = setup('noid'); bare = layer(t, [{'type': 'Feature', 'properties': {'NAME': f['properties']['NAME']}, 'geometry': f['geometry']} for f in BS])
s3 = {k: v for k, v in SIDE.items() if k not in ('record_id_field', 'id_fields')}
rc, rep = I.run(args(t, root, parks, bare, s3), FakeGh())
check('a file with no record id field: no bundle (the world key joins by id); the hand file is still made',
      rc == 0 and 'no \'OBJECTID\'' in (rep['bundle'].get('refused') or '') and not (t / 'out' / 'W-BS.json.gz').exists() and (t / 'out' / 'hand-W-BS.bspa.geojson.gz').exists())
t, root, parks = setup('dupid'); same = layer(t, [feat(7, f['properties']['NAME'], f['geometry']) for f in BS])
rc, rep = I.run(args(t, root, parks, same, SIDE), FakeGh())
check('record ids not unique in the file: no bundle', rc == 0 and 'not unique' in (rep['bundle'].get('refused') or ''))

t, root, parks = setup('lurl'); src = layer(t, BS); LU = 'https://example.org/arcgis/rest/services/bs/MapServer/3'
rc, rep = I.run(args(t, root, parks, src, dict(SIDE, layer_url=LU)), FakeGh())
check('inbox rows carry the ArcGIS layer address when the sidecar gives one (the form the inbox checker reads)',
      rc == 0 and (t / 'out' / 'layer-intake-W-BS.bspa.csv').read_text().count(',' + LU + ',') == 3)

W = I.world_key_ns()
dups = [(cc, s_[0]) for cc, v in W['SRC'].items() for s_ in v if s_[1] == 'arcgis' and sum(1 for x in v if x[0] == s_[0]) > 1]
def refused(fn, *a):
    try: fn(*a)
    except I.Refused: return True
    return False
check(f'a label two sources of one country share ({dups[0] if dups else "none in the key today"}): refused', not dups or refused(I.world_source, *dups[0]))

# a country the world key reads more than one source for: this layer alone must not stand in for the whole copy
CC = 'BZ'; rows_ = W['SRC'][CC]
mine_s = next(x for x in rows_ if x[1] == 'arcgis' and sum(1 for y in rows_ if y[0] == x[0]) == 1); other_s = next(x for x in rows_ if x is not mine_s)
check(f'fixture: the world key reads {len(rows_)} sources for {CC}', len(rows_) > 1)
BZ = [feat(99000001, 'Maya Hill Reserve', box(-88.6, 17.0, -88.4, 17.2)), feat(99000002, 'Nowhere Near', box(-89.1, 16.0, -89.0, 16.1))]
BZ_SIDE = {'area': f'W-{CC}', 'layer': 'bzpa', 'label': mine_s[0], 'source_url': 'https://example.org/bz.geojson', 'license': 'test licence', 'expected': 2,
           'name_fields': ['NAME'], 'record_id_field': 'OBJECTID'}
def bz(tag):
    t, root, parks = setup(tag); parks.write_text(json.dumps([['POTA', f'{CC}-9001', 'Maya Hill', 17.1, -88.5, 'u']])); return t, root, parks, layer(t, BZ, 'bz.geojson')
def release_copy(t, n_mine):
    recs = [{'id': i, 'n': f'Other {i}', 'ty': '', 'src': other_s[0], 'sid': W['src_id'](other_s), '_bb': None, '_r': []} for i in range(3)]
    recs += [{'id': 500 + i, 'n': f'Old {i}', 'ty': '', 'src': mine_s[0], '_bb': None, '_r': []} for i in range(n_mine)]   # an older copy: no sid
    blob = {'cc': CC, 'saved': '2026-11-01', 'detail': 0.002, 'thin': 250, 'recs': recs}
    blob['manifest'] = M.make_manifest(f'W-{CC}.json.gz', blob, 'KPC owner', '2026-11-01', source_full={other_s[0]: 40})
    p = t / 'rel' / f'W-{CC}.json.gz'; p.parent.mkdir(exist_ok=True); M.save_saved(p, blob); return p.read_bytes(), recs

t, root, parks, src = bz('bznone'); gh = FakeGh(assets={'boundary-cache': None})
rc, rep = I.run(args(t, root, parks, src, BZ_SIDE), gh)
check('many sources, the boundary-cache list unreadable: no bundle (fail closed); the hand file is still made',
      rc == 0 and 'could not be read' in (rep['bundle'].get('refused') or '') and not (t / 'out' / f'W-{CC}.json.gz').exists() and (t / 'out' / f'hand-W-{CC}.bzpa.geojson.gz').exists())
t, root, parks, src = bz('bzfirst'); gh = FakeGh(assets={'boundary-cache': set()})
rc, rep = I.run(args(t, root, parks, src, BZ_SIDE), gh)
check('many sources, no copy on the release yet: a first copy of this layer alone, and the report says the other sources are not in it',
      rc == 0 and rep['bundle']['records'] == 1 and 'a first copy' in rep['bundle']['note'] and 'not in it' in rep['bundle']['note'])
t, root, parks, src = bz('bzmerge'); rel, old_recs = release_copy(t, 1); gh = FakeGh(assets={'boundary-cache': {f'W-{CC}.json.gz'}}, files={('boundary-cache', f'W-{CC}.json.gz'): rel})
rc, rep = I.run(args(t, root, parks, src, BZ_SIDE), gh)
mb = M.load_saved(t / 'out' / f'W-{CC}.json.gz')
check('many sources, a copy on the release: the other source\'s 3 records are kept as they are, only this layer\'s are replaced',
      rc == 0 and [r for r in mb['recs'] if r['src'] == other_s[0]] == old_recs[:3] and [r['id'] for r in mb['recs'] if r['src'] == mine_s[0]] == [99000001]
      and rep['bundle']['records'] == 4 and rep['bundle']['layer_records'] == 1)
check('... its manifest is written new for the whole copy and checks; both sources\' full counts are on record',
      M.manifest_problems(f'W-{CC}.json.gz', mb) == [] and mb['manifest']['total'] == 4 and mb['manifest']['source_full'] == {other_s[0]: 40, mine_s[0]: 2})
check('... read only: the release copy is downloaded, nothing is uploaded (a dry run)', not any(c[0] == 'upload' for c in gh.calls) and any(c[0] == 'download' for c in gh.calls))
t, root, parks, src = bz('bzbigger'); rel, _ = release_copy(t, 3); gh = FakeGh(assets={'boundary-cache': {f'W-{CC}.json.gz'}}, files={('boundary-cache', f'W-{CC}.json.gz'): rel})
rc, rep = I.run(args(t, root, parks, src, BZ_SIDE), gh)
check('the release copy holds more of this layer (3) than this trim (1): no bundle (a smaller set never replaces a saved layer)',
      rc == 0 and 'smaller set never replaces' in (rep['bundle'].get('refused') or '') and not (t / 'out' / f'W-{CC}.json.gz').exists())

check('no DNS lookup and no socket in the whole test', DIALS == [])
check("the repo's own outline files are byte for byte unchanged", all((ROOT / f).read_bytes() == b for f, b in before.items()))
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
