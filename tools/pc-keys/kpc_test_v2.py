#!/usr/bin/env python3
"""KPC test of the v2 key, side by side with v1 (26 Nov 2026). It does NOT build v1 again (that takes minutes). It compares v2
with a v1 test that is already on this PC, so one try takes seconds. Saved copies only: nothing is downloaded or uploaded.

  py -3.12 kpc_test_v2.py MN NY SC [--base test-2026-11-26-1654] [--store <folder>] [--facts <file>] [--reports <folder>]
  py -3.12 kpc_test_v2.py MN NY --try my-rules.json [--base ...]      (the TRY A RULE workbench, see the end of this note)

What it does:
  1. Picks the v1 test to compare with: --base, or the newest test in reports\\ that kept a key for every state you typed.
  2. Makes reports\\v2-<date-time>\\ and builds the v2 keys into it twice: a first run (writes locks) into cold\\, then a run that
     reads those locks into warm\\. A lock must never change an answer, so the two keys must be the same bytes.
  3. Runs the scorecard on the warm run. The scorecard is V2-SCORECARD.txt in the same folder; v2-vs-base.csv lists park by park.
Exit code: the scorecard's (0 = V2 passes, 1 = not yet); 2 = it could not run (a file is missing).
TRY A RULE (a place to work out the leftover parks WITHOUT touching v2, the key or the rule table): with --try <my-rules.json> it
builds v2 twice into reports\\v2-try-<date-time>\\: now\\ with the real rule table and try\\ with --rules <my-rules.json>. Then it writes
TRY-REPORT.txt (parks that gain an outline, lose one, change their joined land by more than 10%, the pin-only reasons before and after,
the matcher's gate for the trial run, the scorecard verdict for both runs) and try-changes.csv (one row per changed park). The lock check
is not part of a trial. If the matcher refuses the trial table (exit 2) it shows the matcher's one line and stops.
Works in the repo (tools/pc-keys, repo root two levels up) and on the PC (kit folder with links\\ beside this file).
"""
import argparse, csv, datetime, json, pathlib, re, shutil, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent
LOCKS_ARG_IS_RUN_FOLDER = True   # the contract: --locks is the folder that HOLDS locks/US-<ST>.json, i.e. the cold run's own folder


def say(*a): print(*a, flush=True)


def find_links(here):
    """The copy of the repo: links\\ beside this file (the PC), else the repo root two folders up (the repo)."""
    for c in (here / 'links', here.parents[1] if len(here.parents) > 1 else here):
        if (c / '.github' / 'scripts').is_dir(): return c
    return here / 'links'


def find_store(here):
    """The same search order as kpc_test_keys.py."""
    for p in (here.parent / '3-MAP-STORE-US-CA' / 'results' / 'store',
              here.parent / 'Tools' / 'KPC-TOOLS-NOV14' / '1-STORE-TOOL' / 'kpc-outline-store-full' / 'results' / 'store'):
        if p.is_dir(): return p
    return here.parent / '3-MAP-STORE-US-CA' / 'results' / 'store'


def find_facts(here, links):
    f = here / 'park-facts.json.gz'
    return f if f.is_file() else links / '.pf' / 'data' / 'park-facts.json.gz'


def area_of(x):
    """MN -> US-MN; CA-ON (or US-MN) stays."""
    x = str(x).strip().upper()
    return x if re.match(r'^[A-Z]{2}-[A-Z]{2}$', x) else 'US-' + x


def label_of(area): return area[3:] if area.startswith('US-') else area


def has_keys(rep, states):
    return all((rep / 'keys' / f'{area_of(s)}.json.gz').is_file() for s in states)


