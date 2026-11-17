#!/usr/bin/env python3
"""THE SCORECARD (KPC owner, 2026-11-17; matching plan section 4, handoff 8 part 1). How good is the US key's matching on its own?

People's answers are the answer sheet. For each state asked for, the US key is built TWICE, offline, in two scratch copies of this
checkout (nothing in the checkout is written):
  TODAY   the key as it is: the overrides as they are.
  HIDDEN  the people's answers hidden: overrides.json emptied (no join / YES / NO / alias / none / tract; its part files and the
          bad-id block list left out), the person-reviewed rows ('how' starts with 'reviewed') taken out of the old key file the
          builder starts from, so nothing a person said can be carried in.
Both runs: KPC_KEY_REMATCH_IDS=1 (no saved ids carried), GEO_CACHE_MODE=only + KPC_KEY_OFFLINE=1 (no network at all),
KPC_MASTER_OWNS=1, GEO_DETAIL=0.001, GEO_PAGE=200, KPC_ANSWER_SHEET=off, one fixed KPC_BUILD_DATE, PYTHONHASHSEED=0. The only
difference between the two runs is the people's answers. Two offline runs are compared, never an offline run with the published file.

The answer sheet (per state):
  person YES  every row of the TODAY run whose 'how' starts with 'reviewed' (a person's join as it stands after today's fingerprint
              re-find), EXCEPT the rows a code rule writes with that tag (the wetland-district fee tracts and the rule-18 tract
              list in kpc_key_rules.TRACT_SPLITS): those come back in the hidden run too, so they would only flatter the grade.
  person NO   every entry of a park's 'no' list in data/us-key/overrides.json + its parts (read with kpc_overrides.py), plus the
              bad-id block list (blocked_ids, as the key reads it). Matched as the key matches a NO (kpc_key_rules.is_no: the id, an
              exact name typed in 'no', and with KPC_NO_BY_NAME=1 the saved name + acres).
  reviewed park  a park with at least one person-YES row in the TODAY run, or whose override says none: true (a person looked and
              found no official outline).
The grade of the HIDDEN run (one line per state):
  FOUND  share of person-YES records the matcher joins by itself (same record id on the same park); also BY PARK: of the parks
         with a person-YES, how many get at least one of the person's records (and how many get all), since one park a person
         split into hundreds of parcels would otherwise outweigh a state.
  WRONG  person-NO records it joins (count, and share of the person-NO entries of that state).
  EXTRA  records it joins on reviewed parks that the person did not choose (and not a NO: that is WRONG); share of all its joins
         on reviewed parks. Split by kind, a reading aid only (see extra_kind): other land / same name / same size as the person's
         record (most often the same land in a second layer) / on a none: true park. The top 20 are listed, other land first, busiest
         park first, for a person to skim.
  Each again weighted by activations (POTA activation count, data/parkinfo/<area>.json field 7): a record counts as its park's
  activations. A park with no activation count weighs 0; the line says how many parks of the state have a count.
  The TODAY run is graded the same way as a self-check (FOUND should be about 100% and WRONG 0 there).

Any rule switch can be given (--set KPC_ONE_RECORD_ONE_PARK=1 ...): it goes to BOTH runs, so the same answer sheet grades the switch.
Switches (kpc_key_rules.DEFAULTS) and the other matching settings not given with --set are taken out of the inherited environment,
so a stray variable in the caller's shell never changes a grade. --vs an earlier scorecard JSON prints the change per state.

Output, outside data/ (the folder given with --out; refused inside the checkout's data/):
  <out>/scorecard-<label>.txt   the per-state lines + the top-20 EXTRA lists
  <out>/scorecard-<label>.json  counts, switches, timings, and the park lists (found / missed / wrong / extra)
  <out>/scorecard-<label>-logs/ each builder log (TODAY / HIDDEN per state)
The scratch copies (<out>/scratch-<label>/) are deleted at the end unless --keep.

  python3 .github/scripts/kpc_key_scorecard.py run --states "OH WI" --cache DIR --kpc-data DIR --out DIR [--set K=V ...]
          [--activations DIR] [--label NAME] [--vs OLD.json] [--keep] [--date YYYY-MM-DD]
      --cache     a folder holding US-XX.json.gz (the boundary-cache release assets; hand-US-XX.* files are copied too)
      --kpc-data  a KentuckyPortableClub/KPC-Data checkout: the moved paths (.github/kpc-moved.txt: data/parkinfo, data/trails ...)
                  are laid into both scratch copies, as the key workflow's overlay does
      --activations  a data/parkinfo folder to read the activation counts from (default: the one in --kpc-data)
  python3 .github/scripts/kpc_key_scorecard.py compare --today US-XX.json --hidden US-XX.json --overrides overrides.json
          --parkinfo US-XX.json [--set K=V ...]     grade two key files already built (no build; prints the line + JSON)

Not a rule file (kpc_key_freeze.NOT_RULES): it decides no join and writes nothing into the checkout. Standard library only."""
import argparse, json, os, pathlib, re, shutil, subprocess, sys, threading, time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kpc_key_rules as KR  # noqa: E402
import kpc_overrides as _KOVR  # noqa: E402

