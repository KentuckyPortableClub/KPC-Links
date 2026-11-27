#!/usr/bin/env python3
"""KPC v2 scorecard (26 Nov 2026). Decides, with a pass / fail exit code, whether a v2 US key (kpc_us_key_v2.py) is good enough
against the owner's last PC test of the old matcher (v1). Rule sheet: .claude/notes/rule-sheet-us-key-v2-nov26.md (sections 5, 7, 8).

  py -3 kpc_v2_scorecard.py --v2 <v2 folder> --base <v1 keys folder> --store <layer files folder> --facts <park-facts.json.gz>
                            --states MN NY SC [--v1-seconds MN=252 NY=180] [--out <folder>] [--repo <KPC-Links root>]
                            [--cold <cold run folder>] [--lock-check same|differs|skipped]

Writes V2-SCORECARD.txt (counts only, no park names) and v2-vs-base.csv (park by park, the names are there) into --out
(default: the v2 folder). Exit 0 = every gate passes, 1 = at least one fails. Reads files only; stdlib only; no network.

Words used here:
  outlined  = the park has joined records ("with an outline" in the PC test: 310 of 323 in Minnesota).
  confirmed = the key's own match status 'confirmed'.
  pin inside = the park's pin is inside one of its joined records (a pin within 100 m of the edge counts as on the land).
  size agrees = the joined acres are within 10% of an official size in the park facts (the agency size, or a page size marked
                total). Parks with no official size are left out of that count.
"""
import argparse, csv, datetime, gzip, json, os, pathlib, re, sys, time
from itertools import accumulate

NEAR_M = 100.0       # a pin this close to a record's edge counts as on the land
SIZE_TOL = 0.10      # joined acres within 10% of the official size
ACRE_DIFF = 0.10     # the park-by-park list shows parks whose joined acres differ by more than this
HONEST_SLACK = 1.0   # v2 may be this many percentage points worse than v1 on the two honest numbers
TWO_STATES_SECONDS = 300.0


def load_json(p):
    try:
        p = pathlib.Path(p)
        if p.suffix == '.gz':
            with gzip.open(p, 'rt', encoding='utf-8') as f: return json.load(f)
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError, EOFError): return None


def key_file(folder, st):
    for n in (f'US-{st}.json.gz', f'US-{st}.json'):
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
    for base in (repo, repo / 'links'):
        d = load_json(base / '.github' / 'us-key-v2-rules.json')
        if isinstance(d, dict): return d
    return None


def load_limits(repo):
    """The pin allowance (values.pin_m) and the size tolerance (values.size_tol) from the rule table; each value may be a plain
    number or a dict with 'value' (and why / test). Returns ({'pin_m', 'size_tol'}, note); the note says 'defaults used' when the
    table or a value is missing (then 100 m and 10%)."""
    d, out, miss = load_table(repo), {'pin_m': NEAR_M, 'size_tol': SIZE_TOL}, []
    vals = (d or {}).get('values') or {}
    for k in out:
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
        self.pin_m, self.size_tol = pin_m, size_tol
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
        pin = pin_of(fp)
        if not geoms or not pin:
            n['pin_cant'] += 1; pins[ref] = '-'
        else:
            n['pin_n'] += 1
            ok = pin_on_land(pin[0], pin[1], geoms, store.pin_m)
            n['pin_yes'] += ok; pins[ref] = 'yes' if ok else 'no'
        sizes, ac = official_sizes(fp), joined_acres(p)
        if sizes and ac:
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


