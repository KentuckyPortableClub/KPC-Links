"""Owner-accepted wiring (KPC owner, 2026-11-11; OWNER-ANSWERS-nov11.md item 4, owner chat 2026-11-11 21:16 CT):
keep the NPS admin boundary layer (sgakd, saved copy only) wired for CA and TX in data/state-gis.json, and add
Cesar E. Chavez (CECH, US-0915). The existing overrides for US-0754 (sgakd1159, RORI), US-0915 (sgakd1220, CECH) and US-11900
(sgakd1245, BLSC) can take effect once the owner's checked hand files are merged into the saved copies. Offline: sockets are
refused here and in the build it runs.

  1. CA lists the NPS LRD layer once for RORI and CECH, TX lists it once for BLSC, and the layer keeps its prefix (sgakd);
  2. the master step's own check (kpc_master_fill.new_layer_states) now asks for the CA / TX layer (a person's hand file), and
     stops asking once a saved copy holds it;
  3. an offline single-state build (kpc_us_key.py, GEO_CACHE_MODE=only, in a temp copy; needs KPC-Data for the park files and the
     NPS hand copy): with the wired units in the saved copies, US-0754, US-0915 and US-11900 grade official through their existing
     overrides;
  4. no rules hash moved (data/state-gis.json is not a rule file).
KPC-Data: KPC_DATA=<dir>, else ../kpc-data or ../kpcdata. Without it check 3 prints SKIP."""
import gzip, json, os, pathlib, re, shutil, socket, subprocess, sys, tempfile

def _no_net(*a, **k): raise RuntimeError('network refused in this test')
socket.socket.connect = _no_net; socket.create_connection = _no_net; socket.getaddrinfo = _no_net

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)
def load(p): return json.load(open(p, encoding='utf-8'))
DATA = next((pathlib.Path(d) for d in (os.environ.get('KPC_DATA'), ROOT.parent / 'kpc-data', ROOT.parent / 'kpcdata') if d and (pathlib.Path(d) / 'data').is_dir()), None)
NPS = 'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2'
WIRE = {'CA': [('RORI', 'US-0754', 'sgakd1159'), ('CECH', 'US-0915', 'sgakd1220')], 'TX': [('BLSC', 'US-11900', 'sgakd1245')]}

# 1.
sg = load(ROOT / 'data/state-gis.json')['states']
codes = {}
for st, units in WIRE.items():
    want = {u[0] for u in units}
    rows = [x for x in sg.get(st, []) if x.get('url') == NPS]
    codes[st] = set(re.findall(r"'([A-Z]{4})'", rows[0].get('where', ''))) if len(rows) == 1 else set()
    check(len(rows) == 1 and rows[0]['nm'] == 'UNIT_NAME' and codes[st] == want, f'{st}: the NPS LRD layer is listed once, for {"+".join(sorted(want))}')
check(sorted(s for s, ls in sg.items() if any(x.get('url') == NPS for x in ls)) == ['AK', 'CA', 'CO', 'HI', 'MA', 'NE', 'NY', 'OH', 'PA', 'RI', 'SD', 'TX'], 'the other ten states are unchanged')
lj = load(ROOT / 'data/us-key/layers.json')
check(lj['sgakd'][0].split('/query')[0] == NPS, 'layers.json gives that layer the prefix sgakd (the key keys prefixes by address), so the ids stay sgakd1159 / sgakd1245')
ov = load(ROOT / 'data/us-key/overrides.json')['parks']
check(all(ov[ref]['join'] == [rid] for units in WIRE.values() for _, ref, rid in units), 'the existing overrides still join the wired ids')
check(all(str(ov[ref].get('decided_by') or '').strip() for ref in ('US-0754', 'US-11900')), 'the Nov 9 overrides for US-0754 and US-11900 stay signed')

