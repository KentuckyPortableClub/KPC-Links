#!/usr/bin/env python3
"""RESEARCH INBOX for the problem solver (Nov 9 2026): reads research files in one format and re-checks just those parks; retry loop for held parks.

Reads every research file dropped in data/research-inbox/ (*.csv, *.json; format: docs/research-input-format.md), one row per park,
and runs the problem solver's sure test on JUST those parks. No key rebuild, nothing applied: it RECOMMENDS. Sure rows still go to
Quality and are signed only under the sure rule. The POTA pin is never moved (pins come from KPC-Data parkinfo; a row's own
pin is used only when parkinfo has none, and is never written back).

The sure test (= the sure rule, the same as kpc_problem_solver.py / the Nov 9 triage):
  - the record is a POLYGON (a point or a line is not a boundary);
  - the POTA pin is inside it or within 0.5 km;
  - the name fits (core words match; a typo-level difference, or the agency's own name with the park's number, counts);
  - the KIND of place does not clash (problem solver kind rule, Quality Nov 7 C1);
  - not an overlay (Natura 2000 / Ramsar / UNESCO / Emerald / SSSI ...) unless the park's own name says so;
  - no person said otherwise (overrides 'no', 'none', blocked_ids) and the park has no saved id already (else REJECTED: nothing to add).
Outlines: the saved copy first (RESEARCH_CACHE, default cache/research/<host-layer>.json), then an ALLOWED live read: robots.txt is
checked per host (a 401/403 robots answer = disallow), hosts on KPC_SAVED_ONLY_HOSTS are never read live (the sure rule), one request
per host per second, honest User-Agent. Every live read is saved to the cache (saved outlines first next time).

Out: data/research-inbox/results/<file stem>.json + .md (sure / needs person / rejected, with reasons) and the retry list
data/research-inbox/needs-another-look.json (the sure rule): every park still NEEDS PERSON / held, with its reason and the row, so the
next run after a new layer or a hand download re-checks just those parks (--retry). Never fails a build: exit 0 (selftest exits 1).
  python3 .github/scripts/kpc_research_inbox.py [--retry] [--offline] [--only FILE] [--selftest]"""
import unicodedata, csv, glob, json, math, os, pathlib, re, sys, time, urllib.parse, urllib.request, urllib.robotparser, datetime
import kpc_net_guard; kpc_net_guard.install()   # never-contact hosts refused before any request, redirect hops included

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
ROOT = pathlib.Path(__file__).resolve().parents[2]
UA = 'KPC (kentuckyportableclub.github.io)'
SURE_KM = 0.5
COLS = ['pota_ref', 'park_name', 'layer_url', 'record_id', 'official_name', 'owner', 'confidence', 'notes', 'source', 'pin_lat', 'pin_lon']
HOLD = {h.strip().lower() for h in (os.environ.get('KPC_SAVED_ONLY_HOSTS') or
        'services.arcgis.com,services1.arcgis.com,apps.fs.usda.gov').split(',') if h.strip()}
NEVER = ('services.arcgis.com/33tooklri9xpic7u', 'ncnhde.natureserve.org')   # standing rules: never any request
GENERIC = set(('state park parks wildlife management area areas wma national forest forests refuge nwr recreation natural wild scenic river rivers '
               'the of and at on sp sra wilderness preserve nature conservation game lands land public fishing lake historic historical site monument '
               'memorial trail county city municipal federal us usfws fws blm nf sf wa campground seashore lakeshore pfa sgl sna shs '
               'provincial regional reserve ecological protected parc national de du la le des et reserve reserva parque natural nacional naturpark '
               'country nature reserves nnr lnr sssi wood woods forest '
               # the sure rule: French generic words (accents are folded first): Parc, Reserve nationale de faune, Aire protegee ...
               'nationale faune provinciale aire aires protegee protegees ecologique faunique refuge oiseaux migrateurs nwa '
               # kind words that are not a place's own name (world and Canada layers)
               'quasi prefectural biosphere canada parco regionale nazionale riserva naturale').split())
ABBR2 = set(('al ak az ar ca co ct de fl ga hi id il in ia ks ky la me md ma mi mn ms mo mt ne nv nh nj nm ny nc nd oh ok or pa ri sc sd tn tx ut vt va wa wv wi wy '
             'ab bc mb nb nl ns nt nu on pe qc sk yt').split())   # a state / province code in a POTA name ('PA 046 State Game Land')
OVERLAY = re.compile(r'natura\s*2000|\bramsar\b|unesco|world heritage|biosphere|emerald|\bsssi\b|\bsac\b|\bspa\b|\bsci\b|special area of conservation|'
                     r'special protection area|site of special scientific interest|important bird', re.I)
KINDS = [('history', r'histor|massacre|battle|monument|memorial|fort\b|lighthouse|heritage'), ('wildlife', r'refuge|\bnwr\b|wildlife|waterfowl|hatchery|\bwma\b|\bgame\b'),
         ('forest', r'forest|\bsf\b'), ('wild', r'wilderness|\bwsa\b'), ('recreation', r'recreation|\brma\b|\bsrma\b|\bnra\b|\bsra\b'),
         ('water', r'reservoir|\bdam\b'), ('park', r'\bpark\b|\bsp\b|preserve|natural area'),
         ('nature', r'conservation reserve|ecological reserve|nature reserve|r[ée]serve [ée]cologique'), ('trail', r'\btrail\b'),
         ('fishing', r'fishing|\bpfa\b|hatchery'), ('river', r'wild (?:and|&) scenic|scenic river')]   # Nov 9 spot check: 'State Fishing Lake' is not a 'State Forest'
# a record that is a piece or a facility, not the park's land (Cypremort Point 'wlf Field Off'; NRHP '(Boundary Increase)')
PIECE = re.compile(r'field off|\boffice\b|headquarters|\bhq\b|parking|boat ramp|launch|boundary increase|\btract\b|addition\b', re.I)
# a part of a bigger place ('Stuart's Landing NORTH', 'Salem UNIT of ...'): never an alias of the whole place
PART = re.compile(r'\b(north|south|east|west|upper|lower|little|unit|tract|s\.?e\.?|n\.?w\.?)\b')
# a water-surface layer (lake polygons) is only the park when the park IS the lake
WATER_LAYER = re.compile(r'public_lakes|fishing waterbod|agfc_data/mapserver/9|twra/mapserver/2|/lakes/', re.I)


STATE_AFTER_COMMA = re.compile(r',\s*(?:' + '|'.join(['alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado', 'connecticut', 'delaware', 'florida', 'georgia', 'hawaii', 'idaho', 'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana', 'maine', 'maryland', 'massachusetts', 'michigan', 'minnesota', 'mississippi', 'missouri', 'montana', 'nebraska', 'nevada', 'new hampshire', 'new jersey', 'new mexico', 'new york', 'north carolina', 'north dakota', 'ohio', 'oklahoma', 'oregon', 'pennsylvania', 'rhode island', 'south carolina', 'south dakota', 'tennessee', 'texas', 'utah', 'vermont', 'virginia', 'washington', 'west virginia', 'wisconsin', 'wyoming', 'alberta', 'british columbia', 'manitoba', 'new brunswick', 'newfoundland and labrador', 'nova scotia', 'ontario', 'quebec', 'saskatchewan', 'yukon']) + r')\b')


