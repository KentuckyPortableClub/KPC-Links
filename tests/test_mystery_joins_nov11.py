"""Job 2, Nov 11 2026 (KPC owner, 2026-11-11): the 17 strong Nov 11 mystery matches and the 3 old pins, as recorded in
docs/mystery-joins-nov11-staged.json. Offline: every socket is refused before anything runs (zero network).

Checks:
  1. the file names exactly the 20 parks, each with a known status and a reason;
  2. no pin moved: every pin in the file equals POTA's pin in locations.json (and in KPC-Data's park files when present);
  3. nothing staged is in a live key: the staged ids / names are absent from data/us-key/overrides.json and
     data/world-key/overrides.json, and the held parks (US-11820, US-12735) stay on needs-another-look.json;
  4. joined-live parks: the live world key joins exactly the record named here, and the saved outline (KPC-Data world-bounds
     shard, or the saved record box) gives the documented pin distance;
  5. US-0754 / US-11900: the live overrides join the ids named here, KPC-Data's NPS admin boundary hand copy holds those records
     (name + acres within 10%), and the pin is within 0.5 km of the saved outline;
  6. US-10184 / US-10195: the records the staged entries name are in the saved copy's record list of the live key, with the pin inside;
  7. the four rules hashes did not move.
KPC-Data: KPC_DATA=<dir>, else ../kpc-data or ../kpcdata next to this checkout. Without it the KPC-Data checks print SKIP."""
import json, math, os, pathlib, socket, sys

def _no_net(*a, **k): raise RuntimeError('network refused in this test')
socket.socket.connect = _no_net; socket.create_connection = _no_net; socket.getaddrinfo = _no_net

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)
def skip(msg): print('SKIP ' + msg)

def load(p): return json.load(open(p, encoding='utf-8'))
DATA = next((pathlib.Path(d) for d in (os.environ.get('KPC_DATA'), ROOT.parent / 'kpc-data', ROOT.parent / 'kpcdata') if d and (pathlib.Path(d) / 'data').is_dir()), None)

# ---- pin test helpers (even-odd over every ring; nearest edge in local km) ----
def in_ring(x, y, r):
    c = False
    for i in range(len(r)):
        x1, y1 = r[i][0], r[i][1]; x2, y2 = r[i - 1][0], r[i - 1][1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-300) + x1: c = not c
    return c
def inside(la, lo, rings): return sum(1 for r in rings if in_ring(lo, la, r)) % 2 == 1
def edge_km(la, lo, rings):
    k = math.cos(math.radians(la)); px, py = lo * 111.32 * k, la * 110.574; best = 1e18
    for r in rings:
        pts = [(q[0] * 111.32 * k, q[1] * 110.574) for q in r]
        for i in range(len(pts)):
            (ax, ay), (bx, by) = pts[i - 1], pts[i]; dx, dy = bx - ax, by - ay
            t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
            best = min(best, math.hypot(px - ax - t * dx, py - ay - t * dy))
    return best
def box_km(la, lo, b):
    k = math.cos(math.radians(la))
    return math.hypot(max(b[0] - lo, 0, lo - b[2]) * 111.32 * k, max(b[1] - la, 0, la - b[3]) * 110.574)
