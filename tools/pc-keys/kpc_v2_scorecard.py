#!/usr/bin/env python3
"""KPC v2 scorecard (26 Nov 2026). Decides, with a pass / fail exit code, whether a v2 US key (kpc_us_key_v2.py) is good enough.
Rule sheet: .claude/notes/rule-sheet-us-key-v2-nov26.md (sections 5, 7, 8, 17).
27 Nov 2026 (section 17, the owner: "why judge against crap work.. I need a system that works end to end and gives me excellent
results"): pass / fail is judged on v2 BY ITSELF. Nothing about the old key (v1) is a gate. The v1 numbers, when a v1 key is
given, are printed at the end, for information only. Pin inside the land and size agrees are v2's own quality numbers, with no limit.

  py -3 kpc_v2_scorecard.py --v2 <v2 folder> [--base <v1 keys folder>] --store <layer files folder> --facts <park-facts.json.gz>
                            --states MN NY SC [--v1-seconds MN=252 NY=180] [--out <folder>] [--repo <KPC-Links root>]
                            [--cold <cold run folder>] [--lock-check same|differs|skipped]
  (no --base, or --no-base: no v1 key; the for-information block is left out)

Writes V2-SCORECARD.txt (counts only, no park names) and v2-vs-base.csv (park by park, the names are there) into --out
(default: the v2 folder). Exit 0 = every gate passes, 1 = at least one fails. Reads files only; stdlib only; no network.

Words used here:
  outlined  = the park has joined records ("with an outline" in the PC test: 310 of 323 in Minnesota).
  confirmed = the key's own match status 'confirmed'.
  pin inside = the park's pin is inside one of its joined records (a pin within 100 m of the edge counts as on the land).
  size agrees = the joined acres are within 10% of an official size in the park facts (the agency size, or a page size marked
                total). Parks with no official size are left out of that count.
"""
import argparse, csv, datetime, gzip, json, math, os, pathlib, re, shutil, sys, time
from itertools import accumulate

LINE_PIN_M = 30.48   # a pin this close to a line (a trail) counts as on it (the table's line_pin_m)
NEAR_M = 100.0       # a pin this close to a record's edge counts as on the land
SIZE_TOL = 0.10      # joined acres within 10% of the official size
ACRE_DIFF = 0.10     # the park-by-park list shows parks whose joined acres differ by more than this
HONEST_SLACK = 1.0   # not used since 27 Nov 2026 (H1 / H2 are v2's own numbers, no limit: rule sheet 17); kept for old readers
TWO_STATES_SECONDS = 300.0   # 27 Nov 2026: shown as a target line, not a gate (it went with G8)
LAND_CELLS = 40000   # H3 (same land as v1): about this many grid points over a park's box (coarse on purpose)
LAND_MIN_CELL_M = 20.0
LAND_SHARE = 0.90    # H3 counts a park when one side covers at least this share of the other's land
M2_ACRE = 4046.86


def load_json(p):
    try:
        p = pathlib.Path(p)
        if p.suffix == '.gz':
            with gzip.open(p, 'rt', encoding='utf-8') as f: return json.load(f)
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError, EOFError): return None


def aname(st):
    """'MN' -> 'US-MN'; 'CA-ON' stays (an area is what the layer files and the keys are named by)."""
    st = str(st).strip().upper()
    return st if re.match(r'^[A-Z]{2}-[A-Z]{2}$', st) else 'US-' + st


def key_file(folder, st):
    for n in (f'{aname(st)}.json.gz', f'{aname(st)}.json'):
        if (pathlib.Path(folder) / n).is_file(): return pathlib.Path(folder) / n
    return None


def read_csv(p):
    try:
        with open(p, encoding='utf-8', newline='') as f: return list(csv.DictReader(f))
    except OSError: return None


# ---------------------------------------------------------------- shapes

def decode_rings(r):
    """A layer record's rings in degrees. Same reading as kpc_store_attrs.record_rings: integer rings, the first point and then
    steps, 10**q to the degree (q default 6). [] when there is no shape."""
    rg = r.get('rings')
    if isinstance(rg, str):
        try: rg = json.loads(rg)
        except ValueError: return []
    try: q = 10 ** int(r.get('q') or 6)
    except (TypeError, ValueError): q = 10 ** 6
    out = []
    for ring in rg or []:
        if not isinstance(ring, list) or len(ring) < 2: continue
        xs = [v / q for v in accumulate(ring[0::2])]
        ys = [v / q for v in accumulate(ring[1::2])]
        n = min(len(xs), len(ys))
        if n >= 3: out.append(list(zip(xs[:n], ys[:n])))
    return out


def _inside(x, y, rings):
    """Even-odd: a point is in the record when it is inside an odd number of its rings (holes work)."""
    c = False
    for ring in rings:
        px, py = ring[-1]
        for qx, qy in ring:
            if (qy > y) != (py > y) and x < (px - qx) * (y - qy) / (py - qy) + qx: c = not c
            px, py = qx, qy
    return c


def _edge_m(x, y, rings):
    """Metres from the point to the nearest edge (flat approximation; fine at 100 m)."""
    import math
    kx, ky = 111320.0 * math.cos(math.radians(y)), 110540.0
    best = 1e18
    for ring in rings:
        px, py = ring[-1]
        for qx, qy in ring:
            ax, ay, bx, by = (px - x) * kx, (py - y) * ky, (qx - x) * kx, (qy - y) * ky
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            t = 0.0 if L == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L))
            d = math.hypot(ax + t * dx, ay + t * dy)
            if d < best: best = d
            px, py = qx, qy
    return best


def decode_paths(r):
    """A line record's paths in degrees (the same delta reading as rings; two points make a path). [] when there are none."""
    pr = dict(r); pr['rings'] = r.get('paths')
    out = []
    rg = pr['rings']
    if isinstance(rg, str):
        try: rg = json.loads(rg)
        except ValueError: return []
    try: q = 10 ** int(r.get('q') or 6)
    except (TypeError, ValueError): q = 10 ** 6
    for path in rg or []:
        if not isinstance(path, list) or len(path) < 4: continue
        xs = [v / q for v in accumulate(path[0::2])]; ys = [v / q for v in accumulate(path[1::2])]
        n = min(len(xs), len(ys))
        if n >= 2: out.append(list(zip(xs[:n], ys[:n])))
    return out


def line_m(lon, lat, paths):
    """Metres from the pin to the nearest segment of a line (open paths)."""
    kx, ky, best = 111320.0 * math.cos(math.radians(lat)), 110574.0, 1e18
    for pa in paths:
        for (x1, y1), (x2, y2) in zip(pa, pa[1:]):
            ax, ay, bx, by = (x1 - lon) * kx, (y1 - lat) * ky, (x2 - lon) * kx, (y2 - lat) * ky
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            t = 0.0 if L == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L))
            best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def is_line(rec):
    """A record with paths and no rings is a line (a trail), not a record without a shape."""
    return bool(isinstance(rec, dict) and rec.get('paths') and not rec.get('rings'))


