#!/usr/bin/env python3
"""2-fer key-status gate (Nov 6, Quality 2-fer grade).

An area / same-land 2-fer is a line-match ONLY when every half is an official outline in the CURRENT key.
A key PIN is not a line-match; approximate goes to "not sure". River / trail rows that use an official LINE still run
(the 100-ft rule does not need an area outline). Multi-state parks: prefer an outline copy over a pin copy.
"""
import json, pathlib, re

KEY_STATUS = {}   # ref -> 'official' | 'approximate' | 'pin' | 'missing'


def clear():
    KEY_STATUS.clear()


def _put(ref, p):
    m = p.get('m') or p.get('tracts') or []
    if p.get('g') == 'pin' or not m: KEY_STATUS[ref] = 'pin'
    elif p.get('g') == 'approximate' or any('approx' in str(x[3]) for x in (p.get('m') or []) if len(x) > 3) or p.get('approx'):
        KEY_STATUS[ref] = 'approximate'
    else: KEY_STATUS[ref] = 'official'


def load_key_status(root='.'):
    """Fill KEY_STATUS from the current answer keys (US / CA / world / KY). Prefer outline over pin for multi-state."""
    if KEY_STATUS: return KEY_STATUS
    root = pathlib.Path(root)
    for f in sorted((root / 'data/us-key').glob('US-??.json')):
        for ref, p in json.load(open(f)).get('parks', {}).items():
            if ref in KEY_STATUS and KEY_STATUS[ref] == 'official': continue
            _put(ref, p)
    for f in sorted((root / 'data/ca-key').glob('CA-??.json')):
        if not re.fullmatch(r'CA-[A-Z]{2}', f.stem): continue
        for ref, p in json.load(open(f)).get('parks', {}).items():
            if ref in KEY_STATUS and KEY_STATUS[ref] == 'official': continue
            _put(ref, p)
    try:
        for ref, p in json.load(open(root / 'data/ky-answer-key.json')).get('parks', {}).items():
            if ref in KEY_STATUS and KEY_STATUS[ref] == 'official': continue
            _put(ref, p)
    except Exception: pass  # noqa: BLE001
    for f in sorted((root / 'data/world-key').glob('[A-Z][A-Z].json')):
        for ref, p in json.load(open(f)).get('parks', {}).items():
            if ref in KEY_STATUS and KEY_STATUS[ref] == 'official': continue
            _put(ref, p)
    return KEY_STATUS


def key_line_match(refs, kind, root='.'):
    """'' = ok to be a line-match candidate; else a status string. Area/same-land only (Quality Nov 5)."""
    if kind not in ('area', 'same land'): return ''
    load_key_status(root)
    pin = [r for r in refs if KEY_STATUS.get(r, 'missing') == 'pin']
    apx = [r for r in refs if KEY_STATUS.get(r, 'missing') == 'approximate']
    if pin: return 'dropped: key PIN is not a line-match (' + ', '.join(pin) + ')'
    if apx: return 'not sure: key outline is approximate (' + ', '.join(apx) + ')'
    return ''
