#!/usr/bin/env python3
"""Trimmed outline master records (Nov 10): a short read fails closed; paging honors the layer's maxRecordCount; official beats approximate;
Protected Planet / WDPA never reaches a public file; the never-contact / saved-only / robots / pacing rules hold; read master first (refresh policy).
No network: a fake layer stands in for the agency server."""
import contextlib, csv, datetime, gzip, io, json, os, pathlib, subprocess, sys, tempfile, urllib.request
HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_master as M
import kpc_master_cli as CLI
import kpc_key_freeze as KF
ok = True
def check(c, m):
    global ok; ok &= bool(c); print(('PASS ' if c else 'FAIL ') + m)
def raises(exc, fn, *a, **k):
    try: fn(*a, **k)
    except exc: return True
    except Exception: return False
    return False
def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()) as o: r = fn(*a, **k)
    return r, o.getvalue()

class FakeLayer:
    """An ArcGIS layer that sends at most `cap` rows a page (its maxRecordCount) whatever is asked; `flag` = whether it sets exceededTransferLimit."""
    def __init__(self, n, cap=200, flag=True, advertise=True):
        self.n, self.cap, self.flag, self.advertise, self.sizes, self.calls = n, cap, flag, advertise, [], 0
    def __call__(self, url, params=None):
        self.calls += 1; p = params or {}
        if p.get('returnCountOnly'): return {'count': self.n}
        if 'resultOffset' not in p: return dict({'name': 'fake', 'objectIdField': 'OBJECTID', 'editingInfo': {'lastEditDate': 111}}, **({'maxRecordCount': self.cap} if self.advertise else {}))
        off, want = int(p['resultOffset']), int(p['resultRecordCount']); self.sizes.append(want)
        k = min(want, self.cap, max(0, self.n - off))
        out = {'features': [{'attributes': {'OBJECTID': off + i + 1}, 'geometry': None} for i in range(k)]}
        if self.flag and off + k < self.n: out['exceededTransferLimit'] = True
        return out

# --- 1) the Nov 3 case: a layer that sends 200 a page, asked for 500
for flag in (True, False):
    lay = FakeLayer(17000, cap=200, flag=flag)
    feats, info = M.read_layer('https://example.gov/arc/0', lay, want_page=500)
    check(len(feats) == 17000, f'paging: 17,000 of 17,000 read from a layer that sends 200 a page (server flag {"on" if flag else "OFF"})')
    check(max(lay.sizes) <= 200, f'paging: no page asked for more than the layer\'s maxRecordCount 200 (asked {max(lay.sizes)})')
lay = FakeLayer(1234, cap=200, flag=False, advertise=False)
feats, _ = M.read_layer('https://example.gov/arc/0', lay, want_page=500)
check(len(feats) == 1234, 'paging: a layer that hides its limit and sets no flag is still read to the end (it sends fewer than a page while its own total says more)')
# the old end test would have stopped after the first 200
old_stop = len(FakeLayer(17000, cap=200, flag=False)('u', {'resultOffset': 0, 'resultRecordCount': 500})['features']) < 500
check(old_stop, 'paging: the old end test (fewer than our page = last page) WOULD have stopped at 200 here - the bug this guards')

# --- 2) a short read fails closed
class Lying(FakeLayer):   # says 17,000, only ever delivers 199 and then empty pages
    def __call__(self, url, params=None):
        r = super().__call__(url, params)
        if 'features' in r and int((params or {}).get('resultOffset', 0)) >= 199: return {'features': []}
        if 'features' in r: r['features'] = r['features'][:199]; r.pop('exceededTransferLimit', None)
        return r
