#!/usr/bin/env python3
"""NAME-MATCH CHECK BOT (chat 2, Oct 29 2026; HQ 10:34 AM, Brandon 10:30 + 10:33 AM: 'bot first, then review by 2').
Reads chat 8's candidate lists (KPC_NameMismatch_Decoded_desk.md sections 2-7, KPC_NameMismatch_USCA_desk.md tiers A + B,
KPC_ClueSearch_desk.md 'within 3 km') and, for each POTA park + official layer name, asks the official layer for that feature
near the POTA pin, then measures: pin inside / metres from the edge, acres, number of pieces, owner fields, and whether another
park in the key already uses that record (a clash). Verdict:
  PASS       pin inside or within 100 m of the edge, no clash, 1 ac <= size <= 2,000,000 ac
  FAIL       nearest piece over 2 km from the pin, or the record already belongs to another park
  CAN'T TELL anything else (no answer, several candidates, size odd, 100 m - 2 km)
Read only: nothing is added to the key. Writes .claude/build/research/alias-check.json + KPC_AliasCheck_desk.md. Never fails."""
import glob, json, math, os, pathlib, re, sys, time, urllib.parse, urllib.request

UA = {'User-Agent': 'KPC park-map bot (kentuckyportableclub.github.io; ham radio club)'}
R = pathlib.Path('.claude/build/research')
PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
CPCAD = 'https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0/query'
LAST = {}
DEADLINE = time.time() + float(os.environ.get('MINUTES') or 150) * 60


def get(url, params):
    host = urllib.parse.urlparse(url).netloc
    for k in range(3):
        w = 2 - (time.time() - LAST.get(host, 0))
        if w > 0: time.sleep(w)
        try:
            LAST[host] = time.time()
            with urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), headers=UA), timeout=90) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if 'error' in j: raise RuntimeError(str(j['error'])[:80])
            return j
        except Exception:  # noqa: BLE001
            if k == 2: return None
            time.sleep(5 * (k + 1))


def rows_of(path, refcol, namecol, laycol=None, sections=None):
    out, sec = [], ''
    try: lines = open(path).read().splitlines()
    except Exception: return out  # noqa: BLE001
    for l in lines:
        if l.startswith('## '): sec = l
        if not l.startswith('|') or '---' in l: continue
        c = [x.strip() for x in l.strip('|').split('|')]
        if len(c) <= max(refcol, namecol) or not re.match(r'(US|CA)-\d+$', c[refcol]): continue
        if sections and not any(sec.startswith(f'## {s}.') for s in sections): continue
        nm = re.sub(r'\s*\([\d.]+\)\s*$', '', c[namecol]).strip()
        out.append({'ref': c[refcol], 'layer_name': nm, 'layer': c[laycol] if laycol is not None and len(c) > laycol else '', 'list': os.path.basename(path), 'section': sec[3:40]})
    return out


def inside(pt, ring):
    x, y = pt; c = False; j = len(ring) - 1
    for i in range(len(ring)):
        if (ring[i][1] > y) != (ring[j][1] > y) and x < (ring[j][0] - ring[i][0]) * (y - ring[i][1]) / ((ring[j][1] - ring[i][1]) or 1e-12) + ring[i][0]: c = not c
        j = i
    return c


def seg_m(p, a, b, kx, ky):
    ax, ay, bx, by, px, py = a[0] * kx, a[1] * ky, b[0] * kx, b[1] * ky, p[0] * kx, p[1] * ky
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy or 1e-9
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def measure(rings, lon, lat):
    kx, ky = 111320 * math.cos(math.radians(lat)), 110574
    ins = sum(1 for r in rings if inside((lon, lat), r)) % 2 == 1
    d = min((seg_m((lon, lat), r[i], r[i + 1], kx, ky) for r in rings for i in range(len(r) - 1)), default=1e9)
    ac = abs(sum(sum((a[0] * kx) * (b[1] * ky) - (b[0] * kx) * (a[1] * ky) for a, b in zip(r, r[1:] + r[:1])) / 2 for r in rings)) / 4046.86
    return ins, (0 if ins else round(d)), round(ac, 1)