def core(n):
    # the sure rule: accents folded, so the French and English names of a Canadian park (NAME_E / NAME_F, both read) match plainly
    n = ''.join(c for c in unicodedata.normalize('NFKD', str(n or '')) if not unicodedata.combining(c))
    n = STATE_AFTER_COMMA.sub(' ', n.lower())   # 'Kern, California National Wild and Scenic River': the agency adds the state
    n = re.sub(r'\bst\.?\b', 'saint', n); n = re.sub(r'\bmt\.?\b', 'mount', n); n = re.sub(r'\bft\.?\b', 'fort', n)
    n = re.sub(r'\b0+(\d)', r'\1', n)          # 'PA 046' = '46'
    return {w[:-1] if len(w) > 3 and w.endswith('s') and not w.endswith('ss') else w
            for w in re.findall(r'[a-z0-9à-ÿ]+', n) if w not in GENERIC and w not in ABBR2 and len(w) > 1}


def lev1(a, b):
    """one letter swapped / changed / added: 'echtoa' ~ 'echota'"""
    if a == b: return True
    if abs(len(a) - len(b)) > 1 or min(len(a), len(b)) < 5: return False
    if len(a) == len(b):
        d = [i for i in range(len(a)) if a[i] != b[i]]
        return len(d) == 1 or (len(d) == 2 and d[1] == d[0] + 1 and a[d[0]] == b[d[1]] and a[d[1]] == b[d[0]])
    s, l = sorted((a, b), key=len)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


def name_ok(park, rec):
    """the SAME core words (generic words, accents and state names left out), or a one-letter typo of them, or the park's number
    inside the agency's own name. Nov 9 spot check (Funk Island Deep Closure, Siloam Springs Buckhorn Unit, North/Lower Armit River):
    an extra distinctive word on either side is a different place or a piece, so it is a person's call, not sure."""
    A, B = core(park), core(rec)
    if not A or not B: return False
    if A == B: return True
    if all(w.isdigit() for w in A) and A <= B: return True     # 'PA 046 State Game Land' = '46 - Middle Creek WMA'
    if len(A) != len(B): return False
    return all(any(lev1(x, y) for y in B) for x in A) and all(any(lev1(y, x) for x in A) for y in B)


def kinds(n): return {k for k, rx in KINDS if re.search(rx, str(n or ''), re.I)}


def kind_clash(a, b):
    A, B = kinds(a), kinds(b); return bool(A) and bool(B) and not (A & B)


def km_to(lat, lon, rings):
    """0.0 when the pin is inside (even-odd over every ring), else the km to the nearest edge (local flat earth: fine at < 50 km)."""
    k = math.cos(math.radians(lat)); P = [[((x - lon) * 111.32 * k, (y - lat) * 110.57) for x, y in r[:]] for r in rings if len(r) >= 3]
    inside = False
    for r in P:
        for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
            if (y1 > 0) != (y2 > 0) and 0 < (x2 - x1) * (0 - y1) / ((y2 - y1) or 1e-12) + x1: inside = not inside
    if inside: return 0.0
    best = None
    for r in P:
        for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
            dx, dy = x2 - x1, y2 - y1; t = max(0, min(1, -(x1 * dx + y1 * dy) / ((dx * dx + dy * dy) or 1e-12)))
            d = math.hypot(x1 + t * dx, y1 + t * dy); best = d if best is None or d < best else best
    return None if best is None else round(best, 3)


def rings_of(g):
    if not g: return []
    if 'rings' in g: return g['rings']
    t = g.get('type'); c = g.get('coordinates') or []
    if t == 'Polygon': return c
    if t == 'MultiPolygon': return [r for p in c for r in p]
    return []


def is_poly(g): return bool(g) and ('rings' in g or g.get('type') in ('Polygon', 'MultiPolygon'))


def nurl(u):
    u = str(u or '').strip().split('?')[0].rstrip('/'); u = re.sub(r'/query$', '', u); return u


