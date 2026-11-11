#!/usr/bin/env python3
"""Per-state drop guard for the US key (KPC owner, 2026-11-11): the run fails when a state loses more than 3% of its official parks.

Why: a short read can quietly cost joins (ND 2,168 -> 1,484 records and SD 1,797 -> 1,299 on Nov 10; WI 80,934 -> 1,585 on Nov 6).
The post-key check only warns, after the save. This runs BEFORE the save: it compares each data/us-key/US-XX.json in the working
tree with the copy on main (`git show <ref>:...`) and counts the parks graded official.
  drop = (official on main - official now) / official on main.   Over KPC_DROP_PCT (3) and more than KPC_DROP_MIN (1) park = FAIL.
A drop a person expects (a batch of signed NO answers, say) is let through for that run by naming the states in KPC_DROP_OK
("NV" or "NV UT"; the repo variable of the same name). Exit 1 on a failed state; the workflow then saves nothing from the run.
The outline files are held to the same limit: data/outlines/US-XX.geojson.gz may not hold more than 3% fewer outlines than main's.
Offline. A state with no file on main (new) or no official park on main is skipped.

  python3 .github/scripts/kpc_key_drop_guard.py [--ref HEAD] [--key data/us-key] [--mark FILE]"""
import argparse, glob, gzip, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def official(doc):
    return sum(1 for p in (doc.get('parks') or {}).values() if isinstance(p, dict) and p.get('g') == 'official')


def judge(before, now, pct=3.0, min_parks=1, ok_states=()):
    """before / now: {state: official count}. Returns (failed rows, allowed rows); a row = (state, before, now, percent)."""
    failed, allowed = [], []
    for st in sorted(before):
        b, n = before[st], now.get(st)
        if n is None or b <= 0 or n >= b: continue
        lost = b - n; p = 100.0 * lost / b
        if p > pct and lost > min_parks: (allowed if st in ok_states else failed).append((st, b, n, round(p, 1)))
    return failed, allowed


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--ref', default='HEAD'); ap.add_argument('--key', default='data/us-key')
    ap.add_argument('--repo', default=str(ROOT)); ap.add_argument('--mark')
    a = ap.parse_args()
    pct = float(os.environ.get('KPC_DROP_PCT') or 3); mn = int(os.environ.get('KPC_DROP_MIN') or 1)
    ok = set((os.environ.get('KPC_DROP_OK') or '').replace(',', ' ').upper().split())
    before, now, unread = {}, {}, []
    for f in sorted(glob.glob(os.path.join(a.repo, a.key, 'US-??.json'))):
        st = os.path.basename(f)[3:5]
        r = subprocess.run(['git', 'show', f'{a.ref}:{a.key}/US-{st}.json'], cwd=a.repo, capture_output=True)
        if r.returncode != 0: continue                       # not on main yet: a new state has nothing to drop from
        try: before[st] = official(json.loads(r.stdout)); now[st] = official(json.load(open(f, encoding='utf-8')))
        except ValueError: unread.append(st)
    failed, allowed = judge(before, now, pct, mn, ok)
    ob, on = {}, {}
    for f in sorted(glob.glob(os.path.join(a.repo, 'data', 'outlines', 'US-??.geojson.gz'))):
        st = os.path.basename(f)[3:5]
        r = subprocess.run(['git', 'show', f'{a.ref}:data/outlines/US-{st}.geojson.gz'], cwd=a.repo, capture_output=True)
        if r.returncode != 0: continue
        try: ob[st] = len(json.loads(gzip.decompress(r.stdout))['features']); on[st] = len(json.load(gzip.open(f))['features'])
        except Exception: unread.append(st)  # noqa: BLE001
    of, oa = judge(ob, on, pct, mn, ok)
    for st, b, n, p in oa: print(f'::warning title=Drop guard US-{st}::outlines {b} -> {n} (-{p}%), let through by KPC_DROP_OK for this run')
    for st, b, n, p in of:
        print(f'::error title=Drop guard US-{st}::outlines {b} -> {n} (-{p}%, limit {pct:g}%). The run saves nothing.')
    failed += [r for r in of if r[0] not in {x[0] for x in failed}]; unread = sorted(set(unread))
    for st, b, n, p in allowed:
        print(f'::warning title=Drop guard US-{st}::official parks {b} -> {n} (-{p}%), let through by KPC_DROP_OK for this run')
    for st in unread: print(f'::error title=Drop guard US-{st}::the key file could not be read: counted as a failed state')
    for st, b, n, p in failed:
        print(f'::error title=Drop guard US-{st}::official parks {b} -> {n} (-{p}%, limit {pct:g}%). The run saves nothing. '
              f'If the drop is expected, set the repo variable KPC_DROP_OK to "{st}" for one run.')
    print(f'drop guard: {len(before)} state(s) compared with {a.ref}; {len(failed) + len(unread)} failed, {len(allowed)} let through')
    if failed or unread:
        if a.mark: pathlib.Path(a.mark).write_text(' '.join([r[0] for r in failed] + unread) + '\n')
        return 1
    return 0


if __name__ == '__main__': sys.exit(main())
