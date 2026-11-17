#!/usr/bin/env python3
"""MISSING CHECK (chat 2, Oct 27 2026; HQ 3:46 PM, Brandon: 'chat 8 can't verify what's missing'). For each area of a 2-fer run, every
pair of parks we have an OUTSIDE reason to expect, with what the bot did with it:
  FOUND            a live row (candidate / very tight / water only, or folded into one)
  DROPPED          a pair we looked at and did not show. Its COUNT is in the pushed file; the list, with the exact reason + the
                   rule, goes to the PRIVATE folder (expected-dropped-<tag>.json), because no file we publish may say a pair is
                   not a 2-fer (KPC owner, 2026-11-15 23:14; re-grade R2, 2026-11-16)
  NEVER LOOKED AT  the bot never tested the pair, with why (no official outline, a line park with no line, not in the run…)
Sources (why each pair is expected): 'hand list' = ky-trail-parks.json (Kentucky's river / trail pairs) · 'old guide' = the
Oct 13 Kentucky 2-fers guide (ky-overlaps.geojson, 76 pairs) · 'near-touching' = outlines within 100 m (pass 1's looked file) ·
'member report' (data/fers/member-reports.json, later). POTA activation history (two parks worked by one call on one day) is NOT a
source (KPC owner, 2026-11-16, rule N6: logging mistakes and short drives between nearby parks make it no evidence; only the
official boundaries decide). Writes data/fers/expected-<area>.json; 'pass' = no NEVER LOOKED AT without a reason and
every DROPPED with a reason (both worked out before the DROPPED list is moved out). Chat 8 reviews the DROPPED list in the
private folder + the NEVER LOOKED AT list in the file. AREA='ky' or STATES='US-OH'. Never fails.
Public outline-store run (KPC owner, 2026-11-15; store trial M4: KPC_FERS_FROM_STORE on, KPC_FERS_STORE_KIND public): a pair with a
park whose outline the store holds privately (the run's withheld lists in KPC_FERS_PRIVATE_LOG, as the store-missing list reads
them) is left out and only counted, and the file goes through the store's redact + write guard. No readable list = no file
(fail closed: the old file is not touched)."""
import glob, gzip, itertools, json, math, os, pathlib, re, sys, time
OUT = pathlib.Path('data/fers')
LIVE = ('candidate', 'very tight', 'water only', 'merged into')
# KPC owner, 2026-11-15 23:14 ("we just show what we think are overlaps"): a 2-fer file no longer holds a row that denies a pair,
# so a pair the bot stopped looking at has no row here either. Such a pair falls to the 'looked: no shared ground ...' line below
# (rule 4 / rule 5) from pass 1's own looked list; the exact reason is in the run report's 'not shown' list (kpc_fers.no_denials).
RULES = [(r'^dropped: side by side|two owners side by side', 'rule 14 (ownership: side by side, not layered)'),
         (r'^dropped: private', 'rule 2 + B-G2 (private land counts only for its own number)'),
         (r'^dropped: only inside an area closed', 'rule 10 (closed to the public)'),
         (r'^dropped in pass', 'rule 4 (the shared patch did not hold up on the fresher, finer official outlines)'),
         (r'ruling Oct 27', 'Kentucky ruling (Brandon / HQ Oct 27)'),
         (r'^not sure', 'rule 7 (NOT SURE is kept out)'),
         (r'^dropped', 'see the reason')]


DROPPED_PRIVATE = ('The pairs this run looked at and did not show, with the reason. PRIVATE: a person reads it (chat 8). It names '
                   'both parks of each pair beside a reason that reads as "not a 2-fer", so it never goes into a file we publish '
                   '(KPC owner, 2026-11-15 23:14; re-grade R2, 2026-11-16). The published expected-<tag>.json keeps the COUNT.')
DROPPED_NOTE = ('the pairs we looked at and did not show are not listed here: we show only overlaps we believe in, and no file we '
                'publish says a pair is not a 2-fer (KPC owner, 2026-11-15). The count is in "counts"; the list, with each '
                'reason, is in the private folder for a person (expected-dropped-<tag>.json)')


def private_dir():
    """The PRIVATE folder for material that may not be published, or None. The same three environment names and the same
    git-work-tree refusal as kpc_fers.not_shown_file(), so both land in one place."""
    for v in ('KPC_FERS_NOT_SHOWN_DIR', 'KPC_FERS_PRIVATE_OUT', 'KPC_FERS_PRIVATE_LOG'):
        base = str(os.environ.get(v) or '').strip()
        if not base: continue
        try:
            d = pathlib.Path(base).resolve() / 'not-shown'
            probe = d if d.exists() else d.parent
            if any((q / '.git').exists() for q in (probe, *probe.parents)): continue
            d.mkdir(parents=True, exist_ok=True)
            return d
        except OSError: continue
    return None


