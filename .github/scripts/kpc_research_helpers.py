#!/usr/bin/env python3
"""HELPERS THAT FILL CHAT 8'S SHEETS (chat 10, Oct 30 2026; HQ 7:50 AM, Brandon 7:43 AM 'any other helper that make chat 8 work
easier'). Notes only: nothing here decides, nothing goes to the waiting room, the GIS hunter's logic is untouched.

  packets  For every park in .claude/build/research/fable/<area>.md that still has no OFFICIAL outline, ONE short line in the file's
           '## PARK PACKETS' section (rewritten each run): pin · county (Census TIGERweb, US) · agency guess (from the name's kind
           words) · POTA website · what the GIS hunter / documents bot / website-name read already tried, with dates. So chat 8 starts
           from a full sheet and never repeats a try.
  atlas    For each agency server root in .claude/build/research/agency-atlas/<area>.md, list every layer whose name carries park /
           boundary / recreation / wildlife / forest / lands words + its name field, in the file's '## Layers on these servers'
           section (rewritten each run). Lists only.
  python3 kpc_research_helpers.py packets|atlas [AREA ...]      env DATA = a KPC-Data checkout (default kpcdata)
Manners: KPC-Data's kpc_manners.py (robots obeyed; ArcGIS REST exempt; 2 s per host; 3 strikes = a day's rest). Never fails."""
import datetime as dt, glob, json, os, pathlib, re, sys, time, urllib.parse

DATA = pathlib.Path(os.environ.get('DATA') or 'kpcdata')
sys.path.insert(0, str(DATA / '.github' / 'scripts'))
try:
    from kpc_manners import Manners
    M = Manners('KPC research helpers (chat 10)')
except Exception:  # noqa: BLE001
    M = None
RES = pathlib.Path('.claude/build/research')
FB, AT = RES / 'fable', RES / 'agency-atlas'
TODAY = dt.date.today().isoformat()
PARKW = re.compile(r'park|parc|boundar|recreation|wildlife|faune|forest|forêt|lands?\b|refuge|reserve|réserve|preserve|natural area|'
                   r'wma|management area|conservation|protected|sanctuary|historic|monument|trail|sentier|hatchery|game', re.I)
STATES = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
          'DC': 'District of Columbia', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
          'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota',
          'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
          'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon',
          'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
          'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
          'AB': 'Alberta', 'BC': 'British Columbia', 'MB': 'Manitoba', 'NB': 'New Brunswick', 'NL': 'Newfoundland and Labrador', 'NS': 'Nova Scotia',
          'NT': 'Northwest Territories', 'NU': 'Nunavut', 'ON': 'Ontario', 'PE': 'Prince Edward Island', 'QC': 'Quebec', 'SK': 'Saskatchewan', 'YT': 'Yukon'}
AGENCY = [(r'national wildlife refuge|\bnwr\b|waterfowl production|national fish hatchery|wetland management district', 'US Fish & Wildlife Service'),
          (r'national forest|national grassland|ranger district', 'USDA Forest Service'),
          (r'\bblm\b|recreation management area|\bacec\b|\bhma\b|herd management|national conservation area|wilderness study', 'Bureau of Land Management'),
          (r'national (park|monument|historic(al)? (site|park|trail)|seashore|lakeshore|battlefield|memorial|preserve|river|scenic trail)', 'National Park Service (or the trail / monument partner)'),
          (r'corps|usace|\blake\b.*\b(project|dam)\b', 'US Army Corps of Engineers'),
          (r'\btva\b', 'Tennessee Valley Authority'),
          (r'national wildlife area|migratory bird sanctuary', 'Canadian Wildlife Service (ECCC)'),
          (r'national (park|historic site|marine conservation area) of canada|national historic site', 'Parks Canada'),
          (r'provincial park|provincial recreation area|ecological reserve|conservation reserve|wilderness area', '{P} provincial parks / protected areas'),
          (r'state park|state recreation (area|site)|state historic (site|park)|state beach|state natural area', '{S} state parks'),
          (r'wildlife management area|\bwma\b|\bswa\b|fish and wildlife area|game land|wildlife area|fishing (lake|area)|hatchery', '{S} fish & wildlife agency'),
          (r'state forest', '{S} state forestry'),
          (r'nature preserve|natural area|conservation area', '{S} natural areas program (or a land trust)'),
          (r'county|regional|city|municipal|town|metro|village', 'local government (county / city / regional)'),
          (r'trail', 'the trail\'s managing agency (state / federal / local)')]


def load(p, d=None):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d  # noqa: BLE001


def get_json(u, params=None):
    if not M: return None
    q = (u + ('&' if '?' in u else '?') + urllib.parse.urlencode({**(params or {}), 'f': 'json'}))
    try:
        st, hd, body, final = M.get(q, accept='application/json')
        return json.loads(body.decode('utf-8', 'replace')) if isinstance(st, int) and st < 400 and body else None
    except Exception: return None  # noqa: BLE001


