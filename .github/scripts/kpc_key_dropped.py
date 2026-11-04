#!/usr/bin/env python3
"""KPC dropped-parks lists after a key build (links-07, Nov 4 2026, Mapping; per Brandon via Super Head Bot (relayed), 6:05 AM CST
Nov 4, the dropped-parks part, his words: "I do not need to know about every single park being dropped that is a sign of the system working. Now if it is a real issues then yes. Any park dropped needs to be put on a list separated list by reason. Pin to far, name mismatch etc... no boundary parks should be kept separate I have ran several sweeps looking for layers we may not find them all and that is where the tracer comes in. I will later though do another search for them. Our list of rejections I think we need to maybe use the answer key or something similar where we have all the information we have to help me or the agent solve the issue."
What this does: the post-key check writes the parks each build DROPS, split by reason, each row carrying everything we know so a
person or an agent can solve it from the row alone). READ-ONLY and OFFLINE like kpc_key_postcheck.py (links-01, unchanged): it reads only
this checkout, git history, the KPC-Data answer sheet copy and the pre-check output. Never moves a POTA pin, never edits a key file.

A DROPPED park = a park the new key has with NO outline (g 'pin' / no joined record). Each one gets ONE reason (the first that
fits, in REASONS order) plus every reason that fits (all_reasons). The reasons are the key builders' own words (kpc_us_key.py,
kpc_ca_key.py, kpc_world_key.py candidate reasons, kpc_precheck.py flags, why-not.json tags, overrides.json):
  joined_in_other_area    the park's land is joined in another state's key file ('joined_in', or an outline there): not a real drop
  pota_bad_pin      POTA 0,0 / impossible / missing pin (POTA's error; never moved)
  override_no       a person's 'no' / 'none' in overrides.json, or a person's signed NO / PIN row on the answer sheet (Brandon / KZ4CP, dated after the 9:37 AM CST Nov 2 restart)
  rule18_doubt      rule 18 / doubt / review pile: 'held ...' candidates, 'record also joined to ...', 'check: a small site ...',
                    'same name, more than one kind of area', pre-check HOLD / RULE18, why-not 'pin-doubt'
  pin_too_far       'same name far from the pin, no join at the pin' (the record is there, the pin is not near it)
  wrong_kind        'same name, different kind of place'
  name_mismatch     'similar name' (no exact match), why-not 'name-mismatch'
  inside_other_land 'the POTA pin is inside it (different name)' only, why-not 'needs-parcel' (the pin sits in bigger land)
  private_or_picture_map  why-not 'private' / 'picture-map-only'
  no_boundary       nothing found at all: no candidate, no record at the pin (its own list, no-boundary.csv)

Writes data/status/key-check/<key>-<build>/dropped/<reason>.csv (one per reason, header-only when empty), no-boundary.csv and
index.json (counts, columns, files, the jump check), and adds a count table to data/status/key-check/<key>-<build>.md.
No per-park notices: one summary notice; a ::warning only for a real system problem (a sudden jump in drops, a whole area going
to pins, key files that do not read). Exit code is always 0 (never fails a build).

Distance and kind from the pre-check (6:49 AM CST Nov 4 ask, relayed via Super Head Bot): pre_km / pre_km_what / pre_kind /
pre_kind_why are joined BY REF from the latest kpc_precheck.py output in PRECHECK_OUT (scorecard.csv flags + why: WRONG_KIND with
its layer-kind reason, PIN_WAY_OUT; county.csv 'km to listed'). Nothing is worked out here and no key rule changes. A blank cell
says why in pre_blank_reason: 'no precheck output' (no scorecard.csv), 'precheck older than build' (scorecard.csv older than the
build's 'built' time: a stale run is not used), 'no precheck row', or what the pre-check row lacks.

  KEY / WORKFLOW_NAME, OUT_DIR, ANSWER_SHEET, PRECHECK_OUT, FORCE as kpc_key_postcheck.py.
  KPC_DROP_JUMP_MIN (default 25) / KPC_DROP_JUMP_PCT (default 5): warn when the parks newly dropped this build exceed both.
"""
import csv, json, os, pathlib, re, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_key_postcheck as PK  # noqa: E402  (links-01: KEYS, load_tree, parks_of, has_outline, read_csv, git)
PC, AW = PK.PC, PK.AW