def pin_on_land(lat, lon, geoms, near_m=NEAR_M):
    """True when the pin is inside one of the shapes (geoms = [(box, rings)]) or within near_m of its edge. A coarse box test first."""
    mlat = near_m / 110540.0 * 1.5
    mlon = mlat * 1.6                       # generous: a degree of longitude is shorter than a degree of latitude
    for box, rings in geoms:
        if box[0] <= lon <= box[2] and box[1] <= lat <= box[3] and _inside(lon, lat, rings): return True
    for box, rings in geoms:
        if box[0] - mlon <= lon <= box[2] + mlon and box[1] - mlat <= lat <= box[3] + mlat and _edge_m(lon, lat, rings) <= near_m: return True
    return False


# ---------------------------------------------------------------- the layer files

def load_table(repo):
    """The rule table (.github/us-key-v2-rules.json) from the repo, or links\\ on the PC; None when it is not there."""
    repo = pathlib.Path(repo)
    here = pathlib.Path(__file__).resolve().parent
    for f in (here / 'us-key-v2-rules.json', repo / '.github' / 'us-key-v2-rules.json', repo / 'links' / '.github' / 'us-key-v2-rules.json'):
        d = load_json(f)   # beside this file on the PC (the kit folder), else in the repo copy
        if isinstance(d, dict): return d
    return None


def load_line_pin(repo):
    """values.line_pin_m of the rule table (30.48 m, 100 ft, when it is missing)."""
    v = ((load_table(repo) or {}).get('values') or {}).get('line_pin_m')
    v = v.get('value') if isinstance(v, dict) else v
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 else LINE_PIN_M


def load_limits(repo):
    """The pin allowance (values.pin_m) and the size tolerance (values.size_tol) from the rule table; each value may be a plain
    number or a dict with 'value' (and why / test). Returns ({'pin_m', 'size_tol'}, note); the note says 'defaults used' when the
    table or a value is missing (then 100 m and 10%)."""
    d, out, miss = load_table(repo), {'pin_m': NEAR_M, 'size_tol': SIZE_TOL}, []
    vals = (d or {}).get('values') or {}
    for k in ('pin_m', 'size_tol'):
        v = vals.get(k)
        v = v.get('value') if isinstance(v, dict) else v
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0: out[k] = float(v)
        else: miss.append(k)
    note = ''
    if d is None: note = 'the rule table (us-key-v2-rules.json) was not found: pin allowance 100 m and size tolerance 10% (defaults used)'
    elif miss: note = f"the rule table has no value for {' and '.join(miss)}: the defaults are used (100 m, 10%) (defaults used)"
    return out, note


def load_id_fields(repo):
    """The agency id field of each layer, from .github/us-key-v2-rules.json -> tables -> record_id_fields (the repo, or links\\ on the PC).
    Returns ({layer: field}, note). No table = {} and one plain line: v1 ids are then looked up by the file's own key only."""
    d = load_table(repo)
    if isinstance(d, dict):
        v = (((d.get('tables') or {}).get('record_id_fields') or {}).get('value'))
        if isinstance(v, dict) and v: return {str(k): str(f) for k, f in v.items()}, ''
    return {}, "the rule table with the agency id fields (us-key-v2-rules.json, record_id_fields) was not found: v1 ids are looked up by the file's own key only"


def agency_digits(rec, fld):
    """(digits, letters) of a record's agency id in field fld, any letter case of the field name: 89125.0 -> ('89125', ''),
    'WMA0038200' -> ('38200', 'WMA'), 'SFT00006' -> ('6', 'SFT'); ('', '') when there is none. (Copied from kpc_store_attrs._agency_num.)"""
    a = rec.get('attributes') or {}
    v = next((a[k] for k in a if str(k).lower() == fld.lower() and a[k] not in (None, '')), None)
    if isinstance(v, bool) or v is None: return '', ''
    if isinstance(v, (int, float)):
        x = float(v)
        return (str(int(x)), '') if x > 0 and x.is_integer() else ('', '')
    m = re.fullmatch(r'([A-Za-z]*)0*(\d+)', str(v).strip())
    return (m.group(2), m.group(1).upper()) if m and int(m.group(2)) > 0 else ('', '')


AMBIGUOUS = object()   # a v1 id that fits more than one record and the name does not choose


class Store:
    """The layer files of --store, read once each. A record is found by the file's own key (v2), or, for a v1 id of any date, by
    one of three spellings (own file does not depend on any legacy module): (a) the file's key (layer letters + row number; PAD-US
    the bare number); (b) layer letters + the agency number with no zero ('sgmne89125'); (c) layer letters + '0' + the agency number
    ('sgmne089125'). The agency number is the digits of the layer's agency id field (id_fields)."""

    def __init__(self, folder, id_fields=None, pin_m=NEAR_M, size_tol=SIZE_TOL):
        self.pin_m, self.size_tol, self.line_m = pin_m, size_tol, LINE_PIN_M
        self.lines = {}
        self.folder, self.id_fields, self.files, self.geo = pathlib.Path(folder), dict(id_fields or {}), {}, {}

    def file(self, stem):
        if stem not in self.files:
            d = load_json(self.folder / f'{stem}.layer-records.json.gz') if self.folder.is_dir() else None
            recs = d.get('records') if isinstance(d, dict) else None
            if not isinstance(recs, list): self.files[stem] = None
            else:
                bykey, agency = {}, {}
                for i, r in enumerate(recs):
                    k = str(r.get('key') or '').replace('@', '')
                    if k: bykey.setdefault(k, []).append(i)
                    lay = str(r.get('layer') or '')
                    if lay in self.id_fields and lay != 'PAD-US':
                        n, lt = agency_digits(r, self.id_fields[lay])
                        if n: agency.setdefault(lay, []).append((i, n, lt))
                # the way v1 spelled a layer: by the agency id only when every record of the layer carries the same letters,
                # and a spelling that two records share is not used (v1 fell back to the row spelling for them)
                byb, byc = {}, {}
                for lay, rows in agency.items():
                    if len({lt for _, _, lt in rows}) != 1: continue
                    cnt = {}
                    for i, n, _ in rows: cnt.setdefault(n, []).append(i)
                    for n, idx in cnt.items():
                        if len(idx) == 1: byb[lay + n] = idx[0]; byc[lay + '0' + n] = idx[0]
                self.files[stem] = {'recs': recs, 'bykey': bykey, 'byb': byb, 'byc': byc}
        return self.files[stem]

    def has_key(self, key, stems):
        k = str(key or '').replace('@', '')
        return bool(k) and any((f := self.file(s)) and k in f['bykey'] for s in stems)

    def find(self, key, stems, name=None, v1=False):
        """The record for a file key (v2) or a v1 id (v1; all three spellings), searched in the files in order (the first file with
        a candidate decides). Several candidates: the one whose record name equals the v1 name (letters and digits, any case);
        none or several by name = AMBIGUOUS, never a guess. None = not in the files."""
        k = str(key if key is not None else '').replace('@', '')
        for s in stems:
            f = self.file(s)
            if not f: continue
            idx = list(f['bykey'].get(k) or [])
            if v1:
                for src in ('byb', 'byc'):
                    i = f[src].get(k)
                    if i is not None and i not in idx: idx.append(i)
            if not idx: continue
            if len(idx) == 1: return f['recs'][idx[0]]
            nk = _nk(name)
            by_name = [i for i in idx if nk and _nk(f['recs'][i].get('record_name')) == nk]
            return f['recs'][by_name[0]] if len(by_name) == 1 else AMBIGUOUS
        return None

    def line(self, rec):
        """A line record's paths, or None."""
        if not is_line(rec): return None
        k = id(rec)
        if k not in self.lines: self.lines[k] = decode_paths(rec)
        return self.lines[k] or None

    def shape(self, rec):
        g = self.geo.get(id(rec))
        if g is None:
            rings = decode_rings(rec)
            if rings:
                xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
                g = ((min(xs), min(ys), max(xs), max(ys)), rings)
            else: g = ()
            self.geo[id(rec)] = g
        return g or None


