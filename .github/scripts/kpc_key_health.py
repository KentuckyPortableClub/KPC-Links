#!/usr/bin/env python3
"""DAILY KEY HEALTH DIFF (Nov 6 2026 improvements 3, Mapping; Brandon directly in Mapping's chat, 4:58 PM CST Nov 5: "You write
the code and I think super and quality would agree to it"). READ-ONLY and OFFLINE: it reads key files (this checkout, git
history or a saved folder) and writes a report. It never changes a key, a pin or a 2-fer, and decides nothing.

Compares the CURRENT US (plus the KY key, data/ky-answer-key.json, as area US-KY), Canada or world key with the PREVIOUS SAVED
COPY and flags, per park and per area:
  outline lost         the park had an outline (joined records / KY tracts) and now is a pin or is gone from that area
  outline pieces lost  the park still has an outline but some joined records are gone and none came in (the KY trails case)
  join over 15 km      an outline whose nearest joined record is more than 15 km from the POTA pin (key field bk[1], links-10).
                       REPORT-ONLY by default (v2, 5:28 PM CST Nov 5): listed, no pile proposal (the build's join check holds
                       those joins and writes its own proposals); HEALTH_FAR_PROPOSE=1 proposes them too
  join held            a join the build's join check HELD before the stamp ('held' field, kpc_join_check.py v2): report-only,
                       not counted as 'outline lost' (its proposal is in data/<kind>-key/review/held-joins-ledger.csv)
  acres off            outline acres vs the park's OFFICIAL acres (data/acres.json, where known) outside 0.5x - 2x
  area missing / empty / unreadable / lost its outlines   an area file gone, unreadable, with no parks, or with no outlines
                       where the previous copy had some; and 'many lost' when 10+ (or 25%+) of an area's outlines went
Writes OUT_DIR (default data/status/key-check/health-<key>/): health.csv (one row per flag), summary.json, summary.md and
ledger-proposals.csv: ONE 'pile-enter' PROPOSAL per flagged park (lost outlines, lost pieces, acres outliers; not the
report-only flags) (proposed_by key-health) in the agreement ledger's columns.
Those are proposals, not decisions: KPC-Data's `kpc_ledger_flow.py import <file>` appends them, a different agent confirms, and
an imported file can never carry the confirmation (two-agreements rule, Brandon Nov 5). LEDGER_DATA=<KPC-Data checkout>
appends them right away through that helper (used for the local sample; the workflow step leaves the CSV only).

  KEY=us|ca|world   PREV_REF=<git ref> (default: the build commit before the newest one, like kpc_key_postcheck.py)
  PREV_DIR=<checkout root holding data/<kind>-key/> (instead of git: e.g. KPC-Data's released copy)
  OFFICIAL_ACRES=<file> (default data/acres.json here, else $DATA/data/acres.json)   OUT_DIR   LEDGER_DATA
  --selftest        rule-18 style: 12+ frozen cases, temp folder only
Never fails a run: problems are lines in the report, exit 0 (the selftest exits 1 on a failed case)."""
import csv, glob, json, os, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_key_postcheck as PK  # noqa: E402  (KEYS, git, build_commits, load_tree, acres_of: one reader for both reports)

FAR_KM = 15.0
REPORT_ONLY = {'join over 15 km', 'join held'}   # v2: listed in health.csv, no pile proposal (HEALTH_FAR_PROPOSE=1: far joins propose)
RATIO = (0.5, 2.0)
AREA_LOSS_N, AREA_LOSS_SHARE = 10, 0.25
BY = 'key-health'
FIELDS = ['park', 'kind', 'proposed_by', 'proposal', 'source', 'confirmed_by', 'confirmed_at', 'decided_by',
          'agreed_lat', 'agreed_lon', 'pota_lat', 'pota_lon', 'notes']   # = kpc_agreement_ledger.FIELDS (KPC-Data; test checks)
KY = 'data/ky-answer-key.json'


def pieces(p): return [x for x in ((p or {}).get('m') or (p or {}).get('tracts') or []) if isinstance(x, (list, tuple)) and x]
def outlined(p): return bool(pieces(p)) and (p or {}).get('g') != 'pin'
def ids(p): return {str(x[0]) for x in pieces(p)}


