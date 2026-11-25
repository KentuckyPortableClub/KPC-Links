#!/usr/bin/env python3
"""kpc_same_land.py: is this record the SAME LAND as that one? (KPC owner, 25 Nov 2026, 6:20 + 6:28 AM: 'a better matcher',
'accuracy first', 'never use a row number alone between two reads'.)

Two reads of one agency layer can give the same land different row numbers (OBJECTID): Minnesota's state forest, natural area
and state land layers were numbered again between our 12 Nov saved copy and the outline store's 14 Nov read (Lost Valley Prairie
was row 55, then row 210; same name, same acres to 8 decimals, same outline). So a record is matched to a record of another read
by PROOF, best first, and never by its number:

  1. 'id'         the agency's own UNIT id (id_spec: keep-record-fields.json 'unit id' / crosswalk fields; a web address by the
                  id inside it) is the same on both, after normalising ('SNA 01041' = 'SNA1041', 1041 = '1041.0'), boxes overlap. Pieces of one unit
                  may share an id. A size change over 2 times is noted ('same id, size changed'). Two DIFFERENT ids of the
                  same field = not the same record, whatever else agrees.
  2. 'overlap'    the outlines share ground: at least OVERLAP_SMALL (80%) of the smaller one and OVERLAP_LARGE (50%) of the
                  larger one (area, measured on the outlines, not boxes). Works when acres are missing.
     'piece'      at least PIECE_IN (90%) of the smaller record lies inside the larger one and they share a real name.
     An outline too rough for its size (measured area 20% off its acres, or a tiny 5-point shape) cannot be measured: 'can't tell'.
  3. 'name_size'  the same name (not a generic name such as 'Unit 1' or 'Tract 2'; letters and digits, case aside), sizes within
                  SIZE_TOL (10%), boxes overlap, and the outlines do not show different ground. Name alone never counts.
  R1 (grade 25 Nov 9:51 AM, after the owner's 9:11 MN test): an AGENCY RECORD id (AGENCY_RECORD_IDS: Minnesota DNR's state land
                  'su_id', its wildlife areas' 'uniqueid') proves 'id' only when the boxes overlap AND (a real name in common OR
                  sizes within 10%). A different value never refuses (such a field can be renumbered too).
  R2: an outline too rough to measure (one side coarse) is measured by the OLD record's grid points against the FRESH outline,
      with a 0.001-degree edge allowance: 80% / 50% = 'overlap'; 90% inside + a shared name = 'piece'.
  R3: two records proven by name + size ('two fits'): the one holding at least half of the old record's ground (the R2 measure)
      while every other holds less wins; never the row number.
  None            not proven: the caller shows the pin only and marks it for the code to fix (never a person's job).

A US rule file (kpc_key_freeze.RULE_FILES['us-key']): a change here moves the US rules hash.
Pure Python (no shapely), so GitHub, the PC and the tests measure the same way: the shared share of an outline is counted on a
fixed grid of points over the smaller record's box (GRID x GRID; finer for thin shapes).
  python3 kpc_same_land.py --selftest
"""
import json, math, os, re, sys

OVERLAP_SMALL = 0.80   # owner's numbers to OK (25 Nov 6:20 AM plan): 80% of the smaller record
OVERLAP_LARGE = 0.50   # and 50% of the larger one
PIECE_IN = 0.90        # a piece: 90% of it inside the whole
DIFFERENT_GROUND = 0.50  # under half of the smaller record on the other's ground = different land (name + size cannot win)
SIZE_TOL = 0.10        # name + size: within 10%
SIZE_JUMP = 2.0        # same id, size changed by more than 2 times: noted
GRID = 16          # first look; a share near a threshold is measured again on GRID_FINE
GRID_FINE = 48
NEAR_EDGE = 0.08
MIN_HITS = 12          # fewer grid points than this inside the smaller record: the overlap cannot be told

