"""One way of deciding whether a POTA park and an official land area are the same place, shared by the US, Canada
and world answer keys (Fable's review, Oct 22: 'three scripts, three divergent matchers is the structural fault').

HOW THE WORK IS SPLIT
Each key script still READS names its own way - a generic word in French is not a generic word in English, and
Japan needs romaji - and hands this module plain FACTS about one park and one candidate area: is the kind of
place compatible, are the names the same once read, do they share their words, is the pin inside the outline and
if not how far off is it. This module WEIGHS those facts the same way everywhere, so a rule written once applies
to every country and is measured once.

WHAT THE EVIDENCE IS WORTH (measured on Colorado's saved outlines, Oct 22, not guessed)
A pin INSIDE an area is strong evidence. A pin OUTSIDE is only weak evidence against: of 123 Colorado joins with the
pin outside, 41 were within 100 m (a car park, a gate) and the furthest were all right by name - Vega State Park's
pin is 7.9 km from Vega State Park, Pike National Forest's is 18.8 km out, at the forest office in town. POTA's pins
can be kilometres wrong, so distance only counts against a match when it is large FOR THE SIZE OF THE AREA: a mile
outside a national forest is nothing; a mile outside a 40-acre wildlife area is somewhere else.
An exact name that NO OTHER area nearby carries is also strong evidence, because there is nothing to confuse it with.

Pure functions, no network, no file access: the golden tests and the shadow run call exactly what the keys call.
"""
import math

# ------------------------------------------------------------------------------------------------ geometry
ACRE_KM2 = 0.00404686

# Administrative boundaries, never a park: a BLM field office, a ranger district. A pin falls inside one of these
# almost everywhere in the West, and on Oct 22 that made them look like rivals to the real area - the same mistake as
# Alaska's Beaver Creek Wild and Scenic River joined to 'Eastern Interior Field Office'.
import re as _re
ADMIN = _re.compile(r'\b(field office|district office|ranger district|resource area|administrative unit|'
                    r'supervisor.?s office|management unit office)\b', _re.I)


def is_admin(name):
    return bool(ADMIN.search(str(name or '')))


def rings_of(g):
    return (g or {}).get('rings') or (g if isinstance(g, list) else [])


def inside(la, lo, g):
    """Is the point inside the outline (even-odd across every ring, so holes and islands count right)?"""
    hits = 0
    for r in rings_of(g):
        j = len(r) - 1
        ins = False
        for i in range(len(r)):
            xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
            if (yi > la) != (yj > la) and lo < (xj - xi) * (la - yi) / ((yj - yi) or 1e-15) + xi:
                ins = not ins
            j = i
        hits += ins
    return hits % 2 == 1


def km_to(la, lo, g):
    """Distance in km from the point to the outline's nearest edge; 0 when inside. None when there is no outline."""
    rs = rings_of(g)
    if not rs:
        return None
    if inside(la, lo, g):
        return 0.0
    kx, ky = 111.32 * math.cos(math.radians(la)), 110.57
    best = None
    for ring in rs:
        for i in range(len(ring) - 1):
            x1, y1 = (ring[i][0] - lo) * kx, (ring[i][1] - la) * ky
            x2, y2 = (ring[i + 1][0] - lo) * kx, (ring[i + 1][1] - la) * ky
            dx, dy = x2 - x1, y2 - y1
            L = dx * dx + dy * dy
            t = 0 if L == 0 else max(0.0, min(1.0, -(x1 * dx + y1 * dy) / L))
            d = math.hypot(x1 + t * dx, y1 + t * dy)
            if best is None or d < best:
                best = d
    return best


def size_km(acres):
    """A rough 'width' of the area in km, the square root of its area, never below ~0.2 km."""
    return math.sqrt(max((acres or 0) * ACRE_KM2, 0.05))


