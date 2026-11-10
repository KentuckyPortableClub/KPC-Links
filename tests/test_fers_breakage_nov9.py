#!/usr/bin/env python3
"""Nov 9 2-fer breakage fixes (Quality grade of run 42594981324; Brandon 9:15-9:22 AM CST). Offline: no network, no run started.
1 a pass-1 time-out never rewrites an unfinished area (source check) and near_pairs only measures tested pairs
2 the BLM layer's agency field is the TEXT field ADMIN_AGENCY_CODE (the old pick SMA_ID = a number -> HTTP 400)
2 a live candidate with no ownership source is held NOT SURE; Canadian owners fall back to the manager / source name
2 KISS ownership (Brandon Nov 9, 9:37 + 9:39 AM CST): owner from the record / agency name, no masks, no live ownership calls"""
import json, os, pathlib, sys, tempfile, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S))
os.environ.setdefault('PASS', '5')
try: import cv2  # noqa: F401
except Exception: sys.modules['cv2'] = types.ModuleType('cv2')  # noqa: BLE001
import kpc_fers as K
import kpc_owned as KO
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


src = open(S / 'kpc_fers.py', encoding='utf-8').read()
check("st in old and (st in undone or st not in by): continue" in src, 'pass 1 out of time: an area with untested pairs keeps its previous file')
check("'incomplete': 'pass 1 stopped for time" in src, 'pass 1 out of time: a new unfinished area is saved marked incomplete')
check("near_pairs(G, {p for p in pairs if p in TESTED}, spots)" in src, 'near_pairs measures only the pairs pass 1 tested')

# BLM field pick (mocked server answers)
calls = []
def fake_get(url, params, tries=3, timeout=120):
    calls.append((url, dict(params)))
    if url == KO.BLMSMA: return {'layers': [{'id': 0, 'name': 'IDENTIFY'}, {'id': 7, 'name': 'Bureau of Land Management (BLM)'}]}
    if url.endswith('/7') and params.get('f') == 'json' and 'where' not in params:
        return {'fields': [{'name': 'OBJECTID', 'type': 'esriFieldTypeOID'}, {'name': 'SMA_ID', 'type': 'esriFieldTypeSmallInteger'},
                           {'name': 'ADMIN_AGENCY_CODE', 'type': 'esriFieldTypeString'}], 'advancedQueryCapabilities': {'supportsPagination': True}}
    return {'features': []}
_g = KO.get; KO.get = fake_get; KO.OWN_T.clear()
try: KO.owned_land('blm', [-117.0, 39.0, -116.9, 39.1], 0.0005, 5)
finally: KO.get = _g
wh = [p.get('where') for u, p in calls if u.endswith('/7/query')]
check(wh and all(w == "ADMIN_AGENCY_CODE = 'BLM'" for w in wh), f"BLM where = ADMIN_AGENCY_CODE (got {wh[:1]})")

# blank owner: official agency outlines count as government / public land; others stay held
rows = [{'kind': 'area', 'status': 'candidate', 'refs': ['CA-0005', 'CA-0040']},                       # Banff x Jasper: official agency outlines
        {'kind': 'area', 'status': 'candidate', 'ownership': 'public land (federal)', 'refs': ['a', 'b']},
        {'kind': 'same land', 'status': 'candidate', 'owner_here': 'owner not published', 'refs': ['c', 'd']},
        {'kind': 'same land', 'status': 'candidate', 'owner_here': 'state land (from the outline both numbers are joined to)', 'refs': ['e', 'f']},
        {'kind': 'area', 'status': 'not sure: x', 'refs': ['g', 'h']},
        {'kind': 'area', 'status': 'candidate', 'refs': ['ZZ-NOKEY-1', 'ZZ-NOKEY-2']}]
n = K.hold_no_owner(rows, root=str(HERE))
check(n == 2 and rows[5]['status'].startswith('not sure: no ownership source') and rows[2]['status'].startswith('not sure'), 'blank owner with no official agency outline is held NOT SURE')
check(rows[0]['status'] == 'candidate' and str(rows[0].get('ownership') or '').startswith('public land'), 'official agency outlines (Banff x Jasper) count as public land, no separate owner source')
check(rows[1]['status'] == 'candidate' and rows[3]['status'] == 'candidate' and rows[4]['status'] == 'not sure: x', 'rows with an ownership source untouched')
# point-circle and approximate pairs become an approximate 2-fer, not a drop
import kpc_fers_key_status as KS
KS.clear(); KS.KEY_STATUS['US-APX-1'] = 'approximate'; KS.KEY_STATUS['US-APX-2'] = 'approximate'
apx = [{'kind': 'area', 'status': 'candidate', 'refs': ['US-APX-1', 'US-APX-2'], 'approx': True, 'tier': 'approximate'}]
n2 = K.hold_no_owner(apx, root=str(HERE))
check(n2 == 0 and apx[0]['status'] == 'candidate', 'approximate pair is not held for a blank owner')
d = K.pc_tag({'spots': [dict(apx[0])]})
check(d['spots'][0]['tier'] == 'approximate' and 'Not the official boundary' in d['spots'][0].get('approx_note',''), 'pc_tag writes the approximate 2-fer note')
# WDPA / Protected Planet is never a public 2-fer source
check(K.is_wdpa_outline({'src': 'WDPA', 'gsrc': 'protectedplanet.net'}), 'WDPA outline is detected')
check(not K.is_wdpa_outline({'src': ['PAD-US'], 'g': 'official'}), 'a PAD-US outline is not treated as WDPA')
KS.clear()

