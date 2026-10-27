#!/usr/bin/env python3
"""Rebuild the members-only Multi-Park Spots map (kpc-multi-park-spots.html) from the clean Kentucky 2-fer data
(KentuckyPortableClub/KPC-Data data/fers/US-KY.json, after chat 8's final look). Usage: build.py <US-KY.json>
Keeps Brandon's field-checked points (old rows with the same parks). Chat 2, Oct 27 2026."""
import json, re, sys, math
SHORT = "⚠️ Parks' boundaries may overlap here, but we can't confirm it. Check both official boundary maps and make your own call before you count it."
PAGE = 'kpc-multi-park-spots.html'
d = json.load(open(sys.argv[1]))
s = open(PAGE).read()
m = re.search(r'const DATA=(\[.*?\]);\n', s, re.S)
old = json.loads(m.group(1))
C = json.load(open('kpc-ky-counties.json'))
def inr(x, y, r):
    c = False
    for i in range(len(r)):
        (x1, y1), (x2, y2) = r[i][:2], r[i - 1][:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-15) + x1: c = not c
    return c
def county(la, lo):
    for c in C:
        r = c['r']
        polys = [r] if isinstance(r[0][0][0], (int, float)) else r   # rings, or a list of polygons
        for poly in polys:
            if inr(lo, la, poly[0]) and not any(inr(lo, la, h) for h in poly[1:]): return c['n']
    return ''
def ft(m): return f"{round(m * 3.28084):,} ft" if m < 400 else f"{m / 1609.34:.1f} mi"
LIVE = ('candidate', 'very tight', 'water only')
rows = []
for x in d['spots']:
    st = str(x.get('status', ''))
    if not st.startswith(LIVE): continue
    refs = x['refs']; names = [(x.get('names') or {}).get(r, r) for r in refs]
    kind = x.get('kind')
    label = ('Same land, two park numbers' if kind == 'same land' else
             'Very tight: could be map error, check both official maps on the ground' if st.startswith('very tight') else
             '🚤 Water only: boat or kayak' if st.startswith('water only') else '')
    if kind == 'area': how = 'Overlapping boundaries'
    elif kind == 'same land': how = 'Same land, two park numbers'
    else: how = ('Trail' if kind == 'trail' else 'River') + ' through the park: ' + ' / '.join(n for r, n in zip(refs, names) if r in (x.get('line_source') or {}))
    if x.get('kind') == 'area' and len(refs) > 2: how = f'{len(refs)} parks on one patch'
    if label and label not in how: how = label + ' · ' + how
    if kind == 'area' and x.get('wide_m'): size = f"about {x.get('acres_all') or x.get('acres')} acres" + (f" in {x['patches']} patches" if x.get('patches') else '') + f", {ft(x['wide_m'])} across at the widest"
    elif x.get('len_m'): size = f"{ft(x['len_m'])} of line inside" + (f" ({x['stretches']} stretches)" if x.get('stretches') else '')
    else: size = ''
    la, lo = x['center']
    pts = []
    for p in ([x['access_pin']] if x.get('access_pin') else []) + (x.get('pins') or []):
        if not p or not p.get('at') or str(p.get('from', '')).startswith('none'): continue
        if any(abs(p['at'][0] - q['la']) < 1e-5 and abs(p['at'][1] - q['lo']) < 1e-5 for q in pts): continue
        w = p.get('walk_m') or 0
        q = 'A' if p['from'] in ('road', 'parking / access point') and w < 150 else 'B' if w < 800 else 'C'
        pts.append({'la': p['at'][0], 'lo': p['at'][1], 'q': q, 'what': f"Closest spot inside every park to a {p['from']}" + (f": {p['name']}" if p.get('name') else ''),
                    'note': f"About {ft(w)} from it, straight line. {p.get('note', '')}".strip()})
    pts = pts[:3]
    pts.append({'la': la, 'lo': lo, 'q': 'C', 'what': 'Middle of the spot', 'note': 'The widest point of the possible overlap. Check satellite view and the official maps.'})
    # Brandon's own field checks on the same parks stay first
    for o in old:
        if sorted(o['refs']) == sorted(refs):
            fc = [p for p in o['points'] if re.search(r'field check|KZ4CP|checked this spot', p.get('what', '') + ' ' + p.get('note', ''), re.I)]
            pts = fc + pts
    extra = [SHORT]
    if x.get('members_line'): extra.append('Members: ' + x['members_line'] + '.')
    if x.get('owner_here'): extra.append('Land here: ' + x['owner_here'] + '.')
    if x.get('how_checked'): extra.append(x['how_checked'] + '.')
    if x.get('note'): extra.append(x['note'] + '.')
    if x.get('pairs_here'): extra.append('Also counts as the pairs ' + ', '.join(x['pairs_here']) + ' on this patch.')
    extra += [n[0].upper() + n[1:] + '.' for n in x.get('notes') or []]
    maps = [f"{r}: {u}" for r, u in (x.get('maps') or []) if u]
    if maps: extra.append('Official maps: ' + ' · '.join(maps))
    extra.append(f"Checked {x.get('checked', '')}.")
    rows.append({'type': f'{len(refs)}-fer', 'how': how, 'refs': refs, 'names': names, 'size': size, 'county': county(la, lo),
                 'points': pts, 'note': ' '.join(e.replace('..', '.') for e in extra)})
rows.sort(key=lambda r: (-len(r['refs']), r['how'].startswith(('Very tight', '🚤')), r['county'], r['refs']))
s = s[:m.start(1)] + json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + s[m.end(1):]
open(PAGE, 'w').write(s)
print(len(rows), 'spots;', sum(1 for r in rows if len(r['refs']) > 2), 'with 3+ parks;', sum(len(r['points']) for r in rows), 'points')