REPO = HERE.parents[1]
KEY = '.github/scripts/kpc_us_key.py'
# the rows a code rule tags 'reviewed' (they come back with the answers hidden, so they are not a person's answer here)
RULE_TAGS = ('reviewed: the district = FWS fee', 'reviewed (official tract:')
# person answers inside one override (all emptied in the hidden run: the whole park entry goes)
FIXED_ENV = {'KPC_KEY_REMATCH_IDS': '1', 'GEO_CACHE_MODE': 'only', 'KPC_KEY_OFFLINE': '1', 'KPC_MASTER_OWNS': '1',
             'GEO_DETAIL': '0.001', 'GEO_PAGE': '200', 'GEO_CACHE': 'cache/us', 'KPC_ANSWER_SHEET': 'off', 'PYTHONHASHSEED': '0',
             'PYTHONDONTWRITEBYTECODE': '1', 'MINUTES': '600'}
# matching settings that are never inherited from the caller's shell (only --set gives them)
SCRUB = set(KR.DEFAULTS) | {'KPC_ANSWER_SHEET', 'KPC_KEY_ONLY_PARKS', 'KPC_KEY_ONLY_STATES', 'SHADOW', 'NAME_JOIN', 'STATES',
                            'FINISH_ONLY', 'KPC_REFILL_ONLY', 'KPC_LAYER_IN', 'KPC_LAYER_OUT', 'KPC_REFILL_FORCE', 'ANSWER_SHEET_FILE',
                            'ANSWER_SHEET_CHECK', 'KPC_KEY_REMATCH_IDS', 'GEO_CACHE', 'GEO_CACHE_MODE', 'KPC_BUILD_DATE'}
# checkout paths a US key build never reads: left out of the scratch copies (speed only)
# (the box has few inodes to spare: data/pota alone is 8,700 small files)
SKIP_PREFIXES = ('img/', 'app/', '.claude/', 'data/released/', 'data/outlines/', 'data/canada-bounds/', 'data/maprep-layers/', 'data/pota/')
# KPC-Data moved paths the US key never reads (the other moved paths are laid in)
SKIP_MOVED = {'data/wwff', 'data/sota', 'data/sota-land', 'data/leaders', 'data/alerts'}
SKIP_SUFFIXES = ('.png', '.jpg', '.jpeg', '.pdf', '.mp4', '.zip')
TOP = 20


# ------------------------------------------------------------------ the answer sheet + the grade (pure; the fixture test runs this)
def _sid(x): return str(x)


def is_rule_row(how): return str(how or '').startswith(RULE_TAGS)


def person_row(how): return str(how or '').startswith('reviewed') and not is_rule_row(how)


def activations(parkinfo_parks):
    """{ref: activation count} from a data/parkinfo/<area>.json 'parks' object (field 7); a missing / non-number value is left out."""
    out = {}
    for ref, v in (parkinfo_parks or {}).items():
        a = v[7] if isinstance(v, list) and len(v) > 7 else None
        if isinstance(a, (int, float)) and not isinstance(a, bool): out[ref] = a
    return out


