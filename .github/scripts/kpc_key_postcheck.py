#!/usr/bin/env python3
"""KPC post-key-build check (Nov 4 2026, Mapping; Brandon 4:11 AM CST Nov 4, relayed by Super: "Let's have everything set up and
done instead of back and forth"). READ-ONLY and OFFLINE: no web request at all (so nothing to be polite to), it only reads files in
this checkout, git history, the KPC-Data answer sheet copy and the pre-check output.

After a US / Canada / world key build it compares the NEW key (the working tree) with the PREVIOUS BUILD (the tree of the build
commit before it, read with `git show`) and lists:
  * parks gained / lost; outline -> pin and pin -> outline; outlines whose joined record ids changed (their 2-fers need a rerun)
  * flat / zero-area outlines (acres 0, or a Canada outline file whose area is ~0)
  * POTA pins outside their outline ('well outside' / pin_may_be_wrong, and a point-in-polygon test on Canada's outline files)
  * 0,0 and impossible POTA pins (kpc_precheck.bad_pin; POTA's own error, we never move POTA pins)
  * disagreements with the answer sheet (KPC-Data data/answer-sheet: a person's signed YES/NO first; PROPOSED rows only counted),
    overrides.json (a 'no' id still joined, a 'none' park still an outline, a 'join' name/id missing) and the pre-check
    REVIEW_PILE / RULE 18 / bad-pin flags
  * the parks Brandon's 7:33 PM CST Nov 3 ruling dropped to pins (CA-2218, CA-2227, SE-0797): PASS only when they ARE pins
It writes data/status/key-check/<key>-<build>.json + .md and data/status/key-check/last-<key>.json. It NEVER fails a build:
every problem is a line in the report and the exit code is always 0.

  KEY=us|ca|world (or WORKFLOW_NAME = the finished workflow's name)   BUILD=<run id> (used only when index.json has no 'build' stamp)
  PREV_REF=<git ref> (default: the build commit before the newest one)   NEW_REF=<git ref> (default: the working tree)
  ANSWER_SHEET=<dir> (default kpcdata/data/answer-sheet)   PRECHECK_OUT=<dir> (default /tmp/kpc-precheck; kpc_precheck.py output)
  FERS_DIR=<dir> (optional: KPC-Data data/fers, to count the 2-fer rows touching changed parks)   OUT_DIR (default data/status/key-check)
  FORCE=yes: write a report even when the newest build was already checked.
"""
import csv, fnmatch, glob, json, math, os, pathlib, re, subprocess, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
try: import kpc_precheck as PC  # noqa: E402  (pota_pins, bad_pin; no network)
except Exception: PC = None  # noqa: BLE001
try: import kpc_answer_words as AW  # noqa: E402
except Exception: AW = None  # noqa: BLE001

KEYS = {
    'us': {'dir': 'data/us-key', 'glob': 'US-??.json', 'msg': 'US answer key', 'sheet': 'US.csv', 'wf': 'KPC US answer key'},
    'ca': {'dir': 'data/ca-key', 'glob': 'CA-??.json', 'msg': 'Canada answer key', 'sheet': 'CA.csv', 'wf': 'KPC Canada answer key'},
    'world': {'dir': 'data/world-key', 'glob': '??.json', 'msg': 'World answer key', 'sheet': 'world.csv', 'wf': 'KPC world answer key'},
}
# Brandon 7:33 PM CST Nov 3 (relayed by Super via Quality: 'When in doubt drop it put it on a list'): these must come out as PINS.
MUST_PIN = {'ca': ['CA-2218', 'CA-2227'], 'world': ['SE-0797']}
# Next round v2 C11 (Quality, German pre-check '6 vs 722', Nov 5): a source layer lost in a build shows up here as many parks of ONE
# country going outline -> pin at once (W-41901828387: DE 42, all BfN Naturparke / Nationalparke). 10 per country is above every
# whole-key US / Canada count in the saved reports (US 4 and 0, Canada 8 and 2) and well under the DE loss. A WARNING only: a person
# looks; the build is never failed.
PIN_JUMP = 10


def pin_jump(ch, limit=PIN_JUMP):
    """{country: outline -> pin count} for every country (the part of the park number before '-') at or over the limit."""
    n = {}
    for r in ch.get('outline_to_pin') or []: n[str(r).split('-')[0]] = n.get(str(r).split('-')[0], 0) + 1
    return {c: k for c, k in sorted(n.items(), key=lambda x: (-x[1], x[0])) if k >= limit}