RESTART = (2026, 11, 2, 15, 37)   # 9:37 AM CST Nov 2 restart, in UTC: a sign-off before it never counts (person-answer rule)


def after_restart(d):
    """True when an answer-sheet approved_date is at or after the 9:37 AM CST Nov 2 restart. A bare YYYY-MM-DD is the START of
    that day in CST (as kpc_key_freeze.signed_when): a bare 2026-11-02 is before the restart. 'HH:MM UTC|CST|CDT' and ISO with a zone too."""
    import datetime
    s = str(d or '').strip(); utc = datetime.timezone.utc
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{1,2}):(\d{2})(?::\d{2})?\s*(UTC|Z|CST|CDT|[+-]\d{2}:?\d{2})?)?$', s)
    if not m: return False
    y, mo, da, hh, mm, z = m.groups()
    try: t = datetime.datetime(int(y), int(mo), int(da), int(hh or 0), int(mm or 0))
    except ValueError: return False
    if hh is None or z in ('CST', None): off = -6
    elif z == 'CDT': off = -5
    elif z in ('UTC', 'Z'): off = 0
    else: off = int(z[:3]) + (1 if z[0] == '+' else -1) * int(z[-2:]) / 60
    return (t - datetime.timedelta(hours=off)).replace(tzinfo=utc) >= datetime.datetime(*RESTART, tzinfo=utc)


def signed_row(s, who):
    """A person's signed sheet row (kpc_answer_words.signed_off: Brandon / KZ4CP, a real past date) dated after the restart."""
    return bool(AW and AW.signed_off(s.get('approved_by'), s.get('approved_date'), who) and after_restart(s.get('approved_date')))


REASONS = [   # (code, file title): ONE place to add a reason; order = which reason wins when several fit
    ('joined_in_other_area', "joined in another area's file (not a real drop)"),
    ('pota_bad_pin', 'POTA 0,0 or impossible pin'),
    ('override_no', "overrides 'no'"),
    ('rule18_doubt', 'rule 18 / doubt (review pile)'),
    ('pin_too_far', 'pin too far'),
    ('wrong_kind', 'wrong kind'),
    ('name_mismatch', 'name mismatch'),
    ('inside_other_land', 'pin inside other (different-name) land'),
    ('private_or_picture_map', 'private / picture map only'),
]
NO_BOUNDARY = ('no_boundary', 'no boundary found (separate list)')
CAND_RULES = [   # candidate reason text (the builders' words) -> code
    (r'^held\b|rule g-|rule 18|record also joined to|^check: a small site|more than one kind of area', 'rule18_doubt'),
    (r'far from the pin', 'pin_too_far'),
    (r'different kind of place', 'wrong_kind'),
    (r'^similar name', 'name_mismatch'),
    (r'pin is inside it \(different name\)', 'inside_other_land'),
]
WHYNOT = {'pin-doubt': 'rule18_doubt', 'name-mismatch': 'name_mismatch', 'needs-parcel': 'inside_other_land', 'private': 'private_or_picture_map',
          'picture-map-only': 'private_or_picture_map'}
COLUMNS = ['ref', 'pota_name', 'pota_lat', 'pota_lon', 'area', 'pota_kind', 'official_site', 'reason', 'detail', 'all_reasons', 'new_this_build',
           'before', 'cand_name', 'cand_id', 'cand_layer', 'cand_acres', 'cand_distance_km', 'cand_kind', 'cand_why', 'other_cands',
           'rule18_flag', 'bad_pin_flag', 'precheck_flags', 'why_not_tag', 'override', 'sheet_answer', 'person_answer', 'needs_research',
           'pre_km', 'pre_km_what', 'pre_kind', 'pre_kind_why', 'pre_blank_reason', 'build', 'checked']
PRE_COLS = ('pre_km', 'pre_km_what', 'pre_kind', 'pre_kind_why', 'pre_blank_reason')
JUMP_MIN, JUMP_PCT = 25, 5.0


def note(kind, msg): print(f'::{kind} title=Dropped parks::{msg}')


def load(f, d=None):
    try: return json.load(open(f, encoding='utf-8'))
    except Exception: return d  # noqa: BLE001