# ---- reading records: saved copy first, then an allowed live read
class Reader:
    def __init__(self, cache, offline=False):
        self.cache = pathlib.Path(cache); self.offline = offline; self.rb = {}; self.last = {}; self.mem = {}; self.live = 0; self.why_not = {}
        self.hmem = {}
        try: self.handmap = {nurl(k).lower(): v for k, v in json.load(open(os.environ['RESEARCH_HAND'], encoding='utf-8')).items()}
        except Exception: self.handmap = {}  # noqa: BLE001

    def _cfile(self, url): return self.cache / (re.sub(r'[^A-Za-z0-9]+', '_', re.sub(r'^https?://', '', url))[:150] + '.json')

    def _load(self, url):
        if url not in self.mem:
            f = self._cfile(url)
            try: self.mem[url] = json.load(open(f, encoding='utf-8'))
            except Exception: self.mem[url] = {'url': url, 'recs': {}, 'near': {}}  # noqa: BLE001
        return self.mem[url]

    def save(self):
        self.cache.mkdir(parents=True, exist_ok=True)
        for url, d in self.mem.items():
            if d.get('dirty'): d.pop('dirty'); json.dump(d, open(self._cfile(url), 'w', encoding='utf-8'), separators=(',', ':'))

    def allowed(self, url):
        p = urllib.parse.urlparse(url); host = p.netloc.lower(); low = url.lower()
        if any(n in low for n in NEVER): return False, 'never read (standing rule)'
        if host in HOLD or not kpc_net_guard.host_ok(url)[0]:   # the shared rule: every services*.arcgis.com, any port / user@ / trailing dot
            return False, f'{kpc_net_guard.host_of(url) or host}: saved copy only (no live reads while its robots.txt answers 403)'
        if self.offline: return False, 'offline run'
        if host not in self.rb:
            try:
                r = urllib.request.urlopen(urllib.request.Request(f'{p.scheme}://{p.netloc}/robots.txt', headers={'User-Agent': UA}), timeout=25)
                body = r.read().decode('utf-8', 'replace'); rp = urllib.robotparser.RobotFileParser()
                rp.parse(body.splitlines() if '<html' not in body[:300].lower() else []); self.rb[host] = rp
            except urllib.error.HTTPError as e: self.rb[host] = 'deny' if e.code in (401, 403) else None
            except Exception: self.rb[host] = 'down'  # noqa: BLE001
        rp = self.rb[host]
        if rp == 'deny': return False, f'{host}: robots.txt answers 401/403 (= disallow)'
        if rp == 'down': return False, f'{host}: did not answer'
        if rp is not None and not rp.can_fetch(UA, url): return False, f'{host}: robots.txt disallows this path'
        return True, ''

    def _get(self, url, q):
        host = urllib.parse.urlparse(url).netloc
        w = 1.0 - (time.time() - self.last.get(host, 0))
        if w > 0: time.sleep(w)
        self.last[host] = time.time(); self.live += 1
        req = urllib.request.Request(url + '/query?' + urllib.parse.urlencode(q), headers={'User-Agent': UA})
        j = json.loads(urllib.request.urlopen(req, timeout=90).read().decode('utf-8', 'replace'))
        if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:120])
        return j

    def hand(self, url, lat, lon, km):
        """a hand download for a layer we cannot read live (RESEARCH_HAND = JSON {layer url: file}); read with geopandas, kept in memory"""
        f = (self.handmap or {}).get(nurl(url).lower())
        if not f or f.startswith('http'): return None
        if f not in self.hmem:
            import geopandas as gpd  # noqa: E402  (only when a hand file is used)
            try:
                lay = None
                if '.gdb' in f.lower():   # a file geodatabase: its own-named polygon layer (CPCAD's first layer is a comment table)
                    import pyogrio  # noqa: E402
                    L = [n for n, t in pyogrio.list_layers(f) if t]; stem = re.sub(r'\.gdb$', '', f.rstrip('/').split('/')[-1], flags=re.I)
                    lay = stem if stem in L else (L[0] if L else None)
                g = gpd.read_file(f, layer=lay) if lay else gpd.read_file(f); g = g.to_crs(4326) if g.crs else g; self.hmem[f] = g
            except Exception as e:  # noqa: BLE001
                self.hmem[f] = None; print(f'hand file {f} not read: {e}')
        g = self.hmem[f]
        if g is None: return None
        from shapely.geometry import box as _box  # noqa: E402
        dl = km / 110.57; dx = km / (111.32 * max(.1, math.cos(math.radians(lat))))
        hit = g.iloc[g.sindex.query(_box(lon - dx, lat - dl, lon + dx, lat + dl), predicate='intersects')]
        out = {}
        for i, row in hit.iterrows():
            geom = row.geometry; polys = [geom] if geom.geom_type == 'Polygon' else list(getattr(geom, 'geoms', []))
            rings = [[list(c[:2]) for c in pg.exterior.coords] for pg in polys if pg.geom_type == 'Polygon'] + \
                    [[list(c[:2]) for c in r.coords] for pg in polys if pg.geom_type == 'Polygon' for r in pg.interiors]
            a = {k: (v if isinstance(v, (str, int, float)) else str(v)) for k, v in row.drop(labels='geometry').items() if v is not None and str(v) != 'nan'}
            oid = next((a[k] for k in a if str(k).lower() in ('objectid', 'fid', 'oid')), i)
            out[str(oid)] = {'a': a, 'r': rings, 'poly': geom.geom_type in ('Polygon', 'MultiPolygon'), 'hand': f,
                             **({'pt': [geom.x, geom.y]} if geom.geom_type == 'Point' else {})}
        return out

    def near(self, url, lat, lon, km=SURE_KM + 0.1):
        """the polygons within ~0.6 km of the pin: {id: {'n': names..., 'a': attrs, 'r': rings, 'poly': bool}}, or (None, why)"""
        url = nurl(url); d = self._load(url); key = f'{lat:.5f},{lon:.5f}'
        if not re.search(r'/(MapServer|FeatureServer)/\d+$', url, re.I):
            h = self.hand(url, lat, lon, km)
            return (h, f'hand copy {pathlib.Path(self.handmap[nurl(url).lower()]).name}') if h is not None else (None, 'not an ArcGIS REST layer (WFS / open-data API / web page): needs a hand download')
        if key in d['near']:
            got = {i: d['recs'][i] for i in d['near'][key] if i in d['recs']}
            if not any(not r.get('poly') and not r.get('pt') for r in got.values()): return got, 'saved copy'
            # (a copy saved before Nov 9 6:50 PM kept no point position: read it again for the sure rule POINT-CONFIRMED)
        ok, why = self.allowed(url)
        if not ok:
            alt = (self.handmap or {}).get(url.lower(), '')
            if alt.startswith('http'):   # the same data published on an allowed host (PAD-US Fee on edits.nationalmap.gov)
                r, how = self.near(alt, lat, lon, km); return r, f'{how} on the allowed copy {urllib.parse.urlparse(alt).netloc} ({why.split(":")[0]} not read)'
            h = self.hand(url, lat, lon, km)
            return (h, f'hand copy {pathlib.Path(self.handmap[nurl(url).lower()]).name} ({why.split(":")[0]} not read live)') if h is not None else (None, why)
        dl = km / 110.57; dx = km / (111.32 * max(.1, math.cos(math.radians(lat))))
        q = {'geometry': f'{lon - dx},{lat - dl},{lon + dx},{lat + dl}', 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
             'spatialRel': 'esriSpatialRelIntersects', 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326,
             'maxAllowableOffset': 0.0002, 'geometryPrecision': 5, 'resultRecordCount': 50, 'f': 'json'}
        try: j = self._get(url, q)
        except Exception as e: return None, f'live read failed ({type(e).__name__}: {str(e)[:80]})'  # noqa: BLE001
        ids = []
        for f in j.get('features') or []:
            a = f.get('attributes') or {}; oid = next((a[k] for k in a if k.lower() in ('objectid', 'fid', 'objectid_1', 'oid')), None)
            if oid is None: continue
            g = f.get('geometry') or {}
            d['recs'][str(oid)] = {'a': {k: v for k, v in a.items() if isinstance(v, (str, int, float)) and len(str(v)) < 200},
                                   'r': g.get('rings') or [], 'poly': 'rings' in g, 'gt': j.get('geometryType'),
                                   **({'pt': [g['x'], g['y']]} if 'x' in g and 'y' in g else {})}
            ids.append(str(oid))
        d['near'][key] = ids; d['dirty'] = True; d['read'] = datetime.date.today().isoformat()
        if self.live % 40 == 0: self.save()
        return {i: d['recs'][i] for i in ids}, 'live read (saved now)'


def rec_names(rec):
    return [str(v) for k, v in (rec.get('a') or {}).items() if isinstance(v, str) and re.search(r'name|nom|nm|label|site|title|desig|unit|prop|area|park|desc_en|desc_fr', k, re.I)
            and not re.search(r'url|link|web|code|type|globalid|date|status|iucn|own|mang|manag|agency|gov|iso|parent|sub_loc|source|verif', k, re.I) and len(v) > 2]


def overlay_rec(rec):
    a = rec.get('a') or {}
    return ' '.join(str(a.get(k) or '') for k in a if re.search(r'desig|type|category', k, re.I))


WDPA = re.compile(r'wdpa|protectedplanet|protected_planet|unep-?wcmc|world_database_of_protected', re.I)

# ---- Nov 11 2026: WDPA / Protected Planet is a lead only and never data in a tracked file. An ID (WDPA:123, SAPAD-WDPAID:123, "WDPA 123",
# "WDPA id (123)") or a protectedplanet.net address is data; the word WDPA in a sentence ("WDPA is a lead only") is not.
WDPA_MARK = '[WDPA lead removed]'
WDPA_URL = re.compile(r'(?:https?://)?(?:[\w-]+\.)*protected[\s_-]?planet\.net[^\s,;|)\]"\']*', re.I)
WDPA_ID = re.compile(r'(?:[A-Za-z]+-)?WDPA(?:ID|_?PID)?(?:\s+id)?\s*[:#=]?\s*(?:\(\d+\)|\d+)', re.I)
WDPA_DATA = re.compile(r'wdpa[a-z_]*(?:\s+id)?\s*[:#=]?\s*\(?\d|protected[\s_-]?planet\.net', re.I)   # what the test hunts for


