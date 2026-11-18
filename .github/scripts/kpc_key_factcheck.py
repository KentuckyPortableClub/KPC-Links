#!/usr/bin/env python3
"""THE FACT CHECK (Fable for the KPC owner, 2026-11-18: 'we need accurate keys, we can not trust old information ... grading
is hard and helps improve the system'; .claude/notes/key-quality.md section 2 A).

Every park of a BUILT key is checked against plain facts, with no answer sheet at all. It reads what the key says (each
park's 'm' rows), finds those records in the same saved shapes the key was built from, and for each park writes
  WITNESSES  independent things that agree with the outline: code / pin / size / second layer / designation / agency / name
  FLAGS      facts that disagree (below)
  CLASS      verified (a code join, or the name + two more witnesses) | two | one | none | flagged (a hard flag)
It joins nothing and changes nothing: it is not a rule file (kpc_key_freeze.NOT_RULES). A flag never adds or removes an
outline; it sorts the park into the grading sample (kpc_key_grade.py) and onto the second-look list, busiest first.

THE KEY IS GRADED, NOT THE FILES THAT FEED IT. A row's record is looked up by its id and then PROVEN to be the same record
(the key's own test, kpc_key_rules.saved_row_ok: same name, acres within 10%). Layers renumber their rows; when the id now
sits on another record the row is found again by layer + name + acres, and when that fails the row is 'not in this read'
and takes part in no shape test. (18 Nov: a check that skipped this step called 54 good joins wrong.)

HARD flags (the park is 'flagged'):
  PIN_FAR     POTA's pin is outside every piece and more than 1 km from all of them (more for a very big park: a quarter
              of the radius of a circle of the park's size)
  SIZE_BIG    the outline is over 2x the official acreage (a STRONG official size only, see size_strength)
  BIG_PIECE   one record alone is over 2x the official acreage (STRONG size only)
  SHARED      a record of this park is also joined to another park of the area that fits its name as well or better
  OTHER_PARK  a record carries the full name of a DIFFERENT park of the area and not this park's own
A size flag is a QUESTION (official sizes read off a web page are often about a part of the park); the size WITNESS, when
the two sizes agree, is an answer. A flagged park is one to look at, not one that is wrong.
SOFT flags (reading aids, they pick parks for the targeted sample):
  DESIG       every named record is another kind of place than the park (park vs forest vs wildlife area ...)
  PIN_AWAY    the pin is far from this area's pieces, but the park also lies in an area this run did not check
  SIZE_SMALL  the outline is under half the official acreage (missing pieces, or the official size counts water / leases)
  SIZE_WEAK   the size disagrees but the official size is weak (the sentence may be about another place: US-4236)
  HOLDS_PINS  a small-kind park whose outline holds the pins of 2+ other parks
  FAR_PIECE   one piece lies far from the pin and from the park's own size
  NOT_IN_READ no row of the park could be proven in this read (no shape test was possible)
  CHURN       (with --prev-keys) the outline was lost, or its size or half its records changed since the last build

  python3 .github/scripts/kpc_key_factcheck.py run --keys data/us-key --cache DIR --parkinfo DIR --truth DIR --out DIR
          [--areas "US-OH US-IN"] [--prev-keys DIR] [--date YYYY-MM-DD]
      --keys      the built key files (US-XX.json / CA-XX.json: {'parks': {ref: {'n','t','g','m': [[id, name, acres, how]], 'ac'}}})
      --cache     the saved shapes the key was built from (US-XX.json.gz 'recs' with '_r' rings; hand-US-XX.<layer>.geojson.gz)
      --parkinfo  KPC-Data data/parkinfo (name, website, type, .., lat, lon, activations)
      --truth     KPC-Data data/truth (official acreage as read from the agency's page; optional)
Output (never inside data/): <out>/factcheck-<AREA>.json per area, factcheck-summary.json + .txt, factcheck-flags.csv
(one line per flag, busiest park first). Standard library only."""
import argparse, csv, datetime, glob, gzip, json, math, os, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kpc_key_rules as KR  # noqa: E402

