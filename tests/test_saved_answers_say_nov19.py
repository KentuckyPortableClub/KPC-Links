#!/usr/bin/env python3
"""KPC_SAVED_ANSWERS_SAY (2026-11-19, outside review finding F5; reviewer's first slice, step S6b; a DRAFT for the reviewer). The US
key's saved joins say what they could not do: a join not found in the read, a fingerprint that fits two records (the first one
joins, on or off; ON it is also said), and one record under both 'join' and 'no' of a park (said; which wins is not
changed). Said in the build's notice and the state's counts, never as a check row. Switch OFF unless set.
Real names: Arkansas DeGray Lake Resort State Park US-1080, record sgarb44 under both join and no (saved answers of 19 Nov).
Run:  python3 tests/test_saved_answers_say_nov19.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import pathlib, re, sys, textwrap
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

check(not KR.on('KPC_SAVED_ANSWERS_SAY', {}) and KR.DEFAULTS.get('KPC_SAVED_ANSWERS_SAY') == '0', 'the switch KPC_SAVED_ANSWERS_SAY is OFF unless set')
check('KPC_SAVED_ANSWERS_SAY' in KR.switch_file() and not any('KPC_SAVED_ANSWERS_SAY' in KR.areas_on(a) for a in ('AR', 'KY', 'TN')),
      'the switch file lists it, on for no area')

# the pure decisions
C = [('sgarb101', 'DeGray Lake Resort State Park', 830), ('sgarb102', 'DeGray Lake', 830), ('wsa9', 'DeGray Lake Resort State Park', 819)]
check(KR.refind_saved('DeGray Lake Resort State Park', 819, 'sgarb', C) == ('one', 'sgarb101'), 'one fit: same name, same layer, acres within 10%')
check(KR.refind_saved('DeGray Lake Resort State Park', 2000, 'sgarb', C) == ('none', None), 'no fit: acres too far off')
check(KR.refind_saved('DeGray Lake Resort State Park', 819, 'sgxyz', C) == ('none', None), 'no fit: another layer never fits (Elkhorn / wsa205)')
C2 = C + [('sgarb103', 'degray lake resort state park', 800)]
check(KR.refind_saved('DeGray Lake Resort State Park', 819, 'sgarb', C2) == ('two', ['sgarb101', 'sgarb103']), 'two fits: both ids named')
check(KR.refind_saved('DeGray Lake Resort State Park', 819, 'sgarb', C + [('sgarb101', 'DeGray Lake Resort State Park', 830)]) == ('one', 'sgarb101'),
      'the same record read twice is one fit')
check(KR.refind_saved('X', 0, '', [('5', 'X', 15), ('6', 'X', 25)]) == ('one', '5'), 'acres: at least 20 acres of slack, as the builder')
check(KR.join_not_found('sgarb44', {'sgarb1'}, iter(['degray lake'])) and not KR.join_not_found('sgarb1', {'sgarb1'}, iter([]))
      and not KR.join_not_found('DeGray Lake', set(), iter(['degray lake'])), 'not found: no such id in the read and no such name near the pin')
check(KR.join_and_no({'join': ['sgarb44', 'x'], 'no': ['sgarb44']}) == ['sgarb44'] and KR.join_and_no({'join': ['a'], 'no': ['b']}) == [] and KR.join_and_no(None) == [],
      'join and no on one record: the id is named')

# the build step itself, cut out of kpc_us_key.py (the saved joins of one park) and run on small reads
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
mm = re.search(r"^        ov = OVR\.get\(ref\) or \{\}\n.*?(?=^        _sct, _sfirst)", src, re.S | re.M)
check(bool(mm) and "_kr('KPC_SAVED_ANSWERS_SAY')" in mm.group(0), 'the US key applies the saved joins with the new switch in that step')
def rec(i, n, ac): return {'OBJECTID': i, 'Unit_Nm': n, 'GIS_Acres': ac, '_bb': [0, 0, 0, 0]}
def build(sw, ov, recs, m=None):
    say, far = [], []
    ns = {'KR': KR, 're': re, 'st': 'AR', 'ref': 'US-1080', 'name': 'DeGray Lake Resort State Park', 'OVR': {'US-1080': ov}, 'recs': recs,
          'm': [list(x) for x in (m or [])], 'c': [], 'la': 34.2, 'lo': -93.1, 'near': lambda la, lo, bb, d: True,
          '_oid': lambda a: str(a['OBJECTID']), '_nf': KR.nf, '_no_all': lambda ov, a: False, 'SAVED_SAY': say, 'FAR_JOIN': far,
          '_kr': lambda n: (sw and n == 'KPC_SAVED_ANSWERS_SAY') or n in ('KPC_NO_ALL_PATHS', 'KPC_FAR_JOIN')}
    exec(textwrap.dedent(mm.group(0)), ns)
    return [str(x[0]) for x in ns['m']], ns['c'], say
FPN = 'DeGray Lake Resort State Park'
OV = {'join': ['sgarb44'], 'fp': {'sgarb44': [FPN, 819]}}
R1 = [rec('sgarb101', FPN, 830), rec('sgarb7', 'Other Place', 50)]
R2 = R1 + [rec('sgarb103', FPN, 800)]
for sw in (False, True):
    j, c, say = build(sw, OV, [rec('sgarb44', FPN, 819)])
    check(j == ['sgarb44'] and not say and not c, f'{"ON" if sw else "OFF"}: the saved id is in the read: it joins, nothing said')
    j, c, say = build(sw, OV, R1)
    check(j == ['sgarb101'] and not say and not c, f'{"ON" if sw else "OFF"}: one fit: the re-found record joins, nothing said')
j, c, say = build(False, OV, R2)
check(j == ['sgarb101'] and not say and not c, 'OFF: two fits: the first one joins, as today, nothing said')
j, c, say = build(True, OV, R2)
check(j == ['sgarb101'] and c == [] and [h[1:4] for h in say] == [['two fits', 'US-1080', 'sgarb44']] and 'sgarb101 sgarb103' in say[0][4],
      'ON: two fits: the first one joins as before (Fable + owner, 20 Nov), no check row, said with both candidate ids')
R0 = [rec('sgarb7', 'Other Place', 50)]
j, c, say = build(False, OV, R0)
check(j == [] and not say and not c, 'OFF: not found: nothing joined, nothing said (today)')
j, c, say = build(True, OV, R0)
check(j == [] and c == [] and [h[1:4] for h in say] == [['not found', 'US-1080', 'sgarb44']] and FPN in say[0][4] and '819' in say[0][4],
      'ON: not found: nothing joined, no check row, said with the park, the saved id and the fingerprint')
j, c, say = build(True, {'join': ['rst13946']}, R0)
check(j == [] and [h[1] for h in say] == ['not found'] and 'fingerprint none' in say[0][4], 'ON: an id with no fingerprint that is not in the read is said too')
j, c, say = build(True, {'join': ['Other Place']}, R0)
check(j == ['sgarb7'] and not say, 'ON: a bare-name join finds its record by name and joins, as today (finding (d) not changed)')
j, c, say = build(True, {'join': ['Gone Place']}, R0)
check(j == [] and [h[1] for h in say] == ['not found'], 'ON: a bare-name join that finds nothing near the pin is said')
JN = {'join': ['sgarb44'], 'no': ['sgarb44'], 'fp': {'sgarb44': [FPN, 819]}, 'nofp': {'sgarb44': [FPN, 12342.6]}}
for sw in (False, True):
    j, c, say = build(sw, JN, [rec('sgarb44', FPN, 819)], m=[['sgarb44', FPN, 819, 'name']])
    check(j == [] and c == [], f'{"ON" if sw else "OFF"}: one record under join and no, in the read: the NO wins (today), the same with the switch on')
    check(([h[1:4] for h in say] == [['join and no', 'US-1080', 'sgarb44']]) if sw else not say, f'{"ON: it is said" if sw else "OFF: nothing said"}')

# the notice and the counts are in the builder, behind the switch
check("_ss = [h for h in SAVED_SAY if h[0] == st]" in src and "counts['saved_join_' + _k.replace(' ', '_')]" in src
      and re.search(r"if _kr\('KPC_SAVED_ANSWERS_SAY'\):   # F5: plain counts", src), 'the build notice and the counts (only with the switch on)')
check(not re.search(r"c\.append\([^\n]*(not found|two fits)", src), 'no check row is written for not found or two fits')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
