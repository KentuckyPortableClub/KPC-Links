#!/usr/bin/env python3
"""PROBLEM SOLVER: a recommended fix for every held park (Nov 7 2026; Brandon, 4:55 PM CST Nov 7: the key doctor / join check /
holds "must recommend the fix for each held park, not just flag it").

RECOMMENDS ONLY. It never writes a key file, an override, the answer sheet or the ledger, and it NEVER moves a POTA pin. A person
reads each verdict and applies it (an overrides.json 'join' row, a re-point, or a hold kept). OFFLINE: key files, the build's saved
outlines (GEO_CACHE, the boundary-cache copy the US build already downloads), POTA's pins (PARKINFO) and kpc-us-states.json.
Not a rules file (kpc_key_freeze.NOT_RULES): it decides no join, so the rules hashes do not move.

Verdicts (one per park, with plain-words reasons):
  same land new ID   a hand join (overrides.json 'join') names a record id the key no longer has, and a candidate with the park's
                     name sits at the pin (<= 1 km): re-point the join to the new id (Windy Gap US-9678: cow909 -> cow910)
  land wrong         the held record is not the land the pin is on, and another same-name candidate holds the pin: join that one
                     and drop the held one (Little Pee Dee US-3917: 254041 in place of 254129)
  sliver             the held record's outline is a few points with almost no area (a broken polygon), so its distance means
                     nothing: KEEP HOLDING and look for a proper polygon (Cedar Mesa US-11748, Indian Creek US-5782)
  wrong state        the held land lies in another state than POTA lists, and the pin sits in the listed state: override to the
                     land and flag the POTA listing (Owyhee River US-13039: listed NV, land in ID)
  pin wrong          the held record is the park's land (name and kind match, one such place) and POTA's pin is off it: override
                     to keep the land; the reasons say how the pin looks wrong (one digit off, one coordinate off, a rounded
                     2-decimal pin, or simply elsewhere). The pin is NEVER moved.
  needs a person     anything the checks above cannot settle (no pin, names disagree, acres far apart, ...). Nov 9: a hand join
                     the key's row lacks gets fault = 'key setup' and the reason (layer set up for another state only / PAD-US
                     load filter); a held record with no saved outline falls back to the key's own distance + acres
                     ('pin wrong', MEDIUM, only in the plain case: one state, one such name, acres agree)

  KEY=us (only the US key for now)   PARKINFO=<dir> (default kpcdata/data/parkinfo)   GEO_CACHE=<dir> (default cache/us)
  OUT=<file stem> (default data/us-key/review/problem-solver)   STATES=<file> (default kpc-us-states.json)
  --selftest   (the 17 Research Bot calls of Nov 7, tests/fixtures/problem-solver-17.json)
Never fails the build: exit 0 (the selftest exits 1 on a wrong verdict)."""
import glob, gzip, json, math, os, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_match as KM  # noqa: E402  (inside, km_to: even-odd over every ring)

ROOT = pathlib.Path(__file__).resolve().parents[2]
FAR_KM = 15.0                 # = kpc_join_check.FAR_KM
NEAR_KM = 1.0                 # a candidate this close to the pin "holds" it (the key's working copy is ~1 km coarse)
SLIVER_PTS = 6                # a broken polygon: at most this many points in all its rings ...
SLIVER_AC = 0.5               # ... and under half an acre (or under 1% of the acres it claims)
TYPO_KM = 1.0                 # a one-digit fix that puts the pin within this of the land counts as a typo
SMALL_KM = 10.0               # typo patterns are only read on land smaller than this across: on a huge refuge any one-digit
                              # change lands somewhere inside by chance, so it proves nothing
COORD_MATCH = 0.02            # degrees: one coordinate "matches" the land when it is this close to the land's range (~2 km)
ACRE_RATIO = 3.0              # the outline measured vs the acres the record claims: further apart than this = a person looks
GENERIC = set('state national wildlife management area forest park recreation special preserve heritage refuge wilderness '
              'blm srma rma nra wma swa nwr sf sp the of and at on in watchable bay river creek lake canyon mesa site sites wwa sra srs nhp nhs'.split())
SAME_W = {'nine': '9', 'mile': 'mile', 'mt': 'mount', 'ft': 'fort', 'st': 'saint'}
LINEAR = re.compile(r'\b(trail|wild (and|&) scenic river|heritage river|parkway)\b', re.I)   # = kpc_join_check.LINEAR_KIND
PIN_NEVER = 'the POTA pin is never moved'
FRAGMENT_AC = 1.0             # Quality Nov 7 C2: a held outline under this is a fragment of the land, not the land (Klamath 0.48 ac)
# Quality Nov 7 C1: the KIND of place, read from the words same_name() drops. A park and a record whose kinds are both known and
# share none are different places even when the core name matches (Marais des Cygnes Massacre historic site vs the FWS refuge).
KINDS = [('history', r'histor|massacre|battle|monument|memorial|fort\b|site\b'), ('wildlife', r'refuge|\bnwr\b|wildlife|waterfowl|fish|hatchery'),
         ('forest', r'forest|\bsf\b'), ('wild', r'wilderness|\bwsa\b'), ('recreation', r'recreation|\brma\b|\bsrma\b|\bnra\b|\bsra\b'),
         ('water', r'reservoir|\blake\b|\bdam\b'), ('park', r'\bpark\b|\bsp\b|preserve|natural area')]


