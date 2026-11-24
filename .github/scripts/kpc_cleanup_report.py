"""Report-only clean-up stage (owner approved D, 24 Nov 2026).

After the ordinary key join (or on a saved key), this builds a report:
it collapses check rows to one row per park per reason, with a count of
folded copies and the record IDs kept on the row; it pre-sorts parks
into sure / needs a person / pin wrong / land wrong / needs a layer;
and it can attach problem-solver verdicts as a last check.

It does not rewrite the key's `c` rows. It does not write joins or
overrides. It is not a rules file (no rules hash moves).
"""
from __future__ import annotations

from collections import OrderedDict

BUCKETS = ('sure', 'needs a person', 'pin wrong', 'land wrong', 'needs a layer')


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
        key = (park, reason, piece)
        if key not in groups:
            groups[key] = {
                'park': park,
                'reason': reason,
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