def has_wdpa_data(text): return bool(WDPA_DATA.search(str(text or '')))


def scrub_wdpa(text):
    """Replace WDPA ids and Protected Planet addresses with a plain marker (the sentence around them stays)."""
    t = WDPA_URL.sub(WDPA_MARK, str(text)); t = WDPA_ID.sub(WDPA_MARK, t)
    return t.replace(WDPA_MARK + WDPA_MARK, WDPA_MARK)


def scrub_obj(o):
    """scrub_wdpa over every string in a result / retry-list structure (lists, dicts, text), so a run can never write a WDPA id or address back"""
    if isinstance(o, str): return scrub_wdpa(o) if has_wdpa_data(o) else o
    if isinstance(o, list): return [scrub_obj(x) for x in o]
    if isinstance(o, dict):
        d = {k: scrub_obj(v) for k, v in o.items()}
        if 'wdpa_lead' in d:   # a WDPA-layer lead: its record id IS a WDPA id, so the id fields go too (the reason keeps the plain sentence)
            d.update(wdpa_lead=WDPA_MARK, record_id='')
        return d
    return o


# ---- the answers / solved ledger (Nov 11 2026): data/research-inbox/answers/solved-ledger.csv. Read only: it never writes a key, an override or a pin.
# A sub-folder on purpose: the inbox glob (inbox_files) reads only the files straight in data/research-inbox/, so nothing under answers/ is a batch.
ANSWERS_DIR = 'data/research-inbox/answers'
LEDGER_REL = ANSWERS_DIR + '/solved-ledger.csv'
ANSWER_WORDS = ('match', 'no boundary exists', 'wrong pin', 'other', '')   # the hand-back vocabulary, exactly


def classify_solved(answer, official_id='', source_url='', key_location='', key_status='', wdpa_removed=False):
    """(solved, basis): is this park finished, so no search list / retry list / owner short list hands it out again?
    SOLVED:  'released-key'          the released key already grades it official;
             'settled-match'         answer `match` AND a non-WDPA official id or official source url (a match that rested on a removed WDPA lead
                                     and has no other official id is NOT solved);
             'settled-no-boundary'   answer `no boundary exists` (the agency shows a road, a marker or a monument: nothing to outline).
    NOT SOLVED: `wrong pin` (the pin is flagged, the place is not found), `other` (a person must decide), blank (nothing official found; the note
    says what was searched). The answer words are the Nov 5 / Nov 11 vocabulary exactly."""
    a = str(answer or '').strip(); oid = str(official_id or '').strip(); url = str(source_url or '').strip()
    if a not in ANSWER_WORDS: return False, 'unknown-answer'
    if str(key_location or '').startswith('released-') and str(key_status or '').strip().lower() == 'official': return True, 'released-key'
    if a == 'no boundary exists': return True, 'settled-no-boundary'
    if a == 'match':
        if wdpa_removed and not oid: return False, 'match-rested-on-removed-wdpa-lead'
        if oid or url: return True, 'settled-match'
        return False, 'match-without-official-id'
    return False, {'wrong pin': 'wrong-pin', 'other': 'other-needs-person', '': 'blank-nothing-found'}[a]


# Owner answers recorded 2026-11-11. These are not pending: they have been decided.
# US-10274: the National Register record is the whole 6,908-acre battlefield (the bigger place).
# FR-14979: owner no to the 13 km ZNIEFF join; the live world-key join comes off on the next world key run.
OWNER_NOT_A_MATCH = {
    'US-10274': 'not a match, 2026-11-11: the National Register record is the whole 6,908-acre battlefield (the bigger place); needs the Texas Historical Commission site outline',
    'FR-14979': 'owner no, 2026-11-11: the official record is 13 km from the pin; the live join comes off on the next world key run',
}
# ZA-0085, ZA-0156, ZA-0157: their official ids were WDPA-derived and were removed; they stay unsolved.
OWNER_UNSOLVED_WDPA = {'ZA-0085', 'ZA-0156', 'ZA-0157'}
OWNER_UNSOLVED_WDPA_WHY = 'owner 2026-11-11: stays unsolved; the official id was a WDPA lead and was removed; needs a non-WDPA official id'
OWNER_YES_NOV5_WHY = 'owner settled the Nov 5 confirm on 2026-11-11'
# Recorded owner answers (Brandon accepted the recommendations in chat on 2026-11-11 at 21:16 CT).
# File: data/research-inbox/answers/OWNER-ANSWERS-nov11.md
OWNER_ANSWER_CITE = {
    'US-10274': 'owner chat 2026-11-11 21:16 CT, OWNER-ANSWERS-nov11.md item 7',
    'FR-14979': 'owner chat 2026-11-11 21:16 CT, OWNER-ANSWERS-nov11.md item 2',
}
OWNER_ANSWER_ITEM10 = 'owner chat 2026-11-11 21:16 CT, OWNER-ANSWERS-nov11.md item 10'


def classify_row(answer, official_id='', source_url='', key_location='', key_status='', wdpa_removed=False, confirm='', match_strength='', ref=''):
    """classify_solved split in two (Nov 11 review), with the 2026-11-11 owner answers recorded:
    skip_search     = the research is finished, so no search list hands the park out again (the classify_solved rule, plus OWNER_NOT_A_MATCH);
    owner_decision  = 'pending' for a finished match that still waits on an OWNER yes: a National Register listing boundary
                      (not automatically the park). 'yes' for a Nov 5 confirm the owner settled on 2026-11-11. 'no' for a
                      park the owner said is not a match (US-10274, FR-14979). A released-key park never waits.
    join_ready      = 'no' for a match that is pending an owner yes or whose boundary is written in law with no map file; 'yes' for other solved matches."""
    solved, basis = classify_solved(answer, official_id, source_url, key_location, key_status, wdpa_removed)
    decision, why = '', ''
    if ref in OWNER_NOT_A_MATCH:
        # Owner said this is not a match, even if a Nov 11 row still said match with an official id.
        solved, basis = False, 'other-needs-person' if str(answer or '').strip() in ('other', 'match', '') else basis
        if str(answer or '').strip() == 'match' and basis == 'released-key':
            # a released-key official grade is not undone by this (none of today's not-a-match parks are released official)
            pass
        decision, why = 'no', OWNER_NOT_A_MATCH[ref]
        cite = OWNER_ANSWER_CITE.get(ref, '')
        return {'skip_search': False, 'solved_basis': 'other-needs-person', 'owner_decision': decision,
                'owner_decision_why': why, 'owner_answer': cite, 'join_ready': '', 'join_note': why}
    pending = False
    cite = ''
    if solved and basis == 'settled-match':
        if confirm:
            decision, why = 'yes', f'{OWNER_YES_NOV5_WHY} ({confirm})'
            cite = OWNER_ANSWER_ITEM10
        elif str(match_strength).startswith('nrhp-listing-boundary'):
            pending, why = True, 'National Register listing boundary: not automatically the park'
            decision = 'pending'
    if not solved and ref in OWNER_UNSOLVED_WDPA:
        why = OWNER_UNSOLVED_WDPA_WHY
        cite = OWNER_ANSWER_ITEM10
    law = match_strength == 'boundary-in-law-no-map-file'
    jr, note = '', ''
    if solved and answer == 'match':
        if pending: jr, note = 'no', 'owner decision pending'
        elif law: jr, note = 'no', 'boundary written in law only, no map file'
        else: jr, note = 'yes', ''
    return {'skip_search': solved, 'solved_basis': basis, 'owner_decision': decision, 'owner_decision_why': why,
            'owner_answer': cite, 'join_ready': jr, 'join_note': note}


