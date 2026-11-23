#!/usr/bin/env python3
"""Job 8, 23 Nov 2026 (owner 2:12 PM, approving the outside agent's count; 4:43 PM "Do it"): the US proofs on the Canada key.
Canada joins by name alone. kpc_match_checks.canada_pass confirms a joined park by the agency's own size, POTA's link naming it
with the pin in or by the land, the link and a page point inside it, or the park's own page carrying its name (with the pin
in or by the land, or a page point inside it). The size check is the one that moves: name-joined rows 3 times off the agency's
own figure go to the check list. Nothing else runs here. Invented parks; no network. Prints PASS / FAIL."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_match_checks as MC  # noqa: E402
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


check('the Canada pass exists', hasattr(MC, 'canada_pass'))
LINK_OK = {'site': 'agency (known)', 'usable': True, 'page_kind': 'own page', 'shared_by': 1, 'name_match': 'strong'}


def run(rows, fact, place=None, page=None):
    parks = {'CA-9001': {'n': 'Otter Lake Provincial Park', 't': 'Provincial Park', 'm': [list(r) for r in rows], 'c': []}}
    out = MC.canada_pass(parks, {}, {'CA-9001': fact}, lambda ref, ids: place, (lambda ref, i: page) if page is not None else None)
    return parks['CA-9001'], out


ROW = ['ON:1', 'Otter Lake Provincial Park', 500, 'name · CPCAD']
p, out = run([ROW], {'link': dict(LINK_OK), 'page': {}}, place=True)
check("POTA's link names the park and the pin is in the land: confirmed by link", p['match'] == {'status': 'confirmed', 'why': [], 'by': 'link'})
p, _ = run([ROW], {'link': dict(LINK_OK), 'page': {}}, place=False)
check('the link alone, the pin away from the land: outlined, nothing moved', p['match']['status'] == 'outlined' and p['m'] == [ROW])
p, _ = run([ROW], {'link': {}, 'page': {'own_page': 'own', 'name_vs_pota': 'same', 'host': 'ontarioparks.ca'}}, place=True)
check("the park's own page carries its name and the pin is in the land: confirmed by page name", p['match'].get('by') == 'page name')
p, _ = run([ROW], {'link': {}, 'page': {'own_page': 'own', 'name_vs_pota': 'same', 'host': 'ontarioparks.ca'}}, place=False, page=True)
check("... or a point on that page is inside the land: page name and point", p['match'].get('by') == 'page name and point')
SIZE = {'acres': 510, 'witness': 'agency_document', 'total': True, 'clean': True}
p, _ = run([ROW], {'size': dict(SIZE), 'link': {}, 'page': {}})
check("the agency's own size agrees: confirmed by size", p['match'].get('by') == 'size')
p, out = run([ROW], {'size': dict(SIZE, acres=5000), 'link': {}, 'page': {}})
check('the outline is 3 times off the agency\'s own figure: the name join goes to the check list, the park shows its pin',
      p['m'] == [] and p['c'][0][3].startswith("check (size: the outline is") and p['match']['status'] == 'pin' and out['moved'] == 1)
REVIEWED = ['ON:2', 'Otter Lake Provincial Park', 500, 'reviewed']
p, _ = run([REVIEWED], {'size': dict(SIZE, acres=5000), 'link': {}, 'page': {}})
check("a person's join is never moved by the size check", p['m'] == [REVIEWED])
p, _ = run([ROW], {'link': {}, 'page': {}})
check('no proof: outlined, nothing moved', p['match']['status'] == 'outlined' and p['m'] == [ROW])
parks = {'CA-9002': {'n': 'X', 't': 'Park', 'm': [], 'c': [['ON:3', 'X', 1, 'similar name']]}}
MC.canada_pass(parks, {}, {}, lambda r, i: None)
check('a park with no join is not touched', 'match' not in parks['CA-9002'])
src = (ROOT / '.github/scripts/kpc_ca_key.py').read_text(encoding='utf-8')
check('the Canada builder runs it on each province', 'MC.canada_pass(parks' in src)
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_freeze as F  # noqa: E402
check('the match checks are a Canada rule file (a change moves the Canada rules number)', '.github/scripts/kpc_match_checks.py' in F.RULE_FILES['ca-key'])
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
