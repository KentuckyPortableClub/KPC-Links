#!/usr/bin/env python3
"""KPC v2 state prep (26 Nov 2026). Before a new state is run through the v2 matcher, this measures its saved files and the park facts
and PROPOSES rule-table rows from the measurements, so a new state gets its rows from numbers, not from guesses. Saved copies only:
no network, nothing downloaded or uploaded. It reads the rule table and never writes it.

  py -3.12 kpc_v2_state_prep.py SC [--store <folder>] [--facts <file>] [--v2 <a v2 run folder>] [--out <folder>] [--repo <KPC-Links root>]

Reads: the state's layer file and its neighbours (the rule table's neighbour list), the park facts, the state's park list
(data/pota/saved/parks/US-<ST>.json.gz, the list the matcher uses) and the rule table. Writes ONE new folder, <out>\\v2-prep-<ST>-<time>\\:
  STATE-PREP-<ST>.txt   plain words, one screen, counts first, what to do next at the end (no park names)
  proposed-rows.json    table fragments in the real table's shape (every row has its why; test is TODO); a person decides
  prep-details.csv      every measurement row
  name-compare.csv      every park against every official name we hold (the names are here, never in the txt)
Sections: 1 store room check, 2 id fields, 3 agency record ids, 4 name fields and name styles, 4b official names against POTA's names,
5 what to do next. The idea and the table format come from kpc_id_finder / kpc_keep_fields (.github/keep-record-fields.json).
"""
import argparse, csv, datetime, gzip, json, pathlib, re, subprocess, sys, time, unicodedata
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parent
for _p in (HERE, HERE.parent.parent / 'tools' / 'pc-keys', HERE / 'links' / 'tools' / 'pc-keys'):
    if (_p / 'kpc_v2_scorecard.py').is_file() and str(_p) not in sys.path: sys.path.insert(0, str(_p))
import kpc_v2_scorecard as SC  # noqa: E402  (side-effect free)
import kpc_test_v2 as T  # noqa: E402  (side-effect free: folder helpers)

MIN_PARKS = 3
KIND_EXTRA = {'historic', 'historical', 'memorial', 'monument', 'wild', 'marine', 'heritage', 'nature', 'battlefield', 'seashore', 'lakeshore', 'parkway', 'scenic'}
ID_LIKE = re.compile(r'^[A-Za-z]{0,8}\d{1,14}$')
URLISH = re.compile(r'https?://|www\.', re.I)
TOKEN = re.compile(r'(?:(?<=[/=?&#])|^)([A-Za-z0-9_-]{3,16})(?=[/?&.#]|$)')


# ---------------------------------------------------------------- the rule table (read only)

class Rules:
    def __init__(self, repo):
        d = SC.load_table(repo)
        self.found = isinstance(d, dict)
        t = (d or {}).get('tables') or {}
        self.t = t
        g = lambda k, dflt: ((t.get(k) or {}).get('value')) if isinstance((t.get(k) or {}).get('value'), type(dflt)) else dflt
        self.neighbours = g('neighbours', {})
        self.short = g('short_forms', {})
        self.kinds = set(g('kind_words', []))
        self.places = set(g('place_words', []))
        self.swaps = g('kind_swaps', [])
        self.name_fields = g('name_fields', {})
        self.full_fields = g('full_name_fields', {})
        self.id_ties = g('id_ties', [])
        self.rec_fields = g('record_id_fields', {})
        self.drop = g('drop_layers', {})
        self.kind_set = (self.kinds | KIND_EXTRA) - {'a', 'n', 'no', 'na', 'other', 'name', 'none', 'unknown', 'site', 'sites'} | {'site'}
        self.lim, self.lim_note = SC.load_limits(repo)
        self.place_len = 4
        vals = (d or {}).get('values') or {}
        v = vals.get('place_word_len')
        v = v.get('value') if isinstance(v, dict) else v
        if isinstance(v, int) and v > 0: self.place_len = v


def words(name, R):
    """A name as words: accents and brackets out, '&' = and, a possessive is one word (Devil's -> devils), 'wildlife and fish' = wildlife,
    punctuation out, 'the' out, the table's short forms written out."""
    t = unicodedata.normalize('NFKD', str(name or '')).encode('ascii', 'ignore').decode().lower()
    t = re.sub(r'\(.*?\)', ' ', t).replace('&', ' and ')
    t = re.sub(r"(?<=[a-z])['`]s\b", 's', t).replace("'", '')
    t = t.replace('wildlife and fish', 'wildlife')
    out = []
    for w in re.sub(r'[^a-z0-9 ]+', ' ', t).split():
        if w == 'the': continue
        out.extend(R.short.get(w, w).split())
    return out


def nkey(s): return re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def real_words(ws, R): return {w for w in ws if len(w) >= R.place_len and w not in R.kind_set and w not in R.places and not w.isdigit()}


def core(ws, R): return [w for w in ws if w not in R.kind_set]


def _initial_pair(a, b): return (len(a) == 1 and b.startswith(a) and len(b) > 1) or (len(b) == 1 and a.startswith(b) and len(a) > 1)


def _kind_text(ws, R, drop_and=True): return ' '.join(w for w in ws if w in R.kind_set and not (drop_and and w == 'and'))


def tail_label(prefix, tail, R):
    """A pattern label: the words are shown only when every one is a kind word (they name no place)."""
    return f"{prefix}: {' '.join(tail)}" if tail and all(w in R.kind_set for w in tail) else prefix


def compare_names(pota, off, R):
    """POTA's name against an official name. Returns (verdict, pattern): verdict 'same' | 'after rules' | 'differs'; pattern is the plain
    reason ('' for same)."""
    if nkey(pota) == nkey(off): return 'same', ''
    pw, ow = words(pota, R), words(off, R)
    if not pw or not ow: return 'differs', 'no name to compare'
    if pw == ow: return 'after rules', "spelling rules (short forms, possessive, brackets)"
    if ''.join(pw) == ''.join(ow): return 'after rules', 'words run together'
    pj, oj = ' '.join(pw), ' '.join(ow)
    for sw in R.swaps:
        for rk in sw.get('record_kinds') or []:
            if oj.endswith(rk) and (oj[:-len(rk)].strip() + ' ' + sw['park_kind']).strip() == pj: return 'after rules', 'kind swap (' + sw['park_kind'] + ')'
    if '/' in str(off):
        parts = [x for x in str(off).split('/') if x.strip()]
        for i, part in enumerate(parts):
            if len(parts) > 1 and words(part, R) == pw: return 'differs', 'a second name in front' if i == len(parts) - 1 else 'a second name after'
    if sorted(pw) == sorted(ow): return 'differs', 'same words, other order'
    if len(pw) == len(ow) and all(a == b or _initial_pair(a, b) for a, b in zip(pw, ow)): return 'differs', 'initial vs full word'
    cp, co = core(pw, R), core(ow, R)
    if cp and len(cp) == len(co) and cp != co and all(x == y or _initial_pair(x, y) for x, y in zip(cp, co)): return 'differs', 'initial vs full word'
    if cp and cp == co:
        pk, ok = _kind_text(pw, R), _kind_text(ow, R)
        if pk != ok:
            if not ok: return 'differs', "official name lacks the park's kind word: " + pk
            if not pk: return 'differs', 'official name adds a kind word: ' + ok
            return 'differs', f'kind word differs: {pk} vs {ok}'
    if ow[:len(pw)] == pw and len(ow) > len(pw):
        tail = ow[len(pw):]
        if tail[0] == 'and' and len(tail) > 1 and tail[1] in R.kind_set: return 'differs', 'official name adds "and <kind>"'
        return 'differs', tail_label('official name has extra last word(s)', tail, R)
    if pw[:len(ow)] == ow and len(pw) > len(ow):
        tail = pw[len(ow):]
        return 'differs', tail_label("official name lacks last word(s)", tail, R) if not all(w in R.kind_set for w in tail) else tail_label("official name lacks the park's kind word", tail, R)
    if cp and co and set(cp) < set(co): return 'differs', 'official name has extra word(s)'
    if cp and co and set(co) < set(cp): return 'differs', 'official name lacks word(s)'
    if not (real_words(pw, R) & real_words(ow, R)): return 'differs', 'a completely different name'
    return 'differs', 'other difference'