PIN_NEAR_KM = 0.2      # the saved shapes are simplified to about 100 m: a pin this close counts as inside
PIN_FAR_KM = 1.0
SIZE_FIT = (0.67, 1.5)  # outline / official acreage inside this band = the size witness
SIZE_BIG, SIZE_SMALL = 2.0, 0.5
HARD = ('PIN_FAR', 'SIZE_BIG', 'BIG_PIECE', 'SHARED', 'OTHER_PARK')
SOFT = ('DESIG', 'PIN_AWAY', 'SIZE_SMALL', 'SIZE_WEAK', 'HOLDS_PINS', 'FAR_PIECE', 'NOT_IN_READ', 'CHURN')
STRONG_HOW = ('NPS', 'official')   # a unit-code join / an official trail or river line: it does not rest on the name
METHOD_ORDER = ('reviewed-approx', 'words', 'name', 'same', 'alias', 'reviewed', 'official', 'NPS')   # weakest first
DES_OK = {'NWR': {'refuge'}, 'NF': {'forest'}, 'NG': {'forest'}, 'SP': {'park'}, 'SREC': {'recreation', 'park'},
          'WA': {'wilderness'}, 'NP': {'park'}, 'NM': {'monument'}, 'NRA': {'recreation'}, 'SHCA': {'historic'}}
CONTAINER = {'forest', 'refuge', 'wilderness', 'herd', 'rma'}   # kinds of park that rightly hold other parks' pins
# kinds that are the same sort of place for DESIG (a State Fish and Wildlife Area on a 'fishing area' record is no clash)
KIND_GROUP = {'park': 'P', 'beach': 'P', 'historic': 'P', 'monument': 'P', 'forest': 'F', 'wildlife': 'W', 'refuge': 'W', 'fishing': 'W',
              'herd': 'W', 'conservation': 'W', 'preserve': 'W', 'reserve': 'W', 'recreation': 'R', 'rma': 'R', 'wilderness': 'X', 'study': 'X'}
LINEAR = re.compile(r'\b(trail|river|parkway|byway|canal|scenic riverway|seashore|lakeshore|greenway)\b', re.I)
# words that say what KIND of place it is, or nothing at all: they are not part of the place's own name
_GENERIC = set("""the of and at on in a state national county city regional park parks forest forests wildlife management area areas refuge
 preserve preserves reserve recreation recreational historic historical site sites monument memorial wilderness conservation natural nature
 fish fishing fishery game land lands hunting public access unit tract waterfowl production wetland district habitat wma swa sp sf nwr nf np
 sra srs shs shp nhs nhp sna wa fwa ca wpa wmd blm usfs dnr jr sr""".split())
_ABBR = {'mt': 'mount', 'mtn': 'mountain', 'mtns': 'mountain', 'ft': 'fort', 'st': 'saint', 'ste': 'sainte', 'pt': 'point', 'spgs': 'spring', 'crk': 'creek'}
_STATES = set('al ak az ar ca co ct de fl ga hi id il in ia ks ky la me md ma mi mn ms mo mt ne nv nh nj nm ny nc nd oh ok or pa ri sc sd tn tx ut vt va wa wv wi wy dc'.split())
_PLACE = re.compile(r"((?:[A-Z][\w.'’-]+ ){1,5})(?:National|State|County) (?:Wildlife Refuge|Park|Forest|Recreation Area|Monument|"
                    r"Preserve|Wildlife Area|Wildlife Management Area|Historic Site|Natural Area|Grassland)")


# ---------------- names ----------------
def core(name):
    """The place's own words: kind words out ('State Wildlife Area', 'WMA'), short forms spelled out (Mt -> mount), a plural s
    off, a leading state code off ('PA 144 State Game Land' -> ['144']). 'Black Canyon State Wildlife Area' -> ['black', 'canyon']."""
    t = [_ABBR.get(w, w) for w in KR._full(name).split()]
    if len(t) > 1 and t[0] in _STATES: t = t[1:]
    t = [re.sub(r"(?<=[a-z]{4})s$", '', w) for w in t if w not in _GENERIC]
    return [w for w in t if w and w not in _GENERIC]


def _same_word(a, b):
    """The same word allowing a slip of the pen: one letter off in a word of 5+, two in a word of 9+. A number never differs."""
    if a == b: return True
    if any(c.isdigit() for c in a + b) or min(len(a), len(b)) < 5: return False
    return KR._lev(a, b, 3) <= (2 if min(len(a), len(b)) >= 9 else 1)


def _holds(x, y):
    return all(any(_same_word(a, b) for b in y) for a in x)


def name_fit(park_name, names):
    """'exact' when one of the record's names has the park's place words and no others (spelling slips, hyphens and short
    forms aside); 'part' when one holds the other; ''."""
    pc, best = core(park_name), ''
    for n in names or []:
        rc = core(n)
        if not pc or not rc: continue
        if (_holds(pc, rc) and _holds(rc, pc)) or _same_word(''.join(pc), ''.join(rc)): return 'exact'
        if _holds(pc, rc) or _holds(rc, pc): best = 'part'
    return best