check(raises(M.ShortRead, M.read_layer, 'https://example.gov/arc/0', Lying(17000), 500), 'short read: 199 of 17,000 raises ShortRead (FL DEP sgflf case), nothing returned')
check(raises(M.ShortRead, M.check_complete, None, 10), 'short read: a layer that reports no total cannot be verified, refused')
check(M.check_complete(5, 5) and M.check_complete(5, 6), 'short read: complete or over is accepted')

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); root = t / 'out'
    parks = [['POTA', 'US-0001', 'Alpha State Park', 36.5, -85.5, ''], ['POTA', 'US-0002', 'Beta Wildlife Area', 36.8, -85.1, ''],
             ['POTA', 'US-0003', 'Gamma Creek Forest', 36.9, -85.9, ''], ['POTA', 'US-0004', 'Lonely Park', 36.2, -85.2, ''],
             ['POTA', 'US-0005', 'Delta Lake', 35.5, -85.0, ''], ['POTA', 'US-0006', 'Echo Ridge', 35.0, -83.0, '']]
    json.dump(parks, open(t / 'parks.json', 'w'))
    def sq(x, y, d=0.02): return [[[x - d, y - d], [x + d, y - d], [x + d, y + d], [x - d, y + d], [x - d, y - d]]]
    def gj(feats, p): json.dump({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': pr, 'geometry': {'type': 'Polygon', 'coordinates': g}} for pr, g in feats]}, open(p, 'w'))
    # alpha by id, beta by name + pin, gamma ambiguous (two names fit), lonely nothing; plus a land piece no park matches
    gj([({'OBJECTID': 1, 'POTA_REF': 'US-0001', 'Unit': 'Something Else'}, sq(-85.5, 36.5)), ({'OBJECTID': 2, 'POTA_REF': '', 'Unit': 'Beta Wildlife Area'}, sq(-85.1, 36.8)),
        ({'OBJECTID': 3, 'POTA_REF': '', 'Unit': 'Gamma Creek North'}, sq(-85.9, 36.9, .03)), ({'OBJECTID': 4, 'POTA_REF': '', 'Unit': 'Gamma Creek South'}, sq(-85.9, 36.9, .025)),
        ({'OBJECTID': 5, 'POTA_REF': '', 'Unit': 'Unrelated Ranch'}, sq(-84.0, 35.0)),
        ({'OBJECTID': 6, 'POTA_REF': '', 'Unit': 'Delta Lake'}, sq(-85.0, 35.47, .01)), ({'OBJECTID': 7, 'POTA_REF': '', 'Unit': 'Echo Ridge'}, sq(-83.0, 35.0, .01))], t / 'agency.geojson')
    base = ['trim', '--layer-key', 'ky-agency', '--input', str(t / 'agency.geojson'), '--parks', str(t / 'parks.json'), '--area', 'US-KY', '--root', str(root),
            '--agency', 'State Parks', '--license', 'public domain', '--id-fields', 'POTA_REF', '--name-fields', 'Unit', '--record-id-field', 'OBJECTID']
    # a file with no expected count cannot be verified
    r, _ = quiet(CLI.main, base); check(r == 3 and not root.exists(), 'trim: a file with no expected count is refused (exit 3), nothing written')
    # a short file (5 of 17,000) fails closed and writes nothing, and does not set a baseline
    r, _ = quiet(CLI.main, base + ['--expected', '17000']); check(r == 2 and not (root / 'US-KY.geojson.gz').exists() and not (root / 'layers.json').exists(),
                                                                 'trim: 7 of 17,000 -> exit 2 (SHORT), no master file and no baseline written')
    # a good read
    r, out = quiet(CLI.main, base + ['--expected', '7']); recs = M.load_area('US-KY', root)
    check(r == 0 and set(recs) == {'US-0001', 'US-0002', 'US-0006'}, f'trim: id match (US-0001) and name+pin match (US-0002) kept; ambiguous and unmatched are not ({sorted(recs)})')
    check(recs['US-0001']['via'] == 'id' and recs['US-0002']['via'] == 'name+pin', 'trim: each record says how it matched')
    q = list(csv.DictReader(open(root / 'solver-queue/ky-agency.csv')))
    check({x['ref'] for x in q} == {'US-0003', 'US-0005'} and 'ambiguous' in [x['why'] for x in q if x['ref'] == 'US-0003'][0] and 'outside' in [x['why'] for x in q if x['ref'] == 'US-0005'][0],
          'trim: ambiguous Gamma and Delta Lake (pin just outside its same-name outline) go to the solver queue; Lonely Park (not in this layer) and the unrelated ranch are not queued')
    check(len(recs) == 3 and all(len(r_['record_ids']) >= 1 for r_ in recs.values()) and 'row' not in json.dumps([r_['record_ids'] for r_ in recs.values()]), 'trim: ONLY matched park geometry is kept, with the source record ids')
    need = {'ref', 'name', 'geometry', 'g', 'agency', 'layer_url', 'record_ids', 'source_count', 'date_read', 'license', 'hash'}
    check(all(need <= set(r_) for r_ in recs.values()), 'format: every record carries ref, name, geometry, g, agency, layer url, record ids, source count, date read, licence, hash')
    check(json.load(open(t / 'parks.json')) == parks, 'trim: the POTA pin file is untouched (a pin is never moved)')
    lay = M.load_layers(root)['layers']['ky-agency']
    check(lay['expected_count'] == 7 and lay['source_count'] == 7 and lay['matched'] == 3, 'manifest: the layer\'s expected count is stored with the read')
    # same input again = identical bytes (git shows no change)
    b1 = (root / 'US-KY.geojson.gz').read_bytes(); quiet(CLI.main, base + ['--expected', '7']); check((root / 'US-KY.geojson.gz').read_bytes() == b1, 'format: an unchanged re-read writes byte-identical files')
    # a later short read does not become the baseline; and a big shrink is held
    gj([({'OBJECTID': 1, 'POTA_REF': 'US-0001', 'Unit': 'x'}, sq(-85.5, 36.5))], t / 'small.geojson')
    r, _ = quiet(CLI.main, ['trim', '--layer-key', 'ky-agency', '--input', str(t / 'small.geojson'), '--parks', str(t / 'parks.json'), '--root', str(root), '--expected', '1'])
    check(r == 6 and M.load_layers(root)['layers']['ky-agency']['expected_count'] == 7, 'baseline: a layer now reporting 1 (was 7) is HELD, the baseline stays 7')
    r, _ = quiet(CLI.main, ['trim', '--layer-key', 'ky-agency', '--input', str(t / 'agency.geojson'), '--parks', str(t / 'parks.json'), '--root', str(root)])
    check(r == 0, 'baseline: the stored expected count is used when none is given, and a full read passes')
    r, _ = quiet(CLI.main, ['check', '--root', str(root)]); check(r == 0, 'check: a clean master passes')
    # tamper: a changed geometry no longer matches its hash
    d = M.load_area('US-KY', root); d['US-0001']['geometry']['coordinates'][0][0][0] += 0.5; M.save_area('US-KY', d, root)
    r, _ = quiet(CLI.main, ['check', '--root', str(root)]); check(r == 1, 'check: an edited outline whose hash no longer matches fails')

# --- 3) official beats approximate
G = lambda: {'type': 'Polygon', 'coordinates': sq(-85, 36)}
mk = lambda g, url='https://a.gov/0', geom=None: M.make_record('US-1', 'P', g, geom or G(), 'A', url, ['1'], 10, '2026-11-10', 'pd', 'id')
o, ap, cc, pn = mk('official'), mk('approximate', 'https://b.org/0'), mk('point-circle', 'https://c.org/0'), mk('pin', 'https://d.org/0')
check(M.merge(o, ap)[0] is o and M.merge(o, cc)[0] is o and M.merge(o, pn)[0] is o, 'precedence: an official outline is never replaced by an approximate trace, a circle or a pin')
check(M.merge(ap, o)[0] is o and M.merge(cc, ap)[0] is ap and M.merge(pn, cc)[0] is cc, 'precedence: official > approximate > circle > pin when the better one arrives later')
o2 = mk('official', 'https://other.gov/0'); check(M.merge(o, o2)[0] is o and M.merge(o, o2)[1].startswith('conflict'), 'precedence: two officials from different layers: keep the saved one, report a conflict')
o3 = mk('official', geom={'type': 'Polygon', 'coordinates': sq(-85, 36, .03)}); check(M.merge(o, o3)[0] is o3, 'precedence: the same layer read again replaces its own record (a refresh)')
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); root = t / 'out'
    json.dump([['POTA', 'US-0001', 'Alpha State Park', 36.5, -85.5, '']], open(t / 'p.json', 'w'))
    gj([({'OBJECTID': 1, 'REF': 'US-0001'}, sq(-85.5, 36.5, .02))], t / 'official.geojson'); gj([({'OBJECTID': 9, 'REF': 'US-0001'}, sq(-85.5, 36.5, .05))], t / 'trace.geojson')
    run = lambda key, f, g: quiet(CLI.main, ['trim', '--layer-key', key, '--input', str(f), '--parks', str(t / 'p.json'), '--area', 'US-KY', '--root', str(root), '--expected', '1', '--g', g, '--id-fields', 'REF', '--record-id-field', 'OBJECTID', '--agency', key])[0]
    run('official-layer', t / 'official.geojson', 'official'); run('trace-layer', t / 'trace.geojson', 'approximate')
    rec = M.load_area('US-KY', root)['US-0001']; check(rec['g'] == 'official' and rec['agency'] == 'official-layer', 'precedence (end to end): a trace read AFTER the official outline does not overwrite it')
    shutil_root = t / 'out2'; run2 = lambda key, f, g: quiet(CLI.main, ['trim', '--layer-key', key, '--input', str(f), '--parks', str(t / 'p.json'), '--area', 'US-KY', '--root', str(shutil_root), '--expected', '1', '--g', g, '--id-fields', 'REF', '--record-id-field', 'OBJECTID', '--agency', key])[0]
    run2('trace-layer', t / 'trace.geojson', 'approximate'); run2('official-layer', t / 'official.geojson', 'official')
    check(M.load_area('US-KY', shutil_root)['US-0001']['g'] == 'official', 'precedence (end to end): the official outline replaces an earlier trace')

# --- 4) WDPA never in public output
w = M.make_record('US-9', 'W', 'official', G(), 'Protected Planet', 'https://www.protectedplanet.net/x', ['1'], 1, '2026-11-10', 'WDPA terms', 'id')
check(raises(M.LicenseBlocked, M.assert_public_safe, w), 'WDPA: a Protected Planet record is refused')
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); root = t / 'out'
    check(raises(M.LicenseBlocked, M.save_area, 'US-ZZ', {'US-9': w}, root) and not list(root.glob('*')), 'WDPA: save_area refuses it, no file is written')
    json.dump([['POTA', 'US-0001', 'Alpha', 36.5, -85.5, '']], open(t / 'p.json', 'w')); gj([({'REF': 'US-0001'}, sq(-85.5, 36.5))], t / 'WDPA_polygons.geojson')
    r, _ = quiet(CLI.main, ['trim', '--layer-key', 'wdpa-us', '--input', str(t / 'WDPA_polygons.geojson'), '--parks', str(t / 'p.json'), '--root', str(root), '--expected', '1', '--id-fields', 'REF'])
    check(r == 4 and not root.exists(), 'WDPA: trim of a WDPA file exits 4 and writes nothing')
    r, _ = quiet(CLI.main, ['trim', '--layer-key', 'some-layer', '--input', str(t / 'WDPA_polygons.geojson'), '--parks', str(t / 'p.json'), '--root', str(root), '--expected', '1', '--id-fields', 'REF'])
    check(r == 4, 'WDPA: caught by the file name too, whatever the layer key says')
    rows = [{'WDPAID': 1, 'NAME': 'X', 'MANG_AUTH': 'Some Dept', 'OWN_TYPE': 'State', 'geometry': {'type': 'Polygon'}, 'lat': 1, 'lon': 2}]
    look = M.wdpa_agency_lookup(rows); check(look == [{'WDPAID': 1, 'NAME': 'X', 'MANG_AUTH': 'Some Dept', 'OWN_TYPE': 'State'}], 'WDPA: the private lookup keeps the managing agency fields only, no geometry or coordinates')
    json.dump({'features': [{'properties': rows[0]}]}, open(t / 'w.json', 'w'))
    check(M.private_path_ok(HERE / 'data/outlines/lookup.csv')[0] is False and M.private_path_ok(t / 'priv/lookup.csv')[0], 'WDPA: the lookup file may not be written inside the repo, only outside it')
    r, _ = quiet(CLI.main, ['wdpa-lookup', '--input', str(t / 'w.json'), '--out', str(HERE / 'data/outlines/lookup.csv')]); check(r == 4 and not (HERE / 'data/outlines/lookup.csv').exists(), 'WDPA: wdpa-lookup refuses a path inside the repo')
    r, _ = quiet(CLI.main, ['wdpa-lookup', '--input', str(t / 'w.json'), '--out', str(t / 'priv/lookup.csv')]); txt = open(t / 'priv/lookup.csv').read()
    check(r == 0 and 'Some Dept' in txt and 'geometry' not in txt and 'lat' not in txt.lower().split('\n')[0], 'WDPA: the private lookup file holds the agency and no geometry')
    bad = M.make_record('US-1', 'ok', 'official', G(), 'State', 'https://s.gov/0', ['1'], 1, '2026-11-10', 'pd', 'id'); (t / 'chk').mkdir(); M.save_area('US-KY', {'US-1': bad}, t / 'chk')
    allt = b''.join(gzip.open(p).read() for p in (t / 'chk').glob('*.gz')) + (t / 'chk').joinpath('x').read_bytes() if False else b''.join(gzip.open(p).read() for p in (t / 'chk').glob('*.gz'))
    check(not M.WDPA_RE.search(allt.decode()), 'WDPA: nothing in the written master files mentions WDPA / Protected Planet')
