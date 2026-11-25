#!/usr/bin/env python3
"""FOUND TRAIL LINES -> the trail bot (chat 2, Nov 1 2026; Brandon 1:40 PM: 'there is a flaw in our system when we are finding stuff
but it never makes it in'). The outside research (KPC-Data data/intake/external-results.json) marks a trail park SURE on an official
LINE layer (same proper name, a line within 200 m of the POTA pin), but no bot ever turned those finds into trail lines: the layer
wiring bot (BOT W) skips line layers and the trail bots only read fixed lists. On Nov 1 that was ~100 trail parks still drawn as a pin
(the Mount Vernon Trail among them). This script hands every such find to kpc_us_trails.py (env EXTRA_TRAILS):
  - only result SURE, only polyline layers, only parks that are still a PIN in every state key (no joined piece at all)
  - not when chat 11 / a person said NO to that park + layer (any data/waiting/questions/*.json row with answer NO)
  - the line is read with  <name field> = '<record name>'  AND an envelope of 0.3 deg around the pin (a same-named trail in another
    forest never comes along); federal layers (NPS, Forest Service, BLM, FWS) before state ones; one source per park
  - 'by' names the agency host; the result goes through the waiting room like every trail file (chat 11 checks), then the key
    (kpc_us_key.py TRL) draws it as the park's line + POTA's 100-ft band
Writes the list to argv[1] (default /tmp/finds-lines.json) and data/status/finds-lines-report.json. No network. Exit 0 always."""
import glob, json, os, pathlib, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kpc_json_any import MissingInput, exists_any, glob_json_any, load_json_any  # noqa: E402

FED = re.compile(r'nps\.gov|fs\.usda\.gov|fs\.fed\.us|blm\.gov|fws\.gov|fBc8EJBxQRMcHlei', re.I)
# Nov 2 (PR 4, Official trail lines; Brandon: official sources only): picks that are NOT an agency's own layer, so never wired.
#  - Razorback Regional Greenway (US-13622): the only copy is a personal ArcGIS account (consultant / university re-host), no agency layer
#  - Junction and Breakwater (US-9877) and any park: services9 'USGS_Trails' is a third-party RE-HOST of the USGS trails, not USGS itself
#    (the real USGS National Digital Trails layer is partnerships.nationalmap.gov, wired by hand in data/trails-hand.json)
REJECT_LAYERS = {
    'https://services6.arcgis.com/VcV5jchX8PVtkcbc/ArcGIS/rest/services/dataVIEWER_of_NW_Arkansas_Trails_2021_WFL1/FeatureServer/5': 'personal account re-host (Razorback)',
}
REJECT_HOSTS = re.compile(r'services9\.arcgis\.com/FF3qnCUixr5w9JQi/', re.I)   # third-party USGS_Trails re-host
TRAILY = re.compile(r'\btrail\b|\btrails\b|\broute\b|greenway|\bpath\b|\bway\b|byway|towpath|rail.?trail', re.I)
# 24 Nov 2026 (owner t2067u 'I agree work on it'): a found line under 1 km (about 0.6 mi) is never put on an AREA park (a park
# whose POTA type is not a trail, river, route or greenway: a recreation area, wildlife area, park...). New rows for area parks
# carry 'min_km' (kpc_us_trails.py checks the drawn length); a found line already saved under 1 km on an area park is handed
# back as a 'drop' row, so the trail bot takes it off (listed, never silent).
AREA_MIN_KM = 1.0
TRAIL_TYPE = re.compile(r'trail|greenway|byway|path|route|river|towpath|blueway', re.I)


def area_park(ptype):
    """True when POTA's park type is not a trail / river / route type."""
    return not TRAIL_TYPE.search(str(ptype or ''))


def line_km(lines):
    """Kilometres along [[lon, lat], ...] lines (great circle)."""
    import math
    def km(a, b, c, d):
        r = math.radians
        return 6371 * 2 * math.asin(math.sqrt(math.sin(r(c - a) / 2) ** 2 + math.cos(r(a)) * math.cos(r(c)) * math.sin(r(d - b) / 2) ** 2))
    return sum(km(l[i][1], l[i][0], l[i + 1][1], l[i + 1][0]) for l in lines or [] for i in range(len(l) - 1)
               if l[i] and l[i + 1] and len(l[i]) >= 2 and len(l[i + 1]) >= 2)


def too_short_for_area(row, lines):
    """True when a hand-off row carries min_km and the drawn line is shorter (kpc_us_trails.py: the line is not used)."""
    mk = (row or {}).get('min_km')
    return bool(mk) and line_km(lines) < float(mk)


def saved_line_km(path):
    """Kilometres of a saved line file (data/trails/<ref>.json); None when it cannot be read."""
    try: g = json.load(open(path, encoding='utf-8'))
    except Exception: return None  # noqa: BLE001
    out = 0.0
    for f in (g.get('features') or [g]):
        gg = f.get('geometry') or {}
        c = gg.get('coordinates') or []
        out += line_km([c] if gg.get('type') == 'LineString' else c)
    return out


