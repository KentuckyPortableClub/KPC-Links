#!/usr/bin/env python3
"""Nov 10: the needs list asks only for what is actually missing. (1) the master step lists a layer only when the live key joins
records of it that the saved copy does not hold (or a new layer has none); (2) the seed checks the US / CA-ALL / W-XX copies by layer
id and source label; (3) import-existing takes in the downloads already made (raw facts only) and builds checked hand files; (4) an
official direct file a bot may fetch makes the row a bot's, through the same pre-request check, robots.txt and pacing; (5) the PC
helper's tally counts only rows it can use. No server is contacted: every request goes to a stand-in."""
import contextlib, csv, gzip, io, json, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts')); sys.path.insert(0, str(ROOT / 'tools'))
import kpc_master as M  # noqa: E402
import kpc_master_watch as W  # noqa: E402
import kpc_master_import as I  # noqa: E402
import kpc_pc_helper as H  # noqa: E402
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def gz(path, obj):
    with gzip.open(path, 'wt', encoding='utf-8') as f: json.dump(obj, f)


T = pathlib.Path(tempfile.mkdtemp())

# ---- (4) who_for with an official direct file; the download path refuses before any request ---------------------------------
AG = 'https://services.arcgis.com/abc/arcgis/rest/services/X/FeatureServer/0'
check('who_for: a saved-copy-only layer with no file is a person\'s', M.who_for(AG)[0] == 'person')
w, why = M.who_for(AG, file_url='https://irma.nps.gov/DataStore/DownloadFile/1')
check('who_for: the same layer with an official direct file on an allowed host is a bot\'s', w == 'bot' and 'irma.nps.gov' in why)
check('who_for: a direct file on a services*.arcgis.com host does not make it a bot\'s', M.who_for(AG, file_url='https://services-eu1.arcgis.com/x/file.zip')[0] == 'person')
check('who_for: a direct file whose robots.txt says no does not make it a bot\'s',
      M.who_for(AG, robots_ok=lambda u: 'irma' not in u, file_url='https://irma.nps.gov/x')[0] == 'person')
check('who_for: never-contact stays never, file or not', M.who_for('https://ncnhde.natureserve.org/arcgis/x', file_url='https://irma.nps.gov/x')[0] == 'never')
check('direct_file_of reads the row note', M.direct_file_of({'note': 'x direct file: https://a.gov/f.zip y'}) == 'https://a.gov/f.zip' and M.direct_file_of({}) is None)

import email, urllib.request, urllib.response


def raises_(E, f, *a):
    try: f(*a); return False
    except E: return True


class Stand(urllib.request.BaseHandler):
    """A stand-in for http(s): routes {url: (status, headers, body)}; anything else is a 404. Records every address asked."""
    handler_order = 100
    def __init__(self, routes): self.routes, self.calls = routes, []
    def https_open(self, req):
        u = req.full_url; self.calls.append(u)
        st, hd, body = self.routes.get(u, (404, {}, b''))
        r = urllib.response.addinfourl(io.BytesIO(body), email.message_from_string(''.join(f'{k}: {v}\n' for k, v in hd.items())), u, st)
        r.msg = 'stand-in'; return r
    http_open = https_open


class P(M.Pacer):
    def __init__(self): super().__init__(); self.waits = []
    def wait(self, host): self.waits.append(host)


OKF = 'https://irma.nps.gov/DataStore/DownloadFile/1'
for bad in ('https://services2.arcgis.com/x/file.zip', 'https://services-eu1.arcgis.com/x/f.zip', 'https://ncnhde.natureserve.org/f.zip', 'https://apps.fs.usda.gov/f.zip'):
    st_ = Stand({})
    try: M.download_official_file(bad, T / 'f.bin', handlers=[st_]); check(f'download refuses {bad}', False)
    except M.LiveNotAllowed: check(f'download refuses {bad.split("/")[2]} before any request (robots.txt included)', not st_.calls)
