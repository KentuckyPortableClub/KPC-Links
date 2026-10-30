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
REF = r'(?:US|CA|[A-Z0-9]{1,4})-\d{4,5}'


def refs_in(text):
    return list(dict.fromkeys(m.group(1) for m in re.finditer(r'^\|\s*(' + REF + r')\b', text, re.M)))


_WP = None
def world_pins():
    global _WP
    if _WP is None:
        _WP = {}
        for f in glob.glob(str(DATA / 'data' / 'pota' / 't' / '*.json')):
            for row in load(f, []) or []:
                if isinstance(row, list) and len(row) >= 4: _WP[row[0]] = [row[1], '', '', '', '', row[2], row[3]]
    return _WP


def key_file(area):
    if area.startswith('US-'): return f'data/us-key/{area}.json'
    if area.startswith('CA-'): return f'data/ca-key/{area}.json'
    return f'data/world-key/{area[2:] if area.startswith("W-") else area}.json'


def official(area):
    return {r for r, v in ((load(key_file(area), {}) or {}).get('parks') or {}).items() if isinstance(v, dict) and v.get('g') == 'official' or (isinstance(v, dict) and v.get('m') and area.startswith('W-'))}


def source_of(area, r):
    v = ((load(key_file(area), {}) or {}).get('parks') or {}).get(r) or {}
    s = v.get('src') or [m[3] for m in v.get('m') or [] if isinstance(m, list) and len(m) > 3][:1]
    return ', '.join(s if isinstance(s, list) else [str(s)])[:60] or 'the key'


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
        if area.startswith('W-'): P = world_pins()
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


def old_section(text):
    """The crawler's last lists, per root: {root: [lines]} (so a push-run only crawls roots it has not seen yet)."""
    m = re.search(r'\n## Layers on these servers \(atlas crawler[^\n]*\n(.*?)(?=\n## |\Z)', text, re.S)
    out, cur = {}, None
    for l in (m.group(1).split('\n') if m else []):
        h = re.match(r'- \*\*(\S+?)\*\*:', l) or re.match(r'- (\S+): did not answer', l)
        if h: cur = h.group(1); out[cur] = [l]
        elif cur and l.startswith('  - '): out[cur].append(l)
    return out


def atlas(areas, only_new=False):
    n = 0
    for f in sorted(AT.glob('*.md')):
        area = f.stem
        if areas and area not in areas: continue
        text = f.read_text(encoding='utf-8')
        old = old_section(text)
        roots = roots_in(text)[:12]
        if only_new and not [r for r in roots if r not in old]: continue   # nothing new on this page: no work
        lines = []
        for root in roots:
            if only_new and root in old: lines += old[root]; continue
            res = crawl(root)
            if res is None: lines.append(f'- {root}: did not answer (or robots / resting)'); continue
            lines.append(f'- **{root}**: {len(res)} polygon layer(s) with park / boundary / recreation / wildlife / forest / lands words' + ('' if res else ' (none)'))
            lines += res
        sec = [f'## Layers on these servers (atlas crawler, {TODAY}; lists only, decides nothing; rewritten weekly)', ''] + (lines or ['- no server roots written above yet']) + ['']
        body = re.sub(r'\n## Layers on these servers \(atlas crawler[^\n]*\n.*?(?=\n## |\Z)', '', text, flags=re.S).rstrip('\n')
        new = body + '\n\n' + '\n'.join(sec)
        if new != text: f.write_text(new, encoding='utf-8'); n += 1
    print(f'::notice title=Research helpers::atlas: {n} files updated' + (f"; manners {M.stat}" if M else ''))


# ------------------------------------------------------------------------------------------------ solve (HQ 8:45 AM (1))
FINAL = re.compile(r'\bFINAL\b|picture-map-only|why-not:\s*private|\bprivate land\b', re.I)