def _nk(t): return re.sub(r'[^a-z0-9]', '', str(t or '').lower())


# ---------------------------------------------------------------- park facts, numbers

def joined(p): return bool(isinstance(p, dict) and p.get('m'))


def confirmed(p): return bool(isinstance(p, dict) and (p.get('match') or {}).get('status') == 'confirmed')


def num(x):
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def joined_acres(p):
    a = num(p.get('ac'))
    if a is not None: return a
    s = [num(r[2]) for r in p.get('m') or [] if isinstance(r, (list, tuple)) and len(r) > 2 and num(r[2]) is not None]
    return float(sum(s)) if s else None


def licence_counts(parks):
    """27 Nov 2026 (licence counts): how many outlined parks say share all / part / none (the key's own `share` word). A park with
    no word, or a word that is none of the three, counts as none (fail closed) and is also counted as `unmarked`."""
    out = {'all': 0, 'part': 0, 'none': 0, 'unmarked': 0}
    for p in parks.values():
        if not joined(p): continue
        w = (p or {}).get('share')
        if w in ('all', 'part'): out[w] += 1
        else:
            out['none'] += 1
            if w != 'none': out['unmarked'] += 1
    return out


def licence_text(c, outlined=None):
    """The counts in plain words, one line. `c` is licence_counts() or the sum of several."""
    n = c['all'] + c['part'] + c['none']
    t = f"Licence, what the club may show: share all {c['all']}, share part {c['part']}, share none {c['none']} (of {n if outlined is None else outlined} outlined parks)"
    if c.get('unmarked'): t += f"; {c['unmarked']} had no licence word and count as none"
    return t + '.'


def licence_sum(items):
    tot = {'all': 0, 'part': 0, 'none': 0, 'unmarked': 0}
    for c in items:
        for k in tot: tot[k] += int((c or {}).get(k) or 0)
    return tot


def official_sizes(fp):
    """The official sizes the park facts hold for a park: the agency's size (when its witness counts) and every page size marked total."""
    out = []
    sz = (fp or {}).get('size') or {}
    if isinstance(sz, dict) and num(sz.get('acres')) and sz.get('witness_counts') is not False: out.append(float(sz['acres']))
    for s in ((fp or {}).get('page') or {}).get('sizes') or []:
        if isinstance(s, dict) and s.get('total') and num(s.get('acres')): out.append(float(s['acres']))
    return out


def size_agrees(acres, sizes, tol=SIZE_TOL):
    return bool(acres and any(abs(acres - o) <= tol * o for o in sizes if o > 0))


def pin_of(fp):
    pin = (fp or {}).get('pin')
    if isinstance(pin, (list, tuple)) and len(pin) == 2 and all(num(v) is not None for v in pin): return float(pin[0]), float(pin[1])
    return None


def two_name_count(parks):
    """The PC test's wrong-land definition (kpc_test_keys.wrong_land_lines): one record id on two parks under two different
    names = 'two'; one id on two parks under the same name = 'same' (allowed). Names are compared as letters and digits only."""
    by_id = {}
    for ref, row in sorted((parks or {}).items()):
        if not isinstance(row, dict): continue
        for x in row.get('m') or []:
            if not isinstance(x, (list, tuple)) or len(x) < 2 or not _nk(x[1]): continue
            by_id.setdefault(str(x[0]), {}).setdefault(_nk(x[1]), []).append(ref)
    two = sum(1 for names in by_id.values() if len(names) > 1)
    same = sum(1 for names in by_id.values() if len(names) == 1 and len({r for v in names.values() for r in v}) > 1)
    return two, same


def old_ids(parks):
    n = 0
    for row in (parks or {}).values():
        for k in ('m', 'c'):
            for x in (row or {}).get(k) or []:
                if isinstance(x, (list, tuple)) and x and str(x[0]).endswith('~old'): n += 1
    return n


# ---------------------------------------------------------------- one side (v1 or v2) of one state

def records_of(side, ref, p, store, stems, proof):
    """The layer records a park is joined to. v1: its ids, spelled the v1 way. v2: the file keys in v2-proof.csv (its own m ids
    when there is no proof row). Returns (records, ids_seen, ids_missing, missing_trail_lines)."""
    recs, seen, miss, trl, fit2 = [], 0, 0, 0, 0
    if side == 'v2' and proof is not None:
        rows = [(r.get('file_key'), r.get('record_name')) for r in proof.get(ref, [])]
        v1 = False
    else:
        rows = [(x[0], x[1] if len(x) > 1 else None) for x in p.get('m') or [] if isinstance(x, (list, tuple)) and x]
        v1 = side == 'v1'
    for k, nm in rows:
        seen += 1
        r = store.find(k, stems, nm, v1=v1)
        if r is AMBIGUOUS: fit2 += 1          # fits two records and the name does not choose: left out, never guessed
        elif r is None:
            miss += 1; trl += str(k).startswith('trl')
        else: recs.append(r)
    return recs, seen, miss, trl, fit2


def honest(side, parks, proof, facts, store, stems):
    """The two honest numbers for every outlined park, plus how many ids were not found. Returns (numbers, pin per park)."""
    n = dict(outlined=0, pin_n=0, pin_yes=0, pin_cant=0, size_n=0, size_yes=0, ids=0, ids_missing=0, ids_trail=0, ids_fit2=0, found={})
    pins = {}
    for ref, p in parks.items():
        if not joined(p): continue
        n['outlined'] += 1
        fp = (facts.get('parks') or {}).get(ref) or {}
        recs, seen, miss, trl, fit2 = records_of(side, ref, p, store, stems, proof)
        n['ids'] += seen; n['ids_missing'] += miss; n['ids_trail'] += trl; n['ids_fit2'] += fit2
        n['found'][ref] = (seen - fit2, len(recs))   # how many of its joined ids are in today's files
        geoms = [g for g in (store.shape(r) for r in recs) if g]
        lines = [x for x in (store.line(r) for r in recs) if x]
        pin = pin_of(fp)
        if (not geoms and not lines) or not pin:
            n['pin_cant'] += 1; pins[ref] = '-'
        else:
            n['pin_n'] += 1
            ok = bool(geoms) and pin_on_land(pin[0], pin[1], geoms, store.pin_m)
            if not ok: ok = any(line_m(pin[1], pin[0], x) <= store.line_m for x in lines)
            n['pin_yes'] += ok; pins[ref] = 'yes' if ok else 'no'
        sizes, ac = official_sizes(fp), joined_acres(p)
        all_lines = bool(recs) and all(is_line(r) for r in recs)       # a park that is only trail lines has no area to measure
        if sizes and ac and not all_lines:
            n['size_n'] += 1; n['size_yes'] += size_agrees(ac, sizes, store.size_tol)
    return n, pins


