"""Final-pass solver and pile report (24 Nov 2026). Recommendations only: nothing is
written to the key.

Items: (1) every distance is to the HELD record on the saved outline;
(2) a "pin at the land" verdict of KEEP when the pin is inside or next to
the held record (100 m) and the name fits; (3) never hand a park another
POTA park's land; (4) a kind-of-land guard; (5) a part never takes the
whole (needs a layer); (6) trail parks drop the trl copy when the official
trail holds the pin; (7) partial is labelled "partial, more pieces needed";
(8) unresolved parks go on a page-reader re-read list.

Not a rules file (no rules hash moves).
"""
from __future__ import annotations

import json, pathlib, re, sys
from collections import Counter, OrderedDict

import kpc_problem_solver as PS

NEAR_M = 100
NEAR_KM = 0.1
PART_WORDS = ('unit', 'tract', 'access', 'campground', 'headquarters', 'visitorcenter', 'boatlaunch')
KIND_GROUPS = (
    frozenset({'statepark', 'stateparkarea'}),
    frozenset({'stateforest', 'stateforests'}),
    frozenset({'wma', 'wildlifemanagementarea', 'statewildlifearea', 'swa', 'wildlifearea'}),
    frozenset({'wilderness'}),
    frozenset({'wsa', 'wildernessstudyarea'}),
)
BUCKETS = ('KEEP', 'FIX', 'NEEDS LAYER', 'PARTIAL', 'RE-READ')


def name_key(s):
    return re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def words_key(s):
    return re.findall(r'[a-z0-9]+', str(s or '').lower())


def held_id_of(p):
    held = p.get('held') or {}
    if isinstance(held, dict) and (held.get('ids') or []):
        return str(held['ids'][0])
    bk = p.get('bk') or [None]
    return str(bk[0]) if bk and bk[0] is not None else ''


def held_km(rec, pin):
    """Kilometres from the pin to the HELD record on the saved outline. 0 if inside."""
    if rec is None or not pin or len(pin) < 2:
        return None
    try:
        return PS.km(rec, float(pin[0]), float(pin[1]))
    except (TypeError, ValueError):
        return None


def name_fits(park_name, park_type, rec_name):
    """Official-name test on the held record itself (empty string from sure_name_fits = fits)."""
    if not (rec_name or '').strip():
        return False
    return not PS.sure_name_fits(park_name, park_type or '', rec_name)


def kind_group(text):
    """More specific kinds first, so "Wilderness Study Area" is not also Wilderness."""
    w = set(words_key(text))
    k = name_key(text)
    if ('wilderness' in w and 'study' in w) or 'wsa' in w or 'wildernessstudyarea' in k:
        return KIND_GROUPS[4]
    if 'wilderness' in w:
        return KIND_GROUPS[3]
    if any(tok in w for tok in ('wma', 'swa')) or 'wildlifemanagementarea' in k or 'statewildlifearea' in k:
        return KIND_GROUPS[2]
    if 'state' in w and 'forest' in w:
        return KIND_GROUPS[1]
    if 'state' in w and 'park' in w:
        return KIND_GROUPS[0]
    return None


def kind_clash(park_name, park_type, rec_name):
    """True when the park and the record are different kinds of land (state park / forest / WMA; Wilderness / WSA)."""
    a = kind_group(f'{park_name} {park_type or ""}')
    b = kind_group(rec_name or '')
    return bool(a and b and a != b)


def is_part_name(name):
    w = set(words_key(name))
    return any(tok in w for tok in PART_WORDS)


def stem_key(name):
    """Letters of the name with part-words (and a following number) stripped, so a unit can be compared to the whole."""
    out = []
    skip_num = False
    for w in words_key(name):
        if skip_num and w.isdigit():
            skip_num = False
            continue
        skip_num = False
        if w in PART_WORDS:
            skip_num = True
            continue
        out.append(w)
    return ''.join(out)


def part_takes_whole(park_name, rec_name):
    """A part (unit, tract, access, campground) must not take the whole park, or the other way around."""
    if not park_name or not rec_name:
        return False
    pn, rn = is_part_name(park_name), is_part_name(rec_name)
    if pn == rn:
        return False
    sa, sb = stem_key(park_name), stem_key(rec_name)
    return bool(sa and sb and sa == sb)