def layer_of(cid, layers, k, src=None):
    """The official layer a candidate id comes from: world candidates carry it; 'Alberta Park:491' -> 'Alberta Park'; a layers.json
    prefix ('sgoka4' -> sgoka); a plain number = the national layer (US PAD-US, Canada CPCAD)."""
    if k == 'world' and isinstance(src, str) and not re.fullmatch(r'-?\d+(\.\d+)?', src): return src
    s = str(cid)
    if ':' in s: return s.split(':', 1)[0]
    if re.fullmatch(r'\d+', s): return {'us': 'PAD-US', 'ca': 'CPCAD'}.get(k, 'national layer')
    pre = re.match(r'[A-Za-z_]+', s)
    p = pre.group(0) if pre else s
    for n in range(len(p), 0, -1):
        v = layers.get(p[:n])
        if v is not None:
            return f"{p[:n]}: {v[2]}" if isinstance(v, list) and len(v) > 2 else p[:n]
    return p


def cand_reason(why):
    w = str(why or '').strip().lower()
    for rx, code in CAND_RULES:
        if re.search(rx, w): return code
    return ''


def km_in(why):
    m = re.search(r'(\d+(?:\.\d+)?)\s*km', str(why or ''))
    return m.group(1) if m else ''


def sheet_rows(k, sheet_dir):
    rows = PK.read_csv(pathlib.Path(sheet_dir) / PK.KEYS[k]['sheet']) if sheet_dir else None
    out = {}
    for r in rows or []:
        if (r.get('ref') or '').strip(): out.setdefault(r['ref'].strip(), []).append(r)
    return out, rows is not None


def by_area(tree):
    """{(area, ref): park} - a park listed in several state files (a multi-state park) is one row per file (links-01's parks_of keeps
    only one of them)."""
    return {(a, r): dict(p, _area=a) for a, d in tree.items() for r, p in ((d or {}).get('parks') or {}).items() if isinstance(p, dict)}


def classify(r, p, pin, ov, sheet, who, pile, whynot, elsewhere=()):
    """[(code, detail)] for every reason that fits this dropped park, best first (REASONS order)."""
    hits = {}
    def add(code, det): hits.setdefault(code, det)
    b = PC.bad_pin(pin) if PC else ''
    if b: add('pota_bad_pin', b + " (POTA's error: never moved)")
    o = ov.get(r) if isinstance(ov.get(r), dict) else None
    if o and (o.get('no') or o.get('none')):
        add('override_no', "overrides.json: " + ('none' if o.get('none') else 'no ' + ', '.join(str(x) for x in (o.get('no') or [])[:4])) + (f" ({o.get('when')})" if o.get('when') else ''))
    for s in sheet:
        w = AW.word(s.get('status'))[0] if AW else str(s.get('status') or '').upper()
        if w in ('NO', 'PIN') and signed_row(s, who):
            add('override_no', f"answer sheet {w} by {s.get('approved_by')} {s.get('approved_date')} ({s.get('record_name') or s.get('key_id') or ''})"); break
    pr = pile.get(r)
    if pr and ('RULE18' in (pr.get('flags') or '') or (pr.get('action') or '').upper().startswith('HOLD')):
        add('rule18_doubt', f"pre-check {pr.get('action') or ''} {pr.get('flags') or ''}: {(pr.get('why') or '')[:140]}".strip())
    for c in (p.get('c') or []) + (p.get('a') or []):
        if isinstance(c, list) and len(c) > 3:
            code = cand_reason(c[3])
            if code: add(code, f"{c[1]} ({c[0]}): {c[3]}")
    wn = (whynot.get(r) or {})
    if WHYNOT.get(wn.get('tag')): add(WHYNOT[wn['tag']], f"why-not.json: {wn.get('tag')}" + (f" - {wn.get('why')}" if wn.get('why') else ''))
    if p.get('joined_in') or elsewhere:
        add('joined_in_other_area', 'its land is joined in ' + ', '.join(sorted(set(p.get('joined_in') or []) | set(elsewhere))) + "'s key file (not a real drop when that file has the outline)")
    order = [c for c, _ in REASONS]
    out = [(c, hits[c]) for c in order if c in hits]
    if not out:
        det = 'no official record named like it and none at the pin'
        if wn.get('tag'): det += f" (why-not.json: {wn.get('tag')}" + (f" - {wn.get('why')}" if wn.get('why') else '') + ')'
        out = [(NO_BOUNDARY[0], det)]
    return out


