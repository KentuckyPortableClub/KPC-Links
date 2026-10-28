"""US PARKING / ENTRANCES / ACCESS POINTS for POTA parks outside Kentucky (Brandon Oct 25 2026: 'parking / entrance layer is
weak… start with US Wildlife Management Areas… then state parks'). Kentucky has had this since Oct 18 (kpc-ky-data.json 'ap').

Reads the official agency point layers in data/access-layers.json (the outside research bot's round 3), keeps only the points
an activator can drive to or launch from - parking, entrances, gates, kiosks / information boards, boat ramps and launches,
trailheads, check stations - and ties each one to a POTA park:
  1. by NAME: the layer says which area the point belongs to (Area_Name, PropName, WMA, sgl number…) and that name is the
     park's name (the same name rules as the answer key, kpc_us_key.py); or
  2. by PLACE: the point sits on the park's official land, or within ~300 m of it (the outlines the answer key joined,
     from the saved copies in the boundary-cache release, cache/us/US-XX.json.gz).
A statewide layer (every boat ramp in the state) only ever counts by PLACE. Nothing is matched by a pin alone.
Writes data/access/US-XX.json {updated, st, parks:{ref:[[lat, lon, label]]}} (Kentucky's 'ap' shape) + data/access/index.json.
STATES='MO PA' picks states (default: every state in the layer list). Never fails.
Oct 28 (HQ tune + speed-up): polite (1 request / 2 s per host); a state whose layers' lastEditDate, park list, answer key and
saved outlines are all unchanged since its last build is skipped (FULL=1 rebuilds all); a layer that could not be read keeps
last run's points from that agency; joined land whose box is nowhere near the park's pin is not used (a wrong key join tied
points 270-380 km away); points at 0,0 or outside the state are dropped; a state that lost 40%+ of its points with no reason
keeps its saved copy (GATE FAIL). The gate result goes to /tmp/kpc-gate.txt for the workflow's grade-me line."""
import gzip, hashlib, json, math, os, pathlib, re, sys, time, types, urllib.parse, urllib.request
from kpc_save import save_json, read_dates  # Oct 25 storage plan: write only when the content changed

UA = {'User-Agent': 'KPC access points (kentuckyportableclub.github.io)'}
OUT = pathlib.Path('data/access'); OUT.mkdir(parents=True, exist_ok=True)
CACHE = pathlib.Path(os.environ.get('GEO_CACHE') or 'cache/us')
T0, LIMIT = time.time(), float(os.environ.get('MINUTES') or 150) * 60
FAR_NAME_KM = 100
LINEPARK = re.compile(r'trail|river|parkway|byway|scenic|greenway|canal|route|corridor', re.I)
NEAR_M = 300          # a point this close to the park's land counts as the park's
NAME_KM = 40          # a name match must also be this close to the park's pin (same-named areas elsewhere)
CAP = 40              # points kept per park
VERSION = 'v2-oct28'  # bump when the tying rules change: every state is rebuilt once


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', ' ')[:900]), flush=True)


GAP = float(os.environ.get('POLITE') or 2.0)   # seconds between two requests to the same host
_LAST = {}


def _polite(u):
    h = urllib.parse.urlsplit(u).netloc
    w = _LAST.get(h, 0) + GAP - time.time()
    if w > 0: time.sleep(w)
    _LAST[h] = time.time()


def get(url, params=None, tries=3, timeout=120):
    u = url + ('?' + urllib.parse.urlencode(params) if params else '')
    last = None
    for i in range(tries):
        _polite(u)
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:160])
            return j
        except Exception as e:  # noqa: BLE001
            last = e; time.sleep(4 + 5 * i)
    raise last


# the answer key's name rules (norm / same_name / kinds), loaded without running the key itself
def _key():
    src = pathlib.Path(__file__).resolve().parent.joinpath('kpc_us_key.py').read_text(encoding='utf-8').split('\nidx = {}\n')[0]
    m = types.ModuleType('kpc_us_key'); m.__file__ = str(pathlib.Path(__file__).resolve().parent / 'kpc_us_key.py')
    exec(compile(src, 'kpc_us_key.py', 'exec'), m.__dict__)
    return m
K = _key()

