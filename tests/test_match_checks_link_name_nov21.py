"""Match by more than name: confirm by the park's own page address, and Minnesota DNR id fields (kpc_match_checks.py;
KPC owner, 21 Nov 2026). Invented parks, records and facts only. No network: a socket guard refuses any connection."""
import os, pathlib, socket, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402

UNITS = {'INVP': {'ZZ'}}
TABLE = {'nps': {'agency': 'NPS', 'kind': 'park'}, 'sgmnb': {'agency': 'state parks', 'kind': 'forest'},
         'sgmnc': {'agency': 'state parks', 'kind': 'preserve'}}
STATE_LINK = {'site': 'agency (known)', 'agency': 'ZZ State Parks', 'page_kind': 'own page', 'state_check': 'same state'}


def fact(name='Invented Lake State Park', kind='State Park', link=None, size=None, area='US-ZZ'):
    f = {'area': area, 'name': name, 'type': kind, 'pin': [40.05, -79.95]}
    if link: f['link'] = dict({'usable': True, 'id_shared_by': 1, 'shared_by': 1}, **link)
    if size: f['size'] = dict({'how': 'name+kind', 'flags': []}, **size)
    return f


def srec(oid=1, name='Invented Lake', **kw):
    return dict({'OBJECTID': oid, 'Unit_Nm': name, 'Mang_Type': 'STAT', 'Mang_Name': 'SPR', 'Des_Tp': 'SP', 'GIS_Acres': 2000}, **kw)


def park(name='Invented Lake State Park', rows=None):
    return {'n': name, 't': 'State Park', 'm': rows if rows is not None else [[1, 'Invented Lake', 2000, 'name']], 'c': [], 'g': 'official'}


def run(parks, recs, facts, place=True, **kw):
    return MC.pass_state(parks, recs, facts, lambda ref, ids: place, st='ZZ', units=UNITS, layer_table=TABLE, **kw)


def test_address_names_the_park_in_full():
    assert MC.web_name('https://parks.example.gov/state-parks/invented-creek/index.html') == 'invented creek'
    assert MC.name_match('Invented Creek State Park', 'invented creek') == 'strong'
    assert MC.name_match('Invented Creek State Park', 'creek') == 'part'
    assert MC.name_match('Invented Creek State Park', 'other place') == 'none'
    assert MC.name_match('Invented Creek State Park', '') == ''


def test_link_name_agree_is_own_page_in_the_parks_state():
    f = fact(link=dict(STATE_LINK, name_match='strong'))
    assert MC.link_name_agree(f) == 'strong'
    assert MC.link_name_agree(fact(link=dict(STATE_LINK, name_match='part'))) == 'part'
    assert MC.link_name_agree(fact(link=dict(STATE_LINK, name_match='strong', page_kind='shared link'))) == ''
    assert MC.link_name_agree(fact(link=dict(STATE_LINK, name_match='strong', site='other site'))) == ''
    assert MC.link_name_agree(fact(link=dict(STATE_LINK, name_match='strong', state_check='OTHER STATE (US-YY)'))) == ''
    # computed from the address when the saved name_match is missing (POTA's own link, no fetch)
    f = fact(link=dict(STATE_LINK, url='https://parks.zz.gov/state-parks/invented-lake'))
    f['link'].pop('name_match', None)
    assert MC.link_name_agree(f) == 'strong'


def test_strong_link_and_place_confirms_part_is_only_a_note():
    facts = {'US-9001': fact(link=dict(STATE_LINK, name_match='strong'))}
    p = {'US-9001': park()}
    out = run(p, {'1': srec()}, facts, place=True)
    assert out['confirmed'] == 1 and out['by_link'] == 1 and out['by_id'] == 0 and out['by_size'] == 0
    assert p['US-9001']['match']['status'] == 'confirmed' and p['US-9001']['match']['by'] == 'link'
    assert p['US-9001']['match'].get('link') == 'strong'
    p = {'US-9001': park()}
    out = run(p, {'1': srec()}, facts, place=False)            # strong, but place does not pass: stays outlined
    assert out['outlined'] == 1 and out['by_link'] == 0 and p['US-9001']['match']['status'] == 'outlined'
    p = {'US-9001': park()}
    out = run(p, {'1': srec()}, {'US-9001': fact(link=dict(STATE_LINK, name_match='part'))}, place=True)
    assert out['outlined'] == 1 and p['US-9001']['match'] == {'status': 'outlined', 'why': [], 'notes': ['link name']}