shipped = list((HERE / 'data/outlines').rglob('*')) if (HERE / 'data/outlines').exists() else []
txt = ''.join((gzip.open(p).read().decode() if p.suffix == '.gz' else p.read_text(errors='ignore')) for p in shipped if p.is_file() and p.name != 'README.md')
check(not M.WDPA_RE.search(txt), 'WDPA: nothing under data/outlines/ as shipped mentions WDPA / Protected Planet')

# --- 5) hosts, robots, pacing
calls = []
real = urllib.request.urlopen
def spy(req, *a, **k): calls.append(getattr(req, 'full_url', str(req))); raise AssertionError('network touched: ' + calls[-1])
urllib.request.urlopen = spy
try:
    f = M.http_fetcher(M.Pacer(clock=lambda: 0, sleep=lambda s: None), max_tries=1)
    for u in ('https://services.arcgis.com/33TOOklri9xpic7U/arcgis/rest/services/x/FeatureServer/0', 'https://ncnhde.natureserve.org/arcgis/x/0', 'https://services.arcgis.com/ABC/x/0',
              'https://services1.arcgis.com/ABC/x/0', 'https://apps.fs.usda.gov/arcx/x/0'):
        check(raises(M.LiveNotAllowed, f, u, {'f': 'json'}), f'hosts: {u.split("/")[2]}{"/" + u.split("/")[3] if "33TOO" in u else ""} is refused')
    check(not calls, 'hosts: no request of any kind (robots.txt included) was made for any of them')
