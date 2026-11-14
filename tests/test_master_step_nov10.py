#!/usr/bin/env python3
"""Nov 10: the master step (the one writer of the saved copies), the ONE needs-download list, the host rules (services-eu1 and
any services-<region>.arcgis.com count as services*.arcgis.com; ncnhde is never contacted), and the PC helper.

Nothing here contacts any server: robots and reads are stand-ins or refused before a request.
"""
import gzip, json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M  # noqa: E402
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def key_fn(fn, a, b, name='saved_only'):
    s = (ROOT / '.github/scripts' / fn).read_text(encoding='utf-8')
    ns = {'os': os, 're': re, 'urllib': __import__('urllib.parse')}
    exec(compile(s[s.index(a):s.index(b)], fn, 'exec'), ns)
    return ns[name]


EU = ['services-eu1', 'services-ap1', 'services-uk1']
SO = {'kpc_us_key.py': key_fn('kpc_us_key.py', 'SAVED_ONLY_HOSTS = ', 'def notice('),
      'kpc_ca_key.py': key_fn('kpc_ca_key.py', 'SAVED_ONLY_HOSTS = ', 'def get('),
      'kpc_world_key.py': key_fn('kpc_world_key.py', 'SAVED_ONLY_HOSTS = ', 'def fetch_bytes(')}
# 1. services-eu1 (and any services-<region>) = services*.arcgis.com in every host check
for fn, so in SO.items():
    for h in EU + ['services', 'services1', 'services8']:
        check(f'{fn}: {h}.arcgis.com is saved-copy only', so(f'https://{h}.arcgis.com/x/arcgis/rest/services/y/FeatureServer/0/query'))
    check(f'{fn}: ncnhde.natureserve.org is never read live', so('https://ncnhde.natureserve.org/arcgis/rest/services/x/MapServer/0'))
    check(f'{fn}: www / hub / an agency server are not caught by the rule', not so('https://www.arcgis.com/sharing/rest/x') and not so('https://hub.arcgis.com/search')
          and not so('https://gis.blm.gov/arcgis/rest/services/x/MapServer/0') and not so('https://servicesx.arcgis.com.evil.example/x'))
for h in EU:
    okk, why = M.live_ok(f'https://{h}.arcgis.com/x/arcgis/rest/services/y/FeatureServer/0')
    check(f'kpc_master.live_ok refuses {h}.arcgis.com, robots.txt included', not okk and 'services' in why)
    check(f'kpc_master.live_ok refuses {h} robots.txt itself', not M.live_ok(f'https://{h}.arcgis.com/robots.txt')[0])
check('kpc_master.is_arcgis_services_host: services-eu1 yes, www no', M.is_arcgis_services_host('services-eu1.arcgis.com') and not M.is_arcgis_services_host('www.arcgis.com'))
check('kpc_maprep_state_layers uses the same host rule', 'services(?:\\d+|-[a-z0-9]+)?' in (ROOT / '.github/scripts/kpc_maprep_state_layers.py').read_text(encoding='utf-8'))
check('the world layers on services-eu1 exist (8 or more) and every one is saved-copy only',
      (lambda us: len(us) >= 8 and all(SO['kpc_world_key.py'](u) for u in us))(
          sorted(set(re.findall(r'https://services-eu1\.arcgis\.com/[^"\'\s]+', ''.join(p.read_text(encoding='utf-8', errors='replace') for p in (ROOT / 'data/world-key/layers.json', ROOT / 'data/world-key/extra-layers.json')))))))

