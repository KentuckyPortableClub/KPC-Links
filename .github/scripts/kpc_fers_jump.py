#!/usr/bin/env python3
"""2-FER JUMP REPORT (KPC owner, 2026-11-16, handoff 'proof of work', item 5). After a 2-fer run, any area whose 2-fer count
changed by more than a set amount is LISTED for a spot check before release. It holds nothing and marks nothing: no row, file
or status is changed; it only writes the list (data/fers/jump-<tag>.json) and one ::warning line per listed area.

  count  = the number of rows in the area file's 'spots' (data/fers/<area>.json or .json.gz)
  before = the released copy (--old, KPC-Data's data/fers), after = this run's file (--new)
  listed = |after - before| >= --min-change (default 10, env KPC_FERS_JUMP_MIN) AND the count grew or shrank by at least
           --ratio (default 1.5x, env KPC_FERS_JUMP_RATIO); an area with no released copy is listed when after >= --min-change
           (NY Nov 2026: 3 -> 204 with no warning step)

  python3 .github/scripts/kpc_fers_jump.py --old ../KPC-Data/data/fers --new data/fers --tag newyork [--areas US-NY,US-RI]
  python3 .github/scripts/kpc_fers_jump.py --selftest
Exit 0 always (a report, not a gate); exit 1 only on a bad command line or an unreadable NEW file."""
import argparse, gzip, json, os, pathlib, sys, tempfile

AREA_PREFIX = ('US-', 'CA-', 'W-')


def read_count(d, area):
    for name in (f'{area}.json', f'{area}.json.gz'):
        p = pathlib.Path(d, name)
        if p.exists():
            raw = gzip.open(p, 'rt', encoding='utf-8') if name.endswith('.gz') else open(p, encoding='utf-8')
            with raw as f: doc = json.load(f)
            return len(doc.get('spots') or [])
    return None


def areas_in(d):
    out = set()
    for p in pathlib.Path(d).glob('*.json*'):
        n = p.name.split('.json')[0]
        if n.startswith(AREA_PREFIX): out.add(n)
    return sorted(out)


def jumps(old, new, areas=None, min_change=10, ratio=1.5):
    rows = []
    for a in (areas or areas_in(new)):
        after = read_count(new, a)
        if after is None: continue
        before = read_count(old, a) if old and os.path.isdir(old) else None
        ch = after - (before or 0)
        if before is None: listed = after >= min_change
        else:
            big = abs(ch) >= min_change
            far = (before == 0 and after > 0) or (after == 0 and before > 0) or (before and after and max(after / before, before / after) >= ratio)
            listed = bool(big and far)
        rows.append({'area': a, 'before': before, 'after': after, 'change': ch, 'listed': listed})
    return rows


def main(argv=None):
    if '--selftest' in (argv or sys.argv[1:]): return selftest()
    ap = argparse.ArgumentParser()
    ap.add_argument('--old', default=''); ap.add_argument('--new', default='data/fers'); ap.add_argument('--tag', required=True)
    ap.add_argument('--areas', default=''); ap.add_argument('--out', default='')
    ap.add_argument('--min-change', type=int, default=int(os.environ.get('KPC_FERS_JUMP_MIN') or 10))
    ap.add_argument('--ratio', type=float, default=float(os.environ.get('KPC_FERS_JUMP_RATIO') or 1.5))
    a = ap.parse_args(argv)
    areas = [x.strip() for x in a.areas.split(',') if x.strip()] or None
    try: rows = jumps(a.old, a.new, areas, a.min_change, a.ratio)
    except (OSError, ValueError) as e:
        print(f'::error title=2-fer jump report::could not read this run\'s files: {e}'); return 1
    listed = [r for r in rows if r['listed']]
    doc = {'about': 'Jump report (handoff item 5): areas whose 2-fer count changed by more than the set amount, for a spot check before '
                    'release. Holds nothing, marks nothing.', 'tag': a.tag, 'min_change': a.min_change, 'ratio': a.ratio,
           'old': a.old or None, 'listed': listed, 'areas': rows}
    out = a.out or os.path.join(a.new, f'jump-{a.tag}.json')
    with open(out, 'w', encoding='utf-8', newline='\n') as f: json.dump(doc, f, indent=1); f.write('\n')
    for r in listed:
        print(f"::warning title=2-fer jump {r['area']}::{r['before'] if r['before'] is not None else 'no released copy'} -> {r['after']} 2-fers; spot-check before release (nothing held, nothing marked)")
    print(f"2-fer jump report {a.tag}: {len(listed)} of {len(rows)} area(s) listed (change >= {a.min_change} and >= {a.ratio}x) -> {out}")
    return 0


def selftest():
    ok_all, n = True, 0
    def check(name, got, want):
        nonlocal ok_all, n
        n += 1; good = got == want; ok_all &= good
        print(f"{'PASS' if good else 'SELFTEST FAIL'} {name}" + ('' if good else f' (got {got!r}, want {want!r})'))
    with tempfile.TemporaryDirectory() as t:
        old, new = pathlib.Path(t, 'old'), pathlib.Path(t, 'new'); old.mkdir(); new.mkdir()
        def w(d, a, k, gz=False):
            doc = json.dumps({'st': a, 'spots': [{'i': i} for i in range(k)]})
            if gz:
                with gzip.open(d / f'{a}.json.gz', 'wt', encoding='utf-8') as f: f.write(doc)
            else: (d / f'{a}.json').write_text(doc)
        w(old, 'US-ZA', 3); w(new, 'US-ZA', 204)          # the NY case
        w(old, 'US-ZB', 100); w(new, 'US-ZB', 108)        # small drift
        w(old, 'US-ZC', 2); w(new, 'US-ZC', 8)            # big ratio, small change
        w(old, 'CA-ZD', 60, gz=True); w(new, 'CA-ZD', 20, gz=True)   # a big drop, gzip copies
        w(new, 'W-ZE', 12)                                # no released copy
        (new / 'expected-zz.json').write_text('{}')       # not an area file
        before = sorted((p.name, p.read_bytes()) for p in new.iterdir())
        rows = {r['area']: r for r in jumps(str(old), str(new))}
        check('area files only', sorted(rows), ['CA-ZD', 'US-ZA', 'US-ZB', 'US-ZC', 'W-ZE'])
        check('3 -> 204 is listed', (rows['US-ZA']['listed'], rows['US-ZA']['change']), (True, 201))
        check('100 -> 108 is not', rows['US-ZB']['listed'], False)
        check('2 -> 8 is not (under the set change)', rows['US-ZC']['listed'], False)
        check('60 -> 20 is listed (a drop counts too; gzip read)', rows['CA-ZD']['listed'], True)
        check('no released copy and 12 rows is listed', (rows['W-ZE']['before'], rows['W-ZE']['listed']), (None, True))
        check('the run\'s area files are not changed (nothing held, nothing marked)', sorted((p.name, p.read_bytes()) for p in new.iterdir()), before)
        rc = main(['--old', str(old), '--new', str(new), '--tag', 'zz', '--out', str(pathlib.Path(t, 'j.json'))])
        doc = json.loads(pathlib.Path(t, 'j.json').read_text())
        check('the report lists the jumps and exits 0', (rc, [r['area'] for r in doc['listed']]), (0, ['CA-ZD', 'US-ZA', 'W-ZE']))
    print(f"SELFTEST {'PASS' if ok_all else 'FAIL'}: {n} cases")
    return 0 if ok_all else 1


if __name__ == '__main__':
    sys.exit(main())