def full_names(rec, row):
    """The record's own names as full names (with and without a plural s), for a whole-name test."""
    out = set()
    for n in ([rec.get('Unit_Nm'), rec.get('Loc_Nm')] if rec else [row[1] if len(row) > 1 else '']):
        if n: f = KR._full(n); out |= {f, re.sub(r's$', '', f)}
    return out - {''}


def fit_rank(park_name, rec, row):
    """How well a record fits a park's name: 3 the whole name, 2 the same place words, 1 one holds the other, 0 nothing."""
    pf = KR._full(park_name)
    if {pf, re.sub(r's$', '', pf)} & full_names(rec, row): return 3
    f = name_fit(park_name, [x for x in ((rec.get('Unit_Nm'), rec.get('Loc_Nm')) if rec else (row[1],)) if x])
    return 2 if f == 'exact' else 1 if f == 'part' else 0


def classify(e):
    """verified = a code join, or the name + two more witnesses; flagged = any HARD flag."""
    w = e.get('witnesses') or []
    if any(f[0] in HARD for f in e.get('flags') or []): return 'flagged'
    if 'code' in w or ('name' in w and len([x for x in w if x not in ('name', 'code')]) >= 2): return 'verified'
    return 'two' if len(w) >= 2 else 'one' if len(w) == 1 else 'none'


def method(how):
    """The matcher's method word of a row ('name (designation code ignored) · ...' -> 'name')."""
    h = str(how or '').split(' · ')[0].strip()
    for m in ('reviewed-approx', 'reviewed', 'words', 'name', 'same', 'alias', 'official', 'NPS'):
        if h.startswith(m): return m
    return h.split(' ')[0] or '?'


def family(rid):
    """The layer a record id comes from: its letters ('sgvae490681' -> 'sgvae'); a bare number is PAD-US."""
    return re.sub(r'\d+$', '', str(rid)) or 'padus'


# ---------------- shapes ----------------
def rings_of(rec):
    out = []
    def walk(x):
        if isinstance(x, list) and x and isinstance(x[0], list) and x[0] and isinstance(x[0][0], (int, float)): out.append(x)
        elif isinstance(x, list):
            for y in x: walk(y)
    walk((rec or {}).get('_r')); return out


def bbox_of(rings):
    xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def inside(lat, lon, rings):
    """Even-odd test over every ring (holes and many-part shapes both come out right)."""
    c = False
    for ring in rings:
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i][0], ring[i][1]; x2, y2 = ring[i - 1][0], ring[i - 1][1]
            if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1: c = not c
    return c


def edge_km(lat, lon, rings):
    """Km from a point to the nearest EDGE (to the line between corners, not only to the corners)."""
    kx, ky, best = 111.32 * math.cos(math.radians(lat)), 110.57, 1e9
    for ring in rings:
        n = len(ring)
        for i in range(n):
            ax, ay = (ring[i - 1][0] - lon) * kx, (ring[i - 1][1] - lat) * ky
            bx, by = (ring[i][0] - lon) * kx, (ring[i][1] - lat) * ky
            dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
            t = 0.0 if L == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L))
            d = math.hypot(ax + t * dx, ay + t * dy)
            if d < best: best = d
    return best


def pin_km(lat, lon, rec):
    """0 when the pin is inside the record, else km to its edge; None when the record has no shape."""
    rr = rec.get('_rings')
    if rr is None: rr = rec['_rings'] = rings_of(rec); rec['_bb'] = bbox_of(rr)
    if not rr: return None
    bb = rec['_bb']
    if bb[0] <= lon <= bb[2] and bb[1] <= lat <= bb[3] and inside(lat, lon, rr): return 0.0
    return edge_km(lat, lon, rr)


def park_pin_km(lat, lon, recs):
    """The park's pin against ALL its pieces: 0 when inside one, else km to the nearest edge; None when no piece has a shape."""
    kx, cands = 111.32 * math.cos(math.radians(lat)), []
    for rec in recs:
        rr = rec.get('_rings')
        if rr is None: rr = rec['_rings'] = rings_of(rec); rec['_bb'] = bbox_of(rr)
        if not rr: continue
        bb = rec['_bb']
        if bb[0] <= lon <= bb[2] and bb[1] <= lat <= bb[3] and inside(lat, lon, rr): return 0.0
        cands.append((math.hypot(max(bb[0] - lon, 0, lon - bb[2]) * kx, max(bb[1] - lat, 0, lat - bb[3]) * 110.57), id(rec), rec))
    best = None
    for low, _i, rec in sorted(cands):          # the box distance is never more than the edge distance: stop when it passes the best
        if best is not None and low >= best: break
        d = edge_km(lat, lon, rec['_rings'])
        if best is None or d < best: best = d
    return best