def overrides_with_blocks(doc):
    """{ref: override} with the bad-id block list folded in as NOs (as kpc_us_key.py does)."""
    ovr = {r: dict(v or {}) for r, v in (doc.get('parks') or {}).items()}
    for b in doc.get('blocked_ids') or []:
        if not (isinstance(b, dict) and b.get('ref') and b.get('id') not in (None, '') and str(b.get('decided_by') or '').strip()): continue
        o = ovr.setdefault(b['ref'], {})
        if str(b['id']) not in {str(x) for x in o.get('no') or []}: o['no'] = list(o.get('no') or []) + [str(b['id'])]
    return ovr


def no_entry(ov, x):
    """Which entry of the park's 'no' list a joined row [id, name, ...] falls under: its id, else its exact name, else the saved
    NO fingerprint (nofp, KPC_NO_BY_NAME) whose name it carries. One entry can catch several records (a NO typed as a name)."""
    nos = [str(e) for e in ov.get('no') or []]
    if str(x[0]) in nos: return str(x[0])
    n = KR.nf(x[1] if len(x) > 1 else '')
    for e in nos:
        if KR.nf(e) == n: return e
    for k, v in (ov.get('nofp') or {}).items():
        if v and KR.nf(v[0]) == n: return str(k)
    return '?'


# EXTRA kinds (a reading aid, never a rule). Many states publish one place in several layers (PAD-US + two state layers), or as many
# parcels, and a person picked ONE record:
#   copy       the same size as a record the person chose on that park (acres within 10%, 20 acres at least): most often the same land
#              in a second layer
#   same-name  the same name words as a record the person chose, or as the park (type words dropped), another size: a parcel or a
#              bigger / smaller version of the same place (worth a look: the person's record may be the partial one)
#   none-park  on a park whose override says none: true (a person found no official outline)
#   other      everything else: other land, the real suspects. Listed first.
# the agencies' short forms, written out, so 'Adams Lake SP' and 'Adams Lake State Park' carry the same words (a type word that differs,
# SP vs SF, still differs: 'Beaver Creek SF' is not the same name as Beaver Creek State Park)
_SHORT = {'sp': 'park', 'sf': 'forest', 'wa': 'wildlife area', 'wma': 'wildlife management area', 'sra': 'recreation area',
          'shp': 'historic park', 'shs': 'historic site', 'sb': 'beach', 'nf': 'national forest', 'nwr': 'national wildlife refuge',
          'nra': 'national recreation area', 'sna': 'natural area', 'swa': 'wildlife area', 'fwa': 'fish and wildlife area',
          'sgl': 'game lands', 'gl': 'game land', 'np': 'national park', 'nrma': 'natural resource management area', 'dnp': 'nature preserve'}
_DROP = {'state', 'the', 'of', 'and'}
KIND_ORDER = {'other': 0, 'same-name': 1, 'none-park': 2, 'copy': 3}


def name_words(t):
    import re as _re, unicodedata as _u
    t = _u.normalize('NFKD', str(t or '')).encode('ascii', 'ignore').decode().casefold()
    t = _re.sub(r'\(.*?\)', ' ', t)
    words = ' '.join(_SHORT.get(w, w) for w in _re.findall(r'[a-z0-9]+', t)).split()
    return frozenset(w for w in words if w not in _DROP)


def _num(v):
    try: return float(v or 0)
    except (TypeError, ValueError): return 0.0


def extra_kind(x, chosen, park_name='', none_park=False):
    """x = a joined row [id, name, acres, ...] the person did not choose; chosen = the person-YES rows of that park."""
    if none_park and not chosen: return 'none-park'
    a, nw = _num(x[2] if len(x) > 2 else 0), name_words(x[1] if len(x) > 1 else '')
    for y in chosen:
        b = _num(y[2] if len(y) > 2 else 0)
        if a and b and abs(a - b) <= max(20.0, .1 * max(a, b)): return 'copy'
    if nw and (nw == name_words(park_name) or any(nw == name_words(y[1] if len(y) > 1 else '') for y in chosen)): return 'same-name'
    return 'other'


def _pct(a, b): return round(100.0 * a / b, 1) if b else None


