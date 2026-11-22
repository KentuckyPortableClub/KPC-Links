#!/usr/bin/env python3
"""THE GRADE: blind line-ups, a scorer with honest ranges, and the gold set (Fable for the KPC owner, 2026-11-18;
.claude/notes/key-quality.md sections 2 B, 2 C, 3 and 4). It reads built keys and writes reports. It decides no join: not a
rule file (kpc_key_freeze.NOT_RULES).

WHY IT IS BUILT THIS WAY (18 Nov: a grade that was shown the pre-sort and asked yes/no rubber-stamped by name)
  BLIND     the grader never sees which records the key joined, the method, the flags, the old answers or the grade.
  LINE-UP   each park comes with its joined records MIXED with look-alikes and neighbours that were not joined. The grader
            says for every candidate YES / BIGGER / NO / UNSURE. A key-joined NO = wrong land; a key-joined BIGGER = too
            big; a not-joined YES = a missing piece. One pass measures all three.
  EVIDENCE  a YES / BIGGER / NO with an empty 'source' is scored UNSURE. A source is an official page the grader opened
            (http...) or 'packet:' + the packet facts that settle it (more than the name).
  PLANTS    about one line-up in ten has a known answer (.github/key-grade-plants.json + the strongest fact-checked parks).
            A grader under 90% on the plants does not count: fix the packet, grade again.
  OVERLAP   one line-up in ten goes to two graders. Where they differ the park is DISPUTED: it joins no rate until Fable
            settles it (score --adjudicated FILE).
  RANGES    every rate comes with its exact 95% range and the 'at most' figure (one-sided 95%). 'Under 1%' needs about 300
            parks with none wrong. A rate is only ever worked out from a RANDOM sample, never from a targeted one.
  GOLD      settled parks go in the gold set, split into TUNE (rules may be developed against it) and SEALED (scores a
            finished build; its misses are not shown). Looking at sealed misses (--show-sealed) moves them to TUNE for good,
            so the seal cannot be peeked through.
            22 Nov 2026 (review M7): WHICH parks are SEALED comes only from a PRIVATE list kept in KPC-Store (--sealed FILE, or
            the path in KPC_GOLD_SEALED), never from a hash with a salt in public code. No list = the gold steps stop (exit 4).
            A gold row's own 'half' decides first (KPC-Store marked every leaked row TUNE); a row with no half takes the list (N13).

  sample   --fact DIR --kind random|busiest|targeted|pin|gold [--by none|method|class] [--n 300] [--per-area 25] --seed S --out FILE
  packet   --sample FILE.. --keys DIR --cache DIR --parkinfo DIR --fact DIR [--truth DIR] --out DIR --label L
           (the grader gets ONLY the folder --out; the answer keys go to <out>-keys, which a grader must never see)
           [--size 60] [--plants-file .github/key-grade-plants.json] [--plant-share 0.1] [--overlap 0.1] --seed S
  score    --key packet*.key.json.. --answers grader*.csv.. --out DIR [--adjudicated FILE] [--gold FILE --sealed FILE]
  gold     --gold FILE --sealed FILE --keys DIR --cache DIR --parkinfo DIR [--show-sealed] [--out DIR]
           (--sealed defaults to the path in KPC_GOLD_SEALED; the private sealed list lives in KPC-Store only)
Standard library only. Outputs never go inside data/ (BRANCH FIRST: KPC-Data tools-out)."""
import argparse, csv, datetime, glob, json, math, os, pathlib, random, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kpc_key_rules as KR          # noqa: E402
import kpc_key_factcheck as FC      # noqa: E402

VERDICTS = ('YES', 'BIGGER', 'NO', 'UNSURE')
PLANT_PASS = 0.90
SEALED_ENV = 'KPC_GOLD_SEALED'   # M7: path of the private sealed list (KPC-Store); the list itself is never in this repo
_SEALED = None                   # set by load_sealed(); None = not loaded, and the gold steps stop
# place words too common to make a record a look-alike by themselves ('lake' would bring in half a state)
COMMON = set('lake lakes river creek mountain mountains point island islands springs spring valley falls fort north south east west upper lower little big old new saint mount bay canyon hill hills rock rocks pond fork bend ridge city town cedar pine oak bear deer eagle wolf blue green red white black grand long clear'.split())

PROMPT = """# How to grade this packet (read all of it first)

You are checking park outlines for a ham radio club's park maps (Parks on the Air). People stand on this land and say
"I am in the park", so a wrong outline sends them to the wrong place.

For each park below you get a LINE-UP of official map records, lettered A, B, C ... Some are this park's land. Some are
other places with a similar name or right next door. You are NOT told which, and the right number can be none, one or several.

Give EVERY candidate exactly one verdict:
- YES     this record is this park's land (the whole park or one piece of it).
- BIGGER  the record holds the park but covers far more than the park (a whole lake property, a whole forest, a county-wide
          record, the parent park of a trail or a small unit). It must not be used as this park's outline.
- NO      another place: a different park, a different designation on other ground, a neighbour.
- UNSURE  you could not establish it. Say in 'note' what would settle it.

Evidence rules. They matter more than speed.
1. A name that looks alike is NOT evidence. A State Park, a State Forest and a Wildlife Area with the same place name are
   usually three different pieces of land. Abbreviations are fine ('WMA', 'SP', 'CaesarCrkSP').
2. Every YES, BIGGER or NO needs a 'source': either the address (http...) of an official page you actually opened (the
   park's own page, the managing agency's unit list, an official map or acreage table), or 'packet:' followed by the
   packet facts that settle it, which must be more than the name. Example: 'packet: pin inside + 2,888 acres against 2,888
   official + designation SP'.
3. If you cannot give a source, the verdict is UNSURE. UNSURE is a good answer. A guess is a bad one and is scored as one.
4. The 'Official size' line was read off a web page by a bot. It is sometimes about a different place or only a part of
   the park. Read the quoted sentence before you lean on it.
5. Look up the park's own website first, then the managing agency. Never use a KPC or POTA map, Wikipedia or a hobby site
   as the only source: they may be built from these same records.
6. Some line-ups are tests with known answers. A grader that fails them is not counted at all.

Write one line per candidate into the answers file, columns exactly: ref,candidate,verdict,source,note
Do not skip a candidate. Do not add columns. Do not change any other file.
"""