FLAT_M2 = 100.0          # an outline file under 100 m2 (0.025 ac) is 'flat'
LIST_MAX = 40            # rows shown per section in the .md (the .json has them all)


def note(kind, msg): print(f'::{kind} title=Key check::{msg}')


def git(*a, cwd='.'):
    try:
        r = subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True, timeout=120)
        return r.stdout if r.returncode == 0 else None
    except Exception: return None  # noqa: BLE001


def key_of(env):
    k = (env.get('KEY') or '').strip().lower()
    if k in KEYS: return k
    wf = (env.get('WORKFLOW_NAME') or '').strip()
    for k, v in KEYS.items():
        if wf == v['wf']: return k
    return ''


def build_commits(k, cwd='.', n=400):
    """Newest first: commits whose subject is the key workflow's save message and that touched its key folder."""
    out = git('log', f'-n{n}', '--format=%H%x09%s', '--', KEYS[k]['dir'], cwd=cwd) or ''
    return [ln.split('\t', 1)[0] for ln in out.splitlines() if '\t' in ln and ln.split('\t', 1)[1].strip() == KEYS[k]['msg']]


def load_tree(k, ref=None, cwd='.'):
    """{area: key file dict} at a git ref (None = the working tree)."""
    d, pat = KEYS[k]['dir'], KEYS[k]['glob']
    out = {}
    if ref is None:
        for f in sorted(glob.glob(os.path.join(cwd, d, pat))):
            try: out[pathlib.Path(f).stem] = json.load(open(f, encoding='utf-8'))
            except Exception: out[pathlib.Path(f).stem] = {'_bad': True}  # noqa: BLE001
        return out
    names = (git('ls-tree', '--name-only', ref, d + '/', cwd=cwd) or '').split()
    for p in names:
        if not fnmatch.fnmatch(os.path.basename(p), pat): continue
        txt = git('show', f'{ref}:{p}', cwd=cwd)
        try: out[pathlib.Path(p).stem] = json.loads(txt) if txt is not None else {'_bad': True}
        except ValueError: out[pathlib.Path(p).stem] = {'_bad': True}
    return out


def parks_of(tree):
    """{ref: park}. Multi-state parks appear in every crossed state; prefer a copy with an outline over a pin
    (Nov 6: US-0822 Fort Smith was OK=pin with joined_in AR, and AR had the outline — last-wins kept the pin and
    flagged a false override miss)."""
    P = {}
    def _outline(p): return bool(p and p.get('m')) and p.get('g') != 'pin'
    for area, d in sorted((tree or {}).items()):
        for r, p in ((d or {}).get('parks') or {}).items():
            if not isinstance(p, dict): continue
            q = dict(p, _area=area)
            if r not in P or (_outline(q) and not _outline(P[r])): P[r] = q
    return P


def has_outline(p): return bool(p and p.get('m')) and p.get('g') != 'pin'
def ids_of(p): return {str(x[0]) for x in (p.get('m') or []) if isinstance(x, list) and x}
def names_of(p): return {str(x[1]).strip().lower() for x in (p.get('m') or []) if isinstance(x, list) and len(x) > 1 and x[1]}


def acres_of(p):
    """The park's acres when the key says them (US 'ac'; or numeric acres in m[2]); None = not known."""
    if isinstance(p.get('ac'), (int, float)): return float(p['ac'])
    a = [x[2] for x in (p.get('m') or []) if isinstance(x, list) and len(x) > 2 and isinstance(x[2], (int, float)) and not isinstance(x[2], bool)]
    return float(sum(a)) if a else None


# ---- geometry (pure python: shoelace area on a local projection, ray-casting point in polygon)
def _rings(geom):
    g = (geom or {}).get('geometry', geom) or {}
    c, t = g.get('coordinates') or [], g.get('type')
    polys = c if t == 'MultiPolygon' else [c] if t == 'Polygon' else []
    return [p for p in polys if p and p[0]]