# ---- plain helpers
def words(s):
    w = re.sub(r'[^a-z0-9 ]+', ' ', str(s or '').lower().replace('-', ' ')).split()
    return [SAME_W.get(x, x) for x in w]


def core(s):
    return {x for x in words(s) if x not in GENERIC and len(x) > 1}


def same_name(park, rec):
    a, b = core(park), core(rec)
    return bool(a and b) and (b <= a or a <= b)


def kinds(s):
    t = str(s or '').lower()
    return {k for k, rx in KINDS if re.search(rx, t)}


def kind_clash(park_txt, rec_txt):
    a, b = kinds(park_txt), kinds(rec_txt)
    return sorted(a), sorted(b), bool(a and b and not (a & b))


def rings(rec): return (rec or {}).get('_r') or []


def n_points(rec): return sum(len(r) for r in rings(rec))


def acres(rec):
    """Measured acres: the absolute sum of the rings' signed areas (ArcGIS outer rings and holes wind opposite ways)."""
    tot = 0.0
    for ring in rings(rec):
        if len(ring) < 3: continue
        lat0 = math.radians(sum(p[1] for p in ring) / len(ring)); kx, ky = 111320.0 * math.cos(lat0), 110574.0
        tot += sum((x1 * kx) * (y2 * ky) - (x2 * kx) * (y1 * ky) for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1])) / 2
    return abs(tot) / 4046.856


def box(rec):
    xs = [p[0] for r in rings(rec) for p in r]; ys = [p[1] for r in rings(rec) for p in r]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def centre(rec):
    """Area-weighted centre of the biggest ring (a vertex mean is pulled toward detailed edges)."""
    rs = sorted(rings(rec), key=lambda r: -abs(_signed(r)))
    if not rs: return None
    r = rs[0]; a = _signed(r)
    if not a: return (sum(p[1] for p in r) / len(r), sum(p[0] for p in r) / len(r))
    cx = sum((x1 + x2) * (x1 * y2 - x2 * y1) for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1])) / (6 * a)
    cy = sum((y1 + y2) * (x1 * y2 - x2 * y1) for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1])) / (6 * a)
    return (cy, cx)


def _signed(r): return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1])) / 2 if len(r) > 2 else 0.0


def km(rec, la, lo):
    return KM.km_to(la, lo, {'rings': rings(rec)}) if rings(rec) else None


def decimals(v):
    s = repr(float(v))
    return len(s.split('.')[1].rstrip('0')) if '.' in s else 0


# ---- the states (kpc-us-states.json: [{'a': 'AL', 'p': multipolygon [[outer, holes...], ...]}])
_ST = None
def state_of(la, lo, path=None):
    global _ST
    if _ST is None:
        try: _ST = json.load(open(path or ROOT / 'kpc-us-states.json', encoding='utf-8'))
        except Exception: _ST = []  # noqa: BLE001
    for s in _ST:
        if any(KM.inside(la, lo, {'rings': pl}) for pl in s.get('p') or []): return s.get('a')
    return None


# ---- pin patterns (descriptions only: the pin is never changed)
def one_digit_fixes(v):
    """Every value one typed digit away from v (one digit changed, or two neighbours swapped), decimals only."""
    s = f'{float(v):.4f}'; i0 = s.index('.') + 1; out = []
    for i in range(i0, len(s)):
        for d in '0123456789':
            if d != s[i]: out.append((float(s[:i] + d + s[i + 1:]), f'digit {i - i0 + 1} after the point {s[i]} -> {d}'))
        if i + 1 < len(s) and s[i] != s[i + 1]:
            out.append((float(s[:i] + s[i + 1] + s[i] + s[i + 2:]), f'digits {i - i0 + 1}-{i - i0 + 2} after the point swapped'))
    # the whole-degree digit too (43.3 typed for 43.5 is a decimal; 71 for 72 is the units digit)
    w = int(abs(float(v))); sg = -1 if float(v) < 0 else 1
    for d in (-1, 1): out.append((sg * (abs(float(v)) + d), f'whole degree {w} -> {w + d}'))
    return out