def split_dropped(res, tag):
    """OWNER RULE (KPC owner, 2026-11-15 23:14): no file we publish may say a pair is not a 2-fer. The DROPPED bucket is exactly
    that - a pair we expected, looked at, and did not show, with the reason - so the list is taken OUT of the file that is pushed
    and written to the private folder instead. What stays in the published file: counts['DROPPED'] (the number), FOUND and
    NEVER LOOKED AT (which say we did NOT test a pair, and why: not a verdict about the parks), 'pass' and the filter counts.
    -> (the private path or None, how many pairs)."""
    rows = res.get('DROPPED')
    if not isinstance(rows, list): return None, 0
    res['DROPPED'] = []
    res['DROPPED (not listed here)'] = DROPPED_NOTE
    d = private_dir()
    if d is None: return None, len(rows)
    f = d / f'expected-dropped-{tag}.json'
    try:
        f.write_text(json.dumps({'about': DROPPED_PRIVATE, 'area': res.get('area'), 'date': res.get('date'),
                                 'DROPPED': rows}, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    except OSError: return None, len(rows)
    return f, len(rows)


def rule_of(st):
    return next((r for rx, r in RULES if re.search(rx, st, re.I)), '')


def load(p, d=None):
    try: return json.load(open(p))
    except Exception: return d  # noqa: BLE001


def store_withheld():
    """Public store run: (refs, names, mask) of the run's withheld lists, or 'off' (not a public store run), or None (a public store
    run with no readable list: write nothing)."""
    on = str(os.environ.get('KPC_FERS_FROM_STORE') or '').strip().lower() in ('1', 'on', 'yes', 'true')
    if not on or str(os.environ.get('KPC_FERS_STORE_KIND') or 'public').strip().lower() == 'private': return 'off'
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import kpc_fers_store as S
    return S.load_withheld(str(os.environ.get('KPC_FERS_PRIVATE_LOG') or '').strip())


def build(area, files, tag='', sts=()):
    wh = store_withheld()
    if wh is None:
        print(f'::warning title=2-fer missing check::{area}: public outline-store run without a readable withheld list: expected-{tag or area}.json is not written', flush=True)
        return
    sec = set(wh[0]) if wh != 'off' else set()
    rows = []
    for f in files:
        for s in (load(f, {}) or {}).get('spots') or []: rows.append((set(s.get('refs') or []), str(s.get('status', '')), s.get('id', '')))
    looked = load(OUT / f'looked-{tag or area}.json', {}) or {}
    tested = {tuple(sorted(p.split('+'))) for p in looked.get('tested') or []}
    noout = looked.get('no_outline') or {}
    inrun = set(looked.get('parks') or [])
    exp = {}
    def add(refs, why):
        refs = tuple(sorted(set(refs)))
        if len(refs) < 2: return
        exp.setdefault(refs, set()).add(why)
    if area == 'ky':
        tp = load('ky-trail-parks.json', {}) or {}
        for t in tp.values():
            if not isinstance(t, dict): continue   # Oct 28: the file's top-level 'checked' note
            for p in t.get('parks') or []: add([t['ref']] + p['refs'], 'hand list (ky-trail-parks.json)')
        g = load('ky-overlaps.geojson', {}) or {}
        for ft in g.get('features') or []:
            refs = sorted({r for r, _ in (ft.get('properties') or {}).get('pota') or []})
            for a, b in itertools.combinations(refs, 2): add([a, b], 'old guide (Oct 13 Kentucky 2-fers guide)')
    sts = ['US-KY'] if area == 'ky' else list(sts)
    for a, b, m in looked.get('near100') or []: add([a, b], f'outlines come within {m} m of each other')
    for x in (load(OUT / 'member-reports.json', {}) or {}).get('reports') or []:
        if x.get('area') in (area, None): add(x.get('refs') or [], 'member report: ' + str(x.get('what', ''))[:60])
    n_withheld = 0
    if sec:   # a pair with a withheld park is left out of the public file: counted only
        n_withheld = sum(1 for refs in exp if set(refs) & sec)
        exp = {refs: why for refs, why in exp.items() if not set(refs) & sec}
    out = {'FOUND': [], 'DROPPED': [], 'NEVER LOOKED AT': []}
    for refs, why in sorted(exp.items()):
        rs = set(refs)
        live = [r for r in rows if rs <= r[0] and r[1].startswith(LIVE)]
        pairs_live = len(refs) > 2 and all(any({a, b} <= r[0] and r[1].startswith(LIVE) for r in rows) for a, b in itertools.combinations(refs, 2) if not ({a, b} <= {x for x in refs if x not in inrun}))
        e = {'refs': list(refs), 'why_expected': sorted(why)}
        if live or pairs_live:
            e['row'] = (live[0][2] if live else 'each pair has a row'); out['FOUND'].append(e); continue
        dead = [r for r in rows if rs <= r[0]]
        if dead:
            st = dead[0][1]; e['reason'] = st[:200]; e['rule'] = rule_of(st); out['DROPPED'].append(e); continue
        if not looked:
            e['reason'] = 'unknown'; out['NEVER LOOKED AT'].append(e); continue
        miss = [r for r in refs if r in noout or r not in inrun]
        if miss:
            e['reason'] = '; '.join(f"{r}: {noout.get(r) or 'not in this run (another state, retired, or no POTA pin)'}" for r in miss)
            out['NEVER LOOKED AT'].append(e); continue
        pairs = list(itertools.combinations(refs, 2))
        if all(p in tested for p in pairs):
            e['reason'] = 'looked: no shared ground on the official outlines (no patch 25 yards across; not within 100 ft of a trail / river line)'
            e['rule'] = 'rule 4 / rule 5'; out['DROPPED'].append(e); continue
        unread = [r for r in refs if r in set(looked.get('unread') or [])]
        if unread:
            e['reason'] = 'not tested: the official outline of ' + ', '.join(unread) + ' could not be read in pass 1 (one of its map records did not answer; the next run tries again)'
            out['NEVER LOOKED AT'].append(e); continue
        e['reason'] = 'not tested: the outlines\' boxes do not touch (the parks are apart on the official maps)' if inrun >= rs else 'unknown'
        out['NEVER LOOKED AT'].append(e)
    bad = [e for e in out['NEVER LOOKED AT'] if e.get('reason') == 'unknown'] + [e for e in out['DROPPED'] if not e.get('reason')]
    if not looked: print(f'::notice title=2-fer missing check::{area}: no pass-1 list (looked-{area}.json): run pass 1 first', flush=True)
    res = {'about': __doc__.split('\n')[0] + ' See kpc_fers_expected.py. Chat 8 reviews the private DROPPED list + NEVER LOOKED AT.', 'area': area,
           'date': time.strftime('%Y-%m-%d'), 'pass': not bad, 'counts': {k: len(v) for k, v in out.items()}, **out}
    path = OUT / f'expected-{tag or area}.json'
    # OWNER RULE (2026-11-15 23:14; re-grade R2): the DROPPED list never goes into the pushed file. 'pass', 'counts' and the
    # notice above are worked out from the whole buckets first, so nothing the checkers rely on changes.
    _dpf, _dpn = split_dropped(res, tag or area)
    if _dpn:
        print(f'::notice title=2-fer missing check::{area}: {_dpn} looked-at pair(s) are not listed in the pushed file '
              + (f'(their reasons are in the private folder for a person)' if _dpf is not None else
                 '(no private folder was given, so their reasons were not written anywhere)'), flush=True)
    if wh != 'off':   # public store run: the store's redact + write guard, like every file the bot writes (a refusal = no file)
        import kpc_fers_store as S
        res['withheld (pairs with a park whose outline is held privately: not named)'] = n_withheld
        try: res, n = S.guard_public_file(path, res, wh[0], wh[1], wh[2])
        except S.LeakRefused:
            print(f'::error title=2-fer missing check::{area}: the write guard refused expected-{tag or area}.json: not written', flush=True); return
        if n: res['withheld (items left out by the write guard)'] = n
    path.write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"::notice title=2-fer missing check::{area}: {res['counts']} expected pairs" + ('' if res['pass'] else f' · {len(bad)} with no reason'), flush=True)


def main():
    area = os.environ.get('AREA') or ''
    if area == 'ky': return build('ky', [OUT / 'US-KY.json'])
    raw = (os.environ.get('STATES') or '').upper().replace(',', ' ').split()
    sts = sorted(x if '-' in x else 'US-' + x for x in raw)
    if sts: build('-'.join(sorted(raw)), [OUT / f'{s}.json' for s in sts], os.environ.get('RUN_TAG') or '', sts)


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=2-fer missing check::stopped: {e}', flush=True)
    sys.exit(0)