def area_m2(geom):
    tot = 0.0
    for poly in _rings(geom):
        for i, ring in enumerate(poly):
            if len(ring) < 3: continue
            lat0 = math.radians(sum(pt[1] for pt in ring) / len(ring))
            kx, ky = 111320.0 * math.cos(lat0), 110574.0
            s = 0.0
            for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
                s += (x1 * kx) * (y2 * ky) - (x2 * kx) * (y1 * ky)
            tot += abs(s) / 2 * (1 if i == 0 else -1)
    return max(tot, 0.0)


def _in_ring(x, y, ring):
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-300) + x1: inside = not inside
    return inside


def point_in(geom, la, lo):
    for poly in _rings(geom):
        if _in_ring(lo, la, poly[0]) and not any(_in_ring(lo, la, h) for h in poly[1:]): return True
    return False


# ---- the comparison
def released_tree(k, env, cwd='.'):
    """Nov 8 (Quality, US-42446831487): the RELEASED key (KPC-Data data/<kind>-key, what users get), so outline -> pin is also
    measured against what shipped, not only the previous build (the waiting-room copy). RELEASED_DIR = that folder's parent
    ('released' in the key-check workflow); returns ({area: file}, folder) or ({}, None) when it is not there."""
    d = KEYS[k]['dir']
    for base in [env.get('RELEASED_DIR'), 'released']:
        if not base: continue
        root = base if os.path.isabs(base) else os.path.join(cwd, base)
        f = os.path.join(root, d)
        if os.path.isdir(f) and glob.glob(os.path.join(f, KEYS[k]['glob'])): return load_tree(k, None, cwd=root), f
    return {}, None


def compare(new, old):
    N, O = parks_of(new), parks_of(old)
    R = {'gained': sorted(set(N) - set(O)), 'lost': sorted(set(O) - set(N)), 'outline_to_pin': [], 'pin_to_outline': [], 'outline_changed': []}
    for r in sorted(set(N) & set(O)):
        a, b = has_outline(O[r]), has_outline(N[r])
        if a and not b: R['outline_to_pin'].append(r)
        elif b and not a: R['pin_to_outline'].append(r)
        elif a and b and ids_of(O[r]) != ids_of(N[r]): R['outline_changed'].append(r)
    return N, O, R


def flat(N, k, bounds_dir):
    """Outlines with no area. Canada: the outline file itself is measured (the key rounds a 1-acre park to 0 acres); elsewhere the
    key's acres, labelled as such (0 = under half an acre, or the layer gave no area)."""
    out = []
    for r, p in sorted(N.items()):
        if not has_outline(p) or p.get('line'): continue
        f = pathlib.Path(bounds_dir) / f'{r}.json' if (k == 'ca' and bounds_dir) else None
        if f is not None and f.exists():
            try: m2 = area_m2(json.load(open(f, encoding='utf-8')))
            except Exception: continue  # noqa: BLE001
            if m2 < FLAT_M2: out.append({'park': r, 'area': p['_area'], 'why': f'outline file data/canada-bounds/{r}.json is {m2:.1f} m2 (flat)'})
            continue
        a = acres_of(p)
        if a is not None and a <= 0: out.append({'park': r, 'area': p['_area'], 'why': 'acres 0 in the key (under half an acre, or the layer gave no area' + ('; no outline file to measure)' if k == 'ca' else ')')})
    return out


def pins_outside(N, k, pins, bounds_dir, edge=None):
    """'well outside' / pin_may_be_wrong from the key; for Canada also a point-in-polygon test on the outline file. A pin the key
    already calls 'edge' (near the line, inside the tolerance) is only counted in `edge`, not listed."""
    out = []
    for r, p in sorted(N.items()):
        if not has_outline(p): continue
        why = []
        if p.get('far') == 'well outside': why.append("key says the POTA pin is 'well outside' the joined land")
        if p.get('pin_may_be_wrong'): why.append('key says pin_may_be_wrong')
        if k == 'ca' and bounds_dir and r in pins and PC and not PC.bad_pin(pins[r]) and not why:
            f = pathlib.Path(bounds_dir) / f'{r}.json'
            if f.exists():
                try: inside = point_in(json.load(open(f, encoding='utf-8')), float(pins[r][1]), float(pins[r][2]))
                except Exception: inside = True  # noqa: BLE001
                if not inside and p.get('far') == 'edge':
                    if edge is not None: edge.append(r)
                elif not inside: why.append('POTA pin is outside the data/canada-bounds outline, but the key does not flag it (far=' + repr(p.get('far')) + ')')
        if why: out.append({'park': r, 'area': p['_area'], 'far': p.get('far') or '', 'why': '; '.join(why)})
    return out


