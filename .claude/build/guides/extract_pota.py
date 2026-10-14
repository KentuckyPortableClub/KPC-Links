"""Extract the per-park card details from the ORIGINAL (unpatched) Kentucky POTA Resource PDFs into kpc-guide-pota-data.json,
and sync the 2-fer / 3-fer data from .claude/build/fers/fers.json (the single source for those lines).
Run from the repo root:
  python3 .claude/build/guides/extract_pota.py [numerical.pdf alphabetical.pdf]
The originals are the versions from before commit 6411aa3 (the current PDFs have white-box overlays):
  git show 6411aa3^:KPC_Kentucky_POTA_Resource_Numerical_v2_261005_092033.pdf > /tmp/num.pdf   (same for the Alphabetical one)
Default paths: $KPC_POTA_ORIG_NUM / $KPC_POTA_ORIG_ALPHA, else /tmp/num.pdf and /tmp/alpha.pdf.

What goes in the JSON (keyed by POTA ref), everything else comes live from kpc-ky-data.json `parks`:
  pdfName, counties, type (as printed), nameUrl, btns (button row in PDF order; GPS/OSM/WEATHER/NEARBY are rebuilt
  from coordinates on the page), notes (labelled lines in PDF order; the old 2-FER / TRAIL 2-FER lines are replaced by a
  {"k":"2-FER"} placeholder because the text now comes from fers), also (printed ALSO line, for checking), mapRegion, short
  (the short name used in Nearby lists). US-0608 comes from .claude/build/add_park_card.py.
Also: wildRivers (pages 3-5 of the original), fers (index rows and per-park partner lines), unconfirmed pairs."""
import json, os, re, sys, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdfcards, pdfplumber

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(REPO, 'kpc-guide-pota-data.json')
NUM = sys.argv[1] if len(sys.argv) > 2 else os.environ.get('KPC_POTA_ORIG_NUM', '/tmp/num.pdf')
ALPHA = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('KPC_POTA_ORIG_ALPHA', '/tmp/alpha.pdf')
HEAD = r'next\.pota\.app/park/(US-\d+)$'
DERIVED = {'GPS', 'OSM BOUNDARY', 'WEATHER', 'NEARBY ›'}
BTN_LABELS = ['OFFICIAL MAP', 'AREA MAP', 'BROCHURE', 'GPS', 'OSM BOUNDARY', 'WEBSITE', 'POTA MAP', 'WILD RIVER MAP', 'ENTRANCE',
              'WEATHER', 'NEARBY ›', 'CAMPING ›', 'RESORT ›', 'CABINS ›']
NOTE_KEYS = ['TRAIL 2-FER PARKS', 'TRAIL 2-FER', '2-FER', 'ACCESS POINTS', 'ACCESS ADVISORY', 'PARKING (official page)', 'ALSO',
             'UTILITIES', 'NOTES', 'NPS KENTUCKY SITES']
REGION_KEY = {'Bluegrass Region': 'Bluegrass', 'Northern Kentucky Region': 'Northern Kentucky',
              'Eastern Kentucky (Appalachian / Eastern Coal Field)': 'Eastern Kentucky',
              'South Central / Pennyroyal Region': 'South Central Pennyroyal',
              'Western Kentucky (Western Coal Field)': 'Western Kentucky', 'Jackson Purchase Region': 'Jackson Purchase'}

