#!/usr/bin/env python3
"""Offline (owner rule, 2026-11-10): the master step takes any area id (US-XX, CA-XX / CA-ALL, W-XX). A hand file's area and layer come
only from its name; a file for one area is never applied to another; one national file is checked per area with its own count;
a short file, a WDPA one and a redistribute=no one are refused; a saved copy with no baseline passes the gate only with --first-ok
and the first good full read records it; suspect layer baselines are named by `check`; a bot row on a host a bot may not read is a
person's on every merge; the Canada workflow runs gate -> build -> baseline -> save-check -> upload. Temp dirs, tiny fixtures."""
import gzip, io, json, os, pathlib, subprocess, sys, tempfile, contextlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M  # noqa: E402
import kpc_master_cli as CLI  # noqa: E402
CLIP = str(ROOT / '.github/scripts/kpc_master_cli.py')
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def sq(x, y, d=0.05): return {'type': 'Polygon', 'coordinates': [[[x - d, y - d], [x + d, y - d], [x + d, y + d], [x - d, y + d], [x - d, y - d]]]}


def hand(dir_, name, area, layer, feats, expected=None, **meta):
    m = dict({'area': area, 'layer': layer, 'url': 'https://example.gov/fws/national', 'name_field': 'ORGNAME', 'source': 'hand',
              'count_expected': len(feats) if expected is None else expected}, **meta)
    return M.write_layer_file(pathlib.Path(dir_) / name, m, feats)


def feat(name, x, y): return {'type': 'Feature', 'properties': {'ORGNAME': name}, 'geometry': sq(x, y)}


def quiet(f, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): rc = f(*a)
    return rc, buf.getvalue()


# 1. area ids from the name only
check('name parse: US / CA / CA-ALL / W', M.parse_hand_name('hand-US-AZ.fsod.geojson.gz') == ('US-AZ', 'fsod') and M.parse_hand_name('hand-CA-ON.h160.geojson.gz') == ('CA-ON', 'h160')
      and M.parse_hand_name('hand-CA-ALL.h139.geojson.gz') == ('CA-ALL', 'h139') and M.parse_hand_name('hand-W-AS.sgakd.geojson.gz') == ('W-AS', 'sgakd'))
for bad in ('hand-CA.ParksCanada.geojson.gz', 'hand-US-ABC.x.geojson.gz', 'hand-W-as.x.geojson.gz', 'hand-W-AS.sg-akd.geojson.gz', 'hand-US-AZ.fsod.geojson',
            'hand-X-AS.a.geojson.gz', 'hand-W-AS..geojson.gz', 'hand-W-AS.a.b.geojson.gz', 'hand-W-ÄS.a.geojson.gz', 'hand-W-AS.ä.geojson.gz', 'US-AZ.fsod.geojson.gz'):
    check(f'name parse refuses {bad}', M.parse_hand_name(bad) is None)