# ---------------- small tools ----------------
class NoSealedList(SystemExit):
    pass


def load_sealed(path=None):
    """M7: read the private sealed list ({'parks': [ref, ...]} or [ref, ...]) from path or $KPC_GOLD_SEALED. Fails closed:
    no path, a missing or unreadable file, or no refs -> NoSealedList (exit 4). Returns the set and keeps it for half_of()."""
    global _SEALED
    path = path or os.environ.get(SEALED_ENV) or ''
    if not path:
        print(f'::error title=Gold::no private sealed list (--sealed FILE or {SEALED_ENV}): the gold steps stop', file=sys.stderr)
        raise NoSealedList(4)
    try:
        v = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
        # N13: KPC-Store's sample answer key keeps the private draw under 'sealed_next'; a plain sealed list uses 'parks'
        refs = (v.get('sealed_next') if 'sealed_next' in v else v.get('parks')) if isinstance(v, dict) else v
        if isinstance(refs, dict): refs = list(refs)
        if not isinstance(refs, list) or not refs or not all(isinstance(r, str) and r for r in refs): raise ValueError('no refs')
    except Exception as e:  # noqa: BLE001
        print(f'::error title=Gold::the private sealed list could not be read ({type(e).__name__}): the gold steps stop', file=sys.stderr)
        raise NoSealedList(4) from e
    _SEALED = frozenset(refs)
    return _SEALED


def gold_half(gold_doc, ref):
    """N13: a gold row's own 'half' decides first (Store marked every leaked row TUNE); a row with no half takes the private list."""
    h = (((gold_doc or {}).get('parks') or {}).get(ref) or {}).get('half')
    return h if h in ('TUNE', 'SEALED') else half_of(ref)


def half_of(ref):
    """SEALED only when the park is on the private sealed list (M7). Not loaded = stop (fail closed), never a guess."""
    if _SEALED is None:
        print(f'::error title=Gold::the private sealed list is not loaded (--sealed FILE or {SEALED_ENV}): the gold steps stop', file=sys.stderr)
        raise NoSealedList(4)
    return 'SEALED' if ref in _SEALED else 'TUNE'


def _cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))


def _solve(f, lo=0.0, hi=1.0):
    for _ in range(60):
        mid = (lo + hi) / 2
        if f(mid) > 0: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def interval(k, n, conf=0.95):
    """Exact (Clopper-Pearson) range of a rate: (low, high) two-sided, and 'at most' one-sided at the same confidence."""
    if n <= 0: return 0.0, 1.0, 1.0
    a = (1 - conf) / 2
    lo = 0.0 if k == 0 else _solve(lambda p: a - (1 - _cdf(k - 1, n, p)))
    hi = 1.0 if k == n else _solve(lambda p: _cdf(k, n, p) - a)
    most = 1.0 if k == n else _solve(lambda p: _cdf(k, n, p) - (1 - conf))
    return lo, hi, most


def pct(k, n):
    lo, hi, most = interval(k, n)
    return f"{k} of {n} = {100 * k / n:.1f}% (range {100 * lo:.1f}-{100 * hi:.1f}%, at most {100 * most:.1f}%)" if n else '0 of 0'


def load_fact(fact_dir, areas=None):
    out = {}
    for f in sorted(glob.glob(os.path.join(fact_dir, 'factcheck-[A-Z][A-Z]-[A-Z][A-Z].json'))):
        d = json.load(open(f, encoding='utf-8'))
        if areas and d['area'] not in areas: continue
        out[d['area']] = d['parks']
    return out


# ---------------- sample ----------------
def pool_of(fact):
    """One entry per park (a park in two areas is graded in the area that holds its pin best)."""
    best = {}
    for area, parks in fact.items():
        for ref, e in parks.items():
            k = (e.get('pin_km') if e.get('pin_km') is not None else 1e6, area)
            if ref not in best or k < best[ref][0]: best[ref] = (k, area, e)
    return {ref: (area, e) for ref, (_k, area, e) in best.items()}


def sample(fact, kind, seed, n=300, by='method', per_area=25):
    rng = random.Random(f'{seed}:{kind}:{by}')
    pool = pool_of(fact)
    with_out = sorted(r for r, (_a, e) in pool.items() if e.get('rows'))
    picks = []
    def add(refs, stratum):
        for r in refs: picks.append({'ref': r, 'area': pool[r][0], 'stratum': stratum})
    if kind == 'random' and by == 'none':   # M7 / F8: one plain simple random sample of every park with an outline (the rate)
        add(sorted(rng.sample(with_out, min(n, len(with_out)))), 'random')
    elif kind == 'random':
        strata = {}
        for r in with_out: strata.setdefault(pool[r][1].get('weakest' if by == 'method' else 'class') or '?', []).append(r)
        for s, refs in sorted(strata.items()): add(sorted(rng.sample(refs, min(n, len(refs)))), f'{by}:{s}')
    elif kind == 'busiest':
        per = {}
        for r in with_out: per.setdefault(pool[r][0], []).append(r)
        for a, refs in sorted(per.items()): add(sorted(refs, key=lambda r: (-(pool[r][1].get('act') or 0), r))[:per_area], f'busiest:{a}')
    elif kind == 'targeted':
        refs = [r for r in with_out if pool[r][1].get('class') in ('flagged', 'one', 'none')]
        add(sorted(refs, key=lambda r: (pool[r][1].get('class') != 'flagged', -(pool[r][1].get('act') or 0), r))[:n], 'targeted')
    elif kind == 'pin':
        refs = sorted(r for r, (_a, e) in pool.items() if not e.get('rows'))
        add(sorted(rng.sample(refs, min(n, len(refs)))), 'pin')
    elif kind == 'gold':
        # a mix, each part drawn at random: 40% any park with an outline, 20% weighted by activations, 20% weak or flagged,
        # 10% the loosest methods, 10% pin-only parks (did the key miss an outline that exists?)
        used = set()
        def take(refs, k, stratum, weights=None):
            refs = [r for r in refs if r not in used]
            if weights:
                got = []
                w = [max(1, pool[r][1].get('act') or 0) for r in refs]
                while refs and len(got) < k:
                    i = rng.choices(range(len(refs)), weights=w)[0]; got.append(refs.pop(i)); w.pop(i)
            else: got = rng.sample(refs, min(k, len(refs)))
            used.update(got); add(sorted(got), stratum)
        take(with_out, int(.4 * n), 'gold:any')
        take(with_out, int(.2 * n), 'gold:busy', weights=True)
        take([r for r in with_out if pool[r][1].get('class') in ('flagged', 'one', 'none')], int(.2 * n), 'gold:weak')
        take([r for r in with_out if pool[r][1].get('weakest') in ('reviewed-approx', 'words', 'alias', 'same')], int(.1 * n), 'gold:loose')
        take(sorted(r for r, (_a, e) in pool.items() if not e.get('rows')), n - len(picks), 'gold:pin')
    else: raise SystemExit(f'unknown --kind {kind}')
    return {'seed': str(seed), 'kind': kind, 'by': by, 'made': datetime.date.today().isoformat(), 'parks': picks}