KIND_RX = re.compile(r'(national|state|provincial|county|regional|municipal)?\s*(park reserve|park|forest|wildlife (management )?area|wildlife refuge|'
                     r'refuge|recreation (management )?area|recreation site|historic(al)? (site|park|trail)|monument|preserve|reserve|wilderness|'
                     r'conservation area|natural area|nature reserve|game land|fishing lake|marine park|sanctuary|wma|srma|acec|wild and scenic river|'
                     r'river|trail|seashore|lakeshore|battlefield|memorial|field office|ecological reserve)\b', re.I)


def kind_of(name):
    """The kind of place a record's own name says ('Trap Pond State Park' -> 'state park'); '' when the name says none. Only the
    name words: the key does not store the record's designation field."""
    m = list(KIND_RX.finditer(str(name or '')))
    return ' '.join(m[-1].group(0).lower().split()) if m else ''


def best_cand(p, k, layers, detail=''):
    cs = [c for c in (p.get('c') or []) + (p.get('a') or []) if isinstance(c, list) and len(c) >= 2]
    if not cs: return {}, 0
    # the record the main reason names ("Name (id): ...") is the best candidate; else the builders' first
    # (they sort best first: 'similar name', then same name other kind, then size)
    c = next((x for x in cs if f'({x[0]})' in (detail or '')), cs[0])
    acres = c[2] if len(c) > 2 and isinstance(c[2], (int, float)) and not isinstance(c[2], bool) else ''
    kind = kind_of(c[1])
    why = c[3] if len(c) > 3 else ''
    return {'cand_name': c[1], 'cand_id': c[0], 'cand_layer': layer_of(c[0], layers, k, c[2] if len(c) > 2 else None), 'cand_acres': acres,
            'cand_distance_km': km_in(why) and ('>' + km_in(why)), 'cand_kind': kind, 'cand_why': why}, len(cs) - 1


def built_ts(b):
    """The build's 'built' stamp ('2026-11-04 10:00 UTC', ISO) as a UTC timestamp; None when it does not read."""
    import calendar
    t = str(b or '').strip().replace('T', ' ').replace('Z', '').replace(' UTC', '')[:16]
    try: return calendar.timegm(time.strptime(t, '%Y-%m-%d %H:%M'))
    except ValueError: return None


def precheck_join(pre, built=''):
    """(tables, state) for the pre-check join BY REF. state '' = use it; else the blank reason for every row:
    'no precheck output' or 'precheck older than build' (scorecard.csv written before the build's 'built' time)."""
    d = pathlib.Path(pre)
    sc = PK.read_csv(d / 'scorecard.csv')
    if sc is None: return {}, 'no precheck output'
    b = built_ts(built)
    try:
        if b is not None and os.path.getmtime(d / 'scorecard.csv') < b: return {}, 'precheck older than build'
    except OSError: return {}, 'no precheck output'
    T = {}
    for x in sc: T.setdefault(x.get('park'), []).append(x)
    return {'score': T, 'county': {x.get('park'): x for x in (PK.read_csv(d / 'county.csv') or [])}}, ''


def pre_cols(r, area, J, state):
    """pre_km / pre_km_what / pre_kind / pre_kind_why / pre_blank_reason for one dropped row (joined, never worked out)."""
    out = dict.fromkeys(PRE_COLS, '')
    if state: out['pre_blank_reason'] = state; return out
    s = J['score'].get(r) or []
    s = [x for x in s if x.get('area') == area] or s
    c = J['county'].get(r) or {}
    if not s and not c: out['pre_blank_reason'] = 'no precheck row'; return out
    gaps, fl = [], ' '.join(x.get('flags') or '' for x in s).split()
    km = str(c.get('km to listed') or '').strip()
    if km: out['pre_km'], out['pre_km_what'] = km, 'pin to the nearest WWFF-listed county (pre-check county check)'
    elif 'PIN_WAY_OUT' in fl:
        out['pre_km_what'] = 'pre-check PIN_WAY_OUT: the POTA pin is well outside the joined land'
        gaps.append('distance: the pre-check keeps no km for PIN_WAY_OUT')
    else: gaps.append('distance: the pre-check row has no distance (no county-check row)')
    wk = [x for x in s if 'WRONG_KIND' in (x.get('flags') or '').split()]
    if wk:
        out['pre_kind'] = 'wrong kind'
        out['pre_kind_why'] = next((w for x in wk for w in (x.get('why') or '').split(' | ') if w.startswith(('layer kind:', 'WWFF:'))), '')
    else: gaps.append('kind: no kind problem in the pre-check row (it checks joined records only)')
    out['pre_blank_reason'] = '; '.join(gaps)
    return out


