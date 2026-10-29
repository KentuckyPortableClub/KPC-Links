#!/usr/bin/env python3
"""WWFF PINS WITH NO LOCATION (chat 2, Oct 29 2026; Brandon 1:45 PM 'Yes' to finding the ~1,600 WWFF references that WWFF's own
directory lists with no latitude/longitude). Rule (notes/mapping.md 'WWFF MISSING PINS'): a pin is placed ONLY from an OFFICIAL
register of protected sites, ONLY when exactly ONE site of that country carries the same name (designation words like
LIC / SAC / ZEPA / Reserva Natural dropped on both sides), at the record's own inside point. Sources, best first: the EEA's
Natura 2000 sites, then the EEA's nationally designated areas (CDDA), both read live from bio.discomap.eea.europa.eu (open data).
Two or more same-name sites, or none = NO pin (listed with the reason). HELD (Brandon 12:56 PM freeze): the answers go to
data/wwff-locate/found.json + KPC_WWFF_Locate.md, never into data/wwff. Never fails."""
import glob, json, os, re, time, unicodedata, urllib.parse, urllib.request

UA = {'User-Agent': 'KPC park-map bot (kentuckyportableclub.github.io; ham radio club)'}
ROOT = 'https://bio.discomap.eea.europa.eu/arcgis/rest/services'
ISO = {'EA': 'ES', 'EA6': 'ES', 'EA8': 'ES', 'EA9': 'ES', 'OE': 'AT', 'OK': 'CZ', 'OM': 'SK', 'LY': 'LT', 'YL': 'LV', 'ES': 'EE', 'F': 'FR', 'I': 'IT',
       'LA': 'NO', 'SP': 'PL', 'HA': 'HU', 'YO': 'RO', 'LZ': 'BG', 'SV': 'GR', 'S5': 'SI', '9A': 'HR', 'CT': 'PT', 'CU': 'PT', 'EI': 'IE',
       'ON': 'BE', 'PA': 'NL', 'OZ': 'DK', 'SM': 'SE', 'OH': 'FI', 'DL': 'DE', 'LX': 'LU', '5B': 'CY', '9H': 'MT', 'G': 'GB', 'HB': 'CH', 'TF': 'IS'}
DESIG = r'\b(lic|sac|zec|zepa|spa|sci|sic|zps|zsc|ffh|natura 2000|reserva natural( parcial| integral)?|parque natural|paraje natural( municipal)?|monumento natural|' \
        r'paisaje protegido|zonas? h[uú]medas?|[aá]rbol singular|cuevas?|reserva|parque|national park|nature reserve|naturschutzgebiet|nsg|' \
        r'park narodowy|rezerwat|p[rř][ií]rodn[ií] (rezervace|park|pam[aá]tka)|réserve naturelle|riserva naturale|parco)\b'
LAST = [0.0]
ISO3 = {'ES': 'ESP', 'AT': 'AUT', 'CZ': 'CZE', 'SK': 'SVK', 'LT': 'LTU', 'LV': 'LVA', 'EE': 'EST', 'FR': 'FRA', 'IT': 'ITA', 'NO': 'NOR', 'PL': 'POL', 'HU': 'HUN',
        'RO': 'ROU', 'BG': 'BGR', 'GR': 'GRC', 'SI': 'SVN', 'HR': 'HRV', 'PT': 'PRT', 'IE': 'IRL', 'BE': 'BEL', 'NL': 'NLD', 'DK': 'DNK', 'SE': 'SWE', 'FI': 'FIN',
        'DE': 'DEU', 'LU': 'LUX', 'CY': 'CYP', 'MT': 'MLT', 'GB': 'GBR', 'CH': 'CHE', 'IS': 'ISL'}