# ---------------- packet ----------------
def show_name(rec, row=None):
    if rec is None: return str(row[1] if row and len(row) > 1 else '')
    u, l = str(rec.get('Unit_Nm') or '').strip(), str(rec.get('Loc_Nm') or '').strip()
    return u if not l or KR.nf(l) == KR.nf(u) else f'{u} / {l}'


def layer_label(rid, rec):
    fam = FC.family(rid)
    if fam == 'padus': return 'USGS PAD-US'
    lab = str((rec or {}).get('Loc_Mang') or '').strip()
    return f'{lab} ({fam})' if lab else fam


def groups_of(pairs, pin):
    """Candidates = records grouped by layer + name. pairs = [(id, record or None, row or None)]."""
    g = {}
    for rid, rec, row in pairs:
        k = (FC.family(rid), KR.nf(show_name(rec, row)))
        x = g.setdefault(k, {'family': k[0], 'name': show_name(rec, row), 'ids': [], 'recs': [], 'acres': 0.0, 'km': None, 'des': set(), 'mang': set(),
                             'layer': layer_label(rid, rec), 'shape': rec is not None})
        x['ids'].append(str(rid))
        x['recs'].append([str(rid), str((rec or {}).get('Unit_Nm') or (row[1] if row and len(row) > 1 else '')), round(float((rec or {}).get('GIS_Acres') or (row[2] if row and len(row) > 2 else 0) or 0))])
        x['acres'] += float((rec or {}).get('GIS_Acres') or (row[2] if row and len(row) > 2 else 0) or (FC.ring_acres(FC.rings_of(rec)) if rec is not None else 0) or 0)
        if rec is not None:
            if rec.get('Des_Tp'): x['des'].add(str(rec['Des_Tp']))
            if rec.get('Mang_Name'): x['mang'].add(str(rec['Mang_Name']))
            if pin:
                km = FC.pin_km(pin[0], pin[1], rec)
                if km is not None and (x['km'] is None or km < x['km']): x['km'] = km
    return g


def lineup(area, ref, key_park, by_id, ix, pinfo_row, forced=(), max_joined=10, look=4, near=3):
    """(header facts, [candidate dicts with 'joined']) for one park. No candidate says how it got here."""
    name = (pinfo_row[0] if pinfo_row else None) or key_park.get('n') or ''
    pin = (pinfo_row[5], pinfo_row[6]) if pinfo_row and len(pinfo_row) > 6 and isinstance(pinfo_row[5], (int, float)) and (pinfo_row[5] or pinfo_row[6]) else None
    rows = [list(m) + [''] * (4 - len(m)) for m in key_park.get('m') or []]
    joined_pairs, jids, meths = [], set(), {}
    for row in rows:
        rec, _why = FC.prove(row, by_id, ix)
        rid = str(rec['OBJECTID']) if rec is not None else str(row[0])
        joined_pairs.append((rid, rec, row)); jids.add(rid)
        meths.setdefault((FC.family(rid), KR.nf(show_name(rec, row))), set()).add(FC.method(row[3]))
    jg = groups_of(joined_pairs, pin)
    joined = sorted(jg.items(), key=lambda kv: -kv[1]['acres'])
    more = max(0, len(joined) - max_joined); joined = joined[:max_joined]
    pcw = {w for w in FC.core(name) if len(w) > 3} - COMMON
    kx = 111.32 * math.cos(math.radians(pin[0])) if pin else 0
    alike, close = [], []
    for rid, rec in by_id.items():
        if rid in jids: continue
        names = KR.rec_names(rec) or []
        is_like = bool(FC.name_fit(name, names)) or bool(pcw and pcw & {w for n in names for w in FC.core(n)})
        bd = 0.0
        if pin:
            if rec.get('_rings') is None: rec['_rings'] = FC.rings_of(rec); rec['_bb'] = FC.bbox_of(rec['_rings'])
            bb = rec.get('_bb')
            if not bb: continue
            bd = math.hypot(max(bb[0] - pin[1], 0, pin[1] - bb[2]) * kx, max(bb[1] - pin[0], 0, pin[0] - bb[3]) * 110.57)
        if is_like and bd <= 60: alike.append((bd, rid, rec))
        elif pin and bd <= 10: close.append((bd, rid, rec))
    alike = [(rid, rec, None) for _bd, rid, rec in sorted(alike, key=lambda t: (t[0], t[1]))[:40]]
    close = [(rid, rec, None) for _bd, rid, rec in sorted(close, key=lambda t: (t[0], t[1]))[:25]]
    for rid in forced:
        if rid in by_id and rid not in jids and not any(rid == a[0] for a in alike): alike.append((rid, by_id[rid], None))
    ag, cg = groups_of(alike, pin), groups_of(close, pin)
    far = lambda x: x['km'] if x['km'] is not None else 1e6
    must = lambda x: any(i in forced for i in x['ids'])
    al = sorted(ag.items(), key=lambda kv: (not must(kv[1]), kv[0] not in jg, far(kv[1]), kv[0]))
    al = al[:look + sum(1 for kv in al if must(kv[1]))]
    cl = sorted(((k, x) for k, x in cg.items() if x['km'] is not None and x['km'] <= 10 and k not in ag), key=lambda kv: (far(kv[1]), kv[0]))[:near]
    cands = []
    for k, x in joined: cands.append(dict(x, joined=True, role='joined', methods=sorted(meths.get(k, ()))))
    for k, x in al: cands.append(dict(x, joined=False, role='sibling' if k in jg else 'alike'))
    for k, x in cl: cands.append(dict(x, joined=False, role='near'))
    head = {'ref': ref, 'area': area, 'name': name, 'type': (pinfo_row[2] if pinfo_row and len(pinfo_row) > 2 else None) or key_park.get('t') or '',
            'web': pinfo_row[1] if pinfo_row and len(pinfo_row) > 1 else '', 'pin': pin, 'more_joined_groups': more}
    return head, cands