def pin_pattern(la, lo, rec):
    """How the pin looks wrong against the right land: ('typo', why) / ('one_coord', why) / ('rounded', why) / ('elsewhere', why)."""
    b = box(rec)
    small = bool(b) and math.hypot((b[3] - b[1]) * 110.57, (b[2] - b[0]) * 111.32 * math.cos(math.radians((b[1] + b[3]) / 2))) <= SMALL_KM
    for which, val in (('latitude', la), ('longitude', lo)) if small else ():
        for nv, how in one_digit_fixes(val):
            q = (nv, lo) if which == 'latitude' else (la, nv)
            d = km(rec, *q)
            if d is not None and d <= TYPO_KM:
                return 'typo', f"the {which} looks mistyped: {val} with {how} ({nv:g}) lands {d:.1f} km from the land"
    if small:
        lat_ok = b[1] - COORD_MATCH <= la <= b[3] + COORD_MATCH; lon_ok = b[0] - COORD_MATCH <= lo <= b[2] + COORD_MATCH
        if lat_ok != lon_ok:
            good, bad = ('latitude', 'longitude') if lat_ok else ('longitude', 'latitude')
            return 'one_coord', f"the pin's {good} matches the land but its {bad} is off ({la}, {lo}), so the {bad} may be mistyped"
    if decimals(la) <= 2 and decimals(lo) <= 2:
        return 'rounded', f'the pin is a rough 2-decimal point ({la}, {lo}), only an approximate location'
    return 'elsewhere', f'the pin ({la}, {lo}) is simply away from the land'