def compare_web(pota, web, R):
    """POTA's name against the name inside its page address (lower case, words run together: 'sunkenmeadow')."""
    w = nkey(web)
    pw = words(pota, R)
    if not w or not pw: return 'differs', 'no name to compare'
    pc, pf = ''.join(core(pw, R)), ''.join(pw)
    if w in (pc, pf): return ('same', '') if w == nkey(pota) else ('after rules', 'words run together or kind word left out')
    cw = core(pw, R)
    if cw and len(''.join(cw)) > 3:
        rx = ''.join((re.escape(x) + '[a-z]*') if len(x) == 1 else re.escape(x) for x in cw)
        if re.fullmatch(rx, w): return 'differs', 'initial vs full word'
    if pc and w.startswith(pc) and len(w) > len(pc): return 'differs', 'official name has extra last word(s)'
    if pc and w.endswith(pc) and len(w) > len(pc): return 'differs', 'official name has extra first word(s)'
    if pc and pc.startswith(w) and len(pc) > len(w): return 'differs', 'official name lacks last word(s)'
    if not any(x in w for x in real_words(pw, R)): return 'differs', 'a completely different name'
    return 'differs', 'other difference'


RANK = {'same': 0, 'after rules': 1, 'differs': 2}


def rank(v, pat): return (RANK[v], 1 if pat == 'a completely different name' else 0)


# ---------------------------------------------------------------- loading

def norm_val(v):
    """An id value as text (the matcher's own spelling): 89125.0 -> '89125', 'SRA00304  ' -> 'SRA00304'; '' when empty."""
    if v is None or isinstance(v, bool): return ''
    if isinstance(v, float):
        if v != v: return ''
        if v.is_integer(): v = int(v)
    return str(v).strip().upper()


def strip0(n): return re.sub(r'^([A-Z]*)0+(?=\d)', r'\1', n)


def attr(rec, field):
    a = rec.get('attributes') or {}
    if field in a: return a[field]
    lo = field.lower()
    return next((a[k] for k in a if str(k).lower() == lo), None)


def park_refs(repo, st, facts):
    d = SC.load_json(pathlib.Path(repo) / 'data' / 'pota' / 'saved' / 'parks' / f'US-{st}.json.gz')
    if isinstance(d, dict) and d.get('data'):
        return sorted({str(x.get('reference')) for x in d['data'] if x.get('reference')}), ''
    refs = sorted(r for r, p in facts.items() if str(p.get('area') or '') == f'US-{st}')
    return refs, "the state's park list (data/pota/saved/parks) was not found: the parks of the park facts for this state are used"


def pw_ok(facts, ref): return (facts.get(ref) or {})


def pin_of(fp): return SC.pin_of(fp)


# ---------------------------------------------------------------- section 1

def store_room(doc, R, st):
    man = doc.get('manifest') or {}
    recs = doc.get('records') or []
    by = defaultdict(list)
    for r in recs: by[str(r.get('layer') or '')].append(r)
    rows, gaps = [], []
    for lay in sorted(set(man) | set(by)):
        m = man.get(lay)
        rs = by.get(lay, [])
        keys = Counter(str(r.get('key') or '') for r in rs)
        complete = bool((m or {}).get('complete'))
        why = (m or {}).get('why') or ('' if complete else ('not in the manifest' if m is None else 'not complete'))
        row = {'layer': lay, 'complete': complete, 'why': why, 'records': len(rs), 'no_shape': sum(1 for r in rs if not r.get('rings')),
               'repeat_keys': sum(1 for k, c in keys.items() if c > 1), 'not_in_manifest': m is None and bool(rs), 'dropped': lay in R.drop}
        rows.append(row)
        if not complete: gaps.append(lay)
    return rows, sorted(gaps)


# ---------------------------------------------------------------- section 2

def build_wants(refs, facts):
    """{ref: {kind: id value}} from the park facts: usable link ids and the page's NPS code."""
    out = {}
    for ref in refs:
        fp = facts.get(ref) or {}
        lk = fp.get('link') or {}
        d = {}
        if lk.get('usable') and lk.get('id_value') and lk.get('id_kind'): d[str(lk['id_kind'])] = norm_val(lk['id_value'])
        nc = (fp.get('page') or {}).get('nps_code')
        if nc and 'NPS unit code' not in d: d['NPS unit code'] = norm_val(nc)
        out[ref] = {k: v for k, v in d.items() if v}
    return out


def _hit(hits, vals, shit, shared_ids, wants, key, ref, rec, value):
    if (key[0], wants[ref].get(key[0])) in shared_ids: shit[key].add(ref)
    else: hits[key][ref].add(rec); vals[key][ref].add(value)


def find_id_hits(files, wants, link_ties):
    """Search every string / number field of every record for the parks' id values: whole, stripped of leading zeros, inside a web address.
    files = [(stem, records)]. Returns {(kind, layer, field, way): {ref: {(file index, record index)}}}, {key: {ref: set of values}}."""
    whole, stripped, shared = defaultdict(set), defaultdict(set), []
    byval = defaultdict(lambda: defaultdict(set))
    for ref, d in wants.items():
        for k, v in d.items(): byval[(k, v)][ref].add(ref)
    shared_ids = {kv for kv, refs in byval.items() if len(refs) > 1}
    for ref, d in wants.items():
        for k, v in d.items():
            whole[v].add((k, ref)); stripped[strip0(v)].add((k, ref))
    ties = []
    for t in link_ties:
        try: ties.append((t['kind'], re.compile(t['rx'], re.I)))
        except (re.error, KeyError): pass
    hits, vals = defaultdict(lambda: defaultdict(set)), defaultdict(lambda: defaultdict(set))
    shit = defaultdict(set)    # parks whose id value another park shares: kept apart (the matcher gives such an id to nobody)
    for fi, (stem, recs) in enumerate(files):
        for ri, r in enumerate(recs):
            lay = str(r.get('layer') or '')
            for f, v in (r.get('attributes') or {}).items():
                if v is None or v == '' or isinstance(v, bool): continue
                n = norm_val(v)
                if not n: continue
                got = whole.get(n)
                if got:
                    for k, ref in got: _hit(hits, vals, shit, shared_ids, wants, (k, lay, f, 'whole value'), ref, (fi, ri), n)
                else:
                    s = strip0(n)
                    got = stripped.get(s) if s != n or (n.isdigit() or True) else None
                    if got and s in stripped:
                        for k, ref in got: _hit(hits, vals, shit, shared_ids, wants, (k, lay, f, 'without leading zeros'), ref, (fi, ri), n)
                if isinstance(v, str) and URLISH.search(v):
                    for kind, rx in ties:
                        m = rx.search(v)
                        if m:
                            c = norm_val(m.group(1))
                            for k, ref in whole.get(c, ()):
                                if k == kind: _hit(hits, vals, shit, shared_ids, wants, (k, lay, f, 'inside a web address (link-id-ties)'), ref, (fi, ri), c)
                    for tok in set(TOKEN.findall(v)):
                        c = norm_val(tok)
                        for k, ref in whole.get(c, ()) or stripped.get(strip0(c), ()):
                            _hit(hits, vals, shit, shared_ids, wants, (k, lay, f, 'inside a web address'), ref, (fi, ri), c)
    return hits, vals, shit