def grade(today_parks, hidden_parks, ovr, act, env=None):
    """Grade one state. today_parks / hidden_parks = the 'parks' objects of the two key files, ovr = {ref: override} (with
    overrides_with_blocks), act = {ref: activations}. Returns the counts and the lists (rows are [ref, id, name, acres, how, act])."""
    env = {} if env is None else env
    by_name = KR.on('KPC_NO_BY_NAME', env)
    refs = sorted(set(today_parks) | set(hidden_parks))
    A = lambda r: act.get(r, 0) or 0
    yes, rule_rows, reviewed = {}, 0, set()
    for r in refs:
        for x in (today_parks.get(r) or {}).get('m') or []:
            if person_row(x[3] if len(x) > 3 else ''): yes.setdefault(r, {})[_sid(x[0])] = x
            elif is_rule_row(x[3] if len(x) > 3 else ''): rule_rows += 1
        if yes.get(r) or (ovr.get(r) or {}).get('none'): reviewed.add(r)
    no_n = no_w = 0
    for r in refs:
        k = len((ovr.get(r) or {}).get('no') or [])
        no_n += k; no_w += k * A(r)

    def score(parks):
        found, missed, wrong, extra, hit = [], [], [], [], set()
        joins_rev = joins_rev_w = 0
        for r in refs:
            got = {}
            for x in (parks.get(r) or {}).get('m') or []: got.setdefault(_sid(x[0]), x)
            for i, x in sorted((yes.get(r) or {}).items()):
                (found if i in got else missed).append([r, x[0], x[1], x[2] if len(x) > 2 else None, x[3], A(r)])
            ov = ovr.get(r) or {}
            for i, x in sorted(got.items()):
                how = x[3] if len(x) > 3 else ''
                row = [r, x[0], x[1] if len(x) > 1 else '', x[2] if len(x) > 2 else None, how, A(r)]
                if ov.get('no') and KR.is_no(ov, x[0], x[1] if len(x) > 1 else None, x[2] if len(x) > 2 else None, by_name):
                    wrong.append(row); hit.add((r, no_entry(ov, x))); continue
                if r in reviewed and not is_rule_row(how):
                    joins_rev += 1; joins_rev_w += A(r)
                    if i not in (yes.get(r) or {}):
                        row.append(extra_kind(x, list((yes.get(r) or {}).values()), (today_parks.get(r) or {}).get('n') or '', bool(ov.get('none'))))
                        extra.append(row)
        yn = sum(len(v) for v in yes.values()); yw = sum(len(v) * A(r) for r, v in yes.items())
        # per park too: a park a person split into hundreds of parcels (Wisconsin's parcel layer) weighs one park, not 2,000 records
        fp = {x[0] for x in found}; mp = {x[0] for x in missed}
        yp = [r for r in yes if yes[r]]; ypw = sum(A(r) for r in yp)
        fw = sum(x[5] for x in found)
        busiest = sorted(extra, key=lambda x: (KIND_ORDER[x[6]], -x[5], x[0], str(x[1])))   # other land first, then busiest park
        leaked = sum(1 for r in refs for x in (parks.get(r) or {}).get('m') or [] if person_row(x[3] if len(x) > 3 else ''))
        return {'found': len(found), 'yes': yn, 'found_pct': _pct(len(found), yn), 'found_w_pct': _pct(fw, yw),
                'yes_parks': len(yp), 'found_parks': len(fp), 'found_parks_all': len(fp - mp), 'found_parks_pct': _pct(len(fp), len(yp)),
                'found_parks_w_pct': _pct(sum(A(r) for r in fp), ypw),
                'wrong': len(wrong), 'wrong_parks': len({x[0] for x in wrong}), 'no': no_n, 'no_hit': len(hit),
                'wrong_pct': _pct(len(hit), no_n), 'wrong_w_pct': _pct(sum(A(r) for r, _ in hit), no_w),
                'extra': len(extra), 'extra_parks': len({x[0] for x in extra}),
                'extra_other': sum(1 for x in extra if x[6] == 'other'), 'extra_other_parks': len({x[0] for x in extra if x[6] == 'other'}),
                'extra_same_name': sum(1 for x in extra if x[6] == 'same-name'), 'extra_copy': sum(1 for x in extra if x[6] == 'copy'),
                'extra_none_park': sum(1 for x in extra if x[6] == 'none-park'), 'joins_on_reviewed': joins_rev,
                'extra_pct': _pct(len(extra), joins_rev), 'extra_w_pct': _pct(sum(x[5] for x in extra), joins_rev_w),
                'person_rows_in_run': leaked,
                'lists': {'found': found, 'missed': missed, 'wrong': wrong, 'extra': busiest, 'extra_top': busiest[:TOP]}}
    out = {'parks': len(refs), 'reviewed_parks': len(reviewed), 'rule_rows_left_out': rule_rows,
           'parks_with_activations': sum(1 for r in refs if r in act), 'activations': sum(A(r) for r in refs),
           'hidden': score(hidden_parks), 'today': score(today_parks)}
    return out