def card_record(c):
    code, L, links = c['code'], c['lines'], c['links']
    assert L[0]['text'].startswith(code), (code, L[0]['text'])
    rec = {'pdfName': L[0]['text'][len(code):].strip()}
    sub = L[1]['text']
    i = 2
    while i < len(L) and L[i]['x0'] >= 130 and not L[i]['bold']:
        sub += ' ' + L[i]['text']; i += 1
    parts = sub.split(' • ')
    assert len(parts) == 2, (code, sub)
    rec['counties'] = re.sub(r' Count(y|ies)$', '', parts[0])
    rec['type'] = parts[1]
    assert links[0]['label'] == code
    if len(links) > 1 and links[1]['top'] == links[0]['top']:
        rec['nameUrl'] = links[1]['uri']
    notes, cur = [], None
    for ln in L[i:]:
        t = ln['text']
        if re.fullmatch(r'US-\d+000s|[A-Z]', t.strip()):
            continue  # section heading above the next card
        key = next((k for k in NOTE_KEYS if (t.startswith(k + ' ') or t == k) and ln['bold'].startswith(k)), None)
        if key:
            cur = {'k': key, 't': t[len(key):].strip(), 'top': ln['top'], 'bot': ln['top']}
            notes.append(cur)
        elif cur and ln['x0'] <= 52:
            cur['t'] += ' ' + t.strip(); cur['bot'] = ln['top']
        else:
            rest = t
            for lab in sorted(BTN_LABELS, key=len, reverse=True):
                rest = rest.replace(lab, '')
            if rest.strip():
                raise SystemExit(f'{code}: unexpected line {t!r}')
    btns, gps = [], None
    for l in links[2 if 'nameUrl' in rec else 1:]:
        n = next((n for n in notes if n['top'] - 4 <= l['top'] <= n['bot'] + 4), None)
        if n is not None:
            n.setdefault('links', []).append({'label': l['label'], 'url': l['uri']}); continue
        lab = l['label']
        if lab not in BTN_LABELS:
            raise SystemExit(f'{code}: unknown button {lab!r}')
        if lab == 'GPS':
            m = re.search(r'query=([-\d.]+),([-\d.]+)', l['uri']); gps = [float(m.group(1)), float(m.group(2))]
        btns.append([lab, None if lab in DERIVED else l['uri']])
    # NEARBY is an internal jump (no URI); put it back where the PDF draws it (just before CAMPING/RESORT/CABINS)
    k = next((j for j, b in enumerate(btns) if b[0] in ('CAMPING ›', 'RESORT ›', 'CABINS ›')), len(btns))
    btns.insert(k, ['NEARBY ›', None])
    rec['btns'], rec['gps'] = btns, gps
    out, had = [], False
    for n in notes:
        t = re.sub(r'\s+', ' ', n['t']).strip()
        if n['k'] in ('2-FER', 'TRAIL 2-FER', 'TRAIL 2-FER PARKS'):
            rec.setdefault('old2fer', []).append(n['k'] + ' ' + t)   # kept only for the record; the page uses fers
            if not had:
                out.append({'k': '2-FER'}); had = True
            continue
        if n['k'] == 'ALSO':
            rec['also'] = t
            ins = [x for part in t.split('|') if part.strip().startswith('SOTA inside') for x in re.findall(r'W4K/[A-Z]{2}-\d{3}', part)]
            if ins:
                rec['sotaInside'] = ins   # KY GIS 'inside' summits; WWFF list and SOTA within 3 mi are rebuilt live
            out.append({'k': 'ALSO'})
            continue
        o = {'k': n['k'], 't': t}
        if n.get('links'):
            o['links'] = n['links']
        out.append(o)
    rec['notes'] = out
    rec['pdfPage'] = c['page']
    return rec

def short_names(pdf):
    """Short park names as printed in the Nearby Parks lists ('Pine Mountain SP')."""
    txt = []
    on = False
    for p in pdfplumber.open(pdf).pages:
        t = p.extract_text() or ''
        if 'Nearby Parks' in t:
            on = True
        if on:
            txt.append(t)
    s = {}
    body = ' '.join(re.sub(r'\n', ' ', t) for t in txt)
    for m in re.finditer(r'(US-\d+) ([^•]+?) (\d+(?:\.\d)?) mi', body):
        nm = m.group(2).strip()
        if 'NEAREST FIRST' in nm or '‹ CARD' in nm:
            continue
        s.setdefault(m.group(1), nm)
    return s