def rows_for(k, N, O, cwd, env, build, checked, built=''):
    kd = os.path.join(cwd, PK.KEYS[k]['dir'])
    here = os.getcwd()
    try:
        os.chdir(cwd); pins = PC.pota_pins() if PC else {}
    finally: os.chdir(here)
    ov = (load(os.path.join(kd, 'overrides.json'), {}) or {}).get('parks') or {}
    layers = load(os.path.join(kd, 'layers.json'), {}) or {}
    whynot = (load(os.path.join(kd, 'why-not.json'), {}) or {}).get('parks') or {}
    web = (load(os.path.join(cwd, 'data/parkinfo-web.json'), {}) or {}).get('parks') or {}
    sheet, sheet_read = sheet_rows(k, env.get('ANSWER_SHEET', os.path.join(cwd, 'kpcdata/data/answer-sheet')))
    pre = env.get('PRECHECK_OUT', '/tmp/kpc-precheck')
    pile = {x.get('park'): x for x in (PK.read_csv(pathlib.Path(pre) / 'review-pile.csv') or [])}
    bpf = {x.get('park'): x.get('flag') for x in (PK.read_csv(pathlib.Path(pre) / 'BAD_POTA_PIN_FLAGS.csv') or [])}
    lost = {x.get('park') or x.get('ref'): x for x in (PK.read_csv(pathlib.Path(pre) / 'lost-finds-routed.csv') or [])}
    J, jstate = precheck_join(pre, built)
    who = AW.persons(env.get('KPC_PERSONS')) if AW else set()
    rows = []
    outl = {}
    for (a, r), p in N.items():
        if PK.has_outline(p): outl.setdefault(r, []).append(a)
    for (a, r), p in sorted(N.items()):
        if PK.has_outline(p) or p.get('line'): continue
        pin = pins.get(r)
        why = classify(r, p, pin, ov, sheet.get(r, []), who, pile, whynot, [x for x in outl.get(r, []) if x != a])
        o = O.get((a, r))
        before = 'absent' if o is None else ('outline' if PK.has_outline(o) else 'pin')
        cand, more = best_cand(p, k, layers, why[0][1])
        w = web.get(r) or {}
        site = w.get('web') or (('agency page: ' + w['agency_page']) if w.get('agency_page') else '')
        sh = sheet.get(r, [])
        signed = [s for s in sh if signed_row(s, who)]
        nr = [s for s in sh if 'NEEDS_RESEARCH' in json.dumps(s)]
        lr = lost.get(r) or {}
        oo = ov.get(r) if isinstance(ov.get(r), dict) else None
        pr = pile.get(r) or {}
        row = {'ref': r, 'pota_name': (pin[0] if pin else '') or p.get('n') or '', 'pota_lat': pin[1] if pin else '', 'pota_lon': pin[2] if pin else '',
               'area': p['_area'], 'pota_kind': p.get('t') or '', 'official_site': site, 'reason': why[0][0], 'detail': why[0][1],
               'all_reasons': ';'.join(c for c, _ in why), 'new_this_build': 'yes' if before != 'pin' and O else ('' if not O else 'no'), 'before': before if O else 'no previous build',
               **{c: '' for c in ('cand_name', 'cand_id', 'cand_layer', 'cand_acres', 'cand_distance_km', 'cand_kind', 'cand_why')}, **cand,
               'other_cands': more, 'rule18_flag': 'yes' if ('RULE18' in (pr.get('flags') or '') or any(c == 'rule18_doubt' for c, _ in why)) else '',
               'bad_pin_flag': bpf.get(r) or (PC.bad_pin(pin) if PC else ''), 'precheck_flags': (pr.get('action', '') + ' ' + pr.get('flags', '')).strip(),
               'why_not_tag': (whynot.get(r) or {}).get('tag') or '',
               'override': json.dumps({x: oo[x] for x in ('no', 'none', 'join', 'when', 'why') if x in oo}, ensure_ascii=False)[:400] if oo else '',
               'sheet_answer': ' | '.join(f"{s.get('status')} {s.get('record_name') or ''} ({s.get('key_id') or s.get('record_id') or ''}) by {s.get('approved_by') or '-'} {s.get('approved_date') or ''}".strip() for s in sh)[:400],
               'person_answer': 'yes' if signed else '', 'needs_research': ('sheet: ' + '; '.join((s.get('note') or s.get('status') or '')[:120] for s in nr)) if nr else
               (f"pre-check: {lr.get('route') or lr.get('status') or ''} {lr.get('why') or ''}".strip() if 'NEEDS_RESEARCH' in json.dumps(lr) else ''),
               **pre_cols(r, p['_area'], J, jstate), 'build': build, 'checked': checked}
        rows.append(row)
    import collections
    pj = {'state': jstate or 'used', 'rows': len(rows), 'rows_with_km': sum(1 for x in rows if x['pre_km']),
          'rows_with_kind': sum(1 for x in rows if x['pre_kind']), 'blank_reasons': dict(collections.Counter(x['pre_blank_reason'] for x in rows if x['pre_blank_reason']))}
    return rows, {'pins': len(pins), 'sheet_read': sheet_read, 'precheck_read': bool(pile or bpf), 'precheck_join': pj}


