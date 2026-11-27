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
import argparse, datetime, pathlib, re, subprocess, sys

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


def has_keys(rep, states):
    return all((rep / 'keys' / f'US-{s}.json.gz').is_file() for s in states)


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
        a, b = pathlib.Path(cold) / f'US-{s}.json.gz', pathlib.Path(warm) / f'US-{s}.json.gz'
        if not (a.is_file() and b.is_file()): continue
        seen += 1
        if a.read_bytes() != b.read_bytes(): diff.append(s)
    return ('differs' if diff else 'same' if seen else 'skipped'), diff


def run_v2(v2script, states, store, facts, out, links, locks=None, write_locks=False):
    cmd = [sys.executable, '-X', 'utf8', str(v2script), '--states', *states, '--store', str(store), '--facts', str(facts),
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


def main(argv=None, here=None):
    here = pathlib.Path(here or HERE)
    ap = argparse.ArgumentParser(description='Test the v2 key side by side with a v1 test already on this PC.')
    ap.add_argument('states', nargs='*'); ap.add_argument('--base'); ap.add_argument('--store'); ap.add_argument('--facts')
    ap.add_argument('--reports'); ap.add_argument('--try', dest='try_rules', help='a trial rule table (json): the TRY A RULE workbench')
    a = ap.parse_args(argv)
    states = [s.upper() for s in a.states] or ['MN', 'NY', 'SC']
    links = find_links(here)
    v2script = links / '.github' / 'scripts' / 'kpc_us_key_v2.py'
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
