#!/usr/bin/env python3
"""Drop guard report lines (O9, 20 Nov). The lost-outline count only sees a park that joined to nothing. Three more
things are reported and never held: records swapped, land gained, a quiet shrink.
Runs on invented parks. A throwaway git repo checks that a swap does not hold the state, and that the REPORT line
is a notice between a released copy and today's key."""
import json, os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_key_drop_guard as G  # noqa: E402

FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


def row(i, acres=10):
    return [i, 'rec', acres, 'name']


def park(ids, acres=None, outline=True):
    p = {'n': 'x', 'g': 'official' if outline else 'pin', 'm': [row(i) for i in ids] if outline else [], 'c': []}
    if acres is not None: p['ac'] = acres
    return p


def doc(parks):
    return {'st': 'ZZ', 'parks': parks}


# invented parks. Same record ids and a small acre change are not reported.
same = G.record_moves(doc({'US-9001': park([1], 100)}), doc({'US-9001': park([1], 120)}))
check(same['swapped'] == [] and same['gained'] == [] and same['shrank'] == [], 'same records, acres inside the band: not reported')

# records swapped: an old id left and a new one came in. The park still has an outline, so lost_parks does not see it.
sw = G.record_moves(doc({'US-9002': park([1, 2])}), doc({'US-9002': park([2, 3])}))
check(sw['swapped'] == ['US-9002'] and sw['why']['US-9002'] == 'ids', 'records swapped: an old id left and a new one came in')
check('US-9002' not in G.lost_parks(doc({'US-9002': park([1, 2])}), doc({'US-9002': park([2, 3])})), 'a swap is not a joined-to-nothing loss')

# gained land: every old id kept, one new id in
ga = G.record_moves(doc({'US-9003': park([1])}), doc({'US-9003': park([1, 4])}))
check(ga['gained'] == ['US-9003'] and ga['why']['US-9003'] == 'ids', 'gained land: a new record id, every old one kept')

# quiet shrink: an old id gone, the park still joined, no new id
sh = G.record_moves(doc({'US-9004': park([1, 2])}), doc({'US-9004': park([1])}))
check(sh['shrank'] == ['US-9004'] and sh['why']['US-9004'] == 'ids', 'quietly shrank: a record id left and the park is still joined')

# joined to nothing stays with the hold count, not these three lines
gone = G.record_moves(doc({'US-9005': park([1])}), doc({'US-9005': park([], outline=False)}))
check(gone['swapped'] == [] and gone['gained'] == [] and gone['shrank'] == [], 'joined to nothing is not one of the three report lines')
check(G.lost_parks(doc({'US-9005': park([1])}), doc({'US-9005': park([], outline=False)})) == {'US-9005'}, 'joined to nothing is still the hold count')

# same records, acres outside the band key health already uses (0.5x-2x)
big = G.record_moves(doc({'US-9006': park([1], 100)}), doc({'US-9006': park([1], 250)}))
small = G.record_moves(doc({'US-9007': park([1], 100)}), doc({'US-9007': park([1], 40)}))
check(big['gained'] == ['US-9006'] and big['why']['US-9006'] == 'acres', 'same records, acres over 2x: gained land')
check(small['shrank'] == ['US-9007'] and small['why']['US-9007'] == 'acres', 'same records, acres under half: quietly shrank')

line = G.report_line({'swapped': 2, 'gained': 3, 'shrank': 4})
check(line.startswith('::notice title=Drop guard report::') and '2 park(s) had their records swapped' in line
      and '3 gained land' in line and '4 quietly shrank' in line and 'nothing is held' in line
      and 'US-' not in line, 'the report line is a notice, gives the three counts, names no park, and says nothing is held')

# a swap in a throwaway repo does not hold the state; the released copy vs today prints the report line and exit stays 0
with tempfile.TemporaryDirectory() as t:
    td = pathlib.Path(t)
    k = td / 'data' / 'us-key'; k.mkdir(parents=True)
    rel = td / 'data' / 'released' / 'us-key'; rel.mkdir(parents=True)
    before = {'st': 'ZZ', 'parks': {'US-9002': park([1, 2]), 'US-9008': park([9])}}
    (k / 'US-ZZ.json').write_text(json.dumps(before))
    (rel / 'US-ZZ.json').write_text(json.dumps(before))
    subprocess.run(['git', 'init', '-q'], cwd=td, check=True)
    subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t', 'add', '-A'], cwd=td, check=True)
    subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-q', '-m', 'main'], cwd=td, check=True)
    now = {'st': 'ZZ', 'parks': {'US-9002': park([2, 3]), 'US-9008': park([9])}}
    (k / 'US-ZZ.json').write_text(json.dumps(now))
    r = subprocess.run([sys.executable, str(ROOT / '.github' / 'scripts' / 'kpc_key_drop_guard.py'),
                        '--repo', str(td), '--ref', 'HEAD', '--approved', str(td / 'none.json')],
                       cwd=td, capture_output=True, text=True, env=dict(os.environ))
    out = r.stdout + r.stderr
    check(r.returncode == 0, f'a swap does not hold the state (rc {r.returncode})')
    check('The state is held' not in out and '::error title=Drop guard' not in out, 'a swap prints no hold and no error')
    check('::notice title=Drop guard report::between the released key and today\'s key: 1 park(s) had their records swapped, 0 gained land, 0 quietly shrank' in out,
          'the report line counts the swap between the released key and today')

print(f'{len(FAILS)} failed' if FAILS else 'ALL PASS')
sys.exit(1 if FAILS else 0)