def bad_pins(N, pins):
    out = []
    if not PC: return out
    for r, p in sorted(N.items()):
        if r not in pins: continue      # a park with no POTA pin at all is the pre-check's BAD_POTA_PIN list, not a 0,0 pin
        b = PC.bad_pin(pins[r])
        if b: out.append({'park': r, 'area': p['_area'], 'outline': 'yes' if has_outline(p) else 'no', 'why': b + ' (POTA\'s error: never moved)'})
    return out


def read_csv(f):
    try: return list(csv.DictReader(open(f, encoding='utf-8', newline='')))
    except Exception: return None  # noqa: BLE001


RESTART = (2026, 11, 2, 15, 37)   # links-08: 9:37 AM CST Nov 2 restart, in UTC; a sign-off before it never counts (person-answer rule)


def after_restart(d):
    """links-08 (FINAL-v2 self-check, Brandon's 6:14 AM CST Nov 4 rule, relayed via Super Head Bot): True when an answer-sheet approved_date is
    at or after the 9:37 AM CST Nov 2 restart. A bare YYYY-MM-DD is the START of that day in CST (as kpc_key_freeze.signed_when):
    a bare 2026-11-02 is before the restart. 'HH:MM UTC|CST|CDT' and ISO with a zone are read too."""
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


def sheet_check(N, k, sheet_dir, who):
    rows = read_csv(pathlib.Path(sheet_dir) / KEYS[k]['sheet']) if sheet_dir else None
    if rows is None: return {'read': False, 'signed_disagree': [], 'proposed_disagree': 0, 'rows': 0, 'signed': 0}
    sd, pdis, signed = [], 0, 0
    for row in rows:
        r = (row.get('ref') or '').strip()
        if not r: continue
        w = AW.word(row.get('status'))[0] if AW else str(row.get('status') or '').upper()
        rid = str(row.get('key_id') or row.get('record_id') or '').strip()
        p = N.get(r)
        joined = bool(p) and has_outline(p) and (rid in ids_of(p) or (row.get('record_name') or '').strip().lower() in names_of(p))
        person = (AW.signed_off(row.get('approved_by'), row.get('approved_date'), who) and after_restart(row.get('approved_date'))) if AW else False   # links-08
        bad = (w == 'YES' and not joined) or (w in ('NO', 'PIN') and joined)
        if w == 'PROPOSED':
            if p is not None and has_outline(p) and rid and rid not in ids_of(p): pdis += 1
            continue
        if person: signed += 1
        if bad and person:
            sd.append({'park': r, 'sheet': w, 'id': rid, 'name': row.get('record_name') or '', 'key': 'joined' if joined else ('pin' if p and not has_outline(p) else ('missing' if not p else 'other record')),
                       'who': row.get('approved_by') or '', 'why': "a person's answer beats the bot: the key must follow the sheet"})
    return {'read': True, 'rows': len(rows), 'signed': signed, 'signed_disagree': sd, 'proposed_disagree': pdis}


def override_check(N, k, cwd='.', built=''):
    """Overrides the key does not follow. 'newer' = the override's 'when' date is after the build date: expected until the next build."""
    ov = (PC.load(os.path.join(cwd, KEYS[k]['dir'], 'overrides.json'), {}) if PC else {}).get('parks') or {}
    out = []
    for r, o in sorted(ov.items()):
        p = N.get(r)
        if not isinstance(o, dict) or p is None: continue
        no = {str(x).strip() for x in (o.get('no') or [])}
        nol = {x.lower() for x in no}
        newer = (str(o.get('when'))[:10] > built[:10]) if (built and o.get('when')) else None   # None = the override has no date
        n0 = len(out)
        if has_outline(p) and (ids_of(p) & no or names_of(p) & nol):
            out.append({'park': r, 'area': p['_area'], 'problem': "an id/name in overrides 'no' is still joined", 'ids': sorted(ids_of(p) & no) + sorted(names_of(p) & nol)})
        # 'none' only clears the candidate list in the key builders (kpc_us_key.py / kpc_ca_key.py): a park is DROPPED TO PIN when
        # every joined piece is in 'no' (the line above), so 'none' alone is not reported.
        j = o.get('join')
        if j:
            fp = o.get('fp') or {}
            want = [str(x).strip() for x in (j if isinstance(j, list) else [j]) if str(x).strip()]
            want = [w for w in want if w not in no and w.lower() not in nol]   # a later 'no' on the same id wins over the old 'join'
            have = ids_of(p) | names_of(p)
            def found(w):   # an id, a record name, or the id's saved [name, acres] fingerprint (the builders re-find a moved id by it)
                f = fp.get(w)
                return w in have or w.lower() in have or bool(isinstance(f, list) and f and str(f[0]).strip().lower() in have)
            if want and has_outline(p) and not any(found(w) for w in want):
                out.append({'park': r, 'area': p['_area'], 'problem': "overrides 'join' not found in the key", 'ids': want[:4]})
            elif want and not has_outline(p):
                out.append({'park': r, 'area': p['_area'], 'problem': "overrides 'join' but the key has no outline (pin)", 'ids': want[:4]})
        for x in out[n0:]: x['when'] = str(o.get('when') or ''); x['newer_than_build'] = newer
    return out