# ---- the verdict
def solve(ref, p, pin, recs, override=None, listed_state=None, states_path=None, ctx=None):
    """p = the park's key row; pin = (lat, lon) or None; recs = {record id: saved record with '_r' rings} (may be partial);
    override = the park's overrides.json entry. ctx (Quality Nov 7) = {'states': every state file that lists the park,
    'joined_in': states where the park already has land, 'known_ids': {record id: names} every id this key's rows still list,
    'same_name_recs': {id: name} saved records with the held record's name that the key does not list}. Returns {park, verdict, confidence, recommend, reasons, records}."""
    R = {'park': ref, 'name': p.get('n') or '', 'type': p.get('t') or '', 'state': listed_state or '', 'verdict': 'needs a person',
         'confidence': 'low', 'recommend': 'a person looks (nothing changed)', 'reasons': [], 'records': []}
    why = R['reasons']
    cands = [x for x in (p.get('m') or []) + (p.get('c') or []) if isinstance(x, list) and x]
    held = (p.get('held') or {}).get('ids') or ([p['bk'][0]] if p.get('bk') else [])
    held = [str(h) for h in held if h is not None]
    # a saved outline counts only when it is still the record the key names (ids can be reused between reads: cow910)
    recs = {str(x[0]): recs[str(x[0])] for x in cands if str(x[0]) in recs
            and any(same_name(x[1], recs[str(x[0])].get(k)) for k in ('Unit_Nm', 'Loc_Nm'))}
    km_bk = (p.get('bk') or [None, None])[1]
    ctx = ctx or {}
    others_st = sorted(set(ctx.get('states') or []) - {listed_state})
    if others_st: R['other_states'] = others_st
    # 1. same land, new id
    ov_ids = join_ids(override)
    have = {str(x[0]) for x in cands}
    joined = bool(p.get('m')) and p.get('g') != 'pin'
    if ov_ids and not joined and not (set(ov_ids) & have):
        new = [x for x in cands if same_name(p.get('n'), x[1])]
        bk_id = str((p.get('bk') or [None])[0])
        new.sort(key=lambda x: str(x[0]) != bk_id)
        kn = ctx.get('known_ids') or {}
        # an id counts as still there only under the park's name (ids are reused: CO's cow909 is now another place)
        still = sorted(i for i in ov_ids if i in kn and any(same_name(p.get('n'), nm) for nm in (kn[i] if isinstance(kn, dict) else [p.get('n')])))
        x = new[0] if new else None
        # Quality Nov 7 C3: the distance must be the new record's OWN (not the key's best-record distance), measured on its saved
        # outline, the old id must really be gone (not still in PAD-US in another state: Menominee 272354), and the names must agree
        # in full (a record that leaves words out is not proven the same land: Bonneville, Taylor Creek)
        d_x = None
        if x is not None and pin and recs.get(str(x[0])) and pin[0] not in (None, '') and pin[1] not in (None, ''):
            d_x = km(recs[str(x[0])], float(pin[0]), float(pin[1]))
        elif x is not None and str(x[0]) == bk_id and isinstance(km_bk, (int, float)):
            d_x = float(km_bk)   # the key's own distance IS this record's (its best record); no saved outline under this id
        left = sorted(core(p.get('n')) - core(x[1])) if x else []
        if x is not None and (still or left or d_x is None or d_x > NEAR_KM):
            why.append(f"overrides.json joins {', '.join(ov_ids)}, which this key's row no longer lists")
            if still: why.append(f"but {', '.join(still)} is still a record (another state or the saved outlines), so it is not gone")
            if left: why.append(f"{x[0]} ({x[1]}) leaves out {' '.join(left)!r} of the park's name, so it is not proven the same land")
            if d_x is None: why.append(f"{x[0]} is not the key's best record and has no saved outline here, so its own distance to the pin is unknown")
            elif d_x > NEAR_KM: why.append(f"{x[0]}'s own outline is {d_x:.1f} km from the pin")
            return R
        if x is not None:
            R.update(verdict='same land new ID', confidence='high', recommend=f"re-point the hand join {', '.join(ov_ids)} -> {x[0]} ({x[1]})")
            why.append(f"overrides.json joins {', '.join(ov_ids)}, which is no longer a record anywhere this run can see")
            why.append(f"{x[0]} has the park's name ({x[1]}, ~{x[2]:,} ac) and is {d_x:.2f} km from the pin (its own distance): the same land under a new id")
            twins = [str(y[0]) for y in new[1:] if y[1] == x[1] and y[2] == x[2]]
            if twins: why.append(f"{', '.join(twins)} is the same feature again (same name and acres), not a second candidate")
            return R
    if not pin or pin[0] in (None, '') or pin[1] in (None, '') or (abs(float(pin[0])) < .01 and abs(float(pin[1])) < .01) \
            or abs(float(pin[0])) > 90 or abs(float(pin[1])) > 180:
        why.append('POTA has no usable pin, so the land cannot be checked against it'); return R
    la, lo = float(pin[0]), float(pin[1])
    hrec = [(h, recs.get(h)) for h in held]
    for h, rec in hrec:
        nm = next((x[1] for x in cands if str(x[0]) == h), '')
        R['records'].append({'id': h, 'name': nm, 'points': n_points(rec) if rec else None,
                             'measured_ac': round(acres(rec), 1) if rec else None, 'claimed_ac': (rec or {}).get('GIS_Acres'),
                             'km': round(km(rec, la, lo), 2) if rec and rings(rec) else None})
    # 2. land wrong: another same-name candidate holds the pin
    others = []
    for x in cands:
        if str(x[0]) in held or not same_name(p.get('n'), x[1]): continue
        rec = recs.get(str(x[0]))
        d = km(rec, la, lo) if rec else None
        if d is not None and d <= NEAR_KM: others.append((d, not isinstance(x[0], int), -(x[2] or 0), x))
    held_near = [h for h, rec in hrec if rec is not None and rings(rec) and km(rec, la, lo) <= NEAR_KM]
    if held_near:
        why.append(f"the pin is {'inside' if km(recs[held_near[0]], la, lo) == 0 else 'next to'} the held {held_near[0]} on the saved outline, "
                   f"so the key's {km_bk} km came from its coarse working copy; a person checks the held record")
        return R
    if others and held:
        others.sort(key=lambda t: t[:3]); x = others[0][3]
        R.update(verdict='land wrong', confidence='high', recommend=f"join {x[0]} ({x[1]}) and drop the held {', '.join(held)}")
        why.append(f"the POTA pin is {'inside' if others[0][0] == 0 else f'{others[0][0]:.1f} km from'} {x[0]} ({x[1]}, ~{x[2]:,} ac)")
        for h, rec in hrec:
            d = km(rec, la, lo) if rec else None
            nm = next((y[1] for y in cands if str(y[0]) == h), h)
            why.append(f"the held {h} ({nm}) is " + (f'{d:.1f} km away' if d is not None else f'{km_bk} km away (key)') + ': a different piece of land')
        return R
    if not held:
        miss = [i for i in ov_ids if i not in have]
        if miss and not (set(ov_ids) & have):
            # Nov 9 weekly batch (44 rows said only 'the key names no held record'): say WHY the key's row lacks the hand join
            R['fault'] = 'key setup'
            R['recommend'] = 'fix the key setup named below (nothing changed; the hand join stays, the POTA pin is never moved)'
            why.append(f"overrides.json joins {', '.join(miss)}, but this key's row lists no record at all")
            why.extend(join_gap(i, listed_state, ctx) for i in miss)
            return R
        why.append('the key names no held record'); return R
    h, rec = hrec[0]
    hname = next((x[1] for x in cands if str(x[0]) == h), '')
    if rec is None or not rings(rec):
        why.append(f'no saved outline for {h} in this build, so its shape could not be checked'
                   + (f" (the saved outlines are {ctx['cache_note']}; a layer added since is not in them)" if ctx.get('cache_note') else ''))
        return R   # Nov 9: no_outline_fallback() is written but NOT wired (Quality's Nov 7 rule: no outline -> a person); Quality decides
    # 3. sliver
    pts, mac, cac = n_points(rec), acres(rec), float(rec.get('GIS_Acres') or 0)
    if LINEAR.search(R['type']) and pts <= SLIVER_PTS:
        why.append(f"{h}'s outline is {pts} points, but a {R['type'].lower()} is thin by nature, so the sliver check does not apply")
        return R
    if pts <= SLIVER_PTS and (mac < SLIVER_AC or (cac > 0 and mac < .01 * cac)):
        R.update(verdict='sliver', confidence='high', recommend=f'KEEP HOLDING: {h} is a broken polygon; look for a proper outline of {hname or p.get("n")} ({PIN_NEVER})')
        why.append(f"{h}'s outline is {pts} points and {mac:.2f} acres" + (f', though it claims {cac:,.0f} acres' if cac else ''))
        why.append(f"so its {km_bk} km from the pin means nothing; the pin may well be inside the real area")
        return R
    # 4. the name must match
    if not same_name(p.get('n'), hname):
        why.append(f"the held record's name ({hname}) does not match the park's ({p.get('n')})"); return R
    pk, rk, clash = kind_clash(f"{p.get('n')} {R['type']}", f"{hname} {h} {rec.get('Unit_Nm') or ''} {rec.get('Loc_Nm') or ''}")
    if clash:
        why.append(f"the names match but the kinds do not: the park is a {'/'.join(pk)} place, {h} ({hname}) is {'/'.join(rk)}, "
                   'so they may be different places'); return R
    if mac < FRAGMENT_AC and not LINEAR.search(R['type']):
        why.append(f"{h}'s outline is only {mac:.2f} acres, a fragment of the land, so its distance to the pin proves nothing"); return R
    if others_st:
        why.append(f"the park is also listed in {', '.join(others_st)}; this looks only at the {st_lbl(listed_state)} part"
                   + (f", and it already has land in {', '.join(sorted(ctx.get('joined_in')))}" if ctx.get('joined_in') else '')
                   + ', so the pin may sit on another part'); return R
    unit = sorted(core(hname) - core(p.get('n')))
    if unit:
        why.append(f"{h} ({hname}) adds {' '.join(unit)!r} to the park's name: it is one unit of the park, so the pin may sit on another unit"); return R
    if p.get('m') and p.get('g') != 'pin' and not any(str(x[0]) in held for x in p['m']):
        why.append('the park already has other land joined, so the pin may sit on another parcel'); return R
    extra = {k: v for k, v in (ctx.get('same_name_recs') or {}).items() if k not in {str(x[0]) for x in cands}}
    xr = ctx.get('extra_recs') or {}
    hold = sorted((km(xr[k], la, lo), k) for k in extra if k in xr and rings(xr[k]))
    if hold and hold[0][0] <= NEAR_KM:
        why.append(f"another saved record with the same name, {hold[0][1]} ({extra[hold[0][1]]}), holds the pin "
                   f"({hold[0][0]:.1f} km) but the key did not list it, so the pin may be right and the key misses a parcel"); return R
    if [k for k in extra if k not in xr or not rings(xr[k])]:
        why.append(f"{len(extra)} other saved record(s) carry the same name ({', '.join(list(extra)[:3])}) and could not be measured, "
                   'so another parcel may hold the pin'); return R
    if extra: why.append(f"the other same-name record(s) {', '.join(list(extra)[:3])} are {hold[0][0]:.1f} km or more from the pin too")
    named = [x for x in cands if same_name(p.get('n'), x[1])]
    far_twins = []
    for x in named:
        r2 = recs.get(str(x[0]))
        if r2 is None or str(x[0]) == h: continue
        c1, c2 = centre(rec), centre(r2)
        if c1 and c2 and math.hypot((c1[0] - c2[0]) * 110.57, (c1[1] - c2[1]) * 111.32 * math.cos(math.radians(c1[0]))) > 30 and core(x[1]) == core(hname):
            far_twins.append(x)
    if far_twins:
        why.append(f"two places share the name: {h} and {', '.join(str(x[0]) for x in far_twins)} are over 30 km apart"); return R
    # 5. acres
    if cac > 0 and mac > 0 and not (1 / ACRE_RATIO <= mac / cac <= ACRE_RATIO):
        why.append(f"{h}'s outline measures {mac:,.0f} acres but the record claims {cac:,.0f}"); return R
    pac = float(p.get('ac') or 0)   # the park's own acres in the key (official or POTA), when it has them
    if pac > 0 and mac > 0 and mac / pac < 1 / ACRE_RATIO:
        why.append(f"{h}'s outline is {mac:,.0f} acres but the park is ~{pac:,.0f} acres, so it is only part of the land"); return R
    # 6. wrong state
    c = centre(rec)
    land_st = state_of(*c, path=states_path) if c else None
    pin_st = state_of(la, lo, path=states_path)
    st = (listed_state or '').replace('US-', '')
    if land_st and st and land_st != st and pin_st == st:
        R.update(verdict='wrong state', confidence='high',
                 recommend=f"override: keep {h} ({hname}) and flag the POTA listing: the land is in {land_st}, POTA lists {st} ({PIN_NEVER})")
        why.append(f"{hname} lies in {land_st}; POTA lists the park in {st} and its pin sits in {st}, {km_bk} km from the land")
        why.append('there is only one place with this name in the key, so the land is right and the listing looks wrong')
        return R
    # 7. pin wrong
    kind, how = pin_pattern(la, lo, rec)
    conf = 'high'
    if re.search(r'\bwilderness area\b', R['type'], re.I) and re.search(r'^wsa', h):
        conf = 'medium'; why_k = f"POTA calls it a Wilderness Area but {h} is a Wilderness Study Area (a different kind), so the pin is unexplained"
    else: why_k = None
    R.update(verdict='pin wrong', confidence=conf, recommend=f"override: keep {', '.join(held)} ({hname}) ({PIN_NEVER})")
    if extra:   # other pieces with the same name, all away from the pin too: the park may be several pieces (Quality Nov 7 C2)
        R['confidence'] = 'medium'
        R['recommend'] += f"; check whether the same-name pieces {', '.join(list(extra)[:3])} belong to the park too" 
    why.append(f"{h} is the park's land: same name ({hname})" + (f', ~{cac:,.0f} acres' if cac else f', {mac:,.0f} acres measured'))
    why.append(how)
    if why_k: why.append(why_k)
    return R


