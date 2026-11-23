#!/usr/bin/env python3
"""kpc_saved_answers_fix.py: the saved answers that no longer find their record (owner 23 Nov 2026, 9:20 AM; the outside agent's job
7: 323 not found, 64 that fit two). Offline: reads the saved answers (data/us-key/overrides.json + parts), the US keys, the saved
copies (US-XX.json.gz, the boundary-cache release) and the park facts (POTA pins). It contacts nothing and builds nothing.

  count  the builder's own saved-answer test, before and after (counts only, no park named)
  fix    the ONE-TIME batch the owner asked for, written to the saved answers (a draft PR; nothing merges without him):
         - a record number that changed ("Wouldn't fixing records id be best solution?"): the answer is re-pointed to the record
           of the same name AND acres (within 10%, at least 20) near the pin, on any layer, when exactly one fits; the old number
           is kept under 'renumbered' {old: new};
         - split into pieces: the same-name records near the pin, each smaller than the saved acres, that add up to them (within
           10%, at least 20), two or more: the answer becomes those pieces (each with its own fingerprint);
         - a bare NAME answer whose record now carries another spelling of the same place (W8's same_bare: the same bare name,
           a kind that fits) near the pin, exactly one: it becomes that record's id + fingerprint;
         - the rest (nothing of that name and size near the pin, no fingerprint to check it by): RETIRED, moved from 'join' to
           'retired_join' with the reason, so the normal matching decides the park. Nothing is deleted.
         An answer whose record sits in a NEIGHBOUR state's saved copy is not changed here: the builder reads it from there
         (KPC_SAVED_NEXT_STATE). The answers that fit several parcels of the same park join them all (KPC_SAVED_ALL_PARCELS).

  python3 .github/scripts/kpc_saved_answers_fix.py count --cache DIR --facts park-facts.json.gz [--keys data/us-key]
  python3 .github/scripts/kpc_saved_answers_fix.py fix   --cache DIR --facts park-facts.json.gz [--keys data/us-key] --today YYYY-MM-DD
"""
import argparse, collections, glob, gzip, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_key_rules as KR  # noqa: E402
import kpc_match_checks as MC  # noqa: E402
import kpc_overrides as KOVR  # noqa: E402

NEAR = .6
NB = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'us-key', 'area-tables.json'), encoding='utf-8'))['US_NEIGHBOURS']
ID_RX = re.compile(r'^[a-z_]*\d+$')


def nf(t): return KR.nf(t)


def fam(i): return re.match(r'\D*', str(i)).group()


def box_of(rr):
    xs = [p[0] for r in rr or [] for p in r if len(p) >= 2]; ys = [p[1] for r in rr or [] for p in r if len(p) >= 2]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def near(la, lo, b, pad=NEAR):
    return bool(b) and b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad


def acres(v):
    try: return float(v or 0)
    except (TypeError, ValueError): return 0.0


def load_copies(cache):
    """{state: [(id, name, acres, box)]}: every saved copy, the fields the saved-answer test reads."""
    out = {}
    for f in sorted(glob.glob(os.path.join(cache, 'US-??.json.gz'))):
        st = os.path.basename(f)[3:5]
        rows = []
        for r in json.load(gzip.open(f, 'rt')).get('recs') or []:
            rows.append((str(r.get('OBJECTID')), r.get('Unit_Nm') or r.get('Loc_Nm') or '', acres(r.get('GIS_Acres')), box_of(r.get('_r'))))
        out[st] = rows
    return out


def park_states(keys):
    out = {}
    for f in sorted(glob.glob(os.path.join(keys, 'US-??.json'))):
        st = os.path.basename(f)[3:5]
        for ref in json.load(open(f, encoding='utf-8')).get('parks') or {}:
            out.setdefault(ref, st)
    return out


def test_answer(want, ov, rows, by_id, la, lo, next_door=None, all_parcels=False, park_name=''):
    """The builder's test for one saved join -> ('found' | 'two' | 'none', [ids it joins]). next_door = {id: (state, row)} of the
    other states' copies (KPC_SAVED_NEXT_STATE); all_parcels = KPC_SAVED_ALL_PARCELS."""
    w = str(want)
    near_rows = [x for x in rows if la is None or near(la, lo, x[3])]
    if w in by_id: return 'found', [w]
    fp = (ov.get('fp') or {}).get(w)
    if fp:
        v, h = KR.refind_saved(fp[0], fp[1], fam(w), [(x[0], x[1], x[2]) for x in near_rows])
        if v == 'one': return 'found', [h]
        if v == 'two': return ('found', list(h)) if all_parcels and MC.all_parcels_ok(park_name, [x[1] for x in near_rows if x[0] in h]) else ('two', [h[0]])
    if next_door is not None and w in next_door:
        st2, x = next_door[w]
        if la is None or near(la, lo, x[3]): return 'found', [w]
    if any(nf(x[1]) == nf(w) for x in near_rows): return 'found', [x[0] for x in near_rows if nf(x[1]) == nf(w)][:1]
    return 'none', []