def measure_rows(hits, vals, files, facts, R, geo, shit=None):
    """One row per (id kind, layer, field, way) with at least MIN_PARKS parks hit."""
    shit = shit or {}
    keys = [k for k, refs in hits.items() if len(refs) >= MIN_PARKS] + [k for k in shit if len(shit[k]) >= MIN_PARKS and len(hits.get(k, ())) < MIN_PARKS]
    need = {(k[1], k[2]) for k in keys}
    need_by = defaultdict(list)
    for l_, f_ in need: need_by[l_].append(f_)
    distinct = defaultdict(set)
    where_f = defaultdict(lambda: defaultdict(set))
    for fi, (stem, recs) in enumerate(files):
        for r in recs:
            lay = str(r.get('layer') or '')
            a = r.get('attributes') or {}
            for f in need_by.get(lay, ()):
                v = a.get(f) if f in a else attr(r, f)
                n = norm_val(v)
                if n: distinct[(lay, f)].add(n)
            if lay == 'PAD-US':
                for f in ('Mang_Name', 'Own_Name', 'Mang_Type', 'Own_Type'): where_f[lay][f].add(norm_val(a.get(f)))
    rows = []
    for key in sorted(set(keys), key=lambda k: -len(hits.get(k, ()))):
        kind, lay, field, way = key
        refs = hits.get(key, {})
        nsh = len(shit.get(key, ()))
        recs_hit = {x for s in refs.values() for x in s}
        inside = near = name_ok = 0
        memo = geo.memo
        for ref, rset in refs.items():
            fp = facts.get(ref) or {}
            pin = pin_of(fp)
            pw = real_words(words(fp.get('name'), R), R)
            got_pin = got_near = got_name = False
            for fi, ri in rset:
                rec = files[fi][1][ri]
                mk = (ref, fi, ri)
                if mk not in memo:
                    pn = nr = nm = False
                    g = geo.fast(rec) if pin else None
                    if g:
                        pn = SC.pin_on_land(pin[0], pin[1], [g], R.lim['pin_m']); nr = pn or _near_km(pin, g[0], 5.0)
                    nm = bool(pw & real_words(words(rec.get('record_name'), R) + [w for f in R.name_fields.get(lay, []) for w in words(attr(rec, f), R)], R))
                    memo[mk] = (pn, nr, nm)
                pn, nr, nm = memo[mk]
                got_pin |= pn; got_near |= nr; got_name |= nm
            inside += got_pin; near += got_near or got_pin; name_ok += got_name
        agree = sum(1 for ref, rset in refs.items() if any(memo[(ref, fi, ri)][0] or memo[(ref, fi, ri)][2] for fi, ri in rset))
        two = sum(1 for ref in refs if len(vals[key][ref]) > 1)
        n = len(refs)
        d = len(distinct[(lay, field)])
        if n < MIN_PARKS:
            rows.append({'what': 'id field', 'kind': kind, 'layer': lay, 'field': field, 'way': way, 'parks': n, 'records': 0, 'distinct': d, 'pin_share': 0, 'name_share': 0, 'near5km_share': 0,
                         'agree_share': 0, 'two_values': 0, 'shared_parks': nsh, 'verdict': 'NO', 'reason': f'{nsh} parks hit share one id value with another park (a coincidence or a shared id); the field has {d} different values'})
            continue
        row = {'what': 'id field', 'kind': kind, 'layer': lay, 'field': field, 'way': way, 'parks': n, 'records': len(recs_hit), 'distinct': d, 'shared_parks': nsh,
               'pin_share': round(inside / n, 3), 'name_share': round(name_ok / n, 3), 'near5km_share': round(near / n, 3),
               'agree_share': round(agree / n, 3), 'two_values': two}
        share = agree / n
        reasons = []
        if share < 0.6: reasons.append(f'only {agree} of {n} hit parks have the pin on the land or a place word in common')
        if not (d >= 20 or d >= n): reasons.append(f'the field has only {d} different values for {n} parks hit (a coincidence)')
        if two: reasons.append(f'{two} parks hit two different values')
        if nsh > n: reasons.append(f'{nsh} more parks hit share their id value with another park')
        if lay in R.drop: reasons.append('the rule table drops this layer at load')
        if reasons: row['verdict'], row['reason'] = 'NO', '; '.join(reasons)
        elif share >= 0.8: row['verdict'], row['reason'] = 'PROPOSE', f'{agree} of {n} hit parks agree by pin or name; {d} different values'
        else: row['verdict'], row['reason'] = 'LOOK', f'{agree} of {n} hit parks agree by pin or name (60 to 80 percent): a person decides'
        if lay == 'PAD-US' and row['verdict'] != 'NO':
            for f in ('Mang_Name', 'Own_Name', 'Mang_Type', 'Own_Type'):
                got = {norm_val(attr(files[fi][1][ri], f)) for s in refs.values() for fi, ri in s}
                if len(got) == 1 and len(where_f[lay][f]) >= 3 and '' not in got: row['where'] = {f: next(iter(got))}; break
        rows.append(row)
    return rows


def _near_km(pin, box, km):
    import math
    lat, lon = pin
    dy = max(box[1] - lat, 0, lat - box[3]) * 110.54
    dx = max(box[0] - lon, 0, lon - box[2]) * 111.32 * math.cos(math.radians(lat))
    return math.hypot(dx, dy) <= km


def _agree(ref, rset, files, facts, R, geo):
    fp = facts.get(ref) or {}
    pin = pin_of(fp)
    pw = real_words(words(fp.get('name'), R), R)
    for fi, ri in rset:
        rec = files[fi][1][ri]
        if pin:
            g = geo.fast(rec)
            if g and SC.pin_on_land(pin[0], pin[1], [g], R.lim['pin_m']): return True
        if pw & real_words(words(rec.get('record_name'), R) + [w for f in R.name_fields.get(str(rec.get('layer') or ''), []) for w in words(attr(rec, f), R)], R): return True
    return False


class Geo:
    """Shapes decoded once and kept (the scorecard's own decoder)."""
    def __init__(self): self.c, self.memo = {}, {}

    def fast(self, rec, cap=2500):
        """The same shape with very long rings thinned to about `cap` points (a stride, first and last point kept): for finding the
        records under a pin among huge shapes (a whole park system); the edge is then known to about 100 m."""
        k = ('f', id(rec))
        if k not in self.c:
            g = self.shape(rec)
            if g:
                rings = []
                for ring in g[1]:
                    st = len(ring) // cap
                    rings.append(ring if st < 2 else ring[::st] + ring[-1:])
                g = (g[0], rings)
            self.c[k] = g
        return self.c[k]

    def shape(self, rec):
        k = id(rec)
        if k not in self.c:
            rings = SC.decode_rings(rec)
            if rings:
                xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
                self.c[k] = ((min(xs), min(ys), max(xs), max(ys)), rings)
            else: self.c[k] = None
        return self.c[k]