check('area id check', all(M.AREA_RE.match(x) for x in ('US-KY', 'CA-ALL', 'CA-QC', 'W-VI')) and not any(M.AREA_RE.match(x) for x in ('US-K', 'W-ASX', 'CA', 'w-as')))

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); root = t / 'root'; root.mkdir(); hd = t / 'hand'; hd.mkdir(); store = t / 'store'
    (root / 'layers.json').write_text(json.dumps({'format': 1, 'layers': {}, 'caches': {}}))
    parks = t / 'parks.json'
    parks.write_text(json.dumps([['POTA', 'AS-0002', 'Rose Atoll National Wildlife Refuge', -14.5, -168.1, ''],
                                 ['POTA', 'VI-0002', 'Sandy Point National Wildlife Refuge', 17.7, -64.9, ''],
                                 ['POTA', 'VI-0003', 'Green Cay National Wildlife Refuge', 17.8, -64.7, ''],
                                 ['POTA', 'US-0001', 'Rose Atoll National Wildlife Refuge', -14.5, -168.1, '']]))
    # one national FWS file, packed once per area: each area its own checked file and count
    nat = [feat('ROSE ATOLL NATIONAL WILDLIFE REFUGE', -168.1, -14.5), feat('SANDY POINT NATIONAL WILDLIFE REFUGE', -64.9, 17.7),
           feat('GREEN CAY NATIONAL WILDLIFE REFUGE', -64.7, 17.8)]
    hand(hd, 'hand-W-AS.h172.geojson.gz', 'W-AS', 'h172', nat[:1])
    hand(hd, 'hand-W-VI.h172.geojson.gz', 'W-VI', 'h172', nat[1:])

    def run_fill(areas, extra=()):
        return quiet(CLI.main, ['fill', '--cache', str(t / 'cache'), '--states', '', '--areas', areas, '--root', str(root), '--parks', str(parks), '--hand', str(hd),
                                '--work', str(t / 'work'), '--checked', str(store), '--out-rows', str(t / 'rows.json'), '--offline', '--no-key',
                                '--us-layers', str(t / 'none.json'), '--state-gis', str(t / 'none.json'), *extra])
    rc, out = run_fill('W-AS W-VI')
    check('fill (W-AS W-VI): exit 0', rc == 0)
    check('national file checked per area: W-AS 1 park, W-VI 2 parks, each in its own master area file',
          set(M.load_area('W-AS', root)) == {'AS-0002'} and set(M.load_area('W-VI', root)) == {'VI-0002', 'VI-0003'})
    check('the trim keeps each area to its own parks (no US- park in W-AS)', 'US-0001' not in M.load_area('W-AS', root))
    check('both checked files are in the per-area checked store', sorted(p.name for p in store.iterdir()) == ['hand-W-AS.h172.geojson.gz', 'hand-W-VI.h172.geojson.gz'])
    L = M.load_layers(root)['layers']
    check('each area has its own layer count (W-AS.h172 = 1, W-VI.h172 = 2)', L['W-AS.h172']['expected_count'] == 1 and L['W-VI.h172']['expected_count'] == 2)
    rows = {r['id']: r for r in json.load(open(t / 'rows.json'))['rows']}
    check('world rows are held for a person with the honest why', all(rows[k]['status'] == 'held' and rows[k]['who'] == 'person' and 'world builder does not read hand files yet' in rows[k]['why']
                                                                    for k in ('W-AS|h172', 'W-VI|h172')))
    # a W-AS file is never applied to W-VI
    for p in list(store.iterdir()): p.unlink()
    for a in ('W-AS', 'W-VI'): M.area_path(a, root).unlink()
    rc, out = run_fill('W-VI')
    check('fill for W-VI only: the W-AS file is not touched', not M.area_path('W-AS', root).exists() and not (store / 'hand-W-AS.h172.geojson.gz').exists())
    check('... and the W-VI file is applied', set(M.load_area('W-VI', root)) == {'VI-0002', 'VI-0003'})
    (hd / 'hand-W-VI.h172.geojson.gz').unlink(); M.area_path('W-VI', root).unlink(); (store / 'hand-W-VI.h172.geojson.gz').unlink()
    hand(hd, 'hand-W-VI.h172.geojson.gz', 'W-AS', 'h172', nat[:1])   # a W-AS file renamed to W-VI
    rc, out = run_fill('W-VI')
    check('a file whose own area is W-AS but named W-VI is refused (never applied to another area)',
          not M.area_path('W-VI', root).exists() and not (store / 'hand-W-VI.h172.geojson.gz').exists())
    check('... and the refusal names both', 'its name says W-VI|h172' in out)
    # bad names, short files
    (hd / 'hand-W-VI.h172.geojson.gz').unlink(); (hd / 'hand-W-AS.h172.geojson.gz').unlink()
    hand(hd, 'hand-CA.ParksCanada.geojson.gz', 'CA', 'ParksCanada', nat[:1])
    hand(hd, 'hand-W-VI.sgmng.geojson.gz', 'W-VI', 'sgmng', nat[1:], expected=5)
    rc, out = run_fill('W-VI CA-ALL')
    check('a name outside hand-<AREA>.<layer> is refused, loudly', 'hand-CA.ParksCanada.geojson.gz: not named' in out)
    check('a short hand file (2 of 5) is refused, not kept', 'SHORT' in out and not (store / 'hand-W-VI.sgmng.geojson.gz').exists())
    rc, out = run_fill('W-ASX US-K1')
    check('a bad area id is refused', 'refused: W-ASX US-K1' in out)
    # redistribute=no: refused, exit 4 (the workflow goes red); WDPA the same
    (hd / 'hand-W-VI.sgmng.geojson.gz').unlink(); (hd / 'hand-CA.ParksCanada.geojson.gz').unlink()
    hand(hd, 'hand-W-AS.h172.geojson.gz', 'W-AS', 'h172', nat[:1])
    doc = M.load_layers(root); doc['layers']['W-AS.h172']['redistribute'] = 'no'; M.save_layers(doc, root)
    rc, out = run_fill('W-AS')
    check('redistribute=no on the layer: fill exits 4 and keeps nothing', rc == 4 and not (store / 'hand-W-AS.h172.geojson.gz').exists())
    doc['layers']['W-AS.h172'].pop('redistribute'); M.save_layers(doc, root)
    (root / 'download-sources.json').write_text(json.dumps({'format': 1, 'sources': {'h172': {'areas': ['W-AS'], 'layer': 'h172', 'redistribute': 'no'}}}))
    check('redistribute=no on the download source (by src id, and by layer + area) is refused', M.share_block({'area': 'W-UM', 'layer': 'x', 'src': 'h172'}, root)
          and M.share_block({'area': 'W-AS', 'layer': 'h172'}, root) and not M.share_block({'area': 'W-GU', 'layer': 'h172'}, root))
    rc, out = run_fill('W-AS')
    check('... and fill exits 4 for it', rc == 4)
    check('no field = no known restriction', not M.share_block({'area': 'W-VI', 'layer': 'sgakd', 'url': 'https://example.gov/nps'}, root))
    check('a WDPA-looking layer is refused', M.share_block({'area': 'W-AS', 'layer': 'x', 'url': 'https://www.protectedplanet.net/x'}, root))