def wild_rivers(pdf):
    """Kentucky Wild River Corridors (pages 3-5 of the original): numbered rivers with their details and links."""
    pl = pdfplumber.open(pdf)
    rivers, intro = [], {}
    for pi in range(2, 6):
        page = pl.pages[pi]
        lines = page.extract_text_lines()
        head = lines[0]['text']
        if 'WILD RIVERS' not in head and 'WILD RIVER DETAILS' not in head:
            continue
        if head.startswith('KENTUCKY WILD RIVERS •') and 'DETAILS' not in head:
            intro['mapTitle'] = lines[1]['text']; intro['mapSub'] = lines[2]['text']
            continue
        if 'DETAILS' in head and head.startswith('KENTUCKY'):
            t = []
            for ln in lines[2:]:
                if re.match(r'^\d\s', ln['text']):
                    break
                t.append(ln['text'])
            intro['detailsTitle'] = lines[1]['text']; intro['detailsText'] = ' '.join(t)
        links = [h for h in page.hyperlinks if h.get('uri')]
        cur = None
        for ln in lines:
            m = re.match(r'^(\d) (.+?) OFFICIAL PAGE →$', ln['text'])
            if m:
                cur = {'n': int(m.group(1)), 'name': m.group(2), 'top': ln['top'], 'lines': []}
                rivers.append(cur); continue
            if cur and ln['x0'] < 300 and not ln['text'].startswith('KPC KENTUCKY'):
                if re.match(r'^(COUNTIES|CROSS-REFERENCE)', ln['text']) or not cur['lines']:
                    cur['lines'].append(ln['text'])
                else:
                    cur['lines'][-1] += ' ' + ln['text']
            cur and cur.setdefault('bot', ln['top'])
            if cur:
                cur['bot'] = ln['top']
        for r in rivers:
            if 'links' in r or r.get('_p') not in (None, pi):
                continue
            r['_p'] = pi
            r['links'] = []
            for h in links:
                if r['top'] - 4 <= h['top'] <= r.get('bot', r['top']) + 4:
                    lab = ' '.join((page.crop((h['x0'], h['top'], h['x1'], h['bottom'])).extract_text() or '').split())
                    r['links'].append({'label': lab, 'url': h['uri']})
    out = []
    for r in rivers:
        d = {'n': r['n'], 'name': r['name']}
        for l in r['lines']:
            if l.startswith('COUNTIES'):
                m = re.match(r'COUNTIES (.+?) • ACRES ([\d,]+) • OWNERSHIP (.+?) • MANAGED BY (.+)$', l)
                d['counties'], d['acres'], d['owner'], d['manager'] = m.groups()
            elif l.startswith('CROSS-REFERENCE'):
                d['xref'] = l[len('CROSS-REFERENCE '):]
        d['official'] = next(l['url'] for l in r['links'] if l['label'].startswith('OFFICIAL PAGE'))
        d['xlinks'] = [l for l in r['links'] if not l['label'].startswith('OFFICIAL PAGE')]
        out.append(d)
    return intro, out

def page_links(pdf, pages):
    pl = pdfplumber.open(pdf)
    res = []
    for pi in pages:
        p = pl.pages[pi]
        for h in p.hyperlinks:
            if h.get('uri'):
                lab = ' '.join((p.crop((max(0, h['x0']), max(0, h['top']), min(p.width, h['x1']), min(p.height, h['bottom']))).extract_text() or '').split())
                res.append({'page': pi + 1, 'label': lab, 'url': h['uri']})
    return res

def fers_data():
    """Copy what the public Resource PDFs show from fers.json (resource_patch.py rules). The members-only details
    (parking pins, notes, trips) stay out."""
    F = json.load(open(os.path.join(REPO, '.claude', 'build', 'fers', 'fers.json'), encoding='utf-8'))
    SP = F['spots']
    # same rules as resource_patch.py (sec / guidept / partner tags), kept in step by hand
    def sec(d):
        if d['type'] == '3-fer': return 0
        if 'Historic Trail site' in d['how'] or 'auto tour route' in d['how']: return 1
        if 'Water Route bank' in d['how']: return 3
        if 'riverbank' in d['how'].lower(): return 2
        if 'through the park' in d['how']: return 4
        return 5
    def guidept(d):
        return next((p for p in d['points'] if not p['what'].lower().startswith(('parking', 'drive up'))), d['points'][0])
    rows = []
    for d in SP:
        p = guidept(d)
        s = sec(d)
        tag = ''
        if s == 1 and 'US-1252' not in d['refs']: tag = ' (NOT within 100 ft of the river; NPS-listed site)'
        elif s == 3: tag = ' (Water Route shore, within 100 ft of the water)'
        elif s == 2: tag = ' (riverbank, within 100 ft of the water)'
        rows.append({'type': d['type'], 'sec': s, 'refs': d['refs'], 'names': d['names'], 'county': d['county'],
                     'pin': [p['la'], p['lo']], 'pinWhat': 'approximate riverbank' if 'riverbank' in p['what'].lower() else p['what'][:34].lower(),
                     'tag': tag})
    return {'updated': F.get('updated'), 'sections': ['3-Fers', 'Historic trail sites (visitor centers, certified sites, auto tour route)',
            'Ohio River banks (Lewis & Clark)', 'Trail of Tears Water Route (Kentucky Lake & Mississippi River)', 'Trail 2-fers', 'Shared boundaries'],
            'spots': rows, 'unconfirmed': F['unconfirmed']}