def jump_check(rows, N, O, env):
    """System problems only: (warnings list). A sudden jump = more parks newly dropped than KPC_DROP_JUMP_MIN AND KPC_DROP_JUMP_PCT %
    of the parks the previous build had outlined; a whole area (10+ parks) that had outlines and now has none."""
    if not O: return [], {'checked': False, 'why': 'no previous build to compare'}
    try: mn, pct = int(env.get('KPC_DROP_JUMP_MIN') or JUMP_MIN), float(env.get('KPC_DROP_JUMP_PCT') or JUMP_PCT)
    except ValueError: mn, pct = JUMP_MIN, JUMP_PCT
    was = sum(1 for p in O.values() if PK.has_outline(p))
    new = sum(1 for x in rows if x['new_this_build'] == 'yes' and x['before'] == 'outline')
    lim = max(mn, was * pct / 100)
    warn = []
    if new > lim: warn.append(f'{new} parks lost their outline this build (limit {lim:.0f}: {mn} or {pct:g}% of {was} outlined before): a sudden jump, check the build')
    areas = {}
    for (a, r), p in N.items(): areas.setdefault(a, []).append(r)
    for a, refs in sorted(areas.items()):
        ps = [N[(a, r)] for r in refs]
        before = [O.get((a, r)) for r in refs]
        if len(ps) >= 10 and not any(PK.has_outline(p) for p in ps) and sum(1 for o in before if o and PK.has_outline(o)) >= 5:
            warn.append(f'{a}: every park is a pin now (it had outlines before): a whole area dropped, check the build')
    return warn, {'checked': True, 'new_drops': new, 'outlined_before': was, 'limit': round(lim, 1)}


def md_table(counts, newc, files, warn, pj=None):
    t = ['', '<!-- links-07 dropped parks -->', '## Dropped parks (no outline in this build), by reason', '',
         '| reason | parks | new this build | file |', '|---|---:|---:|---|']
    for code, title in REASONS + [NO_BOUNDARY]:
        t.append(f"| {title} (`{code}`) | {counts.get(code, 0)} | {newc.get(code, 0)} | {files[code]} |")
    t.append(f"| **total** | **{sum(counts.values())}** | **{sum(newc.values())}** | index.json |")
    t += ['', 'Each row carries the POTA name and pin, the area, the official site, the best official candidate (name, id, layer, acres, '
          'kind words, why), the flags, any past person answer and the build. cand_distance_km is the key\'s own (e.g. ">2" km).']
    if pj: t += ['', f"Pre-check join by ref ({pj['state']}): distance (pre_km) on {pj['rows_with_km']} and kind (pre_kind) on "
                 f"{pj['rows_with_kind']} of {pj['rows']} rows; every blank cell says why in pre_blank_reason."]
    if warn: t += [''] + [f'- **System check:** {w}' for w in warn]
    return '\n'.join(t) + '\n<!-- /links-07 -->\n'