def plan_fix(want, ov, rows, la, lo, park_name):
    """For an answer that finds nothing: ('renumber', new id, fp) | ('split', [(id, fp)]) | ('name', id, fp) | ('retire', why)."""
    w = str(want)
    near_rows = [x for x in rows if la is None or near(la, lo, x[3])]
    fp = (ov.get('fp') or {}).get(w)
    if fp and acres(fp[1]) >= 5:
        fn, fa = fp[0], acres(fp[1])
        same = [x for x in near_rows if nf(x[1]) == nf(fn)]
        fit = [x for x in same if abs(x[2] - fa) <= max(20, .1 * fa)]
        if len(fit) > 1 and all(x[3] and fit[0][3] and KR._box_share(x[3], fit[0][3]) >= KR.SAME_GROUND and KR._box_share(fit[0][3], x[3]) >= KR.SAME_GROUND
                                for x in fit):
            # the same land in two layers (PAD-US and the state's own layer): one piece of ground, so one answer; the record of the
            # saved answer's own layer when it has one, else the one whose acres are closest to the saved ones
            fit = sorted(fit, key=lambda x: (fam(x[0]) != fam(w), abs(x[2] - fa)))[:1]
        if len(fit) == 1: return ('renumber', fit[0][0], [fit[0][1], round(fit[0][2], 1)])
        if not fit:
            pieces = [x for x in same if 0 < x[2] < fa]
            if len(pieces) >= 2 and abs(sum(x[2] for x in pieces) - fa) <= max(20, .1 * fa):
                return ('split', [(x[0], [x[1], round(x[2], 1)]) for x in pieces])
        return ('retire', 'record split, merged or redrawn: nothing of that name and size near the pin' if same
                else 'record gone: nothing of that name near the pin')
    if not ID_RX.match(w):
        alike = [x for x in near_rows if MC.same_bare(x[1], w) or MC.same_bare(x[1], park_name) and MC.same_bare(w, park_name)]
        alike = [x for x in alike if MC.same_bare(x[1], w)]
        if len(alike) == 1: return ('name', alike[0][0], [alike[0][1], round(alike[0][2], 1)])
        return ('retire', 'a bare name answer: no single record of that name near the pin')
    return ('retire', 'no fingerprint saved: the answer cannot be checked (key-quality.md: an id alone is never trusted)')


def walk(a, after=False, fixed=None):
    copies = load_copies(a.cache)
    facts = json.load(gzip.open(a.facts, 'rt'))['parks']
    doc = KOVR.load(os.path.join(a.keys, 'overrides.json'))
    parks = fixed if fixed is not None else doc['parks']
    where = park_states(a.keys)
    by_state = {st: {x[0]: x for x in rows} for st, rows in copies.items()}
    doors = {}

    def next_door_of(st):
        """the bordering states' saved copies (KPC_SAVED_NEXT_STATE, as the builder reads them): {id: (state, row)}, and by name"""
        if st not in doors:
            d = {}
            for s2 in KR.neighbours(st, NB):
                for x in copies.get(s2) or []:
                    d.setdefault(x[0], (s2, x))
                    d.setdefault(('name', nf(x[1])), []).append((s2, x))
            doors[st] = d
        return doors[st]
    c = collections.Counter(); by_st = collections.Counter(); plans = []
    for ref, ov in sorted(parks.items()):
        st = where.get(ref)
        if not st or st not in copies or not isinstance(ov, dict): continue
        pin = (facts.get(ref) or {}).get('pin') or [None, None]
        la, lo = pin[0], pin[1]
        name = (facts.get(ref) or {}).get('name') or ''
        for want in ov.get('join') or []:
            v, ids = test_answer(want, ov, copies[st], by_state[st], la, lo,
                                 next_door_of(st) if after else None, all_parcels=after, park_name=name)
            c[v] += 1
            if v != 'found': by_st[(st, v)] += 1
            if v == 'none': plans.append((ref, st, str(want), plan_fix(want, ov, copies[st], la, lo, name)))
    read_here = collections.defaultdict(set)
    for s2, rows in copies.items():
        for x in rows: read_here[s2].add(fam(x[0]))
    for i, (ref, st, w, p) in enumerate(plans):
        if p[0] == 'retire' and ID_RX.match(w) and fam(w) not in read_here[st]:
            plans[i] = (ref, st, w, ('retire', f"the layer it came from ({fam(w)}) is not saved for this state, nor next door (a park across "
                                               f"state lines): the keeper must save that land for {st} before it can join"))
    return c, by_st, plans, doc