def _p(v): return '-' if v is None else f'{v:.1f}%'


def line(st, g, secs=None):
    h, t = g['hidden'], g['today']
    s = (f"{st}  FOUND {h['found']} of {h['yes']} person-YES records = {_p(h['found_pct'])} (by activations {_p(h['found_w_pct'])});"
         f" by park {h['found_parks']} of {h['yes_parks']} = {_p(h['found_parks_pct'])} get at least one, {h['found_parks_all']} get all"
         f" (by activations {_p(h['found_parks_w_pct'])})"
         f" | WRONG {h['wrong']} records on {h['wrong_parks']} parks, hitting {h['no_hit']} of {h['no']} person-NO entries = {_p(h['wrong_pct'])}"
         f" (by activations {_p(h['wrong_w_pct'])})"
         f" | EXTRA {h['extra']} records on {h['extra_parks']} of {g['reviewed_parks']} reviewed parks = {_p(h['extra_pct'])} of its joins there"
         f" (by activations {_p(h['extra_w_pct'])}; other land {h['extra_other']} on {h['extra_other_parks']} parks, same name {h['extra_same_name']},"
         f" same size as the person's record {h['extra_copy']}, on none-parks {h['extra_none_park']})"
         f" | today run: FOUND {_p(t['found_pct'])}, WRONG {t['wrong']}, EXTRA {t['extra']}"
         f" | activations known for {g['parks_with_activations']} of {g['parks']} parks")
    if secs: s += f" | build {secs.get('today', '?')} s today, {secs.get('hidden', '?')} s hidden"
    return s


def extra_lines(st, g):
    rows = g['hidden']['lists']['extra_top']
    if not rows: return [f'{st} EXTRA: none']
    out = [f'{st} EXTRA, top {len(rows)} of {g["hidden"]["extra"]} (other land first, busiest park first): park | activations | record id | record name | acres | how | kind']
    out += [f'  {r[0]} | {r[5]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[6]}' for r in rows]
    return out


def vs_lines(new, old):
    out = []
    for st, g in sorted(new.get('states', {}).items()):
        o = (old.get('states') or {}).get(st)
        if not o: out.append(f'{st}: not in the earlier scorecard'); continue
        a, b = o['hidden'], g['hidden']
        d = lambda k: (None if a.get(k) is None or b.get(k) is None else round(b[k] - a[k], 1))
        warn = []
        if (d('found_pct') or 0) < 0: warn.append('FOUND went DOWN')
        if b['wrong'] > a['wrong']: warn.append('WRONG went UP')
        out.append(f"{st} vs earlier: FOUND {_p(a['found_pct'])} -> {_p(b['found_pct'])} ({d('found_pct'):+}), WRONG {a['wrong']} -> {b['wrong']}, "
                   f"EXTRA {a['extra']} -> {b['extra']}" + (f"  ** {'; '.join(warn)}: needs the owner's word (matching plan 4)" if warn else ''))
    return out


# ------------------------------------------------------------------ the scratch copies + the two builds
def parse_sets(pairs):
    env = {}
    for p in pairs or []:
        for one in str(p).split():
            m = re.fullmatch(r'([A-Z][A-Z0-9_]*)=(.*)', one)
            if not m: raise SystemExit(f'--set {one!r}: give NAME=VALUE (for example KPC_ONE_RECORD_ONE_PARK=1)')
            if m.group(1) in FIXED_ENV or m.group(1) in ('STATES', 'KPC_BUILD_DATE'):
                raise SystemExit(f'--set {m.group(1)}: the scorecard fixes that one (it is the same on both runs)')
            env[m.group(1)] = m.group(2)
    return env