def outline_acres(p):
    if (p or {}).get('m'): return PK.acres_of(p)
    a = [x[2] for x in pieces(p) if len(x) > 2 and isinstance(x[2], (int, float)) and not isinstance(x[2], bool)]
    return float(sum(a)) if a else None


def load(k, ref=None, root='.', prev_dir=None):
    """{area: key file dict}; area US-KY = the KY key for k == 'us'."""
    if prev_dir: tree = PK.load_tree(k, None, cwd=prev_dir); base = prev_dir
    else: tree = PK.load_tree(k, ref, cwd=root); base = root
    if k == 'us':
        if ref and not prev_dir:
            txt = PK.git('show', f'{ref}:{KY}', cwd=root)
            try: ky = json.loads(txt) if txt else None
            except ValueError: ky = {'_bad': True}
        else:
            try: ky = json.load(open(os.path.join(base, KY), encoding='utf-8'))
            except FileNotFoundError: ky = None
            except Exception: ky = {'_bad': True}  # noqa: BLE001
        if ky is not None and 'US-KY' not in tree: tree['US-KY'] = ky
    return tree


def official_acres(path=None):
    cands = [path] if path else ['data/acres.json', os.path.join(os.environ['DATA'], 'data/acres.json') if os.environ.get('DATA') else None]
    for f in cands:
        if not f or not os.path.exists(f): continue
        try: d = json.load(open(f, encoding='utf-8'))
        except Exception: continue  # noqa: BLE001
        d = d.get('parks', d) if isinstance(d, dict) else {}
        out = {}
        for r, v in d.items():
            a = v.get('acres') if isinstance(v, dict) else v
            if isinstance(a, (int, float)) and not isinstance(a, bool) and a > 0: out[r] = float(a)
        return out, f
    return {}, ''


def diff(new, old, official=None):
    """[flag rows] {area, park, name, flag, detail}."""
    official = official or {}
    rows = []
    for area in sorted(set(new) | set(old)):
        N, O = new.get(area), old.get(area)
        if N is None: rows.append({'area': area, 'park': '', 'name': '', 'flag': 'area missing', 'detail': 'the area file is gone from the current key'}); continue
        if N.get('_bad'): rows.append({'area': area, 'park': '', 'name': '', 'flag': 'area unreadable', 'detail': 'the area file did not read as JSON'}); continue
        NP, OP = (N.get('parks') or {}), ((O or {}).get('parks') or {}) if O and not O.get('_bad') else {}
        if not NP: rows.append({'area': area, 'park': '', 'name': '', 'flag': 'area empty', 'detail': 'the area file has no parks'}); continue
        old_out = [r for r, p in OP.items() if outlined(p)]
        if old_out and not any(outlined(p) or (isinstance(p, dict) and p.get('held')) for p in NP.values()):
            rows.append({'area': area, 'park': '', 'name': '', 'flag': 'area lost its outlines', 'detail': f'{len(old_out)} outlines before, none now'})
        lost = 0
        for r, p in sorted(NP.items()):
            o, nm = OP.get(r), (p or {}).get('n') or ''
            if outlined(o) and not outlined(p) and isinstance(p, dict) and p.get('held'):
                rows.append({'area': area, 'park': r, 'name': nm, 'flag': 'join held', 'detail': f"held before the stamp by the join check: {str((p.get('held') or {}).get('why') or '')[:160]}"})
            elif outlined(o) and not outlined(p):
                lost += 1
                rows.append({'area': area, 'park': r, 'name': nm, 'flag': 'outline lost', 'detail': f'was {len(ids(o))} joined record(s) ({", ".join(sorted(ids(o))[:4])}); now a pin'})
            elif outlined(o) and outlined(p) and ids(p) < ids(o):
                rows.append({'area': area, 'park': r, 'name': nm, 'flag': 'outline pieces lost', 'detail': f'{len(ids(o) - ids(p))} of {len(ids(o))} joined record(s) gone: {", ".join(sorted(ids(o) - ids(p))[:4])}'})
            if outlined(p):
                bk = p.get('bk') or []
                if len(bk) > 1 and isinstance(bk[1], (int, float)) and bk[1] > FAR_KM:
                    rows.append({'area': area, 'park': r, 'name': nm, 'flag': 'join over 15 km', 'detail': f'the nearest joined record is {bk[1]:.1f} km from the POTA pin'})
                oa, ac = official.get(r), outline_acres(p)
                if oa and ac is not None and not (RATIO[0] <= ac / oa <= RATIO[1]):
                    rows.append({'area': area, 'park': r, 'name': nm, 'flag': 'acres off', 'detail': f'outline {ac:,.0f} ac vs official {oa:,.0f} ac ({ac / oa:.2f}x, outside {RATIO[0]}x-{RATIO[1]}x)'})
        for r, o in sorted(OP.items()):
            if r not in NP and outlined(o):
                lost += 1
                rows.append({'area': area, 'park': r, 'name': (o or {}).get('n') or '', 'flag': 'outline lost', 'detail': f'the park is gone from this area (was {len(ids(o))} joined record(s))'})
        if lost and (lost >= AREA_LOSS_N or (old_out and lost / len(old_out) >= AREA_LOSS_SHARE)):
            rows.append({'area': area, 'park': '', 'name': '', 'flag': 'many outlines lost in this area', 'detail': f'{lost} of {len(old_out)} outlines lost (a source layer or a rule may have failed)'})
    return rows