finally: urllib.request.urlopen = real
check(M.live_ok('https://services.arcgis.com/33TOOklri9xpic7U/a')[0] is False and M.live_ok('https://services.arcgis.com/OTHER/a')[0] is False, 'hosts: Grant County NM never contacted; other services.arcgis.com orgs are saved-copy only')
check(M.live_ok('https://gis.example.gov/arc/0')[0], 'hosts: an ordinary agency host is allowed (then robots.txt decides)')
get403 = lambda u: (403, ''); get404 = lambda u: (404, ''); get500 = lambda u: (503, '')
getdis = lambda u: (200, 'User-agent: *\nDisallow: /arc/\n'); getok = lambda u: (200, 'User-agent: *\nDisallow: /private/\n')
check(M.robots_allows('https://h.gov/arc/0', get403) is False, 'robots: a 403 on robots.txt = disallow')
check(M.robots_allows('https://h.gov/arc/0', get500) is False and M.robots_allows('https://h.gov/arc/0', getdis) is False, 'robots: a server error, or a Disallow rule = disallow')
check(M.robots_allows('https://h.gov/arc/0', get404) and M.robots_allows('https://h.gov/arc/0', getok), 'robots: no robots.txt (404) or an allowing one = allowed')
clk = [0.0]; slept = []; pc = M.Pacer(clock=lambda: clk[0], sleep=lambda s: (slept.append(s), clk.__setitem__(0, clk[0] + s)))
pc.wait('hub.arcgis.com'); pc.wait('hub.arcgis.com'); pc.wait('gis.example.gov'); pc.wait('gis.example.gov')
check(slept == [60.0, 2.0], f'pacing: 60 s between hub portal requests, 2 s for other hosts ({slept})')
check(M.host_delay('kpc.maps.hub.arcgis.com') == 60 and M.host_delay('x.opendata.arcgis.com') == 60 and M.host_delay('gis.example.gov') == 2, 'pacing: sub-domain hub portals count too')