def cand_line(letter, c):
    km = ('not in the saved shapes (no distance)' if not c['shape'] else 'no pin to measure from' if c['km'] is None else 'the pin is INSIDE it' if c['km'] == 0
          else f"{c['km']:.2f} km from the pin" if c['km'] < 1 else f"{c['km']:.1f} km from the pin")
    mang = sorted(m for m in c['mang'] if m.lower() != c['family'].lower() and m != 'UNK')[:3]      # a layer code is not a manager
    bits = [f'"{c["name"]}"']
    if c['des']: bits.append('designation ' + '/'.join(sorted(c['des'])))
    if mang: bits.append('manager ' + '/'.join(mang))
    bits += [f"layer {c['layer']}", f"{len(c['ids'])} record" + ('s' if len(c['ids']) > 1 else ''), f"{round(c['acres']):,} acres" if c['acres'] >= 0.5 else 'size not given', km]
    return f"  {letter}. " + ' | '.join(bits)


def packet(samples, keys_dir, cache_dir, pinfo_dir, fact, truth_dir, out, label, seed, size=60, plants=None, plant_share=0.1, overlap=0.1):
    rng = random.Random(f'{seed}:packet:{label}')
    want, seen = [], set()
    for s in samples:
        for p in s['parks']:
            if p['ref'] not in seen: seen.add(p['ref']); want.append(dict(p))
    rng.shuffle(want)
    plants = plants or {}
    # the strongest fact-checked parks are plants too: a code join with the pin inside
    strong = sorted((r, a) for a, parks in fact.items() for r, e in parks.items()
                    if e.get('rows') and e['rows'] <= 3 and not e.get('not_in_read') and 'NPS' in (e.get('methods') or []) and 'pin' in (e.get('witnesses') or []) and not e.get('flags') and r not in seen)
    rng.shuffle(strong)
    n_packets = max(1, math.ceil(len(want) / size))
    chunks = [want[i * size:(i + 1) * size] for i in range(n_packets)]
    plant_refs = sorted(plants)
    rng.shuffle(plant_refs)
    cache, keys, pinfo, truth = {}, {}, {}, {}
    def area_data(a):
        if a not in cache:
            cache.clear()       # one area's shapes in memory at a time
            by_id = FC.load_cache(cache_dir, a); cache[a] = (by_id, FC.name_index(by_id))
        if a not in keys:
            def j(d, default=None):
                try: return json.load(open(d, encoding='utf-8')).get('parks') or {}
                except (OSError, ValueError): return default or {}
            keys[a] = j(os.path.join(keys_dir, a + '.json')); pinfo[a] = j(os.path.join(pinfo_dir, a + '.json'))
            truth[a] = j(os.path.join(truth_dir, a + '.json')) if truth_dir else {}
        return cache[a]
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    keys_out = pathlib.Path(str(out).rstrip('/') + '-keys'); keys_out.mkdir(parents=True, exist_ok=True)   # NEVER hand this folder to a grader
    (out / 'GRADER-PROMPT.md').write_text(PROMPT, encoding='utf-8')
    made = []
    for n, chunk in enumerate(chunks, 1):
        items = [dict(p, plant=False, overlap=False) for p in chunk]
        k = max(1, round(plant_share * len(chunk)))
        for _ in range(k):          # known answers: the hard cases first, then strong parks, in turn
            if plant_refs and (len(items) % 2 == 0 or not strong):
                r = plant_refs.pop(0); plant_refs.append(r)
                if r not in {i['ref'] for i in items}: items.append({'ref': r, 'area': plants[r]['area'], 'stratum': 'plant:hard', 'plant': True, 'overlap': False})
            elif strong:
                r, a = strong.pop(0); items.append({'ref': r, 'area': a, 'stratum': 'plant:strong', 'plant': True, 'overlap': False})
        if n_packets > 1 and overlap:   # one in ten of the previous packet's parks again, for the two-grader comparison
            prev = chunks[n - 2]
            for p in rng.sample(prev, max(1, round(overlap * len(prev)))): items.append(dict(p, plant=False, overlap=True))
        items.sort(key=lambda p: p['area']); order = list(range(len(items))); rng.shuffle(order)
        blocks, keyd, tmpl = {}, {}, []
        for it in items:            # built area by area (one cache at a time), shown in shuffled order
            a, ref = it['area'], it['ref']
            by_id, ix = area_data(a)
            kp = keys[a].get(ref) or {}
            pl = plants.get(ref) if it['stratum'] == 'plant:hard' else None
            expect = {}                       # proven record id -> verdicts that are right (the plant file names records by id + name + acres)
            for x in (pl or {}).get('expect') or []:
                rec, _why = FC.prove([x.get('id'), x.get('name'), x.get('acres'), ''], by_id, ix)
                if rec is not None: expect[str(rec['OBJECTID'])] = list(x.get('verdict') or [])
            head, cands = lineup(a, ref, kp if isinstance(kp, dict) else {}, by_id, ix, pinfo[a].get(ref), forced=tuple(expect))
            crng = random.Random(f'{seed}:{ref}'); crng.shuffle(cands)
            off = (truth[a].get(ref) or {}).get('official'); strength = FC.size_strength(head['name'], off)
            lines = [f"### {ref} | {head['name']}",
                     f"Type: {head['type'] or 'not given'} · Area: {a} · Pin: " + (f"{head['pin'][0]:.5f}, {head['pin'][1]:.5f}" if head['pin'] else 'none') + f" · Website: {head['web'] or 'none on file'}"]
            if strength: lines.append(f"Official size (read off a page by a bot; check it): {round(float(off['acres'])):,} acres - \"{str(off.get('sent') or '')[:200]}\" {off.get('url') or ''}")
            else: lines.append('Official size: none on file')
            lines.append('Candidates:' if cands else 'Candidates: none (no official record with a like name or within 10 km is on file)')
            kc = {}
            for i, c in enumerate(cands):
                L = chr(65 + i) if i < 26 else f'A{chr(65 + i - 26)}'
                lines.append(cand_line(L, c)); tmpl.append([ref, L, '', '', ''])
                exp = None
                if pl: exp = next((v for rid, v in expect.items() if rid in c['ids']), None)
                elif it['stratum'] == 'plant:strong':      # a record joined by its Park Service unit code, with the pin on it, IS the park
                    if c['joined'] and 'NPS' in (c.get('methods') or []) and c['km'] is not None and c['km'] <= FC.PIN_NEAR_KM: exp = ['YES']
                kc[L] = {'joined': c['joined'], 'family': c['family'], 'name': c['name'], 'acres': round(c['acres']), 'ids': c['ids'][:20], 'n_ids': len(c['ids']), 'recs': c['recs'][:60],
                         'methods': c.get('methods') or [], 'role': c['role'], 'expect': exp}
            if head['more_joined_groups']: lines.append(f"  (the park has {head['more_joined_groups']} more small record groups not listed)")
            fe = (fact.get(a) or {}).get(ref) or {}
            blocks[ref] = '\n'.join(lines)
            keyd[ref] = {'area': a, 'name': head['name'], 'stratum': it['stratum'], 'plant': it['plant'], 'overlap': it['overlap'], 'cands': kc,
                         'class': fe.get('class'), 'flags': [f[0] for f in fe.get('flags') or []], 'weakest': fe.get('weakest'), 'act': fe.get('act') or 0}
        refs = [items[i]['ref'] for i in order]
        stem = f'packet-{label}-{n:02d}'
        (out / f'{stem}.md').write_text(f'# Packet {label}-{n:02d}: {len(refs)} parks\n\nRead GRADER-PROMPT.md first. Answers go in {stem}.answers.csv.\n\n'
                                        + '\n\n'.join(blocks[r] for r in refs) + '\n', encoding='utf-8')
        with open(out / f'{stem}.answers-template.csv', 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh); w.writerow(['ref', 'candidate', 'verdict', 'source', 'note'])
            pos = {r: i for i, r in enumerate(refs)}
            w.writerows(sorted(tmpl, key=lambda t: (pos[t[0]], len(t[1]), t[1])))
        (keys_out / f'{stem}.key.json').write_text(json.dumps({'label': label, 'packet': n, 'seed': str(seed), 'made': datetime.date.today().isoformat(), 'parks': keyd}, indent=0) + '\n', encoding='utf-8')
        made.append((stem, len(refs), sum(1 for i in items if i['plant'])))
    return made


