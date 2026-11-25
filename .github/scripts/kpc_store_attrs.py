#!/usr/bin/env python3
"""kpc_store_attrs.py (22 Nov 2026, owner: "agency id wouldnt that be the one for sure and the quickest"): the agency id
fields of every record the outline store holds, for the key's match checks in store mode. The saved copies the keys read
(boundary-cache, early November) were trimmed before the id fields were kept (keep-record-fields.json, 21 Nov), so the id
checks found almost nothing there. The store's own files keep each record's attributes; this tool takes from them ONLY the
fields the id checks read (the keep-list's fields, the link-id ties' fields, the Park Service unit code and the id kinds'
own fields) and writes one small file the key reads with KPC_RECORD_ATTRS:
    {"about": ..., "made": ..., "records": {record id as the key spells it: {field: value}}}
Record ids: a PAD-US record by its number, any other by its layer letters + number (sgtxd124), the same as the key.
Never a WDPA field. Reads files only; nothing is fetched.
  python kpc_store_attrs.py --store <store results folder> --out record-attrs.json.gz     (--selftest)"""
import argparse, datetime, glob, gzip, json, os, re, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WDPA = re.compile(r'wdpa', re.I)
MAX_TEXT = 300


def wanted_fields(gh=None):
    """Lower-case field names the id checks read."""
    gh = gh or os.path.join(HERE, '..')
    out = {'unit_code', 's_loc_nm', 'loc_nm', 'mang_name'}
    try:
        for v in (json.load(open(os.path.join(gh, 'keep-record-fields.json'))).get('layers') or {}).values():
            out |= {str(f).lower() for f in v.get('fields') or []}
    except (OSError, ValueError):
        pass
    try:
        for t in json.load(open(os.path.join(gh, 'link-id-ties.json'))).get('ties') or []:
            if t.get('field'): out.add(str(t['field']).lower())
    except (OSError, ValueError):
        pass
    try:
        sys.path.insert(0, HERE)
        import kpc_match_checks as MC
        for spec in MC.ID_KINDS.values():
            out |= {str(f).lower() for f in spec.get('sa') or ()}
    except Exception:  # noqa: BLE001
        pass
    return {f for f in out if f and not WDPA.search(f)}


def record_key(r):
    layer, rid = str(r.get('layer') or ''), str(r.get('record_id') or '')
    if layer == 'PAD-US':
        return rid if rid.isdigit() else ''
    # 24 Nov 2026 (owner 4:19 AM 'fix your part'): the store spells a state-layer record 'sgnya@68990'; the key spells it
    # 'sgnya68990'. The '@' made every state-layer record fall out (New York DEC: 1,161 records, 0 reached the id checks).
    k = str(r.get('key') or '').replace('@', '')
    return k if re.fullmatch(r'[a-z]+\d+', k) else ''


def name_key(s):
    """A record name for the name-and-size bridge: lower-case letters and digits only."""
    return re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def record_rings(r):
    """A store record's rings in degrees ([[[lon, lat], ...], ...]); [] when it has none. Store rings are q-digit integers:
    the first point, then steps."""
    rg = r.get('rings')
    if isinstance(rg, str):
        try: rg = json.loads(rg)
        except ValueError: return []
    try: q = 10 ** int(r.get('q') or 6)
    except (TypeError, ValueError): q = 10 ** 6
    out = []
    for ring in rg or []:
        if not isinstance(ring, list) or len(ring) < 2: continue
        x, y = ring[0], ring[1]; pts = [[x / q, y / q]]
        for i in range(2, len(ring) - 1, 2):
            x += ring[i]; y += ring[i + 1]; pts.append([x / q, y / q])
        if len(pts) >= 3: out.append(pts)
    return out


def record_box(r):
    """[minx, miny, maxx, maxy] of a store record's shape, rounded to 0.001 degree; None when the record has no rings.
    Exchange check 24 Nov: name + size alone hit the wrong piece of a many-piece park once in 1,101 New York bridges."""
    rs = record_rings(r)
    if not rs: return None
    xs = [p[0] for x in rs for p in x]; ys = [p[1] for x in rs for p in x]
    return [round(min(xs), 3), round(min(ys), 3), round(max(xs), 3), round(max(ys), 3)]


PAD_FIELDS = ('Unit_Nm', 'Loc_Nm', 'Own_Type', 'Own_Name', 'Loc_Own', 'Mang_Type', 'Mang_Name', 'Loc_Mang', 'Des_Tp', 'Loc_Ds',
              'Pub_Access', 'GIS_Acres', 'Category', 'FeatClass', 'Agg_Src', 'State_Nm', 'Unit_Code')
