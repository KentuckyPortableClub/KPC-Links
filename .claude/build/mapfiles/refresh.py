#!/usr/bin/env python3
"""Rebuild the main pins in the Kentucky map files (parks.html 'KPC Map Files') from kpc-ky-data.json.
Keeps the access-point folders/waypoints and any 'Notes:' lines already in the files.
Run from the repo root: python3 .claude/build/mapfiles/refresh.py"""
import json, re, html
D = json.load(open('kpc-ky-data.json'))
OV = json.load(open('ky-overlaps.geojson'))['features']
P = {p['c']: p for p in D['parks']}
NAME = {**{p['c']: p['n'] for p in D['parks']}, **{k['c']: k['n'] for k in D['kff']}, **{s['c']: s['n'] for s in D['summits']}}
x = lambda s: html.escape(str(s), quote=False)
def county(co):
    if not co: return 'County: see official site'
    return co + (' Counties' if '/' in co else ' County')
UNC = {}
for f in OV:
    pr = f['properties']
    if pr.get('kind') == 'unconfirmed':
        refs = [r[0] for r in pr.get('pota', [])]
        for r in refs: UNC.setdefault(r, set()).update(q for q in refs if q != r)
def split(text, refpat):
    """return (ref pins text, others) for gpx; ref pin = name 'REF Name' without the access dot"""
    return text
def park_lines(p, notes):
    L = [p['n'], county(p.get('co')) + ' • ' + p['t'], ('POTA', 'https://next.pota.app/park/' + p['c'])]
    if p.get('off'): L.append(('Official Map (official)', p['off']))
    if p.get('web'): L.append(('Website', p['web']))
    if notes: L.append(notes)
    if p.get('tf'): L.append('2-fer (overlapping boundaries): ' + ', '.join(f"{r} {NAME.get(r, '')}".strip() for r in p['tf']))
    if UNC.get(p['c']): L.append('Possible 2-fer (not confirmed, check the boundaries first): ' + ', '.join(sorted(UNC[p['c']])))
    also = (p.get('kff') or []) + (p.get('sota') or [])
    if also: L.append('Also (same ground, other programs): ' + ', '.join(f"{r} {NAME.get(r, '')}".strip() for r in also))
    L.append('Use the official map first. Verify current rules, access and boundaries before activating.')
    return L
def kff_lines(k, old):
    L = [k['n'], county(k.get('co')), ('WWFF Logsearch', 'https://logsearch.wwff.co/directory/' + k['c'])]
    p = P.get(k.get('p'))
    if p:
        L.append(('Matching POTA park: ' + p['c'] + ' ' + p['n'] + ' —', 'https://next.pota.app/park/' + p['c']))
        if p.get('off'): L.append(('Official map', p['off']))
        if p.get('web'): L.append(('Website', p['web']))
    L.append('Verify WWFF rules and boundaries before activating.')
    return L
def kml_desc(L):
    out = []
    for l in L:
        if isinstance(l, tuple):
            lab, u = l
            out.append(f'<a href="{x(u)}">{x(lab.rstrip(" —"))}</a>' if lab in ('POTA', 'Website', 'Official Map (official)') else f'{x(lab)}: <a href="{x(u)}">{x(u)}</a>' if not lab.endswith('—') else f'{x(lab)} <a href="{x(u)}">{x(u)}</a>')
        else: out.append(x(l))
    return '<![CDATA[' + '<br>'.join(out) + ']]>'
def gpx_desc(L):
    return x('\n'.join(l if isinstance(l, str) else (f'{l[0]} {l[1]}' if l[0].endswith('—') else f'{l[0]}: {l[1]}') for l in L))
REFNAME = re.compile(r'^(US-\d+|KFF-\d+) (?!·)')
def old_notes(gpx):
    N = {}
    for m in re.finditer(r'<wpt[^>]*><name>(\S+) [^<]*</name><desc>(.*?)</desc>', gpx, re.S):
        n = re.search(r'^Notes: .*$', html.unescape(m[2]), re.M)
        if n: N[m[1]] = n[0]
    return N
