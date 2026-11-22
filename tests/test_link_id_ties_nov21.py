"""Job A (KPC owner, 21 Nov 2026): a web id the map record carries in its own web address, or that the agency's own park list
maps to a map id, ties the record to the park like a direct id tie. Invented parks, records and facts only. No network."""
import json, pathlib, socket, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402
import kpc_source_fields as SF  # noqa: E402

DEC = {'site': 'agency (known)', 'agency': 'NY Dept of Environmental Conservation', 'id_kind': 'NY DEC page number', 'id_value': '1234'}


def fact(link, name='Invented Ridge Wild Forest', kind='State Forest'):
    return {'area': 'US-ZZ', 'name': name, 'type': kind, 'pin': [40.05, -79.95],
            'link': dict({'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1}, **link)}


def dec(oid='sgnya5', url='https://www.dec.ny.gov/lands/1234.html', name='Invented Ridge'):
    return {'OBJECTID': oid, 'Unit_Nm': name, 'GIS_Acres': 2000, 'SA': {'URL': url}}


def park(rows):
    return {'n': 'Invented Ridge Wild Forest', 't': 'State Forest', 'm': rows, 'c': [], 'g': 'official'}


def run(p, recs, facts, place=True):
    return MC.pass_state(p, recs, facts, lambda ref, ids: place, st='ZZ', units={})


def test_the_address_id_is_read():
    assert MC.ids_from(dec()).get(MC.addr_key('NY DEC page number')) == '1234'
    pad = {'OBJECTID': 77, 'Unit_Nm': 'Invented Beach', 'Mang_Name': 'SPR', 'Comments': 'http://www.parks.ca.gov/?page_id=605'}
    assert MC.ids_from(pad).get(MC.addr_key('CA State Parks page id')) == '605'
    mt = {'OBJECTID': 'sgmtb3', 'SA': {'WEB_PAGE': 'https://myfwp.mt.gov/fwpPub/landsMgmt/siteDetail.action?lmsId=39750001'}}
    assert MC.ids_from(mt).get(MC.addr_key('MT FWP lands id')) == '39750001'
    mn = {'OBJECTID': 'sgmnf2', 'SA': {'WEB_LINK1': 'http://www.dnr.state.mn.us/state_forests/sft00002/index.html'}}
    assert MC.ids_from(mn).get(MC.addr_key('MN DNR unit id')) == 'SFT00002'
    assert MC.ids_from(dict(dec(), OBJECTID='sgzzq9')) == {}                       # another layer: its URL field means nothing here


def test_the_address_confirms_a_name_join():
    p = {'US-9001': park([['sgnya5', 'Invented Ridge', 2000, 'name']])}
    run(p, {'sgnya5': dec()}, {'US-9001': fact(DEC)})
    assert p['US-9001']['match']['status'] == 'confirmed' and p['US-9001']['match']['by'] == 'id'


def test_another_address_id_never_drops_a_record():
    p = {'US-9001': park([['sgnya5', 'Invented Ridge', 2000, 'name']])}
    run(p, {'sgnya5': dec(url='https://www.dec.ny.gov/lands/9999.html')}, {'US-9001': fact(DEC)})
    assert p['US-9001']['m'] and p['US-9001']['match']['status'] == 'outlined'      # agree-only: no vote, not a drop


def test_the_address_joins_a_record_the_name_missed():
    p = {'US-9001': {'n': 'Invented Ridge Wild Forest', 't': 'State Forest', 'm': [], 'c': [], 'g': 'pin'}}
    out = run(p, {'sgnya5': dec(name='Ridge Tract 4')}, {'US-9001': fact(DEC)})
    assert out['gained'] == 1 and p['US-9001']['match']['status'] == 'confirmed'
    p = {'US-9001': {'n': 'Invented Ridge Wild Forest', 't': 'State Forest', 'm': [], 'c': [], 'g': 'pin'}}
    assert run(p, {'sgnya5': dec(name='Ridge Tract 4')}, {'US-9001': fact(DEC)}, place=False)['gained'] == 0   # place still needed


def test_the_agency_list_ties_like_a_direct_id():
    tie = {'agency': 'Invented Parks', 'map_layer': 'sgzza', 'map_field': 'UNIT_NO', 'map_id': 'U-77', 'source_url': 'https://lists.invented.example/p.csv'}
    link = {'site': 'agency (known)', 'agency': 'ZZ State Parks', 'id_kind': 'ZZ page number', 'id_value': '77', 'map_tie': tie}
    rec = {'OBJECTID': 'sgzza4', 'Unit_Nm': 'Unit 77', 'GIS_Acres': 2000, 'SA': {'UNIT_NO': 'U-77'}}
    p = {'US-9001': {'n': 'Invented Ridge Wild Forest', 't': 'State Forest', 'm': [], 'c': [], 'g': 'pin'}}
    out = run(p, {'sgzza4': rec, 'sgzza5': dict(rec, OBJECTID='sgzza5', SA={'UNIT_NO': 'U-78'})}, {'US-9001': fact(link)})
    assert out['gained'] == 1 and [q[0] for q in p['US-9001']['m']] == ['sgzza4'] and p['US-9001']['match']['by'] == 'id'
    wd = dict(tie, map_layer='wdpa', map_field='WDPA_PID')
    assert MC.map_tie_of(fact(dict(link, map_tie=wd))) is None                         # never WDPA


def test_a_wdpa_tie_in_the_file_is_never_used():
    with tempfile.TemporaryDirectory() as t:
        f = pathlib.Path(t) / 'ties.json'
        f.write_text(json.dumps({'ties': [{'kind': 'ZZ page', 'layer': 'wdpa', 'field': 'WDPA_URL', 'rx': r'x/(\d+)'},
                                          {'kind': 'ZZ page', 'layer': 'sgzza', 'field': 'URL', 'rx': r'x/(\d+)'}]}))
        assert [r['layer'] for r in MC.load_link_ties(str(f))] == ['sgzza']


def test_the_address_fields_are_kept_and_are_rules():
    keep = json.load(open(ROOT / '.github/keep-record-fields.json'))['layers']
    for t in json.load(open(ROOT / '.github/link-id-ties.json'))['ties']:
        assert t['field'] in keep[t['layer']]['fields'], t
    assert 'Comments' in SF.keep_fields('PAD-US')
    src = (ROOT / '.github/scripts/kpc_us_key.py').read_text()
    assert "_kf('PAD-US')" in src                                                       # PAD-US asks for the keep-list fields
    import kpc_key_freeze as KF
    assert '.github/link-id-ties.json' in KF.RULE_FILES['us-key']


if __name__ == '__main__':
    bad = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            try: f(); print('PASS', k)
            except Exception as e: bad += 1; print('FAIL', k, repr(e))  # noqa: BLE001
    print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