def load(p, d):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d  # noqa: BLE001


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/finds-lines.json'
    D = pathlib.Path(os.environ.get('DATA') or 'kpcdata')
    # Nov 6: external-results.json may be .gz (.gz wins). Neither copy on disk is still {}, as before.
    ext_path = D / 'data/intake/external-results.json'
    ext = load_json_any(ext_path) if exists_any(ext_path) else {}
    pairs, layers = ext.get('pairs') or {}, ext.get('layers') or {}
    pins, names, typ = {}, {}, {}
    for f in glob.glob('data/parkinfo/US-*.json'):
        for r, v in (load(f, {}).get('parks') or {}).items():
            names[r] = v[0]; typ[r] = v[2] if len(v) > 2 else ''
            if len(v) > 6 and v[5] and v[6]: pins[r] = (float(v[5]), float(v[6]))
    joined, seen = set(), set()
    for f in glob.glob('data/us-key/US-*.json'):
        for r, p in (load(f, {}).get('parks') or {}).items():
            seen.add(r)
            if p.get('m'): joined.add(r)
    qdir = D / 'data/waiting/questions'
    qfiles = glob_json_any(str(qdir / '*.json')) if qdir.is_dir() else []
    if qdir.is_dir() and not qfiles and any(qdir.iterdir()):
        raise MissingInput(f'{qdir} has files but no *.json or *.json.gz, so a NO answer would be ignored')
    no = set()
    for f in qfiles:
        s = load_json_any(f)
        rows = (s.get('open') or s.get('questions') or s.get('rows') or []) if isinstance(s, dict) else s
        rows = list(rows.values()) if isinstance(rows, dict) else rows
        if not isinstance(rows, list): continue
        for q in rows or []:
            if isinstance(q, dict) and re.match(r'\W*NO\b', str(q.get('answer') or ''), re.I):
                no.add((str(q.get('ref') or ''), str(q.get('layer') or q.get('url') or '').rstrip('/')))
    HAND = set((load('data/trails-hand.json', {}).get('parks') or {}))
    # 24 Nov 2026: found lines already saved on an area park under 1 km are handed back to be taken off
    drops = []
    for x in load('data/trails/index.json', []) or []:
        r = str((x or {}).get('ref') or '')
        if x.get('kind') != 'found' or not r.startswith('US-') or r in HAND or not area_park(typ.get(r, '')): continue
        k = saved_line_km(f'data/trails/{r}.json')
        if k is not None and k < AREA_MIN_KM:
            drops.append({'ref': r, 'name': names.get(r) or x.get('name') or r, 'drop': True, 'kind': 'found',
                          'why': f'a found line of {k * 3280.84:,.0f} ft on an area park (under 0.6 mi): not a trail line for this park'})
    cand = {}
    for k, v in pairs.items():
        if v.get('result') != 'SURE' or '|' not in k: continue
        ref, url = k.split('|', 1)
        L = layers.get(url) or {}
        if 'Polyline' not in str(L.get('geometry')) or not L.get('name_field') or not v.get('record_name'): continue
        if not ref.startswith('US-') or ref not in seen or ref in joined or ref not in pins: continue
        if os.path.exists(f'data/trails/{ref}.json'): continue   # Nov 2: a line already saved (state trails bot) is never replaced by a found one (US-11905 187 km -> 4 km was held)
        if ref in HAND: continue   # Nov 2 (PR 4): an official line picked by hand (data/trails-hand.json) is the state trails bot's
        if not (TRAILY.search(names.get(ref, '')) or 'Trail' in typ.get(ref, '')): continue
        if (ref, url.rstrip('/')) in no: continue
        if url.rstrip('/') in REJECT_LAYERS or REJECT_HOSTS.search(url): continue   # Nov 2 (PR 4): not an agency's own layer
        cand.setdefault(ref, []).append((0 if FED.search(url) else 1, url, L, v))
    rows, rep = [], []
    for ref, cs in sorted(cand.items()):
        cs.sort(key=lambda c: c[0]); _, url, L, v = cs[0]
        m = re.match(r'(.+?)/(\d+)$', url.rstrip('/'))
        if not m: continue
        la, lo = pins[ref]; nm = str(v['record_name']).replace("'", "''")
        rows.append({'ref': ref, 'name': names.get(ref) or v['record_name'], 'url': m.group(1), 'layer': int(m.group(2)),
                     'where': f"{L['name_field']} = '{nm}'", 'bbox': [round(lo - .3, 4), round(la - .3, 4), round(lo + .3, 4), round(la + .3, 4)],
                     'kind': 'found', 'by': f"official agency layer '{L.get('title') or ''}' ({L.get('host') or url.split('/')[2]}); sure match found by the outside research, wired by kpc_finds_lines"})
        if area_park(typ.get(ref, '')): rows[-1]['min_km'] = AREA_MIN_KM   # 24 Nov: never a stub under 1 km on an area park
        rep.append([ref, names.get(ref), v['record_name'], url])
    rows += drops
    json.dump(rows, open(out, 'w'), indent=1, ensure_ascii=False)
    os.makedirs('data/status', exist_ok=True)
    json.dump({'about': 'SURE trail-line finds handed to the trail bot (kpc_finds_lines.py)', 'count': len(rows) - len(drops), 'rows': rep,
               'drops': [[d['ref'], d['why']] for d in drops]},
              open('data/status/finds-lines-report.json', 'w'), indent=1, ensure_ascii=False)
    print(f"::notice title=Found trail lines::{len(rows) - len(drops)} trail parks still a pin had a SURE official line in the outside research: handed to the trail bot ({len(no)} NO answers respected); "
          f"{len(drops)} found line(s) under 0.6 mi on an area park handed back to be taken off: {' '.join(d['ref'] for d in drops[:12])}")


if __name__ == '__main__':
    try: main()
    except MissingInput as e:
        print(f'::error title=Found trail lines::{e}')
        sys.exit(1)
    except Exception as e: print(f'::notice title=Found trail lines::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