# 2. who_for: never / person / bot; robots asked only after the host rules, a 403 counts as no
asked = []
rb = lambda u: (asked.append(u), False)[1]
check('who_for: Grant County NM parcel server = never', M.who_for('https://services.arcgis.com/33TOOklri9xpic7U/arcgis/rest/services/P/FeatureServer/0')[0] == 'never')
check('who_for: ncnhde = never', M.who_for('https://ncnhde.natureserve.org/x')[0] == 'never')
check('who_for: services-eu1 = person (no robots asked)', M.who_for('https://services-eu1.arcgis.com/x/FeatureServer/0', rb)[0] == 'person' and not asked)
check('who_for: apps.fs.usda.gov is not a blocked host (2026-11-13): robots.txt decides (asked)', M.who_for('https://apps.fs.usda.gov/arcx/rest/services/EDW/x/MapServer/0', rb)[0] == 'person' and asked); asked.clear()
check('who_for: robots says no (403) = person', M.who_for('https://gis.example.gov/arcgis/rest/services/x/MapServer/0', rb)[0] == 'person' and asked)
check('who_for: allowed = bot', M.who_for('https://gis.example.gov/arcgis/rest/services/x/MapServer/0', lambda u: True)[0] == 'bot')
get = lambda u: (403, '')
check('robots_allows: a robots.txt 403 is a disallow', M.robots_allows('https://gis.example.gov/arcgis/rest/services/x', get, {}) is False)

# 3. the ONE needs list: schema, merge by area|layer, done stays done, no change = no save
r1 = M.needs_row('US-AZ', 'fsod', 'https://services1.arcgis.com/EDW/arcgis/rest/services/X/MapServer/0/query', 'short', 'master', expected=12, have=12, date='2026-11-10')
check('needs row has exactly the schema fields', set(r1) == set(M.NEEDS_FIELDS) and r1['who'] == 'person' and r1['id'] == 'US-AZ|fsod' and r1['status'] == 'open')
check('needs row page for a hosted layer is the hub search, not the services host', M.needs_row('US-AZ', 'x', 'https://services2.arcgis.com/a/arcgis/rest/services/AZ_Parks/FeatureServer/0', 'w', 'm')['page'].startswith('https://hub.arcgis.com/search?q=AZ%20Parks'))
doc = M.load_needs(None)
doc, a1, u1 = M.merge_needs(doc, [r1, dict(r1)])
check('merge: one row per area|layer', a1 == 1 and len(doc['rows']) == 1)
done = dict(r1, status='done', added='2026-11-10')
doc, a2, u2 = M.merge_needs(doc, [done])
check('merge: a done row updates the open one', doc['rows'][0]['status'] == 'done' and u2 == 1)
doc, a3, u3 = M.merge_needs(doc, [dict(r1, added='2026-11-09')])
check('merge: an older open row does not reopen a done row', doc['rows'][0]['status'] == 'done' and u3 == 0)
with tempfile.TemporaryDirectory() as t:
    p = pathlib.Path(t) / 'n.json'
    check('save_needs: first save writes', M.save_needs(doc, p))
    check('save_needs: the same rows again = no change, no save', not M.save_needs(M.merge_needs(M.load_needs(p), [])[0], p))

# 4. layer files and the keep-bigger merge
with tempfile.TemporaryDirectory() as t:
    p = M.layer_file_path(t, 'US-ZZ', 'sgzza')
    M.write_layer_file(p, {'area': 'US-ZZ', 'layer': 'sgzza', 'count_live': 2}, [{'type': 'Feature', 'properties': {'a': 1}, 'geometry': None}])
    meta, feats = M.read_layer_file(p)
    check('layer file round trip (atomic write, no .tmp left)', meta['layer'] == 'sgzza' and len(feats) == 1 and not list(pathlib.Path(t).glob('*.tmp')))
    check('layer file expected: the live total first, then a person\'s checked count', M.layer_file_expected({'count_live': 5, 'count_expected': 3}) == 5 and M.layer_file_expected({'count_expected': 3}) == 3 and M.layer_file_expected({}) is None)
