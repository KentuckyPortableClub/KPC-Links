"""Problem solver (Brandon 4:55 PM CST Nov 7): Research Bot's 17 calls are the fixtures; recommend only, never move a pin."""
import copy, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_problem_solver as S  # noqa: E402

FX = json.load(open(ROOT / 'tests/fixtures/problem-solver-17.json', encoding='utf-8'))['parks']


def go(ref, **ch):
    c = copy.deepcopy(FX[ref]); c.update(ch)
    return S.solve(ref, c['row'], c['pin'], c['recs'], c.get('override'), c['state'])


def test_research_17():
    for ref, want in S.EXPECT.items(): assert go(ref)['verdict'] == want, ref


def test_two_slivers_stay_held():
    for ref in ('US-11748', 'US-5782'):
        r = go(ref); assert r['verdict'] == 'sliver' and r['recommend'].startswith('KEEP HOLDING')


def test_named_fixes():
    assert 'cow909 -> cow910' in go('US-9678')['recommend']
    r = go('US-3917'); assert r['recommend'].startswith('join 254041') and '254129' in r['recommend']
    assert 'ID' in go('US-13039')['recommend'] and 'NV' in go('US-13039')['recommend']
    assert go('US-5789')['confidence'] == 'medium'
    assert 'mistyped' in ' '.join(go('US-4955')['reasons']) and '2-decimal' in ' '.join(go('US-6202')['reasons'])


def test_never_touches_inputs():
    c = copy.deepcopy(FX['US-4933']); before = json.dumps(c, sort_keys=True)
    S.solve('US-4933', c['row'], c['pin'], c['recs'], c.get('override'), c['state'])
    assert json.dumps(c, sort_keys=True) == before   # row, pin and outlines unchanged (the pin is never moved)


def test_no_pin_goes_to_a_person():
    assert go('US-0150', pin=None)['verdict'] == 'needs a person'
    assert go('US-0150', pin=[0, 0])['verdict'] == 'needs a person'


def test_no_outline_goes_to_a_person():
    assert go('US-12028', recs={})['verdict'] == 'needs a person'


def test_reused_id_with_another_name_is_not_used():
    c = copy.deepcopy(FX['US-12028']); c['recs']['sgokc7']['Unit_Nm'] = 'Somewhere Else'; c['recs']['sgokc7']['Loc_Nm'] = ''
    assert S.solve('US-12028', c['row'], c['pin'], c['recs'], None, c['state'])['verdict'] == 'needs a person'


def test_real_small_parcel_is_not_a_sliver():
    # a real 4-point parcel with area (Merrimack River SF sgnhc2075, ~50 ac) is not a sliver
    rec = FX['US-4933']['recs']['sgnhc2075']; assert S.n_points(rec) <= S.SLIVER_PTS and S.acres(rec) > 40


def test_trail_is_not_a_sliver():
    c = copy.deepcopy(FX['US-11748']); c['row']['t'] = 'State Trail'
    assert S.solve('US-11748', c['row'], c['pin'], c['recs'], None, c['state'])['verdict'] == 'needs a person'


def test_name_mismatch_goes_to_a_person():
    c = copy.deepcopy(FX['US-6197']); c['row']['n'] = 'Bridger Wilderness Area'
    assert S.solve('US-6197', c['row'], c['pin'], c['recs'], None, c['state'])['verdict'] == 'needs a person'


def test_typo_not_read_on_huge_land():
    assert 'mistyped' not in ' '.join(go('US-0150')['reasons'])


def test_not_a_rules_file():
    import kpc_key_freeze as F
    assert 'kpc_problem_solver.py' in F.NOT_RULES and all('problem_solver' not in x for v in F.RULE_FILES.values() for x in v)


# ---- Quality Nov 7 FIX (C1-C3): the new calls must not overreach
def solve_ctx(ref, ctx, **row):
    c = copy.deepcopy(FX[ref]); c['row'].update(row)
    return S.solve(ref, c['row'], c['pin'], c['recs'], c.get('override'), c['state'], ctx=ctx)


