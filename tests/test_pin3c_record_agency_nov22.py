#!/usr/bin/env python3
"""Place check 3c and the agency check, fixed after the owner's PC test (KPC owner, 22 Nov 2026). Invented names only. Offline.

Fix 1 (pin_3c): a record that does not hold POTA's pin stays when its name, with the kind words of KINDS left out (after full()),
is the bare name of a record that holds the pin or of the park's own POTA name, or differs from one only by a piece word
(Addition, Unit, Tract, Parcel, Annex, Extension, North / South / East / West, a number). 'One name holds the other' and a
different name stay a check (the Texas cases: a Corps lake 'Test Lake' for 'Lake Test State Park'; 'Lake Test Lands').
Fix 2 (record_agency): a compilation layer (D11 'what' = compilation, the layers D7 reads) gives no agency vote unless the record
carries its own manager field; the agency never comes from the record's name. A same-name WMA or refuge on such a layer still
never stays with a state park (F3 at the name join; the kind clash in the pass), and the refuge's own record still joins the refuge.

Florida (owner's yes, 8:28 PM): the FL layers listing several agencies' land carry D11 'compilation', so a refuge's own record
there is no longer pulled as 'another agency'.

Fails without the fixes: on main, 'Test Lake', 'Ft. Test' and 'Test Lake Addition' go to check by place, the refuge's own record
on a compilation layer goes to check by agency, and a same-name WMA / refuge on a compilation layer stays with the state park.

Run: python3 -B tests/test_pin3c_record_agency_nov22.py
"""
import os, pathlib, socket, sys, types
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
os.chdir(ROOT)


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402

STOP = '\nidx = {}\n'
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
if STOP not in src:
    raise SystemExit('kpc_us_key.py: stop marker not found')
US = types.ModuleType('kpc_us_key_t')
US.__dict__['__file__'] = str(ROOT / '.github/scripts/kpc_us_key.py')
exec(compile(src.split(STOP)[0], 'kpc_us_key.py', 'exec'), US.__dict__)

FAILS = []


def check(ok, what):
    if callable(ok):
        try: ok = ok()
        except Exception as e:  # noqa: BLE001  (on main the helper is missing: a FAIL line, not a crash)
            what += f' [{type(e).__name__}: {e}]'; ok = False
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok:
        FAILS.append(what)


TABLE = {'sgzza': {'agency': 'state parks', 'kind': 'park'},
         'sgzzc': {'agency': 'state parks and wildlife', 'kind': 'unknown', 'what': 'compilation'},
         'fws': {'agency': 'FWS', 'kind': 'refuge'}}
STATE_LINK = {'site': 'agency (known)', 'agency': 'ZZ State Parks', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1}
FWS_LINK = dict(STATE_LINK, agency='US Fish and Wildlife Service')


def fact(name, link):
    return {'area': 'US-ZZ', 'name': name, 'type': 'State Park', 'pin': [40.05, -79.95], 'link': link}


def rec(oid, name):
    return {'OBJECTID': oid, 'Unit_Nm': name, 'Loc_Nm': '', 'Mang_Type': 'STAT', 'Mang_Name': oid[:5].upper(), 'GIS_Acres': 100}


def run(name, rows, recs, link=STATE_LINK, held=()):
    p = {'US-9001': {'n': name, 't': 'State Park', 'm': [list(r) for r in rows], 'c': [], 'g': 'official'}}
    MC.pass_state(p, recs, {'US-9001': fact(name, link)}, lambda ref, ids: True, st='ZZ', units={},
                  holds_fn=(lambda ref, i: i in held) if held else None, layer_table=TABLE)
    return p['US-9001']


def kept(p): return sorted(str(q[0]) for q in p.get('m') or [])
def checked(p): return {str(q[0]): q[3] for q in p.get('c') or []}


# ---------- Fix 1: place check 3c ----------
R = [['sgzza1', 'Test Lake State Park', 900, 'name'], ['sgzza2', 'Test Lake', 300, 'name'],
     ['sgzza3', 'Test Lake Addition', 40, 'name'], ['sgzza4', 'Test Lake State Park Addition', 30, 'name'],
     ['sgzza5', 'Test Lake Unit 2', 20, 'name']]