def join_gap(i, listed_state, ctx):
    """Nov 9: one plain sentence on why the key's row does not list the hand-joined record i."""
    st = st_lbl(listed_state)
    pre = re.match(r'[a-z]*', str(i)).group(0)
    lay = (ctx.get('layer_states') or {}).get(pre)
    if not pre:
        return (f"{i} is a PAD-US record the {st} key did not read. Since Nov 9 (US rules 464d2ce92eda) a saved id is always loaded by id, "
                f"whatever its Category, owner or PAD-US state; if this key was built before that, the next US key build reads it. "
                f"Still missing after that: PAD-US renumbered or removed the record (the saved name + acres re-find it)")
    if lay is not None and st not in lay['states']:
        return (f"{i}: layer {pre} ({lay['name']}) is set up only for {', '.join(sorted(lay['states'])) or 'no state'} in data/state-gis.json, "
                f"so the {st} key never reads it (add the layer for {st}, limited to the joined records)")
    if lay is not None:
        return (f"{i}: layer {pre} ({lay['name']}) is set up for {st} in data/state-gis.json, but this key's row does not list the record: "
                f"the key was built before the layer was set up for {st}, its 'where' filter leaves the record out, or the record is gone")
    return f"{i}: layer {pre} did not return this record for {st} (a built-in layer of the US key, or one this checkout does not list)"