st_ = Stand({'https://irma.nps.gov/robots.txt': (403, {}, b'')})
try: M.download_official_file(OKF, T / 'f.bin', handlers=[st_]); check('robots 403 refuses', False)
except M.LiveNotAllowed: check('download: a robots.txt 403 is a no (only robots.txt was asked)', st_.calls == ['https://irma.nps.gov/robots.txt'])

# every redirect hop is checked before it is followed (live_ok + robots.txt); a hop onto a forbidden host is refused, never asked
for name, target in (('services2.arcgis.com', 'https://services2.arcgis.com/wCOMu5IS7YdSyPNx/arcgis/rest/services/x/FeatureServer/0/query?f=json'),
                     ('ncnhde.natureserve.org', 'https://ncnhde.natureserve.org/arcgis/rest/services/x/MapServer/0'),
                     ('the Grant County server', 'https://services.arcgis.com/33TOOklri9xpic7U/arcgis/rest/services/Parcels/FeatureServer/0'),
                     ('services-eu1.arcgis.com (relative hop)', '//services-eu1.arcgis.com/x/f.zip')):
    st_ = Stand({'https://irma.nps.gov/robots.txt': (404, {}, b''), OKF: (302, {'Location': target}, b'')})
    try: M.download_official_file(OKF, T / 'r.bin', handlers=[st_], pacer=P()); check(f'302 to {name} refused', False)
    except M.LiveNotAllowed:
        check(f'download: a 302 to {name} is refused before it is asked (robots.txt included), nothing written',
              all(name.split()[0].split('(')[0].strip() not in c for c in st_.calls) and not any('arcgis.com' in c or 'natureserve' in c for c in st_.calls)
              and not (T / 'r.bin').exists() and not (T / 'r.bin.part').exists())
OK2 = 'https://www.sciencebase.gov/catalog/file/get/abc'
st_ = Stand({'https://irma.nps.gov/robots.txt': (404, {}, b''), OKF: (302, {'Location': 'https://www.sciencebase.gov/robots-test'}, b''),
             'https://www.sciencebase.gov/robots.txt': (200, {}, b'User-agent: *\nDisallow: /robots-test\n')})
try: M.download_official_file(OKF, T / 'r.bin', handlers=[st_], pacer=P()); check('302 to a robots-disallowed path refused', False)
except M.LiveNotAllowed: check('download: a 302 to a path the landing host\'s robots.txt disallows is refused', 'https://www.sciencebase.gov/robots-test' not in st_.calls)
pc = P()
st_ = Stand({'https://irma.nps.gov/robots.txt': (404, {}, b''), OKF: (302, {'Location': OK2}, b''),
             'https://www.sciencebase.gov/robots.txt': (404, {}, b''), OK2: (200, {}, b'x' * 1000)})
f = M.download_official_file(OKF, T / 'nps.zip', handlers=[st_], pacer=pc)
check('download: a 302 to an allowed host passes (robots.txt of each host first, each request paced per host)',
      st_.calls == ['https://irma.nps.gov/robots.txt', OKF, 'https://www.sciencebase.gov/robots.txt', OK2] and f['size'] == 1000 and (T / 'nps.zip').exists()
      and pc.waits.count('irma.nps.gov') >= 2 and pc.waits.count('www.sciencebase.gov') >= 2)
check('download: raw facts only (name, size, sha256, source, date)', set(f) == {'name', 'size', 'sha256', 'source', 'date'})
st_ = Stand({'https://irma.nps.gov/robots.txt': (302, {'Location': 'https://services9.arcgis.com/robots.txt'}, b'')})
try: M.download_official_file(OKF, T / 'r.bin', handlers=[st_]); check('robots redirect refused', False)
except M.LiveNotAllowed: check('download: a robots.txt that redirects to a forbidden host is refused, never asked', not any('services9' in c for c in st_.calls))
# the live layer reader and the robots.txt / HEAD helpers refuse a forbidden redirect hop too
_real_build = urllib.request.build_opener
def _with(stand):
    urllib.request.build_opener = lambda *h: _real_build(*h, stand)