def find_baseline(reports, states, base=None):
    """The v1 test to compare with: the folder named by --base, else the newest test-* folder that holds keys\\US-<ST>.json.gz for
    every typed state. Returns the folder or None."""
    reports = pathlib.Path(reports)
    if base:
        p = reports / base if (reports / base).is_dir() else pathlib.Path(base)   # a test name in reports\\, or a folder path
        return p if p.is_dir() and has_keys(p, states) else None
    for r in sorted((x for x in reports.glob('test-*') if x.is_dir()), key=lambda x: x.name, reverse=True):
        if has_keys(r, states): return r
    return None


def v1_minutes(report_text, st):
    """'MN: built in 4.2 minutes (exit 0).' -> 4.2, else None."""
    m = re.search(r'^' + re.escape(st) + r': built in ([0-9]+(?:\.[0-9]+)?) minutes', report_text or '', re.M)
    return float(m.group(1)) if m else None


def v1_seconds(base, states):
    try: text = (pathlib.Path(base) / 'REPORT.txt').read_text(encoding='utf-8', errors='replace')
    except OSError: text = ''
    out = {}
    for s in states:
        m = v1_minutes(text, s)
        if m is not None: out[s] = round(m * 60, 1)
    return out


def lock_compare(cold, warm, states):
    """('same'|'differs'|'skipped', [states that differ]): the cold key and the warm key of a state must be the same bytes."""
    diff, seen = [], 0
    for s in states:
        a, b = pathlib.Path(cold) / f'{area_of(s)}.json.gz', pathlib.Path(warm) / f'{area_of(s)}.json.gz'
        if not (a.is_file() and b.is_file()): continue
        seen += 1
        if a.read_bytes() != b.read_bytes(): diff.append(s)
    return ('differs' if diff else 'same' if seen else 'skipped'), diff


def scope_flags(items):
    """The matcher's flags for what was typed: US states by --states (letters), Canadian areas by --areas."""
    us = [label_of(area_of(x)) for x in items if area_of(x).startswith('US-')]
    other = [area_of(x) for x in items if not area_of(x).startswith('US-')]
    return (['--states', *us] if us else []) + (['--areas', *other] if other else [])


def run_v2(v2script, states, store, facts, out, links, locks=None, write_locks=False):
    cmd = [sys.executable, '-X', 'utf8', str(v2script), *scope_flags(states), '--store', str(store), '--facts', str(facts),
           '--out', str(out), '--repo', str(links)]
    if locks: cmd += ['--locks', str(locks)]
    if write_locks: cmd += ['--write-locks']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    for ln in (r.stdout + r.stderr).splitlines():
        if ln.strip(): say('    ' + ln[:200])
    return r.returncode


def _load(p):
    import gzip, json
    try:
        with gzip.open(p, 'rt', encoding='utf-8') as f: return json.load(f)
    except (OSError, ValueError, EOFError): return None


def _stat(p):
    if not (p or {}).get('m'): return 'pin' if p is not None else '-'
    return 'confirmed' if (p.get('match') or {}).get('status') == 'confirmed' else 'outlined'


def _acres(p):
    if not (p or {}).get('m'): return None
    a = p.get('ac')
    if isinstance(a, (int, float)): return float(a)
    s = [x[2] for x in p['m'] if isinstance(x, (list, tuple)) and len(x) > 2 and isinstance(x[2], (int, float))]
    return float(sum(s)) if s else None


