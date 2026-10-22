#!/usr/bin/env python3
"""Runs the golden cases in tests/match_cases.json against the real matching code, with no network.

    python3 tests/run_match_tests.py        # prints every case, exits 1 if any is wrong

kpc_us_key.py also calls failures() on start-up and refuses to write answer keys while any case is wrong, so a
broken rule can never reach the data even if it slips through. Nothing here emails anybody.
"""
import json
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = json.loads((ROOT / 'tests' / 'match_cases.json').read_text(encoding='utf-8'))


def _load(script, stop):
    """The functions of a script without running its main part: everything before the `stop` line."""
    src = (ROOT / '.github' / 'scripts' / script).read_text(encoding='utf-8')
    if stop not in src:
        raise RuntimeError(f'{script}: marker {stop!r} not found - update tests/run_match_tests.py')
    m = types.ModuleType(script)
    m.__dict__['__file__'] = str(ROOT / '.github' / 'scripts' / script)
    exec(compile(src.split(stop)[0], script, 'exec'), m.__dict__)
    return m


def failures(verbose=False, groups=('us_names', 'alerts', 'world_names')):
    out = []
    say = print if verbose else (lambda *a, **k: None)

    us = _load('kpc_us_key.py', '\nidx = {}\n') if 'us_names' in groups else None
    for c in (CASES.get('us_names', []) if us else []):
        a, b = c['a'], c['b']
        rec = {'OBJECTID': 1, 'Unit_Nm': b, 'Loc_Nm': '', '_k': us.kinds(b)}
        # the very function run() calls, with the record right next to the pin - the case where a wrong name hurts most
        got = bool(us.join_how(a, us.kinds(a), rec, True))
        ok = got == c['same']
        say(('ok   ' if ok else 'FAIL ') + f"US   {a!r} vs {b!r}: {'same' if got else 'different'}")
        if not ok: out.append(f"US names: {a!r} vs {b!r} should be {'same' if c['same'] else 'different'} — {c['why']}")

    al = _load('kpc_park_alerts.py', "\nif __name__ == '__main__':") if 'alerts' in groups else None
    parks = al.ky_parks() if al else []
    for c in (CASES.get('alerts', []) if al else []):
        got = al.match_parks({'title': c['title'], 'text': c['text']}, parks)
        ok = True
        if 'refs' in c and sorted(got) != sorted(c['refs']): ok = False
        if any(r in got for r in c.get('refs_exclude', [])): ok = False
        say(('ok   ' if ok else 'FAIL ') + f"ALRT {c['title']!r} -> {got}")
        if not ok: out.append(f"Alert {c['title']!r} went to {got} — {c['why']}")

    wk = _load('kpc_world_key.py', '\nfor cc in COUNTRIES:') if 'world_names' in groups else None
    for c in (CASES.get('world_names', []) if wk else []):
        got = bool(wk.same_name(c['cc'], c['a'], c['b']))
        ok = got == c['same']
        say(('ok   ' if ok else 'FAIL ') + f"{c['cc']:4s} {c['a']!r} vs {c['b']!r}: {'same' if got else 'different'}")
        if not ok: out.append(f"{c['cc']} names: {c['a']!r} vs {c['b']!r} should be {'same' if c['same'] else 'different'} — {c['why']}")
    return out


if __name__ == '__main__':
    bad = failures(verbose=True)
    n = sum(len(CASES.get(k, [])) for k in ('us_names', 'alerts', 'world_names'))
    print(f"\n{n - len(bad)} of {n} golden cases right.")
    for b in bad:
        print('  ✗ ' + b)
    sys.exit(1 if bad else 0)