# ---------------------------------------------------------------- what kind of point it is
KIND = [('Parking', r'park(ing)?\b(?! *(name|code))|\blot\b|pull.?off|pullout|lot type|vehpark|rigpark'),
        ('Entrance', r'entrance|entry|access point|designated access|navigation point|directions point|contact station'),
        ('Gate', r'\bgate'),
        ('Kiosk / information', r'kiosk|information|info (station|source|sign)|reader ?board|sign ?in|entrance sign'),
        ('Check station', r'check(ing)? ?(station|in)'),
        ('Boat ramp / launch', r'ramp|launch|carry.?(in|down)|cartop|slide down|boat(ing)? access|water access|canoe|kayak|paddl'),
        ('Trailhead', r'trail ?head')]
NOT = r'blind|restroom|comfort|latrine|toilet|tower|bridge|trash|picnic|playground|pump ?out|fish clean|pool|water control|culvert|building|corral|road closed|proposed|private|pay to launch|permanently closed|no boats|dock\b|pier'


def kind_of(text):
    t = str(text or '').lower()
    if re.search(NOT, t) and not re.search(r'parking|ramp|launch', t): return None
    for k, rx in KIND:
        if re.search(rx, t): return k
    return None


# ---------------------------------------------------------------- park outlines (the answer key's joins + saved copies)
def outlines_ca(prov):
    """Oct 25 (Canada): rings for the parks the Canada key joined, from the saved provincial outline files
    (data/canada-bounds) and the saved copy of every Canadian area (cache/ca/CA-ALL.json.gz). An id is only trusted with
    its NAME (ids repeat from layer to layer: the Québec lesson of Oct 25)."""
    try: key = json.load(open(f'data/ca-key/CA-{prov}.json'))['parks']
    except Exception: return {}  # noqa: BLE001
    by = {}
    f = pathlib.Path(os.environ.get('GEO_CACHE_CA') or 'cache/ca') / 'CA-ALL.json.gz'
    if f.exists():
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fh:
                for r in json.load(fh).get('recs') or []: by.setdefault(str(r.get('oid')), []).append(r)
        except Exception: by = {}  # noqa: BLE001
    low = lambda x: ' '.join(str(x or '').lower().split())
    out = {}
    for ref, p in key.items():
        rs = []
        bf = pathlib.Path(f'data/canada-bounds/{ref}.json')
        if bf.exists():
            try:
                g = json.load(open(bf)).get('geometry') or {}
                c = g.get('coordinates') or []
                rs = [poly for poly in c if poly] if g.get('type') == 'MultiPolygon' else ([c] if c else [])   # one group per polygon
            except Exception: rs = []  # noqa: BLE001
        if not rs:
            for x in p.get('m') or []:
                r = next((q for q in by.get(str(x[0]), []) if low(x[1]) in (low(q.get('n')), low(q.get('nf')))), None)
                if r and r.get('_r'): rs.append(r['_r'])   # one group per record (Oct 26)
        if rs: out[ref] = rs
    return out


def outlines(st):
    """{ref: [rings]} for parks the key joined, from the saved copy of the state's official land."""
    if st.startswith('CA-'): return outlines_ca(st[3:])
    try: key = json.load(open(f'data/us-key/US-{st}.json'))['parks']
    except Exception: return {}  # noqa: BLE001
    f = CACHE / f'US-{st}.json.gz'
    if not f.exists(): return {}
    try:
        with gzip.open(f, 'rt', encoding='utf-8') as fh: recs = json.load(fh).get('recs') or []
    except Exception: return {}  # noqa: BLE001
    by = {str(r.get('OBJECTID')): r.get('_r') or [] for r in recs}
    out = {}
    for ref, p in key.items():
        # Oct 26: one group of rings per joined record (two records of the same land would cancel each other's inside test)
        rs = [by[str(x[0])] for x in p.get('m') or [] if by.get(str(x[0]))]
        if rs: out[ref] = rs
    return out


def in_ring(x, y, r):
    ins, j = False, len(r) - 1
    for i in range(len(r)):
        xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi: ins = not ins
        j = i
    return ins


def m_to_ring(la, lo, r):
    # rough metres from a point to a ring's edge (flat earth: fine at a few hundred metres)
    kx, ky = 111320 * math.cos(math.radians(la)), 110540
    best = 1e12
    for i in range(len(r) - 1):
        ax, ay, bx, by = (r[i][0] - lo) * kx, (r[i][1] - la) * ky, (r[i + 1][0] - lo) * kx, (r[i + 1][1] - la) * ky
        dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, -(ax * dx + ay * dy) / L))
        best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def on_land(la, lo, rings):
    if rings and rings[0] and rings[0][0] and isinstance(rings[0][0][0], list):   # groups: inside ANY record's land
        return any(on_land(la, lo, g) for g in rings)
    if sum(1 for r in rings if in_ring(lo, la, r)) % 2 == 1: return True
    return any(m_to_ring(la, lo, r) <= NEAR_M for r in rings if len(r) > 2)


