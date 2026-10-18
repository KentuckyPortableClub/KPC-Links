"""US boundary ANSWER KEY, every state but Kentucky (Brandon Oct 17 2026: 'quick and best method… why not start them tonight').
For each state: every federal / state FEE record in USGS PAD-US (names, type, manager, acres, a coarse outline for 'where it is'),
matched to that state's POTA parks (data/parkinfo/US-XX.json) with the same strict rule the Kentucky tools use:
SAME NAME (generic words dropped) AND SAME KIND of place (WMA to WMA, state park to state park…), near the park's pin.
Anything unsure is NOT joined: it goes on the park's 'check' list with the reason. Writes:
  data/us-key/US-XX.json  {updated, st, parks:{ref:{n, t, m:[[objectid, name, acres, how]], c:[[objectid, name, acres, why]]}},
                           nonum:[[objectid, name, designation, manager, acres]] (biggest 300 fed/state places no POTA park matched), counts}
  data/us-key/index.json  {updated, states:{XX:{parks, matched, check, none, nonum}}}
STATES='TN IN' picks states (default: every state + DC except KY). PAD-US's firewall refuses long WHERE clauses, so we list each state with
State_Nm='XX' only and filter here."""
import json, math, os, re, sys, time, urllib.parse, urllib.request, pathlib

Q = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
ALL = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split()
STATES = (os.environ.get('STATES') or '').upper().replace(',', ' ').split() or ALL
OUT = pathlib.Path('data/us-key'); OUT.mkdir(parents=True, exist_ok=True)
T0 = time.time(); LIMIT = float(os.environ.get('MINUTES') or 300) * 60


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', '%0A')), flush=True)


