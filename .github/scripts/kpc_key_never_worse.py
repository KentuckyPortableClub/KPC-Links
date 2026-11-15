#!/usr/bin/env python3
"""kpc_key_never_worse.py: a store-mode key run never saves a worse area (KPC owner, 2026-11-15; keys in store mode).

A store-mode run (repo variable KPC_KEY_SOURCE=store) reads only the saved whole-layer copies and never a live map, so it can
know LESS than the run that made the key on main (a layer the saved copy lacks, a record that only a live read found). Each area
key file given is compared with its copy on --ref (main):
  joined   = parks with at least one joined record ('m')
  official = parks graded 'official' (the parks drawn with an outline)
An area with FEWER joined or FEWER official parks than on --ref is WORSE: it is printed (::error) and written to --worse-out, and
the workflow keeps that area's key from main. An area that is not on --ref yet, or not readable there, has nothing to be worse
than and passes. A file that cannot be read here counts as worse (fail closed). Joins that changed with the same totals are
listed as a notice (a person can look), not refused. Offline, read only: it never writes a key file.

  python3 .github/scripts/kpc_key_never_worse.py [--ref HEAD] [--repo .] [--worse-out FILE] FILE...
  exit 0 = no area worse; 1 = at least one area worse (named in --worse-out); 2 = bad call.
  python3 .github/scripts/kpc_key_never_worse.py --selftest
Not a rule file: it decides no join (kpc_key_freeze.NOT_RULES). Standard library only.
"""
import argparse, json, os, pathlib, subprocess, sys


def counts(doc):
    parks = (doc or {}).get('parks') or {}
    ps = [p for p in parks.values() if isinstance(p, dict)]
    return {'joined': sum(1 for p in ps if p.get('m')), 'official': sum(1 for p in ps if p.get('g') == 'official')}


def joins(doc):
    return {r: sorted(str(x[0]) for x in (p.get('m') or []) if x) for r, p in ((doc or {}).get('parks') or {}).items() if isinstance(p, dict)}


def compare(before, now):
    """(worse?, why, lost_join_refs): worse when either total went down."""
    b, n = counts(before), counts(now)
    why = [f"{k} {b[k]} -> {n[k]}" for k in ('joined', 'official') if n[k] < b[k]]
    jb, jn = joins(before), joins(now)
    lost = sorted(r for r, ids in jb.items() if ids and not jn.get(r))
    return bool(why), ', '.join(why) or f"joined {b['joined']} -> {n['joined']}, official {b['official']} -> {n['official']}", lost


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', default='HEAD'); ap.add_argument('--repo', default='.'); ap.add_argument('--worse-out')
    ap.add_argument('files', nargs='*')
    a = ap.parse_args(argv)
    repo = pathlib.Path(a.repo).resolve()
    worse = []
    for f in a.files:
        p = pathlib.Path(f); rel = os.path.relpath((p if p.is_absolute() else pathlib.Path.cwd() / p).resolve(), repo)
        name = pathlib.Path(rel).stem
        r = subprocess.run(['git', 'show', f'{a.ref}:{rel}'], cwd=repo, capture_output=True)
        if r.returncode != 0:
            print(f'never worse {name}: not on {a.ref} (a first key): passes'); continue
        try: before = json.loads(r.stdout)
        except ValueError:
            print(f'never worse {name}: the copy on {a.ref} is not readable: passes (nothing to compare with)'); continue
        try: now = json.load(open(repo / rel, encoding='utf-8'))
        except (OSError, ValueError) as e:
            print(f'::error title=Never worse {name}::the new key file could not be read ({type(e).__name__}): kept from {a.ref}')
            worse.append(name); continue
        bad, why, lost = compare(before, now)
        if bad:
            print(f'::error title=Never worse {name}::{why} in this store-mode run (fewer than on {a.ref}): the key is kept from {a.ref}'
                  + (f"; joins lost: {' '.join(lost[:12])}{' ...' if len(lost) > 12 else ''}" if lost else ''))
            worse.append(name)
        elif lost:
            print(f"::notice title=Never worse {name}::{why}; same or more parks joined, but {len(lost)} park(s) lost their join: {' '.join(lost[:12])}")
        else:
            print(f'never worse {name}: {why}: ok')
    if a.worse_out: pathlib.Path(a.worse_out).write_text(''.join(w + '\n' for w in worse))
    print(f'never worse: {len(a.files)} area file(s) checked against {a.ref}; {len(worse)} worse' + (f": {' '.join(worse)}" if worse else ''))
    return 1 if worse else 0


def selftest():
    import tempfile
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)
    J = lambda *ids: {'m': [[i, 'x', 1, 'name'] for i in ids], 'g': 'official'}
    P = {'g': 'pin', 'm': []}
    base = {'parks': {'A': J(1), 'B': J(2), 'C': P}}
    check('same key = not worse', not compare(base, base)[0])
    check('one join lost = worse', compare(base, {'parks': {'A': J(1), 'B': P, 'C': P}})[0])
    check('official -> approximate (same joins) = worse', compare(base, {'parks': {'A': J(1), 'B': dict(J(2), g='approximate'), 'C': P}})[0])
    w, why, lost = compare(base, {'parks': {'A': J(1), 'B': P, 'C': J(3)}})
    check(f'a lost join made up by a new one = not worse, but listed ({lost})', not w and lost == ['B'])
    check('a new park, pin only = not worse', not compare(base, {'parks': dict(base['parks'], D=P)})[0])
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); g = lambda *x: subprocess.run(['git', *x], cwd=t, capture_output=True, check=True)
        g('init', '-q'); g('config', 'user.email', 't@example.invalid'); g('config', 'user.name', 't')
        (t / 'k').mkdir(); (t / 'k/X-1.json').write_text(json.dumps(base)); (t / 'k/X-2.json').write_text(json.dumps(base))
        g('add', '-A'); g('commit', '-qm', 'x')
        (t / 'k/X-2.json').write_text(json.dumps({'parks': {'A': J(1), 'B': P, 'C': P}}))
        (t / 'k/X-3.json').write_text(json.dumps(base))
        out = t / 'worse.txt'
        rc = main(['--repo', str(t), '--worse-out', str(out)] + [str(t / f'k/X-{i}.json') for i in (1, 2, 3)])
        check(f'files: only X-2 worse, exit 1 (got {rc}, {out.read_text().split()})', rc == 1 and out.read_text().split() == ['X-2'])
        (t / 'k/X-2.json').write_text('{broken')
        rc = main(['--repo', str(t), '--worse-out', str(out), str(t / 'k/X-2.json')])
        check('an unreadable new file counts as worse (fail closed)', rc == 1 and out.read_text().split() == ['X-2'])
    print('SELFTEST PASS' if ok else 'SELFTEST FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    if sys.argv[1:2] == ['--selftest']: sys.exit(selftest())
    sys.exit(main())