def km(a, b, c, d):
    r = math.radians; return 6371 * 2 * math.asin(math.sqrt(math.sin(r(c - a) / 2) ** 2 + math.cos(r(a)) * math.cos(r(c)) * math.sin(r(d - b) / 2) ** 2))


# ---------------------------------------------------------------- read one layer
def fields_in(text, have):
    """The field names the worklist mentions that the layer really has ('Area_Name', 'PropName, MA_NUM' …)."""
    toks = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', str(text or ''))
    low = {h.lower(): h for h in have}
    return [low[t.lower()] for t in toks if t.lower() in low]


def read_layer(L, box, info=None):
    info = info or get(L['url'], {'f': 'json'})
    have = [f['name'] for f in info.get('fields') or []]
    geo = str(info.get('geometryType', ''))
    if 'Polyline' in geo: return [], 'lines, not points'
    area = [] if re.search(r'location only|^\s*\(?none', L['area'], re.I) else fields_in(L['area'], have)
    typf = fields_in(L['typef'], have)
    namef = [f for f in have if re.search(r'^(name|.*_name|.*name)(_e)?$', f, re.I) and f not in area][:2]
    # Oct 26 (Parks Canada components): a type field holding CODES is read through the layer's own code list
    dom = {f['name']: {str(c.get('code')): str(c.get('name')) for c in ((f.get('domain') or {}).get('codedValues') or [])}
           for f in info.get('fields') or []}
    out, off, mx = [], 0, int(info.get('maxRecordCount') or 1000)
    while True:
        q = {'where': '1=1', 'outFields': ','.join(dict.fromkeys(area + typf + namef)) or '*', 'returnGeometry': 'true', 'outSR': 4326, 'f': 'json',
             'resultOffset': off, 'resultRecordCount': min(mx, 1000)}
        if box: q.update({'geometry': ','.join(map(str, box)), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects'})
        try: j = get(L['url'] + '/query', q)
        except Exception:  # noqa: BLE001
            if off or not box: raise
            box = None; continue          # some services refuse a box: read them whole
        fs = j.get('features') or []
        for f in fs:
            g = f.get('geometry') or {}; a = f.get('attributes') or {}
            if 'x' in g: lo, la = g['x'], g['y']
            elif g.get('rings'):
                pts = [p for r in g['rings'] for p in r]; lo, la = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
            elif g.get('points'): lo, la = g['points'][0][0], g['points'][0][1]
            else: continue
            text = ' '.join(dom.get(x, {}).get(str(a.get(x)), str(a.get(x) or '')) for x in typf).strip()
            if text and re.fullmatch(r'[\d .]+', text):   # codes with no code list: the point's own name says what it is
                text = ' '.join(str(a.get(x) or '') for x in namef).strip()
            out.append({'la': la, 'lo': lo, 'k': kind_of(text) if text else None, 'txt': text, 'area': ' '.join(str(a.get(x) or '') for x in area).strip(), 'nm': ' '.join(str(a.get(x) or '') for x in namef).strip()})
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < min(mx, 1000)): break
        off += len(fs)
    # a layer whose 'type' field never says what a point is (Public/Private, Open/Closed…) is a one-type layer: its own
    # description says what it holds ('points: boat launches'); points whose text is a thing we do not want stay out
    if not any(p['k'] for p in out):
        lk = kind_of(L['what'])
        for p in out:
            if not re.search(NOT, p['txt'].lower()): p['k'] = lk
    out = [p for p in out if p['k']]
    return out, f"{len(out)} kept · area field {','.join(area) or 'none (by place only)'} · type field {','.join(typf) or 'none (one type)'}"


STB = None
def st_box(st):
    global STB
    if st.startswith('CA-'):   # a province: the box around its POTA parks' pins
        try: P = json.load(open('data/parkinfo/CA.json'))['parks']
        except Exception: return None  # noqa: BLE001
        pts = [(v[5], v[6]) for v in P.values() if len(v) > 10 and v[10] == st[3:] and v[5] is not None and v[6] is not None]
        if not pts: return None
        return [min(q[1] for q in pts) - .3, min(q[0] for q in pts) - .3, max(q[1] for q in pts) + .3, max(q[0] for q in pts) + .3]
    if STB is None:
        try: STB = json.load(open('kpc-us-states.json'))
        except Exception: STB = []  # noqa: BLE001
    x = next((b for b in STB if b.get('a') == st), None)
    if not x: return None
    xs = [q[0] for pl in x['p'] for q in pl[0]]; ys = [q[1] for pl in x['p'] for q in pl[0]]
    return [min(xs) - .05, min(ys) - .05, max(xs) + .05, max(ys) + .05]


WILD = re.compile(r'wildlife|game (land|area|management)|conservation area|hunting|habitat|waterfowl|fishing (lake|area)|refuge', re.I)


def agency_short(L):
    a = re.sub(r'\s*\(.*$', '', L['agency']).split(',')[0].strip()
    return a[:60] or L['st'] + ' state agency'


def _md5(fn):
    try: return hashlib.md5(pathlib.Path(fn).read_bytes()).hexdigest()[:12]
    except Exception: return '-'  # noqa: BLE001


GATE = {'pass': [], 'fail': []}
SKIPPED = []


def run(st, layers, old=None):
    ca = st.startswith('CA-')
    try: P = json.load(open('data/parkinfo/CA.json' if ca else f'data/parkinfo/US-{st}.json'))['parks']
    except Exception: notice(f'Access {st}', 'no park file'); return None  # noqa: BLE001
    if ca: P = {r: v for r, v in P.items() if len(v) > 10 and v[10] == st[3:]}
    fn = OUT / (f'{st}.json' if ca else f'US-{st}.json')
    # Oct 28: REUSE. The layers' own lastEditDate + this state's parks, key and saved outlines make the state's signature;
    # all unchanged since the last build = nothing to redo (a layer with no lastEditDate always counts as changed)
    infos, eds = {}, []
    for L in layers:
        try:
            infos[L['url']] = get(L['url'], {'f': 'json'}, tries=2, timeout=60)
            eds.append(str((infos[L['url']].get('editingInfo') or {}).get('lastEditDate') or ''))
        except Exception: eds.append('')  # noqa: BLE001
    pk = json.dumps({r: P[r][:7] for r in sorted(P)}, sort_keys=True)
    keyf = f'data/ca-key/CA-{st[3:]}.json' if ca else f'data/us-key/US-{st}.json'
    cache = (pathlib.Path(os.environ.get('GEO_CACHE_CA') or 'cache/ca') / 'CA-ALL.json.gz') if ca else CACHE / f'US-{st}.json.gz'
    sig = hashlib.md5('|'.join([VERSION, ','.join(sorted(L['url'] for L in layers)), ','.join(eds), hashlib.md5(pk.encode()).hexdigest(), _md5(keyf), _md5(cache)]).encode()).hexdigest()[:16]
    if (old or {}).get('sig') == sig and all(eds) and fn.exists() and os.environ.get('FULL') != '1':
        SKIPPED.append(st); c = dict(old); return c
    parks = {}
    for ref, v in P.items():
        typ = v[2] or ''
        if (not ca and 'National' in typ) or v[5] is None: continue   # Canada: Parks Canada sites count too
        parks[ref] = (v[0], typ, v[5], v[6])          # every state / local park: a ramp on a state park's own land is that park's too
    OL = outlines(st)
    # Oct 28: a joined record whose land is nowhere near the park's pin is a wrong join (Beaver Creek WMA MN got points 270 km
    # away): only groups whose box (padded ~30 km) holds the pin are used
    dropped = 0
    for ref in list(OL):
        v = P.get(ref)
        if not v or v[5] is None: continue
        keep = []
        for g in OL[ref]:
            xs = [q[0] for r in g for q in r]; ys = [q[1] for r in g for q in r]
            if xs and min(xs) - .3 <= v[6] <= max(xs) + .3 and min(ys) - .3 <= v[5] <= max(ys) + .3: keep.append(g)
            else: dropped += 1
        if keep: OL[ref] = keep
        else: del OL[ref]
    # Oct 26: the box around each park's own land (a big national park reaches far past 60 km from its pin: Nahanni, Banff)
    OLB = {}
    for ref, rings in OL.items():
        xs = [q[0] for g in rings for r in g for q in r]; ys = [q[1] for g in rings for r in g for q in r]
        if xs: OLB[ref] = (min(xs) - .01, min(ys) - .01, max(xs) + .01, max(ys) + .01)
    box = st_box(st)
    got, log, failed = {}, [], set()
    stopped = False
    for L in layers:
        if time.time() - T0 > LIMIT: log.append('stopped for time'); stopped = True; failed.add(agency_short(L)); continue
        try: pts, how = read_layer(L, box, infos.get(L['url']))
        except Exception as e:  # noqa: BLE001
            failed.add(agency_short(L))
            log.append(f"{L['url'].split('/services/')[-1][:50]}: not read ({str(e)[:80]})"); continue
        if not pts: log.append(f"{L['url'].split('/services/')[-1][:50]}: 0 ROWS ({how})"); continue
        bad = 0
        n = 0
        src = agency_short(L)
        for p in pts:
            if not (-180 <= p['lo'] <= 180 and -90 <= p['la'] <= 90) or (abs(p['la']) < 1 and abs(p['lo']) < 1) or \
               (box and not ca and not (box[0] - .3 <= p['lo'] <= box[2] + .3 and box[1] - .3 <= p['la'] <= box[3] + .3)):
                bad += 1; continue    # Oct 28: a point at 0,0 or outside the state is a broken row
            hit = set()
            if p['area']:
                for ref, (name, typ, la, lo) in parks.items():
                    if km(la, lo, p['la'], p['lo']) > NAME_KM: continue
                    if K.name_ok(name, p['area'], K.kinds(name) | K.kinds(typ), K.kinds(p['area'])): hit.add(ref)
            byname = set(hit)
            for ref, rings in OL.items():
                if ref in parks and ref not in hit:
                    name, typ, la, lo = parks[ref]
                    b = OLB.get(ref)
                    if b and b[0] <= p['lo'] <= b[2] and b[1] <= p['la'] <= b[3] and on_land(p['la'], p['lo'], rings): hit.add(ref)
            for ref in hit:
                # Oct 27 (research-bots review #9): how the point was tied: 'name' (the layer names the park) or 'place' (it sits
                # on the park's official land); tools word a place-only point as 'nearby public access, not the park's own'
                got.setdefault(ref, []).append([round(p['la'], 6), round(p['lo'], 6), f"{p['k']}{(': ' + p['nm'])[:60] if p['nm'] and p['nm'] != p['area'] else ''} ({src})", 'name' if ref in byname else 'place'])
                n += 1
        log.append(f"{L['url'].split('/services/')[-1][:50]}: {how}; {n} tied to parks" + (f'; {bad} bad rows dropped' if bad else ''))
    try: was = json.load(open(fn))
    except Exception: was = {}  # noqa: BLE001
    # Oct 28: a layer that could not be read this time keeps last run's points from that agency (a timeout must not wipe them)
    if failed:
        for ref, pts in (was.get('parks') or {}).items():
            if ref not in parks: continue    # a retired park stays out
            for q in pts:
                if any(q[2].endswith(f'({s})') for s in failed): got.setdefault(ref, []).append(q)
    # tidy: one point per ~60 m, parking first, at most CAP per park
    order = {k: i for i, (k, _) in enumerate(KIND)}
    out = {}
    far_dropped = 0
    for ref, pts in got.items():
        pts.sort(key=lambda q: order.get(q[2].split(':')[0].split(' (')[0], 9))
        keep = []
        name, typ, pla, plo = parks.get(ref, ('', '', None, None))
        line = bool(LINEPARK.search(f'{name} {typ}'))
        for q in pts:
            # Oct 28 (chat 11's check): a point tied by NAME more than 100 km from its park's pin is a name mix-up (two Robert Moses parks,
            # Copan WMA, Beaver Creek WMA): dropped. Points sitting on the park's own land ('place') and line parks (trails, rivers) stay.
            if pla is not None and not line and (len(q) < 4 or q[3] != 'place') and km(pla, plo, q[0], q[1]) > FAR_NAME_KM:
                far_dropped += 1; continue
            if any(km(q[0], q[1], k[0], k[1]) < .06 for k in keep): continue
            keep.append(q)
            if len(keep) >= CAP: break
        out[ref] = keep
    n_old = sum(len(v) for v in (was.get('parks') or {}).values()); n_new = sum(len(v) for v in out.values())
    if n_old >= 20 and n_new < .6 * n_old:   # Oct 28 self-gate: a big drop with no reason = keep the saved copy
        GATE['fail'].append(f'{st} {n_old}->{n_new} points (kept the saved copy)')
        notice(f'Access {st}', f'GATE FAIL: {n_old} -> {n_new} points; the saved copy is kept | ' + ' | '.join(log)[:600])
        c = dict(old or {}); c.pop('sig', None); return c or None
    GATE['pass'].append(st)
    rd = read_dates(was.get('parks'), out, was.get('read'))   # research-bots review #2: the day each park's points were read
    save_json(fn, {'st': st, 'read': rd, 'src': 'the state agencies\' own point layers (data/access-layers.json)', 'note': 'Official parking / entrance / gate / kiosk / boat ramp / trailhead points from the state agencies (data/access-layers.json), tied to POTA parks by the layer\'s area name or by sitting on the park\'s official land. Built by .github/scripts/kpc_us_access.py.',
                                                   'parks': out})
    c = {'parks_with_points': len(out), 'points': sum(len(v) for v in out.values()), 'wildlife_parks': sum(1 for r, x in parks.items() if WILD.search(x[1])), 'outlines': len(OL)}
    if not failed and not stopped: c['sig'] = sig     # only a complete build may be reused next time
    notice(f'Access {st}', f"{c['parks_with_points']} parks got {c['points']} points" + (f'; {dropped} far-off joined records not used' if dropped else '') + (f'; {far_dropped} name-tied points over {FAR_NAME_KM} km from their park dropped' if far_dropped else '') + '; ' + ' | '.join(log)[:700])
    return c


def main():
    cfg = json.load(open('data/access-layers.json'))['layers']
    want = (os.environ.get('STATES') or '').upper().replace(',', ' ').split() or sorted({L['st'] for L in cfg if re.fullmatch(r'(CA-)?[A-Z]{2}', L['st'])})
    try: idx = json.load(open(OUT / 'index.json')).get('states', {})
    except Exception: idx = {}  # noqa: BLE001
    for st in want:
        if time.time() - T0 > LIMIT: notice('Access', f'stopped for time before {st}'); break
        lay = [L for L in cfg if L['st'] == st]
        if not lay: continue
        try: c = run(st, lay, idx.get(st))
        except Exception as e: notice(f'Access {st}', f'stopped: {type(e).__name__}: {str(e)[:200]}'); continue  # noqa: BLE001
        if c: idx[st] = c
        save_json(OUT / 'index.json', {'states': idx})
    notice('Access points', f"{sum(v['parks_with_points'] for v in idx.values())} parks in {len(idx)} states have official parking / access points"
           + (f"; {len(SKIPPED)} states unchanged, reused: {' '.join(SKIPPED)}" if SKIPPED else ''))
    gate(want)


def gate(want):
    """Oct 28 self-grade: Kentucky's hand-checked pins (kpc-ky-data.json 'ap') must still be there and near their parks, and
    no state may have silently lost its points. Writes /tmp/kpc-gate.txt: PASS|FAIL <tab> areas <tab> note."""
    why = list(GATE['fail'])
    try:
        ky = [p for p in json.load(open('kpc-ky-data.json'))['parks'] if p.get('ap')]
        n = sum(len(p['ap']) for p in ky)
        far = sum(1 for p in ky for q in p['ap'] if p.get('la') is not None and km(p['la'], p['lo'], q[0], q[1]) > 150)   # Daniel Boone NF reaches ~120 km
        if len(ky) < 170 or n < 1200: why.append(f'Kentucky pins thin: {len(ky)} parks / {n} pins (expected 190 / 1360)')
        if far: why.append(f'{far} Kentucky pins over 150 km from their park')
        ky_note = f'KY {len(ky)} parks / {n} pins'
    except Exception as e: why.append(f'Kentucky pins not readable: {e}'); ky_note = 'KY ?'  # noqa: BLE001
    res = 'FAIL' if why else 'PASS'
    msg = f"{ky_note}; {len(GATE['pass'])} states built, {len(SKIPPED)} reused" + ('; ' + '; '.join(why) if why else '')
    notice('Access gate', f'GATE {res} {msg}')
    try: open('/tmp/kpc-gate.txt', 'w').write(f"{res}\t{' '.join(want)[:200]}\t{msg[:400]}\n")
    except Exception: pass  # noqa: BLE001


if __name__ == '__main__':
    try: main()
    except Exception as e: notice('Access points', f'stopped early: {type(e).__name__}: {str(e)[:300]}')  # noqa: BLE001
    sys.exit(0)