def us0608():
    spec = importlib.util.spec_from_file_location('add_park_card', os.path.join(REPO, '.claude', 'build', 'add_park_card.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    P = m.PARK
    counties, typ = P['sub'].split(' • ')
    btns = []
    for lab, url, st in P['buttons']:
        btns.append([lab, None if lab in DERIVED else url])
    btns.insert(len(btns), ['NEARBY ›', None])
    notes = []
    for lab, parts in P['lines']:
        if lab == '2-FER':
            notes.append({'k': '2-FER'}); continue
        t = ''.join(p[0] for p in parts).strip()
        o = {'k': lab, 't': t}
        lk = [{'label': p[0].strip(), 'url': p[2]} for p in parts if p[2]]
        if lab == 'ALSO':
            notes.append({'k': 'ALSO', 'links': lk}); continue
        if lk: o['links'] = lk
        notes.append(o)
    return {'pdfName': P['name'], 'counties': re.sub(r' Count(y|ies)$', '', counties), 'type': typ,
            'nameUrl': 'https://www.fws.gov/refuge/ohio-river-islands', 'btns': btns, 'gps': [m.LA, m.LO], 'notes': notes,
            'also': ''.join(p[0] for p in dict(P['lines'])['ALSO']), 'source': '.claude/build/add_park_card.py'}

def main():
    data = {}
    for which, pdf in (('num', NUM), ('az', ALPHA)):
        cards, npages = pdfcards.cards(pdf, HEAD)
        pins = pdfcards.map_regions(pdf, cards)
        for c in cards:
            rec = card_record(c)
            rec['mapRegion'] = REGION_KEY[pins[c['code']]] if c['code'] in pins else None
            if which == 'num':
                if c['code'] in data: raise SystemExit('duplicate ' + c['code'])
                data[c['code']] = rec
            else:
                a = data.get(c['code'])
                if a is None: raise SystemExit('A-Z only card ' + c['code'])
                diff = [k for k in rec if k not in ('pdfPage', 'mapRegion') and rec[k] != a[k]]
                if diff: print('A-Z card differs from numerical:', c['code'], diff)
                a['pdfPageAZ'] = c['page']
                if not a['mapRegion']: a['mapRegion'] = rec['mapRegion']
        print(which, len(cards), 'cards,', len(pins), 'map pins,', npages, 'pages')
    data['US-0608'] = us0608()
    sh = short_names(NUM)
    for k, v in sh.items():
        if k in data: data[k]['short'] = v
    intro, rivers = wild_rivers(NUM)
    doc = {'source': ['KPC_Kentucky_POTA_Resource_Numerical_v2_261005_092033.pdf', 'KPC_Kentucky_POTA_Resource_Alphabetical_v2_261005_092105.pdf'],
           'note': 'Built by .claude/build/guides/extract_pota.py from the original (pre-6411aa3) PDFs plus fers.json. Park codes, names, counties, coordinates and KFF/SOTA lists on the page come from kpc-ky-data.json.',
           'cards': len(data), 'parks': data, 'wildIntro': intro, 'wildRivers': rivers,
           'introLinks': page_links(NUM, [0, 1]), 'fers': fers_data()}
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', OUT, len(data), 'cards;', len(rivers), 'wild rivers;', len(doc['fers']['spots']), '2-fer/3-fer spots')

def fers_only():
    """Refresh just the 2-fer/3-fer data in kpc-guide-pota-data.json from fers.json (no PDFs needed)."""
    doc = json.load(open(OUT, encoding='utf-8'))
    doc['fers'] = fers_data()
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('refreshed fers in', OUT, len(doc['fers']['spots']), 'spots')

if __name__ == '__main__':
    fers_only() if '--fers' in sys.argv else main()
