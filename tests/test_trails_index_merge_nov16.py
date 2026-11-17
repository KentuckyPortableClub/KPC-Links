#!/usr/bin/env python3
"""Nov 16 2026 (KPC owner): the weekly national-trails bot must merge the trails index, not replace it.

A count of this bot's own list used to become the whole index, so trails other tools had added
fell out even though their line files were still on disk. The rule: keep entries this bot did
not produce when the line file is still there; only remove an entry when its line file is
really gone, and list that drop rather than silently dropping it.

Synthetic data only. Offline, no network, no live trail files are read or written.
This file does not import kpc_us_trails.py (that script starts a build at import time).
(KPC owner, 2026-11-16)"""
import json, os, sys, tempfile, pathlib
HERE = pathlib.Path(__file__).resolve().parent.parent
SRC = (HERE / '.github/scripts/kpc_us_trails.py').read_text(encoding='utf-8')

ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg)
    ok = ok and bool(c)


def rec(ref, name):
    return {'ref': ref, 'name': name, 'kind': 'trail', 'bbox': [0, 0, 1, 1], 'by': 'test', 'kb': 1}


def touch_line(d, ref):
    (d / f'{ref}.json').write_text(json.dumps({
        'type': 'Feature',
        'properties': {'ref': ref, 'name': ref},
        'geometry': {'type': 'MultiLineString', 'coordinates': [[[0, 0], [1, 1]]]}
    }), encoding='utf-8')


# Load only the merge helper from the script (no network, no build).
start = SRC.find('\ndef merge_index_entries(')
end = SRC.find('\nMODE = ', start)
check(start > 0 and end > start, 'kpc_us_trails.py defines merge_index_entries')
ns = {'os': os}
if start > 0 and end > start:
    exec(compile(SRC[start + 1:end], 'merge_index_entries', 'exec'), ns)
merge_index_entries = ns.get('merge_index_entries')
if not callable(merge_index_entries):
    print('SOME FAILED')
    sys.exit(1)


# The write path in the bot must call the merge before it writes index.json.
check('index, _dropped = merge_index_entries(old, index, OUTDIR, note)' in SRC,
      'the bot merges the old index into what it produced, before writing index.json')
if 'json.dump(index, open(OUTDIR + \'/index.json\'' in SRC and 'merge_index_entries(old, index, OUTDIR, note)' in SRC:
    check(SRC.index('merge_index_entries(old, index, OUTDIR, note)') < SRC.index("json.dump(index, open(OUTDIR + '/index.json'"),
          'the merge happens before the index is written')
else:
    check(False, 'the merge happens before the index is written')


# Synthetic area: this bot rebuilt A and B; the old index also had C (file still there)
# and D (file gone). Replace-only would leave only A and B; merge keeps C and lists D.
with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp)
    old = {r: rec(r, n) for r, n in (('A', 'Alpha'), ('C', 'Charlie'), ('D', 'Delta'))}
    produced = [rec('A', 'Alpha rebuilt'), rec('B', 'Bravo')]
    touch_line(d, 'A')
    touch_line(d, 'B')
    touch_line(d, 'C')
    # D has no line file
    notes = []
    merged, dropped = merge_index_entries(old, produced, str(d), lambda t, m: notes.append((t, m)))
    refs = [x['ref'] for x in merged]
    check(refs == ['A', 'B', 'C'], f'merge keeps C (file still there) and this bot\'s A,B; got {refs}')
    check(next(x for x in merged if x['ref'] == 'A')['name'] == 'Alpha rebuilt',
          'a trail this bot rebuilt keeps the new index row, not the old one')
    check(dropped == ['D'], f'D (line file gone) is listed as dropped; got {dropped}')
    check(any(t == 'index dropped' and 'D' in str(m) for t, m in notes),
          f'the drop of D is listed, not silent; notes={notes}')
    check(any(t == 'index kept' and '1 trail' in str(m) for t, m in notes),
          f'C is noted as kept; notes={notes}')
    # Without the fix, writing only `produced` would drop C even though its line file is still there.
    check('C' not in [x['ref'] for x in produced],
          'without the merge, C would have been left out of the written index')


# Empty old index: only what this bot produced is written.
with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp)
    produced = [rec('A', 'Alpha')]
    touch_line(d, 'A')
    merged, dropped = merge_index_entries({}, produced, str(d))
    check([x['ref'] for x in merged] == ['A'] and dropped == [],
          'an empty old index writes only what this bot produced, and drops nothing')


# Every leftover old entry still has a file: all stay, nothing is dropped.
with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp)
    old = {r: rec(r, r) for r in ('X', 'Y')}
    produced = [rec('A', 'Alpha')]
    for r in ('A', 'X', 'Y'):
        touch_line(d, r)
    merged, dropped = merge_index_entries(old, produced, str(d))
    check(sorted(x['ref'] for x in merged) == ['A', 'X', 'Y'] and dropped == [],
          'every old entry whose line file is still there stays in the index')


# If the leftover line files are gone, those entries leave the index and are listed.
with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp)
    old = {r: rec(r, r) for r in ('X', 'Y')}
    produced = [rec('A', 'Alpha')]
    touch_line(d, 'A')
    notes = []
    merged, dropped = merge_index_entries(old, produced, str(d), lambda t, m: notes.append((t, m)))
    check([x['ref'] for x in merged] == ['A'] and dropped == ['X', 'Y'],
          f'gone line files are removed and listed; got refs={[x["ref"] for x in merged]} dropped={dropped}')
    check(any('X' in str(m) and 'Y' in str(m) for t, m in notes if t == 'index dropped'),
          f'both gone files are listed; notes={notes}')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