def try_changes(now_dir, try_dir, states):
    """Per state: counts and one csv row for every park whose outline gains, is lost, or whose joined land changes by more than 10%."""
    out, rows = {}, []
    for st in states:
        a, b = _load(pathlib.Path(now_dir) / f'US-{st}.json.gz'), _load(pathlib.Path(try_dir) / f'US-{st}.json.gz')
        c = {'built': bool(a and b), 'gain': 0, 'lose': 0, 'land': 0, 'why_now': {}, 'why_try': {}}
        out[st] = c
        if not c['built']: continue
        pa, pb = a.get('parks') or {}, b.get('parks') or {}
        for tag, ps in (('why_now', pa), ('why_try', pb)):
            for p in ps.values():
                if not p.get('m'):
                    w = (p.get('match') or {}).get('why') or 'no reason'
                    c[tag][w] = c[tag].get(w, 0) + 1
        for ref in sorted(set(pa) | set(pb)):
            x, y = pa.get(ref), pb.get(ref)
            jx, jy = bool((x or {}).get('m')), bool((y or {}).get('m'))
            ax, ay = _acres(x), _acres(y)
            ch = 'gain' if jy and not jx else 'lose' if jx and not jy else 'land' if jx and jy and ax and ay and abs(ax - ay) > 0.10 * max(ax, ay) else ''
            if not ch: continue
            c[ch] += 1
            mx, my = (x or {}).get('match') or {}, (y or {}).get('match') or {}
            rows.append({'ref': ref, 'state': st, 'name': (y or x or {}).get('n') or '', 'before_status': _stat(x), 'before_by': mx.get('by') or '',
                         'before_acres': '' if ax is None else round(ax, 1), 'after_status': _stat(y), 'after_by': my.get('by') or '',
                         'after_acres': '' if ay is None else round(ay, 1),
                         'change': {'gain': 'gains an outline', 'lose': 'loses its outline', 'land': 'joined land changes by more than 10%'}[ch]})
    return out, rows


def _verdict(card_dir):
    try: text = (pathlib.Path(card_dir) / 'V2-SCORECARD.txt').read_text(encoding='utf-8')
    except OSError: return 'no scorecard', []
    return text.splitlines()[0], re.findall(r'^((?:G|H)\d+) FAIL', text, re.M)