LEVELS = ('id', 'overlap', 'piece', 'name_size')
# R1 (grade 25 Nov 9:51 AM): the agency's own record id fields, by layer (the 12 Nov saved copy holds them in 'SA': sgmne su_id on
# 13,295 records, sgmna uniqueid on 1,751). Proof only with the place and a name or the size agreeing; a different value never refuses.
AGENCY_RECORD_IDS = {'sgmne': ('su_id',), 'sgmna': ('uniqueid',)}
EDGE = 0.001           # R2: a grid point this close (degrees) to the fresh outline's edge counts as on its ground

KIND_WORDS = {'state', 'national', 'county', 'city', 'regional', 'public', 'park', 'parks', 'forest', 'forests', 'wildlife',
              'management', 'area', 'areas', 'natural', 'scientific', 'preserve', 'reserve', 'refuge', 'recreation', 'recreational',
              'conservation', 'land', 'lands', 'unit', 'units', 'tract', 'tracts', 'parcel', 'parcels', 'access', 'site', 'sites',
              'wma', 'wa', 'sna', 'sf', 'sp', 'nwr', 'nf', 'tract', 'section', 'block', 'lot', 'zone', 'part', 'piece', 'the',
              'of', 'and', 'acquisition', 'project', 'easement', 'fee', 'owned', 'dnr', 'dec', 'habitat', 'game', 'fish',
              'hunting', 'fishing', 'trail', 'trails', 'property', 'properties', 'unknown', 'unnamed', 'none', 'na', 'n', 'a',
              'no', 'name', 'other', 'misc', 'miscellaneous', 'admin', 'administrative', 'office', 'headquarters'}
GENERIC_RX = re.compile(r'^(?:(?:unit|tract|parcel|area|block|section|sec|lot|site|piece|part|zone|subunit|pod|cell|no|number|#)'
                        r'[\s#.:-]*[0-9ivxlc]+[a-z]?)$', re.I)


def name_key(s):
    return re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def generic(name):
    """A name that does not tell one piece of land from another: 'Unit 1', 'Tract 3B', 'Wildlife Management Area', ''."""
    t = str(name or '').strip()
    if not name_key(t): return True
    if GENERIC_RX.match(t): return True
    words = [w for w in re.split(r'[^a-z0-9]+', t.lower()) if w]
    return all(w in KIND_WORDS or w.isdigit() or re.fullmatch(r'[ivxlc]+', w) for w in words)


def norm_id(v):
    """'SNA 01041' -> 'SNA1041' = 'SNA01041' -> 'SNA1041'; 1041.0 -> '1041'; '' / None / 0 -> ''. Leading zeros in a run of digits
    never make two ids different (grade 25 Nov, M3 case 4)."""
    if v is None or isinstance(v, bool): return ''
    if isinstance(v, float):
        if v != v or v == 0: return ''
        v = int(v) if v == int(v) else v
    s = str(v).strip().upper()
    if re.fullmatch(r'-?\d+\.0+', s): s = s.split('.')[0]
    s = re.sub(r'[\s_\-./]+', '', s)
    s = re.sub(r'(?<![0-9])0+(?=[0-9])', '', s)
    return '' if s in ('', '0', 'NONE', 'NULL', 'NA') else s


_TABLES = {}


def _table(name):
    if name not in _TABLES:
        try:
            with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), name), encoding='utf-8') as f:
                _TABLES[name] = json.load(f)
        except (OSError, ValueError):
            _TABLES[name] = {}
    return _TABLES[name]


