"""Match by more than name: one state's pass (kpc_match_checks.py, switch KPC_MATCH_CHECKS; KPC owner, 20 Nov 2026).
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


SQ2 = [[[-79.0, 41.0], [-78.9, 41.0], [-78.9, 41.1], [-79.0, 41.1], [-79.0, 41.0]]]   # another square, away from the pin


def test_outline_unless_a_check_fails():
    facts = {'US-9001': fact(link=STATE_LINK)}
    p = {'US-9001': park()}
    out = run(p, {'1': srec()}, facts)
    assert out['outlined'] == 1 and p['US-9001']['m'] and p['US-9001']['match']['status'] == 'outlined'
    p = {'US-9001': park()}
    run(p, {'1': srec(Mang_Type='FED', Mang_Name='BLM')}, facts)                          # agency known and different
    q = p['US-9001']
    assert not q['m'] and q['g'] == 'pin' and q['match'] == {'status': 'pin', 'why': ['agency']}
    assert q['c'][0][0] == 1 and q['c'][0][3].startswith('check (agency')                 # held to check, never dropped


def test_agency_only_when_known_and_kind_is_a_note():
    p = {'US-9001': park()}
    run(p, {'1': srec(Mang_Type='UNK', Mang_Name='UNK')}, {'US-9001': fact(link=STATE_LINK)})
    assert p['US-9001']['match']['status'] == 'outlined'                                   # no data: not a failure
    p = {'US-9001': park()}
    run(p, {'1': srec()}, {})
    assert p['US-9001']['match']['status'] == 'outlined'                                   # no link at all: not a failure
    p = {'US-9001': park()}
    run(p, {'1': srec(Des_Tp='SW', _k=['wma'])}, {'US-9001': fact(link=STATE_LINK)})
    assert p['US-9001']['m'] and p['US-9001']['match'] == {'status': 'outlined', 'why': [], 'notes': ['kind']}


def test_pin_3c():
    rows = [[1, 'Invented Lake', 2000, 'name'], [2, 'Invented Lake', 900, 'name'], [3, 'Invented Hollow', 50, 'name']]
    recs = {'1': srec(), '2': srec(2), '3': srec(3, 'Invented Hollow')}
    hold = {'1': True, '2': False, '3': False}
    p = {'US-9001': park(rows=[list(r) for r in rows])}
    MC.pass_state(p, recs, {}, lambda ref, ids: True, st='ZZ', units=UNITS, holds_fn=lambda ref, i: hold[i])
    # record 2 is outside the pin but shares the name of record 1, which holds it: a park in pieces, kept
    assert [q[0] for q in p['US-9001']['m']] == [1, 2] and p['US-9001']['match']['why'] == ['place']
    assert p['US-9001']['c'][0][0] == 3
    p = {'US-9001': park(rows=[list(r) for r in rows])}
    MC.pass_state(p, recs, {}, lambda ref, ids: True, st='ZZ', units=UNITS, holds_fn=lambda ref, i: False)
    assert len(p['US-9001']['m']) == 3                                                     # no record holds the pin: no flag


def test_national_layer_rule():
    rows = [[11, 'Invented Lake', 2000, 'name'], [12, 'Invented Lake', 400, 'name']]
    recs = {'11': srec(11, Mang_Type='FED', Mang_Name='USFS'), '12': srec(12)}
    p = {'US-9001': park(rows=[list(r) for r in rows])}
    run(p, recs, {})
    assert [q[0] for q in p['US-9001']['m']] == [12] and p['US-9001']['match']['why'] == ['national']
    p = {'US-9001': park(rows=[[11, 'Invented Lake', 2000, 'name'], [12, 'Invented Lake', 2050, 'name']])}
    run(p, recs, {})
    assert len(p['US-9001']['m']) == 2                                                     # a copy of the state land: kept


def test_another_parks_name_goes_to_check():
    p = {'US-9001': park(rows=[[1, 'Invented Lake WMA', 2000, 'name']]),
         'US-9002': {'n': 'Invented Lake Wildlife Management Area', 't': 'Wildlife Management Area', 'm': [], 'c': []}}
    run(p, {'1': srec(Unit_Nm='Invented Lake WMA')}, {})
    assert p['US-9001']['match'] == {'status': 'pin', 'why': ['name']}


def test_id_confirms_and_stands_in_for_the_name():
    facts = {'US-9001': fact(name='Invented National Park', kind='National Park', link=NPS_LINK)}
    nps = {'OBJECTID': 1, 'Unit_Nm': 'Invented Unit', 'Mang_Name': 'NPS', 'Mang_Type': 'FED', 'Loc_Nm': 'INVP', 'Des_Tp': 'XX', 'GIS_Acres': 2000}
    p = {'US-9001': {'n': 'Invented National Park', 't': 'National Park', 'm': [[1, 'Invented Unit', 2000, 'name']], 'c': []}}
    run(p, {'1': nps}, facts)
    assert p['US-9001']['match']['status'] == 'confirmed' and p['US-9001']['match']['id'] == 'NPS unit code INVP'
    p = {'US-9001': {'n': 'Invented National Park', 't': 'National Park', 'm': [[1, 'Invented Unit', 2000, 'name']], 'c': []}}
    run(p, {'1': dict(nps, Loc_Nm='ABCD')}, facts)                                     # another id of the same kind
    assert p['US-9001']['match'] == {'status': 'pin', 'why': ['id']}


def test_tagged_size_counts_and_untagged_never_does():
    p = {'US-9001': park()}
    run(p, {'1': srec()}, {'US-9001': fact(link=STATE_LINK, size=dict(TAG, acres=2050, record_name='Invented Lake'))})
    assert p['US-9001']['match']['status'] == 'confirmed'
    p = {'US-9001': park()}
    run(p, {'1': srec()}, {'US-9001': fact(link=STATE_LINK, size=dict(TAG, acres=100, record_name='Invented Lake'))})
    assert p['US-9001']['match'] == {'status': 'pin', 'why': ['size']}
    p = {'US-9001': park()}
    run(p, {'1': srec()}, {'US-9001': fact(link=STATE_LINK, size={'acres': 100, 'record_name': 'Invented Lake'})})
    assert p['US-9001']['match']['status'] == 'outlined'                                    # untagged: no vote


def test_code_and_person_rows_stand():
    p = {'US-9001': park(rows=[[5, 'Invented Lake', 2000, 'reviewed (a person)'], [6, 'Invented Trail', 0, 'official trail line']])}
    run(p, {'5': srec(5, Mang_Type='FED', Mang_Name='BLM')}, {'US-9001': fact(link=STATE_LINK)})
    assert len(p['US-9001']['m']) == 2 and p['US-9001']['match']['status'] == 'outlined'


def test_gain_by_link_id_needs_place():
    recs = {'1': {'OBJECTID': 1, 'Mang_Name': 'NPS', 'Mang_Type': 'FED', 'Loc_Nm': 'INVP', 'Unit_Nm': 'Invented Unit', 'GIS_Acres': 2000}}
    facts = {'US-9001': fact(name='Invented National Park', kind='National Park', link=NPS_LINK)}
    for pl, want in ((True, 1), (False, 0)):
        p = {'US-9001': {'n': 'Invented National Park', 't': 'National Park', 'm': [], 'c': [], 'g': 'pin'}}
        out = run(p, recs, facts, place=pl)
        assert out['gained'] == want and len(p['US-9001']['m']) == want
        if want: assert MC.row_class(p['US-9001']['m'][0]) == 'code' and p['US-9001']['match']['status'] == 'confirmed'

if __name__ == '__main__':
    bad = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            try: f(); print('PASS', k)
            except Exception as e: bad += 1; print('FAIL', k, repr(e))  # noqa: BLE001
    print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