def get(url, params, tries=3):
    for k in range(tries):
        w = 1.5 - (time.time() - LAST[0])
        if w > 0: time.sleep(w)
        try:
            LAST[0] = time.time()
            with urllib.request.urlopen(urllib.request.Request(url + '?' + urllib.parse.urlencode(params), headers=UA), timeout=90) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if 'error' in j: raise RuntimeError(str(j['error'])[:120])
            return j
        except Exception as e:  # noqa: BLE001
            if k == tries - 1: return {'_err': str(e)[:160]}
            time.sleep(4 * (k + 1))


def core(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    s = re.sub(DESIG, ' ', s)
    s = re.sub(r'\b(de|del|la|las|los|el|y|i|d|l|des|du|le|di|della|von|der|und|the|of|and)\b', ' ', s)
    return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', s).split())


def layers():
    """Every EEA protected-sites layer with a site-name and a country field (found, not guessed)."""
    out = []
    for folder in ('ProtectedSites', 'ProtectedSites_Online'):
        j = get(f'{ROOT}/{folder}', {'f': 'json'})
        for s in (j.get('services') or []):
            if s.get('type') not in ('MapServer', 'FeatureServer'): continue
            nm = s['name']
            if not re.search(r'natura|cdda|nationally', nm, re.I): continue
            su = f"{ROOT}/{nm}/{s['type']}"
            info = get(su, {'f': 'json'})
            for ly in (info.get('layers') or []):
                li = get(f"{su}/{ly['id']}", {'f': 'json'})
                fl = {f['name'] for f in (li.get('fields') or [])}
                namef = next((f for f in ('SITENAME', 'SITE_NAME', 'siteName', 'sitename', 'Site_Name') if f in fl), None)
                ctry = next((f for f in ('MS', 'COUNTRY_CODE', 'ISO3', 'ISO2', 'countryCode', 'CountryCode', 'COUNTRY', 'cddaCountryCode') if f in fl), None)
                if namef and ctry and li.get('geometryType') == 'esriGeometryPolygon':
                    out.append({'url': f"{su}/{ly['id']}", 'name': namef, 'ctry': ctry, 'label': f"{nm.split('/')[-1]} / {li.get('name')}", 'natura': bool(re.search('natura', nm, re.I))})
    out.sort(key=lambda x: not x['natura'])
    print(f"::notice title=WWFF locate layers::{len(out)} EEA layers: " + '; '.join(x['label'] for x in out)[:800], flush=True)
    return out


def inside_point(g):
    """A point inside the record (its biggest ring's centre if inside, else the first vertex pair midpoint)."""
    rs = [r for r in (g or {}).get('rings') or [] if len(r) > 3]
    if not rs: return None
    r = max(rs, key=lambda r: abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(r, r[1:] + r[:1]))))
    x = sum(p[0] for p in r) / len(r); y = sum(p[1] for p in r) / len(r)
    ins = False; j = len(r) - 1
    for i in range(len(r)):
        if (r[i][1] > y) != (r[j][1] > y) and x < (r[j][0] - r[i][0]) * (y - r[i][1]) / ((r[j][1] - r[i][1]) or 1e-12) + r[i][0]: ins = not ins
        j = i
    if ins: return round(y, 5), round(x, 5)
    m = len(r) // 2
    return round((r[0][1] + r[m][1]) / 2, 5), round((r[0][0] + r[m][0]) / 2, 5)