def id_spec(layer):
    """{field (lower case): (kind, [patterns])} for one layer. Only a UNIT id proves or refuses (grade 25 Nov, M3):
      'unit'  the id finder's 'unit id' fields and the crosswalk's SAME ID fields (.github/keep-record-fields.json);
      'web'   a web-address field: compared by the id INSIDE the address (.github/link-id-ties.json patterns), never as text,
              so http / https or a moved site is not a different id;
    A 'record id' field (numbered like a row) is left out: it can be renumbered too. PAD-US: the Park Service unit code."""
    if layer in ('padus', 'PAD-US', ''): return {'unit_code': ('unit', [])}
    out = {}
    ties = {}
    for t in (_table('link-id-ties.json').get('ties') or []):
        if t.get('field') and (t.get('layer') or t.get('pre')) == layer and (t.get('rx') or t.get('pattern')):
            ties.setdefault(str(t['field']).lower(), []).append(t.get('rx') or t.get('pattern'))
    v = (_table('keep-record-fields.json').get('layers') or {}).get(layer) or {}
    why = ' '.join(str(w) for w in v.get('why') or []).lower()
    for f in v.get('fields') or []:
        fl = str(f).lower()
        if fl in ties or 'web address' in why: out[fl] = ('web', ties.get(fl) or [])
        elif 'unit id' in why or 'crosswalk' in why: out[fl] = ('unit', [])
    for fl, rx in ties.items(): out.setdefault(fl, ('web', rx))
    for fl in AGENCY_RECORD_IDS.get(layer, ()):   # R1: agency record ids (never 'unit': they never refuse)
        if fl not in out: out[fl] = ('arec', [])
    return out


def _web_id(v, pats):
    t = str(v or '')
    for rx in pats:
        try: m = re.search(rx, t, re.I)
        except re.error: continue
        if m: return norm_id(''.join(g for g in m.groups() if g) or m.group(0))
    return ''


# ---- outlines -------------------------------------------------------------------------------------------------------------

def rings_of(g):
    """Rings as lists of (lon, lat) from {'rings': [...]}, a list of rings, or None."""
    if isinstance(g, dict): g = g.get('rings')
    out = []
    for r in g or []:
        try: pts = [(float(p[0]), float(p[1])) for p in r if len(p) >= 2]
        except (TypeError, ValueError, IndexError): continue
        if len(pts) >= 3: out.append(pts)
    return out


def box_of(rings):
    xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def boxes_overlap(a, b, slack=0.0):
    if not a or not b: return False
    return a[0] <= b[2] + slack and b[0] <= a[2] + slack and a[1] <= b[3] + slack and b[1] <= a[3] + slack


def _inside(x, y, rings, rboxes):
    """Even-odd over every ring, so holes and many-piece records come out right."""
    c = False
    for r, b in zip(rings, rboxes):
        if y < b[1] or y > b[3] or x > b[2]: continue
        j = len(r) - 1
        for i in range(len(r)):
            xi, yi = r[i]; xj, yj = r[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-300) + xi: c = not c
            j = i
    return c


def acres_of(rings):
    """Area in acres measured on the outline (even-odd: a ring inside an odd number of others is a hole)."""
    if not rings: return 0.0
    lat0 = sum(p[1] for r in rings for p in r) / sum(len(r) for r in rings)
    kx, ky = 111320.0 * math.cos(math.radians(lat0)), 110574.0
    rb = [box_of([r]) for r in rings]
    tot = 0.0
    for k, r in enumerate(rings):
        a = 0.0
        for i in range(len(r)):
            x1, y1 = r[i - 1]; x2, y2 = r[i]
            a += (x1 * kx) * (y2 * ky) - (x2 * kx) * (y1 * ky)
        a = abs(a) / 2.0
        if len(rings) > 1 and len(rings) <= 200:
            x, y = r[0]
            depth = sum(1 for j, o in enumerate(rings) if j != k and boxes_overlap(rb[j], [x, y, x, y]) and _inside(x, y, [o], [rb[j]]))
            tot += -a if depth % 2 else a
        else:
            tot += a
    return abs(tot) / 4046.8564224


