#!/usr/bin/env python3
"""Nov 16 2026 (KPC owner): the state trails bot must check both trail indexes before it writes a line.

A saved official line that lives only in index.json (not in the state bot's own index-state.json)
used to be unprotected, so an OpenStreetMap or coarser official read could replace it. Official
beats OpenStreetMap; a finer saved line beats a coarser one. When the bot skips a write, it logs why.

Synthetic data only. Offline, no network, no live trail files are read or written.
This file does not import kpc_state_trails.py (that script starts a build at import time).
(KPC owner, 2026-11-16)"""
import json, math, os, pathlib, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
SRC = (HERE / '.github/scripts/kpc_state_trails.py').read_text(encoding='utf-8')

ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg)
    ok = ok and bool(c)


def km(a, b, c, d):
    r = math.radians
    return 6371 * 2 * math.asin(math.sqrt(math.sin(r(c - a) / 2) ** 2 + math.cos(r(a)) * math.cos(r(c)) * math.sin(r(d - b) / 2) ** 2))


start = SRC.find('\ndef trail_line_stats(')
end = SRC.find('\n# ---------------------------------------------------------------- run', start)
check(start > 0 and end > start, 'kpc_state_trails.py defines the saved-line helpers')
ns = {'json': json, 'os': os, 're': __import__('re'), 'math': math, 'km': km}
if start > 0 and end > start:
    exec(compile(SRC[start + 1:end], 'keep_saved', 'exec'), ns)
if not all(callable(ns.get(n)) for n in ('saved_record', 'keep_saved_reason', 'record_is_official', 'trail_line_stats')):
    print('SOME FAILED')
    sys.exit(1)
saved_record = ns['saved_record']
keep_saved_reason = ns['keep_saved_reason']
record_is_official = ns['record_is_official']


# The write path must check both indexes and call the keep helper.
check('saved_record(ref, IDX, NATIDX, OUT)' in SRC,
      'before writing, the bot looks up the saved line in both indexes')
check('why = keep_saved_reason(saved, off, total, sum(len(l) for l in lines))' in SRC,
      'before writing, the bot asks whether the saved line must be kept')
check('note(ref, f\'{name}: {why}\')' in SRC,
      'when it skips a write, the reason is logged')


def write_line(folder, ref, npts, km_len, official=True):
    deg = km_len / 111.195
    pts = [[0.0, i * deg / (npts - 1)] for i in range(npts)]
    props = {'ref': ref, 'name': ref}
    if official:
        props['source'] = 'official'
        props['by'] = 'USGS National Transportation Dataset (public domain, Nov 7 extract)'
    else:
        props['source'] = 'osm'
        props['by'] = 'Unofficial line (OpenStreetMap)'
    feat = {'type': 'Feature', 'properties': props,
            'geometry': {'type': 'MultiLineString', 'coordinates': [pts]}}
    (folder / f'{ref}.json').write_text(json.dumps(feat), encoding='utf-8')


def old_keep(idx_state, ref, new_km, new_official, folder):
    """The old rule: only index-state.json, and only a new line under half the saved length."""
    o = idx_state.get(ref)
    return bool(o and o.get('km') and new_km < .5 * o['km'] and (o.get('official') or not new_official)
                and (folder / f'{ref}.json').is_file())


# --- US-13626 style: official USGS line only in index.json; a much longer OSM line must not replace it.
# The old rule would write the OSM line: the trail is not in index-state.json, and 114 km is not
# under half of 16 km anyway.
with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp)
    write_line(d, 'US-13626', 80, 16, official=True)
    nat = {'US-13626': {
        'ref': 'US-13626', 'name': 'Sugar River State Trail', 'kind': 'trail',
        'by': 'New Hampshire GRANIT (state agency GIS clearinghouse) via USGS National Transportation Dataset (public domain, Nov 7 extract)',
    }}
    st = {}
    saved = saved_record('US-13626', st, nat, str(d))
    check(saved['exists'] and saved['official'] and saved['in_nat'] and not saved['in_state'],
          f'13626-style: official saved line is found in index.json only; got {saved}')
    why = keep_saved_reason(saved, False, 114, 200)
    check(why and 'official' in why.lower() and 'OpenStreetMap' in why,
          f'13626-style: official beats OSM and the reason is logged; got {why!r}')
    check(not old_keep(st, 'US-13626', 114, False, d),
          'without the fix, the 13626-style OSM line would have been written (not in index-state.json)')


# --- US-9203 style: official USGS line only in index.json; a coarser official read (fewer
# points, shorter) must not replace it. The old half-length rule would allow 88 km vs 138 km (64%).
with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp)
    write_line(d, 'US-9203', 400, 138, official=True)
    nat = {'US-9203': {
        'ref': 'US-9203', 'name': 'Palmetto State Trail', 'kind': 'trail',
        'by': 'U.S. Forest Service and U.S. Fish and Wildlife Service via USGS National Transportation Dataset (public domain, Nov 7 extract)',
    }}
    st = {}
    saved = saved_record('US-9203', st, nat, str(d))
    check(saved['official'] and saved['in_nat'] and not saved['in_state'],
          '9203-style: official saved line is found in index.json only')
    why = keep_saved_reason(saved, True, 88, 40)  # 40 points vs 400: under half, and 88 vs 138 is outside -25%
    check(why and ('coarser' in why or 'outside' in why),
          f'9203-style: finer official line beats a coarser official read; got {why!r}')
    check(not old_keep(st, 'US-9203', 88, True, d),
          'without the fix, the 9203-style coarser official line would have been written (88 km is not under half of 138)')


# --- A better official line may replace a saved OpenStreetMap line (official still wins).
with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp)
    write_line(d, 'US-X', 80, 20, official=False)
    st = {'US-X': {'ref': 'US-X', 'official': False, 'source': 'osm', 'by': 'Unofficial line (OpenStreetMap)', 'km': 20}}
    saved = saved_record('US-X', st, {}, str(d))
    check(not saved['official'], 'a saved OpenStreetMap line is not treated as official')
    why = keep_saved_reason(saved, True, 22, 100)
    check(why is None, f'a new official line may replace a saved OpenStreetMap line; got {why!r}')


# --- A finer official upgrade within the length band may be written.
with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp)
    write_line(d, 'US-Y', 80, 100, official=True)
    st = {'US-Y': {'ref': 'US-Y', 'official': True, 'source': 'official', 'by': 'US Forest Service', 'km': 100}}
    saved = saved_record('US-Y', st, {}, str(d))
    why = keep_saved_reason(saved, True, 105, 200)
    check(why is None, f'a finer official line of almost the same length may replace the saved one; got {why!r}')


# --- The older half-length protection still holds when the saved line is in index-state.json.
with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp)
    write_line(d, 'US-Z', 100, 100, official=True)
    st = {'US-Z': {'ref': 'US-Z', 'official': True, 'source': 'official', 'by': 'US Forest Service', 'km': 100}}
    saved = saved_record('US-Z', st, {}, str(d))
    why = keep_saved_reason(saved, True, 40, 30)
    check(why and 'kept' in why, f'a half-answered new official line does not replace the saved one; got {why!r}')


# --- No saved line: the new line may be written.
why = keep_saved_reason({'exists': False, 'official': False, 'km': 0, 'pts': 0}, True, 10, 20)
check(why is None, 'with no saved line, a new line may be written')


print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