# 2. the PC helper refuses the same (stdlib only, no request)
import importlib.util  # noqa: E402
sp = importlib.util.spec_from_file_location('kpc_pc_helper', ROOT / 'tools/kpc_pc_helper.py'); H = importlib.util.module_from_spec(sp); sp.loader.exec_module(H)
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); f = t / 'dl.geojson'; parks = t / 'parks.json'; parks.write_text(json.dumps([['POTA', 'US-0001', 'X Park', 33.0, -86.8, '']]))
    # one national file, two states: each state its own checked file and count
    f.write_text(json.dumps({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'OBJECTID': i, 'NAME': f'N{i}'}, 'geometry': sq(x, y, .01)}
                                                                      for i, (x, y) in enumerate([(-86.8, 33.0), (-86.5, 32.5), (-83.5, 33.5)])]}))
    lt = {'zzn': ['https://example.gov/national/MapServer/0', 'NAME', 'National']}
    res = {st: H.check_and_pack({'area': f'US-{st}', 'layer': 'zzn', 'url': lt['zzn'][0], 'expected': 0}, [f], parks, t, lt) for st in ('AL', 'GA')}
    cnt = {st: len(M.read_layer_file(v[2])[1]) if v[0] else None for st, v in res.items()}
    check(f'PC helper: one national file -> one checked file per state, each with its own count {cnt}', cnt == {'AL': 2, 'GA': 1}
          and res['AL'][2].name == 'hand-US-AL.zzn.geojson.gz' and res['GA'][2].name == 'hand-US-GA.zzn.geojson.gz')
    okk, msg, p = H.check_and_pack({'area': 'US-AL', 'layer': 'zzw', 'url': 'https://example.org/wdpa/MapServer/0', 'expected': 0}, [f], parks, t, lt)
    check('PC helper: a WDPA-looking layer is refused, nothing written', not okk and 'refused' in msg and p is None and not (t / 'hand-US-AL.zzw.geojson.gz').exists())
    bad = M.write_layer_file(t / 'hand-US-AL.zzp.geojson.gz', {'area': 'US-AL', 'layer': 'zzp', 'url': 'https://www.protectedplanet.net/x', 'count_expected': 1}, [])
    with contextlib.redirect_stdout(io.StringIO()): r = H.upload([bad], t)
    check('PC helper: a restricted file is never uploaded or packed', r is None and not (t / 'kpc-hand-upload.zip').exists())