# ------------------------------------------------------------------------------------------------ the weighing
# Points. Tuned against measurement, never by feel: change a number, run the golden cases and the shadow
# comparison, and look at what moved before keeping it.
W = {
    'name_exact': 2,        # the names agree once read (generic words gone, accents gone, abbreviations expanded)
    'name_unique': 2,       # ...and no other area within ~10 km carries that name
    'name_words': 1,        # the shorter name's words all appear in the longer one
    'pin_inside': 3,        # POTA's pin falls inside the outline
    'pin_edge': 2,          # outside, but within 250 m or half the area's width: a car park, a gate
                            # (CO, Oct 22: 41 of 123 'outside' pins were within 100 m of the right park)
    'pin_far': 0,           # more than 3 widths away - reported, but NOT held against a match: POTA pins can be
                            # kilometres off (Vega State Park 7.9 km, Pike National Forest 18.8 km, both right)
    'pin_very_far': -3,     # more than 10 widths AND more than 20 km away
    'only_fit_holding_pin': 1,   # the smallest area of a fitting kind that the pin is inside (PIN_JOIN, generalised)
}
JOIN_AT = 4      # enough evidence to join without a person
MARGIN = 2       # and clearly better than the next-best place, or a person decides


def score(f):
    """f = facts about ONE park and ONE candidate area:
         kind_ok      the kinds of place are compatible (or one name gives no kind)       REQUIRED - else rejected
         side_ok      neither says Upper/Lower/North/South/East/West/Middle without the other  REQUIRED
         name_exact, name_unique, name_words      from the caller's own reading of the names
         pin          (lat, lon) of the park, or None
         g, acres     the candidate's outline and size
         smallest_fit True when this is the smallest area of a fitting kind that holds the pin
       Returns (points, reasons)."""
    if not f.get('kind_ok', True):
        return -99, ['a different kind of place']
    if not f.get('side_ok', True):
        # Upper/Lower White Oak Lake are two places; Yates Lake vs Yates Lake WEST may be the whole or a part. Never
        # joined either way - but worth a person's look when the names otherwise agree
        named = f.get('name_exact') or f.get('name_words')
        return (1 if named else -99), ['one name says Upper/Lower/North/South/East/West and the other does not']
    pts, why = 0, []
    if f.get('name_exact'):
        pts += W['name_exact']; why.append('same name')
        if f.get('name_unique'):
            pts += W['name_unique']; why.append('no other place nearby has that name')
    elif f.get('name_words'):
        pts += W['name_words']; why.append('same words')
    pin = f.get('pin')
    if pin and pin[0] is not None:
        d = km_to(pin[0], pin[1], f.get('g'))
        f['km'] = d
        if d is None:
            why.append('no outline to check the pin against')
        elif d == 0:
            pts += W['pin_inside']; why.append('pin inside')
            if f.get('smallest_fit'):
                pts += W['only_fit_holding_pin']; why.append('smallest fitting area holding the pin')
        else:
            rel = d / size_km(f.get('acres'))
            if d <= 0.25 or rel <= 0.5:
                pts += W['pin_edge']; why.append(f'pin {d:.2f} km outside (at the edge)')
            elif rel > 10 and d > 20:
                pts += W['pin_very_far']; why.append(f'pin {d:.0f} km away')
            elif rel > 3:
                pts += W['pin_far']; why.append(f'pin {d:.1f} km off')
            else:
                why.append(f'pin {d:.1f} km outside')
    return pts, why


def decide(groups):
    """groups = [(points, reasons, members)] - one entry per distinct PLACE (all the parcels of one area together).
    Returns ('join' | 'check' | 'none', best_group, runner_up_group)."""
    live = sorted([g for g in groups if g[0] > -50], key=lambda g: -g[0])
    if not live:
        return 'none', None, None
    best = live[0]
    # A place that matches the park's NAME is not seriously rivalled by one that merely holds the pin: in the US
    # the pin sits inside reservoirs, trust land and forests around half the wildlife areas (Fort Lyon SWA lost to
    # John Martin Reservoir that way on Oct 22). Where nothing matches by name (unreadable names abroad), every
    # candidate is a rival as before.
    def named(g): return any(w in ('same name', 'same words') for w in g[1])
    rivals = [g for g in live[1:] if named(g)] if named(best) else live[1:]
    runner = rivals[0] if rivals else None
    if best[0] >= JOIN_AT and (runner is None or best[0] - runner[0] >= MARGIN):
        return 'join', best, runner
    if best[0] >= 1:
        return 'check', best, runner
    return 'none', best, runner
