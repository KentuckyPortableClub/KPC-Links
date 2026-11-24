"""Report-only clean-up stage (owner approved D, 24 Nov 2026).

After the ordinary key join (or on a saved key), this builds a report:
it collapses check rows to one row per park per reason, with a count of
folded copies and the record IDs kept on the row; it pre-sorts parks
into sure / needs a person / pin wrong / land wrong / needs a layer;
and it can attach problem-solver verdicts as a last check.

Folding is by reason class (numbers and units stripped), not the exact
reason text, so "size: 15.01 times" and "size: 5.25 times" are one row.

A small command reads data/us-key/US-*.json (c rows [id, name, acres, why])
and writes the collapsed report. The PC test hook in
tools/pc-keys/kpc_test_keys.py puts the before and after row counts in REPORT.txt.

It does not rewrite the key's `c` rows. It does not write joins or
overrides. It is not a rules file (no rules hash moves).
"""
from __future__ import annotations

import argparse, json, pathlib, re, sys
from collections import OrderedDict

BUCKETS = ('sure', 'needs a person', 'pin wrong', 'land wrong', 'needs a layer')
UNITS = re.compile(r'\b(km|m|mi|ft|acres?|ac|x|times|percent|pct|%)\b', re.I)
PERSON_NO = re.compile(r'\ba person said no to this record\b', re.I)
PARK_REF = re.compile(r'\b(?:US|CA)-\d+\b', re.I)
COUNTY_NAMED = re.compile(r'(names)\s+.+?\s+(County|Counties)\b', re.I)


def reason_class(why):
    """Fold a check-row reason: strip numbers and units, park refs, and a named county.
    A person-NO row that names a place still counts as the same class."""
    s = str(why or '')
    if PERSON_NO.search(s):
        s = 'a person said no to this record'
    s = PARK_REF.sub('PARK', s)
    s = re.sub(r'\d+(?:\.\d+)?', '', s)
    s = UNITS.sub('', s)
    s = COUNTY_NAMED.sub(r'\1 COUNTY', s)
    s = re.sub(r'[^a-z]+', ' ', s.lower())
    return ' '.join(s.split())



def collapse_check_rows(rows):
    """One row per park per reason.

    Each input row is a dict with `park`, `reason`, and optionally `record`,
    `state`, and `piece`. Rows that share a park and reason fold together.
    A second state's own piece of land keeps its own row when `piece` is set
    to a distinct value (the default is no piece, so the same park and reason
    in two states become one row that names both states).

    The input list is not modified. Record IDs stay on the collapsed row
    in first-seen order. The count is the number of input rows folded.
    """
    groups = OrderedDict()
    for raw in rows or []:
        park = raw.get('park')
        reason = raw.get('reason')
        piece = raw.get('piece')
        klass = raw.get('reason_class') or reason_class(reason)
        key = (park, klass, piece)
        if key not in groups:
            groups[key] = {
                'park': park,
                'reason': reason,
                'reason_class': klass,
                'piece': piece,
                'count': 0,
                'records': [],
                'states': [],
            }
        g = groups[key]
        g['count'] += 1
        rec = raw.get('record')
        if rec is not None and rec != '' and rec not in g['records']:
            g['records'].append(rec)
        st = raw.get('state')
        if st and st not in g['states']:
            g['states'].append(st)
    return list(groups.values())


def presort(items):
    """Pre-sort parks into the five report buckets. Counts add up.

    Each item needs a `bucket` in BUCKETS and a `park`. Unknown buckets go
    to `leftover` so they are not hidden. Input is not modified.
    """
    buckets = OrderedDict((b, []) for b in BUCKETS)
    leftover = []
    seen = []
    for it in items or []:
        row = dict(it)
        b = row.get('bucket')
        if b in buckets:
            buckets[b].append(row)
        else:
            leftover.append(row)
        seen.append(row.get('park'))
    counts = {b: len(v) for b, v in buckets.items()}
    counts['leftover'] = len(leftover)
    counts['all'] = sum(counts[b] for b in list(BUCKETS) + ['leftover'])
    return {'buckets': buckets, 'leftover': leftover, 'counts': counts, 'parks': seen}