def load_ledger(root=ROOT, path=None):
    """{ref: ledger row} from solved-ledger.csv; {} when the file is not there (older checkouts keep working)"""
    p = pathlib.Path(path) if path else pathlib.Path(root) / LEDGER_REL
    try: rows = list(csv.DictReader(open(p, encoding='utf-8-sig', newline='')))
    except OSError: return {}
    return {r['ref']: r for r in rows if r.get('ref')}


def is_solved(ref, ledger): return str((ledger or {}).get(ref, {}).get('solved', '')).strip().lower() == 'yes'


def owner_pending(ref, ledger): return str((ledger or {}).get(ref, {}).get('owner_decision', '')).strip().lower() == 'pending'


def is_skipped(ref, ledger):
    """solved AND no owner decision pending: only these leave the retry list, the owner short list and the inbox run"""
    return is_solved(ref, ledger) and not owner_pending(ref, ledger)


def solved_refs(ledger): return {r for r in (ledger or {}) if is_solved(r, ledger)}


def filter_unsolved(rows, ledger, key='pota_ref'):
    """(kept, skipped): rows of a retry list / batch, split by the ledger (solved and no owner decision pending go to skipped); the order is kept"""
    kept, skipped = [], []
    for r in rows: (skipped if is_skipped(r.get(key) or r.get('ref'), ledger) else kept).append(r)
    return kept, skipped


def inbox_files(root=ROOT):
    """the research batches: *.csv / *.json straight in data/research-inbox/ (NOT sub-folders: answers/ and results/ are never batches)"""
    d = pathlib.Path(root) / 'data/research-inbox'
    return sorted(str(f) for f in list(d.glob('*.csv')) + list(d.glob('*.json')) if f.name != 'needs-another-look.json')



def official_layers(cc, root=ROOT):
    """the country's own official layers we already know (world key lists): [(label, url)], and the agency named for it"""
    out, agency = [], ''
    try:
        for L in (json.load(open(pathlib.Path(root) / 'data/world-key/extra-layers.json', encoding='utf-8')).get('countries') or {}).get(cc) or []:
            if L.get('url') and not WDPA.search(L['url']): out.append((L.get('label') or '', L['url']))
    except Exception: pass  # noqa: BLE001
    try:
        S = (json.load(open(pathlib.Path(root) / 'data/world-key/sheet-countries.json', encoding='utf-8')).get('countries') or {}).get(cc) or {}
        agency = S.get('agency') or ''
        for L in S.get('layers') or []:
            if L.get('url') and not WDPA.search(L['url']) and L['url'] not in [u for _, u in out]: out.append((L.get('label') or '', L['url']))
    except Exception: pass  # noqa: BLE001
    return out, agency


def wdpa_lead(row, pin, ov, saved, rd, out, fit, oid, rec):
    """WDPA is never official, but its match is a LEAD (standing step): try the same park on the country's own official layers with
    the same sure test (0.5 km cap, name fits). Sure there = SURE on the official polygon. Else a named next step: the official layer to
    download for that country (WDPA's own designation and managing agency say whose layer it is)."""
    a = rec.get('a') or {}
    desig = next((str(v) for k, v in a.items() if re.fullmatch(r'desig(_eng)?', str(k), re.I) and v), '')
    mang = next((str(v) for k, v in a.items() if re.fullmatch(r'mang_auth|gov_type', str(k), re.I) and v), '')
    cc = str(row.get('pota_ref') or '').split('-')[0].upper()
    lays, agency = official_layers(cc)
    tried = []
    if not row.get('_lead'):
        for lab, u in lays:
            r2 = _judge(dict(row, layer_url=u, record_id='(lead)', _lead=1), pin, ov, saved, rd)
            tried.append(f"{lab or u}: {r2['status']}")
            if r2['status'] == 'SURE':
                return dict(r2, wdpa_lead=oid, reason=r2['reason'] + f' (found from the WDPA lead {oid} "{fit}"; WDPA itself is not used)')
    who = agency or mang or 'the national protected-area agency'
    step = (f'download the official {cc} protected-area layer ({who}' + (f'; WDPA says designation "{desig}"' if desig else '') + ')') if not lays else \
           f'the official {cc} layer(s) did not give a sure match ({"; ".join(tried)[:200]}): a person compares, or download a fuller official layer ({who})'
    return dict(out, status='NEEDS PERSON', retry='official-layer', wdpa_lead=oid, next_step=step, country=cc, official_layers=len(lays),
                reason=f'WDPA match "{fit}" ({oid}) is a lead only, not an official boundary; next step: {step}')


# ---- one row
SFN = 'SOLUTION FOUND vs earlier NO'


def judge(row, pin, ov, saved, rd):
    """Earlier NO (Nov 9 2026): an earlier human NO does not stop the test. A sure match over it is SOLUTION FOUND vs earlier NO,
    never signed, and goes on the owner's short flip list. A point over it gets no circle until it is flipped. Everything else keeps the normal sure rule."""
    no = [str(x) for x in ov.get('no') or []]; blk = [str(x) for x in ov.get('_blocked') or []]
    if not (ov.get('none') or no or blk): return _judge(row, pin, ov, saved, rd)
    r = _judge(row, pin, {k: v for k, v in ov.items() if k not in ('none', 'no', '_blocked')}, saved, rd)
    why = str(ov.get('why') or '')
    dm = re.search(r'\b(20\d\d-\d\d-\d\d|(?:Oct|Nov|Sep|Dec)\w* \d{1,2})\b', why)
    ed = {'decision': '; '.join(x for x in ['no outline of its own (none: true)' if ov.get('none') else '', ('NO to ' + ', '.join(no)) if no else '',
                                           ('blocked ids ' + ', '.join(blk)) if blk else ''] if x),
          'date': ov.get('when') or (dm.group(1) if dm else ''), 'by': ov.get('decided_by') or '', 'why': why[:300]}
    rid, rnm = str(r.get('record_id') or ''), str(r.get('record_name') or '').lower()
    same = bool(rid) and any(rid == x or x.endswith(rid) and not x[-len(rid) - 1:-len(rid)].isdigit() or x.lower() == rnm for x in no + blk)
    r['earlier_no'] = ed
    if r['status'] == 'SURE':
        return dict(r, status=SFN, same_record_as_no=same, retry='brandon',
                    reason=f"{r['reason']} | earlier NO ({ed['date'] or 'no date'}): {ed['decision']}" + (' (the SAME record that was said NO to)' if same else '') + '; not signed: on the owner\'s flip list')
    if r['status'] == 'POINT-CONFIRMED':
        return dict(r, status=SFN, retry='brandon', point_only=True, reason=f"{r['reason']} | earlier NO ({ed['date'] or 'no date'}): {ed['decision']}; no circle until it is flipped")
    r['reason'] = f"{r['reason']} (earlier NO on file, {ed['date'] or 'no date'}: stays)"
    return r


