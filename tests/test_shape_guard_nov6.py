#!/usr/bin/env python3
"""Nov 6: the US shape-source guard. A state that comes back with zero shapes, or under half
the last live key, is short (Wisconsin run 42230313177: 1,585 vs 80,934). The guard does not
decide a join, so the rules hashes stay us a066624520b4, ca 8feccbb7d9ee, world 1b50faf1dfe8 (6a5969a25d2c since the Nov 7 world rebuild).
No network. Does not read or write the real key files."""
import gzip, json, os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_freeze as KF  # noqa: E402
import kpc_shape_guard as G  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


# The held build's numbers: WI shapes missing, the saved copy is not.
check('zero shapes is short', G.is_short(0, 80934))
check('a missing count is short when the live key has shapes', G.is_short(None, 80934))
check('WI 1585 vs live 80934 is short (under half)', G.is_short(1585, 80934))
check('just under half is short', G.is_short(40466, 80934))
check('half the live count is not short', not G.is_short(40467, 80934))
check('the Nov 3 saved copy (80824) is not short vs the live key', not G.is_short(80824, 80934))
check('a live key with no shapes is not a baseline', not G.is_short(0, 0) and not G.is_short(0, None))
check('the cutoff is half', G.FAR == 0.5)

index = {'states': {'WI': {'padus': 80934, 'matched': 333}, 'IA': {'padus': 100}, 'KY': {'padus': 5}}}
check('live counts come from the index padus field', G.live_counts(index) == {'WI': 80934, 'IA': 100, 'KY': 5})

with tempfile.TemporaryDirectory() as d:
    built = pathlib.Path(d) / 'built'
    built.mkdir()
    (built / 'US-WI.json').write_text(json.dumps({'counts': {'padus': 1585}}), encoding='utf-8')
    (built / 'US-IA.json').write_text(json.dumps({'counts': {'padus': 100}}), encoding='utf-8')
    (built / 'US-CA.json').write_text(json.dumps({'counts': {'padus': 0}}), encoding='utf-8')  # not in this job's states
    rows = G.short_rows(built, index, ['WI', 'IA'])
    check('only the short state in this job is listed', rows == [('WI', 1585, 80934)])
    check('a state this job did not build is not listed', G.short_rows(built, index, ['IA']) == [])
    check('zero shapes in a listed state is listed', G.short_rows(built, {'states': {'CA': {'padus': 50}}}, ['CA']) == [('CA', 0, 50)])
    live = pathlib.Path(d) / 'index.json'
    live.write_text(json.dumps(index), encoding='utf-8')
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_shape_guard.py'),
                        '--built', str(built), '--live-index', str(live), '--states', 'WI IA'],
                       capture_output=True, text=True)
    check('CLI exits 2 and names WI when the read is short', r.returncode == 2 and r.stdout.strip() == 'WI 1585 80934')
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_shape_guard.py'),
                        '--built', str(built), '--live-index', str(live), '--states', 'IA'],
                       capture_output=True, text=True)
    check('CLI exits 0 when the read is at least half', r.returncode == 0 and r.stdout.strip() == '')
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_shape_guard.py'),
                        '--live-index', str(pathlib.Path(d) / 'missing.json'), '--states', 'WI'],
                       capture_output=True, text=True)
    check('a missing live index exits 3', r.returncode == 3)
    zpath = pathlib.Path(d) / 'US-WI.json.gz'
    with gzip.open(zpath, 'wt', encoding='utf-8') as f:
        json.dump({'recs': [{'OBJECTID': 'wid1'}, {'OBJECTID': 'sgwid2'}]}, f)
    check('a saved-outline gzip reports its record count', G.cache_count(zpath) == 2)
    check('cache_count on a bad file is none', G.cache_count(pathlib.Path(d) / 'nope.gz') is None)

import kpc_preflight as PF
for _k, _n in (('us-key', 'US'), ('ca-key', 'Canada'), ('world-key', 'world')):
    check(f'{_n} rules hash equals the newest one in docs/key-rules-change.txt', bool(PF.newest_hash(_k)) and KF.rules_hash(_k) == PF.newest_hash(_k))
check('the guard is not a US rule file', 'kpc_shape_guard.py' not in KF.RULE_FILES['us-key'])
check('the guard is listed as not a rule', 'kpc_shape_guard.py' in KF.NOT_RULES)

y = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
check('the US key build runs the shape guard', 'kpc_shape_guard.py' in y)
check('a short read fails the US job out loud', 'Shape source guard (loud fail)' in y and 'part/shape-guard-fail' in y)
check('a short state is refilled from the saved outlines before it can be published as pins',
      'GEO_CACHE_MODE=only' in y and 'boundary-cache' in y)
ca = (ROOT / '.github/workflows/kpc-ca-key.yml').read_text(encoding='utf-8')
wo = (ROOT / '.github/workflows/kpc-world-key.yml').read_text(encoding='utf-8')
check('Canada and world builds are not wired to this guard', 'kpc_shape_guard.py' not in ca and 'kpc_shape_guard.py' not in wo)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