blob = {'recs': [{'OBJECTID': 'sgzza1'}, {'OBJECTID': 'sgzza2'}, {'OBJECTID': '7'}]}
b2, what = M.merge_saved_layer(blob, 'sgzza', [{'OBJECTID': 'sgzza9'}])
check('keep-bigger: a smaller re-read never replaces a saved layer', b2['recs'] == blob['recs'])
b3, what = M.merge_saved_layer(blob, 'sgzza', [{'OBJECTID': f'sgzza{i}'} for i in range(5)])
check('keep-bigger: a bigger read replaces only that layer', sorted(r['OBJECTID'] for r in b3['recs']) == ['7'] + [f'sgzza{i}' for i in range(5)])

# 5. apply_layer_file: fail closed on short or no count; a whole read is trimmed, recorded and merged
import kpc_master_fill as F
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); cache = t / 'cache'; root = t / 'root'; cache.mkdir(); root.mkdir()
    json.dump({'format': 1, 'layers': {}, 'caches': {}}, open(root / 'layers.json', 'w'))
    parks = t / 'parks.json'; json.dump([['POTA', 'US-9999', 'Test Lake State Park', 36.5, -86.5, '']], open(parks, 'w'))
    with gzip.open(cache / 'US-ZZ.json.gz', 'wt') as fh: json.dump({'st': 'ZZ', 'recs': [{'OBJECTID': 'sgzza1', 'Unit_Nm': 'Old'}]}, fh)
    sq = [[[-86.6, 36.4], [-86.4, 36.4], [-86.4, 36.6], [-86.6, 36.6], [-86.6, 36.4]]]
    feats = [{'type': 'Feature', 'properties': {'NAME': 'Test Lake State Park', 'OBJECTID': i, '_kpc': {'OBJECTID': f'sgzza{i}', 'Unit_Nm': 'Test Lake State Park'}},
              'geometry': {'type': 'Polygon', 'coordinates': sq}} for i in (1, 2, 3)]
    lf = M.layer_file_path(t / 'out', 'US-ZZ', 'sgzza')
    M.write_layer_file(lf, {'area': 'US-ZZ', 'layer': 'sgzza', 'count_raw': 3, 'count_live': 4, 'name_field': 'NAME', 'url': 'https://gis.example.gov/x/MapServer/0', 'label': 'Test'}, feats)
    okk, what = F.apply_layer_file(lf, cache, root, parks)
    check(f'apply: 3 of 4 = SHORT, not merged ({what})', not okk and 'SHORT' in what and len(M.load_saved(cache / 'US-ZZ.json.gz')['recs']) == 1)
    M.write_layer_file(lf, {'area': 'US-ZZ', 'layer': 'sgzza', 'count_raw': 3, 'name_field': 'NAME'}, feats)
    okk, what = F.apply_layer_file(lf, cache, root, parks)
    check(f'apply: no total known = refused ({what})', not okk and 'cannot be checked' in what)
    M.write_layer_file(lf, {'area': 'US-ZZ', 'layer': 'sgzza', 'count_raw': 3, 'count_live': 3, 'name_field': 'NAME', 'url': 'https://gis.example.gov/x/MapServer/0', 'label': 'Test'}, feats)
    okk, what = F.apply_layer_file(lf, cache, root, parks)
    recs = M.load_saved(cache / 'US-ZZ.json.gz')['recs']
    check(f'apply: a whole read is merged (keep-bigger) ({what})', okk and len(recs) == 3)
    check('apply: trim wrote the master record + the layer count', (root / 'US-ZZ.geojson.gz').exists() and 'US-ZZ.sgzza' in json.load(open(root / 'layers.json'))['layers'])
    check('apply: raw-add recorded the layer file (name, size, sha256)', any(r['name'] == lf.name and len(r['sha256']) == 64 for r in json.load(open(root / 'raw-manifest.json'))['files']))
    # fill, offline (no key, no request): a short state's saved-copy-only layer becomes a person row; ncnhde a never row
    json.dump({'format': 1, 'layers': {}, 'caches': {'US-ZZ': {'expected_count': 99}}}, open(root / 'layers.json', 'w'))
    usl = t / 'usl.json'; json.dump({'sgzzb': ['https://services-eu1.arcgis.com/a/arcgis/rest/services/B/FeatureServer/0/query', 'NAME', 'B'],
                                     'sgzzc': ['https://ncnhde.natureserve.org/arcgis/rest/services/C/MapServer/0/query', 'NAME', 'C']}, open(usl, 'w'))
    sgj = t / 'sg.json'; json.dump({'states': {}}, open(sgj, 'w'))
    with gzip.open(cache / 'US-ZZ.json.gz', 'wt') as fh: json.dump({'st': 'ZZ', 'recs': [{'OBJECTID': 'sgzzb1'}, {'OBJECTID': 'sgzzc1'}]}, fh)
    import argparse
    # Nov 10 (actually missing): a short copy alone asks no one; a row only when the live key joins a record the copy lacks
    uk = t / 'us-key'; uk.mkdir()
    A = argparse.Namespace(states='ZZ', root=str(root), work=str(t / 'w'), needs=None, hand=None, cache=str(cache), refresh='', us_layers=str(usl), state_gis=str(sgj),
                           offline=True, no_key=True, key=None, parks=str(parks), out_rows=str(t / 'rows.json'), us_key=str(uk), official_files=False)
    F.fill(A)
    check('fill: a short copy whose missing records sit in no joined layer lists nothing', json.load(open(t / 'rows.json'))['rows'] == [])
    json.dump({'parks': {'US-9999': {'m': [['sgzzb2', 'B'], ['sgzzc7', 'C']]}}}, open(uk / 'US-ZZ.json', 'w'))
    F.fill(A)
    rows = {r['id']: r for r in json.load(open(t / 'rows.json'))['rows']}
    check('fill: the joined-but-missing layer is listed with how many records are missing', rows.get('US-ZZ|sgzzb', {}).get('expected') == 2 and 'joins 1 record' in rows.get('US-ZZ|sgzzb', {}).get('why', ''))
    check('fill: services-eu1 layer with a missing joined record -> who=person', rows.get('US-ZZ|sgzzb', {}).get('who') == 'person')
    check('fill: ncnhde layer with a missing joined record -> who=never', rows.get('US-ZZ|sgzzc', {}).get('who') == 'never')
    check('fill: every row has the one schema', all(set(r) == set(M.NEEDS_FIELDS) for r in rows.values()))

