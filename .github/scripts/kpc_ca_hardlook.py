#!/usr/bin/env python3
"""Canada HARD LOOK -> the Canada key (chat 2, Nov 2 2026; chat 10 Nov 1 12:30 AM + Brandon 'do it'). Chat 11's YES rows in KPC-Data
data/waiting/questions/hardlook.json name the exact official layer + record for a Canadian park ('OBJECTID 1649', 'FID 1',
'OGF_ID 450757661 ...', "property_number=00345 (objectid 48)"). The Canada answers bot never read this file (it reads 'questions', this
file has 'rows'), so none of them reached the key. This writes data/ca-key/hardlook-joins.json {rows: [{ref, url, oid | where,
name_field, record_name, names}]}; kpc_ca_key.py reads each record by id and joins it to its park when the key found nothing else.
Only YES answers (first word); NOT SURE / NO / blank never. No network. Exit 0 always."""
import ast, json, os, pathlib, re, sys


def main():
    D = pathlib.Path(os.environ.get('DATA') or 'kpcdata')
    src = D / 'data/waiting/questions/hardlook.json'
    try: R = json.load(open(src, encoding='utf-8')).get('rows') or {}
    except Exception as e: print(f'::notice title=Canada hard look::{src} not read: {e}'); return  # noqa: BLE001
    rows = list(R.values()) if isinstance(R, dict) else R
    out, skip = [], 0
    for r in rows:
        ref = str(r.get('ref') or '')
        if not ref.startswith('CA-') or not re.match(r'\W*YES\b', str(r.get('answer') or ''), re.I): continue
        url = str(r.get('url') or '').strip().rstrip('/')
        if not re.search(r'/(MapServer|FeatureServer)/\d+$', url): skip += 1; continue
        rg = str(r.get('record_given') or '')
        # Nov 2 evening (Mapping; quality notes 2026-11-02): "objectid 4691 / property_number 56474 'Butler's Barracks …'" gave the
        # name 'Butler' (the apostrophe ended the quote) and the join used only the objectid, which DFRP has since renumbered.
        # Now: the name is the quoted text up to the closing quote before '(' / end, or the text after ' / '; a stable number
        # (DFRP property_number) is written as 'where' and read first, the objectid stays as a fallback; 'names' = chat 11's read-back.
        nm = re.findall(r"'(.{3,}?)'(?=\s*(?:\(|,|;|/|$))", rg) or re.findall(r'"([^"]{3,})"', rg)
        if not nm:
            tail = rg.rsplit(' / ', 1)[1].strip() if ' / ' in rg else ''
            if tail and not re.match(r'(?i)(objectid|fid|property_number)\b', tail): nm = [re.sub(r'\s*\(.*$', '', tail).strip()]
        if not nm:   # "OBJECTID 369 (Mud Creek Trail)" or "OBJECTID 39 BATOCHE NATIONAL HISTORIC PARK" (no quotes)
            m3 = re.match(r'\s*[A-Za-z_]+\s*[:=]?\s*\d+\s*(?:\(([^)]{3,})\)|([A-Za-z][^;,(]{2,}))', rg)
            if m3: nm = [(m3.group(1) or m3.group(2)).strip()]
        try: rb = [str(x) for x in ast.literal_eval(str(r.get('names') or '[]'))]   # chat 11 wrote it as a list literal
        except Exception: rb = []  # noqa: BLE001
        row = {'ref': ref, 'url': url, 'name_field': r.get('name_field') or '', 'record_name': nm[0] if nm else ''}
        if rb: row['names'] = rb[:6]
        pn = re.search(r'\bproperty_number\b\s*[:=]?\s*(\d+)', rg, re.I) if 'DFRP' in url else None
        m = re.search(r'\b(?:objectid|fid)\b\s*[:=]?\s*(\d+)', rg, re.I)
        m2 = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*[:=]?\s*(\d+)\b', rg)
        if pn: row['where'] = f"property_number = '{pn.group(1)}'"
        if m: row['oid'] = int(m.group(1))
        elif m2 and not pn: row['where'] = f'{m2.group(1)} = {m2.group(2)}'
        elif nm and row['name_field'] and not pn: row['where'] = f"{row['name_field']} = '" + nm[0].replace("'", "''") + "'"
        elif not pn: skip += 1; continue
        out.append(row)
    os.makedirs('data/ca-key', exist_ok=True)
    json.dump({'about': __doc__.split('\n')[0], 'from': str(src), 'rows': out}, open('data/ca-key/hardlook-joins.json', 'w'), indent=1, ensure_ascii=False)
    print(f'::notice title=Canada hard look::{len(out)} chat 11 YES records for the Canada key ({skip} without a readable record)')


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Canada hard look::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