def run(env=None, cwd='.'):
    env = dict(os.environ if env is None else env)
    k = PK.key_of(env)
    if not k: note('notice', 'no key named (KEY / WORKFLOW_NAME): nothing to do'); return None
    out_dir = pathlib.Path(env.get('OUT_DIR') or os.path.join(cwd, 'data/status/key-check'))
    last = load(out_dir / f'last-{k}.json', {}) or {}
    rep_f = out_dir / (last.get('report') or '')
    rep = load(rep_f, None) if last.get('report') else None
    if not rep: note('notice', f'{k} key: no post-key report yet (last-{k}.json): nothing to list'); return None
    base = rep_f.with_suffix('')
    dd = base / 'dropped'
    idx_f = dd / 'index.json'
    old_idx = load(idx_f, {}) or {}
    if old_idx.get('report_checked') == rep.get('checked') and (env.get('FORCE') or '').lower() != 'yes':
        note('notice', f'{k} key {rep.get("build")}: dropped lists already written for this report'); return old_idx
    tree = PK.load_tree(k, None, cwd=cwd)
    N = by_area(tree)
    prev = (rep.get('prev_ref') or '').strip()
    O = by_area(PK.load_tree(k, prev, cwd=cwd)) if prev else {}
    checked = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())
    rows, info = rows_for(k, N, O, cwd, env, rep.get('build') or '', checked, rep.get('built') or '')
    warn, jc = jump_check(rows, N, O, env)
    bad = [a for a, v in tree.items() if v.get('_bad')]
    if bad: warn.append('key files did not read as JSON: ' + ', '.join(bad)[:200])
    if not info['pins']: warn.append('no POTA pins found: the pin columns are empty')
    dd.mkdir(parents=True, exist_ok=True)
    counts, newc, files = {}, {}, {}
    for code, _ in REASONS + [NO_BOUNDARY]:
        fn = ('no-boundary' if code == 'no_boundary' else code.replace('_', '-')) + '.csv'
        files[code] = fn
        sel = [x for x in rows if x['reason'] == code]
        counts[code], newc[code] = len(sel), sum(1 for x in sel if x['new_this_build'] == 'yes')
        with open(dd / fn, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS); w.writeheader(); w.writerows(sel)
    idx = {'key': k, 'build': rep.get('build'), 'report': rep_f.name, 'report_checked': rep.get('checked'), 'checked': checked,
           'prev_ref': prev or 'none', 'about': 'parks this build has with NO outline, one row each, split by reason (kpc_key_dropped.py, links-07)',
           'counts': counts, 'new_this_build': newc, 'total': len(rows), 'files': files, 'columns': COLUMNS,
           'reasons': {c: t for c, t in REASONS + [NO_BOUNDARY]}, 'jump_check': jc, 'system_warnings': warn,
           'inputs': {'pota_pins': info['pins'], 'answer_sheet_read': info['sheet_read'], 'precheck_read': info['precheck_read']},
           'precheck_join': info['precheck_join']}
    json.dump(idx, open(idx_f, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    mdf = base.with_suffix('.md')
    txt = mdf.read_text(encoding='utf-8') if mdf.exists() else ''
    txt = re.sub(r'\n?<!-- links-07 dropped parks -->.*?<!-- /links-07 -->\n', '', txt, flags=re.S)
    mdf.write_text(txt.rstrip('\n') + '\n' + md_table(counts, newc, {c: f'{base.name}/dropped/{f}' for c, f in files.items()}, warn, info['precheck_join']), encoding='utf-8')
    for w in warn: note('warning', f'{k} key {rep.get("build")}: {w}')
    note('notice', f"{k} key {rep.get('build')}: {len(rows)} parks with no outline (" + ', '.join(f'{c} {n}' for c, n in counts.items() if n) + f") -> {dd}")
    return idx


if __name__ == '__main__':
    try: run()
    except Exception as e:  # noqa: BLE001  (never fail the build)
        import traceback; traceback.print_exc()
        note('warning', f'the dropped-parks lists stopped with an error ({type(e).__name__}: {e}); the build is not affected')
    sys.exit(0)
