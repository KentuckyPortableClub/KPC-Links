"""KEY FACTS: the pin distance and the official record's kind, saved in the answer keys (links-10, Nov 4 2026).

Per Brandon via Super Head Bot (relayed), 7:13 AM CST Nov 4, answering Super's card "Save pin distance and land type in the keys
during this rebuild?": "Yes, add distance and kind to the keys in this rebuild".

Shared by the three key builders (kpc_us_key.py, kpc_ca_key.py, kpc_world_key.py). Just before a key file is saved, EVERY park
(outlined, pinned or dropped) gets one compact field:

  'bk': [id, km, kind, src]            or, when there is no distance,   [id, None, kind, src, why]

  id    the best candidate record: for an outlined park the joined piece nearest the POTA pin; for a park with no outline the
        builder's first candidate ('c', then 'a': the same order kpc_key_dropped.py falls back to); None when there is none
  km    km from the POTA pin to that record's outline on the key's working copy (0.0 = the pin is inside), rounded to 0.01.
        The working copy is the builder's coarse one (GEO_DETAIL, ~1 km in the US key), so read it as 'about'.
  kind  a short code for the kind of place the OFFICIAL RECORD is (never POTA's type):
          src 'des'  from the record's own designation / type field (PAD-US Des_Tp; CPCAD TYPE_E; the world layer's type field),
                     written as a short code; the file's 'bk_kinds' says what each code stands for
          src 'nm'   the layer has no such field: the pre-check's kind_ok() kind tags read from the record's name (TAGS below,
                     kept identical to kpc_precheck.py's by tests/test_key_facts_nov4.py), '+'-joined
          src '-'    neither says a kind: kind ''
  why   only when km is None:  nopin (POTA has no pin), pin00 (POTA's 0,0 pin), pinbad (an impossible pin: latitude past 90 or
        longitude past 180; NEVER moved), noshape (the record has no outline here, e.g. a trail line), nocand (no official record)

Nothing here decides a join or moves a pin: it only measures and labels what the builder already chose. A rule file of all three
keys (kpc_key_freeze.RULE_FILES), so a change here is a rules change. No network."""
import math, re

TAGS = [('memorial', r'national memorial'), ('refuge', r'wildlife refuge|\bnwr\b'), ('wilderness', r'wilderness(?! study)'),
        ('water', r'reservoir|fishing lake'), ('beach', r'\bbeach\b'), ('access', r'fishing access|access site'),
        ('wildforest', r'wild forest'), ('stateforest', r'state forest'), ('hatchery', r'hatchery')]
SAME_PLACE = [{'access', 'water'}, {'access', 'beach'}]
WHY = {'nopin': 'POTA has no pin', 'pin00': "POTA's pin is 0,0", 'pinbad': 'impossible POTA pin (not moved)',
       'noshape': 'the record has no outline in this build', 'nocand': 'no official record found'}
ABOUT = ("bk = [record id, km from the POTA pin (0.01, working copy), kind code, src] or [id, None, kind, src, why] "
         "(links-10; src des = the record's designation field, nm = kind tags from its name, - = none; why: "
         + ', '.join(f'{k} = {v}' for k, v in WHY.items()) + "); bk_kinds = what each 'des' code stands for")


def tags(x):
    x = str(x or '').lower(); return {k for k, r in TAGS if re.search(r, x)}


def kind_ok(t, nm):
    a, b = tags(t), tags(nm)
    if not a or not b: return None
    return bool(a & b) or any(x in pair and y in pair for pair in SAME_PLACE for x in a for y in b)


def pin_why(pin):
    """'' for a usable POTA pin, else the reason code (the pin is never changed)."""
    if not pin or pin[0] is None or pin[1] is None: return 'nopin'
    try: la, lo = float(pin[0]), float(pin[1])
    except (TypeError, ValueError): return 'nopin'
    if la == 0 and lo == 0: return 'pin00'
    if not (-90 <= la <= 90 and -180 <= lo <= 180) or math.isnan(la) or math.isnan(lo): return 'pinbad'
    return ''


