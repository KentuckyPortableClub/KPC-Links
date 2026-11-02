#!/usr/bin/env python3
"""Canada HARD LOOK -> the Canada key (chat 2, Nov 2 2026; chat 10 Nov 1 12:30 AM + Brandon 'do it'). Chat 11's YES rows in KPC-Data
data/waiting/questions/hardlook.json name the exact official layer + record for a Canadian park ('OBJECTID 1649', 'FID 1',
'OGF_ID 450757661 ...', "property_number=00345 (objectid 48)"). The Canada answers bot never read this file (it reads 'questions', this
file has 'rows'), so none of them reached the key. This writes data/ca-key/hardlook-joins.json {rows: [{ref, url, oid | where,
name_field, record_name}]}; kpc_ca_key.py reads each record by id and joins it to its park when the key found nothing else.
Only YES answers (first word); NOT SURE / NO / blank never. No network. Exit 0 always."""
import json, os, pathlib, re, sys


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
        nm = re.findall(r"['\"]([^'\"]{3,})['\"]", rg)
        row = {'ref': ref, 'url': url, 'name_field': r.get('name_field') or '', 'record_name': nm[0] if nm else ''}
        m = re.search(r'\b(?:objectid|fid)\b\s*[:=]?\s*(\d+)', rg, re.I)
        m2 = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*[:=]?\s*(\d+)\b', rg)
        if m: row['oid'] = int(m.group(1))
        elif m2: row['where'] = f'{m2.group(1)} = {m2.group(2)}'
        elif nm and row['name_field']: row['where'] = f"{row['name_field']} = '" + nm[0].replace("'", "''") + "'"
        else: skip += 1; continue
        out.append(row)
    os.makedirs('data/ca-key', exist_ok=True)
    json.dump({'about': __doc__.split('\n')[0], 'from': str(src), 'rows': out}, open('data/ca-key/hardlook-joins.json', 'w'), indent=1, ensure_ascii=False)
    print(f'::notice title=Canada hard look::{len(out)} chat 11 YES records for the Canada key ({skip} without a readable record)')


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Canada hard look::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
