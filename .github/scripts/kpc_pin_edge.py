#!/usr/bin/env python3
"""PIN TO OUTLINE and MEASURED ACRES (Nov 6 2026; ported to Python from the KY GIS Workbench, BDW-Coils tools/ky-maprep-gis.html:
edgeInfo() + acresOf(), which use turf.js booleanPointInPolygon / nearestPointOnLine / area). For the quality checks: is the POTA pin
inside the official outline, how far is it from the nearest edge, and how many acres does the official shape itself measure.

Rings are lists of [lon, lat] (Esri 'rings' or GeoJSON). No network, no third-party library.
  edge_info(lat, lon, rings)   -> {'inside': bool, 'edge_m': metres to the nearest edge, 'at': [lon, lat] of that nearest point}
  acres_rings(rings)           -> acres of an Esri ring list (holes subtract; even-odd, as the 2-fer rasters fill them)
  acres_geojson(geometry)      -> acres of a GeoJSON Polygon / MultiPolygon (turf.area / 4046.86)
"""
import math
import os
import time

R_EARTH = 6378137.0          # turf.js earthRadius (WGS84 semi-major), used by turf.area
ACRE_M2 = 4046.8564224


def _ring_area_m2(ring):
    """turf.js ringArea (signed spherical excess approximation; Chamberlain & Duquette 2007)."""
    n = len(ring)
    if n < 3: return 0.0
    tot = 0.0
    for i in range(n):
        if i == n - 2: lo, mi, up = n - 2, n - 1, 0
        elif i == n - 1: lo, mi, up = n - 1, 0, 1
        else: lo, mi, up = i, i + 1, i + 2
        tot += (math.radians(ring[up][0]) - math.radians(ring[lo][0])) * math.sin(math.radians(ring[mi][1]))
    return tot * R_EARTH * R_EARTH / 2.0


ACRES_S = float(os.environ.get('KPC_ACRES_S', '30'))   # Nov 8: time limit for one acres_rings call (seconds)


class AcresTooSlow(Exception):
    pass


def _in_ring(x, y, r):
    ins, j = False, len(r) - 1
    for i in range(len(r)):
        xi, yi = r[i][0], r[i][1]; xj, yj = r[j][0], r[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi: ins = not ins
        j = i
    return ins


def inside(lat, lon, rings):
    """Even-odd over every ring (holes are holes; two pieces are two pieces)."""
    return sum(1 for r in rings or [] if r and _in_ring(lon, lat, r)) % 2 == 1


def acres_rings(rings):
    """Acres of an Esri ring list: each ring's area counts + or - by how many other rings hold it (even-odd), so holes subtract
    whatever way the rings are wound."""
    rings = [r for r in rings or [] if r and len(r) >= 3]
    # Nov 8 (world W-42480248682, CL stuck 100 min here in kpc_tracts): a ring's first point is only tested against rings whose
    # box holds it. A point outside a ring's box can never be inside that ring, so the answer is exactly the same, only faster.
    # A list too big to finish in ACRES_S seconds raises AcresTooSlow (kpc_tracts leaves ac_measured out, as for any error).
    boxes = []
    for q in rings:
        xs = [p[0] for p in q]; ys = [p[1] for p in q]
        boxes.append((min(xs), min(ys), max(xs), max(ys)))
    stop = time.monotonic() + ACRES_S
    tot = 0.0
    for i, r in enumerate(rings):
        if time.monotonic() > stop: raise AcresTooSlow(f'{len(rings)} rings: over {ACRES_S} s')
        a = abs(_ring_area_m2(r))
        x, y = r[0]
        depth = sum(1 for j, q in enumerate(rings) if j != i and boxes[j][0] <= x <= boxes[j][2] and boxes[j][1] <= y <= boxes[j][3] and _in_ring(x, y, q))
        tot += -a if depth % 2 else a
    return max(tot, 0.0) / ACRE_M2


def acres_geojson(g):
    if not g: return 0.0
    polys = [g['coordinates']] if g.get('type') == 'Polygon' else g.get('coordinates') or [] if g.get('type') == 'MultiPolygon' else []
    m2 = 0.0
    for p in polys:
        if not p: continue
        m2 += abs(_ring_area_m2(p[0])) - sum(abs(_ring_area_m2(h)) for h in p[1:])
    return max(m2, 0.0) / ACRE_M2


def geojson_rings(g):
    if not g: return []
    if g.get('rings'): return g['rings']
    if g.get('type') == 'Polygon': return list(g.get('coordinates') or [])
    if g.get('type') == 'MultiPolygon': return [r for p in g.get('coordinates') or [] for r in p]
    return []


def _xy(lat0, lon, lat):
    """Metres on a local flat projection around the pin (fine for the few-km distances a pin check is about)."""
    k = math.cos(math.radians(lat0))
    return (lon * 111319.49 * k, lat * 110946.26)


def edge_info(lat, lon, rings):
    """inside?, metres from the pin to the nearest edge, and that nearest point ([lon, lat])  (the Workbench's edgeInfo)."""
    px, py = _xy(lat, lon, lat)
    best, at = None, None
    for r in rings or []:
        for i in range(len(r) - 1):
            ax, ay = _xy(lat, r[i][0], r[i][1]); bx, by = _xy(lat, r[i + 1][0], r[i + 1][1])
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
            qx, qy = ax + t * dx, ay + t * dy
            d = math.hypot(px - qx, py - qy)
            if best is None or d < best:
                best = d; at = [r[i][0] + t * (r[i + 1][0] - r[i][0]), r[i][1] + t * (r[i + 1][1] - r[i][1])]
    return {'inside': inside(lat, lon, rings), 'edge_m': None if best is None else round(best, 1), 'at': [round(at[0], 6), round(at[1], 6)] if at else None}


def pin_check(lat, lon, rings, ok_m=30.0):
    """A plain verdict: 'inside', 'edge' (outside but within ok_m), or 'outside'; with the edge distance."""
    e = edge_info(lat, lon, rings)
    e['verdict'] = 'inside' if e['inside'] else ('edge' if e['edge_m'] is not None and e['edge_m'] <= ok_m else 'outside')
    return e


def acres_off(key_ac, measured_ac, ratio=0.5, floor_ac=10.0):
    """True when the key's acres and the measured official shape disagree by more than `ratio` (both ways) and by more than floor_ac."""
    if not key_ac or not measured_ac: return False
    lo, hi = min(key_ac, measured_ac), max(key_ac, measured_ac)
    return hi - lo > floor_ac and lo < hi * (1 - ratio)


if __name__ == '__main__':   # self-test: a 1 km x 1 km square near the equator, a pin 100 m outside
    sq = [[0, 0], [0.008983, 0], [0.008983, 0.009043], [0, 0.009043], [0, 0]]
    a = acres_rings([sq]); e = edge_info(0.0045, 0.009882, [sq])
    assert 245 < a < 250, a
    assert not e['inside'] and 95 < e['edge_m'] < 105, e
    hole = [[0.003, 0.003], [0.006, 0.003], [0.006, 0.006], [0.003, 0.006], [0.003, 0.003]]
    assert 220 < acres_rings([sq, hole]) < 228 and not inside(0.0045, 0.0045, [sq, hole])
    assert abs(acres_geojson({'type': 'Polygon', 'coordinates': [sq, hole]}) - acres_rings([sq, hole])) < 0.5
    print('kpc_pin_edge self-test OK', round(a, 1), e)
