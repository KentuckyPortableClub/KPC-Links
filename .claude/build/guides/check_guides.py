"""Check the guide pages' live calculations against the printed PDFs.
Run from the repo root:  python3 .claude/build/guides/check_guides.py
It recomputes, with the same rules as kpc-guide-sota.js / kpc-guide-wwff.js:
  SOTA: POTA/KFF within 3 mi (minus parks the summit is inside), every summit within 10 mi (else the nearest one)
  WWFF: SOTA within 3 mi (minus summits inside), every KFF within 25 mi (else the nearest one)
and prints any card where the result differs from the PDF. Differences are expected when kpc-ky-data.json changes."""
import json, math, os, re, pdfplumber
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
D = json.load(open(os.path.join(REPO, 'kpc-ky-data.json')))
GS = json.load(open(os.path.join(REPO, 'kpc-guide-sota-data.json')))['summits']
GW = json.load(open(os.path.join(REPO, 'kpc-guide-wwff-data.json')))['refs']

def mi(a, b, c, e):
    p = math.radians
    x = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(e - b) / 2) ** 2
    return 2 * 3958.8 * math.asin(math.sqrt(x))

FMT = {'sota': lambda d: f'{d:.1f}',                                  # SOTA guide: always one decimal
       'wwff': lambda d: f'{d:.1f}' if d < 10 else f'{round(d):.0f}'}   # WWFF guide: whole miles from 10 up

def nearby_text(pdf, title):
    text = []
    on = False
    for p in pdfplumber.open(os.path.join(REPO, pdf)).pages:
        t = p.extract_text() or ''
        if title in t:
            on = True
        if on:
            text.append(t)
    lines = [l.strip() for l in '\n'.join(text).split('\n')]
    out, cur = {}, None
    for l in lines:
        m = re.match(r'^((?:W4K/[A-Z]{2}-\d{3})|(?:KFF-\d{4})) .*‹ CARD$', l)
        if m:
            cur = m.group(1); out[cur] = ''
        elif cur and (l.startswith('WITHIN') or (out[cur] and not l.startswith('KPC KENTUCKY') and not l.startswith('KENTUCKY ') and not l.startswith('GET PERMISSION') and not l.startswith('USE THE OFFICIAL'))):
            out[cur] += ' ' + l
    res = {}
    for k, v in out.items():
        v = v.strip()
        m = re.search(r'nearest is (\S+) ([\d.]+) mi', v)
        if m:
            res[k] = ('nearest', [(m.group(1), m.group(2))])
        else:
            res[k] = ('within', re.findall(r'((?:W4K/[A-Z]{2}-\d{3})|(?:KFF-\d{4})) .*? ([\d.]+) mi', v))
    return res

def near_list(src, pts, radius, fmt):
    L = sorted(((mi(src['la'], src['lo'], p['la'], p['lo']), p['c']) for p in pts if p['c'] != src['c']))
    w = [(c, fmt(d)) for d, c in L if d <= radius]
    return ('within', w) if w else ('nearest', [(L[0][1], FMT['wwff'](L[0][0]))])  # 'nearest is' uses whole miles from 10 up in both guides

def main():
    bad = 0
    S, K, P = D['summits'], D['kff'], D['parks']
    # SOTA cards: parks within 3 mi
    for s in S:
        g = GS.get(s['c'], {})
        inside = {l['label'] for l in g.get('landLinks', [])}
        comp = sorted([(c, round(d, 1)) for d, c in ((mi(s['la'], s['lo'], p['la'], p['lo']), p['c']) for p in P + K) if d <= 3.0 and c not in inside])
        pdf = sorted([(i[0], i[2]) for i in g.get('near', [])])
        if g and comp != pdf:
            bad += 1; print('SOTA 3mi', s['c'], comp, pdf)
    # WWFF cards: SOTA within 3 mi
    for k in K:
        g = GW.get(k['c'])
        if not g:
            continue
        a = g.get('also') or {}
        inside = set(a.get('inside', []))
        comp = sorted([(c, round(d, 1)) for d, c in ((mi(k['la'], k['lo'], s['la'], s['lo']), s['c']) for s in S) if d <= 3.0 and c not in inside])
        pdf = sorted([(c, d) for c, d in a.get('near', [])])
        if comp != pdf:
            bad += 1; print('WWFF sota3', k['c'], comp, pdf)
    for pdf, title, pts, radius, fmt in [('KPC_Kentucky_SOTA_W4K_Resource.pdf', 'Nearby Summits', S, 10, FMT['sota']),
                                    ('KPC_Kentucky_WWFF_KFF_Resource.pdf', 'Nearby Parks', [k for k in K if k['c'] in GW], 25, FMT['wwff'])]:
        printed = nearby_text(pdf, title)
        n = 0
        for p in pts:
            if p['c'] not in printed:
                print('not printed', p['c']); bad += 1; continue
            c = near_list(p, pts, radius, fmt)
            pr = printed[p['c']]
            if c[0] != pr[0] or sorted(c[1]) != sorted(pr[1]):
                bad += 1; n += 1
                if n < 8:
                    print('NEARBY', p['c'], '\n  page', c, '\n  pdf ', pr)
        print(pdf, 'nearby lists checked:', len(pts), 'printed:', len(printed), 'differences:', n)
    print('total differences:', bad)

if __name__ == '__main__':
    main()
