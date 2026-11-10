#!/usr/bin/env python3
"""Turn a research workbook into the research-inbox format (docs/research-input-format.md; Brandon t943u, Nov 9 2026).
Reads Brandon's no-ID lookup workbooks (sheets with FOUND_layer_or_service_url / FOUND_source_url_or_layer, FOUND_record_id,
owner_agency, confidence(high/med/low), notes) and the 'KPC held' style (pota_ref + 'held record ids', the layer read from the id's
prefix in data/us-key/layers.json). One CSV row per park. The pin columns are copied only as a fallback (the POTA pin in parkinfo wins).
  python3 .github/scripts/kpc_research_from_xlsx.py <book.xlsx> <out.csv> [--source TEXT] [--sheets US,Canada] [--conf high,med]"""
import csv, json, pathlib, re, sys
import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from kpc_research_inbox import COLS  # noqa: E402


def layer_fix(u, src=''):
    u = str(u or '').strip().split('?')[0].rstrip('/')
    u = re.sub(r'/query$', '', u)
    if re.search(r'/(FeatureServer|MapServer)$', u, re.I):          # a service, not a layer: WDPA's polygons are layer 1
        u += '/1' if re.search(r'wdpa|world_database_of_protected', u + src, re.I) else '/0'
    return u


def rid_fix(v):
    """one record id from the many ways a workbook writes it: 'PARK_SURVEY_ID 15 (OBJECTID 15)' -> 15, 'CPCAD 471000224' -> 471000224,
    'OBJECTID 394 / PASITES_ID 1039' -> 394, '5102 and 4147' -> '5102 4147'. The id is a hint only: the solver reads the layer at the pin."""
    s = str(v if v is not None else '').strip()
    if not s or re.fullmatch(r'[\w.-]+', s): return s
    m = re.search(r'OBJECTID\s*[:=]?\s*(\d+)', s, re.I)
    if m: return m.group(1)
    n = re.findall(r'\d+', s)
    return ' '.join(n) if n else s


def convert(book, out, source='', sheets=None, conf=None):
    wb = openpyxl.load_workbook(book, read_only=True, data_only=True)
    try: LJ = json.load(open(ROOT / 'data/us-key/layers.json', encoding='utf-8'))
    except Exception: LJ = {}  # noqa: BLE001
    rows = []
    for ws in wb.worksheets:
        if sheets and ws.title not in sheets: continue
        it = ws.iter_rows(values_only=True); H = next(it, None)
        if not H: continue
        H = {str(h).strip(): i for i, h in enumerate(H) if h}
        g = lambda r, *ks: next((r[H[k]] for k in ks if k in H and H[k] < len(r) and r[H[k]] not in (None, '')), '')
        if 'pota_ref' not in H: continue
        for r in it:
            ref = g(r, 'pota_ref')
            if not ref: continue
            c = str(g(r, 'confidence(high/med/low)', 'confidence')).strip().lower()
            if conf and c not in conf: continue
            if 'held record ids' in H:            # the 'KPC held (19)' style: ids with a layer prefix
                ids = [x.strip() for x in str(g(r, 'held record ids')).split(',') if x.strip()]
                pre = re.match(r'[a-z]+', ids[0]).group(0) if ids else ''
                lay = (LJ.get(pre) or [''])[0]
                rows.append({'pota_ref': ref, 'park_name': g(r, 'park_name'), 'layer_url': layer_fix(lay), 'record_id': ' '.join(re.sub(r'^[a-z]+', '', i) for i in ids),
                             'notes': g(r, 'KPC_reason'), 'source': source or f'{pathlib.Path(book).name} [{ws.title}]', 'confidence': 'held'})
                continue
            src = str(g(r, 'FOUND_source_name'))
            if 'case' in H and 'recommendation' in H:   # the t955u 'Solved cases' style (Brandon Nov 9): its verdict is a note, never trusted
                note = ' | '.join(x for x in [f"file verdict {g(r, 'verdict')} ({g(r, 'confidence')})", f"inside {g(r, 'inside')}" if g(r, 'inside') != '' else '',
                                               f"pin {g(r, 'pin_distance_km')} km" if g(r, 'pin_distance_km') != '' else '', str(g(r, 'case')),
                                               f"recommendation: {g(r, 'recommendation')}", f"lead: {g(r, 'lead')}" if g(r, 'lead') else '',
                                               f"raw record id: {g(r, 'record_id')}" if g(r, 'record_id') != '' else ''] if x)
                rows.append({'pota_ref': ref, 'park_name': g(r, 'park_name'), 'layer_url': layer_fix(g(r, 'layer_url')),
                             'record_id': rid_fix(g(r, 'record_id')), 'official_name': g(r, 'official_name'), 'owner': g(r, 'owner_agency'),
                             'confidence': c, 'notes': note[:2000], 'source': source or f'{pathlib.Path(book).name} [{ws.title}]',
                             'pin_lat': g(r, 'pota_lat'), 'pin_lon': g(r, 'pota_lon')})
                continue
            rows.append({'pota_ref': ref, 'park_name': g(r, 'park_name'),
                         'layer_url': layer_fix(g(r, 'FOUND_layer_or_service_url', 'FOUND_source_url_or_layer', 'layer_url'), src),
                         'record_id': str(g(r, 'FOUND_record_id', 'record_id')).strip(), 'official_name': src or g(r, 'official_name'),
                         'owner': g(r, 'owner_agency', 'owner'), 'confidence': c, 'notes': str(g(r, 'notes'))[:2000],
                         'source': source or f'{pathlib.Path(book).name} [{ws.title}]', 'pin_lat': g(r, 'pota_pin_lat', 'pin_lat'), 'pin_lon': g(r, 'pota_pin_lon', 'pin_lon')})
    with open(out, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); [w.writerow({k: r.get(k, '') for k in COLS}) for r in rows]
    print(f'{len(rows)} rows -> {out}')
    return rows


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    convert(a[0], a[1], opt('--source') or '', set(opt('--sheets').split(',')) if opt('--sheets') else None, set(opt('--conf').split(',')) if opt('--conf') else None)