def pct(a, b): return 100.0 * a / b if b else None


def fmt_pct(a, b):
    v = pct(a, b)
    return 'n/a' if v is None else f'{v:.1f}%'


# ---------------------------------------------------------------- the scorecard

def park_name_share(parks):
    """The owner's meaning of 'two names': one record (one joined id) on two parks whose POTA names differ (letters and digits of the
    whole name, text in brackets INCLUDED: 'Pine Hill State Forest (Delaware County)' and '... (Cattaraugus County)' are two names).
    Returns (ids on parks with different names, ids on parks with the very same name, rows for the csv)."""
    by_id = {}
    for ref, row in sorted((parks or {}).items()):
        if not isinstance(row, dict): continue
        for x in row.get('m') or []:
            if isinstance(x, (list, tuple)) and x: by_id.setdefault(str(x[0]), {})[ref] = _nk(row.get('n'))
    diff = same = 0
    rows = []
    for i, refs in sorted(by_id.items()):
        if len(refs) < 2: continue
        if len(set(refs.values())) > 1:
            diff += 1; rows.append({'record_id': i, 'parks': ' '.join(sorted(refs))})
        else: same += 1
    return diff, same, rows


def bare_name(n):
    """A park name without the text in brackets, letters and digits only."""
    return _nk(re.sub(r'\([^)]*\)', ' ', str(n or '')))


def same_name_land(side, st, parks, proof, facts, store, stems):
    """G11 detector: a park proven by a name rule (match.by is not 'id') whose joined record holds the pin (inside, or within the pin
    allowance) of ANOTHER park of the same state list that has the same bare name (brackets taken out). Returns csv rows."""
    groups = {}
    for ref, p in parks.items():
        b = bare_name((p or {}).get('n'))
        if b: groups.setdefault(b, []).append(ref)
    out = []
    for refs in groups.values():
        if len(refs) < 2: continue
        for ref in sorted(refs):
            p = parks[ref]
            if not joined(p) or (p.get('match') or {}).get('by') == 'id': continue
            others = [(q, pin_of((facts.get('parks') or {}).get(q))) for q in sorted(refs) if q != ref]
            others = [(q, pn) for q, pn in others if pn]
            if not others: continue
            recs = records_of(side, ref, p, store, stems, proof)[0]
            for r in recs:
                g = store.shape(r)
                if not g: continue
                for q, pn in others:
                    if pin_on_land(pn[0], pn[1], [g], store.pin_m):
                        out.append({'side': side, 'state': st, 'park': ref, 'other_park': q, 'record_key': r.get('key'), 'record_name': r.get('record_name')})
    return out


def raster(rings, lon0, lat0, s):
    """Grid points (cell centres, s metres apart) that lie inside the shape (even-odd over all rings): a set of ints."""
    kx, ky = 111320.0 * math.cos(math.radians(lat0)), 110574.0
    rows = {}
    for r in rings:
        pts = [((x - lon0) * kx / s, (y - lat0) * ky / s) for x, y in r]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            if y1 == y2: continue
            lo, hi = (y1, y2) if y1 < y2 else (y2, y1)
            for j in range(math.ceil(lo - 0.5), math.ceil(hi - 0.5)):
                rows.setdefault(j, []).append(x1 + (j + 0.5 - y1) * (x2 - x1) / (y2 - y1))
    out = set()
    for j, xs in rows.items():
        xs.sort()
        base = (j + 2 ** 20) << 32
        for a, b in zip(xs[0::2], xs[1::2]):
            for c in range(math.ceil(a - 0.5), math.ceil(b - 0.5)): out.add(base + c + 2 ** 20)
    return out


def land_pair(g1, g2):
    """g1, g2 = lists of (box, rings) (v1's records, v2's records). Returns (acres1, acres2, 1-not-in-2, 2-not-in-1) on one point grid.
    Boxes first: two sides whose boxes do not touch share nothing, and only the part of a side inside the other's box is compared."""
    def box(g): return (min(b[0] for b, _ in g), min(b[1] for b, _ in g), max(b[2] for b, _ in g), max(b[3] for b, _ in g))
    b1, b2 = box(g1), box(g2)
    x0, y0, x1, y1 = min(b1[0], b2[0]), min(b1[1], b2[1]), max(b1[2], b2[2]), max(b1[3], b2[3])
    lat0 = (y0 + y1) / 2
    area = max((x1 - x0) * 111320.0 * math.cos(math.radians(lat0)) * (y1 - y0) * 110574.0, 1.0)
    s = max(LAND_MIN_CELL_M, math.sqrt(area / LAND_CELLS))
    r1 = set().union(*[raster(rg, x0, y0, s) for _, rg in g1])
    if g1 is g2 or [id(r) for r in g1] == [id(r) for r in g2]: r2 = r1
    else: r2 = set().union(*[raster(rg, x0, y0, s) for _, rg in g2])
    ca = s * s / M2_ACRE
    if b1[2] < b2[0] or b2[2] < b1[0] or b1[3] < b2[1] or b2[3] < b1[1]: both = 0
    else: both = len(r1 & r2)
    return len(r1) * ca, len(r2) * ca, (len(r1) - both) * ca, (len(r2) - both) * ca


def land_vs_base(st, bp, vp, proof, store, stems):
    """H3, a report and never a gate: over parks outlined by both v1 and v2, how much of v1's land v2 covers, and the other way round.
    Returns (rows, n_both, n_v2_has_v1, n_v1_has_v2)."""
    rows, nb, n21, n12 = [], 0, 0, 0
    for ref in sorted(set(bp) & set(vp)):
        p1, p2 = bp[ref], vp[ref]
        if not (joined(p1) and joined(p2)): continue
        g = []
        for side, p, pr in (('v1', p1, None), ('v2', p2, proof)):
            recs = records_of(side, ref, p, store, stems, pr)[0]
            g.append([sh for sh in (store.shape(r) for r in recs) if sh])
        if not g[0] or not g[1]: continue
        a1, a2, m1, m2 = land_pair(g[0], g[1])
        if a1 <= 0 or a2 <= 0: continue
        nb += 1
        n21 += (a1 - m1) >= LAND_SHARE * a1
        n12 += (a2 - m2) >= LAND_SHARE * a2
        rows.append({'ref': ref, 'state': st, 'name': p2.get('n') or p1.get('n') or '', 'v1 land acres': round(a1, 1), 'v2 land acres': round(a2, 1),
                     'v1 land not in v2': round(m1, 1), 'v2 land not in v1': round(m2, 1)})
    rows.sort(key=lambda r: -max(r['v1 land not in v2'], r['v2 land not in v1']))
    return rows, nb, n21, n12


