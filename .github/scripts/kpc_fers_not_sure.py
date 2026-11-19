#!/usr/bin/env python3
"""kpc_fers_not_sure.py: the 2-fer bot's own doubts, in the shape of the shared NOT-SURE list (hand-off 06, part 3).

It reports. It does not settle a row, it does not read the list back, and it does not hold a pair because of the list.
A withheld park is never named. A tripwire park is not here: the tripwire bot owns those rows.

Two runs on the same inputs write the same bytes: no clock, rows sorted by park number then code, JSON with sorted keys.
Standard library only."""
import json, re

FOUND_BY = '2-fer bot'
CODES = {
    'SUMMARY_MAP_ONLY': "Every joined record is a summary map, not the agency's own land.",
    'NEAR_SIZE_LINE': 'An overlap is within one grid cell of a size line, so the grid cannot tell which side it is on.',
}
WANTS = {
    'SUMMARY_MAP_ONLY': ['official layer'],
    'NEAR_SIZE_LINE': ['map', 'a person'],
}


def _num(ref):
    m = re.search(r'(\d+)$', str(ref))
    return (int(m.group(1)) if m else 10 ** 12, str(ref))


def _row(ref, area, name, code, shows, where, quote):
    return {
        'ref': str(ref),
        'area': str(area or ''),
        'name': str(name or ref),
        'code': code,
        'how_sure': 'unsure',
        'shows_now': str(shows or '')[:300],
        'why': CODES[code],
        'wants': list(WANTS[code]),
        'found_by': FOUND_BY,
        'evidence': [{'where': str(where or '')[:300], 'quote': str(quote or '')[:200]}],
    }


def rows_from(spots_by_area, parks, names, summary_only, withheld=(), tripwire=()):
    """The rows for this run. spots_by_area is {area: [spot, ...]}. summary_only(ref, parks) is the R-2F1 test.
    names is {ref: name}. Withheld refs and tripwire refs are left out."""
    skip = {str(r) for r in withheld} | {str(r) for r in tripwire}
    out, seen = [], set()

    def add(ref, area, code, shows, where, quote):
        ref = str(ref)
        if ref in skip or (ref, code) in seen:
            return
        if any(h and h in (shows or '') for h in skip):
            return
        seen.add((ref, code))
        out.append(_row(ref, area, names.get(ref) or ref, code, shows, where, quote))

    for area, spots in (spots_by_area or {}).items():
        for s in spots or []:
            if not isinstance(s, dict):
                continue
            status = str(s.get('status') or '')
            if status.startswith('not sure: near a size line'):
                for ref in s.get('refs') or []:
                    add(ref, area, 'NEAR_SIZE_LINE', status, f'{area}.json', status)
    for ref, p in (parks or {}).items():
        if not isinstance(p, dict):
            continue
        try:
            hit = bool(summary_only(ref, parks))
        except Exception:
            hit = False
        if hit:
            add(ref, p.get('st') or '', 'SUMMARY_MAP_ONLY', 'approximate: summary map',
                'the key join', CODES['SUMMARY_MAP_ONLY'])
    out.sort(key=lambda r: (_num(r['ref']), r['code']))
    return out


def dumps(rows):
    return json.dumps(rows, indent=1, sort_keys=True, ensure_ascii=False) + '\n'