def shares(ra, rb, acres_a=None, acres_b=None):
    """(share of a on b's ground, share of b on a's ground), measured on a grid over the smaller record; None when it
    cannot be told (no outline, or too few grid points fall inside the smaller record)."""
    if not ra or not rb: return None
    aa = acres_a if acres_a else acres_of(ra)
    ab = acres_b if acres_b else acres_of(rb)
    if aa <= 0 or ab <= 0: return None
    small, big, a_small = (ra, rb, True) if aa <= ab else (rb, ra, False)
    sb_, bb_ = [box_of([r]) for r in small], [box_of([r]) for r in big]
    bx = box_of(small)
    if not boxes_overlap(bx, box_of(big)):
        return (0.0, 0.0)
    def _count(n):
        ins = both = 0
        dx, dy = (bx[2] - bx[0]) / n, (bx[3] - bx[1]) / n
        for i in range(n):
            x = bx[0] + (i + 0.5) * dx
            for j in range(n):
                y = bx[1] + (j + 0.5) * dy
                if _inside(x, y, small, sb_):
                    ins += 1
                    if _inside(x, y, big, bb_): both += 1
        return ins, both
    ins, both = _count(GRID)
    if ins < MIN_HITS or any(abs(both / ins - t) < NEAR_EDGE for t in (OVERLAP_SMALL, PIECE_IN, DIFFERENT_GROUND) if ins):
        ins, both = _count(GRID_FINE)
    if ins < MIN_HITS: return None
    s_small = both / ins
    s_big = s_small * min(aa, ab) / max(aa, ab)
    return (s_small, s_big) if a_small else (s_big, s_small)


def _near_edge(x, y, rings, d):
    """True when (x, y) lies within d degrees of an edge of the rings."""
    d2 = d * d
    for r in rings:
        for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
            if min(x1, x2) - d > x or max(x1, x2) + d < x or min(y1, y2) - d > y or max(y1, y2) + d < y: continue
            dx, dy = x2 - x1, y2 - y1
            t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
            if (x1 + t * dx - x) ** 2 + (y1 + t * dy - y) ** 2 <= d2: return True
    return False


def ground_share(va, vb, n=GRID_FINE):
    """R2: the share of a's grid points (inside a's outline) on b's ground or within EDGE of b's edge; None when it cannot be
    told (no outline, fewer than MIN_HITS points inside a)."""
    ra, rb = va.get('rings'), vb.get('rings')
    if not ra or not rb: return None
    bx = box_of(ra); bb = box_of(rb)
    if not boxes_overlap(bx, bb, EDGE): return 0.0
    sa_, sb_ = [box_of([r]) for r in ra], [box_of([r]) for r in rb]
    ins = on = 0
    dx, dy = (bx[2] - bx[0]) / n, (bx[3] - bx[1]) / n
    for i in range(n):
        x = bx[0] + (i + 0.5) * dx
        for j in range(n):
            y = bx[1] + (j + 0.5) * dy
            if not _inside(x, y, ra, sa_): continue
            ins += 1
            if boxes_overlap([x, y, x, y], bb, EDGE) and (_inside(x, y, rb, sb_) or _near_edge(x, y, rb, EDGE)): on += 1
    if ins < MIN_HITS: return None
    return on / ins


def point_shares(va, vb):
    """R2: (share of a on b's ground, share of b on a's ground) from a's grid points; the second by the sizes (stated acres
    first: a rough outline's measured area is off). None when it cannot be told."""
    s_a = ground_share(va, vb)
    if s_a is None: return None
    za, zb = (va['acres'] or va['measured']), (vb['acres'] or vb['measured'])
    if za <= 0 or zb <= 0: return None
    return (s_a, min(1.0, s_a * za / zb))


# ---- one record -----------------------------------------------------------------------------------------------------------

COARSE_OFF = 0.20       # an outline whose measured area is more than 20% off its own acres is too rough to measure shared ground
COARSE_SMALL = 20.0     # a record under 20 acres drawn with 5 points or fewer is too rough as well