LIGHT_STEP = 0.00005     # 25 Nov (better matcher): about 5 m; enough to measure shared ground at 80% / 50%
LIGHT_MAX = 2000         # points per record at most (a bigger record is thinned more)


def light_rings(r):
    """25 Nov 2026 (owner 6:20 AM: 'the outlines overlap on the map (area overlap, not just bounding boxes)'): the record's
    outline, thinned (a point closer than LIGHT_STEP to the last kept one is dropped, more when it would pass LIGHT_MAX
    points), 5 decimals. Only for the key's same-land test (kpc_same_land.py); never drawn."""
    rs = record_rings(r)
    n = sum(len(x) for x in rs)
    step = LIGHT_STEP
    while True:
        out = []
        for ring in rs:
            kept = [ring[0]]
            for p in ring[1:-1]:
                if abs(p[0] - kept[-1][0]) >= step or abs(p[1] - kept[-1][1]) >= step: kept.append(p)
            kept.append(ring[-1])
            if len(kept) >= 4: out.append([[round(p[0], 5), round(p[1], 5)] for p in kept])
        if sum(len(x) for x in out) <= LIGHT_MAX or not n: return out
        step *= 2


def record_acres(r):
    a = r.get('attributes') or {}
    for k in ('GIS_Acres', 'ACRES', 'Acres', 'acres', 'GISACRES', 'Shape_Acres'):
        try:
            v = float(a.get(k))
            if v > 0: return v
        except (TypeError, ValueError):
            pass
    try:
        return float(((r.get('attrs') or {}).get('_norm') or {}).get('acres') or 0) or None
    except (TypeError, ValueError):
        return None


def run(store, out, gh=None, today=None):
    want = wanted_fields(gh)
    recs, files, by_name, refound = {}, 0, {}, {}
    manifest = {}
    paths_ = sorted(glob.glob(os.path.join(store, '*.kpcstore.json.gz'))) + sorted(glob.glob(os.path.join(store, '*.layer-records.json.gz')))
    for path in paths_:
        if '.prev.' in os.path.basename(path):
            continue
        files += 1
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            d = json.load(f)
        area = str(d.get('area') or re.sub(r'\.(kpcstore|layer-records)\.json\.gz$', '', os.path.basename(path)))
        # 25 Nov 2026 (format 8; KPC-Store kpc_layer_records.py, the owner's 8:21 AM fix): every record of every layer the keys
        # join, linked to a park or not, with a per-layer manifest (source count, store count, complete). The manifest goes along
        # so the key counts a layer as 'in the store' only when it is complete.
        if d.get('kpcstore_layers'):
            for lay, m in (d.get('manifest') or {}).items():
                manifest.setdefault(area, {})['padus' if lay == 'PAD-US' else lay] = {
                    'complete': bool(m.get('complete')), 'source_count': m.get('source_count'), 'store_count': m.get('store_count'), 'read': m.get('read')}
        groups = d.get('parks') or []
        if d.get('records'): groups = list(groups) + [{'records': d['records']}]
        for p in groups:
            for r in p.get('records') or []:
                k = record_key(r)
                if not k:
                    continue
                a = r.get('attributes') or {}
                got = {str(n): v for n, v in a.items() if str(n).lower() in want and v not in (None, '', ' ')
                       and isinstance(v, (str, int, float)) and not isinstance(v, bool) and len(str(v)) <= MAX_TEXT}
                # 25 Nov 2026 (format 6, the better matcher): every record also carries its name(s), size, box and a light outline,
                # so the key can PROVE which of its records is the same land (kpc_same_land.py) instead of trusting a row number.
                # Helper keys start with '_' and never reach the id checks.
                helper = {'_nm': str(r.get('record_name') or r.get('record_name_in_source') or '')}
                nms = sorted({str(x) for x in (r.get('record_name'), r.get('record_name_in_source'), r.get('tract_name')) if x} - {helper['_nm']})
                if nms: helper['_nms'] = nms
                if record_acres(r): helper['_ac'] = round(record_acres(r), 3)
                bx0 = record_box(r)
                if bx0: helper['_bx'] = bx0; helper['_g'] = light_rings(r)
                # 25 Nov 2026 (owner 7:18 AM: 'Use today's store records as the FRESH source for both matching and drawing'):
                # the area, the date the store read the record, and for PAD-US its own describing fields, so the key can
                # stand the fresh record in for its old saved copy (kpc_us_key fresh_records)
                if area: helper['_st'] = area
                if r.get('read'): helper['_rd'] = str(r.get('read'))[:10]
                if str(r.get('layer') or '') == 'PAD-US':
                    pad = {f: a.get(f) for f in PAD_FIELDS if a.get(f) not in (None, '')}
                    if pad: helper['_pad'] = pad
                if got or helper.get('_g'):
                    # 24 Nov 2026 (B1, #379): a re-found store record ('sgmnb@20') is not proven to be the key's record 20 (the
                    # agency renumbered its layer), nor the record the store's key_record_id names (that is the key's id when the
                    # STORE was built; the key's saved copy has been renumbered since: MN, 25 Nov 4:08 AM test). So it is kept
                    # apart ('refound') with its name, size and key_record_id, and the key takes its fields only for a saved record
                    # that is provably the same record (name + size). A plain record always wins.
                    kid = str(r.get('key_record_id') or '')
                    if '@' in str(r.get('key') or ''):
                        refound.setdefault(k, {}).update(dict(got, **helper, **({'_kid': kid} if re.fullmatch(r'[a-z]+\d+', kid) else {})))
                        k = k + '@'   # the bridge's entry for this record (below)
                    else:
                        recs.setdefault(k, {}).update(dict(got, **helper))
                    # 24 Nov: agencies renumber their records when they republish a layer (New York DEC between our early-
                    # November saved copies and the store's later read), so the record number alone cannot find a saved
                    # record's fields. Also index them by layer + name + size; the key takes a hit only when it is the ONE
                    # store record of that layer with that name and a size within 1% (kpc_us_key, 'store id fields by name').
                    ac = record_acres(r)
                    lay = re.match(r'[a-z]*', k).group(0)
                    if lay and ac:
                        bx = record_box(r)
                        for nm in {name_key(r.get('record_name')), name_key(r.get('record_name_in_source'))} - {''}:
                            by_name.setdefault(lay, {}).setdefault(nm, []).append([round(ac, 3), k] + ([bx] if bx else []))
    doc = {'about': 'Agency id fields of the outline store\'s records, for the key\'s match checks (kpc_store_attrs.py). '
                    'Only the fields the id checks read; never WDPA. Collects, does not decide.',
           'format': 8, 'manifest': manifest, 'refound': refound, 'made': today or datetime.date.today().isoformat(), 'store_files': files, 'records': recs,
           'by_name': {lay: {nm: [[x[0], x[1]] + ([list(x[2])] if x[2] else []) for x in sorted({(x[0], x[1], tuple(x[2]) if len(x) > 2 else ()) for x in v})]
                             for nm, v in d_.items()} for lay, d_ in by_name.items()}}
    tmp = out + '.tmp'
    with gzip.open(tmp, 'wt', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, out)
    print(f'Store id fields: {len(recs):,} records from {files} store files -> {out}')
    return 0