# ------------------------------------------------------------------------------------------------ packets
def refs_in(text):
    return list(dict.fromkeys(m.group(1) for m in re.finditer(r'^\|\s*((?:US|CA)-\d{4,5})\b', text, re.M)))


def official(area):
    k = 'us-key' if area.startswith('US-') else 'ca-key'
    return {r for r, v in ((load(f'data/{k}/{area}.json', {}) or {}).get('parks') or {}).items() if isinstance(v, dict) and v.get('g') == 'official'}


def agency_guess(name, area):
    s, n = area[3:], STATES.get(area[3:], area[3:])
    for rx, ag in AGENCY:
        if re.search(rx, name or '', re.I): return ag.replace('{S}', n).replace('{P}', n)
    return '(not clear from the name)'


COUNTY_LAYER = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer'


def county(la, lo, cache):
    k = f'{la:.4f},{lo:.4f}'
    if k in cache: return cache[k]
    lay = cache.get('_layer')
    if lay is None:
        j = get_json(COUNTY_LAYER) or {}
        lay = next((l['id'] for l in j.get('layers') or [] if re.fullmatch(r'counties', str(l.get('name', '')), re.I)), None)
        cache['_layer'] = lay
    if lay is None: return ''
    j = get_json(f'{COUNTY_LAYER}/{lay}/query', {'geometry': f'{lo},{la}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326,
                                                 'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'NAME,BASENAME', 'returnGeometry': 'false'}) or {}
    f = (j.get('features') or [{}])[0].get('attributes') or {}
    cache[k] = f.get('NAME') or f.get('BASENAME') or ''
    return cache[k]


def tried_summary(area, r):
    out = []
    H = ((load(DATA / 'data' / 'gis-hunter' / f'{area}.json', {}) or {}))
    rec = (H.get('parks') or {}).get(r)
    if rec:
        a = sum(1 for t in rec.get('tried') or [] if t.startswith('A '))
        hits = sum(1 for t in rec.get('tried') or [] if t.startswith('A ') and t.endswith(': hit'))
        b = next((t for t in rec.get('tried') or [] if t.startswith('B ArcGIS')), '')
        b3 = next((t for t in rec.get('tried') or [] if t.startswith('B3')), '')
        out.append(f"GIS hunter {H.get('run', '')}: {a} layers asked at the pin ({hits} hit), result '{rec.get('verdict', '')[:60]}'" + (f'; {b[:70]}' if b else '') + (f'; {b3[:70]}' if b3 else ''))
    if area.startswith('US-'):
        d = ((load(DATA / 'data' / 'docs' / f'{area}.json', {}) or {}).get('parks') or {}).get(r) or {}
        m = d.get('map') or {}
        if d: out.append(f"documents bot {d.get('checked', '')}: map {m.get('kind') or ''} {str(m.get('status') or 'none')[:60]}" + (f" ({m.get('url')})" if m.get('url') else ''))
    nr = (load(DATA / 'data' / 'gis-hunter' / 'name-reads.json', {}) or {}).get(r)
    if nr: out.append(f"website name read {nr.get('date', '')}: '{str(nr.get('title', ''))[:60]}' ({nr.get('tier', '?')} vs POTA)")
    return out or ['nothing tried yet']


def packets(areas):
    cache = load(FB / '_counties.json', {}) or {}
    web = (load(DATA / 'data' / 'parkinfo-web.json', {}) or {}).get('parks') or {}
    n_files = n_lines = 0
    for f in sorted(FB.glob('*.md')):
        area = f.stem
        if areas and area not in areas: continue
        text = f.read_text(encoding='utf-8')
        off = official(area)
        P = ((load(DATA / 'data' / 'parkinfo' / f'{area}.json', {}) or {}).get('parks') or {}) if area.startswith('US-') else {}
        if area.startswith('CA-'):
            for row in (load(DATA / 'data' / 'canada.json', {}) or {}).get('rows') or []:
                if row and row[0] == 'POTA': P[row[1]] = [row[2], '', '', '', '', row[3], row[4]]
        lines = []
        for r in refs_in(text):
            if r in off: continue
            v = P.get(r) or []
            name = v[0] if v else ''
            la, lo = (v[5], v[6]) if len(v) > 6 else (None, None)
            site = (v[1] if len(v) > 1 and str(v[1]).startswith('http') else '') or (web.get(r) or {}).get('web') or (web.get(r) or {}).get('agency_page') or ''
            cty = county(la, lo, cache) if area.startswith('US-') and isinstance(la, (int, float)) else ''
            bits = [f'**{r}** {name}', f'pin {la}, {lo}' if la is not None else 'no pin on file', f'county {cty}' if cty else '',
                    f'agency guess: {agency_guess(name, area)}', f'website: {site}' if site else 'website: none on POTA',
                    'tried: ' + ' | '.join(tried_summary(area, r))]
            lines.append('- ' + ' · '.join(b for b in bits if b))
        sec = [f'## PARK PACKETS (bot, refreshed {TODAY}; read-only: chat 10 rewrites this section, put your finds in the park\'s row above)', ''] + (lines or ['- every park in this file has an official outline now']) + ['']
        body = re.sub(r'\n## PARK PACKETS \(bot[^\n]*\n.*?(?=\n## |\nSTATE [A-Z]{2} DONE|\Z)', '', text, flags=re.S).rstrip('\n')
        m = re.search(r'\nSTATE [A-Z]{2} DONE[^\n]*\s*\Z', body)
        new = (body[:m.start()] + '\n\n' + '\n'.join(sec) + body[m.start():] + '\n') if m else (body + '\n\n' + '\n'.join(sec))
        if new != text: f.write_text(new, encoding='utf-8'); n_files += 1
        n_lines += len(lines)
    json.dump(cache, open(FB / '_counties.json', 'w', encoding='utf-8'), indent=0)
    print(f'::notice title=Research helpers::packets: {n_lines} park lines in {n_files} files' + (f"; manners {M.stat}" if M else ''))


# ------------------------------------------------------------------------------------------------ atlas
def roots_in(text):
    rs = re.findall(r'server root:\s*(https?://\S+?/rest/services)\b', text)
    sec = re.search(r'## Agency servers / folders worth walking\n(.*?)(?=\n## |\Z)', text, re.S)
    if sec: rs += re.findall(r'(https?://[^\s)|]+?/rest/services(?:/[^\s)|]+)?)', sec.group(1))
    return list(dict.fromkeys(u.rstrip('/.,') for u in rs))


def crawl(root, cap_services=30, cap_layers=40):
    out, seen, todo = [], 0, [root]
    j = get_json(root) or {}
    if not j: return None
    folders = [f'{root.split("/rest/services")[0]}/rest/services/{f}' for f in (j.get('folders') or [])][:15] if root.endswith('/rest/services') else []
    svcs = [(s.get('name'), s.get('type')) for s in j.get('services') or []]
    for fu in folders:
        if len(svcs) >= cap_services * 2: break
        svcs += [(s.get('name'), s.get('type')) for s in (get_json(fu) or {}).get('services') or []]
    base = root.split('/rest/services')[0] + '/rest/services'
    svcs = [s for s in svcs if s[1] in ('MapServer', 'FeatureServer')]
    svcs.sort(key=lambda s: not PARKW.search(str(s[0])))   # park-looking services first
    for name, typ in svcs[:cap_services]:
        su = f'{base}/{name}/{typ}'
        sj = get_json(su) or {}
        for l in sj.get('layers') or []:
            if len(out) >= cap_layers: break
            if not (PARKW.search(str(l.get('name', ''))) or PARKW.search(str(name))): continue
            if l.get('subLayerIds'): continue
            lj = get_json(f'{su}/{l["id"]}') or {}
            if 'olygon' not in str(lj.get('geometryType', '')): continue
            nf = next((fd['name'] for fd in lj.get('fields') or [] if re.search(r'(^|_)(name|nom|unit_?nm|prop_?name|park_?name|site_?name|label)$', fd.get('name', ''), re.I)), '')
            out.append(f"  - {l.get('name')}: {su}/{l['id']} (name field {nf or '?'})")
    return out


def atlas(areas):
    n = 0
    for f in sorted(AT.glob('*.md')):
        area = f.stem
        if areas and area not in areas: continue
        text = f.read_text(encoding='utf-8')
        lines = []
        for root in roots_in(text)[:8]:
            res = crawl(root)
            if res is None: lines.append(f'- {root}: did not answer (or robots / resting)'); continue
            lines.append(f'- **{root}**: {len(res)} polygon layer(s) with park / boundary / recreation / wildlife / forest / lands words' + ('' if res else ' (none)'))
            lines += res
        sec = [f'## Layers on these servers (atlas crawler, {TODAY}; lists only, decides nothing; rewritten weekly)', ''] + (lines or ['- no server roots written above yet']) + ['']
        body = re.sub(r'\n## Layers on these servers \(atlas crawler[^\n]*\n.*?(?=\n## |\Z)', '', text, flags=re.S).rstrip('\n')
        new = body + '\n\n' + '\n'.join(sec)
        if new != text: f.write_text(new, encoding='utf-8'); n += 1
    print(f'::notice title=Research helpers::atlas: {n} files updated' + (f"; manners {M.stat}" if M else ''))


if __name__ == '__main__':
    mode, areas = (sys.argv[1] if len(sys.argv) > 1 else 'packets'), set(sys.argv[2:])
    try: {'packets': packets, 'atlas': atlas}[mode](areas)
    except Exception as e: print(f'::notice title=Research helpers::{mode} stopped ({type(e).__name__}: {e})')  # noqa: BLE001
    sys.exit(0)