def cleanup_report(check_rows, solver_verdicts=None):
    """Build the report. Solver verdicts, when given, are a last check only.

    `solver_verdicts` is an optional dict of park id -> {bucket, ...}.
    Parks the solver named are pre-sorted; collapsed check rows are
    returned alongside. The original `check_rows` list is not rewritten
    and is not treated as a key `c` field.
    """
    collapsed = collapse_check_rows(check_rows)
    verdicts = []
    for park, v in (solver_verdicts or {}).items():
        row = dict(v)
        row['park'] = park
        verdicts.append(row)
    sorted_ = presort(verdicts)
    return {
        'collapsed': collapsed,
        'collapsed_count': len(collapsed),
        'input_count': len(check_rows or []),
        'buckets': sorted_['buckets'],
        'leftover': sorted_['leftover'],
        'counts': sorted_['counts'],
        'c_rows_rewritten': False,
    }


def rows_from_key_dir(keys_dir):
    """Read c rows [id, name, acres, why] from US-*.json (or CA-*.json) in keys_dir.
    Display names on the c row are not copied into the report (IDs and reasons only)."""
    keys_dir = pathlib.Path(keys_dir)
    rows = []
    files = sorted(keys_dir.glob('US-*.json')) + sorted(keys_dir.glob('CA-*.json'))
    for f in files:
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        st = f.stem.split('-', 1)[-1]
        parks = d.get('parks') or {}
        if not isinstance(parks, dict):
            continue
        for pid, p in parks.items():
            if not isinstance(p, dict):
                continue
            for x in p.get('c') or []:
                if isinstance(x, list) and x:
                    why = x[3] if len(x) > 3 else ''
                    rows.append({'park': pid, 'reason': why, 'record': x[0], 'state': st})
    return rows


def collapse_summary(rows):
    """Counts for REPORT.txt: raw rows, exact reasons, classes, collapsed rows."""
    rows = list(rows or [])
    exact = {(r.get('park'), r.get('reason')) for r in rows}
    classes = {(r.get('park'), reason_class(r.get('reason'))) for r in rows}
    collapsed = collapse_check_rows(rows)
    return {
        'input_count': len(rows),
        'exact_reasons': len({r.get('reason') for r in rows}),
        'reason_classes': len({reason_class(r.get('reason')) for r in rows}),
        'parks_x_reason': len(exact),
        'parks_x_class': len(classes),
        'collapsed_count': len(collapsed),
        'c_rows_rewritten': False,
        'collapsed': collapsed,
    }


def report_line(summary):
    """One counts-only line for REPORT.txt, for example '16,853 check rows → 2,309 (folded by reason class)'."""
    a = summary.get('input_count') or 0
    b = summary.get('collapsed_count') or 0
    n_exact = summary.get('exact_reasons') or 0
    n_class = summary.get('reason_classes') or 0
    return (f'Check rows (report only, the key\'s c rows were not rewritten): '
            f'{a:,} rows → {b:,} collapsed by reason class '
            f'({n_exact:,} exact reasons → {n_class:,} classes).')


def write_collapsed_report(keys_dir, out_path):
    rows = rows_from_key_dir(keys_dir)
    summary = collapse_summary(rows)
    # Public report: IDs, classes, counts; no display names.
    public = {
        'about': 'Collapsed check-row report. IDs and counts only. The key\'s c rows were not rewritten.',
        'input_count': summary['input_count'],
        'exact_reasons': summary['exact_reasons'],
        'reason_classes': summary['reason_classes'],
        'parks_x_reason': summary['parks_x_reason'],
        'parks_x_class': summary['parks_x_class'],
        'collapsed_count': summary['collapsed_count'],
        'c_rows_rewritten': False,
        'rows': [{'park': r['park'], 'reason_class': r['reason_class'], 'count': r['count'],
                  'records': r['records'], 'states': r['states']} for r in summary['collapsed']],
    }
    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(public, indent=1) + '\n', encoding='utf-8')
    return public, report_line(summary)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Collapse check rows from saved keys. Report only; nothing is written back to the key.')
    ap.add_argument('--keys', required=True, help='Directory of US-*.json key files (for example data/us-key)')
    ap.add_argument('--out', required=True, help='Where to write the collapsed report (JSON, IDs and counts only)')
    args = ap.parse_args(argv)
    public, line = write_collapsed_report(args.keys, args.out)
    print(line, flush=True)
    print(f'Wrote {args.out} ({public["collapsed_count"]} collapsed rows).', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