def _in_ring(x, y, r):
    ins, j = False, len(r) - 1
    for i in range(len(r)):
        xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi: ins = not ins
        j = i
    return ins


def km_to(la, lo, rings):
    """km from the pin to the outline (rings of [lon, lat]); 0.0 inside (even-odd over all rings); None with no ring."""
    rs = [r for r in (rings or []) if r and len(r) >= 3]
    if not rs: return None
    if sum(1 for r in rs if _in_ring(lo, la, r)) % 2 == 1: return 0.0
    k = math.cos(math.radians(la)) * 111.32
    best = None
    for r in rs:
        for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
            ax, ay, bx, by = (x1 - lo) * k, (y1 - la) * 110.57, (x2 - lo) * k, (y2 - la) * 110.57
            dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
            t = 0 if L == 0 else max(0, min(1, -(ax * dx + ay * dy) / L))
            d = math.hypot(ax + t * dx, ay + t * dy)
            if best is None or d < best: best = d
    return round(best, 2)


def code(text, legend):
    """A short code for a designation text; the same text always gets the same code in one file (legend: code -> text)."""
    t = ' '.join(str(text or '').split())
    if not t: return ''
    for c, v in legend.items():
        if v == t: return c
    if len(t) <= 6 and ' ' not in t: c = t                                  # PAD-US codes are short already ('SP', 'NWR', 'SREC')
    else:
        w = re.findall(r'[^\W\d_]+|\d+', t)
        c = ''.join(x[0] for x in w).upper() if len(w) > 1 else t[:4].upper()
        c = c[:6] or 'K'
    base, n = c, 2
    while c in legend and legend[c] != t: c = f'{base}{n}'; n += 1
    legend[c] = t
    return c


def kind_of(name, des, legend):
    """(kind, src) for one official record: its designation field first, else the kind tags of its name."""
    if str(des or '').strip(): return code(des, legend), 'des'
    tg = tags(name)
    return ('+'.join(sorted(tg)), 'nm') if tg else ('', '-')


def best(p):
    """The candidate list the distance is measured over: the joined pieces (not trail lines), else 'c' then 'a'."""
    m = [x for x in (p.get('m') or []) if isinstance(x, list) and x]
    if m: return m, True
    return [x for x in (p.get('c') or []) + (p.get('a') or []) if isinstance(x, list) and x][:1], False


def fact(p, pin, look, legend):
    """The 'bk' list for one park. look(entry) -> (rings or None, designation text or '') for a key list entry."""
    cs, joined = best(p)
    if not cs: return [None, None, '', '-', 'nocand']
    why = pin_why(pin)
    got = []
    for x in cs:
        rings, des = look(x) if not str(x[0]).startswith('trl') else (None, '')
        km = None if why else km_to(float(pin[0]), float(pin[1]), rings)
        got.append((km, x, des))
        if not joined: break
    with_km = [g for g in got if g[0] is not None]
    km, x, des = min(with_km, key=lambda g: g[0]) if with_km else got[0]
    kind, src = kind_of(x[1] if len(x) > 1 else '', des, legend)
    if km is None: return [x[0], None, kind, src, why or 'noshape']
    return [x[0], km, kind, src]


def stamp(parks, pin_of, look):
    """Write 'bk' on every park; returns (legend, counts). Never raises for one park: a park that fails gets why 'noshape'."""
    legend, n = {}, {'parks': 0, 'km': 0, 'kind': 0}
    for ref, p in parks.items():
        try: p['bk'] = fact(p, pin_of(ref), look, legend)
        except Exception:  # noqa: BLE001
            p['bk'] = [None, None, '', '-', 'noshape']
        n['parks'] += 1; n['km'] += p['bk'][1] is not None; n['kind'] += bool(p['bk'][2])
    return legend, n
