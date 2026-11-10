"""Research inbox rules of Nov 9 2026 (offline): Brandon t956u (an earlier NO never blocks the test; a sure match over it is
'SOLUTION FOUND vs earlier NO', never signed), t955u (agency alias = rule 8 list; a name-less layer is position only), and the
t955u workbook converter. Run from the KPC-Links root: python3 tests/test_research_t955_t956.py"""
import csv, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.github', 'scripts'))
import kpc_research_inbox as RI  # noqa: E402
import kpc_research_from_xlsx as RX  # noqa: E402

SQ = [[[-100.01, 40.01], [-99.99, 40.01], [-99.99, 39.99], [-100.01, 39.99], [-100.01, 40.01]]]
PIN = (40.0, -100.0)


class FakeReader:
    def __init__(self, recs): self.recs = recs
    def near(self, url, lat, lon, km=None): return self.recs, 'saved copy'


def row(**k): return dict({'pota_ref': 'US-9999', 'park_name': 'Elk Creek State Park', 'layer_url': 'https://x.gov/arcgis/rest/services/P/MapServer/0', 'record_id': '7'}, **k)
def poly(nm=None): return {'poly': True, 'r': SQ, 'a': ({'NAME': nm} if nm else {'OBJECTID': 7})}


def test_no_earlier_no_is_plain_sure():
    r = RI.judge(row(), PIN, {}, None, FakeReader({'7': poly('Elk Creek State Park')}))
    assert r['status'] == 'SURE', r


def test_earlier_none_gives_solution_found_not_signed():
    ov = {'none': True, 'when': '2026-10-22', 'why': 'a different place (hand review Oct 22)'}
    r = RI.judge(row(), PIN, ov, None, FakeReader({'7': poly('Elk Creek State Park')}))
    assert r['status'] == RI.SFN and r['earlier_no']['date'] == '2026-10-22' and 'none: true' in r['earlier_no']['decision'], r
    assert 'not signed' in r['reason'] and r['same_record_as_no'] is False


def test_earlier_no_on_same_record_is_flagged():
    r = RI.judge(row(), PIN, {'no': ['usx7'], 'why': 'NO (Nov 2)'}, None, FakeReader({'7': poly('Elk Creek State Park')}))
    assert r['status'] == RI.SFN and r['same_record_as_no'] is True and r['earlier_no']['date'] == 'Nov 2', r


def test_earlier_no_without_solution_stays():
    r = RI.judge(row(), PIN, {'none': True, 'when': '2026-10-22'}, None, FakeReader({'7': poly('Some Other Place')}))
    assert r['status'] == 'NEEDS PERSON' and 'earlier NO on file' in r['reason'], r


def test_agency_alias_is_rule8_list():
    r = RI.judge(row(park_name='Elk Creek Park', official_name='Elk Hollow Park'), PIN, {}, None, FakeReader({'7': poly('Elk Hollow Park')}))
    assert r['status'] == 'NEEDS PERSON' and r.get('alias') and 'rule 8' in r['reason'], r
    # KISS: no shared word (an umbrella unit or a translation) is not an alias question
    r = RI.judge(row(park_name='Elk Creek Park', official_name='Gateway Park'), PIN, {}, None, FakeReader({'7': poly('Gateway Park')}))
    assert not r.get('alias'), r


def test_french_english_names_match():   # Brandon t957u: accents folded, French generic words dropped, NAME_F counts
    rec = {'poly': True, 'r': SQ, 'a': {'NAME_E': 'Estuary Islands National Wildlife Area', 'NAME_F': "Réserve nationale de faune des Îles-de-l'Estuaire"}}
    r = RI.judge(row(park_name="Iles de l'Estuaire National Wildlife Area"), PIN, {}, None, FakeReader({'7': rec}))
    assert r['status'] == 'SURE', r


def test_nameless_layer_position_only():
    r = RI.judge(row(), PIN, {}, None, FakeReader({'7': poly()}))
    assert r['status'] == 'SURE' and r.get('position_only'), r
    r = RI.judge(row(record_id='8'), PIN, {}, None, FakeReader({'7': poly()}))     # the pin is not in the record the research named
    assert r['status'] == 'NEEDS PERSON' and r.get('position_only'), r


def test_hard_pin_cap_fails_closed():
    far = [[[-100.0, 40.00525], [-99.99, 40.00525], [-99.99, 40.016], [-100.0, 40.016], [-100.0, 40.00525]]]   # edge 0.58 km north of the pin
    rec = {'poly': True, 'r': far, 'a': {'NAME': 'Elk Creek State Park'}}
    r = RI.judge(row(), PIN, {}, None, FakeReader({'7': rec}))
    assert 0.5 < RI.km_to(PIN[0], PIN[1], far) < 0.65 and r['status'] != 'SURE', r


def test_wdpa_is_never_sure():
    r = RI.judge(row(layer_url='https://data-gis.unep-wcmc.org/server/rest/services/ProtectedSites/The_World_Database_of_Protected_Areas/MapServer/1'),
                 PIN, {}, None, FakeReader({'7': poly('Elk Creek State Park')}))
    assert r['status'] == 'NEEDS PERSON' and 'WDPA' in r['reason'] and r.get('next_step'), r   # never a bare NO: a named next step


def test_wdpa_lead_finds_the_official_polygon():   # Brandon: WDPA is a lead; the official layer decides
    r = RI.judge(row(pota_ref='MX-0001', layer_url='https://data-gis.unep-wcmc.org/server/rest/services/ProtectedSites/The_World_Database_of_Protected_Areas/MapServer/1'),
                 PIN, {}, None, FakeReader({'7': poly('Elk Creek State Park')}))
    assert r['status'] == 'SURE' and r.get('wdpa_lead') and 'unep' not in r['layer_url'], r


def test_record_id_fix():
    assert RX.rid_fix('PARK_SURVEY_ID 15 (OBJECTID 15)') == '15' and RX.rid_fix('OBJECTID 394 / PASITES_ID 1039') == '394'
    assert RX.rid_fix('CPCAD 471000224') == '471000224' and RX.rid_fix('5102 and 4147') == '5102 4147' and RX.rid_fix(22160) == '22160'


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'tests passed')