def build_env(base, sets, date, offline_log):
    e = {k: v for k, v in base.items() if k not in SCRUB}
    e.update(FIXED_ENV); e['KPC_BUILD_DATE'] = date; e['KPC_OFFLINE_LOG'] = str(offline_log)
    e.update(sets)
    return e


def tracked_files(repo):
    r = subprocess.run(['git', '-C', str(repo), 'ls-files', '-z'], capture_output=True, check=True)
    return [p for p in r.stdout.decode('utf-8', 'surrogateescape').split('\0') if p]


def copy_tree(repo, dest, files=None):
    """A scratch copy of the checkout as it is on disk (tracked files, with any local edit), minus the paths a key build never reads."""
    repo, dest = pathlib.Path(repo), pathlib.Path(dest)
    for p in files if files is not None else tracked_files(repo):
        if p.startswith(SKIP_PREFIXES) or p.lower().endswith(SKIP_SUFFIXES): continue
        s = repo / p
        if not s.is_file(): continue
        (dest / p).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(s, dest / p)


# KPC-Data paths the key workflow lays in besides the moved list: the Recreation.gov saved copy and the official pin fills (the same
# list as kpc_key_proof.KPC_DATA_EXTRA; the test checks they agree)
KPC_DATA_EXTRA = ['data/access-leads/keyed-pull-raw.json.gz', 'data/intake']


def lay_kpc_data(tree, kpc_data):
    """KPC-Data's moved paths (.github/kpc-moved.txt) + KPC_DATA_EXTRA laid over the copy, as the key workflow does."""
    tree, kd = pathlib.Path(tree), pathlib.Path(kpc_data)
    mf = tree / '.github/kpc-moved.txt'
    moved = [l.strip() for l in mf.read_text().splitlines()] if mf.is_file() else []
    laid = []
    for p in [x for x in moved if x and not x.startswith('#') and x not in SKIP_MOVED] + KPC_DATA_EXTRA:
        s = kd / p
        if s.is_dir():
            if (tree / p).is_dir(): shutil.rmtree(tree / p)
            elif (tree / p).exists(): (tree / p).unlink()
            shutil.copytree(s, tree / p); laid.append(p)
        elif s.is_file():
            (tree / p).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(s, tree / p); laid.append(p)
    return laid


def lay_cache(tree, cache, states):
    cdir = pathlib.Path(tree) / 'cache/us'; cdir.mkdir(parents=True, exist_ok=True); have = []
    for st in states:
        for f in sorted(pathlib.Path(cache).glob(f'US-{st}.json.gz')) + sorted(pathlib.Path(cache).glob(f'hand-US-{st}.*')):
            shutil.copyfile(f, cdir / f.name); have.append(f.name)
    return have


def hide_answers(tree, states):
    """The HIDDEN copy: an empty override set (one file, no parts, no block list) and no person-reviewed row in the old key files."""
    k = pathlib.Path(tree) / 'data/us-key'
    for f in k.glob(_KOVR.PART_GLOB): f.unlink()
    (k / 'overrides.json').write_text(json.dumps({'note': 'scorecard: the people\'s answers are hidden in this scratch copy',
                                                  'blocked_ids': [], 'parks': {}}, indent=1) + '\n')
    stripped = 0
    for st in states:
        f = k / f'US-{st}.json'
        if not f.is_file(): continue
        d = json.loads(f.read_text(encoding='utf-8'))
        for p in (d.get('parks') or {}).values():
            m = p.get('m') or []
            keep = [x for x in m if not str(x[3] if len(x) > 3 else '').startswith('reviewed')]
            stripped += len(m) - len(keep)
            if len(keep) != len(m): p['m'] = keep
        f.write_text(json.dumps(d, separators=(',', ':')))
    return stripped


def build_one(tree, st, env, log):
    t0 = time.time()
    with open(log, 'w') as fh:
        r = subprocess.run([sys.executable, KEY], cwd=str(tree), env=dict(env, STATES=st), stdout=fh, stderr=subprocess.STDOUT)
    secs = round(time.time() - t0)
    text = pathlib.Path(log).read_text(errors='replace')
    ok = r.returncode == 0 and re.search(rf'^{st}: \d+ parks, ', text, re.M) is not None
    why = '' if ok else (f'exit {r.returncode}' if r.returncode else f'no "{st}: N parks" line (the builder skipped or failed the state)')
    return {'ok': ok, 'secs': secs, 'why': why}