# ---------------------------------------------------------------- section 3

def agency_fields(recs, layer_recs_by, R):
    """Per layer: fields filled on >= 99% of the records, different on >= 99%, id-like, and not the row number."""
    out = []
    for lay, rs in sorted(layer_recs_by.items()):
        if len(rs) < 10 or lay in ('PAD-US',): continue
        fields = Counter()
        for r in rs:
            for f, v in (r.get('attributes') or {}).items(): fields[f] += 1
        cands = []
        for f, c in fields.items():
            if c < 0.95 * len(rs) or f.lower() in ('globalid',) or re.fullmatch(r'fid|oid|rowid|ogc_fid|objectid\w*|id', f.lower()) or re.search(r'shape|acre|area|length|sqft|sq_|perim|lat|lon|x_|y_|year|date', f.lower()): continue
            vals, same_row, idlike, nonint = [], 0, 0, 0
            for r in rs:
                v = (r.get('attributes') or {}).get(f)
                if v is None or v == '' or isinstance(v, bool): continue
                if isinstance(v, float) and not v.is_integer(): nonint += 1; continue
                n = norm_val(v)
                if not n: continue
                vals.append(n)
                if ID_LIKE.fullmatch(n): idlike += 1
                dg = re.sub(r'\D', '', n)
                if dg and dg.lstrip('0') == str(r.get('record_id') or '').lstrip('0'): same_row += 1
            if not vals or nonint > 0.01 * len(rs) or idlike < 0.95 * len(vals): continue
            fill = len(vals) / len(rs); uniq = len(set(strip0(v) for v in vals)) / len(vals)
            row_like = same_row / len(vals)
            cands.append((f, fill, uniq, row_like))
        good = [c for c in cands if c[1] >= 0.99 and c[2] >= 0.99 and c[3] < 0.5]
        near = [c for c in cands if c[1] >= 0.95 and c[2] >= 0.95 and c[3] < 0.5 and c not in good]
        for f, fill, uniq, row_like in good + near:
            row = {'what': 'agency record id', 'layer': lay, 'field': f, 'parks': '', 'records': len(rs), 'distinct': round(uniq * len(rs) * fill),
                   'agree_share': '', 'fill': round(fill, 4), 'unique': round(uniq, 4), 'row_like': round(row_like, 3)}
            tbl = R.rec_fields.get(lay)
            if (f, fill, uniq, row_like) in near: row['verdict'], row['reason'] = 'LOOK', f'filled {fill:.1%}, different {uniq:.1%}: not quite 99 percent'
            elif tbl and tbl.lower() == f.lower(): row['verdict'], row['reason'] = 'IN TABLE', 'already the table\'s field for this layer'
            elif tbl: row['verdict'], row['reason'] = 'LOOK', f"the table already uses {tbl} for this layer; {f} also fits"
            elif len(good) > 1: row['verdict'], row['reason'] = 'LOOK', f'{len(good)} fields fit this layer: a person picks one'
            else: row['verdict'], row['reason'] = 'PROPOSE', f'filled {fill:.1%}, different {uniq:.1%}, not the row number'
            out.append(row)
    return out


# ---------------------------------------------------------------- sections 4 and 4b

def record_names(rec, R):
    lay = str(rec.get('layer') or '')
    names = [rec.get('record_name')] + [attr(rec, f) for f in R.name_fields.get(lay, [])]
    return [str(n) for n in names if n not in (None, '') and str(n).strip().lower() not in ('n/a', 'none', 'null')]


def full_names(rec, R):
    lay = str(rec.get('layer') or '')
    out = []
    for combo in R.full_fields.get(lay, []):
        vals = [attr(rec, f) for f in combo]
        vals = [str(v).strip() for v in vals if v not in (None, '')]
        if vals: out.append(' '.join(vals))
    return out


def build_grid(recs, geo):
    cell, big = defaultdict(list), []
    for i, r in enumerate(recs):
        g = geo.shape(r)
        if not g: continue
        b = g[0]
        x0, x1, y0, y1 = int(b[0] * 10) - 1, int(b[2] * 10) + 1, int(b[1] * 10) - 1, int(b[3] * 10) + 1
        if (x1 - x0 + 1) * (y1 - y0 + 1) > 400: big.append(i); continue
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1): cell[(x, y)].append(i)
    return cell, big


def under_pin(pin, recs, grid, geo, pin_m):
    """The records that hold the pin: inside first; only when none is inside, the ones within the pin allowance of the edge."""
    cell, big = grid
    cand = sorted(set(cell.get((int(pin[1] * 10), int(pin[0] * 10)), ())) | set(big))
    boxed = []
    for i in cand:
        g = geo.fast(recs[i])
        if not g: continue
        bx = g[0]
        if bx[0] - 0.003 <= pin[1] <= bx[2] + 0.003 and bx[1] - 0.003 <= pin[0] <= bx[3] + 0.003: boxed.append((i, g))
    inside = [i for i, g in boxed if g[0][0] <= pin[1] <= g[0][2] and g[0][1] <= pin[0] <= g[0][3] and SC._inside(pin[1], pin[0], g[1])]
    if inside: return inside
    return [i for i, g in boxed if SC.pin_on_land(pin[0], pin[1], [g], pin_m)]


def best_name(pota, rec_idx, recs, R):
    """The record under the pin whose name is closest to POTA's; returns (record index, name, verdict, pattern, full-name verdict row) or None."""
    best = None
    for i in rec_idx:
        for nm in record_names(recs[i], R):
            v, pat = compare_names(pota, nm, R)
            k = rank(v, pat)
            if best is None or k < best[0]: best = (k, i, nm, v, pat)
    if best is None: return None
    return best[1], best[2], best[3], best[4]


def name_study(refs, facts, files_own, R, geo, v2dir, st):
    """Sections 4 and 4b. Returns (unproven stats, 4b rows, patterns)."""
    recs = files_own
    grid = build_grid(recs, geo)
    nkeys = set()
    for r in recs:
        for nm in record_names(r, R): nkeys.add(''.join(words(nm, R)))
    unproven = None
    if v2dir:
        rows = SC.read_csv(pathlib.Path(v2dir) / 'v2-pin-only.csv')
        if rows is not None: unproven = {r.get('ref') for r in rows if r.get('st') in (st, None, '')}
    rows4, rows4b = [], []
    for ref in refs:
        fp = facts.get(ref) or {}
        pota = fp.get('name') or ''
        pin = pin_of(fp)
        under = under_pin(pin, recs, grid, geo, R.lim['pin_m']) if pin else []
        is_unproven = (ref in unproven) if unproven is not None else (''.join(words(pota, R)) not in nkeys)
        bn = best_name(pota, under, recs, R) if under else None
        if is_unproven:
            if not pin: rows4.append({'ref': ref, 'pota': pota, 'pattern': 'the park has no pin', 'record': ''})
            elif not under or not bn: rows4.append({'ref': ref, 'pota': pota, 'pattern': 'no record under the pin at all', 'record': ''})
            else:
                _i, nm, v, pat = bn
                rows4.append({'ref': ref, 'pota': pota, 'pattern': ('same after the table rules: ' + pat) if v == 'after rules' else ('already the same name' if v == 'same' else pat), 'record': nm})
        # 4b: three sources
        srcs = []
        pg = fp.get('page') or {}
        lk = fp.get('link') or {}
        own = pg.get('own_page') == 'own' and not pg.get('unofficial')
        names_page = [x for x in ([pg.get('name_on_page')] + list(pg.get('names') or [])) if x]
        if own:
            for nm in names_page:
                v, pat = compare_names(pota, nm, R)
                if v == 'differs' and not (real_words(words(pota, R), R) & real_words(words(nm, R), R)): v, pat = 'junk', 'page title is not a name'
                srcs.append(('page', nm, v, pat))
        if lk.get('usable') and lk.get('page_kind') == 'own page' and lk.get('web_name'):
            v, pat = compare_web(pota, lk['web_name'], R)
            if v == 'differs' and pat == 'a completely different name': v, pat = 'junk', 'page title is not a name'
            srcs.append(('web address', lk['web_name'], v, pat))
        if bn:
            i, nm, v, pat = bn
            srcs.append(('record under pin', nm, v, pat))
            fv = None
            for fn in full_names(recs[i], R):
                v2, p2 = compare_names(pota, fn, R)
                if fv is None or rank(v2, p2) < rank(fv[2], fv[3]): fv = ('record full name', fn, v2, p2)
            if fv: srcs.append(fv)
        for s, nm, v, pat in srcs: rows4b.append({'ref': ref, 'pota': pota, 'source': s, 'official': nm, 'verdict': v, 'pattern': pat})
    return rows4, rows4b