def no_outline_fallback(R, p, h, hname, held, km_bk, cands, listed_state, others_st):
    """Nov 9 weekly batch (38 rows: 'no saved outline ... in this build'): the saved outlines are an older copy, so a layer added
    since (NV 'sgnvi', Nov 7) has none. When the held record IS the key's best record, the key's OWN distance and the record's acres
    still settle the plain case: same name and kind, one state, the park's acres agree. Then 'pin wrong' at MEDIUM confidence (the
    shape was not checked); anything else stays with a person. Recommends only; the pin is never moved."""
    why = R['reasons']
    x = next((y for y in cands if str(y[0]) == h), None)
    bk_id = str((p.get('bk') or [None])[0])
    if x is None or h != bk_id or not isinstance(km_bk, (int, float)) or km_bk <= NEAR_KM:
        return R
    if not same_name(p.get('n'), hname):
        why.append(f"the held record's name ({hname}) does not match the park's ({p.get('n')})"); return R
    pk, rk, clash = kind_clash(f"{p.get('n')} {R['type']}", f"{hname} {h}")
    if clash:
        why.append(f"the names match but the kinds do not ({'/'.join(pk)} vs {'/'.join(rk)})"); return R
    if others_st:
        why.append(f"the park is also listed in {', '.join(others_st)}, so the pin may sit on another part"); return R
    if sorted(core(hname) - core(p.get('n'))):
        why.append(f"{h} ({hname}) adds words to the park's name: it may be one unit of the park"); return R
    if p.get('m') and p.get('g') != 'pin' and not any(str(y[0]) in held for y in p['m']):
        why.append('the park already has other land joined, so the pin may sit on another parcel'); return R
    if len([y for y in cands if same_name(p.get('n'), y[1])]) > 1:
        why.append('more than one record carries the name and none can be measured here'); return R
    cac, pac = float(x[2] or 0), float(p.get('ac') or 0)
    if cac > 0 and pac > 0 and not (1 / ACRE_RATIO <= cac / pac <= ACRE_RATIO):
        why.append(f"{h} claims {cac:,.0f} acres but the park is ~{pac:,.0f} acres"); return R
    R.update(verdict='pin wrong', confidence='medium',
             recommend=f"override: keep {h} ({hname}) ({PIN_NEVER}); medium: no saved outline, so the shape was not checked")
    why.append(f"{h} is the park's land by name ({hname}" + (f", ~{cac:,.0f} acres" if cac else '') + ") and the only record with it")
    why.append(f"the key's own distance from the pin is {km_bk} km (measured by the build on its working copy)")
    return R