def gj_rings(g): return [ring for poly in ([g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']) for ring in poly]

doc = load(ROOT / 'docs/mystery-joins-nov11-staged.json')
P = doc['parks']
WANT = {'US-10184', 'US-10195', 'US-7374', 'FR-10548', 'FR-10432', 'FR-11106', 'FR-11650', 'FR-12366', 'FR-13422', 'FR-14049', 'FR-14482', 'FR-14979', 'RO-0880',
        'US-13474', 'US-11820', 'US-12735', 'US-10274', 'US-4376', 'US-0754', 'US-11900'}
# 1.
check(set(P) == WANT and len(P) == 20, 'the file names exactly the 20 parks')
check(all(p['status'] in ('joined-live', 'wiring-proposal', 'staged', 'held', 'not-joined', 'owner-yes', 'owner-no-applied', 'applied') and len(p.get('reason') or '') > 20 for p in P.values()), 'each has a known status and a reason')
check(P['US-11820']['status'] == 'held' and P['US-12735']['status'] == 'held' and P['US-13474']['status'] == 'held', 'US-11820, US-12735 and US-13474 stay held')
check(P['US-10274']['status'] == 'not-joined', 'Palmito (the battlefield is the bigger place) is not joined')
check(all(P[r]['status'] == 'owner-yes' and P[r]['owner_decision'] == 'yes' for r in ('US-10184', 'US-10195', 'US-7374')), 'US-10184, US-10195 and US-7374 are owner YES')
check(P['FR-14979']['status'] == 'owner-no-applied' and P['FR-14979']['owner_decision'] == 'no', 'FR-14979 owner no is applied')
check('overrides.json' in (P['US-10184'].get('reason') or '') and 'split' in (P['US-10184'].get('reason') or '').lower(), 'the YES aliases wait for the overrides-split PR; nothing is written to us-key/overrides.json here')
check(all(n['host'] and n['feature'] and n['refs'] and n['saved_copy_checked'] for p in P.values() for n in p.get('needs') or []), 'every hand-download item names host, feature, park and the saved copies checked')
check(all('arcgis.com' not in str(n['host']) for p in P.values() for n in p.get('needs') or []), 'no hand-download item asks for a live services*.arcgis.com read')

# 2. no pin moved
loc = {r[1]: (r[3], r[4]) for r in load(ROOT / 'locations.json') if isinstance(r, list) and len(r) > 4 and r[0] == 'POTA'}
us = [r for r in P if r.startswith('US-')]
check(all(tuple(P[r]['pin']) == tuple(loc[r]) for r in us), 'US pins equal POTA\'s pins in locations.json (none moved)')
if DATA:
    pk = {}
    for f in (DATA / 'data/parkinfo').glob('*.json'):
        if f.name == 'index.json': continue
        try: pk.update({r: v for r, v in (load(f).get('parks') or {}).items() if r in WANT})
        except Exception: pass  # noqa: BLE001
    check(all(r in pk and [pk[r][5], pk[r][6]] == P[r]['pin'] for r in WANT), 'all 20 pins equal KPC-Data\'s park files (none moved)')
else: skip('KPC-Data park files: no KPC-Data checkout')

# 3. nothing staged is live
sys.path.insert(0, str(ROOT / '.github/scripts')); import kpc_overrides as _KOVR  # Nov 12 (KPC-Links #151): manifest + parts
uo = _KOVR.load(ROOT / 'data/us-key/overrides.json')['parks']; wo = load(ROOT / 'data/world-key/overrides.json')['parks']
for r, p in P.items():
    st = ((p.get('entry') or {}).get('staged') or {})
    if p['status'] not in ('staged', 'held', 'not-joined', 'owner-yes'): continue
    if not st and p['status'] != 'owner-yes': continue
    live = (uo if r.startswith('US-') else wo).get(r) or {}
    names = set(st.get('alias_held') or []) | set((st.get('join_held') or {}).get('ids') or []) | {x[1] for x in st.get('ids') or []} | set(st.get('no') or [])
    used = set(map(str, live.get('join') or [])) | set(live.get('alias') or []) | set(live.get('alias_ok_names') or []) | set(map(str, live.get('no') or [])) | {str(x[1]) for x in live.get('ids') or []}
    check(not (names & used), f'{r}: the staged entry is not in the live overrides')
nal = load(ROOT / 'data/research-inbox/needs-another-look.json')['parks']
check(all(nal.get(r, {}).get('wait_on') == 'person' for r in ('US-11820', 'US-12735')), 'US-11820 / US-12735 still wait on a person (hold not lifted)')
check(((P['FR-14979'].get('entry') or {}).get('live') or {}).get('no') == ['znieff2.828'] and (wo.get('FR-14979') or {}).get('no') == ['znieff2.828'],
      'FR-14979: the staged no is now live in data/world-key/overrides.json')
check(any(str(x[0]) == 'znieff2.828' for x in load(ROOT / 'data/world-key/FR.json')['parks']['FR-14979'].get('m') or []),
      'FR-14979: the live world key file still joins znieff2.828 until the next world key run')
check(all(r not in uo or 'Deer Park SHA-WPRA' not in ((uo.get(r) or {}).get('alias') or []) for r in ('US-10184',)),
      'the owner-YES aliases are not yet in data/us-key/overrides.json')
# KPC owner, 2026-11-11 (job 6): the three French parks are 'applied': their entry is live in data/world-key/overrides.json and names, by
# source label and record id, a layer kpc_world_key.py now reads; the live key file still shows the old state until the next world key run.
APPLIED = {'FR-10548': ('IGN Géoplateforme ZNIEFF type II sea', 'znieff2_mer.7'), 'FR-10432': ('IGN Géoplateforme Conservatoire du littoral', 'cdl.502'),
           'FR-11106': ('IGN Géoplateforme RNN protection perimeters', 'pprnn.1')}
_wk = (ROOT / '.github/scripts/kpc_world_key.py').read_text(encoding='utf-8')
# Nov 12 (KPC owner, 2026-11-12; D6) CHANGED: France's built-in layers are data now (data/world-key/area-tables.json SRC.FR)
_fr = json.load(open(ROOT / 'data/world-key/area-tables.json', encoding='utf-8'))['SRC']['FR']
check({r for r, p in P.items() if p['status'] == 'applied'} == set(APPLIED), 'job 6: exactly FR-10548, FR-10432 and FR-11106 are applied')
for r, (lab, rid) in APPLIED.items():
    e = (P[r].get('entry') or {}).get('live') or {}
    check(e == wo.get(r) and e.get('ids') == [[lab, rid]] and P[r].get('needs') == [], f'{r}: the applied entry is the live world override (ids {rid}), no hand download left')
check(all(any(s[0] == 'IGN Géoplateforme ' + n and s[1] == 'wfs' and s[3] == t for s in _fr) for n, t in
          (('ZNIEFF type II sea', 'patrinat_znieff2_mer:znieff2_mer'), ('Conservatoire du littoral', 'patrinat_cdl:cdl'), ('RNN protection perimeters', 'patrinat_pprnn:pprnn'))),
      'job 6: kpc_world_key.py reads the three layers those ids name')
check(wo['FR-10548'].get('no') == ['znieff1.16597', 'Corniche Varoise'], 'FR-10548: the land zone of the same name and Corniche Varoise are refused')
check(all(P[r]['until_next_run'] == 'joined-live' for r in ('FR-10432', 'FR-11106')) and P['FR-10548']['until_next_run'] == 'no join (as now)', 'job 6: until_next_run says what the live key shows until the next run')

# 4. joined-live: the live world key joins the record; the saved outline gives the documented distance
for r, p in P.items():
    if not r.startswith(('FR-', 'RO-')) or (p['status'] not in ('joined-live', 'not-joined') and p.get('until_next_run') != 'joined-live'): continue
    k = load(ROOT / p['key'])['parks'][r]
    rid = p['saved_copy']['records'][0][0]
    check(any(str(x[0]) == str(rid) for x in k.get('m') or []), f'{r}: the live world key joins {rid}')
    pr = p['pin_result']; la, lo = p['pin']
    if 'box_km' in pr:
        t = load(ROOT / f'data/world-key/tracts/{r[:2]}.json')['parks'][r]
        b = next(x['box'] for x in t if str(x['rid']) == str(rid))
        d = box_km(la, lo, b)
        check(abs(d - pr['box_km']) < 0.05 and d <= pr['key_bk_km'] + 0.05, f'{r}: pin {d:.2f} km from the saved record box (documented {pr["box_km"]}, key {pr["key_bk_km"]})')
    elif DATA:
        sh = load(DATA / 'data/world-bounds' / r[:2] / f"{int(r.split('-')[1]) // 100}.json")[r]
        d = edge_km(la, lo, sh['r'])
        check(not inside(la, lo, sh['r']) and abs(d - pr['edge_km']) < 0.05 and abs(d - pr['key_bk_km']) < 0.1, f'{r}: saved outline, pin outside by {d:.2f} km (documented {pr["edge_km"]}, key {pr["key_bk_km"]})')
    else: skip(f'{r}: saved world-bounds shard: no KPC-Data checkout')
if DATA:   # FR-10548: the saved land zone of the same name is NOT where the pin is
    p = P['FR-10548']; sh = load(DATA / 'data/world-bounds/FR/105.json')['FR-10548']; d = edge_km(*p['pin'], sh['r'])
    check(sh['n'] == 'CAP DE SAINT-TROPEZ' and 'type I' in sh['s'] and not inside(*p['pin'], sh['r']) and abs(d - p['pin_result']['edge_km']) < 0.05,
          f'FR-10548: the saved land ZNIEFF-1 of the same name is {d:.2f} km from the pin (not the marine zone the pin is in)')
check(not (load(ROOT / 'data/world-key/FR.json')['parks']['FR-10548'].get('m')), 'FR-10548: the live world key joins nothing (Corniche Varoise stays a candidate only)')

# 5. US-0754 / US-11900
for r in ('US-0754', 'US-11900'):
    p = P[r]; rid, nm, ac = p['saved_copy']['records'][0]; ov = uo.get(r) or {}
    check(ov.get('join') == [rid] and str(ov.get('decided_by') or '').strip() and ov['fp'][rid][0] == nm, f'{r}: the live overrides join {rid} ({nm}), signed')
    if DATA:
        hc = load(DATA / 'data/waiting/outline-sources/hand-layers/us-nps-admin-boundaries-nov9.geojson')['features']
        f = [x for x in hc if x['properties'].get('live_record_id') == rid]
        rg = gj_rings(f[0]['geometry']) if f else []
        d = edge_km(*p['pin'], rg) if rg else None
        check(len(f) == 1 and f[0]['properties']['pota_ref'] == r and f[0]['properties']['unit_name'] == nm and abs(f[0]['properties']['acres'] - ov['fp'][rid][1]) <= max(1, .1 * ac),
              f'{r}: KPC-Data NPS hand copy holds {rid} with the saved name and acres')
        check(d is not None and (inside(*p['pin'], rg) or d <= 0.5) and abs(d - p['pin_result']['edge_km']) < 0.002, f'{r}: pin {d:.3f} km from the saved outline (within 0.5 km, documented {p["pin_result"]["edge_km"]})')
    else: skip(f'{r}: KPC-Data NPS hand copy: no KPC-Data checkout')

# 6. WI: the staged names are the saved copy's records, and the key recorded the pin inside them
for r in ('US-10184', 'US-10195'):
    p = P[r]; k = load(ROOT / p['key'])['parks'][r]; a = {str(x[0]): x for x in (k.get('a') or []) + (k.get('c') or [])}
    rec = p['saved_copy']['records']
    check(all(i in a and a[i][1] == n and 'pin is inside' in a[i][3] for i, n, _ in rec), f'{r}: the saved copy\'s records {[x[0] for x in rec]} are in the live key with the pin inside')
    check(set(p['entry']['staged']['alias_held']) <= {n for _, n, _ in rec} and k.get('g') == 'pin', f'{r}: the staged alias is one of those record names; the park is still a pin (nothing applied)')

# 7. hashes
import kpc_key_freeze as KF
# KPC owner, 2026-11-11 (job 6, world rules change approved): the world hash moved 9358c2ede2d5 -> 889d37136cf8 (three French PatriNat layers); US and CA are as before; fers is main's cef323de4c9a (#157)
# Nov 12 (KPC owner, 2026-11-12; D6 tables out) CHANGED: later declared moves (US 46ef34a04ab0 -> d4ebfafce438, world 889d37136cf8 -> a47e0479ad41) are the
# newest; each hash must equal the one its newest changelog line names (no literal to edit when a later change of the set moves it again).
check((KF.rules_hash('us-key'), KF.rules_hash('ca-key'), KF.rules_hash('world-key'), KF.rules_hash('fers')) == tuple(__import__('kpc_preflight').newest_hash(k) for k in ('us-key', 'ca-key', 'world-key', 'fers')),
      'US / CA / world / fers rules hashes unchanged')
print(f'{"ALL PASS" if not bad else str(bad) + " FAILED"}')
sys.exit(1 if bad else 0)
