#!/usr/bin/env python3
"""Offline test for .github/scripts/kpc_precheck.py (Nov 3, step 4). Builds a tiny fake repo in a temp folder and checks:
light vs full check (a bot's auto YES is NOT a person), 0,0 pins, pin way out -> hold, spelling -> MISNAMED (no hold) vs NAME_MISMATCH
(hold), a county disagreement never holds, DE 'Pond and Access Site' is the same kind as a State Fishing Lake, lost-find routing,
--apply-hold does nothing unless KPC_PRECHECK_HOLD=1 and never touches a person's join, and TAGS matches kpc_us_key.py."""
import csv, json, os, pathlib, re, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
TOOL = HERE / '.github/scripts/kpc_precheck.py'
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def run(root, env=None, args=()):
    e = dict(os.environ, OUT=str(root / 'out'), DATA=str(root / 'nodata'), KFF_COUNTY_CSV=str(root / 'cty.csv'), **(env or {}))
    e.pop('KPC_PRECHECK_HOLD', None) if not (env and 'KPC_PRECHECK_HOLD' in env) else None
    return subprocess.run([sys.executable, str(TOOL), *args], cwd=root, env=e, capture_output=True, text=True).stdout


with tempfile.TemporaryDirectory() as t:
    R = pathlib.Path(t)
    (R / 'data/us-key').mkdir(parents=True); (R / 'data/ca-key').mkdir(parents=True); (R / 'data/pota/t').mkdir(parents=True)
    parks = {
        'US-1': {'n': 'Alpha State Park', 't': 'State Park', 'g': 'official', 'c': [], 'm': [['sgxxa1', 'Alpha State Park', 100, 'reviewed']], 'far': 'well outside'},
        'US-2': {'n': 'Bravo State Park', 't': 'State Park', 'g': 'official', 'c': [], 'm': [['sgxxa2', 'Bravo State Park', 100, 'reviewed']], 'far': 'well outside'},
        'US-3': {'n': 'Starski State Recreation Site', 't': 'State Recreation Site', 'g': 'official', 'c': [], 'm': [['sgxxa3', 'Stariski State Recreation Site', 50, 'name']]},
        'US-4': {'n': 'Raccoon Lake State Recreation Area', 't': 'State Recreation Area', 'g': 'official', 'c': [], 'm': [['sgxxa4', 'Cecil M. Harden Lake', 50, 'name']]},
        'US-5': {'n': 'Fort Churchill State Park', 't': 'State Park', 'g': 'official', 'c': [], 'm': [['sgxxa5', 'Fort Churchill State Historic Park', 50, 'name']]},
        'US-6': {'n': 'Andrews State Fishing Lake', 't': 'State Fishing Lake', 'g': 'official', 'c': [], 'm': [['sgxxa6', 'Andrews Lake and Access Site', 50, 'name']]},
        'US-7': {'n': 'Charlie Wildlife Refuge', 't': 'National Wildlife Refuge', 'g': 'official', 'c': [], 'm': [['sgxxa7', 'Charlie Hatchery', 50, 'name']]},
        'US-8': {'n': 'Delta State Forest', 't': 'State Forest', 'g': 'pin', 'c': [], 'm': []},
        # rule 18 in the general name test (Brandon, relayed by Super 7:26 PM CST Nov 3)
        'US-21': {'n': 'Golf North Fork Wildlife Area', 't': 'Wildlife Area', 'g': 'official', 'c': [], 'm': [['sgxxa21', 'Golf South Fork Wildlife Area', 50, 'name']]},
        'US-22': {'n': 'Hotel (Lewis County) State Forest', 't': 'State Forest', 'g': 'official', 'c': [], 'm': [['sgxxa22', 'Hotel State Forest', 50, 'name']]},
        'US-23': {'n': 'India Unit 2 Wildlife Area', 't': 'Wildlife Area', 'g': 'official', 'c': [], 'm': [['sgxxa23', 'India Unit 3 Wildlife Area', 50, 'name']]},
        'US-25': {'n': 'Kilo Upper Wildlife Area', 't': 'Wildlife Area', 'g': 'official', 'c': [], 'm': [['sgxxa25', 'Kilo Wildlife Area', 50, 'name']]},
        'US-24': {'n': 'Juliet Lake State Park', 't': 'State Park', 'g': 'official', 'c': [], 'm': [['sgxxa24', 'Juliet Lake State Park', 50, 'name']]},
    }
    json.dump({'parks': parks}, open(R / 'data/us-key/US-XX.json', 'w'))
    json.dump({'parks': {'US-1': {'join': ['sgxxa1'], 'why': 'Oct 30 chat 11 YES'}, 'US-2': {'join': ['sgxxa2'], 'why': "2026-11-03 18:41: layers row YES 'Bravo' (auto (T1 map-match STRONG); applied by kpc_key_answers)"},
                         'US-9': {'join': ['sgaki5'], 'why': 'person YES'}, 'US-10': {'alias': ['Echo Pond'], 'why': 'person'}}}, open(R / 'data/us-key/overrides.json', 'w'))
    json.dump({'A': [['US-9', 'XX', 'Nine', 'join', 'w'], ['US-10', 'XX', 'Ten', 'alias', 'w']],
               'B': [['US-8', 'XX', 'Delta State Forest', 'Delta SF', 'https://services.arcgis.com/x/arcgis/rest/services/y/FeatureServer/0']], 'C': []},
              open(R / 'data/us-key/lost-finds.json', 'w'))
    json.dump([['POTA', r, parks.get(r, {}).get('n', r), 0.0 if r == 'US-7' else 38.0, 0.0 if r == 'US-7' else -84.0, ''] for r in parks], open(R / 'locations.json', 'w'))
    with open(R / 'cty.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['park', 'wwff_counties', 'county_pin', 'pin_in_county', 'km_to_listed', 'wwff_name_vs_pota_rule18'])
        w.writerow(['US-5', 'Lincoln County, NV', 'contradicts', 'Lyon County, NV', '321.7', '[OK]'])
    out = run(R)
    rows = {r['park']: r for r in csv.DictReader(open(R / 'out/scorecard.csv'))}
    pile = {r['park']: r for r in csv.DictReader(open(R / 'out/review-pile.csv'))}
    hold = json.load(open(R / 'out/review-hold.json'))['parks']
    check(rows['US-1']['check'] == 'light' and pile['US-1']['action'].startswith('KEEP') and 'US-1' not in hold, 'a person-approved join gets the light check and is never held')
    check(rows['US-2']['check'] == 'full' and 'US-2' in hold, "a bot's auto-T1 YES is not a person: full check, held when the pin is way out")
    check('MISNAMED' in rows['US-3']['flags'] and 'US-3' not in pile, 'Starski / Stariski: a spelling difference is MISNAMED, not a doubt')
    check('NAME_MISMATCH' in rows['US-4']['flags'] and 'US-4' in hold, 'a record that shares no word with the park is a doubt (held)')
    check('COUNTY' in rows['US-5']['flags'] and 'US-5' not in pile and 'likely wrong' in rows['US-5']['why'], 'a county disagreement alone never holds (the WWFF list can be wrong)')
    check('US-6' not in rows or 'WRONG_KIND' not in rows['US-6']['flags'], "DE 'Andrews Lake and Access Site' is the same kind as a State Fishing Lake")
    check('WRONG_KIND' in rows['US-7']['flags'] and 'POTA_0_0' in rows['US-7']['flags'] and 'US-7' in hold, 'refuge joined to a hatchery: wrong kind; 0,0 pin flagged')
    check('NO_OFFICIAL_BOUNDARY' in rows['US-8']['flags'], 'a pin park is in the no-official-boundary batch')
    # v5 (Brandon, relayed by Super 7:43 PM CST Nov 3): a bracketed place qualifier no longer counts in the general test (US-22);
    # an English position word on one side only does (US-25 'Kilo Upper' vs 'Kilo')
    check('US-22' not in pile and ('US-22' not in rows or 'RULE18_PIECE' not in rows['US-22']['flags']), "v5: '(Lewis County)' alone is not a rule 18 piece in the general test")
    for r in ('US-21', 'US-25', 'US-23'):
        check('RULE18_PIECE' in rows[r]['flags'] and r in pile and 'RULE 18' in pile[r]['action'] and r not in hold,
              f'{r}: rule 18 in the general name test -> RULE18_PIECE, review pile, never held')
    check('US-24' not in pile and ('US-24' not in rows or 'RULE18_PIECE' not in rows['US-24']['flags']), 'a plain same-name join is not a rule 18 piece')
    cn0 = json.load(open(R / 'out/counts.json')); check(cn0.get('RULE18_PIECE') == 3 and cn0.get('rule18_pile_added') == 3, 'counts.json counts RULE18_PIECE ' + str(cn0.get('RULE18_PIECE')))
    lr = {r['park']: r for r in csv.DictReader(open(R / 'out/lost-finds-routed.csv'))}
    check(lr['US-9']['route'] == 'PROPOSED' and 'first set up under AK' in lr['US-9']['why / next step'], "lost find on a layer first set up for another state -> PROPOSED: check the build reads it")
    check(lr['US-10']['route'] == 'NEEDS_RESEARCH', 'lost find with only a name alias -> NEEDS_RESEARCH')
    check(lr['US-8']['route'] == 'PROPOSED', 'a SURE find on an official layer -> PROPOSED for the park-finder lane')
    before = open(R / 'data/us-key/US-XX.json').read()
    run(R, args=('--apply-hold',))
    check(open(R / 'data/us-key/US-XX.json').read() == before, '--apply-hold does nothing while KPC_PRECHECK_HOLD is off')
    run(R, env={'KPC_PRECHECK_HOLD': '1'}, args=('--apply-hold',))
    P = json.load(open(R / 'data/us-key/US-XX.json'))['parks']
    check(P['US-1']['m'] and not P['US-2']['m'] and P['US-2']['g'] == 'pin' and P['US-2']['c'][0][3].startswith('held for review (pre-check)'), 'with the switch on: held parks become pins with the reason; the person-approved join stays')
    check(P['US-3']['m'] and P['US-5']['m'], 'spelling-only and county-only parks keep their outline')
# Nov 3 recut: Quality must-fix 1 (pieces), Brandon's bad-pin ruling (relayed 6:45 PM CST), one row per park, red on a crash
with tempfile.TemporaryDirectory() as t:
    R = pathlib.Path(t)
    for d in ('data/us-key', 'data/ca-key', 'data/pota/t', 'data/canada-bounds'): (R / d).mkdir(parents=True)
    us = {'US-11': {'n': 'Lodi Marsh State Wildlife Area', 't': 'State Wildlife Area', 'g': 'official', 'c': [], 'far': 'well outside',
                    'm': [['sgxxl1', 'Lodi Marsh State Wildlife Area', 100, 'reviewed'], ['sgxxl2', 'Lodi Marsh SWA', 40, 'name']]},
          'US-12': {'n': 'Echo State Park', 't': 'State Park', 'g': 'official', 'c': [], 'm': [['sgxxe1', 'Echo State Park', 100, 'name']]},
          'US-6090': {'n': 'Beaver Dam Mountains Wilderness', 't': 'Wilderness', 'g': 'official', 'c': [], 'far': 'well outside',
                      'm': [['999', 'Beaver Dam Mountains Wilderness', 100, 'name']]}}
    json.dump({'parks': us}, open(R / 'data/us-key/US-XX.json', 'w'))
    json.dump({'parks': {'US-6090': us['US-6090']}}, open(R / 'data/us-key/US-YY.json', 'w'))
    ca = {'CA-1': {'n': 'Foxtrot Provincial Park', 't': 'Provincial Park', 'g': 'official', 'c': [], 'm': [['ON pp:1', 'Foxtrot Provincial Park', 500, 'name']]},
          'CA-2': {'n': 'Golf Provincial Park', 't': 'Provincial Park', 'g': 'official', 'c': [], 'm': [['ON pp:2', 'Hotel Conservation Reserve', 500, 'name']]},
          'CA-3': {'n': 'India Provincial Park', 't': 'Provincial Park', 'g': 'official', 'c': [], 'm': [['ON pp:3', 'India Provincial Park', 500, 'name']]},
          'CA-4': {'n': 'Juliet Provincial Park', 't': 'Provincial Park', 'g': 'official', 'c': [], 'm': [['ON pp:4', 'Juliet Provincial Park', 500, 'name']]}}
    json.dump({'parks': ca}, open(R / 'data/ca-key/CA-ON.json', 'w'))
    sq = lambda x, y: {'type': 'Feature', 'geometry': {'type': 'MultiPolygon', 'coordinates': [[[[x, y], [x + .1, y], [x + .1, y + .1], [x, y]]]]}}
    json.dump(sq(-80.0, 45.0), open(R / 'data/canada-bounds/CA-1.json', 'w'))      # inside Ontario's pin box
    json.dump(sq(-80.0, 45.0), open(R / 'data/canada-bounds/CA-2.json', 'w'))
    json.dump(sq(-120.0, 60.0), open(R / 'data/canada-bounds/CA-3.json', 'w'))     # far outside it
    pins = [['POTA', 'US-11', 'Lodi Marsh State Wildlife Area', 43.3, -89.5], ['POTA', 'US-12', 'Echo State Park', 0.0, 0.0],
            ['POTA', 'US-6090', 'Beaver Dam Mountains Wilderness', 37.0, -113.9]]
    capins = [['POTA', 'CA-1', 'Foxtrot Provincial Park', 0.0, 0.0], ['POTA', 'CA-2', 'Golf Provincial Park', 0.0, 0.0],
              ['POTA', 'CA-3', 'India Provincial Park', 0.0, 0.0], ['POTA', 'CA-4', 'Juliet Provincial Park', 45.5, -79.5]]
    json.dump(pins, open(R / 'locations.json', 'w')); json.dump({'rows': capins}, open(R / 'data/canada.json', 'w'))
    json.dump({'parks': {'US-11': {'join': ['sgxxl1'], 'why': 'Nov 2 3 PM: Quality / Brandon YES (person)'}}}, open(R / 'data/us-key/overrides.json', 'w'))
    (R / 'cty.csv').write_text('park,wwff_counties,county_pin,pin_in_county,km_to_listed,wwff_name_vs_pota_rule18\n')
    run(R)
    sc = {r['park']: r for r in csv.DictReader(open(R / 'out/scorecard.csv'))}
    pl = list(csv.DictReader(open(R / 'out/review-pile.csv'))); pile = {r['park']: r for r in pl}
    hold = json.load(open(R / 'out/review-hold.json'))['parks']; cn = json.load(open(R / 'out/counts.json'))
    check('US-11' in hold and hold['US-11']['ids'] == ['sgxxl2'] and hold['US-11']['keep_ids'] == ['sgxxl1'] and pile['US-11']['action'].startswith('HOLD PIECES'),
          'a partly person-reviewed park: only the non-reviewed piece is held (Quality must-fix 1)')
    check('BAD_POTA_PIN_NAME_MATCH' in sc['CA-1']['flags'] and 'CA-1' not in hold, 'bad pin + name match + outline in the province: the pin is the error, the outline stays, flagged')
    check('BAD_POTA_PIN_NAME_MATCH' in sc['US-12']['flags'] and 'US-12' not in hold, "bad pin + name match + the state's own layer (sgxx in US-XX): flagged, kept")
    check('BAD_POTA_PIN_UNBACKED' in sc['CA-2']['flags'] and 'CA-2' in hold, 'bad pin, the name does not match: a doubt, held for review')
    # addendum (Brandon 6:54 PM CST, relayed): names very close -> the outline stays pending Mapping's check (was: held)
    check('BAD_POTA_PIN_NAME_ONLY' in sc['CA-3']['flags'] and 'CA-3' not in hold and 'CA-3' not in pile,
          "bad pin, the name matches but the area is not backed offline: NAME_ONLY, kept pending Mapping's check (6:54 ruling), not held")
    check(sum(1 for r in pl if r['park'] == 'US-6090') == 1 and pile['US-6090']['area'] == 'US-XX US-YY' and cn['review_pile'] == len(pl) == len({r['park'] for r in pl}),
          'one review-pile row per park (US-6090 in two state files)')
    check(cn['bad_pin_name_area'] == {'BAD_POTA_PIN_NAME_MATCH': 2, 'BAD_POTA_PIN_NAME_ONLY': 1, 'BAD_POTA_PIN_UNBACKED': 1} and cn['status'] == 'green', 'counts.json says how many parks fall each way')
    run(R, env={'KPC_PRECHECK_HOLD': '1'}, args=('--apply-hold',))
    P = json.load(open(R / 'data/us-key/US-XX.json'))['parks']
    check([x[0] for x in P['US-11']['m']] == ['sgxxl1'] and P['US-11']['g'] == 'official' and P['US-11']['held_pieces'] == ['sgxxl2']
          and P['US-11']['c'][0][0] == 'sgxxl2', '--apply-hold never moves a person-reviewed piece; the park stays outlined')
    C = json.load(open(R / 'data/ca-key/CA-ON.json'))['parks']
    check(C['CA-1']['m'] and not C['CA-2']['m'] and C['CA-2']['g'] == 'pin', '--apply-hold: the name+area-backed park keeps its outline; the unbacked one becomes a pin')
    import importlib.util as _iu
    sys.path.insert(0, str(HERE / '.github/scripts'))
    _s = _iu.spec_from_file_location('pc2', TOOL); pc2 = _iu.module_from_spec(_s); _s.loader.exec_module(pc2)
    nab = pc2.name_area_backs
    check(nab('Sierra Gorda Biosphere Reserve', [[110, 'Sierra Gorda', 'Mexico: CONANP / SEMARNAT (federal protected areas)', 'name']], 'MX',
              sources=('Mexico: CONANP / SEMARNAT (federal protected areas)',))[:2] == (True, True), "world: a one-country official layer of the park's country backs the area")
    check(nab('Kungsberget Nature Reserve', [[32410, '2000283 Kungsberget', 'EEA nationally designated areas', 'name']], 'SE',
              sources=('EEA nationally designated areas',))[:2] == (True, False), 'world: an EEA (many-country) layer does not back the area')
    check(nab('Echo State Park', [['sgzze1', 'Echo State Park', 1, 'name']], 'US-XX')[:2] == (True, False), "another state's layer does not back the area")
    # addendum: rule 18 in the bad-pin name test (Quality grade of the recut; Super relayed Brandon 7:11-7:12 PM CST, item 3)
    check(nab('North Fork Wildlife Area', [['sgxxn1', 'South Fork Wildlife Area', 9, 'name']], 'US-XX')[0] is False, 'rule 18: North Fork vs South Fork is not a name match')
    check(nab('Ross Lake Unit 2', [['sgxxr3', 'Ross Lake Unit 3', 9, 'name']], 'US-XX')[0] is False, 'rule 18: Unit 2 vs Unit 3 is not a name match')
    check(nab('Upper Bear Creek WMA', [['sgxxb1', 'Lower Bear Creek WMA', 9, 'name']], 'US-XX')[0] is False, 'rule 18: Upper vs Lower is not a name match')
    m27 = [['Québec prote:5246', 'Réserve naturelle de la Rivière-Malbaie (Conservation de la nature - Québec)', 765, 'name'],
           ['Québec prote:2496', 'Réserve naturelle de la Rivière-Malbaie (Sec. SCCN / Par. Stallman)', 44, 'name']]
    check(nab('Riviere Malbaie (CNC/Stallman) Nature Reserve', m27[:1], 'CA-QC')[0] is False and nab('Riviere Malbaie (CNC/Stallman) Nature Reserve', m27, 'CA-QC')[0] is True
          and 'Stallman' in nab('Riviere Malbaie (CNC/Stallman) Nature Reserve', m27, 'CA-QC')[2], "rule 18: POTA's bracket qualifier (CNC/Stallman) names the Stallman tract, not the CNC one (CA-2227)")
    check(nab('PA 012 State Game Land', [['sgpac8', 'State Game Land 12', 9, 'name']], 'US-PA')[:2] == (True, True), 'rule 18: 012 and 12 are the same number')
    check(nab('Sable Island National Park', [['22036', 'Sable Island National Park Reserve Of Canada', 9, 'name']], 'CA-SI')[0] is True, 'a very close name (one of the 8) still matches')
    check(pc2.name_how('North Fork Wildlife Area', 'South Fork Wildlife Area') == 'same', 'name_how itself is unchanged (rule 18 runs beside it: RULE18_PIECE, flag + pile, never a hold)')
    check(pc2.rule18_differs('Kilo Natura 2000', '2001617 Kilo', True) == '', "'Natura 2000' is a network name, not a piece number")
    # addendum: Mapping's own notes and calls are never a person's answer (item 4)
    ps = pc2.person_said
    check(not ps({'why': '2026-11-03: NO 123: zero-area shape (Mapping, Nov 3 (sampled by Quality 12/12 A+B); remade on fresh main)'}), "a Mapping-only note is not a person's")
    check(not ps({'why': "PROPOSED Nov 3 2026 (Mapping addendum, for Quality to grade): same place"}), "a Mapping PROPOSED join is not a person's")
    check(ps({'why': 'Oct 22 review: same place · 2026-11-03: NO 1 (Mapping, Nov 3)'}), "a person's earlier note still counts next to a Mapping note")
    check(ps({'why': 'Brandon: YES (Mapping found the record)'}) and ps({'join': ['1']}), "a person's note that only mentions Mapping counts; an entry with no note counts (as before)")
    # --- addendum (Nov 3, 6:54 PM CST ruling relayed by Super via Quality; Quality spot-check CA-2227) ---
    ca['CA-5'] = {'n': 'Kilo Nature Reserve', 't': 'Nature Reserve', 'g': 'pin', 'c': [], 'm': []}
    ca['CA-6'] = {'n': 'Lima (CNC/Stallman) Nature Reserve', 't': 'Nature Reserve', 'g': 'official', 'c': [],
                  'm': [['QC prote:5246', 'Réserve naturelle de la Lima (Conservation de la nature)', 700, 'name'], ['QC prote:2496', 'Réserve naturelle de la Lima (Par. Stallman)', 40, 'name']]}
    json.dump({'parks': ca}, open(R / 'data/ca-key/CA-ON.json', 'w'))
    json.dump(sq(-79.6, 45.4), open(R / 'data/canada-bounds/CA-6.json', 'w'))
    capins += [['POTA', 'CA-5', 'Kilo Nature Reserve', 0.0, 0.0], ['POTA', 'CA-6', 'Lima (CNC/Stallman) Nature Reserve', 45.45, -79.55]]
    json.dump({'rows': capins}, open(R / 'data/canada.json', 'w'))
    (R / 'data/review').mkdir(parents=True, exist_ok=True)
    json.dump({'mapping_checked': {'CA-3': {'result': 'PASS: record is in ON', 'by': 'Mapping test'}},
               'ask_brandon': {'CA-6': {'ask': 'trim to Stallman?', 'proposal_text': 'no QC prote:5246', 'proposal': {'no': ['QC prote:5246']}},
                               'CA-3': {'ask': 'name only, area not checked: keep?', 'proposal_text': 'nothing changed', 'proposal': {}}}},
              open(R / 'data/review/precheck-notes.json', 'w'))
    ov_before = open(R / 'data/us-key/overrides.json').read()
    run(R)
    fl = {r['park']: r for r in csv.DictReader(open(R / 'out/BAD_POTA_PIN_FLAGS.csv'))}
    hold = json.load(open(R / 'out/review-hold.json'))['parks']; cn = json.load(open(R / 'out/counts.json'))
    pile = {r['park']: r for r in csv.DictReader(open(R / 'out/review-pile.csv'))}
    check(sorted(fl) == sorted(['US-12', 'CA-1', 'CA-2', 'CA-3', 'CA-5']),
          'BAD_POTA_PIN_FLAGS.csv: every bad-pin park once (name-match, name-only, unbacked and no-outline), good pins not listed ' + str(sorted(fl)))
    check(fl['CA-5']['flag'] == 'BAD_POTA_PIN_NO_OUTLINE' and 'CA-5' not in hold and fl['CA-5']['outline now'].startswith('no outline'),
          'a 0,0 park with no outline is flagged, never demoted (6:54 ruling)')
    check(fl['CA-1']['record id(s)'] == 'ON pp:1' and fl['CA-1']['official name(s)'] == 'Foxtrot Provincial Park' and fl['CA-1']['POTA name'] == 'Foxtrot Provincial Park'
          and fl['CA-1']['reason (POTA pin problem; name + area test)'].startswith('0,0 pin;'), 'each flag row has the reason, the record id, the official name and the POTA name')
    check(fl['CA-3']['flag'] == 'BAD_POTA_PIN_NAME_ONLY' and fl['CA-3']["Mapping's check"].startswith('PASS') and fl['CA-2']['outline now'].startswith('HELD'),
          "Mapping's check from precheck-notes.json is shown; the unbacked park says HELD")
    check(cn['bad_pin_flags'] == 5 and cn['bad_pin_flags_by_flag'].get('BAD_POTA_PIN_NO_OUTLINE') == 1 and cn['bad_pin_flags_held'] == 1, 'counts.json counts the flag list ' + str(cn.get('bad_pin_flags_by_flag')))
    check('CA-6' in pile and pile['CA-6']['action'].startswith('ASK BRANDON') and 'NOT applied' in pile['CA-6']['action'] and 'CA-6' not in hold,
          'ask_brandon: in the review pile with the proposal, never held, proposal not applied')
    check('ASK BRANDON' in fl['CA-3']["Mapping's check"] and fl['CA-3']["Mapping's check"].startswith('PASS') and 'CA-3' in pile
          and pile['CA-3']['action'].startswith('ASK BRANDON') and 'CA-3' not in hold and 'ASK_BRANDON' in pile['CA-3']['flags']
          and cn['ask_brandon'] == ['CA-3', 'CA-6'], 'a NAME_ONLY park on the ask list (SE-0797 case): ASK BRANDON in the flag list, the pile and the flags, not held')
    run(R, env={'KPC_PRECHECK_HOLD': '1'}, args=('--apply-hold',))
    C = json.load(open(R / 'data/ca-key/CA-ON.json'))['parks']
    check(len(C['CA-6']['m']) == 2 and C['CA-3']['m'] and open(R / 'data/us-key/overrides.json').read() == ov_before,
          '--apply-hold: the ASK BRANDON park keeps both tracts and the NAME_ONLY park keeps its outline; overrides untouched')
    # a crash is red, not a quiet green
    (R / 'data/us-key/US-ZZ.json').write_text('{"parks": [1, 2]}')
    e = dict(os.environ, OUT=str(R / 'out2'), DATA=str(R / 'nodata')); e.pop('KPC_PRECHECK_HOLD', None)
    rc = subprocess.run([sys.executable, str(TOOL)], cwd=R, env=e, capture_output=True, text=True)
    check(rc.returncode == 1 and '::error' in rc.stdout and json.load(open(R / 'out2/counts.json'))['status'] == 'red', 'a crash exits 1 with an ::error and a red counts.json')
src = open(HERE / '.github/scripts/kpc_us_key.py').read()
tl = re.search(r'^TAGS = \[.*?\]\n', src, re.S | re.M)
import importlib.util  # noqa: E402
sys.path.insert(0, str(HERE / '.github/scripts'))
spec = importlib.util.spec_from_file_location('pc', TOOL); pc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pc)
ns = {}; exec(tl.group(0), {'re': re}, ns) if tl else None
check(tl and ns.get('TAGS') == pc.TAGS, 'TAGS is the same list kpc_us_key.py uses')
# --- Quality grade of the addendum (7:33 PM CST Nov 3): French compass words + one shared word is not 'same' ---
check(pc.rule18_differs('Clear Creek', 'Upper Clear Creek') and pc.rule18_differs('Big Sandy North', 'Big Sandy')
      and pc.rule18_differs('Outer Banks', 'Banks') and not pc.rule18_differs('Hotel (Lewis County) State Forest', 'Hotel State Forest')
      and pc.rule18_differs('Hotel (Lewis County) State Forest', 'Hotel State Forest', True), 'v5: English one-side position words count; brackets only in the bad-pin test')
