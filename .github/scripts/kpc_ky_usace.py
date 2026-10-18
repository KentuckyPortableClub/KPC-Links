"""Army Corps of Engineers OWNED land in Kentucky -> ky-usace.geojson (Brandon Oct 17 2026: 'check all state parks that are next to CoE land and
make sure the CoE land is the same color as land around US-1271').
The PAD-US picture tiles colour land by MANAGER, so Corps land run by a state agency (most lake WMAs, some state park land) shows as state land.
This file lists the land the Corps OWNS (USGS PAD-US Own_Name = USACE, fee land), whoever runs it, so the KY maps can draw it orange.
PAD-US's firewall refuses long WHERE clauses, so we list KY records with a short one and filter here."""
import json, time, urllib.parse, urllib.request, os, sys

Q = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'


def get(params, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(Q + '?' + urllib.parse.urlencode(params), headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(6 * (i + 1))
    raise last


def main():
    recs, off = [], 0
    while off < 40000:
        j = get({'where': "State_Nm='KY'", 'outFields': 'OBJECTID,Unit_Nm,Own_Name,Mang_Name,Loc_Mang,Loc_Own,Category,GIS_Acres', 'returnGeometry': 'false',
                 'f': 'json', 'resultOffset': off, 'resultRecordCount': 1000, 'orderByFields': 'OBJECTID'})
        if j.get('error'):
            print('::error title=PAD-US::%s' % j['error']); sys.exit(1)
        fs = j.get('features', [])
        for f in fs:
            a = f.get('attributes', {})
            if (a.get('Own_Name') or '').upper() == 'USACE' and (a.get('Category') or '') == 'Fee':
                recs.append(a)
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < 1000):
            break
        off += len(fs)
        time.sleep(1)
    print('::notice title=Corps land records::%d KY records owned by USACE (looked at %d)' % (len(recs), off + len(fs)))
    if len(recs) < 20:
        print('::error title=Too few::refusing to write'); sys.exit(1)
    feats, ids = [], [r['OBJECTID'] for r in recs]
    by = {r['OBJECTID']: r for r in recs}
    for i in range(0, len(ids), 40):
        j = get({'objectIds': ','.join(map(str, ids[i:i + 40])), 'outFields': 'OBJECTID', 'returnGeometry': 'true', 'outSR': 4326, 'f': 'geojson',
                 'maxAllowableOffset': 0.00015, 'geometryPrecision': 5})
        for f in j.get('features', []):
            a = by.get((f.get('properties') or {}).get('OBJECTID')) or {}
            if not f.get('geometry'):
                continue
            f['properties'] = {'NAME': a.get('Unit_Nm') or 'Army Corps of Engineers land', 'MANAGER': a.get('Loc_Mang') or a.get('Mang_Name') or '',
                               'MANG': a.get('Mang_Name') or '', 'ACRES': round(a.get('GIS_Acres') or 0), 'OWNER': 'U.S. Army Corps of Engineers'}
            feats.append(f)
        time.sleep(1)
    out = {'type': 'FeatureCollection', 'name': 'Army Corps of Engineers owned land in Kentucky (USGS PAD-US 4, Own_Name USACE, fee)',
           'updated': time.strftime('%Y-%m-%d'), 'features': feats}
    s = json.dumps(out, separators=(',', ':'))
    open('ky-usace.geojson', 'w').write(s)
    mg = {}
    for f in feats:
        mg[f['properties']['MANG']] = mg.get(f['properties']['MANG'], 0) + 1
    print('::notice title=ky-usace.geojson::%d shapes, %d KB; run by: %s' % (len(feats), len(s) // 1024, ', '.join('%s %d' % kv for kv in sorted(mg.items(), key=lambda x: -x[1]))))


main()
