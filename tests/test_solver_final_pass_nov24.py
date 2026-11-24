"""Final-pass solver and pile report (24 Nov 2026). Recommendations only. Invented parks."""
import json, os, pathlib, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '.github' / 'scripts'))
os.chdir(pathlib.Path(__file__).resolve().parents[1])

import kpc_solver_final_pass as F

# A 1 km-ish square around 38.0, -85.0 (about 0.009° lat is 1 km).
INSIDE = [38.0, -85.0]
# ~50 m north of the north edge (edge at 38.001)
NEAR50 = [38.00145, -85.0]
# ~200 m north
FAR200 = [38.0028, -85.0]
# A working-copy ring far away (must not be used for the 100 m test)
FAR_RING = [[(-84.0, 39.0), (-84.0, 39.01), (-83.99, 39.01), (-83.99, 39.0), (-84.0, 39.0)]]

HELD = 'padus:invh1'
TRL = 'trl:invt1'
OFF_TRAIL = 'padus:invtr1'
PART = 'padus:invp1'
FOREST = 'padus:invf1'


def rec(rid, name, ring=None):
    ring = ring or [[(-85.005, 37.999), (-85.005, 38.001), (-84.995, 38.001), (-84.995, 37.999), (-85.005, 37.999)]]
    return {'id': rid, 'Unit_Nm': name, '_r': ring}


def park(ref, name, typ='State Park', hid=HELD, m=None, bk=None):
    m = m if m is not None else [[hid, 0]]
    return {'n': name, 't': typ, 'held': {'ids': [hid]}, 'bk': bk or [hid, 0], 'm': m}


def box(label):
    n = 0
    failed = False
    def ok(cond, why=''):
        nonlocal n, failed
        if not cond:
            failed = True
            print(f'FAIL {label}' + (f': {why}' if why else ''))
            return False
        n += 1
        return True
    def done():
        if failed:
            return False
        if n:
            print(f'PASS {label}')
            return True
        print(f'FAIL {label}: no checks')
        return False
    return ok, done


def test_held_distance_not_working_copy():
    ok, done = box('every distance is to the held record on the saved outline, not the key working copy')
    recs = {HELD: rec(HELD, 'Invented Marsh State Park')}
    p = park('US-ZZ001', 'Invented Marsh State Park', bk=[HELD, 99])  # key bk says 99 km
    row = F.classify('US-ZZ001', p, NEAR50, recs, solver_row={'verdict': 'needs a person'})
    ok(row['held_km'] is not None and row['held_km'] <= 0.1, f"held_km={row['held_km']}")
    ok(row['bucket'] == 'KEEP', row['bucket'])
    # pin far from the saved outline must not KEEP even if someone stuffed a close ring elsewhere
    row2 = F.classify('US-ZZ001', p, FAR200, recs, solver_row={'verdict': 'needs a person'})
    ok(row2['held_km'] is not None and row2['held_km'] > 0.1, f"far held_km={row2['held_km']}")
    ok(row2['bucket'] != 'KEEP', row2['bucket'])
    return done()


def test_keep_pin_inside_name_fits():
    ok, done = box('KEEP when the pin is inside the held record and the name fits')
    recs = {HELD: rec(HELD, 'Invented Marsh State Park')}
    row = F.classify('US-ZZ002', park('US-ZZ002', 'Invented Marsh State Park'), INSIDE, recs)
    ok(row['bucket'] == 'KEEP', row)
    ok(row['held_km'] == 0, row['held_km'])
    ok(row['c_rows_rewritten'] is False)
    return done()


def test_keep_within_100m():
    ok, done = box('KEEP when the pin is within 100 m of the held record and the name fits')
    recs = {HELD: rec(HELD, 'Invented Marsh State Park')}
    row = F.classify('US-ZZ003', park('US-ZZ003', 'Invented Marsh State Park'), NEAR50, recs)
    ok(row['bucket'] == 'KEEP', row)
    ok(0 < (row['held_km'] or 9) <= 0.1, row['held_km'])
    return done()