def rebuild(base, items, lines, typ, style, linkname, link, title, blurb):
    g = open(base + '.gpx', encoding='utf-8').read(); k = open(base + '.kml', encoding='utf-8').read()
    notes = old_notes(g)
    # GPX: drop old ref pins, keep the rest (access points), put fresh ref pins first
    wpts = re.findall(r'<wpt .*?</wpt>\n?', g, re.S)
    keep = [w for w in wpts if not REFNAME.match(re.search(r'<name>([^<]*)</name>', w)[1])]
    head = g[:g.find('<wpt')]
    new = []
    for it in items:
        L = lines(it, notes.get(it['c']))
        new.append(f'<wpt lat="{it["la"]}" lon="{it["lo"]}"><name>{x(it["c"] + " " + it["n"])}</name><desc>{gpx_desc(L)}</desc><link href="{x(link(it))}"><text>{linkname}</text></link><type>{x(typ(it))}</type></wpt>\n')
    open(base + '.gpx', 'w', encoding='utf-8').write(head + ''.join(new) + ''.join(keep) + '</gpx>\n')
    # KML: replace every folder that holds ref pins; keep access folders
    folders = re.findall(r'<Folder><name>.*?</Folder>\n?', k, re.S)
    acc = [f for f in folders if f.startswith('<Folder><name>Official access') or f.startswith('<Folder><name>Nearby access')]
    styles = re.findall(r'<Style id=.*?</Style>\n?', k, re.S)
    smap = {}
    for f in folders:
        if f in acc: continue
        nm = re.match(r'<Folder><name>([^<]*)', f)[1]; s = re.search(r'<styleUrl>#([^<]*)</styleUrl>', f)
        if s: smap[nm] = s[1]
    groups = {}
    for it in items: groups.setdefault(typ(it) if style else title, []).append(it)
    fx = []
    for nm in sorted(groups):
        st = smap.get(nm) or smap.get('Other') or next(iter(smap.values()))
        pm = ''.join(f'<Placemark><name>{x(it["c"] + " " + it["n"])}</name><styleUrl>#{st}</styleUrl><description>{kml_desc(lines(it, notes.get(it["c"])))}</description><Point><coordinates>{it["lo"]},{it["la"]},0</coordinates></Point></Placemark>' for it in sorted(groups[nm], key=lambda i: i['n']))
        fx.append(f'<Folder><name>{x(nm)}</name>{pm}</Folder>\n')
    doc = f'<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>{x(title)}</name>\n<description>{x(blurb)}</description>\n' + ''.join(styles) + ''.join(fx) + ''.join(acc).rstrip('\n') + '</Document></kml>\n'
    open(base + '.kml', 'w', encoding='utf-8').write(doc)
    print(base, len(items), 'pins;', len(keep), 'access points kept;', len(notes), 'notes kept')
parks = sorted(D['parks'], key=lambda p: p['n'])
rebuild('KPC_Kentucky_POTA_Parks', parks, park_lines, lambda p: p['t'], True, 'Next POTA park page', lambda p: 'https://next.pota.app/park/' + p['c'],
        'KPC Kentucky POTA Parks', f'Kentucky Portable Club • {len(parks)} Kentucky POTA parks. Use the official map first; verify current rules, access and boundaries before activating.')
kff = sorted(D['kff'], key=lambda k: k['c'])
rebuild('KPC_Kentucky_KFF_References', kff, kff_lines, lambda k: 'WWFF reference', False, 'WWFF Logsearch', lambda k: 'https://logsearch.wwff.co/directory/' + k['c'],
        'KFF references', 'Kentucky Portable Club • Active Kentucky WWFF (KFF) references from WWFF Logsearch. Verify WWFF rules and boundaries before activating.')