def solve(areas):
    n_rows = n_done = 0
    for f in sorted(FB.glob('*.md')):
        area = f.stem
        if areas and area not in areas: continue
        text = f.read_text(encoding='utf-8')
        off = official(area)
        refs = refs_in(text)
        lines = text.split('\n'); marked = set()
        for i, l in enumerate(lines):
            m = re.match(r'^\|\s*(' + REF + r')\b', l)
            if not m or m.group(1) not in off or m.group(1) in marked or 'SOLVED' in l: continue
            if any(m.group(1) in x and 'SOLVED' in x for x in lines): marked.add(m.group(1)); continue
            lines[i] = l.rstrip().rstrip('|').rstrip() + f' · SOLVED {TODAY} (outline: {source_of(area, m.group(1))}) |'
            marked.add(m.group(1)); n_rows += 1
        text2 = '\n'.join(lines)
        if refs and not re.search(r'^STATE [A-Z0-9-]+ DONE', text2, re.M):
            def final(r): return r in off or any(r in l and FINAL.search(l) for l in lines)
            if all(final(r) for r in refs):
                text2 = text2.rstrip('\n') + f'\n\nSTATE {area} DONE (bot, {TODAY}: all {len(refs)} parks solved or tagged final)\n'; n_done += 1
        if text2 != text: f.write_text(text2, encoding='utf-8')
    print(f'::notice title=Research helpers::solve: {n_rows} rows marked SOLVED, {n_done} files marked DONE')


# ------------------------------------------------------------------------------------------------ inbox tidy + daily habits (HQ 8:45 AM (5) + (7))
IB = pathlib.Path('.claude/inbox')
HABITS = ("- **DAILY HABITS ({d}):** before today's work, skim .claude/build/research/KPC_Fable_Note_To_Opus_Efficiency.md: saved copies first · IDs beat names · "
          "polygons before pages · batch by agency / county · one book, one row, one why-not tag · sanity-check numbers · small independent samples · save as you go · "
          "stage, never ship · bulk off the website repo · write the ruling once · batched look-ups, official hosts only. Read the KPC-Data status board (data/status) "
          "first: open run logs / annotations only when the board says FAILED.")