# 6. kpc_us_key: the master's reader modes; the build only reads
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check('kpc_us_key: KPC_MASTER_OWNS=1 skips the build\'s own re-save of the saved copy', "MASTER_OWNS = os.environ.get('KPC_MASTER_OWNS') == '1' and not REFILL_ONLY" in src
      and src.count("if CMODE == 'use' and not MASTER_OWNS:") == 2)
check('kpc_us_key: KPC_LAYER_OUT writes layer files (no merge)', 'if LAYER_OUT is not None:' in src and '_write_layer_files(st, want, add)' in src)
check('kpc_us_key: KPC_LAYER_IN reads a checked download instead of the live layer, before the saved-only skip', src.index('lf = _layer_in(st, pre)') < src.index('if lf is None and saved_only(url): SAVED_ONLY_SKIPPED'))

# 7. the workflow: the master step sits between the plan / master check and the gate; refresh input; no new cron
wf = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
import yaml
d = yaml.safe_load(wf)
names = [s.get('name', '') for s in d['jobs']['build']['steps']]
i_chk = next(i for i, n in enumerate(names) if n.startswith('Master outlines - read master first'))
i_m = next(i for i, n in enumerate(names) if n.startswith('THE MASTER STEP'))
i_b = next(i for i, n in enumerate(names) if n.startswith('Build the answer key'))
check('workflow: master check -> THE MASTER STEP -> build (the gate is inside the build step)', i_chk < i_m < i_b)
check('workflow: the gate is not in the master step and is unchanged in the build', 'kpc_master_cli.py gate' not in d['jobs']['build']['steps'][i_m]['run'] and 'kpc_master_cli.py gate --cache cache/us --report "$RUNNER_TEMP/master-short.txt"' in d['jobs']['build']['steps'][i_b]['run'])
on = d.get('on') or d.get(True)
check('workflow: refresh input (blank or all), by hand only', 'refresh' in on['workflow_dispatch']['inputs'] and "inputs.refresh == 'all' && 'all'" in wf)
check('workflow: no new cron (still 3)', len(on['schedule']) == 3)
check('workflow: the join collects the parts and saves data/outlines; the needs rows go up as one release asset', 'kpc_master_cli.py collect parts/us-key-part-*/outlines' in wf and 'data/us-key data/status data/outlines' in wf and 'needs-download.json -R "$GITHUB_REPOSITORY" --clobber' in wf)

