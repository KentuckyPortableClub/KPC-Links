#!/usr/bin/env python3
"""25 Nov 2026 (KPC owner, 6:20 + 6:28 AM: 'a better matcher', 'proof or the pin, no hand-offs'): a key record takes the
outline store's id fields only from the fresh store record PROVEN to be the same land (agency id, shared ground, a piece, name
and size; never the row number), and after the match checks a row draws only with proof. Runs the REAL key code (the helper
part of kpc_us_key, as the other store-id tests do). Invented records. Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, math, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
import kpc_match_checks as MC  # noqa: E402
import kpc_source_fields as SF  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


for f in ('kpc_same_land.py', 'kpc_store_attrs.py'):
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts' / f), '--selftest'], capture_output=True, text=True)
    check(f'{f} self-test', 'ALL PASS' in r.stdout)

src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
start = src.index('RA_USED = {}'); end = src.index('\ndef _maiden6')
ns = {'os': os, 're': re, 'json': json, 'gzip': gzip, 'math': math, 'KR': KR, 'MC': MC, 'SF': SF, 'OVR': {}, 'notice': lambda *a: None}
exec(src[start:end], ns)


def sq(x, y, d):
    return [[[x, y], [x + d, y], [x + d, y + d], [x, y + d], [x, y]]]


# the MN case: the store read numbers Lost Valley Prairie 210; the key's older copy has it as 55, and its 210 is other land
lost_store = {'pgrm_project': 'SNA01041', '_nm': 'Lost Valley Prairie', '_ac': 319.49, '_bx': [-92.83, 44.80, -92.82, 44.81], '_g': sq(-92.83, 44.80, 0.01)}
ns['_RA'][0] = {}
ns['_RA_RF'][0] = {'sgmnc210': lost_store,
                   'sgmne7': {'su_id': 900, '_nm': 'SCHOOLCRAFT', '_bx': [-94.0, 47.0, -93.99, 47.01], '_g': sq(-94.0, 47.0, 0.01)}}
slf = ns['same_land_fields']
key55 = {'OBJECTID': 'sgmnc55', 'Unit_Nm': 'Lost Valley Prairie', 'GIS_Acres': 319.49, '_g': {'rings': sq(-92.8301, 44.8001, 0.01)}}
key210 = {'OBJECTID': 'sgmnc210', 'Unit_Nm': 'Crystal Spring', 'GIS_Acres': 40, '_g': {'rings': sq(-92.70, 44.70, 0.003)}}
check('the renumbered record finds its fresh twin by shared ground, with the agency id',
      slf('sgmnc55', key55) == ('overlap', {'pgrm_project': 'SNA01041'}))
check("the key's record 210 is other land: it never takes record 210's fields (the number proves nothing)", slf('sgmnc210', key210)[0] == 'none')
same_place_other_id = {'OBJECTID': 'sgmne3', 'Unit_Nm': 'SCHOOLCRAFT', 'SA': {'su_id': 555}, '_g': {'rings': sq(-94.0, 47.0, 0.01)}}
orig_keep = SF.keep_fields
SF.keep_fields = lambda lay, fields=None, path=None: ['su_id'] if lay == 'sgmne' else []
check('a fresh record with ANOTHER agency id on the same ground: conflict, no fields', slf('sgmne3', same_place_other_id) == ('conflict', None))
check('the same agency id: proven by id', slf('sgmne3', dict(same_place_other_id, SA={'su_id': '900.0'}))[0] == 'id')
SF.keep_fields = orig_keep
check('no store record of the layer near it: none', slf('sgzza1', {'OBJECTID': 'sgzza1', 'Unit_Nm': 'X', '_g': {'rings': sq(-80, 40, 0.01)}}) == ('none', None))

# the gate: proof or the pin
gate = ns['proven_only_gate']
ns['SAME_STATE'].clear(); ns['SAME_STATE'].update({'sg1': 'overlap', 'sg2': 'conflict'})
byid = {'sg1': {'OBJECTID': 'sg1', 'Unit_Nm': 'Alpha WMA', 'GIS_Acres': 100}, 'sg2': {'OBJECTID': 'sg2', 'Unit_Nm': 'Beta WMA', 'GIS_Acres': 50},
        'sg3': {'OBJECTID': 'sg3', 'Unit_Nm': 'Gamma Forest', 'GIS_Acres': 900}, 'sg4': {'OBJECTID': 'sg4', 'Unit_Nm': 'Delta Lake', 'GIS_Acres': 20},
        'sg5': {'OBJECTID': 'sg5', 'Unit_Nm': 'Echo Marsh', 'GIS_Acres': 70}}
ns['OVR'].update({'K-3': {'join': ['sg3'], 'fp': {'sg3': ['Gamma Forest', 880]}},
                  'K-4': {'join': ['sg4'], 'fp': {'sg4': ['Old Name Tract', 20]}},
                  'K-5': {'join': ['sg5'], 'no': ['sg2']}})
parks = {'K-1': {'m': [['sg1', 'Alpha WMA', 100, 'name']], 'match': {'status': 'outlined'}, 'g': 'official'},
         'K-2': {'m': [['sg1', 'Alpha WMA', 100, 'name'], ['sg2', 'Beta WMA', 50, 'name']], 'match': {'status': 'confirmed', 'by': 'id'}, 'g': 'official'},
         'K-3': {'m': [['sg3', 'Gamma Forest', 900, 'reviewed']], 'match': {'status': 'outlined'}, 'g': 'official'},
         'K-4': {'m': [['sg4', 'Delta Lake', 20, 'reviewed']], 'match': {'status': 'confirmed', 'by': 'size'}, 'g': 'official'},
         'K-5': {'m': [['sg5', 'Echo Marsh', 70, 'reviewed']], 'match': {'status': 'outlined'}, 'g': 'official'},
         'K-6': {'m': [['nps1', 'Foxtrot NM', 10, 'NPS unit code']], 'match': {'status': 'outlined'}, 'g': 'official'},
         'K-7': {'m': [['sg1', 'Alpha WMA', 100, 'name']], 'match': {'status': 'outlined'}, 'g': 'official'}}
res = gate('ZZ', parks, byid, skip={'K-7'})
check('an outlined park with a name row only: pin only, the row marked for the code to fix',
      parks['K-1']['m'] == [] and parks['K-1']['g'] == 'pin' and parks['K-1']['match']['status'] == 'pin'
      and parks['K-1']['c'][0][3].startswith('check (code to fix: not proven'))
check('a confirmed park keeps its proven row and loses the one a fresh record with another agency id holds',
      [q[0] for q in parks['K-2']['m']] == ['sg1'] and 'different agency id' in parks['K-2']['c'][0][3])
check("a person's join whose fingerprint still fits draws (even on an outlined park)", [q[0] for q in parks['K-3']['m']] == ['sg3'])
check("a person's join whose fingerprint no longer fits never draws (other land holds the number)",
      parks['K-4']['m'] == [] and "other land holds this record number" in parks['K-4']['c'][0][3])
check("a person's join with no fingerprint on an unproven park: pin, and listed for the owner",
      parks['K-5']['m'] == [] and any(x[1:4] == ['K-5', 'join', 'sg5'] for x in ns['FP_PROPOSALS']))
check('a NO with no fingerprint is still applied and listed for the owner', any(x[1:4] == ['K-5', 'no', 'sg2'] for x in ns['FP_PROPOSALS']))
check('a code row (Park Service unit code) stays', [q[0] for q in parks['K-6']['m']] == ['nps1'])
check('a park the gate skips (official trail line) is left alone', parks['K-7']['m'] and parks['K-7']['g'] == 'official')
check('the counts', res['rows'] == 4 and res['parks'] == 4 and res['pin_now'] == 3)

# switches: MN and NY only (the owner's test order); never Kentucky yet
for sw in ('KPC_SAME_LAND', 'KPC_PROVEN_ONLY'):
    check(f'{sw}: on for MN and NY, off for KY and OH', KR.on(sw, area='MN') and KR.on(sw, area='NY') and not KR.on(sw, area='KY') and not KR.on(sw, area='OH'))
import kpc_key_freeze as KF  # noqa: E402
check('kpc_same_land.py is a US rule file (it moves the US hash)', '.github/scripts/kpc_same_land.py' in KF.RULE_FILES['us-key'])
check('the one line per state: by agency id, by shared ground, pieces, by name and size, not proven',
      all(w in src for w in ("by agency id {_sh.get('id', 0)}", "by shared ground", "by name and size", "not proven {_sh.get('unproven', 0)}", 'now pin only')))
kt = (ROOT / 'tools/pc-keys/kpc_test_keys.py').read_text(encoding='utf-8')
check('the PC test remakes its id file before format 6 and saves the owner list', 'fmt < 6' in kt and 'saved-answers-no-fingerprint.csv' in kt)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