def build(v2dir, basedir, storedir, factsfile, states, v1_seconds=None, repo=None, lock_check='skipped', lock_differs=(), lock_text='', trial=False, land=True, nobase=False):
    """Returns (gates, state_blocks, csv_rows, notes). gates = [(id, ok, text)]."""
    repo = repo or pathlib.Path(__file__).resolve().parents[2]
    id_fields, note = load_id_fields(repo)
    lim, lnote = load_limits(repo)
    store = Store(storedir, id_fields, lim['pin_m'], lim['size_tol'])
    store.line_m = load_line_pin(repo)
    facts = load_json(factsfile) or {}
    notes = [x for x in (note, lnote) if x]
    if not facts.get('parks'): notes.append('park facts not read: the pin and size numbers are empty')
    runj = load_json(pathlib.Path(v2dir) / 'v2-run.json') or {}
    run, areas_run = runj.get('states') or {}, runj.get('areas') or {}
    proof_all = read_csv(pathlib.Path(v2dir) / 'v2-proof.csv')
    pinonly_all = read_csv(pathlib.Path(v2dir) / 'v2-pin-only.csv')
    v1_seconds = v1_seconds or {}
    other_names = read_csv(pathlib.Path(v2dir) / 'v2-id-other-names.csv')
    S, rows = {}, []
    for st in states:
        d = {'st': st}
        kb, k2 = (None if nobase else key_file(basedir, st)), key_file(v2dir, st)
        b, v = ({'parks': {}} if nobase else load_json(kb) if kb else None), load_json(k2) if k2 else None
        d['base_ok'], d['v2_ok'] = isinstance(b, dict), isinstance(v, dict)
        bp = (b or {}).get('parks') or {}; vp = (v or {}).get('parks') or {}
        d['bp'], d['vp'] = bp, vp
        stems = [aname(st)] + [s for s in sorted(((v or {}).get('layer_files') or {})) if s != aname(st)]
        d['stems'] = stems
        d['proof'] = {}
        for r in proof_all or []:
            if r.get('st') == st: d['proof'].setdefault(r.get('ref'), []).append(r)
        d['proof_rows'] = [r for rs in d['proof'].values() for r in rs]
        d['pinonly_rows'] = [r for r in pinonly_all or [] if r.get('st') == st]
        d['nobase'] = nobase
        d['same'] = (True, 0, len(vp), 0, 0) if nobase else (set(bp) == set(vp), len(bp), len(vp), len(set(bp) - set(vp)), len(set(vp) - set(bp)))
        d['out1'], d['out2'] = sum(joined(p) for p in bp.values()), sum(joined(p) for p in vp.values())
        d['conf1'], d['conf2'] = sum(confirmed(p) for p in bp.values()), sum(confirmed(p) for p in vp.values())
        d['pin1'], d['pin2'] = len(bp) - d['out1'], len(vp) - d['out2']
        d['c1'] = sum(len((p or {}).get('c') or []) for p in bp.values())
        d['c2'] = sum(len((p or {}).get('c') or []) for p in vp.values())
        d['old'] = old_ids(vp)
        d['lic'] = licence_counts(vp)
        d['pdiff'], d['psame'], d['pshare'] = park_name_share(vp)
        for r_ in d['pshare']: r_['state'] = st
        d['two'], d['samename'] = two_name_count(vp)
        d['missing'] = sum(1 for r in d['proof_rows'] if not store.has_key(r.get('file_key'), stems))
        d['h1'], pins1 = honest('v1', bp, None, facts, store, stems)
        d['h2'], pins2 = honest('v2', vp, d['proof'] if proof_all is not None else None, facts, store, stems)
        rs = run.get(st) or run.get(aname(st)) or areas_run.get(aname(st)) or {}
        d['run'] = rs
        d['nb'] = rs.get('not_built') or None          # a state v2 did not build: only G9 speaks for it
        d['nb_layer'] = not_built_layer(d['nb']) if d['nb'] else ''
        # store room gap: v1 outlined the park, NONE of v1's joined records is in today's files, and v2 did not outline it another way
        d['gap'] = []
        for ref, p in bp.items():
            seen, got = d['h1']['found'].get(ref, (0, 0))
            if joined(p) and seen and got == 0 and not joined(vp.get(ref)):
                ids = [str(x[0]) for x in p.get('m') or [] if isinstance(x, (list, tuple)) and x]
                lay = sorted({re.match(r'[A-Za-z\-]*', i).group(0) or '(number)' for i in ids})
                d['gap'].append({'ref': ref, 'state': st, 'name': p.get('n') or '', 'v1_record_ids': ' '.join(ids), 'layer_letters': ' '.join(lay),
                                 'trail': all(i.startswith('trl') for i in ids), 'confirmed': confirmed(p)})
        d['out1f'] = d['out1'] - len(d['gap'])
        d['conf1f'] = d['conf1'] - sum(g['confirmed'] for g in d['gap'])
        gaprefs = {g['ref'] for g in d['gap']}
        d['why2'] = {}
        d['step2'] = {}
        for p_ in vp.values():
            m_ = (p_ or {}).get('match') or {}
            if joined(p_): k_ = f"step {m_.get('step')}" if m_.get('step') is not None else (m_.get('by') or 'no step'); d['step2'][k_] = d['step2'].get(k_, 0) + 1
            else: k_ = m_.get('why') or 'no reason'; d['why2'][k_] = d['why2'].get(k_, 0) + 1
        d['gaps'] = [str(x) for x in (rs.get('gaps') or (v or {}).get('gaps') or [])]
        d['sha'] = rs.get('key_text_sha256') or (v or {}).get('key_text_sha256') or ''
        d['sec2'], d['sec1'] = num(rs.get('seconds')), num(v1_seconds.get(st))
        d['g11'] = same_name_land('v2', st, vp, d['proof'] if proof_all is not None else None, facts, store, stems)
        d['g11_v1'] = same_name_land('v1', st, bp, None, facts, store, stems)
        lk = rs.get('locks') if isinstance(rs.get('locks'), dict) else None
        d['locks'] = (lk.get('held', 0), lk.get('broken', 0), lk.get('new', 0)) if lk else (None if 'locks' not in rs and not rs.get('locked_broken') else (0, len(rs.get('locked_broken') or []), 0))
        d['land'] = land_vs_base(st, bp, vp, d['proof'] if proof_all is not None else None, store, stems) if land and not d['nb'] and d['base_ok'] and d['v2_ok'] else None
        d['other_names'] = None if other_names is None else sum(1 for r in other_names if (r.get('st') or r.get('state') or st) == st)
        # the park-by-park list
        for ref in ([] if nobase else sorted(set(bp) | set(vp))):
            p1, p2 = bp.get(ref), vp.get(ref)
            j1, j2 = joined(p1), joined(p2)
            a1, a2 = (joined_acres(p1) if j1 else None), (joined_acres(p2) if j2 else None)
            why = []
            if p1 is None or p2 is None: why.append('park only in ' + ('v1' if p2 is None else 'v2'))
            elif j1 and not j2: why.append('store room gap' if ref in gaprefs else 'outline lost')
            elif j2 and not j1: why.append('outline gained')
            elif j1 and j2 and a1 and a2 and abs(a1 - a2) > ACRE_DIFF * max(a1, a2): why.append('acres differ')
            if not why: continue
            def stat(p, j): return 'confirmed' if j and confirmed(p) else 'outlined' if j else 'pin' if p is not None else '-'
            m2 = (p2 or {}).get('match') or {}
            rows.append({'ref': ref, 'state': st, 'name': (p2 or p1 or {}).get('n') or '',
                         'v1_status': stat(p1, j1), 'v1_by': ((p1 or {}).get('match') or {}).get('by') or '',
                         'v1_acres': '' if a1 is None else round(a1, 1),
                         'v2_status': stat(p2, j2), 'v2_by_step': (f"{m2.get('by') or ''}/step{m2.get('step')}" if m2.get('step') is not None else (m2.get('by') or '')) if p2 else '',
                         'v2_reason': (m2.get('why') or '') if p2 and not j2 else '',
                         'v2_acres': '' if a2 is None else round(a2, 1),
                         'pin_inside_v1': pins1.get(ref, '-'), 'pin_inside_v2': pins2.get(ref, '-'), 'difference': why[0]})
        S[st] = d
    gates = make_gates(S, states, v1_seconds)
    gates.append(lock_gate(lock_check, lock_differs, lock_text, trial))
    return gates, S, rows, notes