def main():
    miss = []
    for f in sorted(glob.glob('data/wwff/*.json')):
        pre = os.path.basename(f)[:-7] if f.endswith('FF.json') else os.path.basename(f)[:-5]
        if not f.endswith('FF.json'): continue   # index.json / SELECT.json are not reference lists
        for r in json.load(open(f)):
            if not isinstance(r, list) or len(r) < 4: continue
            if r[2] in (None, '', 0) or r[3] in (None, '', 0) or r[2] == 0.0:
                miss.append({'ref': r[0], 'name': r[1], 'prefix': pre, 'iso': ISO.get(pre)})
    L = layers() if any(m['iso'] for m in miss) else []
    deadline = time.time() + 60 * float(os.environ.get('MINUTES') or 100)
    found, nofind = [], []
    for m in miss:
        if not m['iso']: m['why'] = 'no official register read for this country yet'; nofind.append(m); continue
        if time.time() > deadline: m['why'] = 'out of time (next run)'; nofind.append(m); continue
        c = core(m['name'])
        if len(c) < 3: m['why'] = 'name too short to match'; nofind.append(m); continue
        words = [w for w in c.split() if len(w) > 3][:3] or c.split()[:2]
        hit = None; why = 'no same-name site in the official registers'
        for ly in L:
            iso3 = ISO3.get(m['iso'])
            cval = iso3 if ly['ctry'] == 'ISO3' and iso3 else m['iso']
            where = f"{ly['ctry']} = '{cval}' AND " + ' AND '.join(f"UPPER({ly['name']}) LIKE '%{w.upper()}%'" for w in words)
            j = get(ly['url'] + '/query', {'where': where, 'outFields': ly['name'], 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.0005, 'f': 'json'})
            if '_err' in j: why = 'the register did not answer: ' + j['_err'][:60]; continue
            same = [f for f in j.get('features') or [] if core((f.get('attributes') or {}).get(ly['name'])) == c]
            names = {core((f.get('attributes') or {}).get(ly['name'])) for f in same}
            if len(same) >= 1 and len(names) == 1:
                pts = [inside_point(f.get('geometry')) for f in same]
                pts = [p for p in pts if p]
                if pts:
                    if len(same) > 1:   # one site in several pieces: the biggest piece's point
                        pt = pts[0]
                    else: pt = pts[0]
                    hit = {'lat': pt[0], 'lon': pt[1], 'source': ly['label'], 'record_name': (same[0].get('attributes') or {}).get(ly['name']), 'pieces': len(same)}
                    break
            elif len(same) > 1: why = 'two or more different same-name sites'
        if hit: m.update(hit); found.append(m)
        else: m['why'] = why; nofind.append(m)
    os.makedirs('data/wwff-locate', exist_ok=True)
    json.dump({'about': __doc__.split('\n')[0], 'made': time.strftime('%Y-%m-%d'), 'rule': 'official register, exactly one same-name site in that country, its own inside point; else no pin',
               'credit': 'European Environment Agency (Natura 2000 / CDDA), open data', 'found': found, 'not_found': nofind},
              open('data/wwff-locate/found.json', 'w'), indent=1, ensure_ascii=False)
    from collections import Counter
    byp = Counter(m['prefix'] for m in found); why = Counter(m['why'][:40] for m in nofind)
    md = [f"# WWFF references with no location: what the official registers say ({time.strftime('%Y-%m-%d')})", '',
          f"{len(miss)} WWFF references have no location in WWFF's own directory. FOUND {len(found)} (one same-name site in the official register), NOT FOUND {len(nofind)}. HELD: nothing is on a map yet (Brandon's freeze).", '',
          '## Found by program', ''] + [f'- {k}: {v}' for k, v in byp.most_common()] + ['', '## Not found, why', ''] + [f'- {k}: {v}' for k, v in why.most_common()] + \
         ['', '## Sample found (check a few)', '', '| Ref | WWFF name | official record | pin | source |', '|---|---|---|---|---|'] + \
         [f"| {m['ref']} | {m['name'][:40]} | {str(m['record_name'])[:40]} | {m['lat']}, {m['lon']} | {m['source'][:40]} |" for m in found[:40]] + \
         ['', 'ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.']
    open('data/wwff-locate/KPC_WWFF_Locate.md', 'w').write('\n'.join(md) + '\n')
    print(f"::notice title=WWFF locate::{len(miss)} with no location: found {len(found)} ({dict(byp.most_common(8))}), not found {len(nofind)} ({dict(why.most_common(4))})", flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=WWFF locate::stopped: {str(e)[:200]}')  # noqa: BLE001