def view(rec, id_fields=()):
    """The parts of a record the proof reads. rec: a key record ({'Unit_Nm', 'Loc_Nm', 'GIS_Acres', '_g', 'SA'}) or a store
    entry from kpc_store_attrs ({'_nm', '_ac', '_g', field: value}). id_fields: id_spec(layer), or a plain list of unit-id
    fields."""
    rec = rec or {}
    names = {str(x) for x in (rec.get('Unit_Nm'), rec.get('Loc_Nm'), rec.get('_nm')) if x and str(x).strip()}
    for n in rec.get('_nms') or []:
        if n: names.add(str(n))
    rings = rings_of(rec.get('_g'))
    try: ac = float(rec.get('GIS_Acres') or rec.get('_ac') or 0)
    except (TypeError, ValueError): ac = 0.0
    flds = dict(rec.get('SA') or {}); flds.update({k: v for k, v in rec.items() if not str(k).startswith('_') and k != 'SA'})
    low = {str(k).lower(): v for k, v in flds.items()}
    spec = id_fields if isinstance(id_fields, dict) else {str(x).lower(): ('unit', []) for x in id_fields}
    ids, arecs = {}, {}
    for f, (kind, pats) in spec.items():
        if kind == 'arec':
            v = norm_id(low.get(f))
            if v: arecs[f] = v
            continue
        v = _web_id(low.get(f), pats) if kind == 'web' else norm_id(low.get(f)) if kind == 'unit' else ''
        if v: ids[f] = v
    measured = acres_of(rings) if rings else 0.0
    npts = sum(len(r) for r in rings)
    coarse = bool(rings) and ((ac > 0 and measured > 0 and abs(measured - ac) > COARSE_OFF * ac) or (measured < COARSE_SMALL and npts <= 5))
    return {'names': {name_key(n) for n in names if not generic(n)}, 'rings': rings, 'box': box_of(rings) or rec.get('_bx') or rec.get('_bb'),
            'acres': ac, 'measured': measured, 'coarse': coarse, 'ids': ids, 'arecs': arecs}


def prove(a, b, id_fields=()):
    """(level, note) for records a and b of two reads of ONE layer: level in LEVELS, or None (not proven). note says why."""
    va, vb = (a if 'names' in a and 'ids' in a else view(a, id_fields)), (b if 'names' in b and 'ids' in b else view(b, id_fields))
    near = boxes_overlap(va['box'], vb['box'], 0.001)
    same_f = [f for f in va['ids'] if f in vb['ids']]
    if same_f:
        if any(va['ids'][f] != vb['ids'][f] for f in same_f):
            return None, 'different agency id (' + ', '.join(f"{f} {va['ids'][f]} / {vb['ids'][f]}" for f in same_f if va['ids'][f] != vb['ids'][f]) + ')'
        if near:
            note = ''
            sa, sb = va['acres'] or va['measured'], vb['acres'] or vb['measured']
            if sa and sb and max(sa, sb) / min(sa, sb) > SIZE_JUMP: note = 'same id, size changed'
            return 'id', note or f"{same_f[0]} {va['ids'][same_f[0]]}"
    if not near: return None, 'different place'
    # R1: the same agency RECORD id, the place agreeing, and a real name in common or the size within 10% (never the id alone)
    ra, rb = va.get('arecs') or {}, vb.get('arecs') or {}
    same_r = [f for f in ra if f in rb and ra[f] == rb[f]]
    if same_r:
        sa, sb = (va['acres'] or va['measured']), (vb['acres'] or vb['measured'])
        if (va['names'] & vb['names']) or (sa > 0 and sb > 0 and abs(sa - sb) <= SIZE_TOL * max(sa, sb) + 0.5):
            return 'id', f"agency record id {same_r[0]} {ra[same_r[0]]}"
    rough = va['coarse'] or vb['coarse']
    # grade 25 Nov (M4): an outline too rough for its size (the key's 0.001-degree saved copy) cannot say 'different ground'
    sh = None if rough else shares(va['rings'], vb['rings'], va['measured'] or None, vb['measured'] or None)
    if sh is None and rough:   # R2: the old record's grid points against the fresh outline, edge allowance EDGE
        sh = point_shares(va, vb)
        if sh is not None:
            small, big = (max(sh), min(sh))
            if small >= OVERLAP_SMALL and big >= OVERLAP_LARGE: return 'overlap', f'{round(small * 100)}% / {round(big * 100)}% shared (rough outline, grid points)'
            if small >= PIECE_IN and va['names'] & vb['names']:
                return 'piece', f'{round(small * 100)}% of the smaller record inside the larger (rough outline, grid points)'
            sh = None   # a rough outline never says 'different ground': the name + size step below decides
    if sh is not None:
        small, big = (max(sh), min(sh))
        if small >= OVERLAP_SMALL and big >= OVERLAP_LARGE: return 'overlap', f'{round(small * 100)}% / {round(big * 100)}% shared'
        # a piece: the names do not say two different places (both named, no name in common = two designations on one
        # ground, such as a waterfowl production area inside a refuge's outline: never a piece of it)
        # S1 (grade 25 Nov): a piece needs a name in common (a 'Unit 4' or an unnamed parcel never takes a whole unit's id)
        if small >= PIECE_IN and va['names'] & vb['names']:
            return 'piece', f'{round(small * 100)}% of the smaller record inside the larger'
        if small < DIFFERENT_GROUND: return None, f'different ground ({round(small * 100)}% shared)'
    if va['names'] & vb['names']:
        if va['acres'] > 0 and vb['acres'] > 0:
            sa, sb = va['acres'], vb['acres']
        else:
            sa, sb = va['measured'], vb['measured']
        if sa > 0 and sb > 0 and abs(sa - sb) <= SIZE_TOL * max(sa, sb) + 0.5:
            return 'name_size', 'same name, size within 10%'
        return None, 'same name, size differs'
    return None, 'not proven'


