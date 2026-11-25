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


def record_box(r):
    """[minx, miny, maxx, maxy] of a store record's shape (rings are q-digit integers, first point then steps), rounded to
    0.001 degree; None when the record has no rings. Exchange check 24 Nov: name + size alone hit the wrong piece of a
    many-piece park once in 1,101 New York bridges; the box must also overlap."""
    rg = r.get('rings')
    if isinstance(rg, str):
        try: rg = json.loads(rg)
        except ValueError: return None
    try: q = 10 ** int(r.get('q') or 6)
    except (TypeError, ValueError): q = 10 ** 6
    xs, ys = [], []
    for ring in rg or []:
        if not isinstance(ring, list) or len(ring) < 2: continue
        x, y = ring[0], ring[1]; xs.append(x); ys.append(y)
        for i in range(2, len(ring) - 1, 2):
            x += ring[i]; y += ring[i + 1]; xs.append(x); ys.append(y)
    if not xs: return None
    return [round(min(xs) / q, 3), round(min(ys) / q, 3), round(max(xs) / q, 3), round(max(ys) / q, 3)]


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
    recs, files, by_name, exact, refound = {}, 0, {}, {}, {}
    for path in sorted(glob.glob(os.path.join(store, '*.kpcstore.json.gz'))):
        if '.prev.' in os.path.basename(path):
            continue
        files += 1
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            d = json.load(f)
        for p in d.get('parks') or []:
            for r in p.get('records') or []:
                k = record_key(r)
                if not k:
                    continue
                a = r.get('attributes') or {}
                got = {str(n): v for n, v in a.items() if str(n).lower() in want and v not in (None, '', ' ')
                       and isinstance(v, (str, int, float)) and not isinstance(v, bool) and len(str(v)) <= MAX_TEXT}
                if got:
                    # 24 Nov 2026 (B1, #379): a re-found store record ('sgmnb@20') is NOT the key's record 20: the agency
                    # renumbered its layer. The store names the key's own old id for it (key_record_id): its fields go there,
                    # exactly. With no key_record_id, they are kept apart ('refound') with the record's name and size, and the key
                    # takes them only when its own saved record of that number is the same record. A plain record always wins.
                    kid = str(r.get('key_record_id') or '')
                    if '@' in str(r.get('key') or ''):
                        if re.fullmatch(r'[a-z]+\d+', kid):
                            exact.setdefault(kid, {}).update(got)
                        else:
                            refound.setdefault(k, {}).update(dict(got, _nm=str(r.get('record_name') or r.get('record_name_in_source') or ''),
                                                                   **({'_ac': round(record_acres(r), 3)} if record_acres(r) else {})))
                        k = kid if re.fullmatch(r'[a-z]+\d+', kid) else k + '@'   # the bridge's entry for this record (below)
                    else:
                        recs.setdefault(k, {}).update(got)
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
    clash = sorted(set(exact) & set(recs))   # a plain record and a re-found one both claim the key's id: neither is trusted
    for kid in clash: recs.pop(kid, None)
    for kid, got in exact.items():
        if kid not in clash: recs[kid] = got
    doc = {'about': 'Agency id fields of the outline store\'s records, for the key\'s match checks (kpc_store_attrs.py). '
                    'Only the fields the id checks read; never WDPA. Collects, does not decide.',
           'format': 4, 'refound': refound, 'exact_from_refound': len(exact) - len(clash), 'clash': clash, 'made': today or datetime.date.today().isoformat(), 'store_files': files, 'records': recs,
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
            {'key': 'point-circle', 'layer': 'point-circle', 'record_id': '', 'attributes': {'URL': 'x'}}]}
        with gzip.open(os.path.join(st, 'US-ZZ.kpcstore.json.gz'), 'wt') as f: json.dump({'parks': [park]}, f)
        with gzip.open(os.path.join(st, 'US-ZZ.kpcstore.prev.json.gz'), 'wt') as f: json.dump({'parks': [{'records': [{'key': 'sgold1', 'layer': 'sgold', 'record_id': '1', 'attributes': {'URL': 'old'}}]}]}, f)
        gh = os.path.join(t, 'gh'); os.mkdir(gh)
        json.dump({'layers': {'x': {'fields': ['Comments', 'WDPA_Cd']}}}, open(os.path.join(gh, 'keep-record-fields.json'), 'w'))
        json.dump({'ties': [{'field': 'URL'}]}, open(os.path.join(gh, 'link-id-ties.json'), 'w'))
        o = os.path.join(t, 'a.json.gz'); run(st, o, gh, '2026-11-22')
        d = json.load(gzip.open(o, 'rt'))
        ok = d['records'] == {'sgzza7': {'URL': 'https://dec.ny.gov/lands/123.html'}, '3422': {'Comments': 'parks.ca.gov/?page_id=9', 'Loc_Nm': 'TEST'},
                              'sgzzc12': {'URL': 'https://example.org/alpha'}}   # B1: a re-found record's fields go to the key's own id
        ok = ok and d.get('refound') == {'sgzzb8': {'URL': 'https://dec.ny.gov/lands/456.html', '_nm': 'Mud Lake Wildlife Area', '_ac': 100.0}}
        ok = ok and d.get('clash') == ['sgzzd9']   # a plain and a re-found record claim one id: neither is trusted
        ok = ok and d.get('format') == 4 and d['by_name'].get('sgzzb', {}).get('mudlakewildlifearea') == [[100.0, 'sgzzb8@']]
        ok = ok and d['by_name'].get('sgzzc', {}).get('alphaforest') == [[50.0, 'sgzzc12']]
    print('selftest', 'ALL PASS' if ok else 'FAIL ' + json.dumps(d['records']))
    return 0 if ok else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--store'); ap.add_argument('--out', default='record-attrs.json.gz'); ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run(a.store, a.out))
