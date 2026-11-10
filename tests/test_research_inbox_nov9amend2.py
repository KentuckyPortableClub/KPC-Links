#!/usr/bin/env python3
"""Nov 9 amendment 2 (Brandon t943u research-input format, t942u retry loop, t939u saved copies): the research inbox reads the format,
runs the sure test on just the file's parks with no network (a fake reader), sends unsettled parks to needs-another-look, and the
converter maps Brandon's xlsx columns. The US/CA/world key readers never read the saved-copy-only hosts live."""
import csv, json, pathlib, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_research_inbox as RI  # noqa: E402
ok = True
def check(c, m):
    global ok; print(('ok   ' if c else 'FAIL ') + m); ok &= bool(c)
check(RI.selftest() == 0, 'name / kind / pin helpers (selftest)')
sq = lambda x, y, d: [[[x - d, y - d], [x + d, y - d], [x + d, y + d], [x - d, y + d], [x - d, y - d]]]
class Fake:
    def near(self, url, lat, lon):
        if 'blocked' in url: return None, 'host.example: robots.txt answers 401/403 (= disallow)'
        return {'7': {'a': {'NAME': 'New Echtoa Historic Site'}, 'r': sq(lon, lat, .01), 'poly': True},
                '8': {'a': {'NAME': 'Echota Ramsar Site', 'DESIG_ENG': 'Ramsar Site'}, 'r': sq(lon, lat, .02), 'poly': True},
                '9': {'a': {'NAME': 'Other Park'}, 'r': [[[lon, lat]]], 'poly': False}}, 'saved copy'
row = {'pota_ref': 'US-1', 'park_name': 'New Echota State Historic Site', 'layer_url': 'https://x/arcgis/rest/services/a/MapServer/0', 'record_id': '7'}
r = RI.judge(row, (34.5, -84.9), {}, None, Fake()); check(r['status'] == 'SURE' and r['record_id'] == '7', f'typo name + pin inside = SURE ({r["reason"][:60]})')
r = RI.judge(dict(row, park_name='Echota Wetland'), (34.5, -84.9), {}, None, Fake()); check(r['status'] != 'SURE', f'overlay / no fit is not SURE ({r["status"]})')
r = RI.judge(row, (34.5, -84.9), {'none': True}, None, Fake()); check(r['status'] == 'NEEDS PERSON', 'a person\'s none: true wins')
r = RI.judge(row, (34.5, -84.9), {'no': ['7']}, None, Fake()); check(r['status'] == 'REJECTED', 'a person\'s no wins')
r = RI.judge(row, (34.5, -84.9), {'_blocked': ['7']}, None, Fake()); check(r['status'] == 'REJECTED', 'blocked_ids wins')
r = RI.judge(row, (34.5, -84.9), {}, 'sggab44', Fake()); check(r['status'] == 'REJECTED' and 'saved ID' in r['reason'], 'a saved id: nothing to add')
r = RI.judge(dict(row, layer_url='https://blocked/x/MapServer/0'), (34.5, -84.9), {}, None, Fake()); check(r['status'] == 'NEEDS PERSON' and r.get('retry') == 'hand-download', 'unreadable layer -> hand download, retry list')
r = RI.judge(row, (34.6, -84.9), {}, None, Fake()); check(r['status'] == 'SURE', 'pin inside the outline (moved box) still sure')
class FakePt:
    def near(self, url, lat, lon): return {'5': {'a': {'NAME': 'Fort Example State Historic Site'}, 'r': [], 'poly': False, 'pt': [lon + .001, lat]}}, 'saved copy'