# ---------------- score ----------------
def read_answers(paths):
    """{grader: {(ref, letter): (verdict, source, note)}}; the grader is the file name up to the first dot."""
    out = {}
    for p in paths:
        g = os.path.basename(p).split('.')[0]
        for x in csv.DictReader(open(p, encoding='utf-8')):
            v = str(x.get('verdict') or '').strip().upper()
            src = str(x.get('source') or '').strip()
            if v not in VERDICTS: v = 'UNSURE'
            if v != 'UNSURE' and not src: v = 'UNSURE'          # no evidence = UNSURE
            out.setdefault(g, {})[(str(x.get('ref') or '').strip(), str(x.get('candidate') or '').strip().upper())] = (v, src, str(x.get('note') or '').strip())
    return out


def merge(v1, v2, joined):
    """Two graders on one candidate -> (verdict, None) or (verdict or None, kind of dispute).
    NO and BIGGER both say 'not this park's outline'. On a record the key did not join, only a YES matters.
    'conflict' (one YES, one NO / BIGGER) blocks the park until Fable settles it; 'one unsure' leaves that candidate UNSURE."""
    if v1 == v2: return v1, None
    s_ = {v1, v2}
    if s_ == {'NO', 'BIGGER'}: return 'BIGGER', None
    if 'YES' in s_ and s_ & {'NO', 'BIGGER'}: return None, 'conflict'
    other = (s_ - {'UNSURE'}).pop()
    if not joined and other in ('NO', 'BIGGER'): return other, None
    return 'UNSURE', 'one unsure'


def outcome(kp, verdicts):
    """One park, one set of verdicts {letter: verdict} -> (outcome, detail letters)."""
    j = {L: verdicts.get(L, 'UNSURE') for L, c in kp['cands'].items() if c['joined']}
    o = {L: verdicts.get(L, 'UNSURE') for L, c in kp['cands'].items() if not c['joined']}
    wrong = sorted(L for L, v in j.items() if v == 'NO'); big = sorted(L for L, v in j.items() if v == 'BIGGER')
    miss = sorted(L for L, v in o.items() if v == 'YES'); uns = sorted(L for L, v in j.items() if v == 'UNSURE')
    if wrong: return 'WRONG LAND', wrong
    if big: return 'TOO BIG', big
    if j and len(uns) == len(j): return 'UNSURE', uns
    if miss: return 'MISSING PIECES', miss
    if not j: return ('PIN IS RIGHT' if all(v in ('NO', 'BIGGER') for v in o.values()) else 'UNSURE'), []
    return ('RIGHT' if not uns else 'RIGHT (part unsure)'), uns