# --- 6) read master first: the refresh policy
now = datetime.datetime(2026, 11, 10, tzinfo=datetime.timezone.utc)
doc = {'layers': {'fresh': {'url': 'https://g.gov/a/0', 'read_date': '2026-11-05', 'expected_count': 100, 'last_edit': 5, 'areas': ['US-KY']},
                  'old': {'url': 'https://g.gov/b/0', 'read_date': '2026-09-01', 'expected_count': 100, 'last_edit': 5, 'areas': ['US-KY']},
                  'edited': {'url': 'https://g.gov/c/0', 'read_date': '2026-11-05', 'expected_count': 100, 'last_edit': 5, 'areas': ['US-KY']},
                  'counted': {'url': 'https://g.gov/d/0', 'read_date': '2026-11-05', 'expected_count': 100, 'last_edit': 5, 'areas': ['US-KY']},
                  'never': {'url': 'https://g.gov/e/0', 'areas': ['US-KY']}, 'saved': {'url': 'https://services.arcgis.com/ABC/x/0', 'read_date': '2026-08-01', 'expected_count': 9, 'areas': ['US-KY']},
                  'other-state': {'url': 'https://g.gov/f/0', 'read_date': '2026-09-01', 'expected_count': 1, 'areas': ['US-OH']}}}