r = RI.judge(dict(row, park_name='Fort Example State Historic Site'), (34.5, -84.9), {}, None, FakePt())
check(r['status'] == 'POINT-CONFIRMED' and r['record_id'] == '5', f'a matching point = POINT-CONFIRMED, not an outline (Brandon t949u): {r["status"]}')
r = RI.judge(dict(row, park_name='Other Place'), (34.5, -84.9), {}, None, FakePt()); check(r['status'] == 'REJECTED', 'a point with another name is not confirmation')
rd = RI.Reader(tempfile.mkdtemp(), offline=True)
check(not rd.allowed('https://services1.arcgis.com/x/arcgis/rest/services/y/FeatureServer/0')[0], 'saved-copy-only host never read live (t939u)')
check(not rd.allowed('https://services.arcgis.com/33TOOklri9xpic7U/arcgis/rest/services/p/FeatureServer/0')[0], 'Grant County NM parcel server never read')
check(not rd.allowed('https://ncnhde.natureserve.org/x')[0], 'ncnhde.natureserve.org never read')
# the converter on a tiny workbook with Brandon's column names
import openpyxl  # noqa: E402
import kpc_research_from_xlsx as CX  # noqa: E402
d = pathlib.Path(tempfile.mkdtemp()); wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'US'
ws.append(['pota_ref', 'park_name', 'FOUND_layer_or_service_url', 'FOUND_record_id', 'owner_agency', 'confidence(high/med/low)', 'notes', 'pota_pin_lat', 'pota_pin_lon'])
ws.append(['US-1', 'New Echota State Historic Site', 'https://x/arcgis/rest/services/a/FeatureServer/0/query', '7', 'GA DNR', 'HIGH', 'typo', 34.5, -84.9])
w2 = wb.create_sheet('World'); w2.append(['pota_ref', 'park_name', 'FOUND_record_id', 'FOUND_source_name', 'FOUND_source_url_or_layer', 'confidence(high/med/low)'])
w2.append(['AE-0015', 'Dubai Desert Conservation Reserve', '365025', 'UNEP-WCMC WDPA (WDPA_poly_latest)', 'https://data-gis.unep-wcmc.org/server/rest/services/ProtectedSites/The_World_Database_of_Protected_Areas/FeatureServer', 'high'])
wb.save(d / 'b.xlsx'); rows = CX.convert(d / 'b.xlsx', d / 'o.csv', source='test')
got = list(csv.DictReader(open(d / 'o.csv', encoding='utf-8')))
check(got[0]['layer_url'].endswith('/FeatureServer/0') and got[0]['record_id'] == '7' and got[0]['owner'] == 'GA DNR' and got[0]['confidence'] == 'high', 'US columns mapped (query suffix dropped, confidence lower case)')
check(got[1]['layer_url'].endswith('/FeatureServer/1'), 'WDPA service -> its polygon layer 1')
check(list(got[0].keys()) == RI.COLS, 'the CSV has exactly the documented columns')
fmt = (HERE / 'docs/research-input-format.md').read_text(encoding='utf-8')
check(all(c in fmt for c in RI.COLS), 'every column is documented in docs/research-input-format.md')
for f in ('kpc_us_key.py', 'kpc_ca_key.py', 'kpc_world_key.py'):
    s = (HERE / '.github/scripts' / f).read_text(encoding='utf-8')
    check('SAVED_ONLY_HOSTS' in s and "services.arcgis.com,services1.arcgis.com,apps.fs.usda.gov" in s and 't939u' in s, f'{f}: saved-copy-only hosts (Brandon t939u)')
fz = (HERE / '.github/scripts/kpc_key_freeze.py').read_text(encoding='utf-8')
check("'kpc_research_inbox.py'" in fz and "'kpc_research_from_xlsx.py'" in fz, 'the inbox scripts are not rules files (recommend only)')
wf = (HERE / '.github/workflows/kpc-research-inbox.yml').read_text(encoding='utf-8')
import yaml  # noqa: E402
_on = yaml.safe_load(wf).get(True) or yaml.safe_load(wf).get('on') or {}
check('schedule' not in _on, 'the inbox workflow has no cron (a new cron needs Brandon\'s words)')
print('ALL PASS' if ok else 'FAILED'); sys.exit(0 if ok else 1)