def score(key_paths, answer_paths, adjudicated=None):
    parks = {}
    for kp in key_paths:
        d = json.load(open(kp, encoding='utf-8'))
        for ref, p in d['parks'].items():
            parks.setdefault(ref, p)
    ans = read_answers(answer_paths)
    adj = {}
    if adjudicated:
        for x in csv.DictReader(open(adjudicated, encoding='utf-8')):
            adj[(x['ref'].strip(), x['candidate'].strip().upper())] = (x['verdict'].strip().upper(), x.get('source', ''), x.get('by', ''))
    rep = {'graders': {}, 'parks': {}, 'disputes': [], 'rates': {}}
    # ---- each grader on the plants
    for g, a in ans.items():
        hit = tot = shy = 0; missed = []
        for ref, p in parks.items():
            for L, c in p['cands'].items():
                if c.get('expect') and (ref, L) in a:
                    if a[(ref, L)][0] == 'UNSURE': shy += 1; continue
                    tot += 1; ok = a[(ref, L)][0] in c['expect']; hit += ok
                    if not ok: missed.append(f"{ref} {L} '{c['name']}' said {a[(ref, L)][0]}, known {'/'.join(c['expect'])}")
        dec = [v for v in a.values() if v[0] != 'UNSURE']
        counts = (tot == 0 and shy == 0) or (tot > 0 and hit / tot >= PLANT_PASS and shy <= tot)
        rep['graders'][g] = {'answers': len(a), 'plants': tot, 'plants_right': hit, 'plants_unsure': shy, 'counts': bool(counts), 'missed': missed[:12],
                             'unsure': sum(1 for v in a.values() if v[0] == 'UNSURE'), 'with_a_page': sum(1 for v in dec if v[1].lower().startswith('http')), 'decided': len(dec)}
    good = [g for g, r in rep['graders'].items() if r['counts']]
    # ---- each park
    for ref, p in parks.items():
        per = {}
        for g in good:
            v = {L: ans[g][(ref, L)][0] for L in p['cands'] if (ref, L) in ans[g]}
            if v: per[g] = v
        if not per: continue
        final, how = None, 'single'
        if len(per) >= 2:           # two graders: only a difference that could change the park's outcome is a dispute
            gs = sorted(per)[:2]; final, kinds = {}, set()
            for L, c in p['cands'].items():
                v, why = merge(per[gs[0]].get(L, 'UNSURE'), per[gs[1]].get(L, 'UNSURE'), c['joined'])
                final[L] = v
                if why:
                    kinds.add(why)
                    rep['disputes'].append({'ref': ref, 'name': p['name'], 'candidate': L, 'record': c['name'], 'joined_by_key': c['joined'], 'kind': why,
                                            **{g: f"{ans[g][(ref, L)][0]} [{ans[g][(ref, L)][1][:140]}]" for g in gs if (ref, L) in ans[g]}})
            how = 'double' if not kinds else 'double (part unsure)' if kinds == {'one unsure'} else 'disputed'
        else: final = dict(next(iter(per.values())))
        hit = [L for L in p['cands'] if (ref, L) in adj]
        if hit:
            for L in hit: final[L] = adj[(ref, L)][0]
            how = 'adjudicated' if all(v is not None for v in final.values()) else how
        if any(v is None for v in final.values()): final = None
        o, letters = outcome(p, final) if final else ('DISPUTED', [])
        rep['parks'][ref] = {'area': p['area'], 'name': p['name'], 'stratum': p['stratum'], 'plant': p['plant'], 'outcome': o, 'letters': letters, 'graded': how,
                             'verdicts': final, 'class': p.get('class'), 'flags': p.get('flags'), 'weakest': p.get('weakest'), 'act': p.get('act')}
    # ---- rates, by stratum, plants left out
    by = {}
    for ref, r in rep['parks'].items():
        if r['plant']: continue
        for s in ('ALL', r['stratum']): by.setdefault(s, []).append(r['outcome'])
    for s, outs in sorted(by.items()):
        decided = [o for o in outs if o not in ('UNSURE', 'DISPUTED')]
        n = len(decided)
        rep['rates'][s] = {'parks': len(outs), 'decided': n, 'unsure': outs.count('UNSURE'), 'disputed': outs.count('DISPUTED'),
                           'wrong_land': pct(decided.count('WRONG LAND'), n), 'too_big': pct(decided.count('TOO BIG'), n),
                           'missing_pieces': pct(decided.count('MISSING PIECES'), n), 'right': pct(sum(1 for o in decided if o.startswith('RIGHT') or o == 'PIN IS RIGHT'), n)}
    return rep, parks, ans