def st_lbl(s): return str(s or '').replace('US-', '') or 'listed'


# ---- the run
def layer_states(root):
    """Nov 9: {layer prefix: {'name', 'states'}} for the state-GIS layers (data/state-gis.json; the prefix is fixed by the layer's
    address in data/us-key/layers.json, so the same address listed under two states is one prefix read in both)."""
    root = pathlib.Path(root)
    try:
        lj = json.load(open(root / 'data/us-key/layers.json', encoding='utf-8'))
        sg = json.load(open(root / 'data/state-gis.json', encoding='utf-8')).get('states') or {}
    except Exception: return {}  # noqa: BLE001
    by = {v[0].split('/query')[0].rstrip('/'): (k, v[2] if len(v) > 2 else k) for k, v in lj.items() if isinstance(v, list) and v and str(v[0]).startswith('http')}
    out = {k: {'name': nm, 'states': set()} for k, nm in by.values() if k.startswith('sg')}
    for st, lays in sg.items():
        for l in lays or []:
            k = by.get(str(l.get('url') or '').rstrip('/'))
            if k and k[0] in out: out[k[0]]['states'].add(st)
    return out


SAVED = {}   # Nov 9: state -> the saved outlines' own 'saved' date (the boundary-cache copy), for the reasons


def cache_note(cache_dir, st):
    return f"from {SAVED[st]}" if SAVED.get(st) else ''


def load_recs(cache_dir, st):
    f = pathlib.Path(cache_dir) / f'US-{st}.json.gz'
    if not f.exists(): return {}
    try:
        d = json.load(gzip.open(f, 'rt', encoding='utf-8'))
        if d.get('saved'): SAVED[st] = str(d['saved'])
        return {str(r.get('OBJECTID')): r for r in d.get('recs') or []}
    except Exception: return {}  # noqa: BLE001


def join_ids(override):
    """The record ids an overrides.json 'join' names (a 'join' can also name a place by its name: those are not ids)."""
    return [str(x) for x in ((override or {}).get('join') or []) if re.fullmatch(r'[a-z]{0,8}\d+', str(x).strip())]


def drift(p, override):
    """A hand join whose ids are all gone, on a park the key left without an outline."""
    ids = join_ids(override)
    if not ids or (p.get('m') and p.get('g') != 'pin'): return False
    return not (set(ids) & {str(x[0]) for x in (p.get('m') or []) + (p.get('c') or []) if x})


def todo(p):
    return bool(p.get('held')) or p.get('far') == 'well outside' or bool(p.get('pin_may_be_wrong'))