# 2. the master step asks for the hand files
import kpc_master as M, kpc_master_fill as F
T = pathlib.Path(tempfile.mkdtemp(prefix='kpc-sgakd-'))
try:
    cache = T / 'cache'; cache.mkdir()
    def copy_(st, recs):
        with gzip.open(cache / f'US-{st}.json.gz', 'wt', encoding='utf-8') as fh: json.dump({'st': st, 'saved': '2026-11-11', 'recs': recs}, fh)
    for st in WIRE: copy_(st, [{'OBJECTID': 12345, 'Unit_Nm': 'x'}])
    new = F.new_layer_states(cache, list(WIRE), ROOT / 'data/us-key/layers.json', ROOT / 'data/state-gis.json')
    check(all(NPS.lower() in [u.lower() for u in new.get(st, [])] for st in WIRE), 'the master step now lists the CA and TX NPS layer as missing from their saved copies')
    check(not M.live_ok(NPS)[0], 'and that host stays saved-copy only (a person\'s hand file, never a live read)')
    copy_('CA', [{'OBJECTID': 'sgakd1159', 'Unit_Nm': 'x'}])
    new = F.new_layer_states(cache, ['CA'], ROOT / 'data/us-key/layers.json', ROOT / 'data/state-gis.json')
    check(NPS.lower() not in [u.lower() for u in new.get('CA', [])], 'once the CA saved copy holds sgakd, it is no longer asked for')

    # 3. offline single-state build in a temp copy
    if DATA is None: print('SKIP offline CA / TX build: no KPC-Data checkout')
    else:
        S = T / 'repo'
        shutil.copytree(ROOT / '.github/scripts', S / '.github/scripts')
        (S / 'tests').mkdir(parents=True)
        for f in ('run_match_tests.py', 'match_cases.json'): shutil.copy(ROOT / 'tests' / f, S / 'tests' / f)
        for f in ('locations.json', 'kpc-us-states.json', 'data/state-gis.json', 'data/retired-refs.json', 'data/nps-units.json', 'data/park-transfers.json', 'data/acres.json'):
            if (ROOT / f).exists(): (S / f).parent.mkdir(parents=True, exist_ok=True); shutil.copy(ROOT / f, S / f)
        k = S / 'data/us-key'; (k / 'tracts').mkdir(parents=True)
        for f in ('overrides.json', 'layers.json', 'index.json', 'US-CA.json', 'US-TX.json', 'tracts/US-CA.json', 'tracts/US-TX.json'):
            if (ROOT / 'data/us-key' / f).exists(): shutil.copy(ROOT / 'data/us-key' / f, k / f)
        (S / 'data/parkinfo').mkdir(parents=True)
        for f in ('US-CA.json', 'US-TX.json', 'index.json'): shutil.copy(DATA / 'data/parkinfo' / f, S / 'data/parkinfo' / f)
        hand = load(DATA / 'data/waiting/outline-sources/hand-layers/us-nps-admin-boundaries-nov9.geojson')['features']
        fx = T / 'fixture'; fx.mkdir()
        for st in WIRE:   # the saved copy after the master step merged this state's hand file: only the wired units
            recs = []
            for f in hand:
                p = f['properties']
                if p['state'][:2] != st or p['unit_code'] not in codes[st]: continue
                g = f['geometry']; polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
                recs.append({'OBJECTID': p['live_record_id'], 'Unit_Nm': p['unit_name'], 'Loc_Nm': '', 'Own_Type': 'STAT', 'Mang_Type': 'STAT', 'Mang_Name': 'SGAKD',
                             'Loc_Mang': 'National Park Service (legal boundary) (park, state GIS table)', 'Des_Tp': '', 'GIS_Acres': p['acres'], 'Category': 'Fee',
                             '_r': [[[round(x, 5), round(y, 5)] for x, y, *_ in ring] for poly in polys for ring in poly], '_k': ['sp'], 'rd': '2026-11-09'})
            with gzip.open(fx / f'US-{st}.json.gz', 'wt', encoding='utf-8') as fh: json.dump({'st': st, 'saved': '2026-11-11', 'detail': 0.01, 'seen': len(recs), 'recs': recs}, fh)
        run = T / 'offline_run.py'
        run.write_text("import os, runpy, socket, sys\n"
                       "def _no(*a, **k):\n    print('NETWORK REFUSED', a[:2], flush=True); raise RuntimeError('network refused')\n"
                       "socket.socket.connect = _no; socket.create_connection = _no; socket.getaddrinfo = _no\n"
                       "os.chdir(sys.argv[1]); sys.path.insert(0, os.path.join(sys.argv[1], '.github/scripts'))\n"
                       "sys.argv = ['kpc_us_key.py']; runpy.run_path('.github/scripts/kpc_us_key.py', run_name='__main__')\n", encoding='utf-8')
        env = {k_: v for k_, v in os.environ.items() if not k_.startswith(('GITHUB_', 'KPC_'))}
        env.update({'STATES': 'CA TX', 'GEO_CACHE_MODE': 'only', 'GEO_CACHE': str(fx), 'HTTPS_PROXY': 'http://127.0.0.1:9', 'HTTP_PROXY': 'http://127.0.0.1:9',
                    'https_proxy': 'http://127.0.0.1:9', 'http_proxy': 'http://127.0.0.1:9'})
        r = subprocess.run([sys.executable, str(run), str(S)], env=env, capture_output=True, text=True, timeout=900)
        out = r.stdout + r.stderr
        check(r.returncode == 0 and 'NETWORK REFUSED' not in out, f'the offline build ran with no network attempt (exit {r.returncode})')
        for st, units in WIRE.items():
            for code, ref, rid in units:
                p = load(k / f'US-{st}.json')['parks'][ref]
                check(p.get('g') == 'official' and [x[0] for x in p.get('m') or []] == [rid] and p['m'][0][3] == 'reviewed' and (p.get('bk') or [None, 9])[1] <= 0.5,
                      f'{ref}: official through its existing override ({rid}, {p.get("bk", [None, None])[1]} km)')
finally:
    shutil.rmtree(T, ignore_errors=True)

# 4.
import kpc_key_freeze as KF
check((KF.rules_hash('us-key'), KF.rules_hash('ca-key'), KF.rules_hash('world-key'), KF.rules_hash('fers')) == ('46ef34a04ab0', '4b4176190334', '9358c2ede2d5', 'cef323de4c9a'),
      'US / CA / world / fers rules hashes unchanged (data/state-gis.json is not a rule file)')
print(f'{"ALL PASS" if not bad else str(bad) + " FAILED"}')
sys.exit(1 if bad else 0)
