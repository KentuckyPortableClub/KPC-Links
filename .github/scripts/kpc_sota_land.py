#!/usr/bin/env python3
"""Is this SOTA summit on public land? (Opus Oct 24 2026; Activators Lounge step 6, Brandon: 'a tool that shows which
summits are on public land and maybe a way to find out who owns the private land').
Every US summit (locations.json SOTA rows) is tested against USGS PAD-US (the national public-lands map), 60 summits per
query (a multipoint), then point-in-polygon here. Proclamation lines are skipped (a national forest's proclamation line
holds private land too). Result per summit:
  P = public, open to the public (PAD-US Pub_Access OA) · R = public, restricted access (RA) · X = closed (XA)
  U = public land, access not known (UK) · E = only a conservation easement (private land) · N = not on the public-lands map
Written to data/sota-land/<ASSOC>.json = {updated, s: {ref: [code, manager, unit name]}}. Each SOTA area is redone every
30 days, oldest first, within a time limit per run (so one run never gets long). A query that fails keeps the area's last
file. Never fails (exit 0). Private owners are NOT looked up or stored (the page links the county's own property map)."""
import datetime as dt
import json
import math
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

Q = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
OUT = pathlib.Path('data/sota-land')
STATE = OUT / 'state.json'
LIMIT = float(os.environ.get('LAND_MINUTES') or 40) * 60
EVERY = 30   # days
CHUNK = 60
T0 = time.time()
MANG = {'NPS': 'National Park Service', 'USFS': 'Forest Service', 'FWS': 'Fish & Wildlife Service', 'BLM': 'Bureau of Land Management',
        'USACE': 'Army Corps of Engineers', 'TVA': 'TVA', 'BOR': 'Bureau of Reclamation', 'DOD': 'Department of Defense', 'NRCS': 'NRCS',
        'SPR': 'State parks', 'SDNR': 'State natural resources', 'SFW': 'State fish & wildlife', 'SDOF': 'State forestry', 'SLB': 'State land board',
        'SDC': 'State conservation', 'OTHS': 'Other state agency', 'CITY': 'City', 'CNTY': 'County', 'REG': 'Regional agency', 'NGO': 'Nonprofit',
        'PVT': 'Private', 'JNT': 'Joint', 'TRIB': 'Tribal', 'UNK': 'Unknown', 'OTHF': 'Other federal'}
RANK = {'OA': 'P', 'RA': 'R', 'UK': 'U', 'XA': 'X'}
BEST = {'P': 0, 'R': 1, 'U': 2, 'X': 3, 'E': 4, 'N': 5}


def note(m):
    print(f'::notice title=SOTA public land::{m}', flush=True)


def get(params, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(Q + '?' + urllib.parse.urlencode(params), headers={'User-Agent': 'KPC SOTA land check (kentuckyportableclub.github.io)'})
            with urllib.request.urlopen(req, timeout=120) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if j.get('error'):
                raise RuntimeError(str(j['error'])[:160])
            return j
        except Exception as e:  # noqa: BLE001
            last = e; time.sleep(6 * (i + 1))
    raise last


def inside(x, y, rings):
    """even-odd over every ring (holes included)"""
    c = False
    for r in rings:
        n = len(r)
        for i in range(n):
            x1, y1 = r[i][0], r[i][1]; x2, y2 = r[i - 1][0], r[i - 1][1]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-15) + x1:
                c = not c
    return c


def check(batch):
    """batch = [(ref, la, lo)] -> {ref: [code, manager, unit]}"""
    mp = json.dumps({'points': [[round(lo, 5), round(la, 5)] for _, la, lo in batch], 'spatialReference': {'wkid': 4326}})
    feats, off = [], 0
    while True:
        j = get({'geometry': mp, 'geometryType': 'esriGeometryMultipoint', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                 'outFields': 'Unit_Nm,Mang_Name,Pub_Access,Category', 'returnGeometry': 'true', 'outSR': 4326,
                 'maxAllowableOffset': 0.00003, 'geometryPrecision': 6, 'resultOffset': off, 'resultRecordCount': 500, 'f': 'json'})
        fs = j.get('features') or []
        feats += fs
        if not j.get('exceededTransferLimit') or not fs:
            break
        off += len(fs)
    out = {}
    for ref, la, lo in batch:
        best = ['N', '', '']
        for f in feats:
            a = f.get('attributes') or {}
            cat = str(a.get('Category') or '')
            if cat == 'Proclamation':
                continue
            rings = (f.get('geometry') or {}).get('rings') or []
            if not rings or not inside(lo, la, rings):
                continue
            code = 'E' if cat == 'Easement' else RANK.get(str(a.get('Pub_Access') or 'UK'), 'U')
            if str(a.get('Mang_Name') or '') == 'PVT' and code != 'E':
                code = 'E' if cat == 'Easement' else 'N'
            if BEST[code] < BEST[best[0]]:
                best = [code, MANG.get(str(a.get('Mang_Name') or ''), str(a.get('Mang_Name') or '')), str(a.get('Unit_Nm') or '')[:60]]
        out[ref] = best
    return out


def main():
    try:
        L = json.load(open('locations.json', encoding='utf-8'))
    except (OSError, ValueError) as e:
        note(f'no summit list ({e})'); return
    by = {}
    for r in L:
        if r[0] != 'SOTA' or r[3] is None:
            continue
        by.setdefault(r[1].split('/')[0], []).append((r[1], float(r[3]), float(r[4])))
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        st = json.loads(STATE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        st = {'done': {}}
    today = dt.date.today()
    due = sorted(by, key=lambda a: st['done'].get(a, '0000'))
    due = [a for a in due if st['done'].get(a, '0000') < (today - dt.timedelta(days=EVERY)).isoformat()]
    did, fails = [], []
    for a in due:
        if time.time() - T0 > LIMIT:
            break
        S = sorted(by[a], key=lambda x: (math.floor(x[1] * 2), math.floor(x[2] * 2)))
        res, ok = {}, True
        for i in range(0, len(S), CHUNK):
            if time.time() - T0 > LIMIT + 600:
                ok = False; break
            try:
                res.update(check(S[i:i + CHUNK]))
            except Exception as e:  # noqa: BLE001
                ok = False; fails.append(f'{a}: {str(e)[:80]}'); break
            time.sleep(0.4)
        if not ok:
            continue   # keep the area's last file
        (OUT / f'{a}.json').write_text(json.dumps({'updated': today.isoformat(), 's': res}, separators=(',', ':')) + '\n', encoding='utf-8')
        st['done'][a] = today.isoformat(); did.append(f'{a} {len(res)}')
    STATE.write_text(json.dumps(st, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    left = len([a for a in by if st['done'].get(a, '0000') < (today - dt.timedelta(days=EVERY)).isoformat()])
    note(f'checked {len(did)} SOTA areas ({", ".join(did[:12])}{"…" if len(did) > 12 else ""}); {left} still due' + (f'; problems: {"; ".join(fails[:3])}' if fails else ''))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        note(f'stopped early: {e}')
    sys.exit(0)