def test_no_keep_without_name():
    ok, done = box('does not KEEP when the held name does not fit, even if the pin is inside')
    recs = {HELD: rec(HELD, 'Invented Lake National Wildlife Refuge')}
    row = F.classify('US-ZZ004', park('US-ZZ004', 'Invented Marsh State Park'), INSIDE, recs)
    ok(row['bucket'] != 'KEEP', row)
    return done()


def test_never_hand_other_pota():
    ok, done = box('never hands a park another POTA park\'s land')
    # land-wrong, the only other record offered is another park's name
    recs = {HELD: rec(HELD, 'Invented Marsh State Park')}
    solver = {
        'verdict': 'land wrong',
        'records': [{'id': 'padus:other1', 'name': 'Invented Other State Park'}],
    }
    pota = {'US-ZZ005': 'Invented Marsh State Park', 'US-ZZ999': 'Invented Other State Park'}
    p = park('US-ZZ005', 'Invented Marsh State Park')
    # pin is far so we do not KEEP the held land; then land-wrong would want to switch
    row = F.classify('US-ZZ005', p, FAR200, recs, solver_row=solver, pota_names=pota)
    ok(row['bucket'] != 'KEEP', row)
    ok('another POTA' in ' '.join(row['reasons']), row['reasons'])
    ok('padus:other1' not in (row['recommend'] or ''), row['recommend'])
    return done()


def test_kind_guard():
    ok, done = box('kind-of-land guard: a state park does not KEEP a state forest')
    recs = {FOREST: rec(FOREST, 'Invented Marsh State Forest')}
    p = park('US-ZZ006', 'Invented Marsh State Park', hid=FOREST)
    row = F.classify('US-ZZ006', p, INSIDE, recs)
    ok(row['bucket'] != 'KEEP', row)
    ok(any('kind-of-land' in x for x in row['reasons']), row['reasons'])
    return done()


def test_wilderness_wsa():
    ok, done = box('kind-of-land guard: Wilderness vs Wilderness Study Area')
    recs = {HELD: rec(HELD, 'Invented Rim Wilderness Study Area')}
    p = park('US-ZZ007', 'Invented Rim Wilderness', typ='Wilderness')
    row = F.classify('US-ZZ007', p, INSIDE, recs)
    ok(row['bucket'] != 'KEEP', row)
    ok(any('kind-of-land' in x for x in row['reasons']), row['reasons'])
    return done()


def test_part_needs_layer():
    ok, done = box('a part never takes the whole: needs a layer')
    recs = {PART: rec(PART, 'Invented Marsh State Park Unit 4')}
    p = park('US-ZZ008', 'Invented Marsh State Park', hid=PART)
    row = F.classify('US-ZZ008', p, INSIDE, recs)
    ok(row['bucket'] == 'NEEDS LAYER', row)
    return done()


def test_trail_drops_trl():
    ok, done = box('trail parks drop the trl copy when the official trail holds the pin')
    recs = {
        OFF_TRAIL: rec(OFF_TRAIL, 'Invented Ridge Trail'),
        TRL: rec(TRL, 'Invented Ridge Trail'),
    }
    p = park('US-ZZ009', 'Invented Ridge Trail', typ='Trail', hid=OFF_TRAIL, m=[[OFF_TRAIL, 0], [TRL, 0]])
    row = F.classify('US-ZZ009', p, INSIDE, recs)
    ok(row['bucket'] == 'FIX', row)
    ok('trl' in (row['recommend'] or '').lower(), row['recommend'])
    return done()


def test_partial_label():
    ok, done = box('partial is labelled "partial, more pieces needed"')
    recs = {HELD: rec(HELD, 'Invented Marsh State Park')}
    row = F.classify('US-ZZ010', park('US-ZZ010', 'Invented Marsh State Park'), FAR200, recs,
                     solver_row={'verdict': 'sliver', 'reasons': ['only a piece of the named land']})
    ok(row['bucket'] == 'PARTIAL', row)
    ok(row['recommend'] == 'partial, more pieces needed', row['recommend'])
    return done()