LAY = 'https://gis.example.gov/arcgis/rest/services/x/MapServer/0'
for target in ('https://services2.arcgis.com/X/arcgis/rest/services/x/FeatureServer/0?f=json', 'https://ncnhde.natureserve.org/x?f=json', 'https://services.arcgis.com/33TOOklri9xpic7U/arcgis/rest/services/P/FeatureServer/0?f=json'):
    st_ = Stand({'https://gis.example.gov/robots.txt': (404, {}, b''), LAY + '?f=json': (302, {'Location': target}, b'')})
    _with(st_)
    try:
        fx = M.http_fetcher(M.Pacer(clock=lambda: 0, sleep=lambda s: None), max_tries=1)
        check(f'layer reader: a 302 to {target.split("/")[2]}{"/33TOO.." if "33TOO" in target else ""} is refused, never asked', raises_(M.LiveNotAllowed, fx, LAY, {'f': 'json'}) and target not in st_.calls)
    finally: urllib.request.build_opener = _real_build
st_ = Stand({'https://gis.example.gov/robots.txt': (404, {}, b''), LAY + '?f=json': (302, {'Location': 'https://gis2.example.gov/l?f=json'}, b''),
             'https://gis2.example.gov/robots.txt': (404, {}, b''), 'https://gis2.example.gov/l?f=json': (200, {}, b'{"name": "ok"}')})
_with(st_)
try:
    fx = M.http_fetcher(M.Pacer(clock=lambda: 0, sleep=lambda s: None), max_tries=1)
    check('layer reader: a 302 to an allowed host passes after that host\'s robots.txt', fx(LAY, {'f': 'json'}).get('name') == 'ok' and 'https://gis2.example.gov/robots.txt' in st_.calls)
finally: urllib.request.build_opener = _real_build
st_ = Stand({'https://gis.example.gov/robots.txt': (302, {'Location': 'https://ncnhde.natureserve.org/robots.txt'}, b'')})
try: M.host_checked_opener([st_]).open('https://gis.example.gov/robots.txt'); check('robots helper redirect refused', False)
except M.LiveNotAllowed: check('robots.txt / HEAD helper: a redirect onto a forbidden host is refused, never asked', not any('natureserve' in c for c in st_.calls))
for nm in ('kpc_master.py', 'kpc_master_fill.py', 'kpc_master_watch.py'):
    check(f'{nm}: no plain urlopen left (every request uses a checked-redirect opener)', 'urlopen(' not in (ROOT / '.github/scripts' / nm).read_text(encoding='utf-8'))
msrc = (ROOT / '.github/scripts/kpc_master.py').read_text(encoding='utf-8')
dsrc = msrc[msrc.index('def download_official_file('):msrc.index('def saved_counts(')]
check('download: no plain urlopen (every open goes through the checked-redirect opener)', 'urlopen' not in dsrc and 'checked_opener(hop_check' in dsrc)
fill_src = (ROOT / '.github/scripts/kpc_master_fill.py').read_text(encoding='utf-8')
check('master step: the official-file path runs only when asked (--official-files) and never offline', "if getattr(a, 'official_files', False) and not a.offline" in fill_src)
wf = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
check('workflow: only refresh=all (the fresh-start run) downloads official files; no new schedule', '[ "$REFRESH" = all ] && echo --official-files' in wf)

# ---- (1) actually missing ---------------------------------------------------------------------------------------------------
blob = {'recs': [{'OBJECTID': 'sgxxa1'}, {'OBJECTID': 'sgxxa2'}, {'OBJECTID': 7}, {'OBJECTID': 'sgxxb5'}]}
(T / 'US-XX.json').write_text(json.dumps({'parks': {'US-1': {'m': [['sgxxa1', 'A']], 'bk': [7, 0.1]}, 'US-2': {'m': [['sgxxa9', 'B'], ['trl3', 'T']]},
                                                    'US-3': {'m': [['sgxxc4', 'C']], 'bk': ['sgxxc4', 0]}}}))
miss = M.joined_missing(T / 'US-XX.json', blob)
check('joined_missing: only ids the key joins and the copy lacks, by layer (trail lines are not in the copy)', miss == {'sgxxa': 1, 'sgxxc': 2})
check('master step: a short copy alone no longer lists every layer', 'this layer may hold the missing records' not in fill_src and 'joined_missing' in fill_src)

