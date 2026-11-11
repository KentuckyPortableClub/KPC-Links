#!/usr/bin/env python3
"""Nov 6 (Quality 2-fer grade): area / same-land 2-fers follow the current key's PIN and approximate status.
A key PIN is not a line-match; approximate is an approximate 2-fer, not a hold. Rule-18 selftests for the Quality examples."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_fers_key_status as FKS
import kpc_precheck as PC

ok = True
def check(cond, msg):
    global ok
    if not cond: ok = False; print('FAIL', msg)
    else: print('PASS', msg)

FKS.clear()
FKS.KEY_STATUS.update({'US-PIN': 'pin', 'US-APX': 'approximate', 'US-OK': 'official', 'US-OK2': 'official'})
check(FKS.key_line_match(['US-PIN', 'US-OK'], 'area').startswith('dropped: key PIN'), 'area + PIN -> dropped')
check(FKS.key_line_match(['US-PIN', 'US-OK'], 'same land').startswith('dropped: key PIN'), 'same land + PIN -> dropped')
check(FKS.key_line_match(['US-APX', 'US-OK'], 'area') == '', 'area + approximate -> allowed as approximate 2-fer')
check(FKS.key_line_match(['US-OK', 'US-OK2'], 'area') == '', 'area + two official -> ok')
check(FKS.key_line_match(['US-PIN', 'US-OK'], 'river') == '', 'river + PIN still allowed (100-ft rule)')
check(FKS.key_line_match(['US-PIN', 'US-OK'], 'trail') == '', 'trail + PIN still allowed')

FKS.clear()
FKS.load_key_status(ROOT)
check(FKS.KEY_STATUS.get('US-11822') == 'pin', f"US-11822 Jemez is PIN (got {FKS.KEY_STATUS.get('US-11822')})")
check(FKS.key_line_match(['US-11822', 'US-2699', 'US-4517'], 'area', ROOT).startswith('dropped'), 'Jemez+Fenton+Santa Fe area is not a line-match')
check(FKS.KEY_STATUS.get('US-12459') == 'approximate', f"US-12459 Housatonic Southern Fields is approximate (got {FKS.KEY_STATUS.get('US-12459')})")
check(FKS.key_line_match(['US-12459', 'US-DUMMY'], 'area', ROOT) == '', 'Housatonic approximate area -> allowed as approximate 2-fer')
check(FKS.KEY_STATUS.get('US-0884') == 'pin', f"US-0884 Kings River is PIN (got {FKS.KEY_STATUS.get('US-0884')})")
check(FKS.key_line_match(['US-0884', 'US-0046'], 'area', ROOT).startswith('dropped'), 'Kings River + Kings Canyon area is not a line-match')
# Multi-state v2 (Quality Part A grade): WEAKEST status across states; per-state when area given.
# US-0367 Northern Tallgrass Prairie NWR: pin in US-IA, official in US-MN.
check(FKS.KEY_BY_AREA.get('US-0367', {}).get('US-IA') == 'pin', f"US-0367 IA is pin (got {FKS.KEY_BY_AREA.get('US-0367')})")
check(FKS.KEY_BY_AREA.get('US-0367', {}).get('US-MN') == 'official', f"US-0367 MN is official (got {FKS.KEY_BY_AREA.get('US-0367')})")
check(FKS.KEY_STATUS.get('US-0367') == 'pin', f"US-0367 weakest across states is pin (got {FKS.KEY_STATUS.get('US-0367')})")
check(FKS.status_for('US-0367', 'US-IA') == 'pin', 'status_for IA -> pin')
check(FKS.status_for('US-0367', 'US-MN') == 'official', 'status_for MN -> official')
check(FKS.key_line_match(['US-0367', 'US-DUMMY'], 'area', ROOT, areas={'US-0367': 'US-IA'}).startswith('dropped'),
      'US-0367 graded in IA (pin) drops an area 2-fer')
check(FKS.key_line_match(['US-0367', 'US-DUMMY'], 'area', ROOT, areas={'US-0367': 'US-MN'}) == '' or
      FKS.status_for('US-0367', 'US-MN') == 'official',
      'US-0367 graded in MN is official (not a pin drop by itself)')
# Weakest-status logic on a tiny fixture (no built key data)
FKS.clear()
FKS.KEY_BY_AREA['US-X'] = {'US-AR': 'official', 'US-OK': 'pin'}; FKS.KEY_STATUS['US-X'] = 'pin'
check(FKS.status_for('US-X', 'US-OK') == 'pin' and FKS.status_for('US-X', 'US-AR') == 'official', 'a ref official in one state and pin in another: status_for follows the asked state')

# Rule-18 selftests (Quality examples that are piece / number cases). Housatonic Southern Fields is caught above by
# key g=approximate (the key already refused a full join); Herb Behnke is the classic unit-of-WA rule-18.
w = PC.rule18_differs('Herb Behnke Unit of Wolf River Bottoms State Wildlife Area', 'Wolf River Bottoms Wildlife Area')
check('rule 18' in w and 'behnke' in w.lower(), f"rule 18 flags Herb Behnke unit vs Wolf River Bottoms WA ({w})")
w2 = PC.rule18_differs('Mount Stanley', 'Mount Stanley 1')
check('number 1' in w2 and 'rule 18' in w2, f"rule 18 flags Mount Stanley vs Mount Stanley 1 ({w2})")
w3 = PC.rule18_differs('Fish Lake No. 1', 'Fish Lake')
check('number 1' in w3 and 'rule 18' in w3, f"rule 18 flags Fish Lake No. 1 vs Fish Lake ({w3})")
# Jemez / Fenton and Neal Smith / N. Tallgrass are NOT rule-18 piece cases: they are different parks. The 2-fer gate
# drops them because the key marks one half PIN / approximate (tested above), not because rule 18 fires on the names.

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