MON = {m: i for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
CLOSED = re.compile(r'^- (?:\(\w\) )?(?:DONE|NOTED|ANSWERED|MOVED|BUILT|RELEASED|CLOSED)\b|^- \*\*DAILY HABITS|^- (?:Oct|Nov|Dec|Sep) \d{1,2}\b[^:]{0,40}:', re.I)   # done / answered items + old history lines ('- Oct 28 7:15 AM: ...')


def newest_date(block):
    ds = []
    for m in re.finditer(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* (\d{1,2})\b', block):
        try: ds.append(dt.date(dt.date.today().year, MON[m.group(1)], int(m.group(2))))
        except ValueError: pass
    for m in re.finditer(r'\b(20\d\d)-(\d\d)-(\d\d)\b', block):
        try: ds.append(dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError: pass
    ds = [d for d in ds if d <= dt.date.today() + dt.timedelta(days=1)]
    return max(ds) if ds else None


def blocks(body):
    out, cur = [], []
    for l in body.split('\n'):
        if l.startswith('- ') and cur: out.append('\n'.join(cur)); cur = []
        cur.append(l)
    if cur: out.append('\n'.join(cur))
    return out


def inbox(only):
    today = dt.date.today(); cut = today - dt.timedelta(days=2)   # older than 24 h, counted in whole days
    moved_all = 0
    for f in sorted(IB.glob('chat-*.md')):
        if only and f.stem not in only: continue
        text = f.read_text(encoding='utf-8'); before = len(text)
        parts = re.split(r'(?m)^(?=## )', text)
        keep, arch = [], []
        for sec in parts:
            head = sec.split('\n', 1)[0]
            if head.startswith('## OPEN -'):   # an item glued to a heading (old edit slip): read it as more OPEN items
                sec = '## OPEN (continued)\n- ' + head[len('## OPEN -'):].strip() + '\n' + (sec.split('\n', 1)[1] if '\n' in sec else ''); head = '## OPEN (continued)'
            if not head.startswith('## '): keep.append(sec); continue
            title, body = head, (sec.split('\n', 1)[1] if '\n' in sec else '')
            bs = blocks(body)
            lead = [b for b in bs if not b.startswith('- ')]
            items = [b for b in bs if b.startswith('- ')]
            if head.startswith('## OPEN'):
                first = head == '## OPEN'
                stay = []
                for b in items:
                    d = newest_date(b.split('\n', 1)[0])
                    if b.startswith('- **DAILY HABITS'): continue   # rewritten below
                    if CLOSED.search(b) and d and d <= cut: arch.append((title, b))
                    else: stay.append(b)
                if first: stay.insert(0, HABITS.format(d=today.strftime('%b %-d, %Y')))
                items = stay
            elif head.startswith('## DONE'):
                stay = []
                for b in items:
                    d = newest_date(b.split('\n', 1)[0])
                    (arch.append((title, b)) if d and d <= cut else stay.append(b))
                items = stay
            elif head.startswith('## REPORT TO HQ'):
                arch += [(title, b) for b in items[10:]]; items = items[:10]
            keep.append('\n'.join([title] + lead + items).rstrip('\n') + '\n\n')
        if not arch and HABITS.format(d=today.strftime('%b %-d, %Y')) in text: continue
        new = ''.join(keep).rstrip('\n') + '\n'
        if arch:
            (IB / 'archive').mkdir(exist_ok=True)
            af = IB / 'archive' / f'{f.stem}-{today:%Y-%m}.md'
            old = af.read_text(encoding='utf-8') if af.exists() else f'# {f.stem} archive {today:%Y-%m} (moved by the nightly inbox tidy; nothing deleted)\n'
            af.write_text(old.rstrip('\n') + f'\n\n## moved {today}\n' + '\n'.join(f'[{t[3:]}] {b}' for t, b in arch) + '\n', encoding='utf-8')
        f.write_text(new, encoding='utf-8'); moved_all += len(arch)
        print(f'::notice title=Inbox tidy::{f.stem}: {len(arch)} items moved, {before // 1024} -> {len(new) // 1024} KB')
    print(f'::notice title=Inbox tidy::{moved_all} items moved in all')


# ------------------------------------------------------------------------------------------------ weekly link check (HQ 8:45 AM (4))
def links(areas):
    urls = {}
    for f in glob.glob(str(DATA / 'data' / 'docs' / 'US-*.json')):
        for r, v in ((load(f, {}) or {}).get('parks') or {}).items():
            for k in ('map', 'rules'):
                u = ((v.get(k) or {}).get('url') or '')
                if u.startswith('http'): urls.setdefault(u, []).append(f'{r} {k}')
    for f in list(FB.glob('*.md')) + list(AT.glob('*.md')):
        for u in re.findall(r'https?://[^\s|)<>\]]+', f.read_text(encoding='utf-8')):
            u = u.rstrip('.,;')
            if '/rest/services' in u and not re.search(r'/(MapServer|FeatureServer)(/\d+)?$', u): continue
            urls.setdefault(u, []).append(f.stem)
    dead, n, t0 = [], 0, time.time()
    for u, where in sorted(urls.items()):
        if time.time() - t0 > 4 * 3600 or not M: break
        n += 1
        try:
            st, hd, body, final = M.get(u)
        except Exception as e: st = type(e).__name__  # noqa: BLE001
        if st in (404, 410) or (isinstance(st, str) and re.search(r'NameResolution|gaierror|URLError', st)):
            dead.append((u, st, where))
    L = [f'# Dead official links (weekly link check, {TODAY}; chat 8 reads this; no email, no comment)', '',
         f'{n} links checked (of {len(urls)}), {len(dead)} dead (404 / 410 / host gone). 403 / timeouts are NOT listed (often bot blocks).', '',
         '| link | answer | where we keep it |', '|---|---|---|'] + [f"| {u} | {st} | {', '.join(sorted(set(w))[:4])} |" for u, st, w in dead]
    (RES / 'dead-links.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(f'::notice title=Research helpers::links: {n} checked, {len(dead)} dead -> .claude/build/research/dead-links.md')


if __name__ == '__main__':
    mode, areas = (sys.argv[1] if len(sys.argv) > 1 else 'packets'), set(sys.argv[2:])
    try: {'packets': packets, 'atlas': atlas, 'atlas-new': lambda a: atlas(a, only_new=True), 'solve': solve, 'inbox': inbox, 'links': links}[mode](areas)
    except Exception as e: print(f'::notice title=Research helpers::{mode} stopped ({type(e).__name__}: {e})')  # noqa: BLE001
    sys.exit(0)
