#!/usr/bin/env python3
"""Held states, 18 Nov (.claude/notes/key-quality.md sections 10 and 11 step 2; causes B + C): five misses the contest and D3 made
in the 17 states the drop guard held. Permanent cases with the real names and acres:
  (a) a bare name takes its kind from its LAYER: Gold Butte National Monument keeps 'Gold Butte' from the BLM monuments / NCAs
      layer (the 178,990-acre 'Gold Butte' herd record stays with the herd area); Red Cliffs NCA keeps its NCA-layer records;
      Mount Irish BLM Wilderness Area does not take the 15,075-acre 'Mount Irish' ACEC record.
  (b) two park numbers for the same land both keep the record, labelled (West Foster Creek Wildlife Area x2; Longview Saline).
  (c) a record with a park's exact full name in any of its names is never handed to another park (Lieber SRA, 718 acres).
  (d) the heritage line is for NATIONAL heritage areas only (Old Ruby State Park State Heritage Area, 7 acres).
  (e) a designation line goes to the park that IS that designation even when POTA writes the name another way (Pat's Cabin,
      Beech Creek National Scenic Area / Reserve).
Also: this change's own scope entry and changelog line, found by their id."""
import ast, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
import kpc_key_rules as KR  # noqa: E402
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


src = (SCR / 'kpc_us_key.py').read_text(encoding='utf-8'); ns = {'re': re}
for n in ast.parse(src).body:   # norm() and its word lists, read from the source (importing kpc_us_key runs the key)
    if (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {'GEN', 'ABBR', 'NOTNAME', 'DESIG_WORDS', 'HERITAGE_RX', 'NATIONAL_HERITAGE_RX'} for t in n.targets)) \
            or (isinstance(n, ast.FunctionDef) and n.name in ('norm', '_dcore')):
        exec(compile(ast.Module([n], []), 'x', 'exec'), ns)
norm = ns['norm']

# (a) the layer's own title says what kind its bare-named records are
check(KR.layer_type_words('BLM national monuments / conservation areas') == {'monument', 'conservation'}, "the BLM monuments / NCAs layer: monument + conservation area")
check(KR.layer_type_words('BLM Nevada national monuments + NCAs (land, state GIS table)') == {'monument', 'conservation'}, "Nevada's copy of it (plurals and 'NCAs' read)")
check(KR.layer_type_words('ACEC Designated Polygons (land, state GIS table)') == {'acec'}, 'the ACEC layer: acec')
check(KR.layer_type_words('National Wilderness Preservation System (Forest Service map)') == {'wilderness'}, "an agency's name in a title is not a kind ('Forest Service')")
check(KR.layer_type_words('Nevada outdoor recreation areas (NV Division of State Parks SCORP)', 'compilation') == set(), 'a compilation layer gives no kind')
GB = {'US-4393': ('Gold Butte National Monument', 'National Monument'), 'US-13115': ('Gold Butte BLM Herd Management Area', 'BLM Herd Management Area')}
nca = KR.layer_type_words('BLM national monuments / conservation areas')
check(KR.contest('Gold Butte', GB, norm, nca) == ('win', 'US-4393'), "Gold Butte (BLM monuments / NCAs layer, nca21295) goes to the monument, not to a person")
check(KR.contest('Gold Butte', GB, norm, ('hma',)) == ('win', 'US-13115'), 'the 178,990-acre herd-layer Gold Butte stays with the herd area')
check(KR.contest('Gold Butte', GB, norm, ())[0] == 'person', 'with no layer kind at all it is still a person (unchanged)')
RC = {'US-6077': ('Red Cliffs BLM National Conservation Area', 'BLM National Conservation Area'), 'US-6063': ('Red Cliffs BLM Recreation Management Area', 'BLM Recreation Management Area')}
check(KR.contest('Red Cliffs', RC, norm, nca) == ('win', 'US-6077'), "Red Cliffs (nca21306 / nca21307) goes to the NCA, not the recreation area")
BX = {'US-3852': ('Buxton Woods State Reserve', 'State Reserve'), 'US-6889': ('Buxton Woods State Game Land', 'State Game Land')}
check(KR.contest('Buxton Woods Coastal Reserve', BX, norm) == ('win', 'US-3852'), "'Buxton Woods Coastal Reserve' (1,008 acres) is the State Reserve's, not the game land's")
i = src.find("_lt = (KR.layer_type_words((gs_.get(str(x[0])) or {}).get('Loc_Mang'), _what(x[0]))")
j = src.find("if _rn and (_pn == _rn or _pn.startswith(_rn + ' ')): return True")
check(0 < i < j and "re.match(r'[a-z]', str(x[0]))" in src[i:j] and "{'study', 'wilderness'}" in src[i:j],
      "D3: a layer record's kind is tested before 'its name begins the park's name' (Mount Irish ACEC), study = wilderness (POTA's BLM WSAs)")
k = src.find("if _m: return _pk.get(_m.group(0), set()) | KR.layer_type_words(")
check(k > 0, "the contest's layer kinds include the layer title's kinds")