probed = []
def probe(L):
    probed.append(L['url']); return {'count': 101 if L['url'].endswith('d/0') else 100, 'last_edit': 6 if L['url'].endswith('c/0') else 5}
pl = {r['layer']: r for r in M.plan(doc, now, 30, probe, areas=['US-KY'])}
check(pl['fresh']['action'] == 'use-master', 'refresh: a fresh layer with the same edit date and count is read from master')
check(pl['old']['action'] == 're-read' and pl['old']['reason'].startswith('(a)'), 'refresh (a): older than N days -> re-read')
check(pl['edited']['action'] == 're-read' and pl['edited']['reason'].startswith('(b)'), 'refresh (b): lastEditDate changed -> re-read')
check(pl['counted']['action'] == 're-read' and pl['counted']['reason'].startswith('(c)'), 'refresh (c): count check differs -> re-read')
check(pl['never']['action'] == 're-read', 'refresh: a layer with no master yet is read once')
check(pl['saved']['action'] == 'use-master' and 'OLD' in pl['saved']['reason'] and not any('services.arcgis.com' in u for u in probed), 'refresh: a saved-copy-only host is never probed live; an old master is flagged, not re-read')
check('other-state' not in pl and sum(1 for r in pl.values() if r['action'] == 're-read') == 4, 'refresh: only the asked area\'s layers are planned, and only the layers that need it are re-read (one layer, not the whole state)')

# --- 7) a short SAVED copy (the Nov 3 caches) is caught
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); c = t / 'cache'; c.mkdir()
    with gzip.open(c / 'US-FL.json.gz', 'wt') as fh: json.dump({'st': 'FL', 'seen': 199, 'recs': [{}] * 199}, fh)
    check(raises(M.ShortRead, M.check_saved_cache, c / 'US-FL.json.gz', 17000), 'saved copy: FL with 199 of ~17,000 fails the check')
    root = t / 'o'; M.save_layers({'format': 1, 'layers': {}, 'caches': {'US-FL': {'expected_count': 17000}}}, root)
    r, _ = quiet(CLI.main, ['check', '--root', str(root), '--cache', str(c)]); check(r == 1, 'saved copy: `check --cache` goes red on it')