def build(v2dir, basedir, storedir, factsfile, states, v1_seconds=None, repo=None, lock_check='skipped', lock_differs=(), lock_text='', trial=False):
    """Returns (gates, state_blocks, csv_rows, notes). gates = [(id, ok, text)]."""
    repo = repo or pathlib.Path(__file__).resolve().parents[2]
    id_fields, note = load_id_fields(repo)
    lim, lnote = load_limits(repo)
    store = Store(storedir, id_fields, lim['pin_m'], lim['size_tol'])
    facts = load_json(factsfile) or {}
    notes = [x for x in (note, lnote) if x]
    if not facts.get('parks'): notes.append('park facts not read: the pin and size numbers are empty')
    run = (load_json(pathlib.Path(v2dir) / 'v2-run.json') or {}).get('states') or {}
    proof_all = read_csv(pathlib.Path(v2dir) / 'v2-proof.csv')
    pinonly_all = read_csv(pathlib.Path(v2dir) / 'v2-pin-only.csv')
    v1_seconds = v1_seconds or {}
    other_names = read_csv(pathlib.Path(v2dir) / 'v2-id-other-names.csv')
    S, rows = {}, []
    for st in states:
        d = {'st': st}
        kb, k2 = key_file(basedir, st), key_file(v2dir, st)
        b, v = load_json(kb) if kb else None, load_json(k2) if k2 else None
        d['base_ok'], d['v2_ok'] = isinstance(b, dict), isinstance(v, dict)
        bp = (b or {}).get('parks') or {}; vp = (v or {}).get('parks') or {}
        d['bp'], d['vp'] = bp, vp
        stems = [f'US-{st}'] + [s for s in sorted(((v or {}).get('layer_files') or {})) if s != f'US-{st}']
        d['stems'] = stems
        d['proof'] = {}
        for r in proof_all or []:
            if r.get('st') == st: d['proof'].setdefault(r.get('ref'), []).append(r)
        d['proof_rows'] = [r for rs in d['proof'].values() for r in rs]
        d['pinonly_rows'] = [r for r in pinonly_all or [] if r.get('st') == st]
        d['same'] = (set(bp) == set(vp), len(bp), len(vp), len(set(bp) - set(vp)), len(set(vp) - set(bp)))
        d['out1'], d['out2'] = sum(joined(p) for p in bp.values()), sum(joined(p) for p in vp.values())
        d['conf1'], d['conf2'] = sum(confirmed(p) for p in bp.values()), sum(confirmed(p) for p in vp.values())
        d['pin1'], d['pin2'] = len(bp) - d['out1'], len(vp) - d['out2']
        d['c1'] = sum(len((p or {}).get('c') or []) for p in bp.values())
        d['c2'] = sum(len((p or {}).get('c') or []) for p in vp.values())
        d['old'] = old_ids(vp)
        d['pdiff'], d['psame'], d['pshare'] = park_name_share(vp)
        for r_ in d['pshare']: r_['state'] = st
        d['two'], d['samename'] = two_name_count(vp)
        d['missing'] = sum(1 for r in d['proof_rows'] if not store.has_key(r.get('file_key'), stems))
        d['h1'], pins1 = honest('v1', bp, None, facts, store, stems)
        d['h2'], pins2 = honest('v2', vp, d['proof'] if proof_all is not None else None, facts, store, stems)
        rs = run.get(st) or {}
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
        d['sec2'], d['sec1'] = num(rs.get('seconds')), num(v1_seconds.get(st))
        d['g11'] = same_name_land('v2', st, vp, d['proof'] if proof_all is not None else None, facts, store, stems)
        d['g11_v1'] = same_name_land('v1', st, bp, None, facts, store, stems)
        lk = rs.get('locks') if isinstance(rs.get('locks'), dict) else None
        d['locks'] = (lk.get('held', 0), lk.get('broken', 0), lk.get('new', 0)) if lk else (None if 'locks' not in rs and not rs.get('locked_broken') else (0, len(rs.get('locked_broken') or []), 0))
        d['other_names'] = None if other_names is None else sum(1 for r in other_names if (r.get('st') or r.get('state') or st) == st)
        # the park-by-park list
        for ref in sorted(set(bp) | set(vp)):
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