def run(args):
    repo = pathlib.Path(args.repo).resolve()
    out = pathlib.Path(args.out).resolve()
    data_dir = (repo / 'data').resolve()
    if out == data_dir or data_dir in out.parents: raise SystemExit(f'--out {out}: never inside the checkout\'s data/ (pick a scratch folder)')
    states = [s.upper() for s in ' '.join(args.states).replace(',', ' ').split()]
    if not states or any(not re.fullmatch(r'[A-Z]{2}', s) or s == 'KY' for s in states):
        raise SystemExit('--states: two-letter US states, not KY (the Kentucky key is its own tool)')
    sets = parse_sets(args.set)
    date = args.date or time.strftime('%Y-%m-%d')
    label = args.label or ('off' if not sets else '_'.join(f'{k}-{v}' for k, v in sorted(sets.items())))
    label = re.sub(r'[^A-Za-z0-9_.=-]+', '_', label)
    out.mkdir(parents=True, exist_ok=True)
    missing = [s for s in states if not (pathlib.Path(args.cache) / f'US-{s}.json.gz').is_file()]
    if missing: raise SystemExit(f'--cache {args.cache}: no saved copy for {" ".join(missing)} (download US-XX.json.gz from the boundary-cache release)')
    ovdoc = _KOVR.load(repo / 'data/us-key/overrides.json')   # fails closed: a missing / bad part stops the scorecard
    ovr = overrides_with_blocks(ovdoc)
    scratch = out / f'scratch-{label}'; logs = out / f'scorecard-{label}-logs'
    if scratch.exists(): shutil.rmtree(scratch)
    logs.mkdir(parents=True, exist_ok=True)
    t_today, t_hidden = scratch / 'today', scratch / 'hidden'
    t0 = time.time()
    files = tracked_files(repo)
    for t in (t_today, t_hidden):
        copy_tree(repo, t, files)
        lay_kpc_data(t, args.kpc_data)
        lay_cache(t, args.cache, states)
    stripped = hide_answers(t_hidden, states)
    prep = round(time.time() - t0)
    act_dir = pathlib.Path(args.activations) if args.activations else t_today / 'data/parkinfo'
    env_t = build_env(os.environ, sets, date, scratch / 'offline-today.txt')
    env_h = build_env(os.environ, sets, date, scratch / 'offline-hidden.txt')
    switches = {k: KR.setting(k, env_t) for k in sorted(KR.DEFAULTS)}
    res = {'about': 'KPC key scorecard (matching plan section 4): the US key built twice offline, the people\'s answers hidden in the second run',
           'date': date, 'label': label, 'set': sets, 'switches': switches, 'commit': _head(repo), 'states': {}, 'failed': {},
           'prep_seconds': prep, 'person_rows_stripped_from_old_key': stripped}
    lines, extras = [], []
    for st in states:
        r = {}
        th = threading.Thread(target=lambda: r.__setitem__('hidden', build_one(t_hidden, st, env_h, logs / f'{st}-hidden.log')))
        th.start(); r['today'] = build_one(t_today, st, env_t, logs / f'{st}-today.log'); th.join()
        secs = {k: v['secs'] for k, v in r.items()}
        bad = {k: v['why'] for k, v in r.items() if not v['ok']}
        if bad:
            res['failed'][st] = bad; lines.append(f'{st}  NOT GRADED: ' + '; '.join(f'{k} run: {v}' for k, v in bad.items()) + f' (logs: {logs})')
            print(lines[-1], flush=True); continue
        td = json.loads((t_today / f'data/us-key/US-{st}.json').read_text(encoding='utf-8')).get('parks') or {}
        hd = json.loads((t_hidden / f'data/us-key/US-{st}.json').read_text(encoding='utf-8')).get('parks') or {}
        pf = act_dir / f'US-{st}.json'
        act = activations(json.loads(pf.read_text(encoding='utf-8')).get('parks') if pf.is_file() else {})
        g = grade(td, hd, {k: v for k, v in ovr.items() if k in td or k in hd}, act, env_t)
        g['seconds'] = secs
        res['states'][st] = g
        lines.append(line(st, g, secs)); extras += extra_lines(st, g)
        print(lines[-1], flush=True)
    tot = _totals(res['states'])
    if tot: res['all'] = tot; lines.append(line('ALL', tot))
    if args.vs:
        old = json.loads(pathlib.Path(args.vs).read_text(encoding='utf-8'))
        lines += [''] + vs_lines(res, old)
    head = [f"KPC key scorecard {date} | label {label} | switches set: {' '.join(f'{k}={v}' for k, v in sorted(sets.items())) or 'none (defaults)'}"
            f" | commit {res['commit'][:12]} | {stripped} person rows taken out of the hidden run's old key files", '']
    (out / f'scorecard-{label}.txt').write_text('\n'.join(head + lines + [''] + extras) + '\n')
    (out / f'scorecard-{label}.json').write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n')
    for x in lines[len(states):]: print(x, flush=True)
    print(f'wrote {out / f"scorecard-{label}.txt"} and .json', flush=True)
    if not args.keep: shutil.rmtree(scratch, ignore_errors=True)
    return 1 if res['failed'] else 0


