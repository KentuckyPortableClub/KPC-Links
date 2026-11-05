#!/usr/bin/env python3
"""2-fer key-status gate (Nov 6, Quality 2-fer grade; v2 per-state).

An area / same-land 2-fer is a line-match ONLY when every half is an official outline in the CURRENT key.
A key PIN is not a line-match; approximate goes to "not sure". River / trail rows that use an official LINE still run
(the 100-ft rule does not need an area outline).

Multi-state (Quality Part A grade Nov 5): status is stored PER STATE. US-0367 is pin in US-IA and official in US-MN —
grade the state's copy, or take the WEAKEST status across states (pin < approximate < official) when no area is given.
"""
import json, pathlib, re

RANK = {'missing': -1, 'pin': 0, 'approximate': 1, 'official': 2}
KEY_STATUS = {}       # ref -> weakest status across areas
KEY_BY_AREA = {}      # ref -> {area: status}


def clear():
    KEY_STATUS.clear(); KEY_BY_AREA.clear()


def _status_of(p):
    m = p.get('m') or p.get('tracts') or []
    if p.get('g') == 'pin' or not m: return 'pin'
    if p.get('g') == 'approximate' or any('approx' in str(x[3]) for x in (p.get('m') or []) if len(x) > 3) or p.get('approx'):
        return 'approximate'
    return 'official'


def _put(ref, area, p):
    st = _status_of(p)
    KEY_BY_AREA.setdefault(ref, {})[area or '_'] = st
    cur = KEY_STATUS.get(ref)
    if cur is None or RANK[st] < RANK.get(cur, 99):
        KEY_STATUS[ref] = st  # keep WEAKEST


def load_key_status(root='.'):
    """Fill KEY_STATUS (weakest) and KEY_BY_AREA (per state/province/country file)."""
    if KEY_STATUS: return KEY_STATUS
    root = pathlib.Path(root)
    for f in sorted((root / 'data/us-key').glob('US-??.json')):
        for ref, p in json.load(open(f)).get('parks', {}).items():
            _put(ref, f.stem, p)
    for f in sorted((root / 'data/ca-key').glob('CA-??.json')):
        if not re.fullmatch(r'CA-[A-Z]{2}', f.stem): continue
        for ref, p in json.load(open(f)).get('parks', {}).items():
            _put(ref, f.stem, p)
    try:
        for ref, p in json.load(open(root / 'data/ky-answer-key.json')).get('parks', {}).items():
            _put(ref, 'US-KY', p)
    except Exception: pass  # noqa: BLE001
    for f in sorted((root / 'data/world-key').glob('[A-Z][A-Z].json')):
        for ref, p in json.load(open(f)).get('parks', {}).items():
            _put(ref, f.stem, p)
    return KEY_STATUS


def status_for(ref, area=None):
    """Status for one ref. When area is given and known, use that state's copy; else weakest."""
    load_key_status()
    if area and ref in KEY_BY_AREA and area in KEY_BY_AREA[ref]:
        return KEY_BY_AREA[ref][area]
    return KEY_STATUS.get(ref, 'missing')


def key_line_match(refs, kind, root='.', areas=None):
    """'' = ok to be a line-match candidate; else a status string. Area/same-land only (Quality Nov 5).
    areas: optional dict {ref: area} or list of areas parallel to refs — grades each half in its state."""
    if kind not in ('area', 'same land'): return ''
    load_key_status(root)
    area_of = {}
    if isinstance(areas, dict):
        area_of = areas
    elif isinstance(areas, (list, tuple)) and len(areas) == len(refs):
        area_of = dict(zip(refs, areas))
    pin, apx = [], []
    for r in refs:
        st = status_for(r, area_of.get(r))
        if st == 'pin': pin.append(r)
        elif st == 'approximate': apx.append(r)
    if pin: return 'dropped: key PIN is not a line-match (' + ', '.join(pin) + ')'
    if apx: return 'not sure: key outline is approximate (' + ', '.join(apx) + ')'
    return ''
