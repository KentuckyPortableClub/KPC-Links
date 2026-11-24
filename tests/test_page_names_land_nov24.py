#!/usr/bin/env python3
"""24 Nov 2026 (owner 6:41 AM "1 name i been screaming this!", 6:57 AM "Page reader whole reason is to read names!!"): the spelling
table and the page-names-the-land witness. Invented parks only. No network. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import pathlib, socket, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('no network in tests'))
import kpc_match_checks as MC  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


S = MC.same_place_name
check('SWA spelled out', S('Invented-Treat State Wildlife Area', 'Invented Treat SWA'))
check('CA at the end = conservation area', S('Invented Bend State Conservation Area', 'Invented Bend CA'))
check('CA in the middle is not spelled out (a state code there)', MC.spelled('Invented CA Lake') == ['invented', 'ca', 'lake'])
check('sulphur = sulfur', S('Hot Sulfur Flats State Wildlife Area', 'Hot Sulphur Flats State Wildlife Area'))
check('trails = trail', S('Invented Heritage Trails State Park', 'Invented Heritage Trail State Park'))
check('a forest is not a park', not S('Invented Hump State Forest', 'Invented Hump State Park'))
check('Wilderness is not a Wilderness Study Area', not S('Invented Peak Wilderness Area', 'Invented Peak WSA'))
check('another place name is not the same (Little ...)', not S('Invented River State Forest', 'Little Invented River State Forest'))
check('a core under 4 letters never matches', not S('Ox State Park', 'Ox Lake State Park') and not S('Ab Park', 'Ab Forest'))

PAGE = lambda name, own='own', kind='html', host='parks.invented.gov': {
    'page': {'own_page': own, 'kind': kind, 'name_on_page': name, 'host': host}, 'link': {'site': 'agency (known)'}}
PN = MC.page_names_land
check("own page names the land's own name", PN(PAGE('Invented Falls State Scenic Viewpoint'), 'Invented Falls State Park', 'Invented Falls State Scenic Viewpoint'))
check('own page heading part names the land', PN(PAGE('Visit | Invented Marsh SWA'), 'Invented Marsh State Wildlife Area', 'Invented Marsh State Wildlife Area'))
check('a list page gives nothing', not PN(PAGE('Invented Falls State Scenic Viewpoint', own='list'), 'Invented Falls State Park', 'Invented Falls State Scenic Viewpoint'))
check('a PDF title gives nothing', not PN(PAGE('Invented Falls State Scenic Viewpoint', kind='pdf'), 'Invented Falls State Park', 'Invented Falls State Scenic Viewpoint'))
check('an unofficial host gives nothing', not PN({'page': {'own_page': 'own', 'kind': 'html', 'name_on_page': 'Invented Falls', 'unofficial': True}, 'link': {}}, 'Invented Falls State Park', 'Invented Falls'))
check("another POTA park's name on the page gives nothing",
      not PN(PAGE('Invented Lake State Park'), 'Invented Lake Access State Park', 'Invented Lake State Park', None, {MC.full('Invented Lake State Park')}))
check('a site heading (same text on 3+ pages of the host) gives nothing',
      not PN(PAGE('State Parks'), 'Invented Lake State Park', 'State Parks', {('parks.invented.gov', MC.full('State Parks')): 3}))
check('a trail is not a park (review: one side had no kind family)', not S('Invented Ridge Trail', 'Invented Ridge State Park'))
check('an access is not a park', not S('Invented Lake Access', 'Invented Lake State Park'))
check('a memorial is not a park', not S('Invented Memorial', 'Invented State Park'))
check('a historic site is not a park', not S('Invented Mill State Historic Site', 'Invented Mill State Park'))
check('a bare name still matches its land', S('Invented Marsh', 'Invented Marsh State Wildlife Area'))
check('nature reserve = nature preserve', S('Invented Bog Nature Reserve', 'Invented Bog Nature Preserve'))

# The same gate as auto-confirm (#369): the HELD record only, the stop list, person-NO, blocked ids, 100 m on the saved outline.
SQ = {'type': 'Polygon', 'coordinates': [[[-88.50, 44.50], [-88.45, 44.50], [-88.45, 44.55], [-88.50, 44.55], [-88.50, 44.50]]]}
HELD = {'OBJECTID': 'sgzzb1', 'Unit_Nm': 'Invented Falls State Scenic Viewpoint', 'GIS_Acres': 500, '_g': SQ}
OTHER = {'OBJECTID': 'sgzzb2', 'Unit_Nm': 'Invented Falls Annex', 'GIS_Acres': 50, '_g': SQ}
recs = {'sgzzb1': HELD, 'sgzzb2': OTHER}
P = {'n': 'Invented Falls State Park', 'm': [['sgzzb1', HELD['Unit_Nm'], 500, ''], ['sgzzb2', OTHER['Unit_Nm'], 50, '']],
     'bk': ['sgzzb1', 99], 'held': {'ids': ['sgzzb1']}}
pg = PAGE('Invented Falls State Scenic Viewpoint')
test = lambda f: (lambda pn, rn: PN(f, pn, rn))
def ok_at(pin, page=pg, park=P, **kw):
    facts = {'US-9002': dict(page, name=park['n'], pin=pin)}
    return MC.auto_confirm_ok('US-9002', park, recs, facts, pin=pin, name_test=test(facts['US-9002']), **kw)
check('page names the held record, pin inside (holds = yes): confirms', ok_at([44.525, -88.475], holds_fn=lambda r, i: True))
check('pin deep inside the saved outline with no holds answer: confirms (0 m, not the distance to the edge)', ok_at([44.525, -88.475]))
check('pin about 63 m outside: confirms (100 m, like auto-confirm)', ok_at([44.525, -88.45 + 0.0008]))
check('pin about 400 m outside: not confirmed (was 1 km before the review)', not ok_at([44.525, -88.45 + 0.005]))
check('a page naming only another joined row (not the held record) gives nothing',
      not ok_at([44.525, -88.475], holds_fn=lambda r, i: True, page=PAGE('Invented Falls Annex')))
check('a park on the stop list is never confirmed', not ok_at([44.525, -88.475], holds_fn=lambda r, i: True, stop_parks={'US-9002'}))
check("a person's NO stops it", not ok_at([44.525, -88.475], holds_fn=lambda r, i: True, is_no=lambda r, i, a: True))
check('a blocked id stops it', not ok_at([44.525, -88.475], holds_fn=lambda r, i: True, blocked={'US-9002': {'sgzzb1'}}))
TBL = {'sgzzb': {'agency': 'state wildlife', 'kind': 'wildlife area'}}
check("a bare record name takes its layer's kind: a wildlife-area layer record never confirms a State Park",
      not ok_at([44.525, -88.475], holds_fn=lambda r, i: True, park=dict(P, m=[['sgzzb1', 'Invented Falls', 500, '']]), layer_table=TBL,
                page=PAGE('Invented Falls')) and MC.kinds_clash({'t': 'State Park'}, HELD, TBL))
# Review round 3: no held record is ever made up from the nearest edge. A tiny bare-named sliver 10 m off and a big same-place
# park outline 20 m off, neither holding the pin, and no 'held' / 'bk' yet (a fresh pass): nothing is confirmed.
SLIVER = {'OBJECTID': 'sgzzc1', 'Unit_Nm': 'Invented Falls', '_g': {'type': 'Polygon', 'coordinates': [[[-88.4499, 44.5249], [-88.4498, 44.5249],
          [-88.4498, 44.5250], [-88.4499, 44.5250], [-88.4499, 44.5249]]]}}
BIG = {'OBJECTID': 'sgzzc2', 'Unit_Nm': 'Invented Falls State Park', '_g': SQ}
fresh = {'n': 'Invented Falls State Park', 't': 'State Park', 'm': [['sgzzc2', 'Invented Falls State Park', 500, ''], ['sgzzc1', 'Invented Falls', 1, '']]}
pin_out = [44.52495, -88.45 + 0.00025]   # ~20 m east of the big outline, ~10 m from the sliver
f_out = {'US-9003': {'name': fresh['n'], 'pin': pin_out}}
check('a fresh pass with no record holding the pin confirms nothing (never the nearest sliver)',
      not MC.auto_confirm_ok('US-9003', fresh, {'sgzzc1': SLIVER, 'sgzzc2': BIG}, f_out, pin=pin_out)
      and MC.held_in_pass('US-9003', fresh, {'sgzzc1': SLIVER, 'sgzzc2': BIG}, pin_out) == '')
f_in = {'US-9003': {'name': fresh['n'], 'pin': [44.525, -88.475]}}
check('a fresh pass (no held / bk) with the pin inside the big outline: held name and pin confirms it',
      MC.auto_confirm_ok('US-9003', fresh, {'sgzzc1': SLIVER, 'sgzzc2': BIG}, f_in, pin=[44.525, -88.475])
      and MC.held_in_pass('US-9003', fresh, {'sgzzc1': SLIVER, 'sgzzc2': BIG}, [44.525, -88.475]) == 'sgzzc2')
check("the builder's explicit no is final in a fresh pass: no held record, nothing confirmed",
      not MC.auto_confirm_ok('US-9003', fresh, {'sgzzc1': SLIVER, 'sgzzc2': BIG}, f_in, pin=[44.525, -88.475], holds_fn=lambda r, i: False))
src = (ROOT / '.github/scripts/kpc_match_checks.py').read_text(encoding='utf-8')
check('the witness only confirms, through the auto-confirm gate, after it',
      "st_, how = 'confirmed', 'page names the land'" in src and 'NEAR_LAND_KM' not in src
      and src.index("'held name and pin'") < src.index("st_, how = 'confirmed', 'page names the land'"))
check('the auto-confirm held-name test also reads the spelling table', 'names_match(pn, rn, spelling) or same_place_name(pn, rn)' in src)
import json as _j
stops = _j.loads((ROOT / '.github/auto-confirm-stops.json').read_text(encoding='utf-8'))
check('the stop list is IDs only and is read by default', all(str(x).startswith(('US-', 'CA-')) for x in stops['parks'])
      and MC.load_auto_confirm_stops()[0] == set(stops['parks']))
import kpc_key_freeze as KF
check('the stop list is a US rule file (in the hash)', '.github/auto-confirm-stops.json' in KF.RULE_FILES['us-key'])
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