# --- 8) raw files: manifest only
check(M.raw_in_repo([('data/x.gdb/a', 10), ('big.zip', 10), ('layer.shp', 1), ('data/outlines/US-KY.geojson.gz', 100), ('index.html', 10 ** 7), ('data/outlines/huge.geojson.gz', 10 ** 7)]) == ['data/x.gdb/a', 'big.zip', 'layer.shp', 'data/outlines/huge.geojson.gz'],
      'raw: layer downloads (.gdb, .zip, .shp...) and any master file over 5 MB are flagged; a normal master file and site files are not')
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); (t / 'a.bin').write_bytes(b'hello'); row = M.raw_add(t / 'a.bin', 'Example Agency', '2026-11-10', root=t / 'o')
    check(row == {'name': 'a.bin', 'size': 5, 'sha256': '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824', 'source': 'Example Agency', 'date': '2026-11-10'}, 'raw: the manifest row is name, size, sha256, source, date')
# the tracked tree has none
try:
    files = CLI.tracked_files(HERE); check(M.raw_in_repo(files) == [], 'raw: this repo tracks no raw layer files')
except Exception as e: print('SKIP raw tracked check:', e)

# --- 9) rules hashes do not move
for k in ('us-key', 'ca-key', 'world-key', 'fers'):
    check(not any('kpc_master' in f for f in KF.RULE_FILES[k]), f'{k}: the master modules are not in its rules hash')
check({'kpc_master.py', 'kpc_master_cli.py'} <= KF.NOT_RULES, 'the master modules are listed in NOT_RULES')
try:
    for f in sorted({f for fs in KF.RULE_FILES.values() for f in fs}):
        same = subprocess.run(['git', '-C', str(HERE), 'diff', '--quiet', 'origin/main', '--', f], capture_output=True).returncode == 0
        check(same, f'rule file unchanged from main: {f}')
except Exception as e: print('SKIP rule-file diff:', e)


# --- 10) the workflows: the US gate really drops only the short state (the shell step, run for real on a fake cache)
try:
    import yaml
    for wf, key in (('kpc-us-key.yml', 'us'), ('kpc-ca-key.yml', 'ca'), ('kpc-world-key.yml', 'world')):
        d = yaml.safe_load(open(HERE / '.github/workflows' / wf)); txt = open(HERE / '.github/workflows' / wf).read()
        check('kpc_master_cli.py gate' in txt and 'kpc_master_cli.py check' in txt and 'kpc_master_cli.py plan' in txt and 'Master gate verdict' in txt, f'{wf}: reads master first (check + plan), gates the saved copy, ends with the verdict step')
    d = yaml.safe_load(open(HERE / '.github/workflows/kpc-us-key.yml'))
    run = [s_['run'] for s_ in d['jobs']['build']['steps'] if s_.get('name', '').startswith('Build the answer key')][0]
    snip = run[run.index('# Nov 10 (master outlines'):run.index('python3 .github/scripts/kpc_us_key.py')]
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); (t / 'cache/us').mkdir(parents=True); (t / '.github/scripts').mkdir(parents=True); (t / 'data/outlines').mkdir(parents=True)
        for fn in ('kpc_master.py', 'kpc_master_cli.py'): (t / '.github/scripts' / fn).write_bytes((HERE / '.github/scripts' / fn).read_bytes())
        json.dump({'format': 1, 'layers': {}, 'caches': {'US-FL': {'expected_count': 17000}, 'US-TN': {'expected_count': 100}}}, open(t / 'data/outlines/layers.json', 'w'))
        for st, seen in (('FL', 199), ('TN', 100), ('KY', 5)):
            with gzip.open(t / f'cache/us/US-{st}.json.gz', 'wt') as fh: json.dump({'seen': seen, 'recs': []}, fh)
        r = subprocess.run(['bash', '-e', '-c', 'set -o pipefail\nSTATES="FL TN KY"\n' + snip + '\necho "STATES NOW: $STATES"'], cwd=t, capture_output=True, text=True, env=dict(os.environ, RUNNER_TEMP=str(t)))
        check(r.returncode == 0 and 'STATES NOW: TN KY' in r.stdout and (t / 'cache/us/short/US-FL.json.gz').exists() and (t / 'cache/us/US-TN.json.gz').exists(), 'workflow: with a short Florida copy the US job builds TN and KY, not FL, and the short copy is set aside')
        check((t / 'master-short.txt').read_text().split() == ['US-FL'], 'workflow: the short copy is named for the verdict step (which then fails the job)')
except ImportError: print('SKIP workflow checks: PyYAML not installed')

print('ALL PASS' if ok else 'FAILED'); sys.exit(0 if ok else 1)