check(pc.rule18_differs('Lac Nord-Est', 'Lac Nord-Ouest') and pc.rule18_differs('Île du Sud', 'Ile du Nord')
      and pc.rule18_differs('Rivière Bonaventure Nature Reserve', 'Riviere Bonaventure Ouest', True)
      and not pc.rule18_differs('Lac Saint-Jean', 'Lac-Saint-Jean', True), 'rule 18: Nord/Sud/Est/Ouest (accents, hyphens) tell pieces apart')
check(pc.name_how('Estuaire de la Riviere Bonaventure Nature Reserve', 'Rivière Bonaventure Ouest White-Tailed Deer Yard', True) == 'other'
      and pc.name_how('Alpha Bravo Charlie Wildlife Area', 'Alpha Delta Echo Wildlife Area', True) == 'other'
      and pc.name_how('France MacKeen Nature Reserve', 'Réserve naturelle Frances-MacKeen', True) != 'other'
      and pc.name_how('Kungsberget Nature Reserve', '2000283 Kungsberget', True) == 'same', "one shared word is not 'same' (a near spelling still counts)")
# --- Brandon 7:33 PM CST ruling (relayed): CA-2218, CA-2227, SE-0797 dropped to pins by overrides, kept on the ask list ---
_co = json.load(open(HERE / 'data/ca-key/overrides.json'))['parks']; _wo = json.load(open(HERE / 'data/world-key/overrides.json'))['parks']
_an = json.load(open(HERE / 'data/review/precheck-notes.json'))['ask_brandon']
check('join' not in _co['CA-2218'] and _co['CA-2218']['none'] and 'Réserve faunique de Rimouski' in _co['CA-2218']['no']
      and set(_co['CA-2227']['no']) >= {'Québec prote:2496', 'Québec recog:2496', 'Québec prote:5246', 'Québec recog:5246', 'Réserve naturelle de la Rivière-Malbaie (Sec. SCCN / Par. Stallman)', 'Réserve naturelle de la Rivière-Malbaie (Conservation de la nature - Québec)'} and _co['CA-2227']['none']
      and '2000283 Kungsberget' in _wo['SE-0797']['no'] and _wo['SE-0797']['none'] and 'join' not in _wo['SE-0797']
      and all(_an[r].get('dropped_to_pin') and 'NOT applied' in _an[r]['status'] for r in ('CA-2218', 'CA-2227', 'SE-0797'))
      and not (HERE / 'data/canada-bounds/CA-2218.json').exists() and not (HERE / 'data/canada-bounds/CA-2227.json').exists(),
      'when in doubt drop it: three parks dropped to pins by overrides (no trim, no join) and kept on the ASK BRANDON list')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