def precheck_flags(N, pre_dir):
    pile = read_csv(pathlib.Path(pre_dir) / 'review-pile.csv') if pre_dir else None
    bp = read_csv(pathlib.Path(pre_dir) / 'BAD_POTA_PIN_FLAGS.csv') if pre_dir else None
    if pile is None: return {'read': False, 'counts': {}, 'hold_still_outline': [], 'rule18': [], 'bad_pin_flags': {}}
    cnt, hold, r18 = {}, [], []
    for row in pile:
        r = row.get('park') or ''
        if r not in N: continue
        for f in re.split(r'[;\s]+', row.get('flags') or ''):
            if f: cnt[f] = cnt.get(f, 0) + 1
        if (row.get('action') or '').startswith('HOLD') and has_outline(N[r]):
            hold.append({'park': r, 'area': N[r]['_area'], 'flags': row.get('flags') or '', 'why': (row.get('why') or '')[:160]})
        if 'RULE18' in (row.get('flags') or ''): r18.append({'park': r, 'area': N[r]['_area'], 'why': (row.get('why') or '')[:160]})
    bpc = {}
    for row in bp or []:
        if (row.get('park') or '') in N: bpc[row.get('flag') or '?'] = bpc.get(row.get('flag') or '?', 0) + 1
    return {'read': True, 'counts': dict(sorted(cnt.items())), 'hold_still_outline': hold, 'rule18': r18, 'bad_pin_flags': bpc}


def must_pin(N, k):
    out = []
    for r in MUST_PIN.get(k, []):
        p = N.get(r)
        if p is None: out.append({'park': r, 'result': 'MISSING from the key'})
        elif has_outline(p): out.append({'park': r, 'result': 'NOT YET PIN', 'ids': sorted(ids_of(p))[:4],
                                         'why': "overrides drop it to a pin (Brandon 7:33 PM CST Nov 3); expected until the next real build of this key"})
        else: out.append({'park': r, 'result': 'PASS (pin)'})
    return out


def fers_touch(changed, fers_dir):
    """2-fer rows (KPC-Data data/fers/<area>.json 'spots') that name a changed park: they were measured on an outline that changed."""
    if not fers_dir or not changed: return None
    ch, n, files = set(changed), 0, {}
    for f in glob.glob(os.path.join(fers_dir, '*.json')):
        try: d = json.load(open(f, encoding='utf-8'))
        except Exception: continue  # noqa: BLE001
        for s in (d.get('spots') or []) if isinstance(d, dict) else []:
            refs = set(s.get('refs') or s.get('parks') or []) | set((s.get('names') or {}).keys())
            if refs & ch: n += 1; files[pathlib.Path(f).stem] = files.get(pathlib.Path(f).stem, 0) + 1
    return {'rows': n, 'files': dict(sorted(files.items(), key=lambda kv: -kv[1])[:30])}