# 3. no baseline yet: the gate holds it unless --first-ok; the first good full read records it; never lowered or replaced
def copy(p, n):
    with gzip.open(p, 'wt', encoding='utf-8') as f: json.dump({'recs': [{'oid': f'x:{i}'} for i in range(n)]}, f)


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); root = t / 'root'; root.mkdir(); c = t / 'cache'; c.mkdir(); ag = t / 'against'; ag.mkdir()
    (root / 'layers.json').write_text(json.dumps({'format': 1, 'layers': {}, 'caches': {'W-AS': {'expected_count': 10}}}))
    gate = lambda *x: subprocess.run([sys.executable, CLIP, 'gate', '--cache', str(c), '--root', str(root), *x], capture_output=True, text=True)
    copy(c / 'CA-ALL.json.gz', 50)
    r = gate(); check('gate: no baseline and no --first-ok = held (exit 7, moved aside)', r.returncode == 7 and (c / 'short/CA-ALL.json.gz').exists())
    os.replace(c / 'short/CA-ALL.json.gz', c / 'CA-ALL.json.gz')
    r = gate('--first-ok'); check('gate --first-ok: no baseline yet = used with a notice', r.returncode == 0 and (c / 'CA-ALL.json.gz').exists() and 'NO BASELINE YET' in r.stdout)
    copy(c / 'W-AS.json.gz', 4)
    r = gate('--first-ok'); check('gate --first-ok: a SHORT copy with a baseline is still held', r.returncode == 7 and (c / 'short/W-AS.json.gz').exists())
    base = lambda *x: subprocess.run([sys.executable, CLIP, 'baseline', '--root', str(root), *x], capture_output=True, text=True)
    copy(ag / 'CA-ALL.json.gz', 45)
    r = base('--against', str(ag), '--how', 'test', str(c / 'CA-ALL.json.gz'))
    cc = M.load_layers(root)['caches']
    check('baseline: the first one is recorded, never above the release copy (45 of 50)', r.returncode == 0 and cc['CA-ALL']['expected_count'] == 45 and cc['CA-ALL']['read_how'] == 'test')
    copy(c / 'CA-ALL.json.gz', 30); base(str(c / 'CA-ALL.json.gz'))
    check('baseline: an existing one is never lowered or replaced', M.load_layers(root)['caches']['CA-ALL']['expected_count'] == 45)
    copy(c / 'W-AS.json.gz', 20); base(str(c / 'W-AS.json.gz'))
    check('baseline: W-AS keeps its own', M.load_layers(root)['caches']['W-AS']['expected_count'] == 10)
    # suspect layer baselines (a count capped at 200) are named by check; the next verified full read re-records it
    (root / 'layers.json').write_text(json.dumps({'format': 1, 'caches': {}, 'layers': {'US-ZZ.sgzza': {'expected_count': 200, 'source_count': 227, 'url': 'https://example.gov/x', 'areas': ['US-ZZ']}}}))
    r = subprocess.run([sys.executable, CLIP, 'check', '--root', str(root)], capture_output=True, text=True)
    check('check: source_count > expected_count = a suspect baseline warning, listed in the summary', 'suspect baseline' in r.stdout and 'US-ZZ.sgzza' in r.stdout and r.returncode == 0)
    lf = M.write_layer_file(t / 'US-ZZ.sgzza.geojson.gz', {'area': 'US-ZZ', 'layer': 'sgzza', 'count_live': 227, 'source': 'live'},
                            [{'type': 'Feature', 'properties': {'NAME': f'n{i}', '_kpc': {'OBJECTID': f'sgzza{i}'}}, 'geometry': sq(i, 0, .1)} for i in range(227)])
    pk = t / 'pk.json'; pk.write_text('[]')
    with contextlib.redirect_stdout(io.StringIO()): import kpc_master_fill as F; F.apply_layer_file(lf, t, root, pk)
    check('the next verified full read re-records the baseline (200 -> 227, no longer suspect)', M.load_layers(root)['layers']['US-ZZ.sgzza']['expected_count'] == 227)
    with gzip.open(t / 'US-ZZ.json.gz', 'wt') as f: json.dump({'recs': [{'OBJECTID': f'sgzza{i}'} for i in range(300)]}, f)
    b2, what = M.merge_saved_layer(M.load_saved(t / 'US-ZZ.json.gz'), 'sgzza', [{'OBJECTID': 'sgzza1'}])
    check('keep-bigger: a smaller layer read never replaces the saved layer', len(b2['recs']) == 300 and 'kept' in what)