def two_source_rows(rows4b, R):
    """Parks where TWO official sources agree with each other but differ from POTA (verdict 'differs', not a junk title)."""
    by = defaultdict(list)
    for r in rows4b:
        if r['verdict'] == 'differs': by[r['ref']].append(r)
    out = []
    for ref, rs in sorted(by.items()):
        keys = [{nkey(r['official']), ''.join(core(words(r['official'], R), R))} - {''} for r in rs]
        best = None
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                if rs[i]['source'] != rs[j]['source'] and keys[i] & keys[j]: best = (i, j)
                if best: break
            if best: break
        if best:
            a, b = rs[best[0]], rs[best[1]]
            pick = min((a, b), key=lambda r: {'page': 0, 'record full name': 1, 'record under pin': 2, 'web address': 3}.get(r['source'], 4))
            out.append({'ref': ref, 'pota': a['pota'], 'official': pick['official'], 'sources': [a['source'], b['source']],
                        'why': f"two official sources write the name the same way and POTA writes it another way ({pick['pattern']}); measured {datetime.date.today():%d %b %Y}",
                        'test': 'TODO', 'verdict': 'LOOK'})
    return out


# ---------------------------------------------------------------- the run

_SHARED = {}


def _squeeze(d):
    """json object hook: a record's rings (lists of numbers, about 36 bytes a number) become one compact text, as soon as the record is read.
    The scorecard's decoder reads that text too. This keeps a 37 MB layer file from needing 1.6 GB."""
    # one copy of each field name (as json.load does for a whole file) and of each short repeated text value
    d = {sys.intern(k): (_SHARED.setdefault(v, v) if isinstance(v, str) and len(v) <= 40 else v) for k, v in d.items()}
    rg = d.get('rings')
    if isinstance(rg, list) and rg and isinstance(rg[0], list): d['rings'] = json.dumps(rg, separators=(',', ':'))
    return d


def load_compact(p):
    """The layer file, read once, in pieces: the records are read one at a time (rings squeezed as each is read) so the whole text of the
    file is never held. Same result as json.load. None when the file is not there or not readable."""
    try:
        with gzip.open(pathlib.Path(p), 'rt', encoding='utf-8') as f: return _stream(f)
    except (OSError, ValueError): return None


def _stream(f, step=1 << 22):
    dec = json.JSONDecoder(object_hook=_squeeze)
    buf, pos, eof = '', 0, False

    def more():
        nonlocal buf, pos, eof
        chunk = f.read(step)
        if not chunk: eof = True; return
        buf = buf[pos:] + chunk; pos = 0

    def skip():
        nonlocal pos
        while True:
            while pos < len(buf) and buf[pos] in ' \t\r\n,': pos += 1
            if pos < len(buf) or eof: return
            more()

    def value():
        nonlocal pos
        while True:
            skip()
            try:
                v, end = dec.raw_decode(buf, pos); pos = end; return v
            except ValueError:
                if eof: raise
                more()
    skip()
    if not buf[pos:pos + 1] == '{':
        more(); skip()
    if buf[pos:pos + 1] != '{': raise ValueError('not an object')
    pos += 1; out = {}
    while True:
        skip()
        if pos >= len(buf): raise ValueError('cut short')
        if buf[pos] == '}': return out
        k = value(); skip()
        if buf[pos] != ':': raise ValueError('no colon')
        pos += 1; skip()
        if k == 'records' and buf[pos] == '[':
            pos += 1; recs = []
            while True:
                skip()
                if buf[pos] == ']': pos += 1; break
                recs.append(value())
            out[k] = recs
        else: out[k] = value()