def md(rep):
    L = [f"# Key check: {rep['key']} build {rep['build']}", '',
         f"Checked {rep['checked']} UTC. New: {rep['new_what']} (newest build commit `{rep['new_ref']}`); previous build commit: `{rep['prev_ref'] or 'none found'}`. Read-only, no web requests. "
         "This report never fails the build.", '']
    if rep.get('no_new_build'): L += ['**No new build:** the newest build commit was already checked. Nothing to compare.', '']
    s = rep['summary']
    L += ['## Summary', '', '| check | count |', '|---|---|'] + [f'| {k} | {v} |' for k, v in s.items()] + ['']
    L += ['## Must be pins (Brandon 7:33 PM CST Nov 3)', ''] + [f"- {x['park']}: **{x['result']}**" + (f" (still joined: {', '.join(x.get('ids') or [])}; {x['why']})" if x.get('why') else '') for x in rep['must_pin']] + ([''] if rep['must_pin'] else ['- none for this key', ''])

    def sec(title, rows, fmt):
        nonlocal L
        L += [f'## {title} ({len(rows)})', '']
        L += [fmt(x) for x in rows[:LIST_MAX]] + ([f'- ... {len(rows) - LIST_MAX} more in the .json'] if len(rows) > LIST_MAX else []) + ([''] if rows else ['- none', ''])
    c = rep['changes']
    sec('Gained', c['gained'], lambda r: f'- {r}')
    sec('Lost', c['lost'], lambda r: f'- {r}')
    sec('Outline -> pin', c['outline_to_pin'], lambda r: f'- {r}')
    if c.get('released'):
        sec(f"Outline -> pin against the RELEASED key ({c['released'].get('build') or 'KPC-Data'})", c['released']['outline_to_pin'], lambda r: f'- {r}')
    sec('Pin -> outline', c['pin_to_outline'], lambda r: f'- {r}')
    sec('Outline changed (joined ids differ: its 2-fers need a rerun)', c['outline_changed'], lambda r: f'- {r}')
    sec("A person's signed answer the key does not follow", rep['answer_sheet']['signed_disagree'], lambda x: f"- {x['park']}: sheet {x['sheet']} {x['id']} {x['name']} by {x['who']}; key: {x['key']}")
    sec('Overrides not followed', rep['overrides'], lambda x: f"- {x['park']} ({x['area']}): {x['problem']}: {', '.join(map(str, x['ids']))}" + (f" (override {x['when']}, newer than the build: expected until the next build)" if x.get('newer_than_build') else (f" (override {x['when']})" if x.get('when') else '')))
    sec('Flat / zero-area outlines', rep['flat'], lambda x: f"- {x['park']} ({x['area']}): {x['why']}")
    sec('POTA pin outside its outline', rep['pins_outside'], lambda x: f"- {x['park']} ({x['area']}): {x['why']}")
    sec('0,0 / impossible POTA pins', rep['bad_pins'], lambda x: f"- {x['park']} ({x['area']}, outline {x['outline']}): {x['why']}")
    sec('Pre-check HOLD rows that are still outlines', rep['precheck']['hold_still_outline'], lambda x: f"- {x['park']} ({x['area']}): {x['flags']}: {x['why']}")
    sec('RULE 18 flags', rep['precheck']['rule18'], lambda x: f"- {x['park']} ({x['area']}): {x['why']}")
    if rep.get('problem_solver') is not None:
        sec('Problem solver: recommended fix per held park (recommends only; no pin is moved)', rep['problem_solver'],
            lambda x: f"- {x['park']} {x['name']}: **{x['verdict']}** ({x['confidence']}): {x['recommend']}. Why: {'; '.join(x['reasons'])}")
    L += ['## Notes', ''] + [f'- {n}' for n in rep['notes']] + ['']
    return '\n'.join(L)


