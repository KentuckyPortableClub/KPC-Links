"""One-off (chat 3, Oct 31; Brandon 9:07 PM 'overlap finder needs a map for the world … default US'): builds kpc-world-map.json
for the Overlap Finder's clickable WORLD and CANADA maps from Natural Earth (public domain): 1:110m countries + 1:50m Canadian
provinces, simplified, coordinates rounded to 0.01 degree. Never fails. The workflow that runs it is deleted after use."""
import json, urllib.request
from shapely.geometry import shape, mapping
B = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/'
def get(n): return json.load(urllib.request.urlopen(urllib.request.Request(B + n, headers={'User-Agent': 'KPC'}), timeout=120))
def rings(g, tol):
    g = g.simplify(tol, preserve_topology=True); m = mapping(g); out = []
    polys = [m['coordinates']] if m['type'] == 'Polygon' else m['coordinates'] if m['type'] == 'MultiPolygon' else []
    for poly in polys:
        rr = [[[round(x, 2), round(y, 2)] for x, y in ring] for ring in poly[:1] if len(ring) >= 4]   # outer ring only (small map)
        if rr: out.append(rr)
    return out
out = {'v': 1, 'src': 'Natural Earth (public domain)', 'countries': [], 'ca': []}
for f in get('ne_110m_admin_0_countries.geojson')['features']:
    p = f['properties']; a = p.get('ISO_A2_EH') or p.get('ISO_A2')
    if not a or a == '-99' or a == 'AQ': continue
    out['countries'].append({'a': a, 'n': p.get('NAME_EN') or p.get('NAME'), 'p': rings(shape(f['geometry']), 0.05)})
for f in get('ne_50m_admin_1_states_provinces.geojson')['features']:
    p = f['properties']
    if p.get('adm0_a3') != 'CAN': continue
    out['ca'].append({'a': (p.get('postal') or '')[:2], 'n': p.get('name'), 'p': rings(shape(f['geometry']), 0.04)})
json.dump(out, open('kpc-world-map.json', 'w'), separators=(',', ':'))
print('::notice title=world map::%d countries, %d provinces' % (len(out['countries']), len(out['ca'])))