_VIEWS = {}


def cached_view(key, rec, id_fields=()):
    """view() of a record that is looked at many times (the store's records), kept by key."""
    k = (key, tuple(id_fields))
    if k not in _VIEWS: _VIEWS[k] = view(rec, id_fields)
    return _VIEWS[k]


_WHY_RANK = ('two fits', 'conflict', 'different agency id', 'same name, size differs', 'different ground', 'not proven', 'different place')


def pick(a, cands, id_fields=(), cache=False, own=None, trace=None):
    """The ONE candidate proven to be the same land as a: (key, level, note), or (None, None, why). cands = {key: record}.
    The strongest level wins; two at that level are one answer only when they carry the same agency ids (pieces of one unit,
    the fields agree), the one with the most shared ground is taken; or two proven records of which one carries a's own
    number (own); else 'two fits' (not proven). why = 'conflict' when a
    record with a DIFFERENT agency id lies on the same ground (half of the smaller one or more) and nothing is proven."""
    va = view(a, id_fields)
    got, conflict, miss = {}, False, []
    if trace is not None: trace.update({'rough': bool(va['coarse']), 'ids': bool(va['ids'] or va['arecs']), 'cands': len(cands)})
    for k, c in cands.items():
        vc = cached_view(k, c, id_fields) if cache else view(c, id_fields)
        lv, note = prove(va, vc, id_fields)
        if lv: got.setdefault(lv, []).append((k, note, vc)); continue
        miss.append((k, note))
        if note.startswith('different agency id') and not conflict and not (va['coarse'] or vc['coarse']):
            sh = shares(va['rings'], vc['rings'], va['measured'] or None, vc['measured'] or None)
            conflict = bool(sh) and max(sh) >= DIFFERENT_GROUND
    for lv in LEVELS:
        hits = got.get(lv) or []
        if not hits: continue
        if len(hits) == 1: return _tr(trace, hits[0][0], lv, hits[0][1])
        if len({tuple(sorted(h[2]['ids'].items())) for h in hits}) == 1 and hits[0][2]['ids']:
            best = max(hits, key=lambda h: (max(shares(va['rings'], h[2]['rings']) or (0, 0)), str(h[0])))
            return _tr(trace, best[0], lv, best[1] + ' (pieces of one unit)')
        # two records proven at the same level (PAD-US often holds one refuge twice, fee and designation): the one that also
        # carries a's own number breaks the tie. The number never proves anything alone; here both are already proven.
        if own is not None and lv in ('id', 'overlap'):   # M2 (grade 25 Nov): never at piece or name + size
            same = [h for h in hits if str(h[0]) == str(own)]
            if len(same) == 1: return _tr(trace, same[0][0], lv, same[0][1] + ' (two fits; the same number breaks the tie)')
        if lv == 'name_size':   # R3: the one record holding at least half of a's ground, every other less; never the number
            gs = [(ground_share(va, h[2]), h) for h in hits]
            win = [h for g_, h in gs if g_ is not None and g_ >= DIFFERENT_GROUND]
            if len(win) == 1 and all(g_ is not None and g_ < DIFFERENT_GROUND for g_, h in gs if h is not win[0]):
                return _tr(trace, win[0][0], lv, win[0][1] + ' (two fits; shared ground breaks the tie)')
        return _tr(trace, None, None, f'two fits ({lv})', hits[0][0])
    why = 'conflict' if conflict else 'not proven'
    best = min(miss, key=lambda m: next((n for n, w in enumerate(_WHY_RANK) if m[1].startswith(w)), len(_WHY_RANK)), default=None)
    return _tr(trace, None, None, why, best[0] if best else None, best[1] if best else '')


