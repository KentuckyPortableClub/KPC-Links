"""batch 1b offline tests for the key (no network): the PAD-US dedupe overlap test and keep list, and the rule 18 tract
exception. Run from the KPC-Links root: python3 tests/test_key_batch1b.py (or python3 -m pytest -q tests/test_key_batch1b.py)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_match_tests as T  # noqa: E402

us = T._load('kpc_us_key.py', '\nidx = {}\n')
KR = us.KR

# Mohawk River State Park (US-8071), the two NYNHP copies as the saved copy keeps them (boundary-cache US-NY.json.gz, detail
# 0.001): PAD-US 2.0 record 232632 and 4.0 record 237555, same name, same 105 ac, but other / shifted land (Quality: 24.5%)
MOHAWK = {"232632": [[[-73.85144, 42.79546], [-73.855, 42.79455], [-73.85642, 42.79634], [-73.85144, 42.79546]], [[-73.85342, 42.80039], [-73.85961, 42.79947], [-73.85817, 42.80101], [-73.85342, 42.80039]], [[-73.85342, 42.80039], [-73.84916, 42.79987], [-73.84692, 42.79793], [-73.85216, 42.79695], [-73.85146, 42.79856], [-73.85342, 42.80039]], [[-73.85103, 42.80155], [-73.84943, 42.80012], [-73.86294, 42.80283], [-73.85941, 42.80285], [-73.85889, 42.80435], [-73.85876, 42.80289], [-73.85554, 42.80166], [-73.8531, 42.80383], [-73.85103, 42.80155]]], "237555": [[[-73.85222, 42.7965], [-73.856, 42.79836], [-73.85099, 42.79844], [-73.85222, 42.7965]], [[-73.85809, 42.80237], [-73.85922, 42.80151], [-73.85778, 42.80305], [-73.85303, 42.80243], [-73.85809, 42.80237]], [[-73.84761, 42.8007], [-73.8465, 42.79997], [-73.84841, 42.79861], [-73.85173, 42.79899], [-73.85104, 42.8006], [-73.853, 42.80243], [-73.84761, 42.8007]], [[-73.8497, 42.80278], [-73.86248, 42.80485], [-73.85896, 42.80486], [-73.85844, 42.80637], [-73.85831, 42.80491], [-73.85509, 42.80368], [-73.85265, 42.80585], [-73.8497, 42.80278]]]}


def rec(oid, name, ac, agg, rings, cat='Fee', des='SP'):
    return {'OBJECTID': oid, 'Unit_Nm': name, 'Loc_Nm': '', 'GIS_Acres': ac, 'Agg_Src': agg, 'Category': cat, 'Des_Tp': des,
            '_g': {'rings': rings}, '_bb': us.bbox({'rings': rings})}


SQ = [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]


def test_mohawk_river_is_not_a_copy():
    old = rec(232632, 'Mohawk River State Park', 105, 'NYNHP_PADUS2_0_x', MOHAWK['232632'])
    new = rec(237555, 'Mohawk River State Park', 105, 'NYNHP_PADUS4_0_x', MOHAWK['237555'])
    assert us._share_inside(old, new) < 0.5
    assert KR.padus_old_copies([old, new], set(), us._share_inside) == set()


def test_refuge_copy_is_dropped_only_with_90_percent_overlap():
    old = rec(3589, 'Arctic National Wildlife Refuge', 19637012, 'FWS_PADUS3_0Fee_FWSInterest_Simplified', SQ, des='NWR')
    new = rec(4519, 'Arctic National Wildlife Refuge', 19637182, 'FWS_PADUS4_0Fee_FWS_FWSInterest_Simplified', SQ, des='NWR')
    assert KR.padus_old_copies([old, new], set(), us._share_inside) == {'3589'}
    assert KR.padus_old_copies([old, new], {'3589'}, us._share_inside) == set()      # a person's join is kept
    assert KR.padus_old_copies([old, new], set(), lambda a, b: None) == set()           # land not measurable: keep both
    assert KR.padus_old_copies([old, new], set(), lambda a, b: 0.89) == set()           # under 90%: keep both


def test_keep_list_is_built_after_the_fingerprint_refind():
    # a person joined id 3765 (US-0171); PAD-US renumbered it 9999: the NEW id must be protected too
    old_ovr = dict(us.OVR)
    try:
        us.OVR.clear(); us.OVR['US-0171'] = {'join': ['3765'], 'fp': {'3765': ['Some Refuge', 1000]}}
        P = {'US-0171': ['Some Refuge', 'US', 'NWR', 0, 0, 0.5, 0.5]}
        recs = [rec(9999, 'Some Refuge', 1010, 'FWS_PADUS4_0Fee', SQ), rec(8888, 'Some Refuge', 1000, 'FWS_PADUS3_0Fee', [[[50, 50], [50, 51], [51, 51], [50, 50]]])]
        assert us._hand_ids(recs, P) == {'3765', '9999'}   # 8888 is far from the pin: not protected
    finally:
        us.OVR.clear(); us.OVR.update(old_ovr)


def test_tract_exception_list_and_grouping():
    for ref, tr in (('US-11813', 'Abo'), ('US-11814', 'Quarai'), ('US-0961', 'Gran Quivira')):
        t = KR.tract_entry(ref)
        assert t['tract'] == tr and t['record'] == 'Salinas Pueblo Missions National Monument' and t['of'] == 3
        assert t['approved_by'] and t['approved'] and t['build']
        assert 'Salinas Pueblo Missions National Monument' in KR.tract_note(t) and tr in KR.tract_note(t)
    assert KR.tract_entry('US-0001') is None
    assert KR.tract_label(KR.tract_entry('US-0961')) == 'Salinas Pueblo Missions NM, Gran Quivira tract (NPS boundary piece)'
    assert KR.tract_note(KR.tract_entry('US-11813')).startswith('Salinas Pueblo Missions NM, Abo tract (NPS boundary piece).')
    # an overrides 'tract' entry needs a person's name; without one it is ignored
    assert KR.tract_entry('US-0001', {'tract': {'record': 'X', 'tract': 'Y'}}) is None
    assert KR.tract_entry('US-0001', {'tract': {'record': 'X', 'tract': 'Y', 'approved_by': 'Brandon'}})['tract'] == 'Y'
    # pieces within 1 km = one tract; pieces 50 km apart = separate tracts (Salinas: 6 pieces -> 3 tracts)
    b = [[-106.0, 34.0, -105.99, 34.01], [-105.989, 34.0, -105.98, 34.01], [-105.5, 34.4, -105.49, 34.41]]
    assert KR.tracts_of(b) == [[0, 1], [2]]


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok  ', k)
    print(f'{n} tests passed')
