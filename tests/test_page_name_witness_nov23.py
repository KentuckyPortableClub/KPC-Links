#!/usr/bin/env python3
"""23 Nov 2026, owner's rulings W-G4 ("Yes I think so") and W-G5 ("Yes"), 12:51 AM: the park's OWN page on an official site
carries the park's own name -> the joined park is confirmed when POTA's pin lies in the joined record ('page name'), or when
the page's own point does ('page name and point'). The page reader's name check decides the name (same, same core, or the
same words with another kind). A page that names another place, a list page, a shared page or an unofficial site confirms
nothing. It confirms only: no piece is joined, moved or dropped. Invented parks and records only. No network."""
import pathlib, socket, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


SQ = lambda x0, y0: {'type': 'Polygon', 'coordinates': [[[x0, y0], [x0 + .1, y0], [x0 + .1, y0 + .1], [x0, y0 + .1], [x0, y0]]]}
TABLE = {'sgzza': {'agency': 'state parks', 'kind': 'park'}}
# the park's own page on an agency site whose web address does NOT carry the park's name (so the link alone confirms nothing)
LINK = {'site': 'agency (known)', 'agency': 'ZZ State Parks', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1,
        'web_name': 'unit 4471', 'name_match': 'none'}


def run(name_vs, own='own', unofficial=False, pin_inside=True, coords=(), link=LINK, page_name='Otter Branch Fishery Area'):
    recs = {'sgzza1': {'OBJECTID': 'sgzza1', 'Unit_Nm': 'Otter Branch State Fish and Wildlife Area', 'Mang_Type': 'STAT', 'Mang_Name': 'SPR',
                       'GIS_Acres': 500, '_g': SQ(-80.0, 40.0), '_bb': [-80.0, 40.0, -79.9, 40.1]}}
    parks = {'US-9001': {'n': 'Otter Branch State Fish and Wildlife Area', 't': 'State Fish and Wildlife Area', 'g': 'official', 'c': [],
                         'm': [['sgzza1', 'Otter Branch State Fish and Wildlife Area', 500, 'same name']]}}
    f = {'US-9001': {'area': 'US-ZZ', 'name': 'Otter Branch State Fish and Wildlife Area', 'type': 'State Fish and Wildlife Area', 'pin': [40.05, -79.95],
                     'page': {'kind': 'html', 'own_page': own, 'unofficial': unofficial, 'host': 'dnr.zz.example.gov', 'name_vs_pota': name_vs,
                              'name_on_page': page_name, 'sizes': [], 'coords': list(coords), 'parts': [], 'inside_of': []}}}
    if link is not None: f['US-9001']['link'] = dict(link)
    in_rec = lambda la, lo: -80.0 <= lo <= -79.9 and 40.0 <= la <= 40.1
    page_holds = lambda ref, i: any(in_rec(la, lo) for la, lo in MC.page_pins(f[ref]))
    MC.pass_state(parks, recs, f, lambda ref, ids: pin_inside, st='ZZ', holds_fn=lambda ref, i: pin_inside, layer_table=TABLE, page_holds_fn=page_holds,
                  auto_confirm_stops={'US-9001'})   # 24 Nov: W4 alone (the held name and pin here would auto-confirm)
    p = parks['US-9001']
    return (p.get('match') or {}).get('status'), (p.get('match') or {}).get('by'), [q[0] for q in p.get('m') or []], len(p.get('c') or [])


check('has the page-name witness', hasattr(MC, 'page_name_agrees'))
for nv in ('same', 'same-core', 'same-words'):
    check(f'the page carries the park\'s name ({nv}) and the pin is inside: confirmed by page name', run(nv)[:2] == ('confirmed', 'page name'))
check('nothing is joined, moved or dropped by it', run('same')[2:] == (['sgzza1'], 0))
# 24 Nov: a page heading that names the joined land itself now confirms ('page names the land'), so these two use another place's name
check('the page names another place: not confirmed', run('differs', page_name='Beaver Pond Lake')[0] == 'outlined')
check('no name read from the page: not confirmed', run(None, page_name='')[0] == 'outlined')
check('a list page: not confirmed', run('same', own='list')[0] == 'outlined')
check('a shared page: not confirmed', run('same', own='shared')[0] == 'outlined')
check('an unofficial site: not confirmed', run('same', unofficial=True)[0] == 'outlined')
check('a site the link tool does not know as official: not confirmed', run('same', link=dict(LINK, site='other site'))[0] == 'outlined')
check('the pin is not in the record and the page gives no point: not confirmed', run('same', pin_inside=False)[0] == 'outlined')
check("the pin is not in the record but the page's own point is: confirmed by page name and point",
      run('same', pin_inside=False, coords=[{'lat': 40.05, 'lon': -79.95, 'role': 'park'}])[:2] == ('confirmed', 'page name and point'))
check("an office point never stands in for the page's point", run('same', pin_inside=False, coords=[{'lat': 40.05, 'lon': -79.95, 'role': 'office'}])[0] == 'outlined')
check('POTA lists no link (no link fact at all), the reader read the own official page: the name still confirms', run('same', link=None)[:2] == ('confirmed', 'page name'))
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