def other_pota_land(rec_name, park_ref, pota_names):
    """True when the record's name is another POTA park in this state."""
    if not rec_name or not pota_names:
        return False
    key = name_key(rec_name)
    if not key:
        return False
    for ref, nm in pota_names.items():
        if ref == park_ref:
            continue
        if name_key(nm) == key:
            return True
    return False


def is_trail_park(park_name, park_type):
    return 'trail' in words_key(f'{park_name} {park_type or ""}')


def is_trl_id(rid):
    return str(rid or '').lower().startswith('trl') or ':trl' in str(rid or '').lower()


def is_official_trail_rec(rec, rid):
    name = (rec or {}).get('Unit_Nm') or (rec or {}).get('Loc_Nm') or ''
    return 'trail' in words_key(name) and not is_trl_id(rid)


def classify(park_ref, p, pin, recs, solver_row=None, pota_names=None):
    """One park, recommendations only. Returns a dict with bucket, reasons, held_km, held_id."""
    solver_row = solver_row or {}
    pota_names = pota_names or {}
    pn, pt = p.get('n') or solver_row.get('name') or '', p.get('t') or solver_row.get('type') or ''
    hid = held_id_of(p)
    rec = recs.get(hid) or recs.get(str(hid)) if hid else None
    rec_nm = ((rec or {}).get('Unit_Nm') or (rec or {}).get('Loc_Nm') or '') if rec else ''
    d = held_km(rec, pin)
    verd = solver_row.get('verdict') or ''
    reasons = []
    out = {
        'park': park_ref,
        'bucket': None,
        'recommend': '',
        'reasons': reasons,
        'held_id': hid or None,
        'held_km': d,
        'name_fits': False,
        'c_rows_rewritten': False,
    }

    # (3) never hand another POTA park's land — applies to a recommended switch
    def blocked_other(rid, rname):
        return other_pota_land(rname, park_ref, pota_names)

    fits = bool(rec) and name_fits(pn, pt, rec_nm)
    out['name_fits'] = fits
    clash = bool(rec) and kind_clash(pn, pt, rec_nm)
    part = bool(rec) and part_takes_whole(pn, rec_nm)
    pin_at = d is not None and d <= NEAR_KM

    # (5) part never takes the whole (same stem, one side is a unit/tract/access/campground)
    if part:
        reasons.append('a part must not take the whole; needs a layer')
        out['bucket'] = 'NEEDS LAYER'
        out['recommend'] = 'needs a layer (a part must not take the whole)'
        return out

    # (4) kind-of-land guard: not KEEP
    if clash:
        reasons.append('kind-of-land guard: the held record is a different kind of place')

    # (6) trail parks: drop the trl copy when the official trail holds the pin
    if is_trail_park(pn, pt) and rec is not None and pin_at:
        mids = [str(x[0]) for x in (p.get('m') or []) if isinstance(x, list) and x]
        trl = [i for i in mids if is_trl_id(i)]
        official_holds = is_official_trail_rec(rec, hid) or any(
            is_official_trail_rec(recs.get(i) or {}, i) and (held_km(recs.get(i), pin) is not None and held_km(recs.get(i), pin) <= NEAR_KM)
            for i in mids if not is_trl_id(i)
        )
        if official_holds and trl:
            reasons.append('official trail holds the pin; drop the trl copy')
            out['bucket'] = 'FIX'
            out['recommend'] = 'drop the trl copy; keep the official trail'
            return out

    # (2) pin at the land + name fits → KEEP (unless kind clash, other-pota, etc.)
    if fits and pin_at and not clash:
        if blocked_other(hid, rec_nm):
            reasons.append('the held record is another POTA park\'s land; not a KEEP')
        else:
            why = 'pin is inside the held record' if d == 0 else f'pin is {d * 1000:.0f} m from the held record'
            reasons.append(f'pin at the land: {why}; the held name fits')
            out['bucket'] = 'KEEP'
            out['recommend'] = 'KEEP: the pin is at the held land and the name fits'
            return out

    # (7) partial: already joined a piece, more pieces needed (solver sliver / incomplete)
    if verd == 'sliver' or (fits and d is not None and not clash and 'piece' in ' '.join(solver_row.get('reasons') or []).lower()):
        reasons.append('partial, more pieces needed')
        out['bucket'] = 'PARTIAL'
        out['recommend'] = 'partial, more pieces needed'
        return out
    if fits and not pin_at and rec is not None:
        # same name, but not next to the pin — might be a partial cover
        if any('partial' in str(x).lower() or 'piece' in str(x).lower() for x in (solver_row.get('reasons') or [])):
            reasons.append('partial, more pieces needed')
            out['bucket'] = 'PARTIAL'
            out['recommend'] = 'partial, more pieces needed'
            return out

    # FIX when the solver already said land wrong, and the target is not another POTA park
    if verd == 'land wrong':
        recs_rec = solver_row.get('records') or []
        target = None
        for r in recs_rec:
            if isinstance(r, dict) and r.get('id') and str(r.get('id')) != hid:
                if blocked_other(r.get('id'), r.get('name') or ''):
                    reasons.append('would have switched to another POTA park\'s land; not applied')
                    continue
                target = r
                break
        if target:
            reasons.append('solver: land wrong; recommend a different record of this park')
            out['bucket'] = 'FIX'
            out['recommend'] = f"join {target.get('id')} and drop the held {hid}"
            return out
        reasons.append('solver: land wrong')
        out['bucket'] = 'FIX'
        out['recommend'] = 'land wrong'  # IDs only; never copy the solver's named recommend text
        return out

    if verd == 'pin wrong':
        reasons.append('solver: pin wrong; the pin is never moved')
        # still a person / keep-hold situation, not FIX of the land
        out['bucket'] = 'RE-READ'
        out['recommend'] = 'unresolved: pin wrong (the pin is never moved); page-reader re-read'
        return out

    # (8) unresolved → re-read list
    reasons.append('unresolved: send to the page-reader re-read list')
    out['bucket'] = 'RE-READ'
    out['recommend'] = 'unresolved: page-reader re-read'
    return out