def try_mode(states, rules, base, secs, reports, store, facts, links, v2script, card):
    import csv, json
    rep = reports / ('v2-try-' + datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'))
    now, tri = rep / 'now', rep / 'try'
    now.mkdir(parents=True, exist_ok=True); tri.mkdir(parents=True, exist_ok=True)
    say(f'Trying the rules in {rules.name}. The real key and the real rule table are not touched.')
    say('  v2 with the trial rules...')
    cmd = [sys.executable, '-X', 'utf8', str(v2script), '--states', *states, '--store', str(store), '--facts', str(facts), '--out', str(tri),
           '--repo', str(links), '--rules', str(rules)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    lines = [x.strip() for x in (r.stdout + r.stderr).splitlines() if x.strip()]
    for x in lines: say('    ' + x[:200])
    if r.returncode == 2:
        say('The matcher refused the trial rules: ' + (lines[-1][:200] if lines else 'no reason given') + '. Nothing else was run.'); return 2
    say('  v2 with the real rules...')
    run_v2(v2script, states, store, facts, now, links)
    verdicts = {}
    for tag, d in (('now', now), ('try', tri)):
        cs = [sys.executable, '-X', 'utf8', str(card), '--v2', str(d), '--base', str(base / 'keys'), '--store', str(store), '--facts', str(facts),
              '--states', *states, '--out', str(rep / ('score-' + tag)), '--repo', str(links), '--trial']
        if secs: cs += ['--v1-seconds'] + [f'{k}={v}' for k, v in secs.items()]
        subprocess.run(cs, capture_output=True, text=True, encoding='utf-8', errors='replace')
        verdicts[tag] = _verdict(rep / ('score-' + tag))
    ch, rows = try_changes(now, tri, states)
    cols = ['ref', 'state', 'name', 'before_status', 'before_by', 'before_acres', 'after_status', 'after_by', 'after_acres', 'change']
    with open(rep / 'try-changes.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    try: run = (json.loads((tri / 'v2-run.json').read_text(encoding='utf-8')) or {}).get('states') or {}
    except (OSError, ValueError): run = {}
    L = [f'KPC try a rule, {datetime.datetime.now():%d %b %Y %I:%M %p}. Counts only, no park names (the names are in try-changes.csv).',
         f'Trial rules: {rules.name}. Compared with the v1 test {base.name}. Lock check not part of a trial.', '']
    for st in states:
        c = ch[st]
        if not c['built']: L.append(f'{st}: one of the two runs did not build this state.'); continue
        def why(d): return ', '.join(f'{k} {v}' for k, v in sorted(d.items())) or 'none'
        g = (run.get(st) or {}).get('gate') or {}
        L += [f"{st}: gain an outline {c['gain']}, lose one {c['lose']}, joined land changes by more than 10%: {c['land']}.",
              f"  Pin-only reasons now: {why(c['why_now'])}.", f"  Pin-only reasons with the trial rules: {why(c['why_try'])}.",
              f"  The matcher's own gate on the trial run: {'ok' if g.get('ok') is True else 'NOT ok' if g else 'not reported'}."]
    L += ['', f"Scorecard, real rules: {verdicts['now'][0]}" + (f" (fails: {' '.join(verdicts['now'][1])})" if verdicts['now'][1] else ''),
          f"Scorecard, trial rules: {verdicts['try'][0]}" + (f" (fails: {' '.join(verdicts['try'][1])})" if verdicts['try'][1] else ''),
          'The park list is try-changes.csv.', '',
          'This changed nothing in the real key or the real rule table.',
          'To make it real: put the row in .github/us-key-v2-rules.json with its why and its test, and open a PR with this report.']
    (rep / 'TRY-REPORT.txt').write_text('\n'.join(L) + '\n', encoding='utf-8')
    say(''); [say(x) for x in L]
    say(f'\nThe report is {rep / "TRY-REPORT.txt"}')
    return 0


# ------------------------------------------------------------------------------------------------ BUILD MODE
def store_areas(store, group='ALL'):
    """Labels of every area with a layer file in the store: group US, CA (Canada) or ALL. MN or CA-ON as typed."""
    store = pathlib.Path(store)
    if not store.is_dir(): return []
    ar = sorted(m.group(1) for f in store.iterdir() for m in [re.match(r'^((?:US|CA)-[A-Z]{2})\.layer-records\.json\.gz$', f.name)] if m)
    return [a for a in ar if group == 'ALL' or a.startswith(group + '-')]


def parse_areas(tokens, store):
    """Typed words -> areas (US-MN, CA-ON). MN, US-MN, CA-ON, or the groups US, CA, ALL (every area with a layer file in the store)."""
    toks = [t.upper() for x in tokens for t in re.split(r'[,\s;]+', str(x)) if t]
    out = []
    for t in toks:
        for a in (store_areas(store, t) if t in ('US', 'CA', 'ALL') else [area_of(t)]):
            if a not in out: out.append(a)
    return out


def newest_v1(reports, area):
    """The newest PC test that holds this area's v1 key (keys\\US-<ST>.json.gz or keys\\CA-<XX>.json.gz), or None."""
    for r in sorted((x for x in pathlib.Path(reports).glob('test-*') if x.is_dir()), key=lambda x: x.name, reverse=True):
        if (r / 'keys' / f'{area}.json.gz').is_file(): return r
    return None


def classify(run_state, rc, area_file_ok):
    """('built' | 'built with a store gap' | 'gate failed' | 'not built', detail)"""
    rs = run_state or {}
    gaps = rs.get('gaps') or []
    if rs.get('not_built'): return 'not built', str(rs.get('not_built'))[:120]
    if not area_file_ok: return 'not built', 'no key was written'
    if (rs.get('gate') or {}).get('ok') is False or rc == 4: return 'gate failed', ''
    if gaps: return 'built with a store gap', ', '.join(str(g) for g in gaps)
    return 'built', ''


def build_one(area, store, facts, links, v2script, card, reports, run, base_pick):
    """One area in its own processes: cold, warm, scorecard. Returns a dict of numbers for the summary."""
    af = run / area; cold, warm = af / 'cold', af / 'warm'
    cold.mkdir(parents=True, exist_ok=True); warm.mkdir(parents=True, exist_ok=True)
    res = {'area': area, 'label': label_of(area), 'seconds': None, 'status': '', 'detail': ''}
    t0 = time.time()
    rc1 = run_v2(v2script, [area], store, facts, cold, links, write_locks=True)
    if rc1 not in (0, 3, 4):
        (af / 'build-error.txt').write_text(f'The matcher stopped with exit code {rc1}. Its lines are on the screen above.\n', encoding='utf-8')
        res.update(status='stopped', detail=f'the build stopped with an error, see {area}\\build-error.txt', seconds=time.time() - t0); return res
    rc2 = run_v2(v2script, [area], store, facts, warm, links, locks=cold if LOCKS_ARG_IS_RUN_FOLDER else cold / 'locks')
    if rc2 not in (0, 3, 4):
        (af / 'build-error.txt').write_text(f'The second matcher run stopped with exit code {rc2}.\n', encoding='utf-8')
        res.update(status='stopped', detail=f'the build stopped with an error, see {area}\\build-error.txt', seconds=time.time() - t0); return res
    lock, differ = lock_compare(cold, warm, [area])
    try: runj = json.loads((warm / 'v2-run.json').read_text(encoding='utf-8'))
    except (OSError, ValueError): runj = {}
    rs = (runj.get('areas') or {}).get(area) or (runj.get('states') or {}).get(label_of(area)) or (runj.get('states') or {}).get(area) or {}
    keyf = warm / f'{area}.json.gz'
    res['status'], res['detail'] = classify(rs, rc2, keyf.is_file())
    res['sec2'] = rs.get('seconds')
    if keyf.is_file():
        (run / 'keys').mkdir(exist_ok=True); shutil.copyfile(keyf, run / 'keys' / keyf.name)
    base = base_pick(area)
    cmd = [sys.executable, '-X', 'utf8', str(card), '--v2', str(warm), '--store', str(store), '--facts', str(facts), '--states', label_of(area),
           '--out', str(af), '--repo', str(links), '--lock-check', lock, '--cold', str(cold)]
    if base:
        cmd += ['--base', str(base / 'keys'), '--base-name', base.name]
        secs = v1_seconds(base, [label_of(area)])
        if secs: cmd += ['--v1-seconds'] + [f'{k}={v}' for k, v in secs.items()]
    else: cmd += ['--no-base']
    if differ: cmd += ['--lock-differs', label_of(area)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    res['card_rc'] = r.returncode; res['base'] = base.name if base else ''
    try: res['score'] = (json.loads((af / 'v2-score.json').read_text(encoding='utf-8')) or {})
    except (OSError, ValueError): res['score'] = {}
    res['gates_failed'] = [g[0] for g in (res['score'].get('gates') or []) if not g[1]]
    res['lock'] = lock
    res['seconds'] = time.time() - t0
    if res['status'] == 'built' and res['gates_failed']: res['detail'] = 'gates: ' + ' '.join(res['gates_failed'])
    return res


def pin_only_rows(run, results):
    """Every pin-only park of the run with its reason (from each warm key and its v2-pin-only.csv)."""
    rows = []
    for r in results:
        warm = run / r['area'] / 'warm'
        kf = warm / f"{r['area']}.json.gz"
        if not kf.is_file(): continue
        key = _load(kf) or {}
        txt = {}
        try:
            with open(warm / 'v2-pin-only.csv', encoding='utf-8', newline='') as f:
                for x in csv.DictReader(f): txt[x.get('ref')] = x.get('reason') or ''
        except OSError: pass
        for ref, p in sorted((key.get('parks') or {}).items()):
            if (p or {}).get('m'): continue
            m = (p or {}).get('match') or {}
            rows.append({'area': r['area'], 'ref': ref, 'name': (p or {}).get('n') or '', 'kind': (p or {}).get('t') or '', 'reason_code': m.get('why') or '', 'reason': txt.get(ref, '')})
    return rows


def build_summary(results, secs_total, run):
    def pct(a, b): return 'n/a' if not b else f'{100.0 * a / b:.1f}%'
    kinds = {}
    for r in results: kinds[r['status']] = kinds.get(r['status'], 0) + 1
    word = {'built': 'built', 'built with a store gap': 'built with a store gap', 'gate failed': 'gate failed', 'not built': 'not built', 'stopped': 'stopped with an error'}
    L = [f"v2 built {kinds.get('built', 0) + kinds.get('built with a store gap', 0) + kinds.get('gate failed', 0)} of {len(results)} areas on this PC: "
         + ', '.join(f"{n} {word[k]}" for k, n in sorted(kinds.items(), key=lambda x: -x[1])) + '.',
         f"{sum(1 for r in results if r.get('gates_failed'))} areas have a failing scorecard gate. Nothing was published, uploaded or changed in v1.", '']
    for r in results:
        sc = (r.get('score') or {}).get('areas', {}).get(r['label']) or {}
        det = f" ({r['detail']})" if r['detail'] else ''
        line = f"{r['label']:6s} {word.get(r['status'], r['status'])}{det}"
        if sc:
            line += f"  outlined {sc.get('out2')} of {sc.get('parks')}  pin inside {pct(sc.get('pin_yes', 0), sc.get('pin_n', 0))}"
            if sc.get('size_n'): line += f"  size agrees {pct(sc.get('size_yes', 0), sc.get('size_n', 0))}"
            lic = sc.get('lic')      # 27 Nov 2026: licence counts, from the scorecard's own v2-score.json
            if lic: line += f"  licence: share all {lic.get('all', 0)}, part {lic.get('part', 0)}, none {lic.get('none', 0)}"
            if not sc.get('nobase'): line += f"  v1 outlined {sc.get('out1')} pin {pct(sc.get('pin_yes1', 0), sc.get('pin_n1', 0))}  ({r.get('base')})"
            else: line += '  no v1 key to compare with'
        if r.get('gates_failed') and r['status'] != 'stopped': line += f"  gates failing: {' '.join(r['gates_failed'])}"
        line += f"  {r['seconds']:.0f} s" if r.get('seconds') is not None else ''
        L.append(line)
    lics = [((r.get('score') or {}).get('areas', {}).get(r['label']) or {}).get('lic') for r in results]
    lics = [x for x in lics if x]
    if lics:
        tot = {k: sum(int(x.get(k) or 0) for x in lics) for k in ('all', 'part', 'none', 'unmarked')}
        L += ['', f"Licence, what the club may show, total over {len(lics)} area{'s' if len(lics) != 1 else ''}: share all {tot['all']}, share part {tot['part']}, share none {tot['none']} "
                  f"(of {tot['all'] + tot['part'] + tot['none']} outlined parks)." + (f" {tot['unmarked']} had no licence word and count as none." if tot['unmarked'] else ''),
              '  (share all = every record of the park may be shown; share part = some may be; share none = only private records prove it.)']
    L += ['', f'{len(results)} areas, {secs_total:.0f} s in all. Files: summary.csv, pin-only-all.csv (every pin-only park with its reason), keys\\ (the built keys), and a folder per area',
          'with its cold and warm runs and its own scorecard (V2-SCORECARD.txt).', 'Counts only here; the park names are in pin-only-all.csv and the per-area csv lists.']
    return L


def build_mode(tokens, store, facts, links, v2script, card, reports, out_root, call=None, say=say):
    areas = parse_areas(tokens or ['MN', 'NY'], store)
    if not areas: say('No area to build: nothing typed matches a layer file in the store folder. Nothing was run.'); return 2
    run = pathlib.Path(out_root) / datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
    run.mkdir(parents=True, exist_ok=True)
    say(f'Building real v2 keys for {len(areas)} area(s) into {run}. One area at a time. Nothing is published or uploaded.')
    pick = lambda area: newest_v1(reports, area)
    results, t0 = [], time.time()
    for i, area in enumerate(areas, 1):
        t1 = time.time()
        if not (pathlib.Path(store) / f'{area}.layer-records.json.gz').is_file():
            r = {'area': area, 'label': label_of(area), 'status': 'not built', 'detail': 'no layer file', 'seconds': 0.0, 'score': {}, 'gates_failed': []}
        else:
            try: r = (call or build_one)(area, store, facts, links, v2script, card, reports, run, pick)
            except Exception as e: r = {'area': area, 'label': label_of(area), 'status': 'stopped', 'detail': f'the build stopped with an error ({type(e).__name__})', 'seconds': time.time() - t1, 'score': {}, 'gates_failed': []}
        results.append(r)
        say(f"{i} of {len(areas)}  {r['label']}  {time.time() - t1:.0f} s  {r['status']}" + (f" ({r['detail']})" if r['detail'] else ''))
    L = build_summary(results, time.time() - t0, run)
    (run / 'V2-BUILD-SUMMARY.txt').write_text('\n'.join(L) + '\n', encoding='utf-8')
    cols = ['area', 'status', 'detail', 'parks', 'outlined', 'confirmed', 'pin_only', 'pin_inside_yes', 'pin_inside_of', 'size_agrees_yes', 'size_agrees_of', 'v1_test', 'v1_outlined',
            'share_all', 'share_part', 'share_none', 'gates_failed', 'seconds']
    with open(run / 'summary.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in results:
            sc = (r.get('score') or {}).get('areas', {}).get(r['label']) or {}
            w.writerow({'area': r['area'], 'status': r['status'], 'detail': r['detail'], 'parks': sc.get('parks'), 'outlined': sc.get('out2'), 'confirmed': sc.get('conf2'), 'pin_only': sc.get('pin2'),
                        'pin_inside_yes': sc.get('pin_yes'), 'pin_inside_of': sc.get('pin_n'), 'size_agrees_yes': sc.get('size_yes'), 'size_agrees_of': sc.get('size_n'),
                        'v1_test': r.get('base', ''), 'v1_outlined': None if sc.get('nobase') else sc.get('out1'),
                        'share_all': (sc.get('lic') or {}).get('all'), 'share_part': (sc.get('lic') or {}).get('part'), 'share_none': (sc.get('lic') or {}).get('none'), 'gates_failed': ' '.join(r.get('gates_failed') or []),
                        'seconds': None if r.get('seconds') is None else round(r['seconds'], 1)})
    po = pin_only_rows(run, results)
    with open(run / 'pin-only-all.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['area', 'ref', 'name', 'kind', 'reason_code', 'reason']); w.writeheader(); w.writerows(po)
    say(''); [say(x) for x in L[:14]]
    say(f'\nThe report is {run / "V2-BUILD-SUMMARY.txt"}')
    if not any(r['status'] in ('built', 'built with a store gap', 'gate failed') for r in results): return 2
    return 1 if any(r['status'] in ('stopped', 'not built', 'gate failed') for r in results) else 0


def main(argv=None, here=None):
    here = pathlib.Path(here or HERE)
    ap = argparse.ArgumentParser(description='Test the v2 key side by side with a v1 test already on this PC.')
    ap.add_argument('states', nargs='*'); ap.add_argument('--base'); ap.add_argument('--store'); ap.add_argument('--facts')
    ap.add_argument('--reports'); ap.add_argument('--try', dest='try_rules', help='a trial rule table (json): the TRY A RULE workbench')
    a = ap.parse_args(argv)
    build = bool(a.states) and a.states[0].lower() == 'build'
    states = [s.upper() for s in (a.states[1:] if build else a.states)] or ([] if build else ['MN', 'NY', 'SC'])
    links = find_links(here)
    v2script = next((p for p in (here / 'kpc_us_key_v2.py', links / '.github' / 'scripts' / 'kpc_us_key_v2.py') if p.is_file()),
                    links / '.github' / 'scripts' / 'kpc_us_key_v2.py')   # beside this file on the PC (the kit folder), else in the repo copy
    if not v2script.is_file():
        say('The v2 key builder (kpc_us_key_v2.py) is not on this PC yet. Nothing was run.'); return 2
    card = next((p for p in (here / 'kpc_v2_scorecard.py', links / 'tools' / 'pc-keys' / 'kpc_v2_scorecard.py') if p.is_file()), None)
    if not card:
        say('The scorecard (kpc_v2_scorecard.py) is not on this PC yet. Nothing was run.'); return 2
    reports = pathlib.Path(a.reports) if a.reports else here / 'reports'
    store = pathlib.Path(a.store) if a.store else find_store(here)
    facts = pathlib.Path(a.facts) if a.facts else find_facts(here, links)
    for what, p in (('the layer files folder', store), ('the park facts', facts)):
        if not p.exists():
            say(f'Not found: {what} ({p}). Nothing was run. Tell Claude.'); return 2
    if build:
        return build_mode(states, store, facts, links, v2script, card, reports, reports.parent / 'v2-keys')
    base = find_baseline(reports, states, a.base)
    if not base:
        say('No earlier v1 test holds a key for ' + ' '.join(states) + '. Run the key test (START-HERE) for these states first. Nothing was run.'); return 2
    secs = v1_seconds(base, states)
    if a.try_rules:
        tr = pathlib.Path(a.try_rules)
        if not tr.is_file():
            say(f'Not found: the trial rules file ({tr}). Nothing was run.'); return 2
        return try_mode(states, tr.resolve(), base, secs, reports, store, facts, links, v2script, card)
    for s in states:
        if s not in secs: say(f'  No v1 build time for {s} in that report: its speed check is skipped.')
    rep = reports / ('v2-' + datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'))
    cold, warm = rep / 'cold', rep / 'warm'
    cold.mkdir(parents=True, exist_ok=True); warm.mkdir(parents=True, exist_ok=True)
    say(f'Comparing v2 with the v1 test {base.name}.')
    say('  v2 first run (writes its locks)...')
    rc1 = run_v2(v2script, states, store, facts, cold, links, write_locks=True)
    if rc1 not in (0, 3, 4):   # 3 = a state was not built, 4 = a state's gate failed: the scorecard still judges the others
        say('The v2 key builder could not start (see above). Tell Claude.'); return 2
    if rc1 in (3, 4): say(f'  The builder did not finish every state (exit {rc1}). The scorecard says which.')
    say('  v2 second run (reads those locks)...')
    rc2 = run_v2(v2script, states, store, facts, warm, links, locks=cold if LOCKS_ARG_IS_RUN_FOLDER else cold / 'locks')
    if rc2 not in (0, 3, 4):
        say('The second v2 run could not start (see above). Tell Claude.'); return 2
    lock, differ = lock_compare(cold, warm, states)
    say(f'  The two runs: {lock}' + (f' ({" ".join(differ)} differ)' if differ else '') + '.')
    cmd = [sys.executable, '-X', 'utf8', str(card), '--v2', str(warm), '--base', str(base / 'keys'), '--store', str(store),
           '--facts', str(facts), '--states', *states, '--out', str(rep), '--repo', str(links), '--lock-check', lock, '--cold', str(cold)]
    if secs: cmd += ['--v1-seconds'] + [f'{k}={v}' for k, v in secs.items()]
    if differ: cmd += ['--lock-differs', *differ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    say('')
    say(r.stdout.rstrip() or r.stderr.rstrip()[-600:])
    say('')
    say(f'The scorecard is {rep / "V2-SCORECARD.txt"}')
    say(f'The park-by-park list is {rep / "v2-vs-base.csv"}')
    return r.returncode if r.returncode in (0, 1) else 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