def make_gates(S, all_states, v1_seconds):
    G = []

    def add(gid, ok, text): G.append((gid, bool(ok), text))
    nb = [s for s in all_states if S[s]['nb']]
    states = [s for s in all_states if not S[s]['nb']]      # a state v2 did not build is judged by G9 only
    miss = [s for s in states if not S[s]['v2_ok'] or not S[s]['base_ok']]
    ok = all(S[s]['same'][0] and S[s]['v2_ok'] and S[s]['base_ok'] for s in states)
    add('G1', ok, 'same parks as v1: ' + per_state(S, states, lambda d: f"{d['st']} {d['same'][1]} v1, {d['same'][2]} v2" + (
        f" ({d['same'][3]} missing, {d['same'][4]} extra)" if not d['same'][0] else '') + ('' if d['v2_ok'] else ' (NO v2 KEY)') + ('' if d['base_ok'] else ' (NO v1 KEY)')))
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
    p2 = sum(S[s]['pin2'] for s in states); c1 = sum(S[s]['c1'] for s in states)
    add('G5', all(S[s]['c2'] + len(S[s]['pinonly_rows']) <= S[s]['pin2'] for s in states),
        f'check rows {c2} + pin-only reasons {r2} against {p2} pin-only parks (v1 had {c1} check rows)')

    def fair(key, label):
        def one(d):
            a, f, b = d[key + '1'], d[key + '1f'], d[key + '2']
            return f"{d['st']} {a} -> {b}" + (f" ({len(d['gap'])} parks set apart: v1 drew them from layers the store room does not hold; fair count {f} -> {b})" if len(d['gap']) else '')
        return f'{label}: ' + per_state(S, states, one)
    add('G6', all(S[s]['out2'] >= S[s]['out1f'] for s in states) and not miss, fair('out', 'outlined parks hold'))
    add('G7', all(S[s]['conf2'] >= S[s]['conf1f'] for s in states) and not miss, fair('conf', 'confirmed parks hold'))
    slow = [s for s in states if v1_seconds and S[s]['sec1'] is not None and (S[s]['sec2'] is None or S[s]['sec2'] > S[s]['sec1'])]
    two_s = [S[s]['sec2'] for s in ('MN', 'NY') if s in S and s in states]
    over = bool(two_s) and (any(x is None for x in two_s) or sum(two_s) >= TWO_STATES_SECONDS)
    sp = per_state(S, states, lambda d: f"{d['st']} {_sec(d['sec2'])} (v1 {_sec(d['sec1'])})")
    add('G8', not slow and not over, 'speed: ' + sp + (f'; MN+NY {sum(x or 0 for x in two_s):.0f} s, limit {TWO_STATES_SECONDS:.0f}' if two_s else '')
        + ('' if v1_seconds else '; v1 times not given'))
    nogate = [s for s in states if not S[s]['run'] or not ((S[s]['run'].get('gate') or {}).get('ok') is True)]
    add('G9', not nb and not nogate, "the matcher's own gate: " + ('ok in every state' if not nb and not nogate else
        (('NOT BUILT ' + ' '.join(nb) + '; ') if nb else '') + (('gate not ok or no run record: ' + ' '.join(nogate)) if nogate else '')))
    h11 = sum(len(S[s]['g11']) for s in states); h11p = len({(g['state'], g['park']) for s in states for g in S[s]['g11']})
    v11 = sum(len(S[s]['g11_v1']) for s in states)
    add('G11', h11 == 0, f"no park on a same-named park's land: v2 {h11} records ({h11p} parks); v1 {v11} (for information)")
    for gid, key, label in (('H1', 'pin', 'pin inside the land'), ('H2', 'size', 'size agrees with the official size')):
        bad = []

        def one(d):
            a, b = d['h1'], d['h2']
            y1, n1, y2, n2 = a[key + '_yes'], a[key + '_n'], b[key + '_yes'], b[key + '_n']
            p1, p2 = pct(y1, n1), pct(y2, n2)
            if p1 is not None and (p2 is None or p2 < p1 - HONEST_SLACK):
                # the size number rests on few parks: it fails only when v2 is also behind by at least 2 parks (counted at v1's rate)
                if key == 'pin' or p2 is None or (p1 * n2 / 100.0 - y2) >= 2: bad.append(d['st'])
            return f"{d['st']} v1 {fmt_pct(y1, n1)} ({y1} of {n1}), v2 {fmt_pct(y2, n2)} ({y2} of {n2})"
        t = per_state(S, states, one)
        add(gid, not bad, f'{label}: {t}' + (f' (v2 worse by more than {HONEST_SLACK:g} point' + (' and 2 parks' if key == 'size' else '') + f' in {" ".join(bad)})' if bad else ''))
    return G


def _sec(x): return 'n/a' if x is None else f'{x:.0f} s'


