#!/usr/bin/env python3
"""OUTLINE ACRES (2026-11-19; outside review F9, the reviewer's first slice, step S4): the size of a park's outline, measured from
the outline's own shape.

Why: the fact check took the key's 'ac' as the outline's size, but 'ac' is not a measurement (missing on many parks, and on some it
fell to the sum of the row acres while the outline did not change: Maryland US-1588 reads 523 in the key, its outline is about
12,920 acres). This file measures the drawn outline instead.

  polygon_acres(geometry)    acres of one GeoJSON Polygon or MultiPolygon in lon/lat; in each polygon the first ring is the
                             outside and the others are holes, which come off. Anything else, or a broken shape, = 0.0.
  state_acres(folder, area)  {park ref: acres} for one area from <folder>/<area>.geojson.gz and its part files
                             (<area>.p2.geojson.gz ...); a ref with several features gets their sum. No file = {}.

The arithmetic is the fact check's own (kpc_key_factcheck.ring_acres), one ring at a time: no new formula. Not a rule file
(kpc_key_freeze.NOT_RULES): it decides no join, and no rule file imports it. Standard library only."""
import gzip, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from kpc_key_factcheck import ring_acres  # noqa: E402


def _ring_ok(ring):
    return isinstance(ring, list) and all(isinstance(p, (list, tuple)) and len(p) >= 2 and all(isinstance(v, (int, float)) for v in p[:2]) for p in ring)


def _poly_acres(poly):
    if not isinstance(poly, list) or not poly or not all(_ring_ok(r) for r in poly): return 0.0
    return max(0.0, ring_acres([poly[0]]) - sum(ring_acres([h]) for h in poly[1:]))


def polygon_acres(geometry):
    """Acres of a GeoJSON Polygon / MultiPolygon (lon/lat), holes off; 0.0 for anything else or a broken shape."""
    try:
        g = geometry or {}
        if g.get('type') == 'Polygon': return _poly_acres(g.get('coordinates'))
        if g.get('type') == 'MultiPolygon':
            cs = g.get('coordinates')
            return sum(_poly_acres(p) for p in cs) if isinstance(cs, list) else 0.0
    except (AttributeError, TypeError, ValueError): pass
    return 0.0


def area_files(folder, area):
    """The outline file of one area and its part files, in order."""
    d = pathlib.Path(folder)
    return [f for f in [d / f'{area}.geojson.gz'] + sorted(d.glob(f'{area}.p*.geojson.gz')) if f.is_file()]


def state_acres(folder, area):
    """{park ref: measured acres} of one area's outline files (part files included)."""
    out = {}
    for f in area_files(folder, area):
        try: doc = json.load(gzip.open(f, 'rt', encoding='utf-8'))
        except (OSError, ValueError, EOFError): continue
        for ft in doc.get('features') or []:
            ref = ((ft or {}).get('properties') or {}).get('ref')
            if ref: out[ref] = out.get(ref, 0.0) + polygon_acres(ft.get('geometry'))
    return out