def proposals(rows, k, what, far_propose=None):
    far_propose = os.environ.get('HEALTH_FAR_PROPOSE') == '1' if far_propose is None else far_propose
    skip = REPORT_ONLY - ({'join over 15 km'} if far_propose else set())
    by = {}
    for r in rows:
        if r['park'] and r['flag'] not in skip: by.setdefault(r['park'], []).append(r)
    out = []
    for park, rs in sorted(by.items()):
        out.append({f: '' for f in FIELDS} | {'park': park, 'kind': 'pile-enter', 'proposed_by': BY,
                    'proposal': 'review pile: ' + '; '.join(sorted({x['flag'] for x in rs})),
                    'source': f'key-health {k} {what}', 'notes': ' | '.join(f"{x['area']}: {x['detail']}" for x in rs)[:900]})
    return out


def write(out_dir, k, rows, props, summary):
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    with open(out / 'health.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['key', 'area', 'park', 'name', 'flag', 'detail']); w.writeheader()
        for r in rows: w.writerow({'key': k, **r})
    with open(out / 'ledger-proposals.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(props)
    json.dump(summary, open(out / 'summary.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    L = [f"# Key health: {k} key, {summary['compared']}", '', '| flag | count |', '|---|---|'] + [f'| {a} | {b} |' for a, b in summary['flags'].items()]
    L += ['', f"Parks flagged: **{summary['parks_flagged']}**, each one a `pile-enter` PROPOSAL in ledger-proposals.csv (proposed by key-health;"
          " a different agent confirms; nothing moves by itself).", f"Official acres: {summary['official_acres']}.", '']
    open(out / 'summary.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')


def run(env=None, root='.'):
    env = dict(os.environ if env is None else env)
    k = PK.key_of(env)
    if not k: PK.note('warning', 'key health: no key given (KEY=us|ca|world)'); return None
    prev_dir, prev_ref = env.get('PREV_DIR') or None, env.get('PREV_REF') or None
    if not prev_dir and not prev_ref:
        bc = PK.build_commits(k, cwd=root); prev_ref = bc[1] if len(bc) > 1 else None
    if not prev_dir and not prev_ref:
        PK.note('notice', f'key health {k}: no previous saved copy (no PREV_DIR and fewer than two build commits): nothing compared'); return None
    new, old = load(k, None, root), load(k, prev_ref, root, prev_dir)
    off, off_f = official_acres(env.get('OFFICIAL_ACRES'))
    rows = diff(new, old, off)
    what = f"current files vs {('saved copy ' + prev_dir) if prev_dir else ('build commit ' + prev_ref[:12])}"
    props = proposals(rows, k, what)
    flags = {}
    for r in rows: flags[r['flag']] = flags.get(r['flag'], 0) + 1
    summary = {'key': k, 'compared': what, 'areas_now': len(new), 'areas_before': len(old), 'flags': dict(sorted(flags.items())),
               'parks_flagged': len(props), 'proposals': len(props), 'official_acres': f'{len(off)} parks from {off_f}' if off_f else 'none on file (data/acres.json not found): no acres check',
               'thresholds': {'far_km': FAR_KM, 'acres_ratio': RATIO, 'area_loss': [AREA_LOSS_N, AREA_LOSS_SHARE]}}
    out_dir = env.get('OUT_DIR') or os.path.join(root, f'data/status/key-check/health-{k}')
    write(out_dir, k, rows, props, summary)
    if env.get('LEDGER_DATA'):
        sys.path.insert(0, os.path.join(env['LEDGER_DATA'], '.github/scripts'))
        import kpc_agreement_ledger as AL, kpc_ledger_flow as LF  # noqa: E401
        AL.LEDGER = pathlib.Path(env.get('LEDGER_FILE') or os.path.join(env['LEDGER_DATA'], 'data/agreement-ledger/ledger.csv'))
        summary['ledger_import'] = LF.import_file(os.path.join(out_dir, 'ledger-proposals.csv'), by=BY)
        json.dump(summary, open(os.path.join(out_dir, 'summary.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    PK.note('notice', f"key health {k}: {len(rows)} flag(s), {len(props)} park(s) proposed for the review pile -> {out_dir}/summary.md")
    return summary


def selftest():
    import tempfile
    ok, n = True, 0
    def check(name, got, want):
        nonlocal ok, n
        n += 1; good = got == want; ok &= good
        print(('PASS ' if good else 'FAIL ') + name + ('' if good else f'  got={got!r} want={want!r}'))
    J = lambda i, nm, ac=100: [i, nm, ac, 'name']
    old = {'US-AA': {'parks': {
        'US-0001': {'n': 'Lost Park', 'g': 'official', 'm': [J(1, 'Lost Park')]},
        'US-0002': {'n': 'Shrunk Park', 'g': 'official', 'm': [J(2, 'Shrunk A'), J(3, 'Shrunk B')]},
        'US-0003': {'n': 'Swapped Park', 'g': 'official', 'm': [J(4, 'Swap A')]},
        'US-0004': {'n': 'Far Park', 'g': 'official', 'm': [J(5, 'Far')]},
        'US-0005': {'n': 'Big Park', 'g': 'official', 'm': [J(6, 'Big', 900)]},
        'US-0006': {'n': 'Gone Park', 'g': 'official', 'm': [J(7, 'Gone')]},
        'US-0007': {'n': 'Fine Park', 'g': 'official', 'm': [J(8, 'Fine', 100)]}}},
        'US-BB': {'parks': {'US-0100': {'n': 'x', 'g': 'official', 'm': [J(9, 'x')]}}},
        'US-CC': {'parks': {'US-0200': {'n': 'y', 'g': 'official', 'm': [J(10, 'y')]}}},
        'US-KY': {'parks': {'US-9001': {'n': 'Trail', 't': 'Trail', 'tracts': [['tr1', 'Trail line', 0, 'name'], ['tr2', 'Trail line 2', 0, 'name']]}}}}
    new = {'US-AA': {'parks': {
        'US-0001': {'n': 'Lost Park', 'g': 'pin', 'm': []},
        'US-0002': {'n': 'Shrunk Park', 'g': 'official', 'm': [J(2, 'Shrunk A')]},
        'US-0003': {'n': 'Swapped Park', 'g': 'official', 'm': [J(44, 'Swap B')]},
        'US-0004': {'n': 'Far Park', 'g': 'official', 'm': [J(5, 'Far')], 'bk': [5, 22.4, 'SP', 'des']},
        'US-0005': {'n': 'Big Park', 'g': 'official', 'm': [J(6, 'Big', 900)]},
        'US-0007': {'n': 'Fine Park', 'g': 'official', 'm': [J(8, 'Fine', 100)], 'bk': [8, 14.9, 'SP', 'des']}}},
        'US-CC': {'parks': {}},
        'US-KY': {'parks': {'US-9001': {'n': 'Trail', 't': 'Trail', 'tracts': []}}}}
    rows = diff(new, old, {'US-0005': 300.0, 'US-0007': 100.0})
    f = {(r['park'] or r['area'], r['flag']) for r in rows}
    check('outline -> pin is "outline lost"', ('US-0001', 'outline lost') in f, True)
    check('records gone, none new: "outline pieces lost"', ('US-0002', 'outline pieces lost') in f, True)
    check('a record swapped for another is NOT a loss', any(p == 'US-0003' for p, _ in f), False)
    check('a join 22.4 km from the pin is flagged', ('US-0004', 'join over 15 km') in f, True)
    check('14.9 km is not flagged (over 15 only)', ('US-0007', 'join over 15 km') in f, False)
    check('900 ac vs official 300 ac (3x) is "acres off"', ('US-0005', 'acres off') in f, True)
    check('100 ac vs official 100 ac is fine', ('US-0007', 'acres off') in f, False)
    check('a park gone from its area with an outline is "outline lost"', ('US-0006', 'outline lost') in f, True)
    check('an area file gone is "area missing"', ('US-BB', 'area missing') in f, True)
    check('an area with no parks is "area empty"', ('US-CC', 'area empty') in f, True)
    check('the KY trails case: KY tracts gone is "outline lost"', ('US-9001', 'outline lost') in f, True)
    check('3 of 7 outlines lost in one area is "many lost" (25%+)', ('US-AA', 'many outlines lost in this area') in f, True)
    props = proposals(rows, 'us', 'test')
    check('one pile-enter proposal per flagged park, none for area rows; the far join is report-only (v2)', sorted(p['park'] for p in props), ['US-0001', 'US-0002', 'US-0005', 'US-0006', 'US-9001'])
    check('HEALTH_FAR_PROPOSE=1: the far join proposes too', 'US-0004' in [p['park'] for p in proposals(diff(new, old, {'US-0005': 100.0}), 'us', 'x', True)], True)
    hn = {'US-AA': {'parks': {'US-0010': {'n': 'Held', 'g': 'pin', 'm': [], 'c': [J(9, 'X')], 'held': {'why': 'nearest part 30.0 km'}}}}}
    ho = {'US-AA': {'parks': {'US-0010': {'n': 'Held', 'g': 'official', 'm': [J(9, 'X')]}}}}
    hr = diff(hn, ho, {})
    check("a join the build HELD is 'join held' (report-only), not 'outline lost', and proposes nothing", ([x['flag'] for x in hr], proposals(hr, 'us', 'x')), (['join held'], []))
    check('proposals carry no confirmation or decision', {(p['kind'], p['proposed_by'], p['confirmed_by'], p['decided_by']) for p in props}, {('pile-enter', BY, '', '')})
    check('no official acres on file -> no acres flags', any(r['flag'] == 'acres off' for r in diff(new, old, {})), False)
    td = pathlib.Path(tempfile.mkdtemp(prefix='kpc-health-'))
    for a, d in old.items():
        if a == 'US-KY': (td / 'old').mkdir(exist_ok=True); json.dump(d, open(td / 'old/ky.json', 'w'))
    (td / 'new/data/us-key').mkdir(parents=True); (td / 'prev/data/us-key').mkdir(parents=True)
    for a, d in new.items():
        if a != 'US-KY': json.dump(d, open(td / f'new/data/us-key/{a}.json', 'w'))
    for a, d in old.items():
        if a != 'US-KY': json.dump(d, open(td / f'prev/data/us-key/{a}.json', 'w'))
    json.dump(new['US-KY'], open(td / 'new/data/ky-answer-key.json', 'w')); json.dump(old['US-KY'], open(td / 'prev/data/ky-answer-key.json', 'w'))
    s = run({'KEY': 'us', 'PREV_DIR': str(td / 'prev'), 'OUT_DIR': str(td / 'out'), 'OFFICIAL_ACRES': str(td / 'none.json')}, root=str(td / 'new'))
    check('run(): files written, KY read from data/ky-answer-key.json', (sorted(os.listdir(td / 'out')), s['flags'].get('outline lost')),
          (['health.csv', 'ledger-proposals.csv', 'summary.json', 'summary.md'], 3))
    print(f"SELFTEST {'PASS' if ok else 'FAIL'}: {n} cases")
    return ok


if __name__ == '__main__':
    if '--selftest' in sys.argv: sys.exit(0 if selftest() else 1)
    try: run()
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); PK.note('warning', f'key health stopped ({type(e).__name__}: {e}); nothing else is affected')
    sys.exit(0)