def render(gates, S, states, notes):
    fails = [g for g in gates if not g[1]]
    gaps = {s: S[s]['gap'] for s in states if not S[s]['nb']}
    ng = sum(len(v) for v in gaps.values())
    L = ['V2 PASSES' if not fails else f'V2 DOES NOT PASS YET ({len(fails)} gate{"s" if len(fails) != 1 else ""})',
         f'KPC v2 scorecard, {datetime.datetime.now():%d %b %Y %I:%M %p}. Counts only, no park names (the names are in the csv lists).']
    if ng:
        trl = sum(g['trail'] for v in gaps.values() for g in v)
        L.append(f"STORE ROOM GAP: {ng} parks ({', '.join(f'{s} {len(v)}' for s, v in gaps.items() if v)}): v1 drew them from layers today's store does not "
                 f"hold (trail lines {trl}, other {ng - trl}). List: v2-store-gap.csv")
    else:
        L.append('STORE ROOM GAP: 0 parks.')
    L.append('')
    for s in states:
        d = S[s]
        h1, h2 = d['h1'], d['h2']
        if d['nb']:
            L.append(f"{s}: NOT BUILT, the store room's layer {d['nb_layer'] or str(d['nb'])[:100]} is not complete" if d['nb_layer'] else f"{s}: NOT BUILT, {str(d['nb'])[:120]}")
            continue
        L.append(f"{s}: {d['same'][1]} parks in v1, {d['same'][2]} in v2. Outlined: v1 {d['out1']}, v2 {d['out2']}. "
                 f"Confirmed: v1 {d['conf1']}, v2 {d['conf2']}. Pin only: v1 {d['pin1']}, v2 {d['pin2']}.")
        lk = d['locks']
        lks = 'Locks: not reported' if lk is None else f'Locks: held {lk[0]}, broken {lk[1]}, new {lk[2]}' + (' (see v2-run.json)' if lk[1] else '')
        L.append(f"  Check rows: v1 {d['c1']}, v2 {d['c2']}. Seconds: v1 {_sec(d['sec1'])}, v2 {_sec(d['sec2'])}. {lks}.")
        L.append(f"  Pin inside the land: v1 {fmt_pct(h1['pin_yes'], h1['pin_n'])} of {h1['pin_n']}, v2 {fmt_pct(h2['pin_yes'], h2['pin_n'])} of {h2['pin_n']}. "
                 f"Size agrees: v1 {fmt_pct(h1['size_yes'], h1['size_n'])} ({h1['size_yes']} of {h1['size_n']}), v2 {fmt_pct(h2['size_yes'], h2['size_n'])} ({h2['size_yes']} of {h2['size_n']}).")
        L.append(f"  Records not in today's file: v1 {h1['ids_missing']} of {h1['ids']} ({h1['ids_trail']} trail lines), v2 {h2['ids_missing']} of {h2['ids']}. "
                 f"Ids that fit two records (left out): v1 {h1['ids_fit2']}, v2 {h2['ids_fit2']}.")
        if d['other_names'] is not None:
            L.append(f"  Id joins that carry another name, for the owner's eyes: {d['other_names']} rows, list: v2-id-other-names.csv")
    L += ['', 'Gates']
    L += [f"{gid} {'PASS' if ok else 'FAIL'} {text}" for gid, ok, text in gates]
    L += [''] + [f'Note: {n}.' for n in notes] + ['Park by park: v2-vs-base.csv.']
    return '\n'.join(L) + '\n'


def lock_detail(cold, warm, states, max_refs=5):
    """G10 detail. The cold key and the warm key of a state must be the same bytes. When they are not, say which it is: the joins
    (each park's joined ids, sorted, and its status) or only labels. Returns (check, [states that differ], text, csv rows)."""
    diff, seen, rows, bad_parks, label_only = [], 0, [], {}, []
    for st in states:
        a, b = pathlib.Path(cold) / f'US-{st}.json.gz', pathlib.Path(warm) / f'US-{st}.json.gz'
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
    ap = argparse.ArgumentParser(description='Score a v2 US key against the v1 keys of the last PC test.')
    ap.add_argument('--v2', required=True); ap.add_argument('--base', required=True); ap.add_argument('--store', required=True)
    ap.add_argument('--facts', required=True); ap.add_argument('--states', nargs='+', required=True)
    ap.add_argument('--v1-seconds', nargs='*', default=[]); ap.add_argument('--out'); ap.add_argument('--repo')
    ap.add_argument('--lock-check', default='skipped', choices=['same', 'differs', 'skipped'])
    ap.add_argument('--lock-differs', nargs='*', default=[])
    ap.add_argument('--trial', action='store_true', help='a trial of other rules: the lock check is not part of it')
    ap.add_argument('--cold', help='the cold run folder: the scorecard then compares it with --v2 itself (G10)')
    a = ap.parse_args(argv)
    states = [s.upper() for s in a.states]
    t0 = time.time()
    lock, differs, ltext, lrows = a.lock_check, a.lock_differs, '', []
    if a.cold: lock, differs, ltext, lrows = lock_detail(a.cold, a.v2, states)
    gates, S, rows, notes = build(a.v2, a.base, a.store, a.facts, states, parse_seconds(a.v1_seconds), a.repo, lock, differs, ltext, a.trial)
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
    text = render(gates, S, states, notes)
    (out / 'V2-SCORECARD.txt').write_text(text, encoding='utf-8')
    write_csv(out / 'v2-vs-base.csv', rows)
    print(text + f'(scorecard took {time.time() - t0:.1f} s)')
    return 0 if all(g[1] for g in gates) else 1


if __name__ == '__main__':
    sys.exit(main())
