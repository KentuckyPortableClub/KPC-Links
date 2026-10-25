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
STATES='MO PA' picks states (default: every state in the layer list). Never fails."""
import gzip, json, math, os, pathlib, re, sys, time, types, urllib.parse, urllib.request

UA = {'User-Agent': 'KPC access points (kentuckyportableclub.github.io)'}
OUT = pathlib.Path('data/access'); OUT.mkdir(parents=True, exist_ok=True)
CACHE = pathlib.Path(os.environ.get('GEO_CACHE') or 'cache/us')
T0, LIMIT = time.time(), float(os.environ.get('MINUTES') or 150) * 60
NEAR_M = 300          # a point this close to the park's land counts as the park's
NAME_KM = 40          # a name match must also be this close to the park's pin (same-named areas elsewhere)
CAP = 40              # points kept per park


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', ' ')[:900]), flush=True)


def get(url, params=None, tries=3, timeout=120):
    u = url + ('?' + urllib.parse.urlencode(params) if params else '')
    last = None
    for i in range(tries):
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
        ('Entrance', r'entrance|entry|access point|designated access'),
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
def outlines(st):
    """{ref: [rings]} for parks the key joined, from the saved copy of the state's official land."""
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
        rs = [ring for x in p.get('m') or [] for ring in by.get(str(x[0]), [])]
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


def read_layer(L, box):
    info = get(L['url'], {'f': 'json'})
    have = [f['name'] for f in info.get('fields') or []]
    geo = str(info.get('geometryType', ''))
    if 'Polyline' in geo: return [], 'lines, not points'
    area = [] if re.search(r'location only|^\s*\(?none', L['area'], re.I) else fields_in(L['area'], have)
    typf = fields_in(L['typef'], have)
    namef = [f for f in have if re.search(r'^(name|.*_name|.*name)$', f, re.I) and f not in area][:2]
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
            text = ' '.join(str(a.get(x) or '') for x in typf).strip()
            out.append({'la': la, 'lo': lo, 'k': kind_of(text) if text else None, 'txt': text, 'area': ' '.join(str(a.get(x) or '') for x in area).strip(), 'nm': ' '.join(str(a.get(x) or '') for x in namef).strip()})
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < min(mx, 1000)): break
        off += len(fs); time.sleep(.4)
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


def run(st, layers):
    try: P = json.load(open(f'data/parkinfo/US-{st}.json'))['parks']
    except Exception: notice(f'Access {st}', 'no park file'); return None  # noqa: BLE001
    parks = {}
    for ref, v in P.items():
        typ = v[2] or ''
        if 'National' in typ or v[5] is None: continue
        parks[ref] = (v[0], typ, v[5], v[6])          # every state / local park: a ramp on a state park's own land is that park's too
    OL = outlines(st)
    box = st_box(st)
    got, log = {}, []
    for L in layers:
        if time.time() - T0 > LIMIT: log.append('stopped for time'); break
        try: pts, how = read_layer(L, box)
        except Exception as e:  # noqa: BLE001
            log.append(f"{L['url'].split('/services/')[-1][:50]}: not read ({str(e)[:80]})"); continue
        n = 0
        src = agency_short(L)
        for p in pts:
            hit = set()
            if p['area']:
                for ref, (name, typ, la, lo) in parks.items():
                    if km(la, lo, p['la'], p['lo']) > NAME_KM: continue
                    if K.name_ok(name, p['area'], K.kinds(name) | K.kinds(typ), K.kinds(p['area'])): hit.add(ref)
            for ref, rings in OL.items():
                if ref in parks and ref not in hit:
                    name, typ, la, lo = parks[ref]
                    if km(la, lo, p['la'], p['lo']) <= 60 and on_land(p['la'], p['lo'], rings): hit.add(ref)
            for ref in hit:
                got.setdefault(ref, []).append([round(p['la'], 6), round(p['lo'], 6), f"{p['k']}{(': ' + p['nm'])[:60] if p['nm'] and p['nm'] != p['area'] else ''} ({src})"])
                n += 1
        log.append(f"{L['url'].split('/services/')[-1][:50]}: {how}; {n} tied to parks")
    # tidy: one point per ~60 m, parking first, at most CAP per park
    order = {k: i for i, (k, _) in enumerate(KIND)}
    out = {}
    for ref, pts in got.items():
        pts.sort(key=lambda q: order.get(q[2].split(':')[0].split(' (')[0], 9))
        keep = []
        for q in pts:
            if any(km(q[0], q[1], k[0], k[1]) < .06 for k in keep): continue
            keep.append(q)
            if len(keep) >= CAP: break
        out[ref] = keep
    (OUT / f'US-{st}.json').write_text(json.dumps({'updated': time.strftime('%Y-%m-%d'), 'st': st, 'note': 'Official parking / entrance / gate / kiosk / boat ramp / trailhead points from the state agencies (data/access-layers.json), tied to POTA parks by the layer\'s area name or by sitting on the park\'s official land. Built by .github/scripts/kpc_us_access.py.',
                                                   'parks': out}, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
    c = {'parks_with_points': len(out), 'points': sum(len(v) for v in out.values()), 'wildlife_parks': sum(1 for r, x in parks.items() if WILD.search(x[1])), 'outlines': len(OL)}
    notice(f'Access {st}', f"{c['parks_with_points']} parks got {c['points']} points; " + ' | '.join(log)[:700])
    return c


def main():
    cfg = json.load(open('data/access-layers.json'))['layers']
    want = (os.environ.get('STATES') or '').upper().replace(',', ' ').split() or sorted({L['st'] for L in cfg if re.fullmatch(r'[A-Z]{2}', L['st'])})
    try: idx = json.load(open(OUT / 'index.json')).get('states', {})
    except Exception: idx = {}  # noqa: BLE001
    for st in want:
        if time.time() - T0 > LIMIT: notice('Access', f'stopped for time before {st}'); break
        lay = [L for L in cfg if L['st'] == st]
        if not lay: continue
        try: c = run(st, lay)
        except Exception as e: notice(f'Access {st}', f'stopped: {type(e).__name__}: {str(e)[:200]}'); continue  # noqa: BLE001
        if c: idx[st] = c
        json.dump({'updated': time.strftime('%Y-%m-%d'), 'states': idx}, open(OUT / 'index.json', 'w'), separators=(',', ':'))
    notice('Access points', f"{sum(v['parks_with_points'] for v in idx.values())} parks in {len(idx)} states have official parking / access points")


if __name__ == '__main__':
    try: main()
    except Exception as e: notice('Access points', f'stopped early: {type(e).__name__}: {str(e)[:300]}')  # noqa: BLE001
    sys.exit(0)