def run_final_pass(solver_parks, keys_by_ref, recs_by_state, pins_by_ref, pota_by_state):
    """Classify every solver park. keys_by_ref: park -> (state, key row)."""
    rows = []
    for r in solver_parks:
        pid = r.get('park')
        st, p = keys_by_ref.get(pid) or (None, None)
        if not p:
            continue
        recs = recs_by_state.get(st) or {}
        pin = pins_by_ref.get(pid)
        pota = pota_by_state.get(st) or {}
        rows.append(classify(pid, p, pin, recs, solver_row=r, pota_names=pota))
    counts = Counter(x['bucket'] for x in rows)
    return {
        'about': 'Final-pass solver pile report. Recommendations only: the key was not rewritten. IDs and counts only in public output.',
        'input_count': len(rows),
        'counts': {b: counts.get(b, 0) for b in BUCKETS},
        'rows': rows,
    }


def ids_only_report(result):
    """Public report: IDs, buckets, counts; no display names."""
    by = OrderedDict((b, []) for b in BUCKETS)
    for r in result.get('rows') or []:
        by.setdefault(r['bucket'], []).append(r['park'])
    return {
        'about': result.get('about'),
        'input_count': result.get('input_count'),
        'counts': result.get('counts'),
        'parks': {b: sorted(v) for b, v in by.items()},
        'c_rows_rewritten': False,
    }


def reread_list(result):
    ids = sorted(r['park'] for r in result.get('rows') or [] if r.get('bucket') == 'RE-READ')
    return {
        'about': 'Unresolved parks for the page-reader re-read list (IDs only). Recommendations only.',
        'count': len(ids),
        'parks': ids,
    }


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='Final-pass solver pile report. Recommendations only; the key is not rewritten.')
    ap.add_argument('--solver', required=True, help='problem-solver.json from a local run')
    ap.add_argument('--out', required=True, help='directory for the IDs-only pile report and the re-read list')
    args = argparse.Namespace() if argv is ... else None
    # This CLI is a thin wrapper; the local driver fills keys and recs. Kept for tests that call classify() directly.
    print('Use classify() / run_final_pass() from a local driver; this module does not load keys by itself.', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
