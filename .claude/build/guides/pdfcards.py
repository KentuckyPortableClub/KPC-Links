"""Shared helpers: pull the summit / reference cards (text + link annotations) out of a KPC Resource PDF.
Used by extract_sota.py and extract_wwff.py. Needs pdfplumber."""
import re, pdfplumber

LINK_FIX = [('’', "'")]

def _label_of(page, h):
    box = (max(0, h['x0']), max(0, h['top']), min(page.width, h['x1']), min(page.height, h['bottom']))
    t = page.crop(box).extract_text() or ''
    return ' '.join(t.split())

def _split_bold(line):
    """Return (bold prefix, rest) of a text line, using the char font names."""
    chars = line['chars']
    i = 0
    while i < len(chars) and 'Bold' in chars[i]['fontname']:
        i += 1
    # line chars carry no spaces, so walk the line text consuming the bold chars
    full = line['text']
    bold_chars = ''.join(c['text'] for c in chars[:i])
    j = k = 0
    while k < len(bold_chars) and j < len(full):
        if full[j] == bold_chars[k]:
            k += 1
        j += 1
    return full[:j].strip(), full[j:].strip()

def cards(path, head_re, first_page=0, footer_y=760):
    """Yield one dict per card: code, page (1-based), lines [(x0, top, bold, rest, text)], links [(label, uri, top, x0)]."""
    rx = re.compile(head_re)
    pdf = pdfplumber.open(path)
    out = []
    for pi, page in enumerate(pdf.pages):
        if pi < first_page:
            continue
        links = [h for h in page.hyperlinks if h.get('uri')]
        heads = sorted([h for h in links if h['x0'] < 60 and rx.search(h['uri'])], key=lambda h: h['top'])
        if not heads:
            continue
        lines = page.extract_text_lines()
        for n, hd in enumerate(heads):
            top = hd['top'] - 2
            bot = heads[n + 1]['top'] - 2 if n + 1 < len(heads) else footer_y
            code = rx.search(hd['uri']).group(1)
            L = []
            for ln in lines:
                if top <= ln['top'] < bot:
                    b, r = _split_bold(ln)
                    L.append({'x0': round(ln['x0']), 'top': round(ln['top']), 'bold': b, 'rest': r, 'text': ln['text']})
            K = []
            for h in sorted([h for h in links if top <= h['top'] < bot], key=lambda h: (round(h['top']), h['x0'])):
                K.append({'label': _label_of(page, h), 'uri': h['uri'], 'top': round(h['top']), 'x0': round(h['x0'])})
            out.append({'code': code, 'page': pi + 1, 'lines': L, 'links': K})
    return out, len(pdf.pages)

def all_uris(path):
    pdf = pdfplumber.open(path)
    return [(i + 1, h['uri']) for i, p in enumerate(pdf.pages) for h in p.hyperlinks if h.get('uri')]

def map_regions(path, cards, title_prefix='REGIONAL MAP'):
    """Regional map pages: every pin is a GoTo link to a card. Returns {code: region heading} for the pins.
    The region name is the page's big heading (e.g. 'Bluegrass Region')."""
    import pypdf
    r = pypdf.PdfReader(path)
    pl = pdfplumber.open(path)
    pageno = {p.indirect_reference.idnum: i + 1 for i, p in enumerate(r.pages)}
    by_page = {}
    for c in cards:
        top = c['lines'][0]['top']
        by_page.setdefault(c['page'], []).append((top, c['code']))
    out = {}
    for i, page in enumerate(r.pages):
        lines = (pl.pages[i].extract_text() or '').split('\n')
        if not lines or not lines[0].startswith(title_prefix):
            continue
        region = lines[1].strip()
        for a in page.get('/Annots', []) or []:
            a = a.get_object()
            dest = a.get('/Dest')
            if not dest or len(dest) < 4 or dest[1] != '/XYZ':
                continue
            pg = pageno[dest[0].idnum]
            ytop = float(r.pages[pg - 1].mediabox.height) - float(dest[3])  # map pages are landscape; use the card page
            cands = sorted(by_page.get(pg, []), key=lambda t: abs(t[0] - ytop))
            if not cands or abs(cands[0][0] - ytop) > 40:
                raise SystemExit(f'map pin on page {i+1} -> page {pg} y {ytop}: no card')
            code = cands[0][1]
            if code in out and out[code] != region:
                raise SystemExit(f'{code} pinned in two regions')
            out[code] = region
    return out
