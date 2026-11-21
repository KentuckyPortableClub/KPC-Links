"""Match by more than name: the checks themselves (kpc_match_checks.py, switch KPC_MATCH_CHECKS; KPC owner, 20 Nov 2026).
Invented parks, records and facts only. No network: a socket guard refuses any connection."""
import gzip, json, os, pathlib, re, socket, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402

UNITS = {'INVP': {'ZZ'}, 'OTHR': {'YY'}}
TAG = {'witness': 'agency_document', 'witness_counts': True}   # a park-facts size tag that counts
TABLE = {'nps': {'agency': 'NPS', 'kind': 'park'}, 'fws': {'agency': 'FWS', 'kind': 'refuge'}, 'sgzza': {'agency': 'state parks', 'kind': 'park'}}
SQ = [[[-80.0, 40.0], [-79.9, 40.0], [-79.9, 40.1], [-80.0, 40.1], [-80.0, 40.0]]]   # about 2,100 acres
STATE_LINK = {'site': 'agency (known)', 'agency': 'ZZ State Parks'}
NPS_LINK = {'site': 'agency (known)', 'agency': 'US National Park Service', 'id_kind': 'NPS unit code', 'id_value': 'INVP'}


def fact(name='Invented Lake State Park', kind='State Park', link=None, size=None, page=None, area='US-ZZ'):
    f = {'area': area, 'name': name, 'type': kind, 'pin': [40.05, -79.95]}
    if link: f['link'] = dict({'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1}, **link)
    if size: f['size'] = dict({'how': 'name+kind', 'flags': []}, **size)
    if page: f['page'] = page
    return f


def srec(oid=1, name='Invented Lake', **kw):
    return dict({'OBJECTID': oid, 'Unit_Nm': name, 'Mang_Type': 'STAT', 'Mang_Name': 'SPR', 'Des_Tp': 'SP', 'GIS_Acres': 2000}, **kw)


def park(name='Invented Lake State Park', rows=None):
    return {'n': name, 't': 'State Park', 'm': rows if rows is not None else [[1, 'Invented Lake', 2000, 'name']], 'c': [], 'g': 'official'}


def run(parks, recs, facts, place=True, **kw):
    return MC.pass_state(parks, recs, facts, lambda ref, ids: place, st='ZZ', units=UNITS, **kw)


def test_kinds_table_is_the_builders():
    src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
    import ast
    node = next(n for n in ast.parse(src).body if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'KINDS')
    ns = {'KINDS': ast.literal_eval(node.value)}
    assert MC.KINDS == ns['KINDS']          # one kind table: the copy here never drifts from the name join's


def test_exact_name_and_link_tie():
    assert MC.exact_name('Invented Lake State Park', 'Invented Lake', 'State Park')
    assert not MC.exact_name('Invented State Park', 'Invented Lake', 'State Park')   # 'X' never ties 'X Lake'
    assert MC.link_tie(fact(link=NPS_LINK), UNITS)[0] == 'NPS unit code'
    for bad in ({'page_kind': 'home page'}, {'usable': False}, {'id_shared_by': 2}, {'id_value': 'NOPE'}, {'id_value': 'OTHR'}):
        assert MC.link_tie(fact(link=dict(NPS_LINK, **bad)), UNITS)[0] is None, bad


def test_agency_check():
    f = fact(link=STATE_LINK)
    assert MC.link_agency(f, 'ZZ') == 'STATE' and MC.link_agency(f, 'YY') is None       # another state's agency: no data
    assert MC.agency_check(f, srec(), 'ZZ') == 'agrees'
    assert MC.agency_check(f, srec(Mang_Type='FED', Mang_Name='USFS'), 'ZZ') == 'differs'
    assert MC.agency_check(f, srec(Mang_Type='UNK', Mang_Name='UNK'), 'ZZ') == 'no data'
    assert MC.agency_check(fact(link={'site': 'other site', 'agency': 'ZZ State Parks'}), srec(), 'ZZ') == 'no data'
    nps = fact(link=NPS_LINK)
    assert MC.agency_check(nps, {'OBJECTID': 'nps7'}, 'ZZ', TABLE) == 'agrees'           # owner from the layer table, not the name
    assert MC.agency_check(nps, {'OBJECTID': 'fws7', 'Unit_Nm': 'Invented National Park'}, 'ZZ', TABLE) == 'differs'
    assert MC.agency_check(fact(link={'site': 'government site', 'agency': 'Recreation.gov'}), srec(Mang_Type='FED', Mang_Name='USACE'), 'ZZ') == 'agrees'


def test_kind_check():
    assert MC.kind_check('State Park', srec()) == 'agrees'
    assert MC.kind_check('State Park', srec(Des_Tp='SW', Unit_Nm='Invented Lake Wildlife Management Area', _k=['wma'])) == 'differs'
    assert MC.kind_check('State Park', srec(Des_Tp='XX')) == 'no data'
    assert MC.kind_check('Unique Area', srec()) == 'no data'


def test_other_park_name_flag():
    names = {MC.full('Invented Lake Wildlife Management Area')}
    assert MC.other_park_name('Invented Lake WMA', 'Invented Lake State Park', names)     # short form spelled out
    assert not MC.other_park_name('Invented Lake State Park', 'Invented Lake State Park', names | {MC.full('Invented Lake State Park')})
    assert not MC.other_park_name('Invented Lake', 'Invented Lake State Park', names)


def test_ids_same_kind_only():
    assert MC.ids_from({'OBJECTID': 1, 'Mang_Name': 'NPS', 'Loc_Nm': 'INVP'}) == {'NPS unit code': 'INVP'}
    mn = {'OBJECTID': 'sgzza1', 'SA': {'uniqueid': 'WMA0000100'}}
    assert MC.ids_from(mn, 'https://x.invalid/us_mn_state_dnr/wma/FeatureServer/0') == {'MN DNR unit id': 'WMA0000100'}
    assert MC.ids_from(mn, 'https://x.invalid/other/FeatureServer/0') == {}
    assert MC.ids_from({'OBJECTID': 2, 'Mang_Name': 'FWS', 'Loc_Nm': 'ABCD'}) == {}       # a refuge code is not an NPS unit code


def test_size_witness_counts_only_the_two_proof_tags():
    for tag, counts in (('agency_document', True), ('hand_copy', True), ('same_record', False), ('other_layer', False), ('unknown', False)):
        assert bool(MC.size_witnesses(fact(size={'acres': 2000, 'witness': tag, 'source_url': 'https://agency.invented.example/p'}))) == counts, tag
    assert not MC.size_witnesses(fact(size={'acres': 2000, 'record_name': 'Invented Lake'}))            # untagged
    assert not MC.size_witnesses(fact(size={'acres': 2000, 'witness': 'agency_document', 'witness_counts': False}))
    pg = fact(page={'own_page': 'own', 'unofficial': False, 'name_vs_pota': 'same', 'sizes': [{'acres': 2000, 'total': True, 'clean': True}]})
    assert not MC.size_witnesses(pg)


def test_layer_table_gives_the_owner():
    assert MC.record_agency({'OBJECTID': 'sgzza4'}, TABLE) == 'STATE'
    assert MC.record_agency({'OBJECTID': 'sgzza4'}, None) is None                            # no table: no data
    assert MC.record_agency({'OBJECTID': 'sgzzq4'}, TABLE) is None                           # a layer the table does not hold
    for words, fam in (('state (many owners)', None), ('several agencies', None), ('unknown', None), ('state water district', 'DIST'),
                       ('state wildlife', 'STATE'), ('BLM', 'BLM'), ('many owners (national list)', None)):
        assert MC.layer_family(words) == fam, words
    assert MC.record_agency({'OBJECTID': 4, 'Mang_Type': 'STAT', 'Mang_Name': 'SPR'}, TABLE) == 'STATE'   # PAD-US: its own fields
    with tempfile.TemporaryDirectory() as t:
        try: MC.load_layer_table(os.path.join(t, 'none.json'))
        except OSError: pass
        else: raise AssertionError('a missing layer table must raise')

if __name__ == '__main__':
    bad = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            try: f(); print('PASS', k)
            except Exception as e: bad += 1; print('FAIL', k, repr(e))  # noqa: BLE001
    print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