# (b) same land, two park numbers
WF = {'US-11142': ('West Foster Creek Wildlife Area', 'Wildlife Area'), 'US-12277': ('West Foster Creek Wildlife Area State Fish and Wildlife Area', 'State Fish and Wildlife Area')}
check(KR.contest('West Foster Creek', WF, norm, ('wma',)) == ('both', KR.SAME_LAND), 'West Foster Creek (1,061 acres): both park numbers keep the record, labelled')
LS = {'US-7348': ('Longview Saline Wildlife Management Area', 'Wildlife Management Area'), 'US-7183': ('Longview Saline State Natural Area', 'State Natural Area')}
check(KR.contest('Longview Saline Natural Area WMA', LS, norm) == ('both', KR.SAME_LAND), "'Longview Saline Natural Area WMA' names both kinds of one place: both keep it, labelled")
check(KR.contest('Big Lake', {'US-0163': ('Big Lake National Wildlife Refuge', 'NWR'), 'US-7265': ('Big Lake Wildlife Management Area', 'WMA')}, norm, ('wma',)) == ('win', 'US-7265'),
      'one place, two kinds, a record of ONE kind: a contest win, not same land')
SH = {'US-4417': ('Sam Houston National Forest', 'National Forest'), 'US-10509': ('Sam Houston National Forest Wildlife Management Area', 'Wildlife Management Area')}
check(KR.contest('Sam Houston National Forest WMA', SH, norm) == ('win', 'US-10509'),
      "'Sam Houston National Forest WMA' stays with the WMA (it fits the WMA's kinds exactly): same land is only for a record the contest cannot place")
check(KR.contest('Kirkpatrick Basin Wildlife Management Area', {'US-13614': ('Kirkpatrick Basin North Wildlife Management Area', 'WMA'), 'US-13615': ('Kirkpatrick Basin South Wildlife Management Area', 'WMA')}, norm)[0] == 'person',
      'two places of one kind (North / South) are never same land')
check("parks[_r]['same_land'] = sorted(" in src and '_x == KR.SAME_LAND' in src, "the key labels both parks 'same_land' with the other park number")

# Fable's review of #271 (18 Nov): bracket words, the wilderness kind word, size before a person
HC = {'US-5833': ('Horseshoe Canyon (North) BLM Wilderness Area', 'Wilderness Area'), 'US-5846': ('Horseshoe Canyon (South) BLM Wilderness Area', 'Wilderness Area')}
check(KR.brackets('Horseshoe Canyon (North) BLM Wilderness Area') == 'north' and KR.brackets('Bear Swamp(Cayuga County) State Forest') == 'cayuga county',
      'bracket words are read (also with no space before the bracket)')
check(KR.contest('Horseshoe Canyon (North)', HC, norm, ('wsa',)) == ('win', 'US-5833'),
      "'Horseshoe Canyon (North)' (wsa978) goes to the North park, never to South and never 'same land'")
check(KR.contest('Horseshoe Canyon', HC, norm, ('wsa',))[0] != 'both', 'two parks told apart by a bracket word are never the same name or the same place')
check("len({KR.brackets(parks[r].get('n') or '') for r in _rs}) == 1" in src, "the key's same_land label also needs the same bracket words")
check(KR.LAYER_TYPE['wild'] == 'wilderness', "the US kind tag 'wild' (the federal wilderness layers) is WILDERNESS, not wildlife")
DC = {'US-6010': ('Deep Creek BLM Wilderness Area', 'Wilderness Area'), 'US-6011': ('Deep Creek North BLM Wilderness Area', 'Wilderness Area')}
check(KR.contest('Deep Creek North', DC, norm, ('wild',)) == ('win', 'US-6011'), "layer kind ('wild',) alone: bare 'Deep Creek North' (wbl268) goes to Deep Creek North")
WW = {'US-1': ('Foster Creek Wildlife Area', 'Wildlife Area'), 'US-2': ('Foster Creek BLM Wilderness Area', 'Wilderness Area')}
check(KR.contest('Foster Creek', WW, norm, ('wild',)) == ('win', 'US-2'), 'a wilderness-layer record never fits a wildlife area of the same name')
sz = lambda refs: 'US-13126' if 'US-13126' in refs else None
DM = {'US-10844': ('Diamond BLM Herd Management Area', 'BLM Herd Management Area'), 'US-13126': ('Diamond Complex BLM Herd Management Area', 'BLM Herd Management Area')}
check(KR.contest('Diamond', DM, norm, ('acec',), None, sz) == ('win', 'US-13126'),
      'a layer kind that fits none of the parks falls back to the bare-name path: the land a park already holds decides first')
check(KR.contest('Diamond', DM, norm, ('acec',))[1].startswith('a bare name'), '... and with no size or agency answer it goes to a person as a bare name')

# second round (18 Nov): the state-gis kind tail is not a layer title; the size step needs the same box
check(KR.layer_type_words('Alaska Department of Natural Resources (preserve, state GIS table)') == set(),
      "Alaska's legislatively designated areas layer says no kind ('preserve' is the coarse state-gis tag): Kenai River US-12708 keeps 'Kenai River' (sgakb796)")
