#!/usr/bin/env python3
"""D1 on a person's own rows (KPC owner, 2026-11-17): a saved join / NO is the LAND (name + acres), not the number."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '.github' / 'scripts'))
import kpc_key_rules as KR

def rec(i, n, a): return {'OBJECTID': i, 'Unit_Nm': n, 'GIS_Acres': a}
R = [rec(100, 'Other Place', 50), rec(200, 'Elk Lake WMA', 1000), rec(101, 'Elk Lake WMA', 1010), rec(300, 'Fox SP', 80), rec(301, 'Big River', 500)]
BY = {str(a['OBJECTID']): a for a in R}
def rf(old, nm, ac): return [a for a in R if a['Unit_Nm'] == nm]
fails = 0
def ck(c, msg):
    global fails
    print(('ok   ' if c else 'FAIL ') + msg); fails += not c

# 1. join id 100 saved as Elk Lake WMA 1000 ac; 100 now holds 'Other Place' -> moves to the ONE same name + acres? two hits (200, 101) -> lost
ov = {'join': [100], 'fp': {'100': ['Elk Lake WMA', 1000]}}
n, notes = KR.saved_land_moves(ov, BY, rf)
ck(notes and notes[0][0] == 'join check' and n['join'] == [100] and ov['join'] == [100], 'two same-name hits = not sure: the join stays and goes to check')
# 2. one hit -> moves
def rf1(old, nm, ac): return [a for a in R if a['Unit_Nm'] == nm and a['OBJECTID'] == 101]
n, notes = KR.saved_land_moves(ov, BY, rf1)
ck(n['join'] == [101] and '101' in n['fp'] and '100' not in n['fp'] and notes[0][0] == 'join moved', 'one same name + acres in the layer: the join moves')
# 3. a record that still fits is left alone
n, notes = KR.saved_land_moves({'join': [300], 'fp': {'300': ['Fox SP', 82]}}, BY, rf)
ck(not notes and n['join'] == [300], 'a row that still fits is not touched')
# 4. a gone id is not this rule's job
n, notes = KR.saved_land_moves({'join': [999], 'fp': {'999': ['Fox SP', 80]}}, BY, rf)
ck(not notes and n['join'] == [999], 'a gone id keeps the old re-find path')
# 5. a NO moves with its land
n, notes = KR.saved_land_moves({'no': [100], 'nofp': {'100': ['Big River', 500]}}, BY, rf)
ck(n['no'] == [301] and notes[0][0] == 'no moved', 'a NO moves to its land (the NO is the land)')
# 6. a NO whose land is not found stays
n, notes = KR.saved_land_moves({'no': [100], 'nofp': {'100': ['Gone River', 500]}}, BY, rf)
ck(n['no'] == [100] and notes[0][0] == 'no kept', 'a NO whose land is not found again stays (a person looks)')
# 7. a join never moves onto a record the person said NO to
n, notes = KR.saved_land_moves({'join': [100], 'fp': {'100': ['Elk Lake WMA', 1000]}, 'no': [101]}, BY, rf1)
ck(n['join'] == [100] and notes[0][0] == 'join check', 'a join never moves onto a NO record')
# 8. acres more than 10% off = other land
n, notes = KR.saved_land_moves({'join': [300], 'fp': {'300': ['Fox SP', 400]}}, BY, lambda o, nm, ac: [])
ck(notes and notes[0][0] == 'join check', 'same name, acres 5x off = other land: check')
n, notes = KR.saved_land_moves({'join': [7]}, {'7': {'OBJECTID': 7, 'Unit_Nm': 'FW 49 - Tract (Holland WMA)', 'Loc_Nm': 'Holland WMA', 'GIS_Acres': 10}}, rf) if False else (None, [])
n, notes = KR.saved_land_moves({'join': [7], 'fp': {'7': ['Holland WMA', 10]}}, {'7': {'OBJECTID': 7, 'Unit_Nm': 'FW 49 - Tract (Holland WMA)', 'Loc_Nm': 'Holland WMA', 'GIS_Acres': 10}}, rf)
ck(not notes, 'the saved name on the second name field still fits')
# 10. Ohio: the first name is a code, the key shows 'second (first)'
oh = {'OBJECTID': 'sgoha26', 'Unit_Nm': 'CaesarCrkSP', 'Loc_Nm': 'CAESAR CREEK', 'GIS_Acres': 6953}
ck(KR.saved_row_ok(['sgoha26', 'CAESAR CREEK (CaesarCrkSP)', 6953], oh) and KR.saved_row_ok(['sgoha26', 'CAESAR CREEK', 6953], oh)
   and not KR.saved_row_ok(['sgoha26', 'Hueston Woods', 6953], oh), "Ohio's shown name 'CAESAR CREEK (CaesarCrkSP)' still fits its record")
# 9. the switch is listed OFF
import json
sw = json.load(open(pathlib.Path(__file__).resolve().parents[1] / '.github' / 'key-switches.json'))
ck(KR.DEFAULTS.get('KPC_SAVED_ID_LAND') == '0', 'KPC_SAVED_ID_LAND is OFF by default')
print('FAILED' if fails else 'ALL PASS'); sys.exit(1 if fails else 0)
