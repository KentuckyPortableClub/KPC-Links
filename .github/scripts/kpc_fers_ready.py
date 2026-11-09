#!/usr/bin/env python3
"""2-fer ready-areas gate (Nov 8 2026; Brandon t808u).

Reads .github/fers-ready-areas.json (declared list). An area may run only when it matches an
entry that documents BOTH ownership and management sources. No hardcoded country ifs in the
finder — open a new area by editing the JSON (and bumping key-rules-version.json 'fers').

US-* and CA-* are ready today. W-* is not (no fee ownership wired for world ownership_step).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
READY_FILE = ROOT / '.github' / 'fers-ready-areas.json'


def load_ready(root=None):
    """Load the declared ready-areas file. Missing / broken = empty (nothing ready)."""
    p = pathlib.Path(root or ROOT) / '.github' / 'fers-ready-areas.json'
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return {'about': 'missing', 'require': ['ownership', 'management'], 'areas': {}}


def _entry_ok(ent):
    """Both ownership and management blocks present with a source name."""
    if not isinstance(ent, dict):
        return False
    o, m = ent.get('ownership') or {}, ent.get('management') or {}
    return bool(isinstance(o, dict) and o.get('source') and isinstance(m, dict) and m.get('source'))


def area_ready(area, ready=None):
    """True when area (e.g. US-KY, CA-ON, W-AU) matches a ready entry with both sources."""
    ready = ready if ready is not None else load_ready()
    area = str(area or '').strip().upper()
    if not area:
        return False
    for _name, ent in (ready.get('areas') or {}).items():
        if not _entry_ok(ent):
            continue
        pat = ent.get('match') or ''
        try:
            if pat and re.fullmatch(pat, area):
                return True
        except re.error:
            continue
    return False


def filter_areas(areas, ready=None, log=None):
    """Split areas into (allowed, skipped). skipped items are (area, reason). log(msg) optional."""
    ready = ready if ready is not None else load_ready()
    allowed, skipped = [], []
    for a in areas:
        a = str(a or '').strip().upper()
        if not a:
            continue
        if area_ready(a, ready):
            allowed.append(a)
        else:
            why = (f'{a}: not on .github/fers-ready-areas.json '
                   f'(needs both ownership and management; Brandon Nov 8 / t808u)')
            skipped.append((a, why))
            if log:
                log(why)
    return allowed, skipped


def skip_message(skipped):
    """One clear log / notice line for the gate."""
    if not skipped:
        return ''
    names = ' '.join(a for a, _ in skipped)
    return (f'2-fer ready-areas: SKIP {names} — not declared ready '
            f'(ownership + management required). See .github/fers-ready-areas.json.')


def selftest():
    ok = True

    def check(c, msg):
        nonlocal ok
        print(('PASS ' if c else 'FAIL ') + msg)
        ok = ok and bool(c)

    ready = {
        'require': ['ownership', 'management'],
        'areas': {
            'US-*': {
                'match': r'^US-[A-Z]{2}$',
                'ownership': {'source': 'PAD-US', 'fields': ['Own_Type']},
                'management': {'source': 'PAD-US', 'fields': ['Mang_Name']},
            },
            'CA-*': {
                'match': r'^CA-[A-Z]{2}$',
                'ownership': {'source': 'CPCAD', 'fields': ['OWNER_E']},
                'management': {'source': 'CPCAD', 'fields': ['OWNER_E']},
            },
            'bad': {
                'match': r'^W-XX$',
                'ownership': {'source': 'only-own'},
                # no management
            },
        },
    }
    check(area_ready('US-KY', ready), 'US-KY ready')
    check(area_ready('CA-ON', ready), 'CA-ON ready')
    check(not area_ready('W-AU', ready), 'W-AU not ready')
    check(not area_ready('W-GB', ready), 'W-GB not ready')
    check(not area_ready('W-XX', ready), 'entry without management is not ready')
    allow, skip = filter_areas(['US-TN', 'W-AU', 'CA-BC', 'W-FR'], ready)
    check(allow == ['US-TN', 'CA-BC'], f'filter keeps US/CA: {allow}')
    check([a for a, _ in skip] == ['W-AU', 'W-FR'], f'filter skips world: {skip}')
    check('SKIP' in skip_message(skip) and 'W-AU' in skip_message(skip), 'skip_message names areas')
    # real file on this checkout
    real = load_ready(ROOT)
    check(area_ready('US-OH', real) and area_ready('CA-AB', real) and not area_ready('W-AU', real),
          'repo fers-ready-areas.json: US/CA yes, W-AU no')
    return ok


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(0 if selftest() else 1)
    # CLI: list which of the given areas are ready
    ready = load_ready()
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    allow, skip = filter_areas(args or [], ready, log=lambda m: print(f'::notice title=2-fer ready-areas::{m}', flush=True))
    if skip:
        print(skip_message(skip), flush=True)
    print('allowed=' + ' '.join(allow))
    print('skipped=' + ' '.join(a for a, _ in skip))
    sys.exit(0 if allow or not args else 2)