def not_built_layer(text):
    """The layer names from the matcher's 'not built' text (it says 'layer sgzz is not complete'); the text itself when it says otherwise."""
    m = re.search(r'layers?\s+([\w\-]+(?:[ ,]+(?:and )?[\w\-]+)*?)\s+(?:is|are)\s+not\s+complete', str(text), re.I)
    return m.group(1).strip() if m else ''


def lock_gate(lock_check, differs=(), detail='', trial=False):
    """G10 (rule sheet 7): a lock may never change an answer. The runner builds twice, cold and with locks, and says if the keys differ."""
    if trial: return ('G10', True, 'a lock never changes an answer: lock check not part of a trial')
    lc = str(lock_check or 'skipped').lower()
    if lc == 'same': return ('G10', True, 'a lock never changes an answer: the cold run and the run with locks are the same')
    if lc == 'differs':
        return ('G10', False, 'a lock changed an answer: ' + (detail or 'the cold run and the run with locks differ' + (f' in {" ".join(differs)}' if differs else '')))
    return ('G10', False, 'a lock never changes an answer: NOT CHECKED (no cold run was given, so nothing is proven; use --cold)')


def per_state(S, states, f):
    return ', '.join(f(S[s]) for s in states)


def make_gates(S, all_states, v1_seconds=None):
    """The gates: v2 judged BY ITSELF. 27 Nov 2026, the owner: "why judge against crap work.. I need a system that works end to
    end and gives me excellent results". So no gate reads the v1 key: G1 (same parks as v1), G6 / G7 (outlined / confirmed hold
    against v1), G8 (speed against v1), H1 / H2 (pin inside / size agrees, v2 against v1) are not gates any more. Their numbers
    are in v1_info_lines() at the end of the text, for information only. G1 is not replaced: the park facts are not POTA's list
    for an area (a park listed in two states has one area there), and the scorecard reads no other park list.
    v1_seconds is not used here any more; it is kept so old callers still work."""
    G = []

    def add(gid, ok, text): G.append((gid, bool(ok), text))
    nb = [s for s in all_states if S[s]['nb']]
    states = [s for s in all_states if not S[s]['nb']]      # a state v2 did not build is judged by G9 only
    nokey = [s for s in states if not S[s]['v2_ok']]         # 27 Nov 2026: a missing v2 key failed G1 before; now it fails G9
    n = sum(S[s]['old'] for s in states)
    add('G2', n == 0, f'ids ending in ~old in joins or check rows: {n}')
    two, same = sum(S[s]['two'] for s in states), sum(S[s]['samename'] for s in states)
    pd_, ps_ = sum(S[s]['pdiff'] for s in states), sum(S[s]['psame'] for s in states)
    add('G3', two == 0 and pd_ == 0, f'two names: ids naming two records {two} (same record name on two parks: {same}, allowed); '
        f'one record on two parks with different park names {pd_}; one record on two parks with the very same park name {ps_} (allowed)')
    n, tot = sum(S[s]['missing'] for s in states), sum(len(S[s]['proof_rows']) for s in states)
    nopf = [s for s in states if not S[s]['proof_rows'] and S[s]['out2']]
    add('G4', n == 0 and not nopf, f'joined records not in the layer files: {n} of {tot}' + (f' (no proof rows for {" ".join(nopf)})' if nopf else ''))
    c2 = sum(S[s]['c2'] for s in states); r2 = sum(len(S[s]['pinonly_rows']) for s in states)
    p2 = sum(S[s]['pin2'] for s in states)
    add('G5', all(S[s]['c2'] + len(S[s]['pinonly_rows']) <= S[s]['pin2'] for s in states),
        f'check rows {c2} + pin-only reasons {r2} against {p2} pin-only parks')
    nogate = [s for s in states if s not in nokey and (not S[s]['run'] or not ((S[s]['run'].get('gate') or {}).get('ok') is True))]
    bad9 = nb or nogate or nokey
    add('G9', not bad9, "the matcher's own gate: " + ('ok in every state' if not bad9 else
        (('NOT BUILT ' + ' '.join(nb) + '; ') if nb else '') + (('NO v2 KEY ' + ' '.join(nokey) + '; ') if nokey else '')
        + (('gate not ok or no run record: ' + ' '.join(nogate)) if nogate else '')).rstrip('; '))
    h11 = sum(len(S[s]['g11']) for s in states); h11p = len({(g['state'], g['park']) for s in states for g in S[s]['g11']})
    add('G11', h11 == 0, f"no park on a same-named park's land: {h11} records ({h11p} parks)")
    return G


def quality_text(d):
    """27 Nov 2026: v2's own two quality numbers, one line. Not pass or fail: no limit is set yet (rule sheet section 17)."""
    h = d['h2']
    return (f"Quality, not pass or fail (no limit is set yet; a low number needs a look): pin inside the land {fmt_pct(h['pin_yes'], h['pin_n'])} "
            f"({h['pin_yes']} of {h['pin_n']}); size agrees with the official size {fmt_pct(h['size_yes'], h['size_n'])} ({h['size_yes']} of {h['size_n']}).")


def has_v1(d): return bool(not d['nobase'] and d['base_ok'])


