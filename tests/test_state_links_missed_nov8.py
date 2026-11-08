#!/usr/bin/env python3
"""Nov 8 2026 (zip-nov7e ITEM4): Kure Atoll US-0121 is in POTA's park data but not in api.pota.app/location/parks/US-HI, so the
weekly park-links build adds it from its own park call (MISSED). Offline: checks the script carries it and still parses."""
import ast, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
s = (ROOT / '.github/scripts/kpc_state_links.py').read_text(encoding='utf-8')
ast.parse(s)
ok = "MISSED = {'HI': ['US-0121']}" in s and 'for ref in MISSED.get(st, [])' in s and s.count("api.pota.app/park/") >= 3
print(('PASS ' if ok else 'FAIL ') + 'US-0121 is added to US-HI from its own POTA park call')
sys.exit(0 if ok else 1)
