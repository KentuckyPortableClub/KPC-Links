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
src = (ROOT / '.github/scripts/kpc_match_checks.py').read_text(encoding='utf-8')
check('the witness only confirms: it sits in the status ladder, after W4, and moves no land',
      "st_, how = 'confirmed', 'page names the land'" in src and src.index("'page name and point'") < src.index("st_, how = 'confirmed', 'page names the land'"))
check('the place test is in or within NEAR_LAND_KM (1 km) of the land', MC.NEAR_LAND_KM == 1.0 and 'pin_near(str(q[0]))' in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