p = run('Test Lake State Park', R, {r[0]: rec(r[0], r[1]) for r in R}, held={'sgzza1'})
check(kept(p) == ['sgzza1', 'sgzza2', 'sgzza3', 'sgzza4', 'sgzza5'],
      "3c keeps 'Test Lake', 'Test Lake Addition', '... State Park Addition' and 'Test Lake Unit 2' beside the pin's 'Test Lake State Park'")
R = [['sgzza1', 'Invented Tract 7', 900, 'name'], ['sgzza2', 'Ft. Test', 300, 'name']]
p = run('Fort Test State Park', R, {r[0]: rec(r[0], r[1]) for r in R}, held={'sgzza1'})
check('sgzza2' in kept(p), "3c keeps 'Ft. Test' by the park's own POTA name 'Fort Test State Park' (the pin's record has another name)")
R = [['sgzza1', 'Lake Test State Park', 900, 'name'], ['sgzza2', 'Test Lake', 300, 'name'], ['sgzza3', 'Lake Test Lands', 200, 'name']]
p = run('Lake Test State Park', R, {r[0]: rec(r[0], r[1]) for r in R}, held={'sgzza1'})
c = checked(p)
check(kept(p) == ['sgzza1'] and all(c.get(i, '').startswith('check (place') for i in ('sgzza2', 'sgzza3')),
      "3c still checks the Texas-style other land: a Corps lake 'Test Lake' and 'Lake Test Lands' for 'Lake Test State Park'")
R = [['sgzza1', 'Test State Park', 900, 'name'], ['sgzza2', 'Lake Test Park', 100, 'name']]
p = run('Test State Park', R, {r[0]: rec(r[0], r[1]) for r in R}, held={'sgzza1'})
check(kept(p) == ['sgzza1'] and checked(p).get('sgzza2', '').startswith('check (place'),
      "3c still checks 'one name holds the other' ('Lake Test Park' for 'Test State Park')")
check(lambda: not MC.same_bare('Test Creek WMA', 'Test Creek State Park') and not MC.same_bare('Test Creek NWR', 'Test Creek State Park'),
      '3c never takes two kinds of place for one park (WMA or refuge against a state park)')
check(lambda: MC.bare_name('Test Lake State Recreation Area') == 'test lake' and MC.bare_name('Test Creek NWR') == 'test creek',
      'the bare name drops the kind words of KINDS after full() writes the short forms out')
check(not hasattr(MC, 'TYPE_WORDS'), 'one kind list: 3c builds on KINDS / SHORT / full(), no second word list')

# ---------- Fix 2: agency on a compilation layer ----------
check(MC.record_agency({'OBJECTID': 'sgzzc1', 'Unit_Nm': 'Test Creek National Wildlife Refuge'}, TABLE) is None,
      'a compilation layer gives no agency vote (None), and never from the record\'s name')
check(MC.record_agency({'OBJECTID': 'sgzzc1', 'SA': {'MANAGER': 'US Fish and Wildlife Service'}}, TABLE) == 'FWS'
      and MC.record_agency({'OBJECTID': 'sgzzc1', 'manager': 'ZZ Department of Natural Resources'}, TABLE) == 'STATE',
      "a compilation record's OWN manager field is read (saved source field or the keeper's 'manager')")
check(MC.record_agency({'OBJECTID': 'sgzzc1', 'SA': {'OWNER': 'FWS'}}, TABLE) is None, 'an owner field is not a manager field')
check(MC.record_agency({'OBJECTID': 'sgzza1'}, TABLE) == 'STATE', "a layer that is not a compilation still votes by the layer table")
import json  # noqa: E402
LT = json.loads((ROOT / '.github/layer-agency-kind.json').read_text(encoding='utf-8'))['layers']
check(LT.get('sgtxd', {}).get('what') == 'compilation' and 'what' not in LT.get('sgfla', {}),
      "the club's layer table marks the layers D11 labels 'compilation' (a conservation-lands list), not an agency's own layer")