# ---- (2) seed checks the copies by layer id and source label ---------------------------------------------------------------
C = T / 'copies'; C.mkdir()
gz(C / 'US-XX.json.gz', {'recs': [{'OBJECTID': 'sgxxa1'}, {'OBJECTID': 'fws9'}]})
gz(C / 'US-YY.json.gz', {'recs': [{'OBJECTID': 'fws10'}]})
gz(C / 'CA-ALL.json.gz', {'recs': [{'oid': 'BC BC Parks :1', 'src': 'BC BC Parks EcoRes'}, {'oid': 'BC BC Parks :2', 'src': 'BC BC Parks EcoRes'}, {'oid': 123}]})
gz(C / 'W-GB.json.gz', {'recs': [{'src': 'Natural England LNR'}] * 3 + [{'src': 'FE_RecAreas_170226'}]})
check('saved_counts: US by prefix, CA by layer id and label, world by label',
      M.saved_counts(C / 'US-XX.json.gz') == {'sgxxa': 1, 'fws': 1} and M.saved_counts(C / 'CA-ALL.json.gz')['BC BC Parks '] == 2 and M.saved_counts(C / 'W-GB.json.gz')['src:Natural England LNR'] == 3)
rows = [{'row_id': '1', 'area': 'US-XX', 'layer_id': 'other;sgxxa', 'layer_name': 'a', 'current_source_url': AG, 'host_rule': 'saved-only', 'official_download_page_url': 'https://x.gov/p', 'direct_file_url': ''},
        {'row_id': '2', 'area': 'US', 'layer_id': '', 'layer_name': 'FWS', 'current_source_url': 'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0',
         'host_rule': 'saved-only', 'official_download_page_url': 'https://x.gov/p', 'direct_file_url': ''},
        {'row_id': '3', 'area': 'CA-BC', 'layer_id': 'ca:BC BC Parks ;x', 'layer_name': 'British Columbia Parks', 'current_source_url': AG, 'host_rule': 'saved-only', 'official_download_page_url': 'https://x.gov/p', 'direct_file_url': ''},
        {'row_id': '4', 'area': 'GB', 'layer_id': '', 'layer_name': 'Local Nature Reserves England', 'current_source_url': AG, 'host_rule': 'saved-only', 'official_download_page_url': 'https://x.gov/p', 'direct_file_url': ''},
        {'row_id': '5', 'area': 'GB', 'layer_id': '', 'layer_name': 'FE_RecAreas_170226', 'current_source_url': AG, 'host_rule': 'saved-only', 'official_download_page_url': 'https://x.gov/p', 'direct_file_url': ''},
        {'row_id': '6', 'area': 'PF', 'layer_id': '', 'layer_name': 'Te Fenua', 'current_source_url': AG, 'host_rule': 'saved-only', 'official_download_page_url': 'https://x.gov/p', 'direct_file_url': ''},
        {'row_id': '7', 'area': 'VI', 'layer_id': '', 'layer_name': 'FWS realty', 'current_source_url': AG, 'host_rule': 'saved-only', 'official_download_page_url': 'https://x.gov/p', 'direct_file_url': 'https://iris.fws.gov/f.zip'}]
with open(T / 'list.csv', 'w', newline='', encoding='utf-8') as fh:
    w_ = csv.DictWriter(fh, fieldnames=list(rows[0])); w_.writeheader(); w_.writerows(rows)