def run(env=None, root='.'):
    env = env or os.environ; root = pathlib.Path(root)
    pi_dir = pathlib.Path(env.get('PARKINFO') or root / 'kpcdata/data/parkinfo')
    cache = env.get('GEO_CACHE') or str(root / 'cache/us')
    ov = {}
    try: ov = json.load(open(root / 'data/us-key/overrides.json', encoding='utf-8')).get('parks') or {}
    except Exception: pass  # noqa: BLE001
    out = []
    files = {}
    for f in sorted(glob.glob(str(root / 'data/us-key/US-??.json'))):
        try: files[pathlib.Path(f).stem[3:]] = json.load(open(f, encoding='utf-8')).get('parks') or {}
        except Exception: continue  # noqa: BLE001
    lay_st = layer_states(root)
    where, joined_in, known = {}, {}, {}
    for st, parks in files.items():
        for r, p in parks.items():
            if not isinstance(p, dict): continue
            where.setdefault(r, []).append('US-' + st)
            if p.get('m') and p.get('g') != 'pin' and not p.get('held'): joined_in.setdefault(r, set()).add(st)
            for x in (p.get('m') or []) + (p.get('c') or []):
                if isinstance(x, list) and x: known.setdefault(str(x[0]), set()).add(str(x[1]) if len(x) > 1 else '')
    # (the saved outlines are an older read, so only the key's own rows say an id still exists: CO's cache still has cow909)
    for st, parks in files.items():
        pick = {r: p for r, p in parks.items() if isinstance(p, dict) and (todo(p) or drift(p, ov.get(r)))}
        if not pick: continue
        try: pins = json.load(open(pi_dir / f'US-{st}.json', encoding='utf-8')).get('parks') or {}
        except Exception: pins = {}  # noqa: BLE001
        recs = load_recs(cache, st)
        by_name = {}
        for k, v in recs.items(): by_name.setdefault(' '.join(sorted(core(v.get('Unit_Nm') or v.get('Loc_Nm')))), {})[k] = v.get('Unit_Nm') or v.get('Loc_Nm')
        for r, p in sorted(pick.items()):
            row = pins.get(r) or []
            hid = str(((p.get('held') or {}).get('ids') or [(p.get('bk') or [None])[0]])[0])
            hn = next((x[1] for x in (p.get('m') or []) + (p.get('c') or []) if isinstance(x, list) and x and str(x[0]) == hid), '')
            pre = re.match(r'[a-z]*', hid).group(0)   # the same layer only (an HMA or a WSA with the name is another kind of land)
            sn = {k: v for k, v in by_name.get(' '.join(sorted(core(hn))), {}).items()
                  if k != hid and re.match(r'[a-z]*', k).group(0) == pre} if core(hn) else {}
            ctx = {'states': where.get(r, []), 'joined_in': joined_in.get(r, set()) - {st}, 'known_ids': known, 'same_name_recs': sn,
                   'extra_recs': {k: recs[k] for k in sn}, 'layer_states': lay_st, 'cache_note': cache_note(cache, st)}
            out.append(solve(r, p, (row[5], row[6]) if len(row) > 6 else None, recs, ov.get(r), 'US-' + st, ctx=ctx))
    stem = pathlib.Path(env.get('OUT') or root / 'data/us-key/review/problem-solver')
    stem.parent.mkdir(parents=True, exist_ok=True)
    n = {}
    for x in out: n[x['verdict']] = n.get(x['verdict'], 0) + 1
    json.dump({'about': 'recommendations only: nothing is applied and no POTA pin is moved (kpc_problem_solver.py)',
               'counts': n, 'parks': out}, open(str(stem) + '.json', 'w', encoding='utf-8'), indent=1)
    open(str(stem) + '.md', 'w', encoding='utf-8').write(md(out, n))
    print(f'problem solver: {len(out)} parks; ' + ', '.join(f'{k} {v}' for k, v in sorted(n.items())))
    return out


def md(out, n):
    L = ['# Problem solver: a recommended fix for each held park', '',
         'Recommendations only. Nothing here is applied, and no POTA pin is ever moved. A person applies each one.', '',
         ', '.join(f'**{v}** {k}' for k, v in sorted(n.items())) or 'Nothing held.', '',
         '| Park | State | Name | Verdict | Confidence | Recommended fix | Why |', '|---|---|---|---|---|---|---|']
    for x in out:
        stx = x.get('state', '').replace('US-', '') + (f" (also {', '.join(s.replace('US-', '') for s in x['other_states'])})" if x.get('other_states') else '')
        L.append(f"| {x['park']} | {stx} | {x['name']} | {x['verdict']} | {x['confidence']} | {x['recommend']} | {'; '.join(x['reasons'])} |".replace('\n', ' '))
    return '\n'.join(L) + '\n'


# ---- the selftest: Research Bot's 17 calls (Nov 7, approved by Brandon 4:54 PM CST)
EXPECT = {'US-0150': 'pin wrong', 'US-10281': 'pin wrong', 'US-11401': 'pin wrong', 'US-12028': 'pin wrong', 'US-4894': 'pin wrong',
          'US-4933': 'pin wrong', 'US-4934': 'pin wrong', 'US-4955': 'pin wrong', 'US-5789': 'pin wrong', 'US-5869': 'pin wrong',
          'US-6197': 'pin wrong', 'US-6202': 'pin wrong', 'US-13039': 'wrong state', 'US-3917': 'land wrong',
          'US-9678': 'same land new ID', 'US-11748': 'sliver', 'US-5782': 'sliver'}


def selftest(path=None):
    fx = json.load(open(path or ROOT / 'tests/fixtures/problem-solver-17.json', encoding='utf-8'))
    bad = 0
    for ref, c in sorted(fx['parks'].items()):
        r = solve(ref, c['row'], c['pin'], c['recs'], c.get('override'), c['state'])
        ok = r['verdict'] == EXPECT[ref]
        bad += not ok
        print(('ok  ' if ok else 'FAIL') + f" {ref} {r['verdict']} ({r['confidence']}): {r['recommend']} | {'; '.join(r['reasons'])}")
    return bad


if __name__ == '__main__':
    if '--selftest' in sys.argv: sys.exit(1 if selftest() else 0)
    try: run()
    except Exception as e:  # noqa: BLE001
        print(f'::warning title=Problem solver::stopped ({type(e).__name__}: {str(e)[:160]}); the key build is not affected')
    sys.exit(0)