def _totals(states):
    if not states: return None
    keys = ('found', 'yes', 'yes_parks', 'found_parks', 'found_parks_all', 'wrong', 'wrong_parks', 'no', 'no_hit', 'extra', 'extra_parks', 'extra_other', 'extra_other_parks', 'extra_same_name', 'extra_copy', 'extra_none_park', 'joins_on_reviewed', 'person_rows_in_run')
    t = {'parks': sum(g['parks'] for g in states.values()), 'reviewed_parks': sum(g['reviewed_parks'] for g in states.values()),
         'parks_with_activations': sum(g['parks_with_activations'] for g in states.values())}
    for side in ('hidden', 'today'):
        s = {k: sum(g[side][k] for g in states.values()) for k in keys}
        s['found_pct'] = _pct(s['found'], s['yes']); s['found_parks_pct'] = _pct(s['found_parks'], s['yes_parks']); s['found_parks_w_pct'] = None; s['wrong_pct'] = _pct(s['no_hit'], s['no']); s['extra_pct'] = _pct(s['extra'], s['joins_on_reviewed'])
        for k in ('found_w_pct', 'wrong_w_pct', 'extra_w_pct'): s[k] = None   # weighted shares are per state (their bases differ)
        t[side] = s
    return t


def _head(repo):
    try: return subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
    except Exception: return ''  # noqa: BLE001


def compare(args):
    sets = parse_sets(args.set)
    td = json.loads(pathlib.Path(args.today).read_text(encoding='utf-8')).get('parks') or {}
    hd = json.loads(pathlib.Path(args.hidden).read_text(encoding='utf-8')).get('parks') or {}
    ovr = overrides_with_blocks(_KOVR.load(args.overrides))
    pi = json.loads(pathlib.Path(args.parkinfo).read_text(encoding='utf-8')).get('parks') if args.parkinfo else {}
    g = grade(td, hd, ovr, activations(pi), build_env({}, sets, '2000-01-01', '-'))
    st = args.state or re.sub(r'^US-|\.json$', '', pathlib.Path(args.today).name)
    print(line(st, g)); print('\n'.join(extra_lines(st, g)))
    if args.json: pathlib.Path(args.json).write_text(json.dumps({'states': {st: g}}, indent=1, ensure_ascii=False) + '\n')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run'); r.add_argument('--states', nargs='+', required=True); r.add_argument('--cache', required=True)
    r.add_argument('--kpc-data', required=True); r.add_argument('--out', required=True); r.add_argument('--set', action='append')
    r.add_argument('--activations'); r.add_argument('--label'); r.add_argument('--vs'); r.add_argument('--keep', action='store_true')
    r.add_argument('--date'); r.add_argument('--repo', default=str(REPO))
    c = sub.add_parser('compare'); c.add_argument('--today', required=True); c.add_argument('--hidden', required=True)
    c.add_argument('--overrides', required=True); c.add_argument('--parkinfo'); c.add_argument('--set', action='append')
    c.add_argument('--state'); c.add_argument('--json')
    a = ap.parse_args(argv)
    return run(a) if a.cmd == 'run' else compare(a)


if __name__ == '__main__':
    sys.exit(main())