def main():
    links = '.'
    P = {}
    for f in glob.glob('data/parkinfo/US-*.json') + ['data/parkinfo/CA.json']:
        try:
            for r, v in json.load(open(f))['parks'].items():
                if len(v) > 6 and v[5] is not None: P[r] = (v[0], v[5], v[6], str(v[2]) if len(v) > 2 else '')
        except Exception: pass  # noqa: BLE001
    KEY, claimed, PROV = {}, {}, {}
    for f in glob.glob('data/us-key/US-??.json') + glob.glob('data/ca-key/CA-??.json'):
        for r, p in json.load(open(f))['parks'].items():
            KEY[r] = p; PROV[r] = os.path.basename(f)[3:5]
            for x in p.get('m') or []: claimed.setdefault(str(x[0]), set()).add(r)
    LU = json.load(open('data/us-key/layers.json')); LC = json.load(open('data/ca-key/layers.json'))
    cand = (rows_of(R / 'KPC_NameMismatch_Decoded_desk.md', 1, 3, 7, sections=['2', '3', '4', '5', '6', '7'])
            + rows_of(R / 'KPC_NameMismatch_USCA_desk.md', 1, 3, None, sections=['1'])
            )
    # ClueSearch's own section title starts 'Within 3 km'
    cand += [x for x in rows_of(R / 'KPC_ClueSearch_desk.md', 1, 3, 6) if x['section'].lower().startswith('within')]
    seen, res = set(), []
    for c in cand:
        k = (c['ref'], c['layer_name'].lower())
        if k in seen or c['ref'] not in P: continue
        seen.add(k)
        if time.time() > DEADLINE: c.update(verdict="CAN'T TELL", why='out of time (next run)'); res.append(c); continue
        nm, la, lo, ty = P[c['ref']]
        srcs = []
        if c['layer'] and c['layer'] in LU: srcs.append((c['layer'], LU[c['layer']][0], LU[c['layer']][1]))
        elif c['ref'].startswith('US-'):
            srcs.append(('pad', PADUS, 'Unit_Nm'))
        else:
            srcs.append(('cpcad', CPCAD, 'NAME_E'))
            PFX = {'ON': ('Ontario', 'ON-'), 'QC': ('Québec', 'QC'), 'BC': ('BC',), 'AB': ('Alberta', 'AB-'), 'MB': ('Manitoba', 'MB'), 'SK': ('Sask', 'SK'),
                   'NB': ('New Brunswic', 'NB'), 'NS': ('Nova Scotia', 'NS-'), 'NL': ('NL', 'Newfoundland'), 'PE': ('PE',), 'YT': ('YT', 'Yukon'), 'NT': ('NT',), 'NU': ('NU',)}
            for pre, urls in LC.items():
                if pre != 'cpcad' and urls and pre.startswith(PFX.get(PROV.get(c['ref'], ''), ('~~',))):
                    for u in urls: srcs.append((pre, u.rstrip('/') + '/query', None))
        best = None
        for key, url, fld in srcs:
            q = str(c['layer_name']).replace("'", "''")
            where = f"UPPER({fld}) = UPPER('{q}')" if fld else '1=1'
            j = get(url, {'where': where, 'geometry': f'{lo - .3},{la - .3},{lo + .3},{la + .3}', 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
                          'spatialRel': 'esriSpatialRelIntersects', 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': .0001, 'f': 'json'})
            if not j or 'features' not in j: continue
            oidf = j.get('objectIdFieldName') or 'OBJECTID'
            for f in j['features']:
                a = f.get('attributes') or {}
                if not fld and not any(isinstance(v, str) and v.strip().lower() == c['layer_name'].lower() for v in a.values()): continue
                rings = [r for r in ((f.get('geometry') or {}).get('rings') or []) if len(r) > 3]
                if not rings: continue
                ins, dm, ac = measure(rings, lo, la)
                oid = a.get(oidf)
                rid = str(oid) if key in ('pad', 'cpcad') else (f'{key}{oid}' if c['ref'].startswith('US-') else f'{key}:{oid}')
                cl = sorted(claimed.get(rid, set()) - {c['ref']})
                own = next((str(a[x]) for x in ('Own_Name', 'OWNER', 'Owner', 'OWNER_E', 'Mang_Name', 'MANAGER') if a.get(x)), '')
                row = {'record': rid, 'inside': ins, 'edge_m': dm, 'acres': ac, 'pieces': len(rings), 'owner': own, 'clash': cl, 'src': key}
                if best is None or (row['edge_m'], -row['acres']) < (best['edge_m'], -best['acres']): best = row
            if best and best['edge_m'] == 0: break
        if not best: c.update(verdict="CAN'T TELL", why='no feature with that name near the pin (or the map did not answer)')
        else:
            c.update(best)
            if best['clash']: c.update(verdict='FAIL', why=f"the record already belongs to {', '.join(best['clash'])}")
            elif best['edge_m'] > 2000: c.update(verdict='FAIL', why=f"nearest piece {best['edge_m']} m from the POTA pin")
            elif best['edge_m'] <= 100 and 1 <= best['acres'] <= 2_000_000: c.update(verdict='PASS', why='pin inside' if best['inside'] else f"pin {best['edge_m']} m from the edge")
            else: c.update(verdict="CAN'T TELL", why=f"pin {best['edge_m']} m from the edge, {best['acres']} ac")
        c['pota_name'] = nm; c['pota_type'] = ty
        res.append(c)
    json.dump({'about': __doc__.split('\n')[0], 'date': time.strftime('%Y-%m-%d'), 'rows': res}, open(R / 'alias-check.json', 'w'), indent=1, ensure_ascii=False)
    from collections import Counter
    cnt = Counter(r['verdict'] for r in res)
    L = ['# Name-match check (bot, %s)' % time.strftime('%Y-%m-%d'), '', "HQ / Brandon Oct 29 10:30 AM: bot first, then review by two (chat 2 + chat 11 for CAN'T TELL). Nothing added yet.", '',
         f"PASS {cnt.get('PASS', 0)} · FAIL {cnt.get('FAIL', 0)} · CAN'T TELL " + str(cnt.get("CAN'T TELL", 0)), '']
    for v in ('PASS', "CAN'T TELL", 'FAIL'):
        rows = [r for r in res if r['verdict'] == v]
        L += [f'## {v} ({len(rows)})', '', '| Park | POTA name | Layer name | record | pin | acres | pieces | owner | why |', '|---|---|---|---|---|---|---|---|---|']
        L += [f"| {r['ref']} | {r['pota_name'][:40]} | {r['layer_name'][:40]} | {r.get('record', '')} | {'inside' if r.get('inside') else (str(r.get('edge_m', '')) + ' m') if 'edge_m' in r else ''} | {r.get('acres', '')} | {r.get('pieces', '')} | {str(r.get('owner', ''))[:30]} | {r['why'][:70]} |" for r in rows]
        L.append('')
    L.append("ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.")
    (R / 'KPC_AliasCheck_desk.md').write_text('\n'.join(L) + '\n')
    print(f"::notice title=Name-match check::{len(res)} candidates: " + ' · '.join(f'{k} {v}' for k, v in cnt.items()), flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Name-match check::stopped: {str(e)[:200]}', flush=True)  # noqa: BLE001
    sys.exit(0)