def _judge(row, pin, ov, saved, rd):
    ref, name = row.get('pota_ref'), row.get('park_name') or ''
    out = {'pota_ref': ref, 'park_name': name, 'layer_url': row.get('layer_url'), 'file_record_id': row.get('record_id')}
    if saved: return dict(out, status='REJECTED', reason=f'already has a saved ID ({saved}); nothing to add')
    if not row.get('layer_url') or str(row.get('record_id') or '').strip().upper() in ('', 'NONE'):
        return dict(out, status='NEEDS PERSON', reason='no official outline found by the research; back to Research (layers to try are in the notes)', retry='research')
    if not pin: return dict(out, status='NEEDS PERSON', reason='no POTA pin, so the pin test cannot be done; a person compares the outline with the park')
    if ov.get('none'): return dict(out, status='NEEDS PERSON', reason=f'a person set this park to no outline earlier (overrides none: true): a person decides')
    recs, how = rd.near(row['layer_url'], pin[0], pin[1])
    if recs is None:
        return dict(out, status='NEEDS PERSON', reason=f'outline not readable: {how}; needs a hand download or a saved copy', retry='hand-download', why_not=how)
    no = {str(x).lower() for x in (ov.get('no') or [])}; blocked = {str(x) for x in ov.get('_blocked') or []}
    best = None
    for oid, rec in recs.items():
        if not rec.get('poly'): continue
        nms = rec_names(rec); fit = next((n for n in nms if name_ok(name, n)), None)
        if not fit: continue
        d = km_to(pin[0], pin[1], rec.get('r') or [])
        if d is None: continue
        c = (d, oid != str(row.get('record_id')).split()[0].split(',')[0].strip(), oid, fit, rec)
        if best is None or c < best: best = c
    if best is None:
        anyp = [r for r in recs.values() if r.get('poly')]
        on = {oid: km_to(pin[0], pin[1], rec.get('r') or []) for oid, rec in recs.items() if rec.get('poly')}
        # the sure rule + rule 8: the AGENCY's own name for the place (the file's official name) on a polygon at the pin is an alias:
        # it joins only on an owner YES to that exact name with the pin inside. Listed, never signed here.
        oname = str(row.get('official_name') or '').strip()
        if oname:
            # KISS: only the pin INSIDE, a shared core word with the park name, and not a piece/facility (no umbrella units)
            al = sorted((on[o], o, n) for o, rec in recs.items() if rec.get('poly') and on.get(o) == 0
                        for n in rec_names(rec)[:3] if name_ok(oname, n) and not kind_clash(name, n) and core(name) & core(n) and not PIECE.search(n)
                        and not (PART.findall(name.lower()) and set(PART.findall(name.lower())) - set(PART.findall(n.lower()))))
            if al:
                dk, o, n = al[0]
                if o.lower() in no or n.lower() in no: return dict(out, status='REJECTED', record_id=o, record_name=n, km=dk, reason=f'a person already said NO to {o} "{n}" (overrides no)')
                return dict(out, status='NEEDS PERSON', record_id=o, record_name=n, km=dk, read=how, alias=True, retry='person',
                            reason=f'agency alias: the record "{n}" ({o}) is not the park name "{name}"; joins only on an owner YES to that exact name with the pin inside (rule 8; pin {"inside" if dk == 0 else str(dk) + " km"})')
        # the sure rule: a layer WITHOUT names (ND state forests, PEI parks, Rio Bonito tracts) is position only. The pin inside exactly
        # one polygon there, and that polygon is the file's own record, is SURE (flagged position_only for Quality); else a person decides.
        if anyp and not any(rec_names(r) for r in anyp):
            ins = [o for o, d0 in on.items() if d0 == 0]
            fid = str(row.get('record_id') or '').split()
            if len(ins) == 1 and fid and ins[0] == fid[0].strip(' ,;'):
                o = ins[0]
                if o.lower() in no: return dict(out, status='REJECTED', record_id=o, km=0, reason=f'a person already said NO to {o} (overrides no)')
                if o in blocked: return dict(out, status='REJECTED', record_id=o, km=0, reason=f'{o} is on the bad-ID block list for this park')
                return dict(out, status='SURE', record_id=o, record_name='(layer has no names)', km=0, read=how, position_only=True,
                            reason=f'sure by position only: the layer has no names; the pin is inside record {o}, the record the research named')
            return dict(out, status='NEEDS PERSON', read=how, position_only=True, retry='person',
                        reason='the layer has no names, so only position can match, and the pin is not inside the named record: a person compares the map' + (f' (pin inside {", ".join(ins)})' if ins else ''))
        # the sure rule (6:50 PM CST): a POINT record that matches confirms the park exists: POINT-CONFIRMED (review later for a
        # boundary). It is never an outline: kept out of the keys and the 2-fers, listed separately.
        for oid, rec in recs.items():
            if rec.get('poly') or not rec.get('pt'): continue
            fit = next((n for n in rec_names(rec) if name_ok(name, n)), None)
            if not fit or kind_clash(name, fit): continue
            k = math.cos(math.radians(pin[0])); dkm = round(math.hypot((rec['pt'][0] - pin[1]) * 111.32 * k, (rec['pt'][1] - pin[0]) * 110.57), 3)
            if dkm <= SURE_KM:
                return dict(out, status='POINT-CONFIRMED', record_id=oid, record_name=fit, km=dkm, read=how, retry='boundary', pt=[round(rec['pt'][0], 7), round(rec['pt'][1], 7)],
                            reason=f'point record "{fit}" ({oid}) {dkm} km from the pin confirms the park exists; no boundary yet (review later for one; never used as an outline)')
        if recs and not anyp: return dict(out, status='REJECTED', reason=f'the layer gives points or lines here, not a boundary, and no point there has the park\'s name ({how})')
        return dict(out, status='NEEDS PERSON', reason=f'no polygon whose name fits "{name}" within {SURE_KM} km of the pin on this layer ({how}; '
                    f'{len(anyp)} other polygon(s) there: ' + '; '.join(sorted({(rec_names(r) or ["?"])[0][:40] for r in anyp}))[:160] + ')', retry='layer')
    d, _, oid, fit, rec = best
    out.update(record_id=oid, record_name=fit, km=d, read=how)
    if oid.lower() in no or fit.lower() in no: return dict(out, status='REJECTED', reason=f'a person already said NO to {oid} "{fit}" (overrides no)')
    if oid in blocked: return dict(out, status='REJECTED', reason=f'{oid} is on the bad-ID block list for this park')
    if kind_clash(name, fit): return dict(out, status='NEEDS PERSON', reason=f'same core name but a different kind of place: "{fit}" vs "{name}" (kind rule)')
    if PIECE.search(fit) and not PIECE.search(name): return dict(out, status='NEEDS PERSON', reason=f'the record "{fit}" reads like a piece or a facility of the place, not its whole land: a person decides')
    if WATER_LAYER.search(str(row.get('layer_url'))) and not re.search(r'\blake|fishing|pond|reservoir', name, re.I):
        return dict(out, status='NEEDS PERSON', reason=f'the record is a lake surface ("{fit}") and the park is not a lake: a person decides')
    ol = overlay_rec(rec) + ' ' + fit
    if OVERLAY.search(ol) and not OVERLAY.search(name): return dict(out, status='REJECTED', reason=f'overlay designation ("{OVERLAY.search(ol).group(0)}"), not the park itself')
    # hard cap, fail closed: a pin more than 0.5 km from the polygon is never SURE
    if not (isinstance(d, (int, float)) and 0 <= d <= SURE_KM):
        return dict(out, status='NEEDS PERSON', reason=f'polygon "{fit}" ({oid}) fits the name but the pin is {d} km away (over {SURE_KM} km): a person checks the pin', retry='person')
    # WDPA / Protected Planet is never an official boundary: at most a labelled approximate outline a person approves
    if WDPA.search(str(row.get('layer_url') or '') + ' ' + str(rec.get('hand') or '') + ' ' + str(how)):
        return wdpa_lead(row, pin, ov, saved, rd, out, fit, oid, rec)
    note = '' if str(row.get('record_id') or '').split()[0].strip(' ,;') == oid else f' (the file said record {row.get("record_id")}; the polygon at the pin is {oid})'
    return dict(out, status='SURE', reason=f'sure match: polygon "{fit}" record {oid}, name fits, pin {"inside" if d == 0 else str(d) + " km"}{note}')


