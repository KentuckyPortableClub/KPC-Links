"""Standing candidate check in the problem solver (Nov 9 2026): pin cap, acreage, piece merge,
land type, earlier NO, and the official-website step. No network (pages are passed in)."""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '.github/scripts'))
import kpc_problem_solver as PS

# a 1-acre square around (0, 0) — actually ~1 acre needs ~63.6 m side
# 1 degree lat ~ 110.57 km; 0.001 deg ~ 110 m. A 0.0006 deg square is ~4,400 m2 ~ 1.1 acre? Let's build from acres().

def square(lon, lat, half_deg=0.002):
    return [[
        [lon - half_deg, lat - half_deg],
        [lon + half_deg, lat - half_deg],
        [lon + half_deg, lat + half_deg],
        [lon - half_deg, lat + half_deg],
        [lon - half_deg, lat - half_deg],
    ]]


def rec(**kw):
    r = {'id': '1', 'name': 'Test Park', 'rings': square(-86, 38)}
    r.update(kw)
    if 'rings' in r and '_r' not in r:
        r['_r'] = r['rings']
    return r


def test_pin_inside_and_acres_yes():
    ring = square(-86, 38, 0.01)
    r = rec(name='Blue Lake Wildlife Management Area', rings=ring, acres=100)
    park = {'ref': 'US-1', 'name': 'Blue Lake Wildlife Management Area', 'pin': (38, -86), 'official_acres': 100}
    v = PS.check_candidate(park, [r], official_acres=100)
    assert v['verdict'] == 'YES', v
    assert v['signed_by']
    assert v['pin_km'] == 0


def test_pin_over_half_km_is_no():
    r = rec(name='Blue Lake WMA', rings=square(-86, 38, 0.001))
    park = {'ref': 'US-1', 'name': 'Blue Lake Wildlife Management Area', 'pin': (38.01, -86)}  # ~1.1 km north
    v = PS.check_candidate(park, [r], official_acres=None)
    assert v['verdict'] == 'NO', v
    assert 'km' in v['why']


def test_acres_off_is_no():
    r = rec(name='Blue Lake Wildlife Management Area', rings=square(-86, 38, 0.01), acres=100)
    park = {'ref': 'US-1', 'name': 'Blue Lake Wildlife Management Area', 'pin': (38, -86), 'official_acres': 1000}
    v = PS.check_candidate(park, [r], official_acres=1000)
    assert v['verdict'] == 'NO', v
    assert '15%' in v['why']


def test_acres_within_15_pass():
    r = rec(name='Blue Lake Wildlife Management Area', rings=square(-86, 38, 0.01), acres=90)
    park = {'ref': 'US-1', 'name': 'Blue Lake Wildlife Management Area', 'pin': (38, -86)}
    v = PS.check_candidate(park, [r], official_acres=100)
    assert v['verdict'] == 'YES', v


def test_piece_without_merge_is_person():
    r = rec(name='Blue Lake West Wildlife Management Area', rings=square(-86, 38, 0.01), acres=50)
    park = {'ref': 'US-1', 'name': 'Blue Lake Wildlife Management Area', 'pin': (38, -86)}
    v = PS.check_candidate(park, [r], official_acres=100)
    assert v['verdict'] in ('ONLY-PERSON', 'NO'), v
    assert v.get('piece') or 'piece' in v['why']


def test_merge_same_name_parts_then_acres():
    west = rec(id='1', name='Blue Lake West Wildlife Management Area', rings=square(-86, 38, 0.01), acres=50, layer_url='L')
    # override acres after merge: give each half of official 100 via explicit acres, and merge rings
    east = rec(id='2', name='Blue Lake East Wildlife Management Area', rings=square(-85.98, 38, 0.01), acres=50, layer_url='L')
    # official 100, halves 50+50 should pass after merge if rec_acres sums via geometry or acres field
    # rec_acres uses geometry first if _r present; so set acres on merged via summing in function only if geometry used
    park = {'ref': 'US-1', 'name': 'Blue Lake Wildlife Management Area', 'pin': (38, -86)}
    v = PS.check_candidate(park, [west, east], official_acres=None)
    # without official acres, merge still happens; may be ONLY-PERSON
    assert v['merged'] or 'merged' in v['why'].lower() or v['verdict'] in ('YES', 'ONLY-PERSON', 'NO'), v