def v1_info_lines(S, states, compared='', v1_seconds_given=True):
    """27 Nov 2026: everything that compares v2 with the old key, for information only (the owner: "why judge against crap
    work"). [] when no area has a v1 key: then the block is left out of the text."""
    built = [s for s in states if not S[s]['nb']]
    with_v1 = [s for s in built if has_v1(S[s])]
    if not with_v1: return []
    L = ['', 'Next to the old key (v1), for information only. Not part of pass or fail.']
    if compared: L.append(f'Compared with: {compared}')
    gaps = {s: S[s]['gap'] for s in with_v1}
    ng = sum(len(v) for v in gaps.values())
    if ng:
        trl = sum(g['trail'] for v in gaps.values() for g in v)
        L.append(f"Store room gap: {ng} parks ({', '.join(f'{s} {len(v)}' for s, v in gaps.items() if v)}): v1 drew them from layers today's store does not "
                 f"hold (trail lines {trl}, other {ng - trl}). List: v2-store-gap.csv")
    else:
        L.append('Store room gap: 0 parks.')
    for s in built:
        d = S[s]
        if not has_v1(d):
            L.append(f'{s}: no v1 key to compare with.'); continue
        h1, h2 = d['h1'], d['h2']
        sm = d['same']
        L.append(f"{s}: parks v1 {sm[1]}, v2 {sm[2]}" + ('' if sm[0] else f" ({sm[3]} not in v2, {sm[4]} not in v1)") + '.'
                 f" Outlined v1 {d['out1']} -> v2 {d['out2']}, confirmed v1 {d['conf1']} -> v2 {d['conf2']}"
                 + (f" ({len(d['gap'])} parks set apart: v1 drew them from layers the store room does not hold; fair count outlined {d['out1f']} -> {d['out2']}, "
                    f"confirmed {d['conf1f']} -> {d['conf2']})" if d['gap'] else '') + '.')
        L.append(f"  Pin inside the land: v1 {fmt_pct(h1['pin_yes'], h1['pin_n'])} ({h1['pin_yes']} of {h1['pin_n']}), v2 {fmt_pct(h2['pin_yes'], h2['pin_n'])} ({h2['pin_yes']} of {h2['pin_n']}). "
                 f"Size agrees: v1 {fmt_pct(h1['size_yes'], h1['size_n'])} ({h1['size_yes']} of {h1['size_n']}), v2 {fmt_pct(h2['size_yes'], h2['size_n'])} ({h2['size_yes']} of {h2['size_n']}).")
        L.append(f"  Check rows: v1 {d['c1']}, v2 {d['c2']}. Seconds: v1 {_sec(d['sec1'])}, v2 {_sec(d['sec2'])}" + ('' if v1_seconds_given else ' (v1 times not given)') + '. '
                 f"v1 records not in today's file: {h1['ids_missing']} of {h1['ids']} ({h1['ids_trail']} trail lines); v1 ids that fit two records: {h1['ids_fit2']}. "
                 f"v1 parks on a same-named park's land: {len(d['g11_v1'])} records.")
        if d['land'] is not None:
            _, n, a, b = d['land']
            L.append(f"  Same land as v1, parks outlined by both {n}: v2 covers at least 90% of v1's land in {a}; v1 covers at least 90% of v2's land in {b}. List: v2-land-vs-base.csv")
    L.append('Park by park: v2-vs-base.csv.')
    return L


def _sec(x): return 'n/a' if x is None else f'{x:.0f} s'


def render(gates, S, states, notes, compared='', v1_seconds_given=True):
    """27 Nov 2026 (rule sheet 17): the first lines are v2 by itself: the verdict, then per area the parks outlined and pin only,
    the quality numbers, the licence counts; then the gates. Every v1 number is in the last block, for information only."""
    fails = [g for g in gates if not g[1]]
    L = ['V2 PASSES' if not fails else f'V2 DOES NOT PASS YET ({len(fails)} gate{"s" if len(fails) != 1 else ""}: {" ".join(g[0] for g in fails)})',
         f'KPC v2 scorecard, {datetime.datetime.now():%d %b %Y %I:%M %p}. v2 is judged by itself; the old key (v1) is not part of pass or fail. '
         'Counts only, no park names (the names are in the csv lists).']
    shas = [(s, S[s]['sha']) for s in states if S[s].get('sha')]
    if shas: L += ['Key text sha256 (the same on every machine; the zip bytes are not): ' + ', '.join(f'{s} {h}' for s, h in shas)]
    L.append('')
    for s in states:
        d = S[s]
        if d['nb']:
            L.append(f"{s}: NOT BUILT, the store room's layer {d['nb_layer'] or str(d['nb'])[:100]} is not complete" if d['nb_layer'] else f"{s}: NOT BUILT, {str(d['nb'])[:120]}")
            continue
        if not d['v2_ok']:
            L.append(f'{s}: NO v2 KEY in the folder.'); continue
        L.append(f"{s}: {d['same'][2]} parks. Outlined {d['out2']}, pin only {d['pin2']}. Confirmed {d['conf2']}.")
        L.append('  ' + quality_text(d))
        L.append('  ' + licence_text(d['lic'], d['out2']))
        fmt = lambda c: ', '.join(f'{k} {v}' for k, v in sorted(c.items(), key=lambda x: (-x[1], x[0]))) or 'none'
        L.append(f"  Pin only, by reason: {fmt(d['why2'])}. Outlined, by step: {fmt(d['step2'])}." + (f" Store room gap in the layer file: {', '.join(d['gaps'])}." if d['gaps'] else ''))
        lk = d['locks']
        lks = 'Locks: not reported' if lk is None else f'Locks: held {lk[0]}, broken {lk[1]}, new {lk[2]}' + (' (see v2-run.json)' if lk[1] else '')
        h2 = d['h2']
        L.append(f"  Check rows {d['c2']}. Seconds {_sec(d['sec2'])}. {lks}. Records not in today's file: {h2['ids_missing']} of {h2['ids']}. "
                 f"Ids that fit two records (left out): {h2['ids_fit2']}.")
        if d['other_names'] is not None:
            L.append(f"  Id joins that carry another name, for the owner's eyes: {d['other_names']} rows, list: v2-id-other-names.csv")
    built = [s for s in states if not S[s]['nb']]
    if built:
        tot = licence_sum(S[s]['lic'] for s in built)
        L.append(f"Total over {len(built)} built area{'s' if len(built) != 1 else ''}: " + licence_text(tot, sum(S[s]['out2'] for s in built)))
        L.append('  (share all = every record of the park may be shown; share part = some may be; share none = only private records prove it.)')
    two_s = [S[s]['sec2'] for s in ('MN', 'NY') if s in S and not S[s]['nb']]
    if len(two_s) == 2:     # rule sheet 7, "speed is a test": shown, but no longer a gate (it was part of G8)
        L.append(f"Speed: MN + NY {'n/a' if None in two_s else f'{sum(two_s):.0f} s'} (the rule sheet's target is under {TWO_STATES_SECONDS:.0f} s; not a gate).")
    L += ['', 'Gates (v2 by itself)']
    L += [f"{gid} {'PASS' if ok else 'FAIL'} {text}" for gid, ok, text in gates]
    L += v1_info_lines(S, states, compared, v1_seconds_given)
    L += [''] + [f'Note: {n}.' for n in notes]
    return '\n'.join(L).rstrip('\n') + '\n'