def run(env=None, cwd='.'):
    env = dict(os.environ if env is None else env)
    k = key_of(env)
    if not k: note('warning', 'no key given (KEY=us|ca|world or WORKFLOW_NAME): nothing checked'); return None
    out_dir = pathlib.Path(cwd) / (env.get('OUT_DIR') or 'data/status/key-check')
    notes = []
    bc = build_commits(k, cwd=cwd)
    new_ref = env.get('NEW_REF') or None
    newest = (git('rev-parse', new_ref, cwd=cwd) or '').strip() if new_ref else (bc[0] if bc else '')
    prev_ref = env.get('PREV_REF') or None
    if not prev_ref:
        later = [c for c in bc if c != newest]
        if new_ref is None and bc: later = bc[1:]
        prev_ref = later[0] if later else None
        if not prev_ref: notes.append('no previous build commit in the fetched history: gained/lost lists are empty (compared with nothing)')
    last_f = out_dir / f'last-{k}.json'
    last = {}
    try: last = json.load(open(last_f))
    except Exception: pass  # noqa: BLE001
    if newest and last.get('build_commit') == newest and (env.get('FORCE') or '').lower() != 'yes':
        note('notice', f'{k} key: newest build commit {newest[:9]} was already checked ({last.get("checked")}): no new build, nothing written')
        return {'key': k, 'no_new_build': True, 'build_commit': newest}
    new = load_tree(k, new_ref, cwd=cwd)
    old = load_tree(k, prev_ref, cwd=cwd) if prev_ref else {}
    if any(v.get('_bad') for v in new.values()): notes.append('some NEW key files did not read as JSON: ' + ', '.join(a for a, v in new.items() if v.get('_bad'))[:300])
    idx = PC.load(os.path.join(cwd, KEYS[k]['dir'], 'index.json'), {}) if PC else {}
    build = idx.get('build') or (('run-' + env['BUILD']) if env.get('BUILD') else '') or ('git-' + newest[:9] if newest else 'unknown')   # the key's own stamp first
    build = re.sub(r'[^A-Za-z0-9._-]', '-', str(build))
    N, O, ch = compare(new, old)
    rel, rel_dir = released_tree(k, env, cwd)
    if rel_dir:
        _rx = PC.load(os.path.join(rel_dir, 'index.json'), {}) if PC else {}
        _, RO, rch = compare(new, rel)
        ch['released'] = {'build': _rx.get('build') or '', 'dir': rel_dir, 'parks': len(RO), 'gained': rch['gained'], 'lost': rch['lost'],
                          'outline_to_pin': rch['outline_to_pin'], 'pin_to_outline': rch['pin_to_outline']}
    else: notes.append('released key not found (RELEASED_DIR / ./released/data/<kind>-key): outline -> pin is measured against the previous build only')
    here = os.getcwd()
    try:
        os.chdir(cwd); pins = PC.pota_pins() if PC else {}
    finally: os.chdir(here)
    if not pins: notes.append('no POTA pins found (data/pota, locations.json, data/canada.json): the pin checks are empty')
    bounds = os.path.join(cwd, env.get('CA_BOUNDS') or 'data/canada-bounds') if k == 'ca' else None
    who = AW.persons(env.get('KPC_PERSONS')) if AW else set()
    sheet = sheet_check(N, k, env.get('ANSWER_SHEET', os.path.join(cwd, 'kpcdata/data/answer-sheet')), who)
    if not sheet['read']: notes.append('answer sheet not read (ANSWER_SHEET folder missing): no sheet check')
    else: notes.append(f"answer sheet: {sheet['rows']} rows, {sheet['signed']} signed by a person; {sheet['proposed_disagree']} PROPOSED rows name another record (bot proposals: counted, not used)")
    pre = precheck_flags(N, env.get('PRECHECK_OUT', '/tmp/kpc-precheck'))
    if not pre['read']: notes.append('pre-check output not found (PRECHECK_OUT): REVIEW_PILE / RULE 18 / bad-pin flags not checked')
    edge = []
    rep = {'key': k, 'build': build, 'built': idx.get('built') or '', 'checked': time.strftime('%Y-%m-%d %H:%M', time.gmtime()), 'new_ref': newest[:12] if newest else 'none found',
           'new_what': f'git {new_ref}' if new_ref else 'the checked-out files (main as the build left it, plus any later commits)',
           'prev_ref': (git('rev-parse', '--short=12', prev_ref, cwd=cwd) or prev_ref or '').strip() if prev_ref else '', 'changes': ch,
           'flat': flat(N, k, bounds), 'pins_outside': pins_outside(N, k, pins, bounds, edge), 'pins_at_edge': edge, 'bad_pins': bad_pins(N, pins),
           'answer_sheet': sheet, 'overrides': override_check(N, k, cwd=cwd, built=str(idx.get('built') or '')), 'precheck': pre, 'must_pin': must_pin(N, k), 'notes': notes}
    ft = fers_touch(ch['outline_changed'] + ch['outline_to_pin'] + ch['lost'], env.get('FERS_DIR'))
    if ft is not None: rep['fers_touched'] = ft; notes.append(f"2-fer rows naming a changed / dropped / lost park: {ft['rows']} (they were measured on the old outline)")
    newp = {r for r in ch['gained'] + ch['pin_to_outline'] + ch['outline_changed']}
    rep['summary'] = {'parks now': len(N), 'parks before': len(O), 'gained': len(ch['gained']), 'lost': len(ch['lost']), 'outline -> pin': len(ch['outline_to_pin']),
                      'pin -> outline': len(ch['pin_to_outline']), 'outline changed': len(ch['outline_changed']), 'flat outlines': len(rep['flat']),
                      'flat outlines new or changed this build': sum(1 for x in rep['flat'] if x['park'] in newp),
                      'pins outside outline': len(rep['pins_outside']), 'pins outside, new or changed this build': sum(1 for x in rep['pins_outside'] if x['park'] in newp),
                      "pins just outside, key says 'edge' (not listed)": len(rep['pins_at_edge']),
                      '0,0 / impossible pins': len(rep['bad_pins']), 'signed sheet answers not followed': len(sheet['signed_disagree']),
                      'overrides not followed': len(rep['overrides']),
                      'overrides not followed, dated before the build (a real miss)': sum(1 for x in rep['overrides'] if x.get('newer_than_build') is False), 'pre-check HOLD still outline': len(pre['hold_still_outline']), 'RULE 18 flags': len(pre['rule18']),
                      'must-be-pin not yet pin': sum(1 for x in rep['must_pin'] if x['result'] != 'PASS (pin)')}
    # Nov 7 (Brandon 4:55 PM CST): the problem solver's recommended fix per held park (kpc_problem_solver.py, recommends only)
    try:
        ps = json.load(open(os.path.join(cwd, KEYS[k]['dir'], 'review', 'problem-solver.json'), encoding='utf-8'))
        rep['problem_solver'] = ps.get('parks') or []; rep['summary']['problem solver verdicts'] = len(rep['problem_solver'])
        for v, n in sorted((ps.get('counts') or {}).items()): rep['summary'][f'problem solver: {v}'] = n
    except Exception: rep['problem_solver'] = None  # noqa: BLE001
    if ch.get('released'):
        _r = ch['released']
        rep['summary'][f"outline -> pin vs released ({_r['build'] or 'KPC-Data'})"] = len(_r['outline_to_pin'])
        rep['summary'][f"pin -> outline vs released ({_r['build'] or 'KPC-Data'})"] = len(_r['pin_to_outline'])
        rep['summary']['gained / lost vs released'] = f"{len(_r['gained'])} / {len(_r['lost'])}"
        if _r['outline_to_pin']: note('warning', f"{k} key {build}: {len(_r['outline_to_pin'])} outline -> pin against the RELEASED key {_r['build']}: {', '.join(_r['outline_to_pin'][:15])}")
    rep['pin_jump'] = pj = pin_jump(ch)
    rep['summary'][f'countries with {PIN_JUMP}+ outline -> pin (a lost source layer?)'] = len(pj)
    if pj:
        notes.append(f"outline -> pin jumped in {', '.join(f'{c} {n}' for c, n in pj.items())} ({PIN_JUMP}+ in one country): check that build's source reads before trusting it")
        note('warning', f"{k} key {build}: outline -> pin jumped in {', '.join(f'{c} {n}' for c, n in pj.items())} ({PIN_JUMP}+ in one country; a source layer may have been lost)")
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f'{k}-{build}'
    json.dump(rep, open(f'{base}.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    open(f'{base}.md', 'w', encoding='utf-8').write(md(rep))
    json.dump({'key': k, 'build': build, 'build_commit': newest, 'report': f'{base.name}.json', 'checked': rep['checked']}, open(last_f, 'w'), indent=1)
    s = rep['summary']
    note('notice', f"{k} key {build}: +{s['gained']} / -{s['lost']} parks, {s['outline -> pin']} outline->pin, {s['pin -> outline']} pin->outline, "
                   f"{s['outline changed']} outlines changed, {s['signed sheet answers not followed']} signed answers not followed, {s['overrides not followed']} overrides not followed, "
                   f"must-be-pin not yet pin: {s['must-be-pin not yet pin']} -> {base}.md")
    return rep


if __name__ == '__main__':
    try: run()
    except Exception as e:  # noqa: BLE001  (never fail the build: the error is a line in the log)
        import traceback; traceback.print_exc()
        note('warning', f'the key check stopped with an error ({type(e).__name__}: {e}); the build is not affected')
    sys.exit(0)
