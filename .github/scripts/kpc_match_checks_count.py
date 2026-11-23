#!/usr/bin/env python3
"""kpc_match_checks_count.py: what the match checks (kpc_match_checks.py) would do to the saved US keys. Counts only, including confirmed by id, by link and by size.

Offline and read-only: reads the saved key files (data/us-key/US-XX.json), a saved copy of the records the key reads (the
builder's own cache files US-XX.json.gz, with outlines), KPC-Data's park facts file and data/nps-units.json. It contacts
nothing, builds nothing and writes only the --out file. No park is named in its output.

  python3 kpc_match_checks_count.py --cache DIR --facts park-facts.json.gz [--keys data/us-key] [--out report.json]
"""
import argparse, copy, glob, gzip, json, math, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_match_checks as TA  # noqa: E402

NATIONAL = ('wld', 'hma', 'hab', 'rma', 'rst', 'wsrc', 'fwsr', 'fsod', 'nca', 'wsa', 'wbl', 'fws', 'nps')


def is_national(rid):
    s = str(rid)
    return s.isdigit() or re.match(r'[a-z_]*', s).group(0) in NATIONAL


def in_ring(x, y, r):
    ins, j = False, len(r) - 1
    for i in range(len(r)):
        xi, yi = r[i][0], r[i][1]; xj, yj = r[j][0], r[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi: ins = not ins
        j = i
    return ins


def near_rings(la, lo, rings, km):
    k = math.cos(math.radians(la)) * 111.32
    for r in rings:
        for (x1, y1), (x2, y2) in zip(r, r[1:]):
            ax, ay, bx, by = (x1 - lo) * k, (y1 - la) * 110.57, (x2 - lo) * k, (y2 - la) * 110.57
            dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
            t = 0 if L == 0 else max(0, min(1, -(ax * dx + ay * dy) / L))
            if math.hypot(ax + t * dx, ay + t * dy) <= km: return True
    return False


def box(rings):
    xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def klass_rows(m):
    return {TA.row_class(q) for q in m}


def predict_state(st, key, recs, facts, layers, units, seen=None, table=None):
    parks = copy.deepcopy(key['parks'])
    recs = dict(recs)
    before = key['parks']
    geo = {}
    for i, a in recs.items():
        rr = [r for r in (a.get('_r') or []) if len(r) >= 3]
        if rr: geo[i] = (rr, box(rr))

    # records the key joined that the saved cache does not hold (the Fish and Wildlife layer is read live, never cached):
    # a stand-in made from the key's own row, with the builder's kind rule; place then comes from the key's own 'far' note
    stub = set()
    for ref, p in before.items():
        for q in p.get('m') or []:
            i = str(q[0])
            if i not in recs:
                recs[i] = {'OBJECTID': i, 'Unit_Nm': q[1], 'Loc_Nm': '', 'GIS_Acres': q[2], '_k': sorted(TA.kinds(q[1]))}
                if i.startswith('fws'): recs[i]['Mang_Type'] = 'FED'
                stub.add(i)
    proxy = set()

    def place(ref, ids):
        pin = (facts.get(ref) or {}).get('pin')
        pts = ([tuple(pin)] if pin and len(pin) == 2 and None not in pin else []) + TA.page_pins(facts.get(ref))
        sh = [geo[i] for i in ids if i in geo]
        if not sh and ids and all(i in stub for i in ids) and pts:
            proxy.add(ref)
            far = before.get(ref, {}).get('far')
            return None if far == 'edge' else far is None
        if not sh or not pts: return None
        pad = TA.NEAR_KM / 100.0
        for la, lo in pts:
            for rr, b in sh:
                if not (b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad): continue
                if sum(1 for r in rr if in_ring(lo, la, r)) % 2 == 1 or near_rings(la, lo, rr, TA.NEAR_KM): return True
        return False

    def holds(ref, i):
        pin = (facts.get(ref) or {}).get('pin')
        if not pin or len(pin) != 2 or None in pin or i not in geo: return None
        rr, b = geo[i]
        la, lo = pin
        if not (b[0] <= lo <= b[2] and b[1] <= la <= b[3]): return False
        return sum(1 for r in rr if in_ring(lo, la, r)) % 2 == 1

    def url_of(a):
        pre = re.match(r'[a-z]*', str(a.get('OBJECTID'))).group(0)
        v = layers.get(pre)
        return v[0] if isinstance(v, list) and v else ''

    def is_no(ref, rid, a):
        return False   # the saved NOs live in overrides; the builder applies them, the count here is an upper bound

    skip = {r for r, p in before.items() if p.get('line')}
    hits = []
    def near(ref, i, ids):   # W8b: the record against the park's other joined land (saved shapes)
        if i not in geo: return None
        other = [r for j in ids if j in geo for r in geo[j][0]]
        return TA.rings_near(geo[i][0], other) if other else None

    res = TA.pass_state(parks, recs, facts, place, url_of, is_no, skip, st, units, hits, holds, table, near_fn=near)
    if seen is not None: seen.update(hits=hits, parks=parks, recs=recs)
    c = {k: 0 for k in ('parks', 'joined_before', 'nonname_before', 'confirmed', 'outlined', 'pin', 'gain', 'lose', 'id_confirmed',
                        'confirmed_by_id', 'confirmed_by_link', 'confirmed_by_size',
                        'rows_to_check', 'rows_joined_by_id', 'nat_before', 'nat_name_before', 'nat_after', 'nat_parks_before',
                        'nat_parks_after', 'rec_missing', 'line_untouched')}
    for ref, p0 in before.items():
        p1 = parks[ref]; c['parks'] += 1
        j0, j1 = bool(p0.get('m')), bool(p1.get('m'))
        c['joined_before'] += j0; c['gain'] += (not j0) and j1; c['lose'] += j0 and not j1
        c['nonname_before'] += j0 and 'name' not in klass_rows(p0['m'])
        s_ = (p1.get('match') or {}).get('status')
        if j0 or j1:
            if s_ in ('confirmed', 'outlined'): c[s_] += 1
            elif not j1: c['pin'] += 1
            else: c['line_untouched'] += 1          # an official trail line park: not checked here, kept as it is
        c['id_confirmed'] += bool((p1.get('match') or {}).get('id'))
        by = (p1.get('match') or {}).get('by')
        if by in ('id', 'link', 'size'): c['confirmed_by_' + by] += 1
        n0 = [q for q in p0.get('m') or [] if is_national(q[0])]
        n1 = [q for q in p1.get('m') or [] if is_national(q[0])]
        c['nat_before'] += len(n0); c['nat_after'] += len(n1)
        c['nat_name_before'] += sum(1 for q in n0 if TA.how_word(q) in ('name', 'words'))
        c['nat_parks_before'] += bool(n0); c['nat_parks_after'] += bool(n1)
        c['rec_missing'] += sum(1 for q in p0.get('m') or [] if str(q[0]) not in recs)
    c['rows_to_check'] = sum(1 for h in hits if h[1] != 'joined (id)')
    c['rows_joined_by_id'] = sum(1 for h in hits if h[1] == 'joined (id)')
    for k, v in res['why'].items(): c['why: ' + k] = v
    for k, v in res['notes'].items(): c['note: ' + k] = v
    c['rec_stand_in'] = len(stub); c['place_from_key_note'] = len(proxy)
    return c


def load_recs(dirs, st):
    """{record id: record} from the first of the folders holding each record; None = no folder has the state."""
    out, found = {}, False
    for d in dirs:
        cf = os.path.join(d, f'US-{st}.json.gz')
        if not os.path.exists(cf): continue
        found = True
        for r in json.load(gzip.open(cf, 'rt')).get('recs') or []:
            out.setdefault(str(r['OBJECTID']), r)
    return out if found else None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--keys', default='data/us-key')
    ap.add_argument('--cache', required=True, action='append', help='a folder of US-XX.json.gz record copies (repeat: the first holding a record wins)')
    ap.add_argument('--facts', required=True)
    ap.add_argument('--units', default='data/nps-units.json')
    ap.add_argument('--layer-table', help="each layer's owner (KPC-Links .github/layer-agency-kind.json; default: this repo's)")
    ap.add_argument('--out')
    a = ap.parse_args(argv)
    table = TA.load_layer_table(a.layer_table)
    facts = json.load(gzip.open(a.facts, 'rt') if a.facts.endswith('.gz') else open(a.facts))['parks']
    layers = json.load(open(os.path.join(a.keys, 'layers.json')))
    units = TA.load_nps_units(a.units)
    rep = {'about': 'counts only; no park named', 'modes': {}}
    for mode in ('rule',):
        per = {}
        for f in sorted(glob.glob(os.path.join(a.keys, 'US-??.json'))):
            st = os.path.basename(f)[3:5]
            recs = load_recs(a.cache, st)
            if recs is None: per[st] = {'no_cache': 1}; continue
            key = json.load(open(f))
            per[st] = predict_state(st, key, recs, facts, layers, units, table=table)
        tot = {}
        for v in per.values():
            for k, n in v.items(): tot[k] = tot.get(k, 0) + n
        rep['modes'][mode] = {'total': tot, 'states': per}
        print(mode, json.dumps(tot), flush=True)
    if a.out:
        with open(a.out, 'w') as fh: json.dump(rep, fh, indent=1, sort_keys=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