def test_c1_kind_clash_goes_to_a_person():
    # a historic site whose core name matches a wildlife refuge record (US-9190 Marais des Cygnes) is not 'pin wrong'
    assert solve_ctx('US-6197', None, n='Popo Agie Historic Site', t='State Historic Site')['verdict'] == 'needs a person'


def test_c2_other_state_or_unit_goes_to_a_person():
    r = solve_ctx('US-12028', {'states': ['US-OK', 'US-AR'], 'joined_in': {'AR'}})
    assert r['verdict'] == 'needs a person' and r['other_states'] == ['US-AR'] and 'AR' in ' '.join(r['reasons'])
    assert solve_ctx('US-12028', {'same_name_recs': {'sgokc99': 'Barren Fork'}})['verdict'] == 'needs a person'
    assert solve_ctx('US-12028', None, ac=50000)['verdict'] == 'needs a person'        # the outline is only part of the park
    c = copy.deepcopy(FX['US-12028']); hid = 'sgokc7'
    for x in c['row'].get('m', []) + c['row'].get('c', []):
        if str(x[0]) == hid: x[1] = x[1] + ' Lower Unit'
    assert S.solve('US-12028', c['row'], c['pin'], c['recs'], None, c['state'])['verdict'] == 'needs a person'


def test_c2_fragment_goes_to_a_person():
    c = copy.deepcopy(FX['US-12028']); r = c['recs']['sgokc7']
    x0, y0 = r['_r'][0][0]; r['_r'] = [[[x0, y0], [x0 + .0005, y0], [x0 + .0005, y0 + .0005], [x0, y0 + .0005], [x0 + .0002, y0 + .0007], [x0, y0 + .0006], [x0 - .0001, y0 + .0003]]]
    assert S.solve('US-12028', c['row'], c['pin'], c['recs'], None, c['state'])['verdict'] == 'needs a person'


def test_c3_same_land_new_id_needs_proof():
    assert go('US-9678')['verdict'] == 'same land new ID'                      # Windy Gap: the one Quality supports
    still = solve_ctx('US-9678', {'known_ids': {'cow909': {'Windy Gap WWA'}}})  # the old id is still a record (Menominee 272354)
    assert still['verdict'] == 'needs a person'
    reused = solve_ctx('US-9678', {'known_ids': {'cow909': {'Windy Ridge STL'}}})  # the id lives on under another name: still gone
    assert reused['verdict'] == 'same land new ID'
    assert solve_ctx('US-9678', None, n='Windy Gap Upper Fork Watchable Wildlife Area')['verdict'] == 'needs a person'   # leaves words out


def test_c2_far_same_name_pieces_lower_confidence():
    c = copy.deepcopy(FX['US-4933']); far = copy.deepcopy(c['recs']['sgnhc2075'])
    r = S.solve('US-4933', c['row'], c['pin'], c['recs'], None, c['state'],
                ctx={'same_name_recs': {'zz1': 'Merrimack River State Forest'}, 'extra_recs': {'zz1': far}})
    assert r['verdict'] == 'pin wrong' and r['confidence'] == 'medium' and 'zz1' in r['recommend']
    r = S.solve('US-4933', c['row'], c['pin'], c['recs'], None, c['state'],
                ctx={'same_name_recs': {'zz2': 'Merrimack River State Forest'}, 'extra_recs': {}})
    assert r['verdict'] == 'needs a person'   # an unmeasured same-name record may hold the pin


if __name__ == '__main__':
    fails = 0
    for n, f in sorted(globals().items()):
        if n.startswith('test_') and callable(f):
            try: f(); print('ok  ', n)
            except AssertionError as e: fails += 1; print('FAIL', n, e)
    sys.exit(1 if fails else 0)
