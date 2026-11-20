#!/usr/bin/env python3
"""Strict 'verified' (2026-11-19; outside review F6, the reviewer's first slice, step S6c): with --strict-verified the fact check
calls a park verified only on a witness NOT read from the joined record (the size), counts 'code' only when every row is a code row
and a record was found, and keeps parks with a soft shape flag (FAR_PIECE / HOLDS_PINS / SIZE_SMALL) out. Off = today's class.
Made-up entries only: the class cases one by one, five planted wrong same-name joins through check_area, and the run with and
without the option.
Run:  python3 tests/test_strict_verified_nov19.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import gzip, json, math, pathlib, shutil, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_factcheck as FC  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

def ent(wit, methods=('name',), rows=1, nir=0, flags=()):
    return {'witnesses': list(wit), 'methods': list(methods), 'rows': rows, 'not_in_read': nir, 'flags': [[f, 'x'] for f in flags]}

# ---- the class cases: (what, entry, class today, class strict, strict_why written?)
CASES = [
    ('name + designation + agency (all from the record)', ent(['name', 'designation', 'agency']), 'verified', 'two', True),
    ('name + pin + designation + agency + second layer, no size', ent(['pin', 'name', 'second layer', 'designation', 'agency']), 'verified', 'two', True),
    ('name + size + designation', ent(['size', 'name', 'designation']), 'verified', 'verified', False),
    ('name + size + pin', ent(['pin', 'size', 'name']), 'verified', 'verified', False),
    ('name + size alone (one other)', ent(['size', 'name']), 'two', 'two', False),
    ('a code row beside a name row (code + name)', ent(['code', 'name'], methods=('name', 'NPS'), rows=2), 'verified', 'two', True),
    ('a code row beside a name row, + size + pin', ent(['code', 'pin', 'size', 'name'], methods=('name', 'NPS'), rows=2), 'verified', 'verified', False),
    ('all-code rows, a record found', ent(['code', 'pin'], methods=('NPS',), rows=2, nir=1), 'verified', 'verified', False),
    ('all-code rows (NPS + official), records found', ent(['code'], methods=('official', 'NPS'), rows=2), 'verified', 'verified', False),
    ('all-code rows, NO record found in the saved shapes', ent(['code', 'name'], methods=('NPS',), rows=2, nir=2, flags=('NOT_IN_READ',)), 'verified', 'two', True),
    ('all-code row, no record, code alone', ent(['code'], methods=('NPS',), nir=1), 'verified', 'one', True),
    ('soft FAR_PIECE on a name + size + 2', ent(['pin', 'size', 'name', 'designation'], flags=('FAR_PIECE',)), 'verified', 'two', True),
    ('soft HOLDS_PINS on all-code + found', ent(['code', 'pin'], methods=('NPS',), flags=('HOLDS_PINS',)), 'verified', 'two', True),
    ('soft SIZE_SMALL on name + designation + agency', ent(['name', 'designation', 'agency'], flags=('SIZE_SMALL',)), 'verified', 'two', True),
    ('another soft flag (SIZE_WEAK) does not block name + size + pin', ent(['pin', 'size', 'name'], flags=('SIZE_WEAK',)), 'verified', 'verified', False),
    ('a hard flag (SHARED) with every witness', ent(['code', 'pin', 'size', 'name', 'designation'], methods=('NPS',), flags=('SHARED',)), 'flagged', 'flagged', False),
    ('a hard flag (PIN_FAR) beside a soft one', ent(['name', 'designation'], flags=('PIN_FAR', 'FAR_PIECE')), 'flagged', 'flagged', False),
    ('one witness', ent(['pin']), 'one', 'one', False),
    ('no witness', ent([]), 'none', 'none', False),
]
for what, e, today, strict, why in CASES:
    off = dict(e); got_off = FC.classify(off)
    on = dict(e); got_on = FC.classify(on, True)
    check(got_off == today and 'strict_why' not in off, f'off: {what} = {today} as today (got {got_off}), no strict_why')
    check(got_on == strict and (('strict_why' in on) == why), f"on: {what} = {strict} (got {got_on}){'; why: ' + on['strict_why'] if 'strict_why' in on else ''}")
e = ent(['code', 'name'], methods=('name', 'NPS'), rows=2); FC.classify(e, True)
check('non-code' in e.get('strict_why', ''), f"the why of a code row beside a name row names it: {e.get('strict_why')!r}")
e = ent(['code'], methods=('NPS',), nir=1); FC.classify(e, True)
check('no record found' in e.get('strict_why', ''), f"the why of all-code rows with no record names it: {e.get('strict_why')!r}")
e = ent(['name', 'designation', 'agency']); FC.classify(e, True)
check('no size' in e.get('strict_why', ''), f"the why of a name + record-only park names the size: {e.get('strict_why')!r}")
e = ent(['name', 'designation', 'agency'], flags=('FAR_PIECE',)); FC.classify(e, True); e['flags'] = []; e['witnesses'].append('size')
check(FC.classify(e, True) == 'verified' and 'strict_why' not in e, 'a re-class that now passes (PIN_FAR dropped later in main) clears the old strict_why')

# ---- five planted wrong same-name joins, through the whole check of one area
def ring(lon, lat, side_km):
    dx, dy = side_km / (111.32 * math.cos(math.radians(lat))), side_km / 110.57
    return [[lon, lat], [lon + dx, lat], [lon + dx, lat + dy], [lon, lat + dy], [lon, lat]]
KEY, BY, PIN = {'parks': {}}, {}, {}
for i in range(5):
    ref, nm, rid = f'US-91{i:02d}', f'Made Up {"ABCDE"[i]}ville State Park', f'mdd{500 + i}'
    # the record carries the park's own name, kind and manager, holds the pin, but is a 9 km square: the wrong (or extra) land
    BY[rid] = {'OBJECTID': rid, 'Unit_Nm': nm, 'Loc_Nm': '', 'Mang_Name': 'STAT', 'Des_Tp': 'SP', 'GIS_Acres': 20015, '_r': [ring(-85.0 + i, 38.0, 9.0)]}
    KEY['parks'][ref] = {'n': nm, 't': 'State Park', 'g': 'official', 'm': [[rid, nm, 20015, 'name']]}
    PIN[ref] = [nm, 'https://parks.madeup.gov/x', 'State Park', '', '', 38.01, -84.99 + i, 3, 0, 0]
AGENCY = {'parks.madeup.gov': {'_parks': 10, 'STAT': 10}}
off = FC.check_area('US-XX', KEY, BY, PIN, {}, agency=AGENCY, today='2026-11-19')['parks']
on = FC.check_area('US-XX', KEY, BY, PIN, {}, agency=AGENCY, today='2026-11-19', strict=True)['parks']
wits = {r: sorted(e['witnesses']) for r, e in off.items()}
check(all({'name', 'designation', 'agency'} <= set(w) and 'size' not in w for w in wits.values()), f'the five planted joins: name + designation + agency agree, no size: {sorted(set(map(tuple, wits.values())))}')
check(all(e['class'] == 'verified' for e in off.values()), 'option off: all five planted wrong joins are verified (the fault F6)')
check(all(e['class'] != 'verified' and e.get('strict_why') for e in on.values()), f"option on: none of the five is verified: {sorted({(e['class'], e['strict_why']) for e in on.values()})}")
check(all('strict_why' not in e for e in off.values()), 'option off: no strict_why in any entry')
TRUTH = {r: {'official': {'acres': 20000.0, 'clean': True, 'sent': f"{KEY['parks'][r]['n']} covers 20,000 acres.", 'url': 'https://x.gov/a'}} for r in KEY['parks']}
good = FC.check_area('US-XX', KEY, BY, PIN, TRUTH, agency=AGENCY, today='2026-11-19', strict=True)['parks']
check(all('size' in e['witnesses'] and e['class'] == 'verified' for e in good.values()), 'option on: the same five with an official size that agrees ARE verified')

# ---- the run, with and without the option
tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-strict-verified-'))
for d in ('cache', 'pinfo', 'keys'): (tmp / d).mkdir()
with gzip.open(tmp / 'cache' / 'US-XX.json.gz', 'wt', encoding='utf-8') as fh: json.dump({'recs': list(BY.values())}, fh)
json.dump({'parks': PIN}, open(tmp / 'pinfo' / 'US-XX.json', 'w')); json.dump(KEY, open(tmp / 'keys' / 'US-XX.json', 'w'))
base = ['run', '--keys', str(tmp / 'keys'), '--cache', str(tmp / 'cache'), '--parkinfo', str(tmp / 'pinfo'), '--date', '2026-11-19']
FC.main(base + ['--out', str(tmp / 'o1')]); FC.main(base + ['--out', str(tmp / 'o2'), '--strict-verified'])
r1 = json.load(open(tmp / 'o1' / 'factcheck-US-XX.json'))['parks']; r2 = json.load(open(tmp / 'o2' / 'factcheck-US-XX.json'))['parks']
check({e['class'] for e in r1.values()} == {'verified'} and not any('strict_why' in e for e in r1.values()), 'the run without the option: the old classes, no strict_why')
check('verified' not in {e['class'] for e in r2.values()} and all(e.get('strict_why') for e in r2.values()), 'the run with --strict-verified: not verified, strict_why written')
check('verified 0' in (tmp / 'o2' / 'factcheck-summary.txt').read_text(), 'the summary of the strict run counts the strict classes')
shutil.rmtree(tmp, ignore_errors=True)

# ---- not a rule file
check('kpc_key_factcheck.py' in KF.NOT_RULES and not any('kpc_key_factcheck' in f for fs in KF.RULE_FILES.values() for f in fs),
      'kpc_key_factcheck.py is in NOT_RULES and in no RULE_FILES (no rules hash moves)')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