check(KR.box_overlap([0, 0, 1, 1], [0.05, 0.05, 1.05, 1.05]) > .8 and KR.box_overlap([0, 0, 1, 1], [1.2, 0, 2.2, 1]) == 0, 'box overlap: a copy covers, a neighbour does not')
check("KR.box_overlap(_bb0, (gs_.get(str(x[0])) or {}).get('_bb')) >= .6" in src,
      "the contest's size step counts only a held record whose box covers this one (60%): Big Lake NWR (10,911 ac, boxes 47%) does not take the state's 'Big Lake' (10,804 ac, PAD-US 166827); Caddo Lake WMA keeps its 8,307-ac copy (70%)")

# (c) exact full name in any of the record's names
lieber = {'OBJECTID': 'sginc3226', 'Unit_Nm': 'Cagles Mill Lake', 'Loc_Nm': 'Lieber State Recreation Area', 'GIS_Acres': 718.0}
names = {KR._full(n) for n in KR.rec_names(lieber)}
check(KR._full('Lieber State Recreation Area') in names and KR._full('Cagles Mill Lake National Recreation Area') not in names,
      "sginc3226 carries Lieber SRA's exact full name (Loc_Nm) and not Cagles Mill Lake NRA's")
a = src.find('_nms = ({KR._full(n) for n in (KR.rec_names(gs_.get(_id) or {}) or [])}')
b = src.find('_v, _x = (\'win\', _fx[0]) if len(_fx) == 1 else KR.contest(')
check(0 < a < b, 'the contest first gives a record to the ONE sharing park whose exact full name it carries')
check("if re.match(r'[a-z]', _id) else set()" in src[a - 50:b], "only a state layer record: PAD-US's local name (Mt. Hood NF land 'Willamette National Forest') does not count")

# (d) national heritage areas only
NH = ns['NATIONAL_HERITAGE_RX']
check(not NH.search('State Heritage Area Old Ruby State Park State Heritage Area'), 'Old Ruby State Park State Heritage Area (7 acres) is not a national heritage area')
check(bool(NH.search('National Heritage Area Abraham Lincoln National Heritage Area')) and bool(NH.search('Blackstone River Valley National Heritage Corridor')),
      'a national heritage area or corridor still gets pin + sits on')
check('if NATIONAL_HERITAGE_RX.search(' in src, 'D3 tests the national heritage pattern')

import os  # noqa: E402
_data = pathlib.Path(os.environ.get('DATA') or (ROOT.parent / 'kpc-data'))
if (_data / 'data/parkinfo').is_dir():
    _h = []
    for f in sorted((_data / 'data/parkinfo').glob('US-*.json')):
        for ref, v in (json.loads(f.read_text(encoding='utf-8')).get('parks') or {}).items():
            t = f"{v[2] if len(v) > 2 else ''} {v[0]}"
            if ns['HERITAGE_RX'].search(t) and not NH.search(t): _h.append(ref)
    check(sorted(set(_h)) == ['US-12413', 'US-12830'], f"the US parks named or typed heritage area / corridor that are NOT national are Spokane Plains Battlefield and Old Ruby, two small Washington state sites (a new one fails this: look at it) ({sorted(set(_h))})")
else: print('SKIP heritage count: no KPC-Data checkout')

# (e) the designation is the park, written another way
dc = ns['_dcore']
check(dc(KR._full('Pats Cabin WSA')).replace(' ', '') == dc(KR._full("Pat's Cabin Wilderness Area")).replace(' ', ''), "'Pats Cabin WSA' IS Pat's Cabin Wilderness Area (wsa1412)")
check(dc(KR._full('Beech Creek National Scenic Area')).replace(' ', '') == dc(KR._full('Beech Creek National Scenic Reserve')).replace(' ', ''),
      "'Beech Creek National Scenic Area' (fsod75, 8,042 acres) IS Beech Creek National Scenic Reserve")
check(dc(KR._full('Phipps - Death Hollow ISA')) == dc(KR._full('Phipps-Death Hollow BLM Wilderness Area')), 'the Phipps - Death Hollow case still holds')

# bookkeeping, by this change's own id
sc = next((c for c in json.loads((ROOT / '.github/us-key-rule-scope.json').read_text())['changes'] if c.get('id') == '2026-11-18-held-states-contest-d3'), {})
check(sc.get('from') == '51840791a6b9' and len(sc.get('scope', {}).get('states', [])) == 50 and sc['scope'].get('saved_ids') is True
      and 'APPROVED' in str(sc.get('approved')), 'scope entry 2026-11-18-held-states-contest-d3 (from the Q1 hash 51840791a6b9, every US state the key builds, saved ids re-matched, approved)')
log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
own = next((x for x in log.splitlines() if 'branch prep/held-states-contest-d3' in x and 'US rules 51840791a6b9 -> ' in x), '')
check(bool(own) and 'APPROVED' in own, "this change's own changelog line is there and approved by the owner")

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