# ---- files
WDPA = re.compile(r'wdpa|protected\s*planet|protectedplanet|unep-wcmc', re.I)


def wdpa_row(row):
    """True when a research row's lead comes from WDPA / Protected Planet (its layer, record source, name or notes say so)."""
    return bool(WDPA.search(' '.join(str(row.get(c) or '') for c in ('layer_url', 'official_name', 'owner', 'notes', 'source'))))


def read_rows(path):
    p = pathlib.Path(path)
    if p.suffix.lower() == '.json':
        j = json.load(open(p, encoding='utf-8')); rows = j.get('rows') if isinstance(j, dict) else j
    else:
        rows = list(csv.DictReader(open(p, encoding='utf-8-sig', newline='')))
    return [{c: (str(r.get(c)).strip() if r.get(c) not in (None, '') else '') for c in COLS} for r in rows if r.get('pota_ref')]


def pins_and_overrides(root, kpcdata):
    PIN = {}
    for f in glob.glob(str(pathlib.Path(kpcdata) / 'data/parkinfo/*.json')):
        try:
            for r, v in (json.load(open(f, encoding='utf-8')).get('parks') or {}).items():
                if isinstance(v, list) and len(v) > 6 and v[5] is not None and v[6] is not None and not (abs(v[5]) < .01 and abs(v[6]) < .01): PIN[r] = (v[5], v[6])
        except Exception: pass  # noqa: BLE001
    OV, SAVED = {}, {}
    for kind in ('us', 'ca', 'world'):
        try: O = json.load(open(pathlib.Path(root) / f'data/{kind}-key/overrides.json', encoding='utf-8'))
        except Exception: continue  # noqa: BLE001
        for r, v in (O.get('parks') or {}).items():
            OV[r] = dict(v)
            if v.get('join') and (kind != 'world' or v.get('ids')): SAVED[r] = ', '.join(map(str, v.get('ids') or v['join']))[:80]
        for b in O.get('blocked_ids') or []: OV.setdefault(str(b.get('ref')), {}).setdefault('_blocked', []).append(str(b.get('id')))
    return PIN, OV, SAVED