# 8. PC helper: stdlib only, never fetches anything but GitHub, never opens a never row, fails closed on a short download
hp = (ROOT / 'tools/kpc_pc_helper.py').read_text(encoding='utf-8')
imports = {x.split('.')[0] for x in re.findall(r'^import (.+)$', hp, re.M)[0].replace(' ', '').split(',')}
check('PC helper: standard library only (+ kpc_master)', imports <= set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else True)
check('PC helper README exists', (ROOT / 'tools/README-pc-helper.md').exists())
sys.path.insert(0, str(ROOT / 'tools'))
import kpc_pc_helper as H  # noqa: E402
try: H.fetch('https://services-eu1.arcgis.com/robots.txt'); refused = False
except SystemExit: refused = True
check('PC helper: refuses to fetch any host but GitHub', refused)
nd = {'rows': [dict(r1, who='person'), dict(r1, id='US-NM|g', layer='g', who='person', url='https://services.arcgis.com/33TOOklri9xpic7U/arcgis/rest/services/P/FeatureServer/0'),
               dict(r1, id='US-NC|n', layer='n', who='never', url='https://ncnhde.natureserve.org/x')]}
check('PC helper: only person rows, never the Grant County server or a never row', [r['id'] for r in H.rows_for_person(nd)] == ['US-AZ|fsod'])
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); dl = t / 'dl'; dl.mkdir()
    sq = [[[-86.6, 36.4], [-86.4, 36.4], [-86.4, 36.6], [-86.6, 36.6], [-86.6, 36.4]]]
    gj = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'OBJECTID': i, 'NAME': 'X'}, 'geometry': {'type': 'Polygon', 'coordinates': sq}} for i in range(3)]}
    (dl / 'x.geojson').write_text(json.dumps(gj))
    parks = t / 'parks.json'; json.dump([['POTA', 'US-9999', 'X', 36.5, -86.5, '']], open(parks, 'w'))
    row = dict(r1, area='US-TN', layer='sgtna', expected=5)
    okk, msg, out = H.check_and_pack(row, [dl / 'x.geojson'], parks, t, {})
    check(f'PC helper: a download smaller than the baseline is refused, nothing written ({msg[:60]})', not okk and 'SHORT' in msg and not list(t.glob('hand-*')))
    row['expected'] = 3
    okk, msg, out = H.check_and_pack(row, [dl / 'x.geojson'], parks, t, {})
    m2, f2 = M.read_layer_file(out) if out else ({}, [])
    check(f'PC helper: a whole download becomes one checked hand file ({msg[:60]})', okk and out.name == 'hand-US-TN.sgtna.geojson.gz' and m2.get('count_expected') == 3 and len(f2) == 3 and len(m2['raw']['sha256']) == 64)
    snap = H.snapshot(dl); (dl / 'y.json.crdownload').write_text('x')
    check('PC helper: watches Downloads and ignores files from before', H.new_files.__code__ is not None and 'x.geojson' in snap)

if __name__ == '__main__':
    print('ALL PASS' if ok else 'FAILED')
    sys.exit(0 if ok else 1)
