"""Adds the US-0608 Ohio River Islands NWR card to both Kentucky POTA Resource PDFs without a full rebuild.
Numerical: new page after the US-0000s page that ends with US-0538 (Reelfoot).
Alphabetical: the page with Obion Creek / Old Fort Harrod gets Old Fort Harrod moved to a new page,
which shows Ohio River Islands first, then Old Fort Harrod (keeps A-Z order).
Also bumps the Find a Park counts: US-0000s 7 -> 8 (numerical), O 5 -> 6 (alphabetical).
Usage (repo root): python3 .claude/build/add_park_card.py   (run once; it refuses if US-0608 already has a card)"""
import io, re, subprocess
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import DecodedStreamObject, NameObject, ArrayObject, DictionaryObject, FloatObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

FD = '/usr/share/fonts/truetype/crosextra/'
for n, f in [('Car', 'Carlito-Regular'), ('CarB', 'Carlito-Bold'), ('CalB', 'Caladea-Bold')]:
    pdfmetrics.registerFont(TTFont(n, FD + f + '.ttf'))
sw = pdfmetrics.stringWidth
W, H = 612, 792
BG, WHITE, GOLD, DARK, OSM, WEB, INK, MUTED, LINE, LABEL, KFF = (HexColor(x) for x in
    ['#f6f1e4', '#ffffff', '#e9a820', '#12291e', '#2d6a4f', '#1b4332', '#1b1f1a', '#5c6360', '#ddd5c2', '#1b4332', '#2d6a4f'])
WXF, WXS, NBF = HexColor('#e7eef5'), HexColor('#9db7d1'), HexColor('#fff4d6')

LA, LO = 38.68733, -83.58048
PARK = {
 'ref': 'US-0608', 'name': 'Ohio River Islands National Wildlife Refuge', 'sub': 'Lewis County • National Wildlife Refuge',
 'buttons': [('OFFICIAL MAP', 'https://www.fws.gov/refuge/ohio-river-islands/visit-us', 'off'),
             ('GPS', f'https://www.google.com/maps/search/?api=1&query={LA},{LO}', 'out'),
             ('OSM BOUNDARY', f'https://www.openstreetmap.org/?mlat={LA}&mlon={LO}#map=13/{LA}/{LO}', 'osm'),
             ('WEBSITE', 'https://www.fws.gov/refuge/ohio-river-islands', 'web'),
             ('WEATHER', f'https://weather.com/weather/today/l/{LA},{LO}', 'wx'),
             ('NPS LEWIS & CLARK', 'https://www.nps.gov/lecl/planyourvisit/visitor-centers-in-kentucky.htm', 'nb')],
 'lines': [('2-FER', [('US-4572 ', KFF, 'https://pota.app/#/park/US-4572'), ('Lewis and Clark National Historic Trail — the islands are in the Ohio River, and the NPS lists the refuge on its Lewis & Clark Visitor Centers in Kentucky page. GPS guide pins in the 2-Fers & 3-Fers Index; do your own research.', INK, None)]),
           ('ACCESS', [('BOAT ACCESS ONLY. ', INK, None), ('Kentucky part: Manchester 1 Island (20 acres) and Manchester 2 Island (94 acres), Ohio River mile 395. Nearest public ramp: Manchester, Ohio (Island Creek, SR 52). Watch for steep banks and rock dikes when landing.', INK, None)]),
           ('ALSO', [('WWFF: ', INK, None), ('KFF-0608', KFF, 'https://wwff.co/directory/?showRef=KFF-0608')]),
           ('NOTES', [('Open 1 hour before sunrise to 1 hour after sunset. No camping, fires or overnight mooring. Kentucky hunting seasons apply. The refuge spans PA, WV, OH and KY, so it is not an ATNO for most hunters.', INK, None)])]}

def spaced_w(t, f, s, g): return sum(sw(ch, f, s) + g for ch in t) - g
def spaced(c, x, y, t, f, s, g):
    for ch in t: c.setFont(f, s); c.drawString(x, y, ch); x += sw(ch, f, s) + g

