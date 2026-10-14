"""Extract the per-reference card details from KPC_Kentucky_WWFF_KFF_Resource.pdf into kpc-guide-wwff-data.json.
Run from the repo root:  python3 .claude/build/guides/extract_wwff.py
Codes, names, counties, coordinates and POTA pairing come live from kpc-ky-data.json on the page; this file keeps
only what the PDF cards add (park type, links, access points, notes, SOTA 'Also' lines)."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdfcards

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
PDF = os.path.join(REPO, 'KPC_Kentucky_WWFF_KFF_Resource.pdf')
OUT = os.path.join(REPO, 'kpc-guide-wwff-data.json')

# Button label in the PDF -> key in the JSON. GPS / OSM / WEATHER are rebuilt on the page from coordinates.
BTN = {'OFFICIAL MAP': 'map', 'AREA MAP': 'areamap', 'BROCHURE': 'brochure', 'WEBSITE': 'web', 'ENTRANCE': 'entrance',
       'CAMPING ›': 'camp', 'RESORT ›': 'resort', 'CABINS ›': 'cabins'}
DERIVED = {'GPS', 'OSM BOUNDARY', 'WEATHER'}
NOTE_KEYS = ['ACCESS POINTS', 'ACCESS ADVISORY', 'PARKING (official page)', 'TRAIL', 'NOTES', 'ALSO']

def parse_also(t):
    """'SOTA inside (KY GIS): W4K/EC-131 Unnamed 1820C • ... | SOTA within 3 mi: W4K/EC-082 Unnamed 2065 1.6 mi'"""
    res = {'inside': [], 'near': []}
    for part in t.split('|'):
        part = part.strip()
        m = re.match(r'SOTA inside \(KY GIS\):\s*(.*)$', part)
        if m:
            res['inside'] = re.findall(r'(W4K/[A-Z]{2}-\d{3})', m.group(1))
            continue
        m = re.match(r'SOTA within 3 mi:\s*(.*)$', part)
        if m:
            for it in m.group(1).split('•'):
                mm = re.search(r'(W4K/[A-Z]{2}-\d{3}).*?([\d.]+) mi\s*$', it.strip())
                if not mm:
                    raise SystemExit('cannot parse ALSO item: ' + it)
                res['near'].append([mm.group(1), float(mm.group(2))])
            continue
        raise SystemExit('cannot parse ALSO: ' + part)
    return res

REGION_KEY = {'Bluegrass Region': 'Bluegrass', 'Northern Kentucky Region': 'Northern Kentucky',
              'Eastern Kentucky (Appalachian / Eastern Coal Field)': 'Eastern Kentucky',
              'South Central / Pennyroyal Region': 'South Central Pennyroyal',
              'Western Kentucky (Western Coal Field)': 'Western Kentucky', 'Jackson Purchase Region': 'Jackson Purchase'}

def main():
    cards, npages = pdfcards.cards(PDF, r'logsearch\.wwff\.co/directory/(KFF-\d{4})')
    data = {}
    for c in cards:
        code = c['code']
        L = c['lines']
        head = L[0]['text']
        assert head.startswith(code), (code, head)
        rec = {'pdfName': head[len(code):].strip()}
        sub = L[1]['text']
        while len(L) > 2 and L[2]['x0'] >= 130 and not L[2]['bold']:
            sub += ' ' + L[2]['text']   # wrapped subtitle
            L = L[:2] + L[3:]
        parts = [p.strip() for p in sub.split(' • ')]
        rec['counties'] = re.sub(r' Count(y|ies)$', '', parts[0])
        rec['type'] = parts[1] if len(parts) > 1 else ''
        pota = [p for p in parts[2:] if p.startswith('POTA: ')]
        if pota:
            rec['potaName'] = pota[0][6:]
        if len(parts) > 2 + len(pota):
            raise SystemExit('unexpected subtitle ' + sub)
        links = c['links']
        assert links[0]['label'] == code, links[0]
        if len(links) > 1 and links[1]['top'] == links[0]['top']:
            rec['nameUrl'] = links[1]['uri']
        btn_top = [l for l in links[2 if 'nameUrl' in rec else 1:]]
        btns = []
        gps = None
        notes = []
        # labelled lines: anything below the button rows
        cur = None
        for ln in L[2:]:
            if re.fullmatch(r'KFF-\d000s', ln['text'].strip()):
                continue  # section heading that sits above the next card
            key = next((k for k in NOTE_KEYS if ln['text'].startswith(k + ' ') and ln['bold'].startswith(k)), None)
            if key:
                cur = {'k': key, 't': ln['text'][len(key):].strip(), 'top': ln['top'], 'bot': ln['top']}
                notes.append(cur)
            elif cur and ln['x0'] <= 52:
                cur['t'] += ' ' + ln['text'].strip()
                cur['bot'] = ln['top']
            else:
                # button rows: only button labels allowed
                t = ln['text']
                for lab in sorted(list(BTN) + list(DERIVED) + ['NEARBY ›', 'POTA US-\\d+'], key=len, reverse=True):
                    t = re.sub(re.escape(lab) if '\\' not in lab else lab, '', t)
                if t.strip():
                    raise SystemExit(f'{code}: unexpected line {ln["text"]!r}')
        note_tops = [(n['top'] - 4, n['bot'] + 4) for n in notes]
        for l in btn_top:
            in_note = next((n for n, (a, b) in zip(notes, note_tops) if a <= l['top'] <= b), None)
            if in_note is not None:
                in_note.setdefault('links', []).append({'label': l['label'], 'url': l['uri']})
                continue
            lab = l['label']
            if lab == 'GPS':
                m = re.search(r'query=([-\d.]+),([-\d.]+)', l['uri'])
                gps = [float(m.group(1)), float(m.group(2))]
            elif lab in DERIVED:
                pass
            elif lab.startswith('POTA US-'):
                rec.setdefault('pota', []).append(lab[5:])
                assert l['uri'] == 'https://next.pota.app/park/' + lab[5:], l
            elif lab in BTN:
                btns.append({'k': BTN[lab], 'url': l['uri']})
            else:
                raise SystemExit(f'{code}: unknown button {lab!r} {l["uri"]}')
        if btns:
            rec['links'] = btns
        rec['gps'] = gps
        out_notes = []
        for n in notes:
            n['t'] = re.sub(r'\s+', ' ', n['t']).strip()
            if n['k'] == 'ALSO':
                rec['also'] = parse_also(n['t'])
                rec['alsoText'] = n['t']
                continue
            o = {'k': n['k'], 't': n['t']}
            if n.get('links'):
                o['links'] = n['links']
            out_notes.append(o)
        if out_notes:
            rec['notes'] = out_notes
        rec['pdfPage'] = c['page']
        if code in data:
            raise SystemExit('duplicate card ' + code)
        data[code] = rec
    pins = pdfcards.map_regions(PDF, cards)
    for code, reg in pins.items():
        data[code]['mapRegion'] = REGION_KEY[reg]   # region the PDF's regional map put the pin in
    missing = [c for c in data if 'mapRegion' not in data[c]]
    if missing:
        raise SystemExit('cards with no map pin: ' + ', '.join(missing))
    doc = {'source': os.path.basename(PDF), 'pages': npages, 'cards': len(data),
           'note': 'Extracted from the PDF by .claude/build/guides/extract_wwff.py. Codes, names, counties and GPS on the page come from kpc-ky-data.json.',
           'refs': data}
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', OUT, len(data), 'cards from', npages, 'pages')

if __name__ == '__main__':
    main()