def selftest():
    with tempfile.TemporaryDirectory() as t:
        st = os.path.join(t, 'store'); os.mkdir(st)
        park = {'ref': 'K4-0001', 'records': [
            {'key': 'sgzza7', 'layer': 'sgzza', 'record_id': '7', 'attributes': {'URL': 'https://dec.ny.gov/lands/123.html', 'Notes': 'x' * 50, 'WDPA_Cd': 5}},
            {'key': 'sgzzb@8', 'layer': 'sgzzb', 'record_id': '8', 'record_name': 'Mud Lake Wildlife Area', 'attributes': {'URL': 'https://dec.ny.gov/lands/456.html', 'ACRES': 100.0}},
            {'key': 'sgzzc@30', 'layer': 'sgzzc', 'record_id': '30', 'key_record_id': 'sgzzc12', 'record_name': 'Alpha Forest', 'attributes': {'URL': 'https://example.org/alpha', 'ACRES': 50.0}},
            {'key': 'sgzzd@5', 'layer': 'sgzzd', 'record_id': '5', 'key_record_id': 'sgzzd9', 'attributes': {'URL': 'https://example.org/refound'}},
            {'key': 'sgzzd9', 'layer': 'sgzzd', 'record_id': '9', 'attributes': {'URL': 'https://example.org/plain'}},
            {'key': '3422', 'layer': 'PAD-US', 'record_id': '3422', 'attributes': {'Comments': 'parks.ca.gov/?page_id=9', 'Loc_Nm': 'TEST', 'GIS_Acres': 4}},
            {'key': 'point-circle', 'layer': 'point-circle', 'record_id': '', 'attributes': {'URL': 'x'}},
            {'key': 'sgzze@4', 'layer': 'sgzze', 'record_id': '4', 'record_name': 'Lost Valley Prairie', 'q': 6,
             'rings': [[-92830000, 44800000, 10000, 0, 0, 10000, -10000, 0, 0, -10000]], 'attributes': {'gis_acres': 216.0}}]}
        with gzip.open(os.path.join(st, 'US-ZZ.kpcstore.json.gz'), 'wt') as f: json.dump({'parks': [park]}, f)
        with gzip.open(os.path.join(st, 'US-ZZ.kpcstore.prev.json.gz'), 'wt') as f: json.dump({'parks': [{'records': [{'key': 'sgold1', 'layer': 'sgold', 'record_id': '1', 'attributes': {'URL': 'old'}}]}]}, f)
        with gzip.open(os.path.join(st, 'US-ZZ.layer-records.json.gz'), 'wt') as f:
            json.dump({'kpcstore_layers': 1, 'area': 'US-ZZ', 'manifest': {'fws': {'complete': True, 'source_count': 1, 'store_count': 1},
                                                                          'PAD-US': {'complete': False, 'source_count': 9, 'store_count': 2}},
                       'records': [{'key': 'fws4026', 'layer': 'fws', 'record_id': '4026', 'record_name': 'Rothi WPA', 'q': 6,
                                    'rings': [[-95800000, 46800000, 10000, 0, 0, 10000, -10000, 0, 0, -10000]], 'attributes': {}}]}, f)
        gh = os.path.join(t, 'gh'); os.mkdir(gh)
        json.dump({'layers': {'x': {'fields': ['Comments', 'WDPA_Cd']}}}, open(os.path.join(gh, 'keep-record-fields.json'), 'w'))
        json.dump({'ties': [{'field': 'URL'}]}, open(os.path.join(gh, 'link-id-ties.json'), 'w'))
        o = os.path.join(t, 'a.json.gz'); run(st, o, gh, '2026-11-22')
        d = json.load(gzip.open(o, 'rt'))
        plain = {k: {f: v for f, v in x.items() if not f.startswith('_')} for k, x in d['records'].items() if k != 'fws4026'}
        ok = plain == {'sgzza7': {'URL': 'https://dec.ny.gov/lands/123.html'}, '3422': {'Comments': 'parks.ca.gov/?page_id=9', 'Loc_Nm': 'TEST'},
                              'sgzzd9': {'URL': 'https://example.org/plain'}}   # B1: re-found records are never filed as plain ones
        ok = ok and {k: {f: x for f, x in v.items() if f not in ('_st', '_rd')} for k, v in d.get('refound', {}).items() if k != 'sgzze4'} == {'sgzzb8': {'URL': 'https://dec.ny.gov/lands/456.html', '_nm': 'Mud Lake Wildlife Area', '_ac': 100.0},
                                         'sgzzc30': {'URL': 'https://example.org/alpha', '_nm': 'Alpha Forest', '_ac': 50.0, '_kid': 'sgzzc12'},
                                         'sgzzd5': {'URL': 'https://example.org/refound', '_nm': '', '_kid': 'sgzzd9'}}
        ok = ok and d.get('format') == 8 and d['by_name'].get('sgzzb', {}).get('mudlakewildlifearea') == [[100.0, 'sgzzb8@']]
        ok = ok and d['by_name'].get('sgzzc', {}).get('alphaforest') == [[50.0, 'sgzzc30@']]
        e = d['refound'].get('sgzze4') or {}   # format 6: name, size, box and a light outline, for the same-land proof
        ok = ok and e.get('_nm') == 'Lost Valley Prairie' and e.get('_bx') == [-92.83, 44.8, -92.82, 44.81] and len((e.get('_g') or [[]])[0]) == 5
        ok = ok and d['manifest'] == {'US-ZZ': {'fws': {'complete': True, 'source_count': 1, 'store_count': 1, 'read': None},
                                                 'padus': {'complete': False, 'source_count': 9, 'store_count': 2, 'read': None}}}
        ok = ok and (d['records'].get('fws4026') or {}).get('_nm') == 'Rothi WPA'   # format 8: a layer record that no park links
        ok = ok and e.get('_st') == 'US-ZZ' and d['records']['3422'].get('_pad') == {'Loc_Nm': 'TEST', 'GIS_Acres': 4}   # format 7
    print('selftest', 'ALL PASS' if ok else 'FAIL ' + json.dumps(d['records']) + ' ' + json.dumps(d.get('refound')))
    return 0 if ok else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--store'); ap.add_argument('--out', default='record-attrs.json.gz'); ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run(a.store, a.out))