_, nd = W.seed(T / 'list.csv', T / 'src.json', copies=C, same_as={'W-GB': {'Local Nature Reserves England': 'Natural England LNR'}})
st = {r['id']: (r['who'], r['status'], r['have']) for r in nd}
check('seed: a US row is done when any layer id is in the copy', st['US-XX|other'][1] == 'done' and st['US-XX|other'][2] == 1)
check('seed: a national row with no layer id finds the key\'s own prefix (fws) across the copies', st['US|h002'][1] == 'done' and st['US|h002'][2] == 2)
check('seed: a Canada row matches CA-ALL by its layer id, trailing spaces and all', st['CA-BC|h003'][1] == 'done' and st['CA-BC|h003'][2] == 2)
check('seed: a world row matches W-XX by source label, or by the box-side equivalent label', st['W-GB|h004'][1] == 'done' and st['W-GB|h005'][1] == 'done')
check('seed: a layer in no copy stays a person\'s open row', st['W-PF|h006'][:2] == ('person', 'open'))
check('seed: an official direct file a bot may fetch makes it a bot\'s open row', st['W-VI|h007'][:2] == ('bot', 'open'))
check('seed: no licence flags in the public sources file', 'license' not in (T / 'src.json').read_text().lower())

# ---- (3) import-existing -------------------------------------------------------------------------------------------------------
check('real_path: /vsizip/ paths point at the zip on disk', str(I.real_path('/vsizip//a/b.zip/inner.gdb')) == '/a/b.zip')
D = T / 'dl'; D.mkdir(); (D / 'query (5).json').write_text(json.dumps({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {}, 'geometry': None}] * 2}))
(D / 'INDEX.md').write_text('| File | Layer |\n|---|---|\n| `query (5).json` | Nevada Department of Wildlife wildlife management areas |\n| `query (9).json` | missing file |\n')
fs = I.md_table_files(D / 'INDEX.md', D)
check('downloads table: only files that exist, with their row text', [p.name for p, _ in fs] == ['query (5).json'])
check('count_features reads a GeoJSON count', I.count_features(D / 'query (5).json') == 2)
inv = {'by_url': {I.norm_url(AG): [D / 'query (5).json']}, 'files': fs + [(D / 'x', 'protected areas of somewhere')]}
srcs = {'sources': {'h1': {'name': 'Protected Areas'}, 'h2': {'name': 'Nevada Department of Wildlife wildlife management areas'}}}
m = I.match_rows([{'id': 'A', 'url': AG}, {'id': 'B', 'url': 'u', 'src': 'h1'}, {'id': 'C', 'url': 'u', 'src': 'h2'},
                  {'id': 'D', 'url': AG, 'who': 'bot', 'note': 'direct file: https://iris.fws.gov/f'}], inv, srcs)
check('match: by layer address; by a FULL source name; a generic name never; a bot row with an official file is left to the bot',
      set(m) == {'A', 'C'})
fa = I.facts(D / 'query (5).json', 'https://x.gov/p')
check('raw facts: name, size, sha256, date, source, count; no terms', set(fa) == {'name', 'size', 'sha256', 'source', 'date', 'count'} and fa['count'] == 2)
R = T / 'root'; R.mkdir(); M.raw_add_facts(dict(fa, license='x'), root=R)
check('raw_add_facts keeps facts only', 'license' not in M.raw_manifest_path(R).read_text())
doc = I.build_needs([M.needs_row('US-NV', 'nvx', AG, 'w', 'hand-filled list (Nov 10)', who='person')], [], {'US-NV|nvx': [D / 'query (5).json']}, {str(D / 'query (5).json'): fa})
r0 = doc['rows'][0]
check('import-existing: a covered row is done (source existing download) and names the file', r0['status'] == 'done' and r0['source'] == 'existing download' and 'query (5).json (2 records)' in r0['note'])
cli = (ROOT / '.github/scripts/kpc_master_cli.py').read_text(encoding='utf-8')
check('CLI: import-existing is a subcommand', "sp.add_parser('import-existing'" in cli)