def run(st, store, facts_file, v2dir, out_parent, repo, now=None, flat=False):
    t0 = time.time()
    R = Rules(repo)
    facts = (SC.load_json(facts_file) or {}).get('parks') or {}
    keep = {f'US-{st}'} | {f'US-{x}' for x in str(R.neighbours.get(st, '')).split()}
    lines, notes = [], []
    if not R.found: notes.append('the rule table (us-key-v2-rules.json) was not found: defaults and no table rows to compare with')
    if R.lim_note: notes.append(R.lim_note)
    refs, n = park_refs(repo, st, facts)
    if n: notes.append(n)
    rset = set(refs)
    facts = {r: p for r, p in facts.items() if r in rset or str((p or {}).get('area') or '') in keep}    # other states' parks are never looked at
    docs = {}
    stems = [f'US-{st}'] + [f'US-{x}' for x in sorted(str(R.neighbours.get(st, '')).split())]
    for s in stems:
        d = load_compact(pathlib.Path(store) / f'{s}.layer-records.json.gz')
        if isinstance(d, dict): docs[s] = d
    _SHARED.clear()
    own = docs.get(f'US-{st}')
    rep = pathlib.Path(out_parent) if flat else pathlib.Path(out_parent) / f'v2-prep-{st}-{(now or datetime.datetime.now()):%Y-%m-%d-%H%M%S}'
    rep.mkdir(parents=True, exist_ok=True)
    details, proposed = [], {'about': 'PROPOSED rows only, from measurements. Nothing here is in the real rule table. A person decides each row; every row needs its why and its test.',
                             'state': st, 'tables': {}, 'link_id_ties': [], 'other_spellings': [], 'name_candidates': []}
    L = [f'KPC v2 state prep for {st}, {datetime.datetime.now():%d %b %Y %I:%M %p}. Saved copies only. Counts only, no park names.']
    if own is None:
        msg = f'{st}: the layer file US-{st}.layer-records.json.gz was not found in {store}. Nothing was measured.'
        (rep / f'STATE-PREP-{st}.txt').write_text('\n'.join(L + [msg]) + '\n', encoding='utf-8')
        print(msg); return 2, rep
    # 1
    srows, gaps = store_room(own, R, st)
    nb_gaps = []
    for s, d in docs.items():
        if s != f'US-{st}':
            for r in store_room(d, R, s)[0]:
                if not r['complete']: nb_gaps.append(f"{s} {r['layer']}")
    for s in stems[1:]:
        if s not in docs: nb_gaps.append(f'{s}: no file')
    for r in srows: details.append(dict(section='1 store room', **{'what': 'layer', 'layer': r['layer'], 'verdict': 'complete' if r['complete'] else 'NOT COMPLETE',
        'reason': r['why'], 'records': r['records'], 'note': f"no shape {r['no_shape']}; repeated keys {r['repeat_keys']}; not in manifest {r['not_in_manifest']}; dropped by the table {r['dropped']}"}))
    verdict = f'v2 can build {st}' if not gaps else f'v2 cannot build {st} until: {", ".join(gaps)}'
    L += ['', '1. STORE ROOM', f"  {len(srows)} layers, {sum(r['records'] for r in srows)} records, {sum(r['no_shape'] for r in srows)} with no shape, "
          f"{sum(r['repeat_keys'] for r in srows)} row keys that repeat, {sum(1 for r in srows if r['not_in_manifest'])} layers not in the manifest.",
          f'  {verdict}.' + (f' Neighbour gaps (they do not stop {st}): {len(nb_gaps)}.' if nb_gaps else '')]
    # shapes of the own file
    files = [(s, docs[s].get('records') or []) for s in stems if s in docs]
    geo = Geo()
    # 2
    wants = build_wants(refs, facts)
    kinds = Counter(k for d in wants.values() for k in d)
    link_ties = (SC.load_json(pathlib.Path(repo) / '.github' / 'link-id-ties.json') or {}).get('ties') or []
    hits, vals, shit = find_id_hits(files, wants, link_ties)
    idrows = measure_rows(hits, vals, files, facts, R, geo, shit)
    for r in idrows: details.append(dict(section='2 id fields', **r))
    cnt = Counter(r['verdict'] for r in idrows)
    got_kinds = {r['kind'] for r in idrows if r['verdict'] in ('PROPOSE', 'LOOK')}
    nofield = [(k, c) for k, c in kinds.most_common() if k not in got_kinds]
    L += ['', '2. ID FIELDS', f"  {sum(kinds.values())} parks with an id, {len(kinds)} id kinds. Rows measured (3 parks or more hit): {len(idrows)}: "
          f"PROPOSE {cnt['PROPOSE']}, LOOK {cnt['LOOK']}, NO {cnt['NO']}."]
    L += [f'  {k}: {c} parks, no field found.' for k, c in nofield[:8]]
    ties = []
    for r in idrows:
        if r['verdict'] not in ('PROPOSE', 'LOOK'): continue
        meas = f"{st}: {r['parks']} parks, {r['records']} records; pin on the land {round(r['pin_share'] * r['parks'])} of {r['parks']}, within 5 km {round(r['near5km_share'] * r['parks'])}, place word in common {round(r['name_share'] * r['parks'])}; {r['distinct']} different values in the field"
        if r['way'].startswith('inside a web address (link-id-ties)'): continue
        if r['way'] == 'inside a web address':
            have = any(x.get('kind') == r['kind'] and x.get('layer') == r['layer'] and str(x.get('field')).lower() == r['field'].lower() for x in link_ties)
            proposed['link_id_ties'].append({'kind': r['kind'], 'layer': r['layer'], 'field': r['field'], 'rx': 'TODO: write the address pattern',
                'measured': meas, 'why': r['reason'], 'test': 'TODO', 'verdict': r['verdict'] + (' (already in link-id-ties.json)' if have else '')}); continue
        row = {'kind': r['kind'], 'layer': r['layer'], 'field': r['field']}
        if r.get('where'): row['where'] = r['where']
        row.update({'measured': meas, 'why': r['reason'], 'way': r['way'], 'test': 'TODO', 'verdict': r['verdict'], 'parks_hit': r['parks']})
        if not any(t.get('kind') == row['kind'] and t.get('layer') == row['layer'] and t.get('field', '').lower() == row['field'].lower() for t in ties): ties.append(row)
    for t in ties:
        if any(x.get('kind') == t['kind'] and x.get('layer') == t['layer'] and str(x.get('field')).lower() == t['field'].lower() for x in R.id_ties): t['verdict'] += ' (already in the table)'
    proposed['tables']['id_ties'] = {'value': ties}
    # 3
    by_layer = defaultdict(list)
    for r in own.get('records') or []: by_layer[str(r.get('layer') or '')].append(r)
    arows = agency_fields(own.get('records') or [], by_layer, R)
    for r in arows: details.append(dict(section='3 agency record ids', **r))
    ac = Counter(r['verdict'] for r in arows)
    L += ['', '3. AGENCY RECORD IDS (for locks and published ids)', f"  Fields measured: {len(arows)}: PROPOSE {ac['PROPOSE']}, LOOK {ac['LOOK']}, already in the table {ac['IN TABLE']}."]
    proposed['tables']['record_id_fields'] = {'value': {r['layer']: r['field'] for r in arows if r['verdict'] == 'PROPOSE'},
                                              'why': 'filled on 99 percent of the records, different on 99 percent, not the row number', 'test': 'TODO'}
    # 4 / 4b
    recs_own = own.get('records') or []
    rows4, rows4b = name_study(refs, facts, recs_own, R, geo, v2dir, st)
    pats = Counter(r['pattern'] for r in rows4)
    for p, c in pats.items():
        ex = [r for r in rows4 if r['pattern'] == p][:3]
        details.append({'section': '4 name patterns', 'what': 'pattern', 'reason': p, 'parks': c, 'verdict': 'LOOK',
                        'examples': ' | '.join(f"{e['ref']}: {e['pota']} / {e['record']}" for e in ex)})
        if not p.startswith('no record under') and not p.startswith('the park has no'): proposed['name_candidates'].append({'pattern': p, 'parks': c, 'why': 'measured on parks the matcher left unproven', 'test': 'TODO', 'verdict': 'LOOK'})
    # second full-name field candidates
    full_fields = []
    for lay, rs in sorted(by_layer.items()):
        if lay in R.full_fields or len(rs) < 10: continue
        cnt_f = Counter()
        for r in rs[:2000]:
            nm = words(r.get('record_name'), R)
            if not nm: continue
            for f, v in (r.get('attributes') or {}).items():
                if isinstance(v, str):
                    w = words(v, R)
                    if len(w) > len(nm) and w[:len(nm)] == nm and any(x in R.kind_set for x in w[len(nm):]): cnt_f[f] += 1
        for f, c in cnt_f.items():
            if c >= 0.5 * min(len(rs), 2000): full_fields.append((lay, f, c / min(len(rs), 2000)))
    for lay, f, sh in full_fields:
        details.append({'section': '4 name fields', 'what': 'second full-name field', 'layer': lay, 'field': f, 'agree_share': round(sh, 3), 'verdict': 'LOOK', 'reason': 'holds the record name plus a kind word'})
        proposed['tables'].setdefault('full_name_fields', {'value': {}, 'why': 'a longer name with the kind word', 'test': 'TODO'})['value'].setdefault(lay, []).append([f])
    L += ['', '4. NAME STYLES (parks the matcher would leave unproven' + (', from the v2 run' if v2dir else ', no exact record name') + ')']
    nogap = sum(c for p, c in pats.items() if p.startswith('no record under') or p.startswith('the park has no'))
    L += [f'  {len(rows4)} unproven parks. {nogap} have no record under the pin at all (a store room gap or a pin problem, counted apart).']
    for p, c in [x for x in pats.most_common() if not (x[0].startswith('no record under') or x[0].startswith('the park has no'))][:6]: L.append(f'  {c:4d}  {p}')
    L += [f'  Second full-name fields found: {len(full_fields)}. Every name pattern is a LOOK: a name rule needs a person\'s yes.']
    # 4b
    srcn = ('page', 'web address', 'record under pin', 'record full name')
    L += ['', "4b. OFFICIAL NAMES AGAINST POTA'S NAMES"]
    for s in srcn:
        rs = [r for r in rows4b if r['source'] == s]
        parks_with = len({r['ref'] for r in rs})
        c = Counter(r['verdict'] for r in rs)
        L.append(f"  {s}: {parks_with} parks have a name; same {c['same']}, same after rules {c['after rules']}, differs {c['differs']}" + (f", address is not a name {c['junk']}" if s == 'web address' else f", title is not a name {c['junk']}" if s == 'page' else '') + '.')
    dp = Counter(r['pattern'] for r in rows4b if r['verdict'] == 'differs')
    L.append('  Differences, most common first:')
    for p, c in dp.most_common(7): L.append(f'  {c:4d}  {p}')
    two = two_source_rows(rows4b, R)
    proposed['other_spellings'] = two
    L.append(f'  Parks where two official sources agree with each other but differ from POTA: {len(two)}.')
    L.append('  An other-spelling row only says this is another way to write the park\'s name. The pin or the size must still prove the land.')
    # 5
    L += ['', '5. WHAT TO DO NEXT',
          f'  1. Fix the store room gaps first' + (f' ({", ".join(gaps)})' if gaps else ' (none)') + '.',
          '  2. Copy the real rule table. Add the PROPOSE rows from proposed-rows.json (each needs its why and its test). Look at the LOOK rows.',
          f'  3. Run the workbench: py -3.12 kpc_test_v2.py {st} --try <the copy>. Read which parks change.',
          '  4. A row goes into the real table only with its why and its test, in a PR. The matcher does not read other_spellings yet.']
    for n_ in notes: L.append(f'  Note: {n_}.')
    L.append(f'  ({time.time() - t0:.0f} s)')
    gen = Counter()
    for p_, c_ in pats.items():
        if not (p_.startswith('no record under') or p_.startswith('the park has no')): gen[p_.split(':')[0]] += c_
    proposed['counts'] = {'parks': len(refs), 'with_id': sum(1 for d_ in wants.values() if d_), 'can_build': not gaps, 'blockers': list(gaps), 'unproven': len(rows4),
                          'id_propose': cnt['PROPOSE'], 'id_look': cnt['LOOK'], 'id_no': cnt['NO'], 'patterns': dict(gen), 'seconds': round(time.time() - t0, 1)}
    # files
    (rep / f'STATE-PREP-{st}.txt').write_text('\n'.join(L) + '\n', encoding='utf-8')
    (rep / 'proposed-rows.json').write_text(json.dumps(proposed, indent=1, ensure_ascii=False, sort_keys=True), encoding='utf-8')
    cols = ['section', 'what', 'kind', 'layer', 'field', 'way', 'where', 'parks', 'records', 'distinct', 'pin_share', 'name_share', 'near5km_share', 'agree_share',
            'two_values', 'fill', 'unique', 'row_like', 'verdict', 'reason', 'note', 'examples']
    with open(rep / 'prep-details.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader()
        for d in details:
            d = dict(d)
            if 'where' in d: d['where'] = json.dumps(d['where'])
            w.writerow(d)
    with open(rep / 'name-compare.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['ref', 'pota', 'source', 'official', 'verdict', 'pattern']); w.writeheader(); w.writerows(rows4b)
    print('\n'.join(L)); print(f'\nThe report is {rep / ("STATE-PREP-" + st + ".txt")}')
    return 0, rep


STATE_FILE = re.compile(r'^US-([A-Z]{2})\.layer-records\.json\.gz$')


def store_states(store):
    """Every state with a layer file in the store folder (US-<ST>.layer-records.json.gz), sorted."""
    return sorted(m.group(1) for f in pathlib.Path(store).iterdir() for m in [STATE_FILE.match(f.name)] if m) if pathlib.Path(store).is_dir() else []


def parse_states(tokens, store):
    """(states, is_many). US or ALL = every state with a layer file."""
    toks = [t.upper() for x in tokens for t in re.split(r'[,\s;]+', str(x)) if t]
    if any(t in ('US', 'ALL') for t in toks):
        return store_states(store), True
    out = []
    for t in toks:
        if t not in out: out.append(t)
    return out, len(out) > 1


def child_prep(st, out, store, facts, repo, v2):
    """One state in its own process (memory is given back when it ends). Returns (exit code, output text)."""
    cmd = [sys.executable, '-X', 'utf8', str(pathlib.Path(__file__).resolve()), st, '--out', str(out), '--store', str(store), '--facts', str(facts), '--repo', str(repo), '--flat']
    if v2: cmd += ['--v2', str(v2)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def _gen(p): return p.split(':')[0]


def merge_rows(per_state):
    """per_state = {ST: proposed-rows dict}. Identical rows of several states appear once, with all their states and summed counts."""
    def add(table, key, row, st, n=0):
        if key not in table: table[key] = dict(row, states=[], parks_hit=0)
        e = table[key]
        if st not in e['states']: e['states'].append(st)
        e['parks_hit'] += n
        e.setdefault('measured_by_state', {})
    out = {'id_ties': {}, 'link_id_ties': {}, 'record_id_fields': {}, 'full_name_fields': {}, 'name_candidates': {}}
    other = []
    for st, pr in per_state.items():
        for kind in ('id_ties', 'link_id_ties'):
            rows = (pr.get('tables', {}).get('id_ties', {}).get('value') if kind == 'id_ties' else pr.get('link_id_ties')) or []
            for r in rows:
                if not str(r.get('verdict', '')).startswith(('PROPOSE', 'LOOK')): continue
                key = (r.get('kind'), r.get('layer'), str(r.get('field')).lower(), r.get('way', ''), json.dumps(r.get('where'), sort_keys=True))
                add(out[kind], key, {k: v for k, v in r.items() if k not in ('measured', 'parks_hit')}, st, int(r.get('parks_hit') or 0))
                out[kind][key]['measured_by_state'][st] = r.get('measured', '')
        for lay, f in ((pr.get('tables', {}).get('record_id_fields') or {}).get('value') or {}).items():
            add(out['record_id_fields'], (lay, str(f).lower()), {'layer': lay, 'field': f, 'verdict': 'PROPOSE', 'why': 'filled on 99 percent of the records, different on 99 percent, not the row number', 'test': 'TODO'}, st)
        for lay, fl in ((pr.get('tables', {}).get('full_name_fields') or {}).get('value') or {}).items():
            for f in fl:
                f = f[0] if isinstance(f, list) else f
                add(out['full_name_fields'], (lay, str(f).lower()), {'layer': lay, 'field': f, 'verdict': 'LOOK', 'why': 'holds the record name plus a kind word', 'test': 'TODO'}, st)
        for c in pr.get('name_candidates') or []:
            add(out['name_candidates'], _gen(c['pattern']), {k: v for k, v in c.items() if k not in ('parks', 'pattern')} | {'pattern': _gen(c['pattern'])}, st, int(c.get('parks') or 0))
        other += [dict(x, state=st) for x in pr.get('other_spellings') or []]
    res = {'about': 'PROPOSED rows only, every state together. Nothing here is in the real rule table. A row found in several states appears once with all its states. '
                    'A person decides each row; every row needs its why and its test.', 'states': sorted(per_state)}
    for k, v in out.items(): res[k] = sorted(v.values(), key=lambda e: (-len(e['states']), -e['parks_hit']))
    res['other_spellings'] = other
    return res


NEXT = ['  1. Fix the store room gaps first (the layers named above).',
        '  2. Copy the real rule table. Add the PROPOSE rows from proposed-rows-all.json (each needs its why and its test). Look at the LOOK rows.',
        '  3. Run the workbench: py -3.12 kpc_test_v2.py <states> --try <the copy>. Read which parks change.',
        '  4. A row goes into the real table only with its why and its test, in a PR. The matcher does not read other_spellings yet.']


def many(states, label, store, facts, repo, v2, out_parent, now=None, call=None, say=print):
    """Several states, one after another, each in its own process. Returns (exit code, parent folder)."""
    call = call or child_prep
    parent = pathlib.Path(out_parent) / f'v2-prep-{label}-{(now or datetime.datetime.now()):%Y-%m-%d-%H%M%S}'
    parent.mkdir(parents=True, exist_ok=True)
    res, failed, proposed, t0 = {}, {}, {}, time.time()
    for i, st in enumerate(states, 1):
        t1 = time.time()
        sub = parent / st
        if not (pathlib.Path(store) / f'US-{st}.layer-records.json.gz').is_file():
            failed[st] = 'the layer file was not found'
        else:
            sub.mkdir(parents=True, exist_ok=True)
            try: rc, text = call(st, sub, store, facts, repo, v2)
            except Exception as e: rc, text = 1, f'could not start the child: {e!r}'
            pj = sub / 'proposed-rows.json'
            if rc == 0 and pj.is_file():
                try:
                    proposed[st] = json.loads(pj.read_text(encoding='utf-8')); res[st] = proposed[st].get('counts') or {}
                except ValueError: rc = 1; text += '\nproposed-rows.json could not be read'
            if st not in res:
                (sub / 'prep-error.txt').write_text(f'Exit code {rc}\n{text[-6000:]}', encoding='utf-8')
                failed[st] = f'the prep stopped with an error, see {st}\\prep-error.txt'
        say(f'{i} of {len(states)}  {st}  {time.time() - t1:.0f} s' + ('' if st not in failed else f'  ({failed[st]})'))
    L = summary_text(states, res, failed, time.time() - t0)
    (parent / 'STATE-PREP-SUMMARY.txt').write_text('\n'.join(L) + '\n', encoding='utf-8')
    cols = ['state', 'can_build', 'blockers', 'parks', 'with_id', 'id_propose', 'id_look', 'id_no', 'unproven', 'top_pattern', 'top_pattern_parks', 'seconds', 'problem']
    with open(parent / 'summary.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for st in states:
            c = res.get(st)
            if c is None: w.writerow({'state': st, 'problem': failed.get(st, '')}); continue
            tp = top_pattern(c)
            w.writerow({'state': st, 'can_build': 'yes' if c.get('can_build') else 'no', 'blockers': ' '.join(c.get('blockers') or []), 'parks': c.get('parks'), 'with_id': c.get('with_id'),
                        'id_propose': c.get('id_propose'), 'id_look': c.get('id_look'), 'id_no': c.get('id_no'), 'unproven': c.get('unproven'),
                        'top_pattern': tp[0], 'top_pattern_parks': tp[1], 'seconds': c.get('seconds')})
    (parent / 'proposed-rows-all.json').write_text(json.dumps(merge_rows(proposed), indent=1, ensure_ascii=False, sort_keys=True), encoding='utf-8')
    pat, pst = Counter(), defaultdict(set)
    for st, c in res.items():
        for p_, n in (c.get('patterns') or {}).items(): pat[p_] += n; pst[p_].add(st)
    with open(parent / 'name-patterns-all.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f); w.writerow(['pattern', 'parks', 'states'])
        for p_, n in pat.most_common(): w.writerow([p_, n, len(pst[p_])])
    say('\n'.join(L[:12])); say(f'\nThe report is {parent / "STATE-PREP-SUMMARY.txt"}')
    return (2 if not res else 1 if failed else 0), parent


def top_pattern(c):
    p = sorted(((n, p_) for p_, n in (c.get('patterns') or {}).items()), key=lambda x: (-x[0], x[1]))
    return (p[0][1], p[0][0]) if p else ('', 0)


def summary_text(states, res, failed, secs):
    ok = [s for s in states if s in res and res[s].get('can_build')]
    no = [s for s in states if s in res and not res[s].get('can_build')]
    block = Counter(b for s in no for b in res[s].get('blockers') or [])
    L = [f'v2 can build {len(ok)} of {len(states)} states today.',
         f'v2 cannot build {len(no)}' + (': blocked by ' + ', '.join(f'{b} ({n})' for b, n in block.most_common(8)) + ('' if len(block) <= 8 else ', ...') if no else '') + '.']
    if failed: L.append(f'{len(failed)} states could not be measured (listed below).')
    L.append('')
    for s in states:
        c = res.get(s)
        if c is None: L.append(f'{s}  {failed.get(s, "not measured")}'); continue
        bl = c.get('blockers') or []
        b = 'can build' if c.get('can_build') else 'cannot build (' + ', '.join(bl[:3]) + (', ...' if len(bl) > 3 else '') + ')'
        tp = top_pattern(c)
        L.append(f"{s}  {b}  parks {c.get('parks')}  with an id {c.get('with_id')}  id rows PROPOSE {c.get('id_propose')} LOOK {c.get('id_look')}  unproven {c.get('unproven')}"
                 + (f'  top name pattern: {tp[0]} ({tp[1]})' if tp[1] else ''))
    tot = lambda k: sum(int(res[s].get(k) or 0) for s in res)
    L += ['', f"Totals over {len(res)} states: parks {tot('parks')}, with an id {tot('with_id')}, id rows PROPOSE {tot('id_propose')} LOOK {tot('id_look')}, unproven {tot('unproven')}. ({secs:.0f} s)",
          'Files: summary.csv, proposed-rows-all.json, name-patterns-all.csv, and a folder per state with its own report.', '', 'WHAT TO DO NEXT'] + NEXT
    return L


def main(argv=None, here=None):
    here = pathlib.Path(here or HERE)
    ap = argparse.ArgumentParser(description='Measure states and propose rule-table rows. One state, several (MN NY SC), or US / ALL for every state in the store folder.')
    ap.add_argument('states', nargs='*'); ap.add_argument('--store'); ap.add_argument('--facts'); ap.add_argument('--v2'); ap.add_argument('--out'); ap.add_argument('--repo')
    ap.add_argument('--flat', action='store_true', help='write the four files straight into --out (used for each state of a several-state run)')
    a = ap.parse_args(argv)
    links = pathlib.Path(a.repo) if a.repo else T.find_links(here)
    store = pathlib.Path(a.store) if a.store else T.find_store(here)
    facts = pathlib.Path(a.facts) if a.facts else T.find_facts(here, links)
    toks = a.states or [input('States (for example SC, or MN NY SC, or US for every state): ').strip() or 'SC']
    for what, p in (('the layer files folder', store), ('the park facts', facts)):
        if not p.exists(): print(f'Not found: {what} ({p}). Nothing was run.'); return 2
    states, is_many = parse_states(toks, store)
    if not states: print(f'No state to run: no US-<ST>.layer-records.json.gz in {store}. Nothing was run.'); return 2
    out = pathlib.Path(a.out) if a.out else here / 'reports'
    if not is_many: return run(states[0], store, facts, a.v2, out, links, flat=a.flat)[0]
    label = 'US' if any(str(t).upper() in ('US', 'ALL') for t in toks) else '-'.join(states)
    return many(states, label, store, facts, links, a.v2, out)[0]


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