def cmd_count(a):
    for label, after in (('before', False), ('after (next state + all parcels, no batch)', True)):
        c, by_st, plans, _ = walk(a, after)
        print(f'{label}: found {c["found"]:,}, not found {c["none"]:,}, fit two {c["two"]:,}')
        if after:
            k = collections.Counter(p[3][0] for p in plans)
            print('  the batch would: ' + ', '.join(f'{n} {w}' for w, n in sorted(k.items())))
    return 0


WSR = re.compile(r'wild and scenic|scenic river', re.I)


def protected_parks(keys, facts):
    """Parks whose saved answers other sheets pin: an official trail LINE park (the key's 'line'; the trail-31 sheet) and every wild and
    scenic river park (the corridor sheet). The batch never changes them."""
    out = set()
    for f in sorted(glob.glob(os.path.join(keys, 'US-??.json'))):
        for ref, p in (json.load(open(f, encoding='utf-8')).get('parks') or {}).items():
            if p.get('line') or WSR.search(str(p.get('t') or '') + ' ' + str(p.get('n') or '')): out.add(ref)
    for ref, p in (facts or {}).items():
        if WSR.search(str(p.get('type') or '') + ' ' + str(p.get('name') or '')): out.add(ref)
    return out


def cmd_fix(a):
    c, by_st, plans, doc = walk(a, True)
    parks = doc['parks']
    protected = protected_parks(a.keys, json.load(gzip.open(a.facts, 'rt'))['parks'])
    k = collections.Counter()
    for ref, st, want, plan in plans:
        ov = parks[ref]
        join = [str(x) for x in ov.get('join') or []]
        if want not in join: continue
        if ov.get('evidence') or ov.get('decided_by'):
            k['kept: a signed or decided answer, never changed here'] += 1; continue   # a person's signed decision is never re-pointed or retired
        if ref in protected:
            k['kept: a trail line or wild and scenic river park (pinned by its own sheet)'] += 1; continue
        if plan[0] == 'retire' and plan[1].startswith('the layer it came from'):
            k['kept: waits for its layer to be saved for this state'] += 1; continue   # an accepted cross-state answer waits; never retired
        i = join.index(want)
        kind = plan[0]
        if kind == 'renumber':
            new, fp = plan[1], plan[2]
            join[i] = new
            ov.setdefault('fp', {}).pop(want, None); ov['fp'][new] = fp
            ov.setdefault('renumbered', {})[want] = new
        elif kind == 'split':
            join[i:i + 1] = [x for x, _ in plan[1]]
            old_fp = ov.setdefault('fp', {}).pop(want, None)
            for x, fp in plan[1]: ov['fp'][x] = fp
            ov.setdefault('split_from', {})[want] = {'into': [x for x, _ in plan[1]], 'fp': old_fp}
        elif kind == 'name':
            join[i] = plan[1]
            ov.setdefault('fp', {})[plan[1]] = plan[2]
            ov.setdefault('renumbered', {})[want] = plan[1]
        else:
            join.pop(i)
            ov.setdefault('retired_join', []).append({'id': want, 'fp': (ov.get('fp') or {}).get(want), 'why': plan[1], 'when': a.today})
        ov['join'] = join
        if not ov['join']: ov.pop('join')
        ov.setdefault('fixed', []).append(f"{a.today}: saved answer {want} {kind} (owner 23 Nov 2026 9:20 AM, job 7)")
        k[kind] += 1
    KOVR.save(os.path.join(a.keys, 'overrides.json'), doc)
    print('saved answers changed: ' + ', '.join(f'{n} {w}' for w, n in sorted(k.items())))
    c2, _, plans2, _ = walk(a, True)
    print(f'after the batch (with next state + all parcels): found {c2["found"]:,}, not found {c2["none"]:,}, fit two {c2["two"]:,}')
    print('  still not found, by why: ' + ', '.join(f'{n} {w}' for w, n in sorted(collections.Counter(
        ('kept signed or decided' if (parks[r].get('evidence') or parks[r].get('decided_by')) else 'kept pinned park' if r in protected
         else 'waits for its layer' if p[1].startswith('the layer it came from') else 'other') for r, s, w, p in plans2).items())))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['count', 'fix'])
    ap.add_argument('--cache', required=True)
    ap.add_argument('--facts', required=True)
    ap.add_argument('--keys', default='data/us-key')
    ap.add_argument('--today', default='')
    a = ap.parse_args(argv)
    if a.cmd == 'fix' and not a.today:
        ap.error('fix needs --today')
    return cmd_count(a) if a.cmd == 'count' else cmd_fix(a)


if __name__ == '__main__':
    sys.exit(main())