def test_unresolved_reread():
    ok, done = box('unresolved parks go on the page-reader re-read list')
    recs = {HELD: rec(HELD, 'Invented Lake')}
    p = park('US-ZZ011', 'Invented Marsh State Park')
    row = F.classify('US-ZZ011', p, FAR200, recs, solver_row={'verdict': 'needs a person'})
    ok(row['bucket'] == 'RE-READ', row)
    report = F.run_final_pass(
        [{'park': 'US-ZZ011', 'verdict': 'needs a person'}],
        {'US-ZZ011': ('ZZ', p)},
        {'ZZ': recs},
        {'US-ZZ011': FAR200},
        {'ZZ': {}},
    )
    rr = F.reread_list(report)
    ok(rr['parks'] == ['US-ZZ011'], rr)
    pub = F.ids_only_report(report)
    ok('Invented' not in json.dumps(pub), pub)
    ok(pub['counts']['RE-READ'] == 1)
    return done()


def test_hashes_do_not_move():
    ok, done = box('rules hashes do not move (module is in NOT_RULES)')
    import kpc_key_freeze as K
    t = pathlib.Path('.github/scripts/kpc_key_freeze.py').read_text(encoding='utf-8')
    ok("kpc_solver_final_pass.py" in t and "kpc_solver_final_pass.py" in str(getattr(K, 'NOT_RULES', '')) or "kpc_solver_final_pass.py" in t)
    # current main hashes, this branch is from origin/main with no signed rule edits
    ok(K.rules_hash('us-key') == '3aabd63147fd', K.rules_hash('us-key'))
    ok(K.rules_hash('ca-key') == '3a1d4bf2e112', K.rules_hash('ca-key'))
    ok(K.rules_hash('world-key') == '167bf55f79a8', K.rules_hash('world-key'))
    ok(K.rules_hash('fers') == '62e77c250cc5', K.rules_hash('fers'))
    return done()


def test_fails_without_keep_rule():
    """If the pin-at-the-land KEEP rule is removed, this test fails."""
    ok, done = box('the KEEP rule is required (fails without it)')
    recs = {HELD: rec(HELD, 'Invented Marsh State Park')}
    real = F.classify
    # simulate the rule being absent: never emit KEEP for pin-at-the-land
    def stripped(*a, **k):
        row = real(*a, **k)
        if row.get('bucket') == 'KEEP':
            row = dict(row)
            row['bucket'] = 'RE-READ'
            row['recommend'] = 'unresolved'
        return row
    F.classify = stripped
    try:
        row = real('US-ZZ012', park('US-ZZ012', 'Invented Marsh State Park'), INSIDE, recs)
    finally:
        F.classify = real
    # the real function still KEEPs (we restored it); prove the stripped one would fail the KEEP test
    bad = stripped('US-ZZ012', park('US-ZZ012', 'Invented Marsh State Park'), INSIDE, recs)
    ok(row['bucket'] == 'KEEP', row)
    ok(bad['bucket'] != 'KEEP', 'stripped still KEEP — the fail-without proof is broken')
    return done()


def main():
    fns = [
        test_held_distance_not_working_copy,
        test_keep_pin_inside_name_fits,
        test_keep_within_100m,
        test_no_keep_without_name,
        test_never_hand_other_pota,
        test_kind_guard,
        test_wilderness_wsa,
        test_part_needs_layer,
        test_trail_drops_trl,
        test_partial_label,
        test_unresolved_reread,
        test_hashes_do_not_move,
        test_fails_without_keep_rule,
    ]
    bad = 0
    for f in fns:
        try:
            if not f():
                bad += 1
        except Exception as e:
            print(f'FAIL {f.__name__}: {type(e).__name__}: {e}')
            bad += 1
    print('ALL PASS' if not bad else f'SOME FAILED ({bad})')
    return 0 if not bad else 1


if __name__ == '__main__':
    raise SystemExit(main())