def card_overlay(top):
    """Draws the card with its top edge at `top` (points from the page top). Returns (pdf bytes, links, bottom)."""
    links = []; buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(W, H))
    T = H - top
    # body lines first (to know the height)
    tw = 572 - 50 - 12; rows = []
    for lab, parts in PARK['lines']:
        words = []
        for txt, col, url in parts:
            for wd in re.findall(r'\S+\s*', txt): words.append((wd, col, url, 'CarB' if txt.startswith('BOAT ACCESS ONLY') or url else 'Car'))
        x0 = sw(lab + ' ', 'CarB', 9); line = []; x = x0; cur = []
        for wd, col, url, fnt in words:
            w = sw(wd.rstrip(), fnt, 9)
            if x + w > tw and cur: rows.append((lab if not line else '', cur)); line.append(1); cur = []; x = 0
            cur.append((x, wd, col, url, fnt)); x += sw(wd, fnt, 9)
        rows.append((lab if not line else '', cur)); rows.append(None)
    body_h = sum(12 if r else 4.5 for r in rows)
    h = 72 + body_h + 4
    c.setFillColor(WHITE); c.setStrokeColor(LINE); c.setLineWidth(1); c.roundRect(40, T - h, 532, h, 8, stroke=1, fill=1)
    # ref pill
    c.setFillColor(GOLD); c.roundRect(50, T - 25.5, 76, 16, 8, stroke=0, fill=1)
    c.setFillColor(INK); w = spaced_w(PARK['ref'], 'CarB', 7.4, .9); spaced(c, 88 - w / 2, T - 20, PARK['ref'], 'CarB', 7.4, .9)
    links.append(((50, T - 25.5, 126, T - 9.5), 'https://next.pota.app/park/' + PARK['ref']))
    c.setFillColor(INK); c.setFont('CalB', 15); c.drawString(136, T - 23.5, PARK['name'])
    links.append(((136, T - 25.5, 572, T - 9.5), 'https://www.fws.gov/refuge/ohio-river-islands'))
    c.setFillColor(MUTED); c.setFont('Car', 9.4); c.drawString(136, T - 37.5, PARK['sub'])
    x = 50; yb = T - 66.5
    for lab, url, st in PARK['buttons']:
        bw = 66.6 if spaced_w(lab, 'CarB', 6.4, .8) < 56 else spaced_w(lab, 'CarB', 6.4, .8) + 18
        fill, stroke, tc = {'off': (DARK, GOLD, GOLD), 'out': (WHITE, DARK, INK), 'osm': (OSM, None, WHITE), 'web': (WEB, None, WHITE), 'wx': (WXF, WXS, HexColor('#2a4a6b')), 'nb': (NBF, GOLD, INK)}[st]
        c.setFillColor(fill)
        if stroke: c.setStrokeColor(stroke); c.setLineWidth(1.1)
        c.roundRect(x, yb, bw, 18, 9, stroke=1 if stroke else 0, fill=1)
        c.setFillColor(tc); w = spaced_w(lab, 'CarB', 6.4, .8); spaced(c, x + bw / 2 - w / 2, yb + 6.4, lab, 'CarB', 6.4, .8)
        links.append(((x, yb, x + bw, yb + 18), url)); x += bw + 5
    y = T - 80.5
    for r in rows:
        if r is None: y -= 4.5; continue
        lab, cur = r
        if lab: c.setFillColor(LABEL); c.setFont('CarB', 9); c.drawString(50, y, lab)
        off = 50 + (sw(lab + ' ', 'CarB', 9) if lab else 0) if False else 50
        for xx, wd, col, url, fnt in cur:
            xx_abs = 50 + xx
            c.setFillColor(col); c.setFont(fnt, 9); c.drawString(xx_abs, y, wd)
            if url: links.append(((xx_abs, y - 2, xx_abs + sw(wd.rstrip(), fnt, 9), y + 8), url))
        y -= 12
    c.showPage(); c.save()
    return buf.getvalue(), links, top + h

def rects_pdf(rects, color=BG):
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(W, H)); c.setFillColor(color)
    for x0, top0, x1, top1 in rects: c.rect(x0, H - top1, x1 - x0, top1 - top0, stroke=0, fill=1)
    c.showPage(); c.save(); return PdfReader(io.BytesIO(buf.getvalue())).pages[0]
def text_pdf(items):
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(W, H))
    for kind, *a in items:
        if kind == 'rect': x0, top0, x1, top1, col = a; c.setFillColor(col); c.rect(x0, H - top1, x1 - x0, top1 - top0, stroke=0, fill=1)
        else: x, base_top, t, f, s, col = a; c.setFillColor(col); c.setFont(f, s); c.drawString(x, H - base_top, t)
    c.showPage(); c.save(); return PdfReader(io.BytesIO(buf.getvalue())).pages[0]
def drop_annots(page, keep):
    if '/Annots' not in page: return
    page[NameObject('/Annots')] = ArrayObject([a for a in page['/Annots'] if keep([float(v) for v in a.get_object()['/Rect']])])
def add_links(writer, page, links):
    arr = page.get('/Annots') or ArrayObject()
    for (x0, y0, x1, y1), url in links:
        d = DictionaryObject({NameObject('/Type'): NameObject('/Annot'), NameObject('/Subtype'): NameObject('/Link'),
                              NameObject('/Rect'): ArrayObject([FloatObject(v) for v in (x0, y0, x1, y1)]), NameObject('/Border'): ArrayObject([FloatObject(0)] * 3),
                              NameObject('/A'): DictionaryObject({NameObject('/S'): NameObject('/URI'), NameObject('/URI'): __import__('pypdf').generic.TextStringObject(url)})})
        arr.append(writer._add_object(d))
    page[NameObject('/Annots')] = arr
def copy_annots(writer, frompage, topage, keep, dy=0):
    arr = topage.get('/Annots') or ArrayObject()
    for a in frompage.get('/Annots') or []:
        a = a.get_object(); r = [float(v) for v in a['/Rect']]
        if not keep(r): continue
        d = DictionaryObject({k: v for k, v in a.items() if k != '/P'})
        d[NameObject('/Rect')] = ArrayObject([FloatObject(r[0]), FloatObject(r[1] + dy), FloatObject(r[2]), FloatObject(r[3] + dy)])
        arr.append(writer._add_object(d))
    topage[NameObject('/Annots')] = arr
