"""Builds kpc-ky-facilities.json (chat 3, Oct 25) from chat 2's data/ky-park-structures.json + data/ky-park-features.json:
per Kentucky state park / historic site (POTA ref): picnic shelters, restrooms / bath houses, trailheads (parking, restrooms), GPS each.
Run from the repo root: python3 .claude/build/facilities/build.py"""
import json, re, math
S = json.load(open('data/ky-park-structures.json'))['layers']['structures']
F = json.load(open('data/ky-park-features.json'))
D = json.load(open('kpc-ky-data.json'))
def norm(s): return re.sub(r'[^a-z0-9 ]+', ' ', s.lower().replace("'", '')).split()
def km(a, b, c, d): return 6371 * 2 * math.asin(math.sqrt(math.sin(math.radians(c - a) / 2) ** 2 + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(math.radians(d - b) / 2) ** 2))
parks = [p for p in D['parks'] if re.search(r'State (Resort )?Park|State Historic Site', p['n'])]
def ref_for(name):
    w = norm(name.replace('DAM VILLAGE', 'DAM VILLAGE'))
    best = None
    for p in parks:
        pw = norm(p['n'])
        if pw[:len(w)] == w or all(x in pw for x in w): 
            if best is None or len(pw) < len(norm(best['n'])): best = p
    if not best and w and w[-1] == 'lake': return ref_for(' '.join(w[:-1]))   # 'DALE HOLLOW LAKE' = Dale Hollow State Park
    return best
def kind(b):
    u = b.upper()
    sh = bool(re.search(r'SHELT|PAVIL', u)) and not re.search(r'GOLF|\bTEE\b|\d+ ?TEE|TEE \d', u)   # golf course shelters are not picnic shelters
    rr = bool(re.search(r'RESTR|\bR ?R\b|\bRR\b|TOILET|COMFORT|BATH ?HOUSE|SHOWER', u)) and not re.search(r'W/?O\b|WITHOUT', u)
    if re.search(r'GOLF|TEE\b|CORPORATE|OFFICE|POOL|GROC|CONCESSION|DRESSING', u) and not sh: rr = rr and 'POOL' not in u
    return sh, rr
out, miss = {}, set()
for la, lo, a in S:
    sh, rr = kind(a.get('BL_NAME', ''))
    if not (sh or rr): continue
    p = ref_for(a['PARK_NAME'])
    if not p: miss.add(a['PARK_NAME']); continue
    o = out.setdefault(p['c'], {'n': p['n'], 'sh': [], 'rr': [], 'th': []})
    nm = re.sub(r'\s+', ' ', a['BL_NAME']).strip().title().replace('W/O Rr', 'without restrooms').replace('W/Rr', 'with restrooms').replace('Rr', 'restrooms')
    if sh: o['sh'].append([round(la, 6), round(lo, 6), nm])
    if rr: o['rr'].append([round(la, 6), round(lo, 6), nm])
# trailheads: the nearest of these parks (its shelters / restrooms or its pin) within 4 km
for t in F.get('trailheads', []):
    best, bd = None, 4.0
    for p in parks:
        pts = [(p['la'], p['lo'])] if p.get('la') else []
        pts += [(x[0], x[1]) for x in (out.get(p['c'], {}).get('sh', []) + out.get(p['c'], {}).get('rr', []))]
        for a, b in pts:
            d = km(t['la'], t['lo'], a, b)
            if d < bd: bd, best = d, p
    if best:
        o = out.setdefault(best['c'], {'n': best['n'], 'sh': [], 'rr': [], 'th': []})
        o['th'].append([t['la'], t['lo'], (t.get('NAME') or '').title(), (t.get('TRAIL_NAME') or '').title(), t.get('PARKING') == 'Yes', t.get('RESTROOMS') == 'Yes'])
json.dump({'about': "Kentucky State Parks GIS (kygisserver.ky.gov Ky_State_Parks_Features): shelters, restrooms / bath houses and trailheads per state park / historic site, matched to POTA refs (built by .claude/build/facilities/build.py from chat 2's data files). The state's own building list: confirm on site.",
           'parks': out}, open('kpc-ky-facilities.json', 'w'), separators=(',', ':'), ensure_ascii=False)
print(len(out), 'parks;', sum(len(v['sh']) for v in out.values()), 'shelters,', sum(len(v['rr']) for v in out.values()), 'restrooms,', sum(len(v['th']) for v in out.values()), 'trailheads; unmatched:', sorted(miss))