# Canada: no 'ow' text -> manager / source name
check(K.owner_of_text('Parks Canada Agency') == 'FED:CANADA', 'Parks Canada Agency = federal')
check(K.owner_of_text('') == '' and K.owner_of_text('Alberta Parks (Government of Alberta)') == 'STATE', 'provincial source name gives the owner')
check("owner_of_text(r.get('mg')) or owner_of_text(r.get('src') or r.get('ty'))" in src, 'ca_owners falls back to mg / src / ty')

# Nov 9 KISS ownership (Brandon 9:37 / 9:39 AM CST): owner from the record / agency name; no masks, no live ownership calls
check(K.owned_land('blm', [-117, 39, -116.9, 39.1]) is None and K.fs_owned([-84, 37, -83.9, 37.1]) is None, 'no owned-land mask is read')
check('KO.owned_land(' not in src and 'KO.fs_owned(' not in src, 'the 2-fer run makes no live owned-land calls')
_os = src[src.index('def ownership_step'):src.index('OWNWORD = {')]
check(not any(f in _os for f in ('pad_at(', 'cpcad_at(', 'usace_at(')), 'the ownership step makes no live calls')
for n, k in (('Daniel Boone National Forest', 'FED:USFS'), ('Thunder Basin National Grassland', 'FED:USFS'), ('Mammoth Cave National Park', 'FED:NPS'),
             ('Reelfoot National Wildlife Refuge', 'FED:FWS'), ('Red Rock Canyon National Conservation Area', 'FED:BLM'), ('Banff National Park Of Canada', 'FED:CANADA'),
             ('Cumberland Falls State Resort Park', 'STATE'), ('Clay WMA', 'STATE'), ('Kentenia State Forest', 'STATE'), ('Shelby County Park', 'LOCAL')):
    check(K.owner_from_name(n) == k, f'{n} -> {k}')
K.REGION = 'na'
parks = {'A': {'st': 'US-ID', 'ids': [1], 'names': {'1': 'Boise National Forest'}}, 'B': {'st': 'US-ID', 'ids': [2], 'names': {'2': 'Ponderosa State Park'}},
         'C': {'st': 'US-ID', 'ids': [3], 'names': {'3': 'Something Place'}}}
K.OWN.update({'A': (set(), True), 'B': (set(), True), 'C': (set(), False)})
PIN = {'A': ['Boise National Forest'], 'B': ['Ponderosa State Park'], 'C': ['Something Place']}
K.PINS.update(PIN)
s1 = {'refs': ['A', 'B']}; v1 = K.ownership_step(s1, parks, PIN)
check(v1[0] == 'ok' and s1.get('mixed_owners') == ['FED:USFS', 'STATE'], f'national forest x state park = public ground, two owners kept as before ({v1})')
v2 = K.ownership_step({'refs': ['A', 'C']}, parks, PIN)
check(v2[0] == 'not sure' and 'Something Place' in v2[1], f'a truly blank owner with no official outline = NOT SURE ({v2})')
import kpc_fers_key_status as KS
KS.clear(); KS.KEY_STATUS['C'] = 'official'; KS.KEY_STATUS['A'] = 'official'; KS.KEY_BY_AREA['C'] = {'_': 'official'}; KS.KEY_BY_AREA['A'] = {'_': 'official'}
s3 = {'refs': ['A', 'C']}
v3 = K.ownership_step(s3, parks, PIN)
check(v3[0] == 'ok' and 'official agency outline' in (s3.get('owner_src') or ''), f'blank owner on official agency outlines = public land ({v3})')
KS.clear(); KS.load_key_status = lambda root='.': KS.KEY_STATUS  # keep later tests from needing a full reload
# restore normal loader after this file's remaining tests do not need the stub; real load happens if KEY_STATUS empty
KS.clear()
check('no saved owned-land line yet for' not in src, 'no NOT SURE just because a saved owned-land file is missing')

# post-line after a hand-started kpc-fers.yml run (live save vs the save before it)
import kpc_fers_postline as POST
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); (t / 'data/fers').mkdir(parents=True); (t / 'prev/data/fers').mkdir(parents=True)
    sp = lambda st: {'spots': [{'refs': ['US-1', 'US-2'], 'kind': 'area', 'status': st, 'wide_m': 100}]}
    (t / 'data/fers/US-CO.json').write_text(json.dumps(sp('not sure: x'))); (t / 'prev/data/fers/US-CO.json').write_text(json.dumps(sp('candidate')))
    try:
        r = POST.main({'DATA': str(t), 'LINKS': str(HERE), 'PREV_DIR': str(t / 'prev'), 'OUT': str(t / 'out')})
        a = r['areas'].get('US-CO') or {}
        check(r.get('mode', '').startswith('live save') and a.get('live_before') == 1 and a.get('live_now') == 0, 'post-line compares a live save with the save before it')
    except Exception as e: check(False, f'post-line PREV_DIR: {e}')  # noqa: BLE001
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