def test_id_and_size_outrank_a_link_name():
    nps = {'OBJECTID': 1, 'Unit_Nm': 'Invented Unit', 'Mang_Name': 'NPS', 'Mang_Type': 'FED', 'Loc_Nm': 'INVP', 'Des_Tp': 'NP', 'GIS_Acres': 2000}
    facts = {'US-9001': fact(name='Invented National Park', kind='National Park',
                             link={'site': 'agency (known)', 'agency': 'US National Park Service', 'page_kind': 'own page',
                                   'id_kind': 'NPS unit code', 'id_value': 'INVP', 'name_match': 'strong', 'state_check': ''})}
    p = {'US-9001': {'n': 'Invented National Park', 't': 'National Park', 'm': [[1, 'Invented Unit', 2000, 'name']], 'c': []}}
    run(p, {'1': nps}, facts, place=True)
    assert p['US-9001']['match']['by'] == 'id' and p['US-9001']['match']['status'] == 'confirmed'
    p = {'US-9001': park()}
    tag = {'witness': 'agency_document', 'witness_counts': True, 'acres': 2050}
    run(p, {'1': srec()}, {'US-9001': fact(link=dict(STATE_LINK, name_match='strong'), size=tag)}, place=True)
    assert p['US-9001']['match']['by'] == 'size' and p['US-9001']['match']['status'] == 'confirmed'


def test_minnesota_sft_and_pgrm_project_confirm_like_nps():
    url_b = 'https://example.invalid/us_mn_state_dnr/bdry_state_forest/FeatureServer/4'
    url_c = 'https://example.invalid/us_mn_state_dnr/bdry_scientific_and_nat_areas/FeatureServer/4'
    rec_b = {'OBJECTID': 'sgmnb7', 'Unit_Nm': 'Invented Forest', 'Mang_Type': 'STAT', 'Mang_Name': 'SGMNB',
             'GIS_Acres': 2000, 'SA': {'sft': 'SFT0000100'}}
    rec_c = {'OBJECTID': 'sgmnc8', 'Unit_Nm': 'Invented Natural Area', 'Mang_Type': 'STAT', 'Mang_Name': 'SGMNC',
             'GIS_Acres': 2000, 'SA': {'pgrm_project': 'SNA0000200'}}
    assert MC.ids_from(rec_b, url_b) == {'MN DNR unit id': 'SFT0000100'}
    assert MC.ids_from(rec_c, url_c) == {'MN DNR unit id': 'SNA0000200'}
    assert MC.ids_from(rec_b, '') == {'MN DNR unit id': 'SFT0000100'}          # the layer prefix is enough
    # a WMA uniqueid on the Minnesota DNR path still works
    rec_a = {'OBJECTID': 'sgmna9', 'SA': {'uniqueid': 'WMA0000300'}}
    assert MC.ids_from(rec_a, url_b) == {'MN DNR unit id': 'WMA0000300'}
    facts = {'US-9001': fact(name='Invented State Forest', kind='State Forest',
                             link={'site': 'agency (known)', 'agency': 'MN Dept of Natural Resources', 'page_kind': 'own page',
                                   'id_kind': 'MN DNR unit id', 'id_value': 'SFT0000100', 'usable': True, 'state_check': 'same state'})}
    p = {'US-9001': {'n': 'Invented State Forest', 't': 'State Forest', 'm': [['sgmnb7', 'Invented Forest', 2000, 'name']], 'c': []}}
    run(p, {'sgmnb7': rec_b}, facts, place=True, url_of=lambda a: url_b)
    assert p['US-9001']['match']['status'] == 'confirmed' and p['US-9001']['match']['by'] == 'id'
    assert p['US-9001']['match']['id'] == 'MN DNR unit id SFT0000100'


def test_a_different_same_kind_id_goes_to_check():
    rec = {'OBJECTID': 'sgmnb7', 'Unit_Nm': 'Invented Forest', 'Mang_Type': 'STAT', 'Mang_Name': 'SGMNB',
           'GIS_Acres': 2000, 'SA': {'sft': 'SFT0000999'}}
    facts = {'US-9001': fact(name='Invented State Forest', kind='State Forest',
                             link={'site': 'agency (known)', 'agency': 'MN Dept of Natural Resources', 'page_kind': 'own page',
                                   'id_kind': 'MN DNR unit id', 'id_value': 'SFT0000100', 'usable': True, 'state_check': 'same state'})}
    p = {'US-9001': {'n': 'Invented State Forest', 't': 'State Forest', 'm': [['sgmnb7', 'Invented Forest', 2000, 'name']], 'c': []}}
    run(p, {'sgmnb7': rec}, facts, place=True)
    assert p['US-9001']['match'] == {'status': 'pin', 'why': ['id']}
    assert p['US-9001']['c'][0][3].startswith('check (id')


if __name__ == '__main__':
    bad = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            try: f(); print('PASS', k)
            except Exception as e: bad += 1; print('FAIL', k, repr(e))  # noqa: BLE001
    print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