def ring_acres(rings):
    """Acres of a shape from its corners (even-odd: holes come off when rings are wound opposite; else an upper bound)."""
    tot = 0.0
    for ring in rings:
        if len(ring) < 3: continue
        lat0 = sum(p[1] for p in ring) / len(ring); kx, ky = 111.32 * math.cos(math.radians(lat0)), 110.57
        a = 0.0
        for i in range(len(ring)):
            x1, y1 = ring[i - 1][0] * kx, ring[i - 1][1] * ky; x2, y2 = ring[i][0] * kx, ring[i][1] * ky
            a += x1 * y2 - x2 * y1
        tot += a / 2
    return abs(tot) * 247.105


# ---------------- loading ----------------
def load_cache(cache_dir, area):
    """{record id: record} of one area: the cache file plus the hand layers of that area."""
    by_id = {}
    f = pathlib.Path(cache_dir) / f'{area}.json.gz'
    if f.is_file():
        for r in json.load(gzip.open(f, 'rt', encoding='utf-8')).get('recs') or []: by_id[str(r.get('OBJECTID'))] = r
    for hf in sorted(pathlib.Path(cache_dir).glob(f'hand-{area}.*.geojson.gz')):
        try: d = json.load(gzip.open(hf, 'rt', encoding='utf-8'))
        except (OSError, ValueError): continue
        k = d.get('kpc') or {}; lay, nf_, of_ = k.get('layer') or '', k.get('name_field'), k.get('oid_field') or 'OBJECTID'
        for ft in d.get('features') or []:
            p, g = ft.get('properties') or {}, ft.get('geometry') or {}
            rid = f"{lay}{p.get(of_)}"
            if rid in by_id: continue
            rec = {'OBJECTID': rid, 'Unit_Nm': p.get(nf_) or '', 'Loc_Nm': '', 'Mang_Name': lay.upper(), 'Des_Tp': '', '_r': g.get('coordinates')}
            rec['GIS_Acres'] = round(ring_acres(rings_of(rec)), 1); by_id[rid] = rec
    return by_id


def name_index(by_id):
    ix = {}
    for rid, r in by_id.items():
        for n in KR.rec_names(r) or []: ix.setdefault((family(rid), KR.nf(n)), []).append(r)
    return ix


def core_index(by_id):
    """{the place words of a record name: [records]} for the second-layer witness (looked up by the park's own place words)."""
    cx = {}
    for rid, r in by_id.items():
        for n in (r.get('Unit_Nm'), r.get('Loc_Nm')):
            k = tuple(sorted(core(n))) if n else ()
            if k: cx.setdefault(k, []).append(r)
    return cx


def prove(row, by_id, ix):
    """The record a key row means in this read, PROVEN by the key's own test, or (None, why). Returns (record, how found)."""
    rec = by_id.get(str(row[0]))
    if rec is not None and KR.saved_row_ok(row, rec): return rec, 'id'
    got = [r for r in ix.get((family(row[0]), KR.nf(row[1] if len(row) > 1 else '')), []) if KR.saved_row_ok(row, r)]
    if len(got) == 1: return got[0], 'found again by layer + name + acres'
    return None, ('the id now sits on another record' if rec is not None else 'the id is not in this read')


def size_strength(park_name, off):
    """How far an 'official acreage' read off a web page can be trusted: 'strong' (the truth checker calls it clean, and the
    sentence names this park or no other named place stands beside it), 'weak' (another place is named: US-4236's 1,238
    acres belonged to the refuge next door), 'unclean' (the checker's own doubt), None (no size)."""
    if not isinstance(off, dict) or not off.get('acres'): return None
    if not off.get('clean'): return 'unclean'
    cw = [w for w in core(park_name) if len(w) > 3]
    if any(w in KR._full(off.get('sent') or '') for w in cw): return 'strong'
    text = f"{off.get('line') or ''} {off.get('sent') or ''}"
    return 'weak' if any(not _holds(core(m.group(1)), cw) for m in _PLACE.finditer(text) if core(m.group(1))) else 'strong'