def has_card(path):
    t = subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True, text=True).stdout
    return 'Ohio River Islands National Wildlife Refuge' in t and re.search(r'US-0608\s+Ohio River Islands', t) is not None

def numerical(path):
    rd = PdfReader(path); wr = PdfWriter(clone_from=rd)
    pi = next(i for i, p in enumerate(rd.pages) if 'US-0538' in (p.extract_text() or '') and 'Reelfoot' in (p.extract_text() or ''))
    # new page: a fresh copy of that page (header, banner, footer), body covered, card drawn
    src = PdfReader(path).pages[pi]
    wr.insert_page(src, index=pi + 1); np_ = wr.pages[pi + 1]
    np_.merge_page(rects_pdf([(0, 80, W, 764)]))
    np_[NameObject('/Annots')] = ArrayObject(); copy_annots(wr, wr.pages[pi], np_, lambda r: r[1] > H - 80 or r[3] < 30)
    data, links, bottom = card_overlay(92)
    np_.merge_page(PdfReader(io.BytesIO(data)).pages[0]); add_links(wr, np_, links)
    # Find a Park: US-0000s count 7 -> 8
    p2 = wr.pages[1]
    p2.merge_page(text_pdf([('rect', 88.4, 204.2, 92.9, 212.0, WHITE), ('text', 88.9, 209.6, '8', 'CarB', 6.8, MUTED)]))
    return wr, pi + 2

def alphabetical(path):
    rd = PdfReader(path); wr = PdfWriter(clone_from=rd)
    pi = next(i for i, p in enumerate(rd.pages) if 'Obion Creek' in (p.extract_text() or '') and 'Old Fort Harrod' in (p.extract_text() or ''))
    t = subprocess.run(['pdftotext', '-bbox', '-f', str(pi + 1), '-l', str(pi + 1), path, '-'], capture_output=True, text=True).stdout
    m = re.search(r'yMin="([\d.]+)"[^>]*>Old</word>\s*<word[^>]*>Fort</word>', t); oftitle = float(m.group(1))
    ctop, cbot = oftitle - 12, oftitle + 82          # Old Fort Harrod card: about 605.5-698.5 from the page top
    # new page after it: header/footer copy, Ohio River Islands card, then Old Fort Harrod moved up under it
    src = PdfReader(path).pages[pi]
    wr.insert_page(src, index=pi + 1); np_ = wr.pages[pi + 1]
    np_.merge_page(rects_pdf([(0, 80, W, 764)]))
    drop_annots(np_, lambda r: r[1] > H - 80 or r[3] < 30)
    data, links, bottom = card_overlay(92)
    np_.merge_page(PdfReader(io.BytesIO(data)).pages[0])
    newtop = bottom + 8.5; dy = ctop - newtop       # move up by dy points
    card = PdfReader(path).pages[pi]
    clip = f'q 38 {H - cbot - 1:.2f} 536 {cbot - ctop + 2:.2f} re W n\n'.encode()
    s = DecodedStreamObject(); s.set_data(clip + card.get_contents().get_data() + b'\nQ\n')
    card.replace_contents(s)
    np_.merge_transformed_page(card, Transformation().translate(0, dy))
    # links on the new page: header (logo), the new card, and Old Fort Harrod's buttons moved up (internal jumps kept)
    np_[NameObject('/Annots')] = ArrayObject()
    copy_annots(wr, wr.pages[pi], np_, lambda r: r[1] > H - 80 or r[3] < 30)
    add_links(wr, np_, links)
    copy_annots(wr, wr.pages[pi], np_, lambda r: H - cbot <= r[1] <= H - ctop, dy=dy)
    # old page: cover Old Fort Harrod and drop its links (they now live on the new page)
    op = wr.pages[pi]
    op.merge_page(rects_pdf([(36, ctop - 2, 576, cbot + 2)]))
    drop_annots(op, lambda r: not (H - cbot <= r[1] <= H - ctop))
    # Find a Park: O count 5 -> 6
    p2 = wr.pages[1]
    p2.merge_page(text_pdf([('rect', 247.4, 295.6, 251.6, 303.2, WHITE), ('text', 247.85, 301.0, '6', 'CarB', 6.8, MUTED)]))
    return wr, pi + 2

if __name__ == '__main__':
    import sys
    for path, fn in [('KPC_Kentucky_POTA_Resource_Numerical_v2_261005_092033.pdf', numerical), ('KPC_Kentucky_POTA_Resource_Alphabetical_v2_261005_092105.pdf', alphabetical)]:
        if has_card(path): print(path, 'already has a US-0608 card; skipped'); continue
        wr, newpage = fn(path)
        out = sys.argv[1] + '/' + path if len(sys.argv) > 1 else path
        wr.write(out); print(path, '-> new card on page', newpage, '->', out)