def write_score(rep, parks, ans, out, gold=None):
    gdoc = {}
    if gold and pathlib.Path(gold).is_file():   # N13: the rows' own halves, read before anything is hidden or listed
        gdoc = json.loads(pathlib.Path(gold).read_text(encoding='utf-8'))
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    L = ['GRADERS']
    for g, r in sorted(rep['graders'].items()):
        L.append(f"  {g}: {r['answers']} answers, {r['unsure']} unsure, {r['with_a_page']} of {r['decided']} decided ones cite a page | known answers {r['plants_right']} of {r['plants']} right, {r['plants_unsure']} unsure"
                 + ('' if r['counts'] else '  ** FAILED THE KNOWN ANSWERS: NOT COUNTED **'))
        for m in r['missed']: L.append(f'      missed: {m}')
    L.append('RATES (random strata are rates; busiest / targeted / gold strata are work lists, not rates)')
    for s, r in rep['rates'].items():
        L.append(f"  {s}: {r['parks']} parks, {r['decided']} decided, {r['unsure']} unsure, {r['disputed']} disputed")
        for k in ('wrong_land', 'too_big', 'missing_pieces', 'right'): L.append(f"      {k.replace('_', ' ')}: {r[k]}")
    conf = [d for d in rep['disputes'] if d.get('kind') == 'conflict']
    L.append(f"DISPUTES for Fable: {len(conf)} conflict(s) (one says YES, one says no) on {len({d['ref'] for d in conf})} park(s); {len(rep['disputes']) - len(conf)} candidate(s) where one grader was unsure")
    (out / 'score.txt').write_text('\n'.join(L) + '\n', encoding='utf-8')
    shown = dict(rep, parks={ref: (r if not (gold and gold_half(gdoc, ref) == 'SEALED' and not r['plant'] and r['graded'] != 'adjudicated') else {'area': r['area'], 'stratum': r['stratum'], 'sealed': True})
                             for ref, r in rep['parks'].items()})
    (out / 'score.json').write_text(json.dumps(shown, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    if rep['disputes']:
        cols = sorted({k for d in rep['disputes'] for k in d}, key=lambda k: (k not in ('ref', 'name', 'candidate', 'record', 'joined_by_key', 'kind'), k))
        with open(out / 'disputes.csv', 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, cols + ['fable_verdict', 'fable_source']); w.writeheader(); w.writerows(rep['disputes'])
    with open(out / 'findings.csv', 'w', newline='', encoding='utf-8') as fh:      # every non-RIGHT park: the cause code is filled by the adjudicator
        w = csv.writer(fh); w.writerow(['activations', 'ref', 'area', 'name', 'outcome', 'record', 'methods', 'fact_class', 'fact_flags', 'graded', 'sources', 'cause (A-F)', 'fix'])
        rows, hidden = [], 0
        for ref, r in rep['parks'].items():
            if r['plant'] or r['outcome'].startswith('RIGHT') or r['outcome'] == 'PIN IS RIGHT': continue
            if gold and gold_half(gdoc, ref) == 'SEALED' and r['graded'] != 'adjudicated': hidden += 1; continue      # the sealed half is never listed: it scores the next finished build first
            p = parks[ref]
            for Lr in r['letters'] or ['']:
                c = p['cands'].get(Lr, {})
                srcs = ' | '.join(f"{g}: {a[(ref, Lr)][1][:120]}" for g, a in ans.items() if (ref, Lr) in a)
                rows.append([r.get('act') or 0, ref, r['area'], r['name'], r['outcome'], c.get('name', ''), '/'.join(c.get('methods') or []), r.get('class'), '/'.join(r.get('flags') or []), r['graded'], srcs, '', ''])
        w.writerows(sorted(rows, key=lambda x: -x[0]))
    if gold:
        L.append(f'FINDINGS listed: {len({x[1] for x in rows})} park(s) of the TUNE half; {hidden} more are in the SEALED half and are not listed (gold --show-sealed reveals them, and that moves them to TUNE)')
        (out / 'score.txt').write_text('\n'.join(L) + '\n', encoding='utf-8')
    if gold:        # settled parks join the gold set: two graders agreed, or adjudicated, or one grader with a page on every decided verdict
        gp = pathlib.Path(gold)
        g = json.loads(gp.read_text(encoding='utf-8')) if gp.is_file() else {'about': 'KPC gold set: parks verified against official sources. SEALED rows score finished builds only.', 'parks': {}, 'log': []}
        added = 0
        for ref, r in rep['parks'].items():
            if r['outcome'] in ('UNSURE', 'DISPUTED') or not r['verdicts'] or 'UNSURE' in r['verdicts'].values(): continue
            p = parks[ref]
            srcs = {Lr: [a[(ref, Lr)][1] for a in ans.values() if (ref, Lr) in a] for Lr in p['cands']}
            need = [Lr for Lr, c in p['cands'].items() if c['joined'] or r['verdicts'][Lr] in ('YES', 'BIGGER')]
            if r['graded'] == 'single' and not all(any(x.lower().startswith('http') for x in srcs[Lr]) for Lr in need): continue
            g['parks'][ref] = {'area': r['area'], 'name': r['name'], 'graded': r['graded'], 'date': datetime.date.today().isoformat(),
                               'half': 'TUNE' if (p['plant'] or r['graded'] == 'adjudicated') else gold_half(g, ref),
                               'cands': [{'family': c['family'], 'name': c['name'], 'acres': c['acres'], 'recs': c.get('recs') or [], 'n_recs': c.get('n_ids') or len(c.get('recs') or []),
                                          'verdict': r['verdicts'][Lr], 'sources': srcs[Lr][:2]} for Lr, c in p['cands'].items()]}
            added += 1
        g['log'].append(f"{datetime.date.today().isoformat()}: {added} park(s) added or refreshed")
        gp.write_text(json.dumps(g, indent=0, ensure_ascii=False) + '\n', encoding='utf-8')
    return L


# ---------------- gold: score a finished build ----------------
def gold_score(gold_path, keys_dir, cache_dir, pinfo_dir, show_sealed=False):
    gp = pathlib.Path(gold_path); g = json.loads(gp.read_text(encoding='utf-8'))
    per_area = {}
    for ref, p in g['parks'].items(): per_area.setdefault(p['area'], []).append(ref)
    res = {'TUNE': [], 'SEALED': []}
    for area, refs in sorted(per_area.items()):
        try: key = json.load(open(os.path.join(keys_dir, area + '.json'), encoding='utf-8')).get('parks') or {}
        except (OSError, ValueError): continue
        by_id = FC.load_cache(cache_dir, area); ix = FC.name_index(by_id)
        try: pinfo = json.load(open(os.path.join(pinfo_dir, area + '.json'), encoding='utf-8')).get('parks') or {}
        except (OSError, ValueError): pinfo = {}
        for ref in refs:
            p = g['parks'][ref]; kp = key.get(ref) if isinstance(key.get(ref), dict) else {}
            now, now_groups = set(), set()          # the records the key joins NOW, each proven in this read (ids get renumbered)
            for m in (kp or {}).get('m') or []:
                row = list(m) + [''] * (4 - len(m)); rec, _w = FC.prove(row, by_id, ix)
                rid = str(rec['OBJECTID']) if rec is not None else str(row[0])
                now.add(rid); now_groups.add((FC.family(rid), KR.nf(show_name(rec, row))))
            wrong, big, miss = [], [], []
            for c in p['cands']:
                ids = [str(rec['OBJECTID']) for rec in (FC.prove([x[0], x[1], x[2], ''], by_id, ix)[0] for x in c.get('recs') or []) if rec is not None]
                if not ids: continue
                share = sum(1 for i in ids if i in now) / len(ids)
                if c['verdict'] == 'NO' and share > 0: wrong.append(c['name'])
                elif c['verdict'] == 'BIGGER' and share > 0: big.append(c['name'])
                elif c['verdict'] == 'YES' and share < 0.8: miss.append(c['name'])
            new = [k[1] for k in now_groups if k not in {(c['family'], KR.nf(c['name'])) for c in p['cands']}]
            o = 'WRONG LAND' if wrong else 'TOO BIG' if big else 'MISSING PIECES' if miss else 'NEW RECORD (ungraded)' if new else 'RIGHT'
            half = gold_half(g, ref)   # N13: the row's own half first, else the private list (never a public hash)
            res[half].append((ref, area, p['name'], o, (wrong + big + miss + new)[:3]))
    lines = []
    for half in ('TUNE', 'SEALED'):
        rows = res[half]; n = len([r for r in rows if not r[3].startswith('NEW')])
        lines.append(f"{half}: {len(rows)} gold parks in these keys | wrong land {pct(sum(r[3] == 'WRONG LAND' for r in rows), n)} | too big {pct(sum(r[3] == 'TOO BIG' for r in rows), n)}"
                     f" | missing pieces {pct(sum(r[3] == 'MISSING PIECES' for r in rows), n)} | new ungraded records on {sum(r[3].startswith('NEW') for r in rows)}")
        if half == 'TUNE' or show_sealed:
            for r in rows:
                if r[3] != 'RIGHT': lines.append(f"    {r[0]} {r[1]} {r[2]}: {r[3]} {r[4]}")
    if show_sealed:      # looking costs the seal: every sealed miss just shown becomes a TUNE park
        moved = [r[0] for r in res['SEALED'] if r[3] != 'RIGHT']
        for ref in moved: g['parks'][ref]['half'] = 'TUNE'
        if moved:
            g['log'].append(f"{datetime.date.today().isoformat()}: {len(moved)} sealed miss(es) shown, moved to TUNE for good: {', '.join(moved[:40])}")
            gp.write_text(json.dumps(g, indent=0, ensure_ascii=False) + '\n', encoding='utf-8')
            lines.append(f'{len(moved)} sealed park(s) were shown and are now TUNE. Add fresh sealed parks to replace them.')
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('sample'); s.add_argument('--fact', required=True); s.add_argument('--kind', required=True); s.add_argument('--by', default='method')
    s.add_argument('--n', type=int, default=300); s.add_argument('--per-area', type=int, default=25); s.add_argument('--seed', required=True)
    s.add_argument('--areas'); s.add_argument('--out', required=True)
    p = sub.add_parser('packet'); p.add_argument('--sample', nargs='+', required=True)
    for k in ('keys', 'cache', 'parkinfo', 'fact', 'out', 'label', 'seed'): p.add_argument('--' + k, required=True)
    p.add_argument('--truth'); p.add_argument('--size', type=int, default=60); p.add_argument('--plants-file', default=str(HERE.parent / 'key-grade-plants.json'))
    p.add_argument('--plant-share', type=float, default=0.1); p.add_argument('--overlap', type=float, default=0.1)
    c = sub.add_parser('score'); c.add_argument('--key', nargs='+', required=True); c.add_argument('--answers', nargs='+', required=True)
    c.add_argument('--out', required=True); c.add_argument('--adjudicated'); c.add_argument('--gold'); c.add_argument('--sealed')
    gd = sub.add_parser('gold'); gd.add_argument('--gold', required=True)
    for k in ('keys', 'cache', 'parkinfo'): gd.add_argument('--' + k, required=True)
    gd.add_argument('--show-sealed', action='store_true'); gd.add_argument('--out'); gd.add_argument('--sealed')
    a = ap.parse_args(argv)
    if a.cmd == 'sample':
        fact = load_fact(a.fact, set(a.areas.replace(',', ' ').split()) if a.areas else None)
        d = sample(fact, a.kind, a.seed, a.n, a.by, a.per_area)
        pathlib.Path(a.out).write_text(json.dumps(d, indent=0) + '\n', encoding='utf-8')
        cnt = {}
        for x in d['parks']: cnt[x['stratum']] = cnt.get(x['stratum'], 0) + 1
        print(f"{len(d['parks'])} parks:", ', '.join(f'{k} {v}' for k, v in sorted(cnt.items())) if len(cnt) <= 14 else f'{len(cnt)} strata')
    elif a.cmd == 'packet':
        samples = [json.load(open(f, encoding='utf-8')) for f in a.sample]
        areas = {x['area'] for s_ in samples for x in s_['parks']}
        try: plants = json.load(open(a.plants_file, encoding='utf-8')).get('plants') or {}
        except (OSError, ValueError): plants = {}
        fact = load_fact(a.fact)
        for stem, n, npl in packet(samples, a.keys, a.cache, a.parkinfo, fact, a.truth, a.out, a.label, a.seed, a.size, plants, a.plant_share, a.overlap):
            print(f'{stem}: {n} parks ({npl} with a known answer)')
    elif a.cmd == 'score':
        if a.gold: load_sealed(a.sealed)   # M7: stop before scoring when the private sealed list is missing
        rep, parks, ans = score(a.key, a.answers, a.adjudicated)
        print('\n'.join(write_score(rep, parks, ans, a.out, a.gold)))
    elif a.cmd == 'gold':
        load_sealed(a.sealed)
        lines = gold_score(a.gold, a.keys, a.cache, a.parkinfo, a.show_sealed)
        print('\n'.join(lines))
        if a.out: pathlib.Path(a.out).mkdir(parents=True, exist_ok=True); (pathlib.Path(a.out) / 'gold-score.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
