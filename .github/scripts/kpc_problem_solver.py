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
Standing candidate check (check_candidate): pin within 0.5 km, acreage within about 15% of an official figure
when we have one, whole park vs a piece (same-name parts on the same layer are merged first), land type and agency
fit, and a record already rejected stays out unless new evidence appears. official_website reads the park's official
page (from POTA / the key) with robots.txt, a crawl delay, a cache, and the never-touch host list; a name plus
acreage that agree with the polygon push toward YES, a page that describes a different place or size toward NO.
A dead or missing site is noted and does not block. Verdicts from the check: YES (auto, signed by this bot rule as
a recommendation only), NO (with why), or ONLY-PERSON. This file still writes no override.

  --check <csv-or-json>   run the standing check (optional --fetch-site to read official pages)
  --inbox [--retry] [--offline]   check the research files in data/research-inbox/, only those parks;
               --retry re-checks data/research-inbox/needs-another-look.json; see docs/research-input-format.md
  --selftest              the 17 Research Bot calls of Nov 7

Never fails the build: exit 0 (the selftest exits 1 on a wrong verdict)."""
import glob, gzip, json, math, os, pathlib, re, sys, unicodedata, urllib.parse, urllib.request

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

# POTA often stores the WDPA site ID as a Protected Planet (or DOPA Explorer) URL on the park website.
WDPA_URL_RE = re.compile(
    r'protectedplanet\.net/([0-9]+)|dopa-explorer\.jrc\.ec\.europa\.eu/wdpa/([0-9]+)', re.I)
WDPA_ID_KEYS = ('wdpaid', 'wdpa_id', 'wdpa_pid', 'site_id', 'site_pid')
WDPA_LAYER_MARKS = ('unep-wcmc', 'protectedplanet', 'world_database_of_protected_areas', 'wdpa_leads', 'wdpa_v0')


def pota_wdpa_id(park):
    """The WDPA site ID POTA already stores (explicit field, or the number in a Protected Planet URL)."""
    park = park or {}
    for k in ('wdpa_id', 'wdpaid', 'site_id', 'pota_wdpa_id'):
        v = park.get(k)
        if v not in (None, '', 0, '0'):
            try:
                return int(str(v).strip())
            except ValueError:
                pass
    web = str(park.get('website') or park.get('url') or '')
    m = WDPA_URL_RE.search(web)
    if m:
        return int(m.group(1) or m.group(2))
    return None


def rec_wdpa_ids(rec):
    """WDPA site IDs carried on a record (official layers often use WDPAID / WDPA_PID; WDPA uses site_id)."""
    ids = set()
    blobs = [rec]
    attrs = rec.get('attrs') or rec.get('properties') or rec.get('a')
    if isinstance(attrs, dict):
        blobs.append(attrs)
    for blob in blobs:
        if not isinstance(blob, dict):
            continue
        for k, v in blob.items():
            if v in (None, ''):
                continue
            kl = re.sub(r'[^a-z0-9]', '', str(k).lower())
            if kl in ('wdpaid', 'wdpaidid', 'wdpapid', 'siteid', 'sitepid') or kl.endswith('wdpaid'):
                try:
                    ids.add(int(str(v).strip()))
                except ValueError:
                    pass
    ids.discard(0)
    return ids


def is_wdpa_rec(rec):
    layer = str(rec.get('layer_url') or rec.get('layer') or rec.get('source') or rec.get('gsrc') or '')
    return any(s in layer.lower() for s in WDPA_LAYER_MARKS)

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



# ---- standing candidate check (one function + one official-website function)

SURE_KM = 0.5
ACRE_TOL = 0.15
PIECE_RX = re.compile(
    r'\b(north|south|east|west|upper|lower|unit|tract|zone|addition|type [ab]|management [ab])\b|'
    r'\((north|south|east|west)\)', re.I)
# land-type tokens that should not be mixed
TYPE_RX = {
    'hatchery': r'\bhatchery\b',
    'conservation': r'conservation area|nature reserve|nature preserve',
    'beach': r'\bbeach\b',
    'aquatic': r'aquatic reserve|fish habitat',
    'river': r'wild (and|&) scenic|\bnational wild\b',
    'wildlife': r'wildlife (area|management|complex|demonstration)',
    'dam': r'\bdam\b',
    'airstrip': r'\bairstrip\b|\bairport\b',
    'reservoir': r'\breservoir\b',
    'lighthouse': r'\blighthouse\b',
    'fortress': r'\bfortress\b',
}
TYPE_CLASH = {
    frozenset(('hatchery', 'conservation')),
    frozenset(('beach', 'aquatic')),
    frozenset(('beach', 'river')),
    frozenset(('wildlife', 'river')),
    frozenset(('airstrip', 'reservoir')),
    frozenset(('lighthouse', 'fortress')),
}
NEVER_HOST = (
    'ncnhde.natureserve.org',
    'apps.fs.usda.gov',
)
NEVER_SUB = ('33TOOklri9xpic7U',)
HOLD_HOST = ('services.arcgis.com', 'services1.arcgis.com')  # saved copies only; no live page fetch
ACRE_RX = re.compile(
    r'(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+)\s*(acres?|hectares?|\bha\b|km[²2]|sq(?:uare)?\s*km)',
    re.I)
COORD_RX = re.compile(r'(?<!\d)([+-]?\d{1,2}\.\d{3,7})\s*[,/ ]\s*([+-]?\d{1,3}\.\d{3,7})')
MAP_RX = re.compile(r'\b(boundary|boundaries|official map|park map|site map|\.pdf|geospatial|gis|shapefile|kml|kmz|geojson)\b', re.I)


def _types(s):
    t = str(s or '').lower()
    return {k for k, rx in TYPE_RX.items() if re.search(rx, t)}


def _to_acres(n, unit):
    u = unit.lower().replace('²', '2')
    if u.startswith('acre'): return n
    if u in ('hectare', 'hectares', 'ha'): return n * 2.4710538147
    if 'km' in u: return n * 247.10538147
    return n


def rec_acres(rec):
    """Acres from the geometry, else a layer acre/hectare attribute."""
    if rec.get('acres') is not None:
        try: return float(rec['acres'])
        except (TypeError, ValueError): pass
    if rec.get('_r') or rec.get('rings'):
        r = dict(rec)
        if rec.get('rings') and not rec.get('_r'): r['_r'] = rec['rings']
        a = acres(r)
        if a: return a
    attrs = rec.get('attrs') or rec.get('a') or {}
    for k, v in attrs.items():
        lk = str(k).lower()
        if not any(s in lk for s in ('acre', 'hect', 'gaz_area', 'gis_area', 'o_area', 'rep_area')): continue
        try: n = float(str(v).replace(',', ''))
        except (TypeError, ValueError): continue
        if n <= 0: continue
        if 'hect' in lk or lk.endswith('_ha') or 'o_area_ha' in lk or lk in ('gaz_area', 'gis_area') and n < 20000:
            # gaz_area / gis_area on AU layers are hectares when the number is in that range
            if 'hect' in lk or lk.endswith('_ha') or 'o_area_ha' in lk or lk in ('gaz_area', 'gis_area'):
                return n * 2.4710538147
        if 'acre' in lk: return n
    return None


def _merge_parts(park_name, recs):
    """If the named record looks like a piece, merge same-name parts from the same layer and recheck."""
    recs = [r for r in (recs or []) if r]
    if not recs: return recs, False
    main = recs[0]
    name = str(main.get('name') or main.get('record_name') or '')
    if not PIECE_RX.search(name): return recs, False
    # a word that marks a piece and is not also in the park name
    if not any(m and m.group(0).lower() not in park_name.lower() for m in [PIECE_RX.search(name)]):
        return recs, False
    layer = (main.get('layer_url') or main.get('layer') or '').rstrip('/')
    core_p = core(park_name) | core(name)
    extra = []
    for r in recs[1:]:
        if (r.get('layer_url') or r.get('layer') or '').rstrip('/') != layer and layer:
            continue
        if not (core(r.get('name') or r.get('record_name')) & core_p):
            continue
        extra.append(r)
    if not extra: return recs, True  # still a piece, nothing to merge
    rings = []
    for r in [main] + extra:
        rings.extend(r.get('_r') or r.get('rings') or [])
    merged = dict(main)
    merged['_r'] = rings
    merged['rings'] = rings
    merged['name'] = (main.get('name') or '') + ' + ' + ' + '.join(str(r.get('name') or r.get('id') or '') for r in extra)
    merged['merged_from'] = [main.get('id')] + [r.get('id') for r in extra]
    ac = acres({'_r': rings}) if rings else None
    if ac: merged['acres'] = ac
    return [merged] + [r for r in recs if r is not main and r not in extra], True


def official_website(park, rec=None, pin=None, rec_acres_v=None, fetch=False, html=None, url=None):
    """Read the park's official website (one function). URL from the park row, the key, or api.pota.app.
    robots.txt, crawl delay, a cache, and the never-touch host list are obeyed. A dead or missing
    site is noted and does not block. Map/PDF links are returned as leads."""
    out = {'url': '', 'status': 'none', 'note': '', 'name_fit': None, 'acres_fit': None,
           'location_fit': None, 'page_acres': None, 'map_leads': [], 'push': None, 'why': ''}
    url = url or (park or {}).get('website') or (park or {}).get('official_url') or ''
    if not url and fetch:
        url = _pota_website((park or {}).get('ref') or (park or {}).get('pota_ref')) or ''
    out['url'] = url
    if not url:
        out['status'] = 'missing'; out['note'] = 'no official website on file'; out['why'] = out['note']
        return out
    if html is None and not fetch:
        out['status'] = 'not-fetched'; out['note'] = 'website on file, not fetched this run'; out['why'] = out['note']
        return out
    host = urllib.parse.urlparse(url).netloc.lower()
    path = urllib.parse.urlparse(url).path or ''
    if any(h == host or host.endswith('.' + h) for h in NEVER_HOST) or any(s in url for s in NEVER_SUB):
        out['status'] = 'blocked'; out['note'] = 'never-touch host; page not fetched'; out['why'] = out['note']
        return out
    if any(host == h or host.endswith('.' + h) for h in HOLD_HOST):
        out['status'] = 'blocked'; out['note'] = 'saved-copy host; no live page fetch'; out['why'] = out['note']
        return out
    if html is None:
        html, err = _fetch_site(url)
        if err:
            out['status'] = 'dead' if err != 'robots' else 'robots'
            out['note'] = err; out['why'] = f'official page not readable ({err}); does not block'
            return out
    text = html
    try:
        sys.path.insert(0, str(pathlib.Path(os.environ.get('KPCDATA') or ROOT.parent / 'KPC-Data') / '.github/scripts'))
        import kpc_manners as _KM  # noqa: E402
        if '<html' in html[:400].lower() or '<!doctype' in html[:400].lower():
            text = _KM.page_text(html)
            out['map_leads'] = [u for u, lab in _KM.links_in(html, url) if MAP_RX.search(u + ' ' + lab)][:12]
        else:
            out['map_leads'] = [u for u, lab in _KM.links_in(html, url) if MAP_RX.search(u + ' ' + lab)][:12]
    except Exception:
        text = re.sub(r'<[^>]+>', ' ', html)
        out['map_leads'] = [urllib.parse.urljoin(url, m) for m in re.findall(r'href=["\']([^"\']+)["\']', html, re.I)
                            if MAP_RX.search(m)][:12]
    park_name = str((park or {}).get('name') or (park or {}).get('park_name') or '')
    rec_name = str((rec or {}).get('name') or (rec or {}).get('record_name') or '')
    rec_local = str((rec or {}).get('name_local') or (rec or {}).get('name_ja') or '')
    # name tokens keep letters in every script (Japanese / Arabic pages otherwise look empty)
    def _tok(s):
        s = unicodedata.normalize('NFKC', str(s or '')).lower().replace('-', ' ')
        s = re.sub(r'[^\w]+', ' ', s, flags=re.UNICODE)
        return {x for x in s.split() if x not in GENERIC and len(x) > 1}
    path = urllib.parse.urlparse(url or '').path.replace('/', ' ').replace('_', ' ').replace('.html', ' ').replace('.php', ' ')
    title = (text or '')[:20000] + ' ' + ' '.join(w for w in path.replace('-', ' ').split() if len(w) > 3)
    pc, rc, lc, tc = _tok(park_name), _tok(rec_name), _tok(rec_local), _tok(title)
    name_ok = bool(tc and ((pc and (tc & pc)) or (rc and (tc & rc)) or (lc and (tc & lc))))
    out['name_fit'] = name_ok
    # acreage on the page
    found = []
    for m in ACRE_RX.finditer(text[:20000]):
        try: n = float(m.group(1).replace(',', ''))
        except ValueError: continue
        found.append(_to_acres(n, m.group(2)))
    # pick the figure closest to the record acres when we have one, else the first reasonable one
    page_ac = None
    if found:
        if rec_acres_v:
            page_ac = min(found, key=lambda a: abs(a - rec_acres_v))
        else:
            page_ac = found[0]
    out['page_acres'] = page_ac
    if page_ac and rec_acres_v and rec_acres_v > 0:
        out['acres_fit'] = abs(page_ac - rec_acres_v) / rec_acres_v <= ACRE_TOL
    # coordinates on the page vs the pin
    if pin and pin[0] is not None:
        for m in COORD_RX.finditer(text[:20000]):
            a, b = float(m.group(1)), float(m.group(2))
            # lat,lon or lon,lat
            pairs = [(a, b)] if abs(a) <= 90 else []
            if abs(b) <= 90: pairs.append((b, a))
            for la, lo in pairs:
                k = math.cos(math.radians(pin[0]))
                dkm = math.hypot((lo - pin[1]) * 111.32 * k, (la - pin[0]) * 110.57)
                if dkm <= 10:
                    out['location_fit'] = True
                    break
            if out['location_fit']:
                break
        if out['location_fit'] is None and COORD_RX.search(text[:20000]):
            out['location_fit'] = False
    why = []
    if name_ok: why.append('official page name fits')
    elif text: why.append('official page name does not clearly fit')
    if out['acres_fit'] is True: why.append(f'page acres {page_ac:,.0f} agree with the polygon')
    elif out['acres_fit'] is False: why.append(f'page acres {page_ac:,.0f} differ from the polygon ({rec_acres_v:,.0f})')
    if out['location_fit'] is True: why.append('page coordinates fit the pin')
    elif out['location_fit'] is False: why.append('page coordinates do not fit the pin')
    if out['map_leads']: why.append(f'{len(out["map_leads"])} map or PDF lead(s) on the page')
    if name_ok and out['acres_fit'] is True:
        out['push'] = 'yes'
    elif (out['acres_fit'] is False and rec_acres_v and page_ac and
          (page_ac / rec_acres_v > 3 or rec_acres_v / page_ac > 3)) or out['location_fit'] is False:
        out['push'] = 'no'
    elif (text and not name_ok and pc and tc and not (tc & pc) and not (lc and (tc & lc))
          and any(all(ord(c) < 128 for c in w) for w in tc)
          and any(all(ord(c) < 128 for c in w) for w in (pc | rc))):
        # a Latin page name that shares no tokens is a different place; a page in another
        # script with no Latin name overlap is unclear, not a block
        out['push'] = 'no'
    out['status'] = 'ok'
    out['why'] = '; '.join(why) or 'official page read'
    out['note'] = out['why']
    return out


def _pota_website(ref):
    """Website field from api.pota.app park info (allowed). Cached. Never used to move a pin."""
    if not ref: return ''
    cache = pathlib.Path(os.environ.get('POTA_WEB_CACHE') or ROOT / 'cache/official-pages')
    cache.mkdir(parents=True, exist_ok=True)
    f = cache / f'pota-{ref}.json'
    try:
        if f.exists():
            d = json.loads(f.read_text(encoding='utf-8'))
            return d.get('website') or d.get('parkinfoWebsite') or ''
    except Exception:
        pass
    url = 'https://api.pota.app/park/' + urllib.parse.quote(str(ref))
    # robots + manners if available
    body, err = _fetch_site(url)
    if err or not body: return ''
    try:
        d = json.loads(body)
    except Exception:
        return ''
    try: f.write_text(json.dumps(d), encoding='utf-8')
    except Exception: pass
    return d.get('website') or d.get('parkinfoWebsite') or ''


def _fetch_site(url):
    """Polite fetch: manners when present, else a robots.txt check + 2 s gap. Returns (text, err)."""
    kpdata = pathlib.Path(os.environ.get('KPCDATA') or ROOT.parent / 'KPC-Data')
    sys.path.insert(0, str(kpdata / '.github/scripts'))
    os.environ.setdefault('KPC_MANNERS_CACHE', str(ROOT / 'cache/official-pages'))
    os.environ.setdefault('KPC_MANNERS_CACHE_ALL', '1')
    try:
        import kpc_manners as KM  # noqa: E402
        M = KM.Manners('official park page check')
        st, _headers, body, _final = M.get(url)
        if st == 200 and body:
            if isinstance(body, bytes):
                if body[:5] == b'%PDF-':
                    return KM.pdf_text(body, pages=3), None
                return body.decode('utf-8', 'replace'), None
            return str(body), None
        if KM.robots_block(st) or st == 'robots':
            return None, 'robots'
        return None, f'http {st}'
    except Exception as e:  # noqa: BLE001
        # last-resort: do not fetch if we cannot check robots
        return None, f'not fetched ({type(e).__name__})'


def check_candidate(park, recs, official_acres=None, earlier_no=None, fetch_site=False, page_html=None):
    """Standing check for every candidate. park = {ref, name, pin=(lat,lon), website?, kind?, agency?}.
    recs = list of records {id, name, rings/_r, acres?, layer_url?, attrs?, agency?, type?}.
    Official acres may also come from a record attribute. YES is a bot-rule recommendation only
    (this function writes no override)."""
    park = park or {}
    recs = list(recs or [])
    ref = park.get('ref') or park.get('pota_ref') or ''
    name = park.get('name') or park.get('park_name') or ''
    pin = park.get('pin')
    why = []
    recs, was_piece = _merge_parts(name, recs)
    park_wid = pota_wdpa_id(park)
    match_how = None
    if park_wid is not None and recs:
        official_id, wdpa_id_hits = [], []
        for r in recs:
            if park_wid in rec_wdpa_ids(r):
                (official_id if not is_wdpa_rec(r) else wdpa_id_hits).append(r)
        if official_id:
            recs = official_id + [r for r in recs if r not in official_id]
            match_how = 'official_wdpa_id'
            why.append(f'official record carries the same WDPA ID ({park_wid}) as POTA')
        elif wdpa_id_hits:
            recs = wdpa_id_hits + [r for r in recs if r not in wdpa_id_hits]
            match_how = 'pota_wdpa_id'
            why.append(f'matched by the WDPA site ID POTA already stores ({park_wid})')
    rec = recs[0] if recs else None
    if not rec:
        return {'ref': ref, 'verdict': 'ONLY-PERSON', 'signed_by': None, 'why': 'no candidate record', 'merged': False}
    rid = str(rec.get('id') or rec.get('record_id') or '')
    rname = str(rec.get('name') or rec.get('record_name') or '')
    earlier_no = {str(x) for x in (earlier_no or []) if x is not None}
    # website is fetched later; earlier-NO is decided after the site can count as new evidence

    # pin
    dkm = None
    rings_ = rec.get('_r') or rec.get('rings') or []
    if pin and rings_:
        dkm = KM.km_to(pin[0], pin[1], {'rings': rings_})
    elif pin and rec.get('pt'):
        k = math.cos(math.radians(pin[0]))
        dkm = round(math.hypot((rec['pt'][0] - pin[1]) * 111.32 * k, (rec['pt'][1] - pin[0]) * 110.57), 3)
    if pin and dkm is None and not rec.get('pt') and not rings_:
        why.append('no shape or official point to test the pin against')
    elif pin and dkm is not None and dkm > SURE_KM:
        return {'ref': ref, 'verdict': 'NO', 'signed_by': None,
                'why': f'pin is {dkm} km from the record (over {SURE_KM} km)', 'pin_km': dkm, 'record_id': rid, 'merged': bool(rec.get('merged_from'))}
    elif pin and dkm == 0:
        why.append('pin is inside the record')
    elif pin and dkm is not None:
        why.append(f'pin is {dkm} km from the record (within {SURE_KM} km)')

    # acres
    rac = rec_acres(rec)
    off = official_acres
    if off is None:
        off = park.get('official_acres')
    acres_ok = None
    if off and rac and off > 0:
        acres_ok = abs(rac - off) / off <= ACRE_TOL
        if acres_ok:
            why.append(f'record acres {rac:,.0f} agree with official {off:,.0f} (within 15%)')
        else:
            why.append(f'record acres {rac:,.0f} vs official {off:,.0f} (off by more than 15%)')

    # whole vs piece
    piece = was_piece and not rec.get('merged_from')
    if rec.get('merged_from'):
        why.append('same-name parts on the same official layer were merged')
        if acres_ok:
            piece = False
        elif off and rac and acres_ok is False:
            piece = True
            why.append('even after the merge, the acreage still does not cover the official park')
    elif was_piece or (PIECE_RX.search(rname) and not any(w in name.lower() for w in re.findall(r'(north|south|east|west|unit|tract|zone)', rname.lower()))):
        piece = True
        why.append(f'record looks like a piece of the park ({rname})')

    # land type / agency
    pt, rt = _types(name + ' ' + str(park.get('kind') or '')), _types(rname + ' ' + str(rec.get('type') or rec.get('kind') or ''))
    clash = None
    for pair in TYPE_CLASH:
        if pair <= (pt | rt) and pt & pair and rt & pair and not (pt & rt & pair):
            # both sides of the pair appear, but not the same token on both
            if (pt & pair) != (rt & pair):
                clash = tuple(sorted(pair))
                break
    # simpler: types on park vs record share a clash pair and do not share that token
    if clash is None and pt and rt and not (pt & rt):
        for pair in TYPE_CLASH:
            if (pt & pair) and (rt & pair) and (pt & pair) != (rt & pair):
                clash = tuple(sorted(pair)); break
    if clash:
        why.append(f'land type does not fit ({clash[0]} vs {clash[1]})')
    pagency = str(park.get('agency') or park.get('kind') or '').lower()
    ragency = str(rec.get('agency') or rec.get('owner') or rec.get('mang') or '').lower()
    agency_clash = False
    if 'blm' in name.lower() and ragency and 'blm' not in ragency and any(s in ragency for s in ('fish', 'idfg', 'wdfw', 'state')):
        agency_clash = True
        why.append('agency does not fit (park is BLM, record is not)')

    # official website (does not block when dead or missing)
    site = official_website(park, rec, pin, rec_acres_v=rac, fetch=fetch_site, html=page_html, url=park.get('website'))
    if site.get('why'):
        why.append(site['why'])

    if rid and rid in earlier_no:
        # new evidence: a merge that now covers official acres, or a website that agrees
        new_ev = bool(rec.get('merged_from')) or site.get('push') == 'yes'
        if not new_ev:
            return {'ref': ref, 'name': name, 'verdict': 'NO', 'signed_by': None,
                    'why': f'record {rid} was already rejected and no new evidence is on hand' + ('; ' + '; '.join(why) if why else ''),
                    'record_id': rid, 'record_name': rname, 'record_acres': rec_acres(rec),
                    'merged': bool(rec.get('merged_from')), 'site': site}

    # verdict
    if clash or agency_clash:
        verd = 'NO'
    elif piece and not rec.get('merged_from'):
        verd = 'ONLY-PERSON' if acres_ok is not False else 'NO'
    elif acres_ok is False:
        verd = 'ONLY-PERSON' if site.get('push') == 'yes' else 'NO'
    elif dkm is None and not pin:
        verd = 'ONLY-PERSON'
        why.append('no POTA pin, so a person compares the outline')
    elif site.get('push') == 'no' and not (acres_ok and (dkm == 0 or (dkm is not None and dkm <= SURE_KM))):
        verd = 'NO'
    elif site.get('push') == 'no' and acres_ok is False:
        verd = 'NO'
    elif (dkm is not None and dkm <= SURE_KM) and (acres_ok is True or (off is None and not piece and not clash)):
        # official acres missing: only YES when type fits, not a piece, pin ok, and the site does not push NO
        if off is None and site.get('push') != 'yes':
            verd = 'ONLY-PERSON'
            why.append('no official acreage to compare, so a person checks')
        else:
            verd = 'YES'
    else:
        verd = 'ONLY-PERSON'

    # website can upgrade or downgrade when the rest was close
    # a page that matches the polygon cannot override a known official-acre miss, and WDPA is never official
    layer = str(rec.get('layer_url') or rec.get('layer') or rec.get('source') or '')
    wdpa = is_wdpa_rec(rec)
    if wdpa:
        why.append('WDPA / Protected Planet is never official')
        if verd == 'YES':
            verd = 'ONLY-PERSON'
    if (verd == 'ONLY-PERSON' and site.get('push') == 'yes' and dkm is not None and dkm <= SURE_KM
            and not clash and not piece and acres_ok is not False and not wdpa):
        verd = 'YES'
        why.append('official page name and acreage agree; bot rule can take this')
    if verd == 'YES' and site.get('push') == 'no':
        verd = 'NO'
        why.append('official page describes a different place or size')

    signed = 'candidate-check rule, Nov 9 2026' if verd == 'YES' else None
    out = {'ref': ref, 'name': name, 'verdict': verd, 'signed_by': signed, 'why': '; '.join(why) or verd,
            'pin_km': dkm, 'record_id': rid, 'record_name': rname, 'record_acres': rac, 'official_acres': off,
            'merged': bool(rec.get('merged_from')), 'piece': bool(piece), 'site': site,
            'wdpa_id': park_wid, 'match_how': match_how}
    return out


def run_check(path, fetch_site=False, out_dir=None):
    """Run check_candidate on a CSV or JSON of candidates (the LOOK list or a research-inbox results file)."""
    path = pathlib.Path(path)
    rows = []
    if path.suffix.lower() == '.json':
        data = json.loads(path.read_text(encoding='utf-8'))
        raw = data.get('rows') or data.get('parks') or (data if isinstance(data, list) else [])
        if isinstance(raw, dict):
            raw = [{'ref': k, **(v if isinstance(v, dict) else {'v': v})} for k, v in raw.items()]
        for r in raw:
            recs = r.get('records') or r.get('recs')
            if recs:
                rec_list = recs
            else:
                rec_list = [{'id': r.get('record_id') or r.get('file_record_id'), 'name': r.get('record_name'),
                   'layer_url': r.get('layer_url'), 'acres': r.get('record_acres') or r.get('computed_acres'),
                   'agency': r.get('agency'), 'type': r.get('record_type'),
                   'rings': r.get('rings'), '_r': r.get('_r'), 'pt': r.get('official_pt') or r.get('pt')}]
            park = {'ref': r.get('ref') or r.get('pota_ref'), 'name': r.get('name') or r.get('park_name'),
                    'pin': r.get('pin'), 'website': r.get('website'), 'kind': r.get('pota_kind') or r.get('kind'),
                    'official_acres': r.get('official_acres')}
            earlier = r.get('earlier_no') or r.get('rejected_ids') or []
            if isinstance(earlier, dict): earlier = [earlier.get('id')] if earlier.get('id') else []
            rows.append((park, rec_list, earlier, r))
    else:
        import csv
        with path.open(encoding='utf-8', newline='') as f:
            for r in csv.DictReader(f):
                rec = {'id': r.get('record_id'), 'name': r.get('record_name'),
                       'acres': r.get('record_acres'), 'agency': r.get('agency')}
                # official acres may be a sentence; try first number
                off = None
                m = re.search(r'([\d,.]+)', r.get('official_acres') or '')
                rec_ac = None
                m2 = re.search(r'([\d,.]+)', str(r.get('record_acres') or ''))
                try:
                    if m2: rec['acres'] = float(m2.group(1).replace(',', ''))
                    if m: off = float(m.group(1).replace(',', ''))
                except ValueError: pass
                # unit in official text: ha vs acres
                ot = (r.get('official_acres') or '').lower()
                if off and (' ha' in ot or 'hectare' in ot) and 'acre' not in ot.split('ha')[0][-12:]:
                    off = off * 2.4710538147
                pin = r.get('pin')
                if isinstance(pin, str) and pin.startswith('['):
                    try: pin = json.loads(pin)
                    except Exception: pin = None
                park = {'ref': r.get('ref'), 'name': r.get('name'), 'pin': pin, 'website': r.get('website'),
                        'official_acres': off, 'kind': r.get('pota_kind')}
                earlier = [x for x in re.findall(r'\d+', r.get('earlier_no') or '')]
                rows.append((park, [rec], earlier, r))
    out = []
    for park, recs, earlier, raw in rows:
        # skip empty refs
        if not park.get('ref'): continue
        out.append(check_candidate(park, recs, official_acres=park.get('official_acres'),
                                   earlier_no=earlier, fetch_site=fetch_site))
    n = {}
    for x in out: n[x['verdict']] = n.get(x['verdict'], 0) + 1
    dest = pathlib.Path(out_dir or path.with_name(path.stem + '-solver-check'))
    dest.parent.mkdir(parents=True, exist_ok=True)
    json.dump({'about': 'standing candidate check (recommendations only; no override written)',
               'counts': n, 'parks': out}, open(str(dest) + '.json', 'w', encoding='utf-8'), indent=1)
    lines = [f"# Candidate check: {path.name}", '',
             ', '.join(f'**{v}** {k}' for k, v in sorted(n.items())) or 'No rows.', '']
    for x in out:
        lines.append(f"- **{x.get('ref')}** {x.get('name') or ''}: **{x['verdict']}** — {x['why']}")
    open(str(dest) + '.md', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print(f'candidate check: {len(out)} parks; ' + ', '.join(f'{k} {v}' for k, v in sorted(n.items())))
    print('wrote', str(dest) + '.json', 'and', str(dest) + '.md')
    return out


if __name__ == '__main__':
    if '--selftest' in sys.argv: sys.exit(1 if selftest() else 0)
    if '--check' in sys.argv:
        i = sys.argv.index('--check')
        src = sys.argv[i + 1] if i + 1 < len(sys.argv) else ''
        if not src:
            print('usage: kpc_problem_solver.py --check <csv-or-json> [--fetch-site]'); sys.exit(2)
        fetch = '--fetch-site' in sys.argv
        run_check(src, fetch_site=fetch); sys.exit(0)
    if '--inbox' in sys.argv:   # research files in data/research-inbox/, just those parks (+ --retry)
        import kpc_research_inbox as RI  # noqa: E402
        _fs = sorted(f for f in glob.glob(str(ROOT / 'data/research-inbox/*.csv')) + glob.glob(str(ROOT / 'data/research-inbox/*.json')) if not f.endswith('needs-another-look.json'))
        try: RI.run(_fs, root=ROOT, offline='--offline' in sys.argv, retry='--retry' in sys.argv)
        except Exception as e:  # noqa: BLE001
            print(f'::warning title=Research inbox::stopped ({type(e).__name__}: {str(e)[:160]}); no key is affected')
        sys.exit(0)
    try: run()
    except Exception as e:  # noqa: BLE001
        print(f'::warning title=Problem solver::stopped ({type(e).__name__}: {str(e)[:160]}); the key build is not affected')
    sys.exit(0)