# ---------------- one area ----------------
def check_area(area, key, by_id, pinfo, truth, agency=None, prev=None, today=None):
    parks = {r: p for r, p in (key.get('parks') or {}).items() if isinstance(p, dict)}
    ix = name_index(by_id); cx = core_index(by_id)
    full = {}      # full name of every park of the area -> refs (for OTHER_PARK)
    for r, p in parks.items():
        f = KR._full((pinfo.get(r) or [None])[0] or p.get('n'))
        if f: full.setdefault(f, set()).add(r); full.setdefault(re.sub(r's$', '', f), set()).add(r)
    owners = {}    # record id -> refs that join it (for SHARED)
    for r, p in parks.items():
        for m in p.get('m') or []: owners.setdefault(str(m[0]), set()).add(r)
    pins = {}
    for r in parks:
        pi = pinfo.get(r) or []
        la, lo = (pi[5], pi[6]) if len(pi) > 6 else (None, None)
        if isinstance(la, (int, float)) and isinstance(lo, (int, float)) and (la or lo) and abs(la) <= 90 and abs(lo) <= 180: pins[r] = (la, lo)
    agency = agency or {}
    out = {}
    for ref, p in sorted(parks.items()):
        rows = p.get('m') or []
        pi = pinfo.get(ref) or []
        name = (pi[0] if pi else None) or p.get('n') or ''
        ptype = (pi[2] if len(pi) > 2 else None) or p.get('t') or ''
        act = pi[7] if len(pi) > 7 and isinstance(pi[7], (int, float)) else 0
        e = {'n': name, 't': ptype, 'g': p.get('g'), 'act': act, 'rows': len(rows)}
        if not rows: out[ref] = e; continue
        pin = pins.get(ref)
        ptw = KR.type_words(f'{name} {ptype}')
        prov, shown, fits, fams, meths = [], [], [], {}, set()
        for m in rows:
            row = list(m) + [''] * (4 - len(m))
            rec, how_found = prove(row, by_id, ix)
            prov.append((row, rec)); meths.add(method(row[3]))
            fit = name_fit(name, (KR.rec_names(rec) if rec else None) or [row[1]]); fits.append(fit)
            if rec is not None and fit == 'exact': fams[family(row[0])] = fams.get(family(row[0]), 0.0) + float(rec.get('GIS_Acres') or row[2] or 0)
            if len(shown) < 12:
                km = pin_km(pin[0], pin[1], rec) if (rec is not None and pin and len(rows) <= 40) else None
                shown.append([row[0], row[1], row[2], method(row[3]), how_found, None if km is None else round(km, 2), fit])
        recs = [(row, rec) for row, rec in prov if rec is not None]
        unproven = len(prov) - len(recs)
        best_km = park_pin_km(pin[0], pin[1], [rec for _row, rec in recs]) if pin and recs else None
        e['name_fit'] = 'exact' if 'exact' in fits else 'part' if 'part' in fits else ''
        e['m'] = shown; e['methods'] = sorted(meths, key=lambda x: METHOD_ORDER.index(x) if x in METHOD_ORDER else 99)
        e['weakest'] = e['methods'][0]; e['not_in_read'] = unproven
        # ---- size
        by_fam = {}
        for row, rec in recs: by_fam[family(row[0])] = by_fam.get(family(row[0]), 0.0) + float(rec.get('GIS_Acres') or row[2] or 0)
        est = max(by_fam.values()) if by_fam else sum(float(r[2] or 0) for r in rows if len(r) > 2)
        ac = float(p['ac']) if isinstance(p.get('ac'), (int, float)) and p['ac'] > 0 else est
        off = (truth.get(ref) or {}).get('official'); strength = size_strength(name, off)
        oac = float(off['acres']) if strength else None
        e['acres'] = {'outline': round(ac), 'from': 'key' if 'ac' in p else 'estimate', 'official': oac, 'official_is': strength,
                      'official_url': (off or {}).get('url') if strength else None, 'official_says': str((off or {}).get('sent') or '')[:160] if strength else None}
        flags, wit = [], []
        if any(method(r[3]) in STRONG_HOW for r in rows): wit.append('code')
        # ---- pin
        if pin: e['pin'] = [round(pin[0], 5), round(pin[1], 5)]
        if pin and best_km is not None:
            e['pin_km'] = round(best_km, 2)
            if best_km <= PIN_NEAR_KM: wit.append('pin')
            elif best_km > max(PIN_FAR_KM, 0.25 * math.sqrt(max(ac, 1) * 0.004047 / math.pi)): flags.append(['PIN_FAR', f'the pin is {best_km:.1f} km outside the nearest piece'])
        # ---- size witness and flags
        if oac and ac:
            ratio = ac / oac
            if strength == 'strong':
                if SIZE_FIT[0] <= ratio <= SIZE_FIT[1]: wit.append('size')
                elif ratio > SIZE_BIG: flags.append(['SIZE_BIG', f'outline {round(ac):,} acres against {round(oac):,} official ({ratio:.1f}x)'])
                elif ratio < SIZE_SMALL: flags.append(['SIZE_SMALL', f'outline {round(ac):,} acres against {round(oac):,} official ({ratio:.2f}x)'])
                big = [row for row, rec in recs if float(rec.get('GIS_Acres') or row[2] or 0) > SIZE_BIG * oac]
                if big: flags.append(['BIG_PIECE', f"'{big[0][1]}' alone is {round(float(big[0][2] or 0)):,} acres against {round(oac):,} official"])
            elif ratio > SIZE_BIG or ratio < SIZE_SMALL:
                flags.append(['SIZE_WEAK', f'outline {round(ac):,} acres against {round(oac):,} "official", but that size is {strength}'])
        # ---- name, second layer
        if 'exact' in fits: wit.append('name')
        # a second official layer that shows the same land under the same name, whether or not the key joined it (so the
        # witness does not come and go when the key drops a duplicate copy)
        if fams and recs:
            for _row, rec in recs[:60]:
                if rec.get('_rings') is None: rec['_rings'] = rings_of(rec); rec['_bb'] = bbox_of(rec['_rings'])
            bbs = [r['_bb'] for _row, r in recs[:60] if r.get('_bb')]
            for o in cx.get(tuple(sorted(core(name))), [])[:400]:
                f = family(o.get('OBJECTID'))
                if f in fams or not bbs: continue
                if o.get('_rings') is None: o['_rings'] = rings_of(o); o['_bb'] = bbox_of(o['_rings'])
                ob = o.get('_bb')
                if ob and any(ob[0] <= b[2] and b[0] <= ob[2] and ob[1] <= b[3] and b[1] <= ob[3] for b in bbs):
                    fams[f + ' (not joined)'] = fams.get(f + ' (not joined)', 0.0) + float(o.get('GIS_Acres') or 0)
        ff = sorted(v for v in fams.values() if v > 0)
        if len(ff) >= 2 and ff[-2] >= 0.7 * ff[-1]: wit.append('second layer')
        # ---- designation
        if any(rec.get('Des_Tp') in DES_OK and (DES_OK[rec['Des_Tp']] & ptw) for _row, rec in recs): wit.append('designation')
        named = [KR.type_words(' '.join((KR.rec_names(rec) if rec else None) or [row[1]])) for row, rec in prov[:40]]
        named = [t for t in named if t]
        pg = {KIND_GROUP.get(k) for k in ptw} - {None}
        if pg and named and len(named) == min(len(rows), 40) and not any(({KIND_GROUP.get(k) for k in t} - {None}) & pg for t in named):
            flags.append(['DESIG', f"the park is a {'/'.join(sorted(ptw))} and every record is a {'/'.join(sorted(set().union(*named)))}"])
        # ---- agency (learned table: weak, but independent of this park's own name)
        host = KR.web_host(pi[1] if len(pi) > 1 else '')
        trow = agency.get(host) or {}
        if trow.get('_parks', 0) >= 5 and any(trow.get(str(rec.get('Mang_Name') or ''), 0) >= max(3, 0.3 * trow['_parks']) for _row, rec in recs): wit.append('agency')
        # ---- shared and other park's name
        sh = set()
        for row, rec in prov:
            oth = [o for o in owners.get(str(row[0]), ()) if o != ref]
            if not oth: continue
            mine_rank = fit_rank(name, rec, row)
            if any(fit_rank((pinfo.get(o) or [None])[0] or parks[o].get('n') or '', rec, row) >= mine_rank for o in oth): sh.update(oth)
        sh = sorted(sh)
        if sh: flags.append(['SHARED', f"a record is also joined to {', '.join(sh[:4])}" + (f' (+{len(sh) - 4})' if len(sh) > 4 else '')])
        mine = {KR._full(name), re.sub(r's$', '', KR._full(name))}
        for row, rec in prov[:200]:
            fn = full_names(rec, row)
            if fn & mine: continue
            hit = next((c for c in sorted(fn) if c in full and ref not in full[c]), None)
            if hit: flags.append(['OTHER_PARK', f"'{(rec or {}).get('Unit_Nm') or row[1]}' carries the name of {sorted(full[hit])[0]}"]); break
        # ---- far piece
        if pin and 2 <= len(recs) <= 40 and not LINEAR.search(f'{name} {ptype}') and not (ptw & CONTAINER):
            rad = math.sqrt(max(ac, 1) * 0.004047 / math.pi)
            for row, rec in recs:
                km = pin_km(pin[0], pin[1], rec)
                if km is not None and km > max(5.0, 3 * rad): flags.append(['FAR_PIECE', f"'{row[1]}' is {km:.0f} km from the pin"]); break
        if unproven == len(rows): flags.append(['NOT_IN_READ', 'no row of this park could be proven in this read'])
        e['_recs'] = [rec for _row, rec in recs]   # dropped before saving (HOLDS_PINS below)
        e['witnesses'], e['flags'] = wit, flags
        out[ref] = e
    # ---- HOLDS_PINS: a small-kind park whose outline holds the pins of other parks
    for ref, e in out.items():
        rs = e.pop('_recs', None)
        if not rs or len(rs) > 60: continue
        ptw = KR.type_words(f"{e['n']} {e['t']}")
        if ptw & CONTAINER or LINEAR.search(f"{e['n']} {e['t']}") or re.search(r'\bnational\b', e['n'], re.I): continue
        held = []
        for o, (la, lo) in pins.items():
            if o == ref or name_fit(e['n'], [out[o]['n']]): continue
            if any(pin_km(la, lo, rec) == 0.0 for rec in rs): held.append(o)
            if len(held) >= 6: break
        if len(held) >= 2: e['flags'].append(['HOLDS_PINS', f"the outline holds the pins of {', '.join(held[:4])}"])
    # ---- CHURN and the class
    for ref, e in out.items():
        if not e.get('rows'):
            if prev and (prev.get(ref) or {}).get('m'): e['flags'] = [['CHURN', 'had an outline in the last build, has none now']]; e['class'] = 'pin'
            else: e['class'] = 'pin'
            continue
        if prev is not None:
            q = prev.get(ref) or {}; a, b = {str(m[0]) for m in q.get('m') or []}, {str(m[0]) for m in (key['parks'][ref].get('m') or [])}
            pa, na = q.get('ac'), key['parks'][ref].get('ac')
            if a and (len(a & b) < 0.5 * len(a) or (pa and na and abs(na - pa) > 0.1 * pa)):
                e['flags'].append(['CHURN', f'{len(a)} records / {pa} acres last build, {len(b)} / {na} now'])
        e['class'] = classify(e)
    return {'area': area, 'made': today or datetime.date.today().isoformat(), 'key_read': key.get('read') or '', 'parks': out}


