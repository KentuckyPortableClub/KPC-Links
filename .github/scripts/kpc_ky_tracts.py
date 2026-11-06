#!/usr/bin/env python3
"""KENTUCKY TRACT RECORDS (Nov 6 2026, big key / 2-fer patch): the same side file the US / Canada / world keys write (kpc_tracts.py),
for the hand-checked KY answer key (data/ky-answer-key.json, tracts[] = [layer, name, acres, how, pieces]). Writes data/tracts/US-KY.json.
The KY answer key itself is not changed.

Each tract gets its source's stable id, official acres and owner through the ONE table (kpc_source_fields.py): KDFWR_ID for Fish &
Wildlife areas, the state park layer's acreage, the nature preserve / natural area owner, NPS UNIT_CODE (data/nps-units.json), ...
The ids come from ONE attribute-only request per Kentucky state layer (no shapes), made through kpc_manners (robots.txt obeyed, 2 s per
host); when kpc_manners is not on the path (KPC_MANNERS_DIR) or a host says no, the tracts are written without those ids.
Measured acres and pieces come from the website's own ky-*.geojson files; parks inside parks from those shapes.
  KPC_TRACT_STORE=0 turns it off.   KY_TRACTS_LIVE=0 = no request at all.
"""
import json, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_tracts as TR
import kpc_source_fields as SF
import kpc_pin_edge as PE

KYGIS = 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'
# KY answer-key layer -> (the website's file, the live layer that holds the source facts, its name field)
KYL = {'bwma': ('ky-hunting-areas.geojson', KYGIS + 'Ky_Public_Hunting_Areas_WGS84WM/MapServer/1', 'AREANAME'),
       'bstate': ('ky-state-parks.geojson', KYGIS + 'Ky_State_Parks_Features_WGS84WM/MapServer/8', 'PUBLIC_NAM'),
       'bsnp': ('ky-nature-preserves.geojson', KYGIS + 'Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0', 'MANAME'),
       'bsna': ('ky-natural-areas.geojson', KYGIS + 'Ky_KNP_Natural_Areas_WGS84WM/MapServer/0', 'MANAME'),
       'bwild': ('ky-wild-rivers.geojson', KYGIS + 'Ky_KNP_Wild_River_Corridors_WGS84WM/MapServer/0', 'MANAME'),
       'bdbnf': ('ky-dbnf.geojson', 'EDW_ForestSystemBoundaries', None), 'bnps': ('ky-nps.geojson', 'NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2', None),
       'bfws': ('ky-fws.geojson', 'FWSInterest', None), 'bwilder': ('ky-wilderness.geojson', 'EDW_Wilderness', None), 'bpad': ('ky-padus-parks.geojson', 'PAD-US/PAD_US/MapServer', None),
       'busace': ('ky-usace.geojson', 'usace_recreation_areas', None)}


def low(x): return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', str(x or '').lower()).split())


def shapes(fn):
    try: fc = json.load(open(fn, encoding='utf-8'))
    except Exception: return {}  # noqa: BLE001
    out = {}
    for f in fc.get('features') or []:
        p = f.get('properties') or {}
        nm = p.get('NAME') or p.get('name') or p.get('ref') or ''
        out.setdefault(low(nm), []).extend(PE.geojson_rings(f.get('geometry')))
    return out


def live_facts(url, nf, mp):
    """{low(name): attrs} from one attribute-only request, via kpc_manners; {} when not allowed / not available."""
    if os.environ.get('KY_TRACTS_LIVE', '1') == '0' or not nf: return {}
    d = os.environ.get('KPC_MANNERS_DIR')
    if d: sys.path.insert(0, d)
    try: import kpc_manners as KM
    except Exception: return {}  # noqa: BLE001
    flds = ','.join(dict.fromkeys([nf] + SF.extra_fields(mp)))
    q = url + '/query?' + urllib.parse.urlencode({'where': '1=1', 'outFields': flds, 'returnGeometry': 'false', 'f': 'json'})
    try:
        st, _h, body, _u = KM.Manners('KPC tract records (read-only)').get(q)
        if st != 200: print(f'::notice title=KY tracts::{url.split("/services/")[-1]}: {st} (ids left out)'); return {}
        j = json.loads(body)
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=KY tracts::{url.split("/services/")[-1]}: {e} (ids left out)'); return {}
    out = {}
    for f in j.get('features') or []:
        a = f.get('attributes') or {}
        out.setdefault(low(a.get(nf)), a)
    return out


def main():
    if not TR.on(): print('KPC_TRACT_STORE=0: nothing written'); return
    K = json.load(open('data/ky-answer-key.json', encoding='utf-8'))['parks']
    G, LIVE, MAP = {}, {}, {}
    for lay, (fn, url, nf) in KYL.items():
        MAP[lay] = SF.mapping(url)
        G[lay] = shapes(fn)
        LIVE[lay] = live_facts(url, nf, MAP[lay]) if url.startswith('http') else {}
    try: NPS = {low(u['name']): u['code'] for u in json.load(open('data/nps-units.json'))['units']}
    except Exception: NPS = {}  # noqa: BLE001
    PT, SH = {}, {}
    for ref, p in K.items():
        ts, rg = [], []
        for t in p.get('tracts') or []:
            lay, nm = str(t[0]), t[1] if len(t) > 1 else ''
            how = t[3] if len(t) > 3 else ''
            mp = MAP.get(lay) or {'key': lay, 'how': 'none'}
            r = G.get(lay, {}).get(low(nm)) or []
            x = TR.tract(f'{lay}:{nm}', nm, how, LIVE.get(lay, {}).get(low(nm)) or {}, mp, r, lay, src_key=mp.get('key') or lay,
                         ac_key=t[2] if len(t) > 2 else None)
            if len(t) > 4 and t[4]: x['pieces_key'] = t[4]
            if lay == 'bnps' and NPS.get(low(nm)): x['unit_code'] = NPS[low(nm)]
            if p.get('owned_only'): x['owned_only'] = p['owned_only']
            ts.append(x); rg += r
        if ts: PT[ref] = ts
        if rg: SH[ref] = rg
    nested = TR.nested_geometry(SH)
    d = TR.doc('US-KY', PT, nested, 'Kentucky: from data/ky-answer-key.json + the ky-*.geojson files; ids from the KY state GIS layers.')
    d['live_ids'] = {lay: len(v) for lay, v in LIVE.items() if v}
    TR.save('data/tracts/US-KY.json', d)
    print(f"::notice title=KY tracts::{len(PT)} parks, {sum(len(v) for v in PT.values())} tracts, {len(nested)} park-in-park links; "
          f"coverage {json.dumps(d['coverage'])}")


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::warning title=KY tracts::stopped ({type(e).__name__}: {e}); nothing written')  # noqa: BLE001
