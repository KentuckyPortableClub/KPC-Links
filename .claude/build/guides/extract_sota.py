"""Extract the per-summit card details from KPC_Kentucky_SOTA_W4K_Resource.pdf into kpc-guide-sota-data.json.
Run from the repo root:  python3 .claude/build/guides/extract_sota.py
Codes, names, counties, elevation, points and GPS come live from kpc-ky-data.json on the page; this file keeps only
what the PDF cards add: the KY GIS public-land line and the POTA / KFF parks within 3 miles (as printed)."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdfcards

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
PDF = os.path.join(REPO, 'KPC_Kentucky_SOTA_W4K_Resource.pdf')
OUT = os.path.join(REPO, 'kpc-guide-sota-data.json')
KEYS = {'INSIDE PUBLIC LAND (KY GIS)': 'land', 'POTA / KFF WITHIN 3 MI': 'near'}
NEAR_TAIL = "(to the park's reference point — check boundaries)"
LAND_TAIL = '(official KY public-land polygons; confirm before claiming)'

REGION_KEY = {'Bluegrass Region': 'Bluegrass', 'Northern Kentucky Region': 'Northern Kentucky',
              'Eastern Kentucky (Appalachian / Eastern Coal Field)': 'Eastern Kentucky',
              'South Central / Pennyroyal Region': 'South Central Pennyroyal',
              'Western Kentucky (Western Coal Field)': 'Western Kentucky', 'Jackson Purchase Region': 'Jackson Purchase'}

def main():
    cards, npages = pdfcards.cards(PDF, r'sotl\.as/summits/(W4K/[A-Z]{2}-\d{3})$')
    data = {}
    for c in cards:
        code = c['code']
        L = c['lines']
        assert L[0]['text'].startswith(code), (code, L[0]['text'])
        rec = {'pdfName': L[0]['text'][len(code):].strip()}
        m = re.match(r'(.+?) County • Region ([A-Z]{2}) • ([\d,]+) m / ([\d,]+) ft • (\d+) points?$', L[1]['text'])
        if not m:
            raise SystemExit(f'{code}: subtitle {L[1]["text"]!r}')
        rec['county'], rec['region'] = m.group(1), m.group(2)
        rec['m'], rec['ft'], rec['pts'] = int(m.group(3).replace(',', '')), int(m.group(4).replace(',', '')), int(m.group(5))
        assert L[2]['text'] == 'GPS OSM MAP WEATHER NEARBY ›', (code, L[2]['text'])
        cur = None
        paras = []
        for ln in L[3:]:
            t = ln['text'].replace('’', "'")
            if re.fullmatch(r'[A-Z]{2}(-\d{3}\+)?', t.strip()):
                continue  # section heading above the next card (EC-051+, KA, PR ...)
            key = next((k for k in KEYS if t.startswith(k + ' ')), None)
            if key:
                cur = {'k': KEYS[key], 't': t[len(key):].strip(), 'top': ln['top'], 'bot': ln['top']}
                paras.append(cur)
            elif cur and ln['x0'] <= 52:
                cur['t'] += ' ' + t.strip()
                cur['bot'] = ln['top']
            else:
                raise SystemExit(f'{code}: unexpected line {t!r}')
        gps = None
        for l in c['links']:
            if l['label'] == 'GPS':
                mm = re.search(r'query=([-\d.]+),([-\d.]+)', l['uri'])
                gps = [float(mm.group(1)), float(mm.group(2))]
        rec['gps'] = gps
        for p in paras:
            t = re.sub(r'\s+', ' ', p['t']).strip()
            links = [l for l in c['links'] if p['top'] - 4 <= l['top'] <= p['bot'] + 4]
            if p['k'] == 'near':
                assert t.endswith(NEAR_TAIL), (code, t)
                items = []
                for it in t[:-len(NEAR_TAIL)].strip().split(' • '):
                    mm = re.fullmatch(r'((?:US|KFF)-\d+) (.+) ([\d.]+) mi', it.strip())
                    if not mm:
                        raise SystemExit(f'{code}: near item {it!r}')
                    items.append([mm.group(1), mm.group(2), float(mm.group(3))])
                for l in links:  # every printed code is a link to its POTA / Logsearch page
                    assert any(i[0] == l['label'] for i in items), (code, l)
                    want = ('https://next.pota.app/park/' if l['label'].startswith('US-') else 'https://logsearch.wwff.co/directory/') + l['label']
                    assert l['uri'] == want, (code, l)
                assert len(links) == len(items), (code, links, items)
                rec['near'] = items
            else:
                assert t.endswith(LAND_TAIL), (code, t)
                rec['land'] = t[:-len(LAND_TAIL)].strip()
                for l in links:
                    rec.setdefault('landLinks', []).append({'label': l['label'], 'url': l['uri']})
        rec['pdfPage'] = c['page']
        if code in data:
            raise SystemExit('duplicate ' + code)
        data[code] = rec
    pins = pdfcards.map_regions(PDF, cards)
    for code, reg in pins.items():
        data[code]['mapRegion'] = REGION_KEY[reg]   # region the PDF's regional map put the pin in
    missing = [c for c in data if 'mapRegion' not in data[c]]
    if missing:
        raise SystemExit('cards with no map pin: ' + ', '.join(missing))
    doc = {'source': os.path.basename(PDF), 'pages': npages, 'cards': len(data),
           'note': 'Extracted from the PDF by .claude/build/guides/extract_sota.py. Codes, names, counties, elevation, points and GPS on the page come from kpc-ky-data.json.',
           'summits': data}
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', OUT, len(data), 'cards from', npages, 'pages')

if __name__ == '__main__':
    main()