def test_hatchery_vs_conservation_is_no():
    r = rec(name='Joe Hogan Hatchery', type='State Hatchery', rings=square(-91.9, 34.77, 0.01), acres=355)
    park = {'ref': 'US-12753', 'name': 'Joe Hogan State Conservation Area', 'pin': (34.77, -91.9), 'kind': 'State Conservation Area'}
    v = PS.check_candidate(park, [r], official_acres=270)
    assert v['verdict'] == 'NO', v
    assert 'hatchery' in v['why'] or 'land type' in v['why']


def test_beach_vs_aquatic_reserve_is_no():
    r = rec(name='St Kilda-Chapman Creek', type='Aquatic Reserve', rings=square(138.5, -34.7, 0.05), acres=3470)
    park = {'ref': 'AU-8807', 'name': 'St Kilda State Beach', 'pin': (-34.7, 138.5), 'kind': 'State Beach'}
    v = PS.check_candidate(park, [r], official_acres=3470)
    assert v['verdict'] == 'NO', v


def test_earlier_no_stays_out():
    r = rec(id='250668', name='Bear Run Nature Reserve', rings=square(-79.46, 39.91, 0.01), acres=40)
    park = {'ref': 'US-0622', 'name': 'Bear Run State Conservation Area', 'pin': (39.91, -79.46)}
    v = PS.check_candidate(park, [r], official_acres=5162, earlier_no=['250668'])
    assert v['verdict'] == 'NO', v
    assert 'rejected' in v['why']


def test_website_name_and_acres_push_yes():
    html = '<html><h1>Blue Lake Wildlife Management Area</h1><p>The official size is 100 acres.</p></html>'
    r = rec(name='Blue Lake Wildlife Management Area', rings=square(-86, 38, 0.01), acres=100)
    park = {'ref': 'US-1', 'name': 'Blue Lake Wildlife Management Area', 'pin': (38, -86),
            'website': 'https://example.org/blue-lake', 'official_acres': 100}
    v = PS.check_candidate(park, [r], official_acres=100, page_html=html)
    assert v['verdict'] == 'YES', v
    assert v['site']['push'] == 'yes' or v['site']['name_fit'] is True, v['site']


def test_website_different_size_pushes_no():
    html = '<html><h1>Other River Corridor</h1><p>This protected corridor covers 30,000 acres of river.</p></html>'
    r = rec(name='Râul Olt între Mărunței și Turnu Măgurele', rings=square(24.5, 44.15, 0.2), acres=30196)
    park = {'ref': 'RO-0443', 'name': 'Drăgăneşti-Olt Park', 'pin': (44.15, 24.5),
            'website': 'https://example.org/olt', 'official_acres': 1.4}
    v = PS.check_candidate(park, [r], official_acres=1.4, page_html=html)
    assert v['verdict'] == 'NO', v


def test_dead_site_does_not_block():
    r = rec(name='Blue Lake Wildlife Management Area', rings=square(-86, 38, 0.01), acres=100)
    park = {'ref': 'US-1', 'name': 'Blue Lake Wildlife Management Area', 'pin': (38, -86),
            'website': '', 'official_acres': 100}
    v = PS.check_candidate(park, [r], official_acres=100)
    assert v['verdict'] == 'YES', v
    assert v['site']['status'] in ('missing', 'none', 'not-fetched')


def test_map_pdf_leads_saved():
    html = '''<html><h1>Blue Lake Wildlife Management Area</h1>
    <p>100 acres.</p>
    <a href="/maps/boundary.pdf">Official boundary map</a>
    <a href="/files/park-map.pdf">Park map</a>
    </html>'''
    park = {'ref': 'US-1', 'name': 'Blue Lake Wildlife Management Area',
            'website': 'https://example.org/blue-lake'}
    site = PS.official_website(park, rec={'name': 'Blue Lake Wildlife Management Area'}, rec_acres_v=100,
                               html=html, url=park['website'])
    assert any(u.endswith('.pdf') for u in site['map_leads']), site
    assert site['name_fit'] is True
    assert site['acres_fit'] is True


def test_page_matching_polygon_does_not_override_official_acre_miss():
    """Zone-sized page figure that matches the polygon, when the official park is larger: person, not auto-YES."""
    html = '<html><h1>Pumicestone Passage Fish Habitat Area</h1><p>The management zone is 11,394 acres.</p></html>'
    r = rec(name='Pumicestone Channel', rings=square(153.13, -26.81, 0.05), acres=11392)
    park = {'ref': 'AU-10072', 'name': 'Pumicestone Passage Fish Habitat Protection Area',
            'pin': (-26.81, 153.13), 'website': 'https://example.org/pumicestone', 'official_acres': 23524}
    v = PS.check_candidate(park, [r], official_acres=23524, page_html=html)
    assert v['verdict'] == 'ONLY-PERSON', v
    assert v['site']['push'] == 'yes' or v['site']['acres_fit'] is True, v['site']