def summarize(doc):
    c = {'parks': 0, 'with_outline': 0}
    for e in doc['parks'].values():
        c['parks'] += 1
        if not e.get('rows'): continue
        c['with_outline'] += 1; c[e['class']] = c.get(e['class'], 0) + 1
        for f in e['flags']: c[f[0]] = c.get(f[0], 0) + 1
        if e.get('not_in_read'): c['rows_not_in_read'] = c.get('rows_not_in_read', 0) + e['not_in_read']
    return c


def line(area, c):
    w = c.get('with_outline', 0) or 1
    cls = ' '.join(f"{k} {c.get(k, 0)}" for k in ('verified', 'two', 'one', 'none', 'flagged'))
    fl = ' '.join(f"{k} {c[k]}" for k in HARD + SOFT if c.get(k))
    return (f"{area}  parks {c['parks']}, with an outline {c.get('with_outline', 0)} | {cls} ({100 * c.get('verified', 0) // w}% verified by facts, "
            f"{100 * c.get('flagged', 0) // w}% flagged) | {fl or 'no flags'}" + (f" | rows not in this read {c['rows_not_in_read']}" if c.get('rows_not_in_read') else ''))


def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    for k in ('keys', 'cache', 'parkinfo', 'out'): r.add_argument('--' + k, required=True)
    r.add_argument('--truth'); r.add_argument('--areas'); r.add_argument('--prev-keys'); r.add_argument('--date')
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out).resolve()
    root = HERE.parents[1]
    if root in out.parents and out.relative_to(root).parts[:1] == ('data',):
        raise SystemExit('--out must not be inside data/ (BRANCH FIRST: results go on KPC-Data tools-out)')
    out.mkdir(parents=True, exist_ok=True)
    want = set((a.areas or '').replace(',', ' ').split())
    files = sorted(f for f in glob.glob(os.path.join(a.keys, '[A-Z][A-Z]-[A-Z][A-Z].json')) if not want or os.path.basename(f)[:-5] in want)
    agency = KR.agency_table()
    total, lines, flagrows, docs = {}, [], [], []
    in_areas = {}
    for pf in glob.glob(os.path.join(a.parkinfo, '*.json')):
        try:
            for r in (json.load(open(pf, encoding='utf-8')).get('parks') or {}): in_areas.setdefault(r, set()).add(os.path.basename(pf)[:-5])
        except (OSError, ValueError): pass
    for f in files:
        area = os.path.basename(f)[:-5]
        try: key = json.load(open(f, encoding='utf-8'))
        except (OSError, ValueError) as ex: lines.append(f'{area}  key not readable: {ex}'); continue
        by_id = load_cache(a.cache, area)
        if not by_id: lines.append(f'{area}  no saved shapes for this area in --cache: not checked'); continue
        def _j(d, name):
            p = pathlib.Path(d) / name if d else None
            try: return (json.load(open(p, encoding='utf-8')).get('parks') or {}) if p and p.is_file() else {}
            except (OSError, ValueError): return {}
        prev = None
        if a.prev_keys:
            try: prev = {r: p for r, p in (json.load(open(os.path.join(a.prev_keys, area + '.json'), encoding='utf-8')).get('parks') or {}).items() if isinstance(p, dict)}
            except (OSError, ValueError): prev = None
        doc = check_area(area, key, by_id, _j(a.parkinfo, area + '.json'), _j(a.truth, area + '.json'), agency, prev, a.date)
        docs.append(doc); print(f'{area} checked', flush=True)
    # a park in two areas has its pin in one of them: PIN_FAR stands only when no checked area holds the pin
    best, done = {}, {d['area'] for d in docs}
    for d in docs:
        for ref, e in d['parks'].items():
            if 'pin_km' in e: best[ref] = min(best.get(ref, 1e9), e['pin_km'])
    for d in docs:
        for ref, e in d['parks'].items():
            fl = e.get('flags') or []
            if any(f[0] == 'PIN_FAR' for f in fl):
                if best.get(ref, 1e9) <= max(PIN_FAR_KM, 0.25 * math.sqrt(max((e.get('acres') or {}).get('outline') or 1, 1) * 0.004047 / math.pi)): e['flags'] = [f for f in fl if f[0] != 'PIN_FAR']
                elif (in_areas.get(ref) or set()) - done: e['flags'] = [['PIN_AWAY', f[1] + '; the park also lies in ' + ', '.join(sorted(in_areas[ref] - done))] if f[0] == 'PIN_FAR' else f for f in fl]
                if e.get('rows'): e['class'] = classify(e)
    for doc in docs:
        area = doc['area']
        c = summarize(doc); doc['counts'] = c
        with open(out / f'factcheck-{area}.json', 'w', encoding='utf-8') as fh: json.dump(doc, fh, ensure_ascii=False, separators=(',', ':'))
        lines.append(line(area, c))
        for k, v in c.items(): total[k] = total.get(k, 0) + v
        for ref, e in doc['parks'].items():
            for fl in e.get('flags') or []:
                flagrows.append({'activations': e['act'], 'area': area, 'ref': ref, 'name': e['n'], 'grade': e['g'], 'class': e.get('class'),
                                 'weakest_method': e.get('weakest', ''), 'flag': fl[0], 'kind': 'HARD' if fl[0] in HARD else 'soft', 'detail': fl[1]})
    lines.append(line('ALL', total) if total else 'ALL  nothing checked')
    (out / 'factcheck-summary.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (out / 'factcheck-summary.json').write_text(json.dumps({'made': a.date or datetime.date.today().isoformat(), 'all': total, 'lines': lines}, indent=1) + '\n', encoding='utf-8')
    flagrows.sort(key=lambda x: (x['kind'] != 'HARD', -(x['activations'] or 0), x['ref']))
    with open(out / 'factcheck-flags.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, ['activations', 'area', 'ref', 'name', 'grade', 'class', 'weakest_method', 'flag', 'kind', 'detail']); w.writeheader(); w.writerows(flagrows)
    print(lines[-1]); print(f'wrote {out}/factcheck-summary.txt, factcheck-flags.csv and one file per area')
    return 0


if __name__ == '__main__':
    sys.exit(main())