def lock_detail(cold, warm, states, max_refs=5):
    """G10 detail. The cold key and the warm key of a state must be the same bytes. When they are not, say which it is: the joins
    (each park's joined ids, sorted, and its status) or only labels. Returns (check, [states that differ], text, csv rows)."""
    diff, seen, rows, bad_parks, label_only = [], 0, [], {}, []
    for st in states:
        a, b = pathlib.Path(cold) / f'{aname(st)}.json.gz', pathlib.Path(warm) / f'{aname(st)}.json.gz'
        if not (a.is_file() and b.is_file()): continue
        seen += 1
        if a.read_bytes() == b.read_bytes(): continue
        diff.append(st)
        pa = (load_json(a) or {}).get('parks') or {}; pb = (load_json(b) or {}).get('parks') or {}

        def sig(p):
            if not isinstance(p, dict): return None
            return (sorted(str(x[0]) for x in p.get('m') or [] if isinstance(x, (list, tuple)) and x), (p.get('match') or {}).get('status'))
        n = 0
        for ref in sorted(set(pa) | set(pb)):
            if sig(pa.get(ref)) != sig(pb.get(ref)):
                n += 1
                if n <= max_refs:
                    sa, sb = sig(pa.get(ref)), sig(pb.get(ref))
                    rows.append({'state': st, 'ref': ref, 'cold_ids': ' '.join(sa[0]) if sa else '', 'warm_ids': ' '.join(sb[0]) if sb else '',
                                 'cold_status': sa[1] if sa else '', 'warm_status': sb[1] if sb else ''})
        if n: bad_parks[st] = n
        else: label_only.append(st)
    if not diff: return ('same' if seen else 'skipped'), [], '', rows
    if bad_parks:
        text = 'joins differ in ' + ', '.join(f'{n} parks ({st})' for st, n in bad_parks.items())
    else:
        text = 'same joins, the files differ only in labels'
    return 'differs', diff, text, rows


CSV_COLS = ['ref', 'state', 'name', 'v1_status', 'v1_by', 'v1_acres', 'v2_status', 'v2_by_step', 'v2_reason', 'v2_acres',
            'pin_inside_v1', 'pin_inside_v2', 'difference']


def write_csv(path, rows):
    rows = sorted(rows, key=lambda r: (r['state'], r['difference'], r['ref']))
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS); w.writeheader(); w.writerows(rows)


def parse_seconds(items):
    out = {}
    for it in items or []:
        for part in re.split(r'[\s,]+', str(it).strip()):
            if '=' in part:
                k, _, v = part.partition('=')
                try: out[k.strip().upper()] = float(v)
                except ValueError: pass
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description='Score a v2 US key by itself; a v1 key, when given, is shown for information only.')
    ap.add_argument('--v2', required=True); ap.add_argument('--base'); ap.add_argument('--no-base', action='store_true', help='no v1 key for these areas (the same as leaving out --base)'); ap.add_argument('--base-name', help='the name of the v1 test, for the information block'); ap.add_argument('--store', required=True)
    ap.add_argument('--facts', required=True); ap.add_argument('--states', nargs='+', required=True)
    ap.add_argument('--v1-seconds', nargs='*', default=[]); ap.add_argument('--out'); ap.add_argument('--repo')
    ap.add_argument('--lock-check', default='skipped', choices=['same', 'differs', 'skipped'])
    ap.add_argument('--lock-differs', nargs='*', default=[])
    ap.add_argument('--trial', action='store_true', help='a trial of other rules: the lock check is not part of it')
    ap.add_argument('--no-land', action='store_true', help='skip H3 (same land as v1), the slowest part')
    ap.add_argument('--cold', help='the cold run folder: the scorecard then compares it with --v2 itself (G10)')
    a = ap.parse_args(argv)
    if not a.base: a.no_base = True   # 27 Nov 2026: no v1 key is fine; v2 is judged by itself (rule sheet 17)
    states = [s.upper() for s in a.states]
    t0 = time.time()
    lock, differs, ltext, lrows = a.lock_check, a.lock_differs, '', []
    if a.cold: lock, differs, ltext, lrows = lock_detail(a.cold, a.v2, states)
    gates, S, rows, notes = build(a.v2, a.base, a.store, a.facts, states, parse_seconds(a.v1_seconds), a.repo, lock, differs, ltext, a.trial, not a.no_land, a.no_base)
    out = pathlib.Path(a.out or a.v2); out.mkdir(parents=True, exist_ok=True)
    gap = [g for st in states if not S[st]['nb'] for g in S[st]['gap']]
    with open(out / 'v2-store-gap.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['ref', 'state', 'name', 'v1_record_ids', 'layer_letters'], extrasaction='ignore'); w.writeheader(); w.writerows(gap)
    with open(out / 'v2-same-name-land.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['side', 'state', 'park', 'other_park', 'record_key', 'record_name']); w.writeheader()
        for st in states:
            if not S[st]['nb']: w.writerows(S[st]['g11'] + S[st]['g11_v1'])
    shared = [r for st in states for r in S[st]['pshare']]
    with open(out / 'v2-two-park-names.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['state', 'record_id', 'parks']); w.writeheader(); w.writerows(shared)
    if lrows:
        with open(out / 'v2-lock-diff.csv', 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(lrows[0])); w.writeheader(); w.writerows(lrows)
    if not a.no_land:
        lr = sorted([r for st in states if S[st]['land'] for r in S[st]['land'][0]], key=lambda r: -max(r['v1 land not in v2'], r['v2 land not in v1']))
        with open(out / 'v2-land-vs-base.csv', 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['ref', 'state', 'name', 'v1 land acres', 'v2 land acres', 'v1 land not in v2', 'v2 land not in v1']); w.writeheader(); w.writerows(lr)
    oth = pathlib.Path(a.v2) / 'v2-id-other-names.csv'
    if oth.is_file() and oth.resolve().parent != out.resolve(): shutil.copyfile(oth, out / 'v2-id-other-names.csv')   # the text points to it in the report folder
    bp_ = pathlib.Path(a.base) if a.base else None
    compared = a.base_name or ('' if a.no_base else (bp_.parent.name if bp_ and bp_.name.lower() == 'keys' else (bp_.name if bp_ else '')))
    if a.no_base: compared = 'no v1 key to compare with (reported on its own)'
    text = render(gates, S, states, notes, compared, bool(parse_seconds(a.v1_seconds)))
    nums = {st: {'parks': S[st]['same'][2], 'nobase': S[st]['nobase'], 'not_built': bool(S[st]['nb']), 'out1': S[st]['out1'], 'out2': S[st]['out2'], 'conf1': S[st]['conf1'], 'conf2': S[st]['conf2'],
                 'pin2': S[st]['pin2'], 'pin_yes': S[st]['h2']['pin_yes'], 'pin_n': S[st]['h2']['pin_n'], 'size_yes': S[st]['h2']['size_yes'], 'size_n': S[st]['h2']['size_n'],
                 'pin_yes1': S[st]['h1']['pin_yes'], 'pin_n1': S[st]['h1']['pin_n'], 'has_v1': has_v1(S[st]), 'why': S[st]['why2'], 'step': S[st]['step2'], 'lic': S[st]['lic'], 'gaps': S[st]['gaps'], 'sec2': S[st]['sec2'],
                 'h3': (S[st]['land'][1:] if S[st]['land'] else None), 'gate_ok': (S[st]['run'].get('gate') or {}).get('ok') if S[st]['run'] else None} for st in states}
    (out / 'v2-score.json').write_text(json.dumps({'gates': [[g, ok, t] for g, ok, t in gates], 'areas': nums}, indent=1, ensure_ascii=False), encoding='utf-8')
    (out / 'V2-SCORECARD.txt').write_text(text, encoding='utf-8')
    write_csv(out / 'v2-vs-base.csv', rows)
    print(text + f'(scorecard took {time.time() - t0:.1f} s)')
    return 0 if all(g[1] for g in gates) else 1


if __name__ == '__main__':
    sys.exit(main())