def get(params, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(Q + '?' + urllib.parse.urlencode(params), headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
            with urllib.request.urlopen(req, timeout=180) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if j.get('error'): raise RuntimeError(str(j['error'])[:200])
            return j
        except Exception as e:  # noqa: BLE001
            last = e; time.sleep(8 * (i + 1))
    raise last


# ---------------- names + kinds (same idea as kpc-bounds.js, with other states' words) ----------------
GEN = (r"state natural area|natural area preserve|state nature preserve|nature preserve|natural area|fish and wildlife area|state wildlife area|"
       r"wildlife management area|wildlife area|state game lands?|game lands?|game management area|conservation area|state conservation area|"
       r"state resort park|state historic site|state historical park|state historic park|historic site|state recreation area|recreation area|"
       r"state beach|state seashore|national wildlife refuge|national recreation area|national historical park|national historic site|"
       r"national park|national forest|national grassland|national monument|national seashore|national lakeshore|national battlefield|"
       r"national military park|national preserve|national river|state park|state forest|wma|nwr|nra|sp|sf|the|of|and")
def norm(s):
    s = re.sub(r'&', ' and ', str(s or '').lower())
    s = re.sub(r"[’'`]", '', s)
    s = re.sub(r'\b(' + GEN + r')\b', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


KINDS = [('wma', r'wildlife management area|\bwma\b|wildlife area|game lands?|game management area|hunting area|fish and wildlife area|public hunting'),
         ('ca', r'conservation area'),
         ('snp', r'nature preserve|natural area|\bsnp\b|\bsna\b|natural heritage'),
         ('hist', r'historic site|historical park|historic park|historic area|\bshs\b'),
         ('sp', r'state (resort )?park|\bsrp\b|recreation(al)? area|state beach|state seashore'),
         ('nf', r'national forest|national grassland'), ('sf', r'state forest'),
         ('nwr', r'wildlife refuge|\bnwr\b'), ('nfh', r'hatchery|\bnfh\b'),
         ('nps', r'national (park|monument|preserve|seashore|lakeshore|battlefield|military park|river|scenic river|parkway)'),
         ('wild', r'wilderness')]
def kinds(s):
    s = str(s or '').lower(); return {k for k, r in KINDS if re.search(r, s)}
DES = {'SP': 'sp', 'SREC': 'sp', 'SHCA': 'hist', 'NWR': 'nwr', 'NF': 'nf', 'NG': 'nf', 'NP': 'nps', 'NM': 'nps', 'NRA': 'nps', 'NHS': 'hist', 'WA': 'wild'}


def same_name(a, b):
    a, b = norm(a), norm(b)
    if not a or not b: return False
    if a == b: return True
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return len(s) > 5 and l.startswith(s) and len(s) / len(l) >= 0.6


def same_kind(ka, kb): return not ka or not kb or bool(ka & kb)


def words(s): return set(w for w in norm(s).split() if len(w) > 2)


# ---------------- geometry helpers (coarse) ----------------
def rings(g): return g.get('rings') or [] if g else []
def bbox(g):
    xs = [p[0] for r in rings(g) for p in r]; ys = [p[1] for r in rings(g) for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None
def in_ring(x, y, r):
    ins = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi: ins = not ins
        j = i
    return ins
def inside(la, lo, g): return sum(1 for r in rings(g) if in_ring(lo, la, r)) % 2 == 1
def near(la, lo, b, pad): return b and b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad


def pad_state(st):
    recs, off = [], 0
    while True:
        j = get({'where': "State_Nm='%s'" % st, 'outFields': 'OBJECTID,Unit_Nm,Loc_Nm,Own_Type,Mang_Type,Mang_Name,Loc_Mang,Des_Tp,d_Des_Tp,Pub_Access,GIS_Acres,Category',
                 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.01, 'geometryPrecision': 3, 'f': 'json',
                 'resultOffset': off, 'resultRecordCount': 1000, 'orderByFields': 'OBJECTID'})
        fs = j.get('features', [])
        for f in fs:
            a = f.get('attributes') or {}
            if (a.get('Category') or '') != 'Fee': continue
            if (a.get('Own_Type') or '') not in ('FED', 'STAT') and (a.get('Mang_Type') or '') not in ('FED', 'STAT'): continue
            g = f.get('geometry') or {}
            a['_bb'] = bbox(g); a['_g'] = g
            a['_k'] = kinds(a.get('Unit_Nm')) | kinds(a.get('Loc_Nm')) | ({DES[a['Des_Tp']]} if a.get('Des_Tp') in DES else set())
            recs.append(a)
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < 1000): break
        off += len(fs); time.sleep(.6)
    return recs, off + len(fs)


def out_date(): return time.strftime('%Y-%m-%d')


def run(st):
    try: P = json.load(open(f'data/parkinfo/US-{st}.json'))['parks']
    except Exception: notice(f'US key {st}', 'no park file, skipped'); return None  # noqa: BLE001
    recs, seen = pad_state(st)
    parks, used = {}, set()
    for ref, r in sorted(P.items()):
        name, typ, la, lo = r[0], r[2] if len(r) > 2 else '', r[5] if len(r) > 5 else None, r[6] if len(r) > 6 else None
        kp = kinds(name) | kinds(typ)
        m, c = [], []
        for a in recs:
            nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
            close = la is None or near(la, lo, a['_bb'], .6)
            if not close: continue
            if (same_name(name, nm) or (a.get('Loc_Nm') and same_name(name, a['Loc_Nm']))) and same_kind(kp, a['_k']):
                m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), 'name'])
        if not m and la is not None:
            # unsure: not joined, only listed so a person can look
            for a in recs:
                nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
                if not near(la, lo, a['_bb'], .02): continue
                w1, w2 = words(name), words(nm)
                share = len(w1 & w2) / max(1, min(len(w1), len(w2))) if w1 and w2 else 0
                if same_name(name, nm): why = 'same name, different kind of place'
                elif share >= .6: why = 'similar name'
                elif inside(la, lo, a['_g']): why = 'the POTA pin is inside it (different name)'
                else: continue
                c.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), why])
            c.sort(key=lambda x: (x[3] != 'similar name', x[3] != 'same name, different kind of place', -x[2])); c = c[:6]
        for x in m: used.add(x[0])
        parks[ref] = {'n': name, 't': typ, 'm': sorted(m, key=lambda x: -x[2]), 'c': c}
    nonum = sorted(([a['OBJECTID'], a.get('Unit_Nm') or a.get('Loc_Nm') or '', a.get('d_Des_Tp') or a.get('Des_Tp') or '', a.get('Loc_Mang') or a.get('Mang_Name') or '',
                     round(a.get('GIS_Acres') or 0)] for a in recs if a['OBJECTID'] not in used), key=lambda x: -x[4])
    counts = {'parks': len(parks), 'matched': sum(1 for p in parks.values() if p['m']), 'check': sum(1 for p in parks.values() if not p['m'] and p['c']),
              'none': sum(1 for p in parks.values() if not p['m'] and not p['c']), 'nonum': len(nonum), 'padus': len(recs), 'read': seen}
    out = {'updated': time.strftime('%Y-%m-%d'), 'st': st, 'note': 'Built by .github/scripts/kpc_us_key.py from USGS PAD-US (fed + state fee land) and POTA. m = joined (same name + same kind), c = check by hand (NOT joined).',
           'counts': counts, 'parks': parks, 'nonum': nonum[:300]}
    # plain-words review page for this state (GitHub shows .md files nicely)
    R = OUT / 'review'; R.mkdir(exist_ok=True)
    L = [f'# {st}: POTA parks vs official land (USGS PAD-US)', '', f"Built {out_date()} by `.github/scripts/kpc_us_key.py`. **{counts['matched']} of {counts['parks']}** parks joined to official land "
         f"(same name + same kind of place). **{counts['check']}** to check by hand, **{counts['none']}** with nothing found. Nothing below is joined until a person checks it.", '']
    chk = [(r, p) for r, p in parks.items() if not p['m'] and p['c']]
    L += ['## To check (not joined)', ''] + [f"- **{r}** {p['n']} ({p['t']}) → " + '; '.join(f"{x[1]} (~{x[2]:,} ac, {x[3]})" for x in p['c']) for r, p in chk] + ['']
    L += ['## Nothing found in PAD-US', ''] + [f"- {r} {p['n']} ({p['t']})" for r, p in parks.items() if not p['m'] and not p['c']] + ['']
    L += ['## Biggest federal / state places with no POTA park joined (first 60)', ''] + [f"- {x[1]} · {x[2]} · {x[3]} · ~{x[4]:,} ac" for x in nonum[:60]]
    (R / f'US-{st}.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    (OUT / f'US-{st}.json').write_text(json.dumps(out, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
    return counts


idx = {}
try: idx = json.load(open(OUT / 'index.json')).get('states', {})
except Exception: pass  # noqa: BLE001
done = []
for st in STATES:
    if st == 'KY': continue
    if time.time() - T0 > LIMIT: notice('US key', f'stopped for time before {st}; run again for the rest'); break
    try:
        c = run(st)
    except Exception as e:  # noqa: BLE001
        notice(f'US key {st}', f'FAILED: {e}'); continue
    if c:
        idx[st] = c; done.append(st)
        print(f"{st}: {c['parks']} parks, {c['matched']} joined, {c['check']} to check, {c['none']} nothing found, {c['nonum']} places with no POTA park", flush=True)
    json.dump({'updated': time.strftime('%Y-%m-%d'), 'states': idx}, open(OUT / 'index.json', 'w'), separators=(',', ':'))
tot = {k: sum(v.get(k, 0) for v in idx.values()) for k in ('parks', 'matched', 'check', 'none')}
notice('US answer key', f"{len(done)} states this run ({' '.join(done)}). All states so far: {tot['parks']} parks, {tot['matched']} joined, {tot['check']} to check, {tot['none']} nothing found")