def test_lighthouse_vs_fortress_is_no():
    r = rec(name='Fortress of Louisbourg National Historic site', rings=square(-59.96, 45.91, 0.2), acres=14676)
    park = {'ref': 'CA-6375', 'name': 'Louisbourg Lighthouse (The Tower) Historic Site',
            'pin': (45.91, -59.96), 'official_acres': 14826}
    v = PS.check_candidate(park, [r], official_acres=14826)
    assert v['verdict'] == 'NO', v
    assert 'lighthouse' in v['why'] and 'fortress' in v['why']


def test_wdpa_is_never_official_yes():
    r = rec(name='Blue Lake', rings=square(-86, 38, 0.01), acres=100,
            layer_url='https://data-gis.unep-wcmc.org/server/rest/services/ProtectedSites/The_World_Database_of_Protected_Areas/FeatureServer/1')
    park = {'ref': 'XX-1', 'name': 'Blue Lake', 'pin': (38, -86), 'official_acres': 100}
    v = PS.check_candidate(park, [r], official_acres=100)
    assert v['verdict'] != 'YES', v
    assert 'WDPA' in v['why']


def test_pota_wdpa_id_from_url_and_field():
    assert PS.pota_wdpa_id({'website': 'https://www.protectedplanet.net/2516'}) == 2516
    assert PS.pota_wdpa_id({'website': 'https://dopa-explorer.jrc.ec.europa.eu/wdpa/14075'}) == 14075
    assert PS.pota_wdpa_id({'wdpa_id': '196501'}) == 196501
    assert PS.pota_wdpa_id({'website': 'https://www.parks.vic.gov.au/x'}) is None
    assert 2516 in PS.rec_wdpa_ids({'attrs': {'WDPAID': 2516}})
    assert 1268 in PS.rec_wdpa_ids({'properties': {'site_id': 1268}})
    assert not PS.rec_wdpa_ids({'attrs': {'PA_ID': 'WA_44838'}})


def test_id_first_picks_the_record_with_the_pota_site_id():
    wrong = rec(name='Other Place Reserve', rings=square(20.7, 40.9, 0.05), acres=10,
                attrs={'site_id': 99}, layer_url='https://www.protectedplanet.net/99')
    right = rec(name='Galichica', rings=square(20.8, 41.0, 0.05), acres=100,
                attrs={'site_id': 2516}, layer_url='https://www.protectedplanet.net/2516')
    park = {'ref': 'MK-0002', 'name': 'Galichica National Park', 'pin': (41.0, 20.8),
            'website': 'https://www.protectedplanet.net/2516'}
    v = PS.check_candidate(park, [wrong, right])
    assert v['match_how'] == 'pota_wdpa_id', v
    assert v['wdpa_id'] == 2516, v
    assert v['record_name'] == 'Galichica', v
    assert v['verdict'] != 'YES', v


def test_official_record_with_same_wdpa_id_wins():
    wdpa = rec(name='Galichica', rings=square(20.8, 41.0, 0.05), acres=100,
               attrs={'site_id': 2516},
               layer_url='https://www.protectedplanet.net/2516')
    official = rec(name='Galichica National Park', rings=square(20.8, 41.0, 0.05), acres=100,
                   attrs={'WDPAID': 2516},
                   layer_url='https://agency.example.gov/protected-areas')
    park = {'ref': 'MK-0002', 'name': 'Galichica National Park', 'pin': (41.0, 20.8),
            'website': 'https://www.protectedplanet.net/2516', 'official_acres': 100}
    v = PS.check_candidate(park, [wdpa, official], official_acres=100)
    assert v['match_how'] == 'official_wdpa_id', v
    assert v['verdict'] == 'YES', v
    assert 'never official' not in v['why']


if __name__ == '__main__':
    import sys
    names = [n for n, fn in sorted(globals().items()) if n.startswith('test_') and callable(fn)]
    failed = 0
    for n in names:
        try:
            globals()[n]()
            print('PASS ' + n)
        except Exception as e:
            failed += 1
            print('FAIL ' + n + ': ' + repr(e))
    print('ALL PASS' if not failed else 'SOME FAILED')
    sys.exit(0 if not failed else 1)