def run(files, root=ROOT, kpcdata=None, cache=None, offline=False, retry=False, ledger=None):
    root = pathlib.Path(root); inbox = root / 'data/research-inbox'
    ledger = load_ledger(root) if ledger is None else ledger   # solved parks are not checked again (answers/solved-ledger.csv)
    PIN, OV, SAVED = pins_and_overrides(root, kpcdata or os.environ.get('KPCDATA') or root / 'kpcdata')
    rd = Reader(cache or os.environ.get('RESEARCH_CACHE') or root / 'cache/research', offline=offline)
    nal_f = inbox / 'needs-another-look.json'
    try: nal = json.load(open(nal_f, encoding='utf-8'))
    except Exception: nal = {'about': 'Retry loop: parks Quality denied or held, or the research could not settle. A new layer or a hand download re-checks just these (kpc_research_inbox.py --retry).', 'parks': {}}  # noqa: BLE001
    jobs = [(pathlib.Path(f).stem, read_rows(f)) for f in files]
    if retry: jobs.append(('retry', [dict(v['row'], pota_ref=r) for r, v in list(nal['parks'].items()) + list((nal.get('point_confirmed') or {}).items()) + list((nal.get('brandon_flip') or {}).items()) if v.get('row')]))
    # Nov 11 2026 (owner): WDPA / Protected Planet stays private and off this public repo. A row whose lead comes from it is not
    # checked and nothing from it is written into results/ or needs-another-look.json (keep such files privately, off-repo).
    nw = sum(1 for _, rows in jobs for r in rows if wdpa_row(r))
    jobs = [(s, [r for r in rows if not wdpa_row(r)]) for s, rows in jobs if not (rows and all(wdpa_row(r) for r in rows))]
    if nw: print(f'research inbox: {nw} WDPA / Protected Planet row(s) skipped (never written to this public repo)')
    today = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    allres = {}
    for stem, rows in jobs:
        res = []
        rows, done = filter_unsolved(rows, ledger)   # a solved park is never handed out again: not read, not judged, off the retry list
        for row in done:
            L = ledger[row['pota_ref']]
            res.append({'pota_ref': row['pota_ref'], 'park_name': row.get('park_name') or L.get('name', ''), 'status': 'SOLVED', 'record_id': L.get('official_id', ''),
                        'reason': f"already solved in the answers ledger ({L.get('solved_basis', '')}); not checked again", 'checked': today, 'source': row.get('source')})
            nal['parks'].pop(row['pota_ref'], None)
        for row in rows:
            ref = row['pota_ref']; pin = PIN.get(ref)
            if not pin and row.get('pin_lat') and row.get('pin_lon'):
                try: pin = (float(row['pin_lat']), float(row['pin_lon']))
                except ValueError: pin = None
            r = judge(row, pin, OV.get(ref) or {}, SAVED.get(ref), rd); r['checked'] = today; r['source'] = row.get('source'); res.append(r)
            if r['status'] == 'NEEDS PERSON' and r.get('retry') != 'research': nal['parks'][ref] = {'status': 'needs another look', 'reason': r['reason'], 'since': nal['parks'].get(ref, {}).get('since', today), 'last': today, 'wait_on': r.get('retry', 'person'), 'row': row}
            elif r['status'] == 'POINT-CONFIRMED':
                nal.setdefault('point_confirmed', {})[ref] = {'status': 'POINT-CONFIRMED', 'reason': r['reason'], 'since': nal.get('point_confirmed', {}).get(ref, {}).get('since', today), 'last': today, 'row': row}
                nal['parks'].pop(ref, None)
            elif r['status'] == SFN:   # the short flip list
                nal.setdefault('brandon_flip', {})[ref] = {'status': r['status'], 'reason': r['reason'], 'earlier_no': r.get('earlier_no'), 'record_id': r.get('record_id'),
                                                          'record_name': r.get('record_name'), 'layer_url': r.get('layer_url'), 'last': today, 'row': row}
                nal['parks'].pop(ref, None)
            elif r['status'] in ('SURE', 'REJECTED') and ref in nal['parks'] and stem == 'retry': nal['parks'].pop(ref)
        allres[stem] = res
        if stem != 'retry' or res:
            outd = inbox / 'results'; outd.mkdir(parents=True, exist_ok=True)
            res = scrub_obj(res); allres[stem] = res   # (a run can never write a WDPA id or address back)
            n = {}; [n.__setitem__(x['status'], n.get(x['status'], 0) + 1) for x in res]
            json.dump({'counts': n, 'rows': res}, open(outd / f'{stem}.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
            L = [f'# Research inbox: {stem}', '', 'Recommendations only. SURE rows go to Quality, then are signed under the sure rule. Pins are never moved.', '',
                 ', '.join(f'**{v}** {k}' for k, v in sorted(n.items())), '', '| Park | Name | Status | Record | Why |', '|---|---|---|---|---|']
            L += [f"| {x['pota_ref']} | {x['park_name']} | {x['status']} | {x.get('record_id', '')} | {x['reason']} |".replace('\n', ' ') for x in res]
            open(outd / f'{stem}.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
            print(f'research inbox {stem}: {len(res)} rows; ' + ', '.join(f'{k} {v}' for k, v in sorted(n.items())))
    rd.save()
    # the sure rule (KISS): ONE short plain list for the owner: solutions over an earlier NO, and agency-alias names (rule 8)
    BL = ['# Owner short list', '', 'Each line: the park, what was found, and what you said before. Say YES to flip, or NO.', '']
    for r, v in sorted((nal.get('brandon_flip') or {}).items()):
        if is_skipped(r, ledger): continue   # solved parks are not put on the owner short list again (a pending owner decision stays on it)
        e = v.get('earlier_no') or {}
        BL.append(f"- **{r}** {(v.get('row') or {}).get('park_name', '')}: found record {v.get('record_id')} \"{v.get('record_name')}\". You said before ({e.get('date') or 'no date'}): {e.get('decision')}.")
    seen = set()
    for rf in sorted((inbox / 'results').glob('*.json')):
        try: res = json.load(open(rf, encoding='utf-8')).get('rows') or []
        except Exception: continue  # noqa: BLE001
        for x in res:
            if x.get('alias') and x['status'] == 'NEEDS PERSON' and x['pota_ref'] not in seen and x['pota_ref'] not in SAVED and not is_skipped(x['pota_ref'], ledger):
                seen.add(x['pota_ref'])
                BL.append(f"- **{x['pota_ref']}** {x['park_name']}: the agency calls it \"{x.get('record_name')}\" (record {x.get('record_id')}). Same park?")
    open(inbox / 'brandon-list.md', 'w', encoding='utf-8').write(scrub_wdpa('\n'.join(BL)) + '\n')
    for k in ('parks', 'point_confirmed', 'brandon_flip'):   # Nov 11: no WDPA lead is kept in the public retry list
        if isinstance(nal.get(k), dict): nal[k] = {r: v for r, v in nal[k].items() if not wdpa_row(v.get('row') or v)}
    nal = scrub_obj(nal)
    json.dump(nal, open(nal_f, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, sort_keys=True)
    # the sure rule: the 100 ft circle around the OFFICIAL point of each POINT-CONFIRMED park (the 2-fer 'point-circle' tier reads it);
    # a park that turns SURE (a real boundary) loses its circle here, and the 2-fer bot never uses a circle for a park with an outline.
    pc_f = root / 'data/point-circles.json'
    try: pc = json.load(open(pc_f, encoding='utf-8'))
    except Exception: pc = {'about': 'Nov 9 2026: POINT-CONFIRMED parks: an official POINT record with the park\'s name within 0.5 km of the POTA pin. kind point-circle-100ft = a 30.48 m circle around the OFFICIAL point (the POTA pin is never moved), a stand-in used ONLY by the 2-fer bot as the labelled point-circle tier; never an official boundary, never a key outline. Replaced automatically when a real boundary is found.', 'parks': {}}  # noqa: BLE001
    for res in allres.values():
        for r in res:
            if r['status'] == 'POINT-CONFIRMED' and r.get('pt'):
                pc['parks'][r['pota_ref']] = {'kind': 'point-circle-100ft', 'radius_m': 30.48, 'pt': r['pt'], 'layer_url': r.get('layer_url'), 'record_id': r.get('record_id'),
                                              'record_name': r.get('record_name'), 'pin_km': r.get('km'), 'read': r.get('read'), 'confirmed': r.get('checked'), 'decided_by': 'point-circle rule (Nov 9 2026)'}
            elif r['status'] == 'SURE': pc['parks'].pop(r['pota_ref'], None)
    json.dump(pc, open(pc_f, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, sort_keys=True)
    print(f'live reads {rd.live}; needs another look: {len(nal["parks"])}')
    return allres


def selftest():
    bad = 0
    for a, b, want in [('New Echota State Historic Site', 'New Echtoa Historic Site', True), ('PA 046 State Game Land', '46 - Middle Creek Wildlife Management Area', True),
                       ('Dodge County State Fishing Lake', 'DODGE COUNTY PFA', True), ('Kern National Wild and Scenic River', 'Kern, California National Wild and Scenic River', True),
                       ('Lone Rock BLM Recreation Management Area', 'Black Rock SRMA', False), ('Cooper Lake State Park', 'Cooper - South Sulphur', False),
                       ('Narcisse Provincial Park', 'Narcisse Wildlife Management Area', True)]:
        ok = name_ok(a, b) == want; bad += not ok; print(('ok  ' if ok else 'FAIL') + f' name_ok({a!r}, {b!r}) = {not want if not ok else want}')
    ok = kind_clash('Narcisse Provincial Park', 'Narcisse Wildlife Management Area'); bad += not ok; print(('ok  ' if ok else 'FAIL') + ' kind clash park vs WMA')
    sq = [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]]
    ok = km_to(0, 0, sq) == 0.0 and 100 < km_to(0, 3, sq) < 250; bad += not ok; print(('ok  ' if ok else 'FAIL') + ' pin inside / outside')
    return bad


if __name__ == '__main__':
    if '--selftest' in sys.argv: sys.exit(1 if selftest() else 0)
    a = sys.argv[1:]
    only = a[a.index('--only') + 1] if '--only' in a else None
    fs = [only] if only else inbox_files(ROOT)
    try: run(fs, offline='--offline' in a, retry='--retry' in a)
    except Exception as e:  # noqa: BLE001
        print(f'::warning title=Research inbox::stopped ({type(e).__name__}: {str(e)[:160]}); no key is affected')
    sys.exit(0)