R = [['sgzzc1', 'Test Creek National Wildlife Refuge', 900, 'name']]
p = run('Test Creek National Wildlife Refuge', R, {'sgzzc1': rec('sgzzc1', R[0][1])}, link=FWS_LINK)
check(kept(p) == ['sgzzc1'], "the refuge's own record on a compilation layer stays with the refuge (it was pulled as 'another agency')")
r_ = rec('sgzzc1', R[0][1]); r_['SA'] = {'MANAGER': 'ZZ Department of Natural Resources'}
p = run('Test Creek National Wildlife Refuge', R, {'sgzzc1': r_}, link=FWS_LINK)
check(checked(p).get('sgzzc1', '').startswith('check (agency'), "a compilation record whose own manager field is another agency still goes to check")

# ---------- Florida (owner's yes, 22 Nov 2026 8:28 PM): the FL layers that list several agencies' land are compilations ----------
check(sorted(k for k, v in LT.items() if k.startswith('sgfl') and v.get('what') == 'compilation') == ['sgfld', 'sgfle', 'sgflf'],
      "the FL layers that list several agencies' land (two water-district layers, state-owned lands) are marked; parks, forests, WMAs are not")
R = [['sgfld1', 'Test Key National Wildlife Refuge', 900, 'name']]
p = {'US-9001': {'n': 'Test Key National Wildlife Refuge', 't': 'National Wildlife Refuge', 'm': [list(r) for r in R], 'c': [], 'g': 'official'}}
MC.pass_state(p, {'sgfld1': rec('sgfld1', R[0][1])}, {'US-9001': dict(fact(R[0][1], FWS_LINK), area='US-FL')},
              lambda ref, ids: True, st='FL', units={}, layer_table=LT)
check(kept(p['US-9001']) == ['sgfld1'] and not checked(p['US-9001']),
      "a refuge's own record on an FL compilation layer is no longer pulled as 'another agency'")
r_ = rec('sgfla1', 'Test Key National Wildlife Refuge')
check(MC.agency_check(dict(fact('x', FWS_LINK), area='US-FL'), r_, 'FL', LT) == 'differs',
      "an FL agency's own layer (state parks) still votes: a refuge-named record there still differs from a refuge link")

# ---------- the owner's guard: same-name WMA / refuge on a compilation layer never stays with a state park ----------
for nm in ('Test Creek WMA', 'Test Creek NWR'):
    a = {'OBJECTID': 'sgzzc1', 'Unit_Nm': nm, 'Loc_Nm': '', '_k': US.kinds(nm), 'Mang_Type': 'STAT'}
    check(not US.join_how('Test Creek State Park', US.kinds('Test Creek State Park'), a, True),
          f"F3 still refuses the name join of a compilation record '{nm}' to 'Test Creek State Park'")
    R = [['sgzza1', 'Test Creek State Park', 900, 'name'], ['sgzzc1', nm, 300, 'name']]
    p = run('Test Creek State Park', R, {r[0]: rec(r[0], r[1]) for r in R})
    check(kept(p) == ['sgzza1'] and checked(p).get('sgzzc1', '').startswith('check (kind'),
          f"a compilation record '{nm}' that reached the pass goes to check by kind, not kept for 'Test Creek State Park'")
a = {'OBJECTID': 'sgzzc1', 'Unit_Nm': 'Test Creek NWR', 'Loc_Nm': '', '_k': US.kinds('Test Creek NWR'), 'Mang_Type': 'STAT'}
check(bool(US.join_how('Test Creek National Wildlife Refuge', US.kinds('Test Creek National Wildlife Refuge'), a, True)),
      "the refuge's own compilation record 'Test Creek NWR' still name-joins 'Test Creek National Wildlife Refuge'")
R = [['sgzzc1', 'Test Creek WMA', 300, 'name']]
p = run('Test Creek National Wildlife Refuge', R, {'sgzzc1': rec('sgzzc1', 'Test Creek WMA')}, link=FWS_LINK)
check(checked(p).get('sgzzc1', '').startswith('check (kind'), "a compilation 'Test Creek WMA' does not stay with the refuge either")

print('ALL PASS' if not FAILS else f'{len(FAILS)} FAIL: ' + ' | '.join(FAILS))
sys.exit(1 if FAILS else 0)