def _tr(trace, k, lv, note, best=None, best_note=''):
    """pick's answer, written into trace (R6: the per-row proof list) when one is given."""
    if trace is not None:
        trace.update({'best': k if k is not None else best, 'level': lv,
                      'why': note if lv or not best_note or best_note == note else f'{note}: {best_note}'})
    return k, lv, note


def selftest():
    sq = lambda x, y, d: {'rings': [[[x, y], [x + d, y], [x + d, y + d], [x, y + d], [x, y]]]}
    ok, bad = True, []
    def t(name, cond):
        nonlocal ok
        ok &= bool(cond)
        if not cond: bad.append(name)
    t('generic', generic('Unit 1') and generic('Tract 3B') and generic('Wildlife Management Area') and not generic('Lost Valley Prairie'))
    t('norm ids', norm_id('SNA 01041') == 'SNA1041' == norm_id('sna-01041') == norm_id('SNA1041') and norm_id(1041.0) == '1041' == norm_id('1041.0'))
    ac = acres_of(rings_of(sq(-92.8, 44.8, 0.01)))
    t('acres', 205 < ac < 225)            # 0.01 degree square at 44.8 N: about 789 m x 1,106 m = 216 acres
    old = {'OBJECTID': 'sgmnc55', 'Unit_Nm': 'Lost Valley Prairie', 'GIS_Acres': 216, '_g': sq(-92.83, 44.80, 0.01)}
    new = {'_nm': 'Lost Valley Prairie', '_ac': 216, '_g': sq(-92.8301, 44.8001, 0.01)['rings'], 'pgrm_project': 'SNA01041'}
    other = {'_nm': 'Crystal Spring', '_ac': 40, '_g': sq(-92.70, 44.70, 0.003)['rings'], 'pgrm_project': 'SNA01022'}
    t('overlap', prove(old, new)[0] == 'overlap')
    k, lv, _ = pick(old, {'sgmnc210': new, 'sgmnc55': other}); t('number means nothing', (k, lv) == ('sgmnc210', 'overlap'))
    a = dict(old, SA={'pgrm_project': 'SNA 01041'})
    t('unit id', prove(a, new, ['pgrm_project'])[0] == 'id')
    t('other unit id', prove(a, dict(new, pgrm_project='SNA09999'), ['pgrm_project'])[0] is None)
    t('leading zeros are one id', prove(a, dict(new, pgrm_project='SNA1041'), ['pgrm_project'])[0] == 'id')
    web = {'url': ('web', [r'dec\.ny\.gov/(?:lands|outdoor)/(\d+)\.html'])}
    w1, w2 = dict(old, SA={'URL': 'http://www.dec.ny.gov/lands/8139.html'}), dict(new, URL='https://dec.ny.gov/lands/8139.html')
    t('http / https: one web id', prove(w1, w2, web)[0] == 'id')
    t('a record-id field never refuses', prove(dict(old, SA={'su_id': 1}), dict(new, su_id=2), {'su_id': ('record', [])})[0] == 'overlap')
    whole = {'_nm': 'Big Forest', '_g': sq(-93, 45, 0.1)['rings']}
    t('a named piece', prove({'Unit_Nm': 'Big Forest', '_g': sq(-92.95, 45.05, 0.01)}, whole)[0] == 'piece')
    t('Unit 4 is no piece', prove({'Unit_Nm': 'Unit 4', '_g': sq(-92.95, 45.05, 0.01)}, whole)[0] is None)
    t('unnamed is no piece', prove({'Unit_Nm': '', '_g': sq(-92.95, 45.05, 0.01)}, whole)[0] is None)
    wpa = {'Unit_Nm': 'Otter Tail County Waterfowl Production Area', '_g': sq(-92.95, 45.05, 0.01)}
    t('two designations', prove(wpa, dict(whole, _nm='Northern Tallgrass Prairie National Wildlife Refuge'))[0] is None)
    n1 = {'Unit_Nm': 'Mud Lake WMA', 'GIS_Acres': 100, '_bb': [-90, 40, -89.99, 40.01]}
    n2 = {'_nm': 'Mud Lake WMA', '_ac': 105, '_bx': [-90, 40, -89.99, 40.01]}
    t('name and size', prove(n1, n2)[0] == 'name_size')
    t('size off', prove(n1, dict(n2, _ac=150))[0] is None)
    t('generic name', prove(dict(n1, Unit_Nm='Unit 2'), dict(n2, _nm='Unit 2'))[0] is None)
    t('name + size tie is never broken by the number', pick(n1, {'sgxx20': n2, 'sgxx31': dict(n2, _ac=102)}, own='sgxx31')[0] is None)
    g1 = {'Unit_Nm': 'Mud Lake WMA', 'GIS_Acres': 216, '_g': sq(-90, 40, 0.01)}
    g2 = {'_nm': 'Mud Lake WMA', '_ac': 216, '_g': sq(-89.993, 40.0, 0.01)['rings']}
    t('different ground', prove(g1, g2)[0] is None)
    t('a coarse outline is cannot-tell, then name + size', prove(dict(g1, GIS_Acres=400), dict(g2, _ac=410))[0] == 'name_size')
    p1 = {'_nm': 'X', '_g': sq(-92.83, 44.80, 0.01)['rings'], 'sft': 'SFT1'}
    p2 = {'_nm': 'X', '_g': sq(-92.8302, 44.8002, 0.01)['rings'], 'sft': 'SFT2'}
    t('two fits', pick(old, {'a': p1, 'b': p2}, ['sft'])[0] is None)
    t('pieces of one unit', pick(old, {'a': p1, 'b': dict(p2, sft='SFT1')}, ['sft'])[0] in ('a', 'b'))
    q1, q2 = {'_nm': 'Agassiz NWR', '_g': sq(-92.83, 44.80, 0.01)['rings']}, {'_nm': 'Agassiz NWR', '_g': sq(-92.83, 44.80, 0.01)['rings']}
    t('overlap tie by the number', pick(old, {'3569': q1, '9999': q2})[0] is None and pick(old, {'3569': q1, '9999': q2}, own='3569')[0] == '3569')
    print('selftest', 'ALL PASS' if ok else 'FAIL ' + ', '.join(bad))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(selftest() if '--selftest' in sys.argv else 0)