# ---- Canada hand files ----------------------------------------------------------------------------------------------------------
ca = (ROOT / '.github/scripts/kpc_ca_key.py').read_text(encoding='utf-8')
check('Canada key reads checked hand files (KPC_CA_HAND), fail closed and keep-bigger', "os.environ.get('KPC_CA_HAND')" in ca and 'SHORT, not used (fail closed)' in ca and 'the saved ones are kept' in ca)
cawf = (ROOT / '.github/workflows/kpc-ca-key.yml').read_text(encoding='utf-8')
check('Canada workflow downloads hand-CA files from the boundary-cache release', "-p 'hand-CA.*.geojson.gz' -D cache/ca-hand --clobber ||" in cawf and 'KPC_CA_HAND: cache/ca-hand' in cawf)
_hl = [l for l in cawf.splitlines() if 'hand-CA' in l and ('gh release' in l or '::warning' in l)]
check('Canada workflow: a failed hand-file listing or download is a ::warning:: naming hand-CA.*.geojson.gz, never hidden (no 2>/dev/null, no bare echo)',
      len([l for l in _hl if 'gh release' in l]) == 2 and all('2>/dev/null' not in l for l in _hl) and sum('::warning title=download hand-CA.*.geojson.gz::' in l for l in _hl) == 2
      and '::notice title=hand-CA.*.geojson.gz::no Canada hand files waiting' in cawf and 'no Canada hand files waiting"' not in cawf.replace('waiting on boundary-cache"', ''))
ns = {}; exec(ca[ca.index('def _hand_rings(g):'):ca.index('CA_HAND = os.environ')], ns)
check('hand rings: Polygon and MultiPolygon to rings; points give none',
      len(ns['_hand_rings']({'type': 'MultiPolygon', 'coordinates': [[[[0, 0], [1, 0], [1, 1], [0, 0]]], [[[2, 2], [3, 2], [3, 3], [2, 2]]]]})) == 2 and ns['_hand_rings']({'type': 'Point', 'coordinates': [0, 0]}) == [])

# ---- NV / WY table entries ------------------------------------------------------------------------------------------------------
sg = json.loads((ROOT / 'data/state-gis.json').read_text(encoding='utf-8'))['states']
nv = [x for x in sg['NV'] if 'NDOWWMAs' in x.get('url', '')]
pts = [x for x in sg['NV'] + sg['WY'] if x.get('geom') == 'point']
check('state-gis: the NV NDOW WMA polygon layer has an entry with its name field', len(nv) == 1 and nv[0]['nm'] == 'WMA_NAME')
check('state-gis: the NV / WY point layers are listed without nm (the outline key skips them)', len(pts) == 3 and all('nm' not in x and x.get('pnm') for x in pts))

# ---- (5) the helper tally -------------------------------------------------------------------------------------------------------
nd2 = {'rows': [{'id': 'US-AZ|sgaza', 'area': 'US-AZ', 'layer': 'sgaza', 'who': 'person', 'status': 'open', 'url': AG, 'host': 'services.arcgis.com'},
                {'id': 'US-NV|nvx', 'area': 'US-NV', 'layer': 'nvx', 'who': 'person', 'status': 'open', 'url': AG, 'host': 'services.arcgis.com'},
                {'id': 'W-PF|h210', 'area': 'W-PF', 'layer': 'h210', 'who': 'person', 'status': 'open', 'url': AG, 'host': 'services.arcgis.com'},
                {'id': 'US-NC|sgnca', 'area': 'US-NC', 'layer': 'sgnca', 'who': 'never', 'status': 'open', 'url': 'https://ncnhde.natureserve.org/x', 'host': 'ncnhde.natureserve.org'},
                {'id': 'US-AZ|sgazb', 'area': 'US-AZ', 'layer': 'sgazb', 'who': 'person', 'status': 'done', 'url': AG, 'host': 'services.arcgis.com'}]}
LT = {'sgaza': ['u', 'NAME', 'label']}
check('helper: only rows it can use (a US layer the key has an entry for)', [r['id'] for r in H.rows_for_person(nd2, layers_table=LT)] == ['US-AZ|sgaza'])
(T / 'nd.json').write_text(json.dumps(nd2))
_f = H.fetch; H.fetch = lambda url, dest=None: json.dumps(LT)
buf = io.StringIO()
with contextlib.redirect_stdout(buf): H.main(['--list', '--needs', str(T / 'nd.json'), '--out', str(T / 'h')])
H.fetch = _f
out = buf.getvalue()
check('helper tally: the count is the rows it can use; the rest are named once as not asked here',
      out.startswith('1 layer(s) to download by hand, 1 download(s).') and '2 open row(s) this helper cannot use' in out and '1 never-contact row(s)' in out)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