# 4. the who of a row as the host rules see it, on every merge
SV5 = 'https://services5.arcgis.com/x/arcgis/rest/services/CPWAdminData/FeatureServer/5/query'
r0 = dict(M.needs_row('US-CO', 'sgcoc', SV5, 'refilled and checked by the master step', 'master', who='bot'), status='done')
d, _, _ = M.merge_needs(M.load_needs(None), [r0])
check('merge: a bot row on a services*.arcgis.com host with no direct file is a person\'s', d['rows'][0]['who'] == 'person')
r1 = M.needs_row('US-AL', 'sgaki', 'https://mapservices.nps.gov/arcgis/rest/services/x/MapServer/1/query', 'read 1 of 200: SHORT', 'master', who='bot')
check('an open bot row on an allowed host with no direct file is held (the bot re-reads it; nobody downloads it)', M.honest_who(r1)['status'] == 'held')
r2 = dict(M.needs_row('W-AS', 'h172', SV5, 'w', 'm', who='bot'), note='direct file: https://iris.fws.gov/APPS/ServCat/DownloadFile/1')
check('a bot row with an allowed direct file stays a bot\'s', M.honest_who(r2) == r2)
check('a person\'s row is never made a bot\'s', M.honest_who(dict(r1, who='person')) == dict(r1, who='person'))

# 5. workflows: Canada gate --first-ok before the build; baseline -> save-check -> upload; layers.json saved; US fill -> gate -> build -> save-check -> upload
def steps(wf, job):
    return [(s.get('name') or '', s.get('run') or '') for s in yaml.safe_load(open(ROOT / '.github/workflows' / wf))['jobs'][job]['steps']]


def at(text, *subs):
    i = [text.find(x) for x in subs]
    return all(x >= 0 for x in i) and i == sorted(i)


ca = steps('kpc-ca-key.yml', 'run')
b = next(r for n, r in ca if n.startswith('Build the Canada answer key'))
check('Canada: gate --first-ok runs before the key build', at(b, 'gate --first-ok --cache cache/ca', 'kpc_ca_key.py'))
k = next(r for n, r in ca if n.startswith('Keep the saved copy current'))
check('Canada: baseline -> save-check -> archive -> upload, in that order', at(k, 'kpc_master_cli.py baseline', 'save-check', 'kpc_archive.sh put', 'gh release upload boundary-cache'))
check('Canada: the save keeps the recorded baseline (data/outlines/layers.json)', 'data/outlines/layers.json' in next(r for n, r in ca if n == 'Save'))
names = [n for n, _ in ca]
check('Canada: the build step comes before the keep step', names.index(next(n for n in names if n.startswith('Build the Canada'))) < names.index(next(n for n in names if n.startswith('Keep the saved copy'))))
us = steps('kpc-us-key.yml', 'build')
iu = {n: i for i, (n, _) in enumerate(us)}
fi = next(i for n, i in iu.items() if n.startswith('THE MASTER STEP')); bi = next(i for n, i in iu.items() if n.startswith('Build the answer key'))
si = next(i for n, i in iu.items() if n.startswith("Save this job's new live reads"))
check('US: fill -> (gate + build) -> save-check -> upload', fi < bi < si and 'kpc_master_cli.py fill' in us[fi][1] and at(us[bi][1], 'gate --cache cache/us', 'kpc_us_key.py')
      and at(us[si][1], 'save-check', 'gh release upload boundary-cache'))
check('US: fill exit 4 (licence) goes red', '"$kpc_rc" = 4' in us[fi][1] and 'exit 4' in us[fi][1])

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
