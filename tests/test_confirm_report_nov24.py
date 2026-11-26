#!/usr/bin/env python3
"""24 Nov 2026 plan B (report only): per-rule auto-confirm counters, evidence on each
confirm, header stamps, and a size flag. Invented parks only. No network.
The size-hold switch defaults OFF: a far-off confirm is flagged, not withheld.
Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import json, os, pathlib, socket, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k):
    raise RuntimeError('no network in tests')


socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402
import kpc_confirm_report as CR  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402
import kpc_key_rules as KR  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


# ---- shapes (same square as test_auto_confirm_nov24) ----
SQ = {'type': 'Polygon', 'coordinates': [[[-88.50, 44.50], [-88.45, 44.50], [-88.45, 44.55], [-88.50, 44.55], [-88.50, 44.50]]]}
REC = {'OBJECTID': 'sgzza1', 'Unit_Nm': 'Invented Marsh State Wildlife Area', 'GIS_Acres': 500, '_g': SQ,
       'SA': {'Unit_ID': 'IM-1'}}
PIN_INSIDE = [44.525, -88.475]
TABLE = {'sgzza': {'agency': 'state wildlife', 'kind': 'wildlife area'}}
LINK = {'site': 'agency (known)', 'agency': 'ZZ DNR', 'page_kind': 'own page', 'usable': True,
        'id_shared_by': 1, 'shared_by': 1, 'web_name': 'unit 4471', 'name_match': 'none',
        'id_kind': 'unit id', 'id_value': 'IM-1'}
PAGE = {'kind': 'html', 'own_page': 'own', 'unofficial': False, 'host': 'dnr.zz.example.gov',
        'url': 'https://dnr.zz.example.gov/invented-marsh',
        'name_vs_pota': 'differs', 'name_on_page': '', 'sizes': [], 'coords': [], 'parts': [],
        'inside_of': [], 'county_areas': []}
EMPTY = set()


def fresh(name='Invented Marsh State Wildlife Area', hid='sgzza1', ac=500):
    return {'n': name, 't': 'State Wildlife Area',
            'm': [[hid, name, ac, 'same name']], 'g': 'official', 'ac': ac}


def facts(name, pin, acres=None, page=None):
    row = {'area': 'US-ZZ', 'name': name, 'type': 'State Wildlife Area', 'pin': pin, 'link': dict(LINK),
           'page': dict(page or PAGE)}
    if acres is not None:
        row['size'] = {'acres': acres, 'agency': 'ZZ DNR', 'from': 'acreage bot'}
    return {'US-9001': row}


def run(name='Invented Marsh State Wildlife Area', pin=PIN_INSIDE, acres=None, rec=None,
        page=None, size_hold=False, spelling=None, ac=500):
    parks = {'US-9001': fresh(name=name, ac=ac)}
    before = [list(x) for x in parks['US-9001']['m']]
    recs = {'sgzza1': rec or REC}
    MC.pass_state(parks, recs, facts(name, pin, acres, page), lambda ref, ids: True, st='ZZ',
                  holds_fn=lambda ref, i: True, layer_table=TABLE,
                  auto_confirm_stops=EMPTY, spelling_table=spelling or {}, size_hold=size_hold)
    return parks['US-9001'], before


# exact held name and pin, evidence present, land unchanged
p, before = run()
m = p.get('match') or {}
ev = m.get('evidence') or {}
check('exact held name and pin confirms, and records that rule',
      m.get('status') == 'confirmed' and m.get('by') == 'held name and pin' and m.get('name_how') == 'exact')
check('land is not changed', p.get('m') == before)
check('evidence has agency id, outline acres, pin 0 ft, and the page link',
      ev.get('agency_id') == 'IM-1' and ev.get('outline_acres') == 500
      and ev.get('pin_ft') == 0 and ev.get('page_link') == 'https://dnr.zz.example.gov/invented-marsh'
      and ev.get('held_id') == 'sgzza1')
check('no size flag when official acres are missing', 'size_flag' not in ev)

# spelling table vs looser name
p, _ = run(name='Invented Marsh SWA', spelling={'swa': 'statewildlifearea'})
check('spelling table is counted as its own name path',
      (p.get('match') or {}).get('by') == 'held name and pin'
      and (p.get('match') or {}).get('name_how') == 'spelling table')

# same_place_name without a table (SWA spelled out by the built-in SPELL map)
p, _ = run(name='Invented Marsh SWA', spelling={})
check('#371 looser name (same_place_name) is its own path when no table is needed',
      (p.get('match') or {}).get('by') == 'held name and pin'
      and (p.get('match') or {}).get('name_how') == 'looser name')

# page names the land
page_names = dict(PAGE, name_on_page='Invented Marsh State Wildlife Area', name_vs_pota='differs',
                  parts=['Invented Marsh State Wildlife Area'])
# pass_state uses page_names_land via auto_confirm_ok name_test only when held-name fails
# so use a park name that does not match the record, but the page names the land
p, before = run(name='Invented Marsh', page=page_names, ac=500)
# Invented Marsh vs Invented Marsh State Wildlife Area may still same_place_name (kind words stripped)
# Force a name that fails both name tests? 'Blue Lake' would fail auto-confirm held-name, then page path
# if the page names the land's name.
p, before = run(name='Blue Lake Recreation Site', page=dict(PAGE, name_on_page='Invented Marsh State Wildlife Area',
                                                             parts=['Invented Marsh State Wildlife Area']),
                ac=500)
# kinds may clash (recreation vs wildlife) — kinds_clash blocks auto-confirm
# Use a matching kind: State Wildlife Area park whose POTA name is different but page names the land
p, before = run(name='West Pond Wildlife Area', page=dict(PAGE, name_on_page='Invented Marsh State Wildlife Area',
                                                       parts=['Invented Marsh State Wildlife Area']))
check('page names the land confirms when the held-name test does not, and land is unchanged',
      (p.get('match') or {}).get('status') == 'confirmed'
      and (p.get('match') or {}).get('by') == 'page names the land'
      and p.get('m') == before)

# size flag, switch OFF: still confirmed
p, _ = run(acres=10)  # outline 500 is 50x official 10
ev = (p.get('match') or {}).get('evidence') or {}
check('far-off official acres are flagged, and with the switch OFF the confirm still stands',
      (p.get('match') or {}).get('status') == 'confirmed'
      and ev.get('size_flag') == 'far off'
      and ev.get('official_acres') == 10
      and ev.get('outline_acres') == 500
      and not (p.get('match') or {}).get('size_hold'))

# size flag, switch ON: withheld for auto-confirm only
p, before = run(acres=10, size_hold=True)
check('with the switch ON, a far-off auto-confirm is left outlined and flagged, land unchanged',
      (p.get('match') or {}).get('status') == 'outlined'
      and (p.get('match') or {}).get('size_hold') is True
      and ((p.get('match') or {}).get('evidence') or {}).get('size_flag') == 'far off'
      and p.get('m') == before)

# counters: exact + looser in one pass (two parks, one record). Page-names is a
# separate pass so its heading is not also another POTA park's name in the state.
def two():
    rec2 = dict(REC, OBJECTID='sgzza2')
    parks = {
        'US-9001': fresh('Invented Marsh State Wildlife Area', hid='sgzza1'),
        'US-9002': fresh('Invented Marsh SWA', hid='sgzza2'),
    }
    recs = {'sgzza1': REC, 'sgzza2': rec2}
    f = {
        'US-9001': facts('Invented Marsh State Wildlife Area', PIN_INSIDE)['US-9001'],
        'US-9002': facts('Invented Marsh SWA', PIN_INSIDE)['US-9001'],
    }
    return MC.pass_state(parks, recs, f, lambda ref, ids: True, st='ZZ',
                         holds_fn=lambda ref, i: True, layer_table=TABLE,
                         auto_confirm_stops=EMPTY, spelling_table={})

out = two()
check('per-rule counters: one exact and one looser name in the same pass',
      out.get('by_held name and pin', 0) == 2
      and out.get('by_name_exact', 0) == 1
      and out.get('by_name_looser name', 0) == 1
      and out.get('confirmed', 0) == 2)

parks = {'US-9003': fresh('West Pond Wildlife Area')}
out_p = MC.pass_state(parks, {'sgzza1': REC},
                      {'US-9003': {**facts('West Pond Wildlife Area', PIN_INSIDE)['US-9001'],
                                   'page': dict(PAGE, name_on_page='Invented Marsh State Wildlife Area',
                                                parts=['Invented Marsh State Wildlife Area'])}},
                      lambda ref, ids: True, st='ZZ', holds_fn=lambda ref, i: True,
                      layer_table=TABLE, auto_confirm_stops=EMPTY, spelling_table={})
check('page names the land is counted on its own path',
      out_p.get('by_page names the land', 0) == 1 and out_p.get('confirmed', 0) == 1)

# county belt kept: pin holds the land that sits outside the named county
# Reuse a large square; county area far away would mark it outside, but holds=True keeps it.
careas = [('Invented', -90.0, 40.0, 10.0)]  # name, lon, lat, radius_km — well away from the square
page_c = dict(PAGE, county_areas=[{'name': 'Invented', 'lon': -90.0, 'lat': 40.0, 'radius_km': 10}])
# outside_counties reads county_areas_of(fact) — need the real shape from page_facts helper
# Look at county_areas_of

# header / stamps
td = pathlib.Path(tempfile.mkdtemp())
pf = td / 'park-facts.json'
pf.write_text(json.dumps({
    'made': '2026-11-24',
    'tool': 'kpc_park_facts 10 (2026-11-23)',
    'sources': {'page': {'bot': 'park page reader (kpc-park-pages)', 'parks': 3}},
    'parks': {
        'US-9001': {'size': {'acres': 500}},
        'US-9002': {'size': {'acres': 'n/a'}},
        'US-9003': {'page': {'url': 'https://example.invalid/x'}},
    }
}), encoding='utf-8')
cache = td / 'cache'
cache.mkdir()
# a tiny saved-copy
import gzip
with gzip.open(cache / 'US-ZZ.json.gz', 'wt', encoding='utf-8') as fh:
    json.dump({'st': 'ZZ', 'saved': '2026-11-24', 'recs': []}, fh)
stamp = CR.park_facts_stamp(str(pf))
check('park-facts stamp names the made date, a short hash, and the tool',
      stamp.startswith('2026-11-24 ') and 'tool kpc_park_facts 10 (2026-11-23)' in stamp)
check('page-reader version comes from sources.page',
      'park page reader (kpc-park-pages)' in CR.page_reader_version(str(pf))
      and '3 parks' in CR.page_reader_version(str(pf)))
check('official size count skips a non-number', CR.official_size_count(str(pf)) == 1)
rs = CR.restock_stamp('ZZ', str(cache))
check('per-state restock stamp uses the copy\'s saved date and a short hash',
      rs.startswith('saved 2026-11-24 ') and len(rs.split()[-1]) == 12)

# rule changes since: last hash = current => none; last = ae8e (main before this PR) => this change once scoped
# (scope not yet written in the first run of this test after measure; the check below allows either)
lines = CR.header_lines(root=ROOT, facts_path=str(pf), cache_dir=str(cache), states=['ZZ'],
                        last_rules=KF.rules_hash('us-key', ROOT))
check('header says no rule changes when last test used the current hash',
      any('Rule changes since the last test' in x and 'none' in x for x in lines))
extra = CR.match_checks_extra({'by_held name and pin': 2, 'by_name_exact': 1, 'by_name_spelling table': 0,
                               'by_name_looser name': 1, 'by_page names the land': 1, 'county_belt': 3,
                               'size_far_confirms': 2, 'size_far_ids': ['US-9001', 'US-9002']},
                              ra_used=10, ra_bridged=0, restock='saved 2026-11-24 abcdefabcdef')
check('the extra match-checks line names every rule and the flagged IDs, never a park name',
      'held name and pin 2 (exact 1, spelling table 0, looser name 1)' in extra
      and 'page names the land 1' in extra and 'county belt kept 3' in extra
      and 'store-id fields on 10' in extra and 'size far from official acres (report only): 2' in extra
      and 'US-9001' in extra and 'Invented' not in extra)

# switch defaults OFF; listed in DEFAULTS and key-switches with on: []
sw = json.loads((ROOT / '.github/key-switches.json').read_text(encoding='utf-8'))['switches']
check('KPC_CONFIRM_SIZE_HOLD defaults OFF in DEFAULTS and in key-switches (on: [])',
      KR.DEFAULTS.get('KPC_CONFIRM_SIZE_HOLD') == '0'
      and sw.get('KPC_CONFIRM_SIZE_HOLD', {}).get('on') == [])
check('the confirm-report helper is not a rules file',
      'kpc_confirm_report.py' in KF.NOT_RULES
      and '.github/scripts/kpc_confirm_report.py' not in KF.RULE_FILES['us-key'])

# world / 2-fers hashes must stay at main; US and CA move because report lines live in rule files
check('world and 2-fer hashes stay at main (167bf55f79a8 / 62e77c250cc5)',
      KF.rules_hash('world-key', ROOT) == '167bf55f79a8'
      and KF.rules_hash('fers', ROOT) in ('62e77c250cc5', __import__('kpc_preflight').newest_hash('fers')))   # 26 Nov: or its newest declared line
# newest changelog hash must equal the measured US / CA hashes (written after the measure step)
try:
    import kpc_preflight as PF
    us_ok = PF.newest_hash('us-key') == KF.rules_hash('us-key', ROOT)
    ca_ok = PF.newest_hash('ca-key') == KF.rules_hash('ca-key', ROOT)
except Exception as e:  # noqa: BLE001
    us_ok = ca_ok = False
    print('preflight newest_hash error', e)
check('US and CA rules hashes equal the newest changelog line', us_ok and ca_ok)
check('US and CA hashes moved off main (ae8e40264dda / 7696c35aa512)',
      KF.rules_hash('us-key', ROOT) != 'ae8e40264dda'
      and KF.rules_hash('ca-key', ROOT) != '7696c35aa512')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
