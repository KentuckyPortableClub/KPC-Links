#!/usr/bin/env python3
"""KPC_NO_FOLLOWS_FP (job 10 of Fable's 20 Nov jobs list; outside review R4 / finding F7). A person's saved NO named a record id;
after a layer refresh renumbers that record, the NO no longer applied and the land joined again (Arkansas US-1080). With the
switch ON a 'no' id that is gone from the read follows its saved fingerprint ('nofp': name + acres within 10%, the SAME layer, near
the pin), the way a saved join already does. OFF = today. The build steps are cut out of kpc_us_key.py and run on small reads, so
this test fails while the builder has no such step.
Run:  python3 tests/test_no_follows_fp_nov20.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import pathlib, re, sys, textwrap
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

check(not KR.on('KPC_NO_FOLLOWS_FP', {}) and KR.DEFAULTS.get('KPC_NO_FOLLOWS_FP') == '0', 'the switch KPC_NO_FOLLOWS_FP is OFF unless set')
check('KPC_NO_FOLLOWS_FP' in KR.switch_file() and not any('KPC_NO_FOLLOWS_FP' in KR.areas_on(a) for a in ('AR', 'KY', 'MO')),
      'the switch file lists it, on for no area')

def rec(i, n, ac): return {'OBJECTID': i, 'Unit_Nm': n, 'GIS_Acres': ac, '_bb': [0, 0, 0, 0]}
NM = 'DeGray Lake Resort State Park'

# the pure step
def rf(recs):
    return lambda old, nm, ac: [a for a in recs if re.match(r'\D*', str(a['OBJECTID'])).group() == re.match(r'\D*', old).group() and KR.nf(a['Unit_Nm']) == KR.nf(nm)]
OVN = {'no': ['sgarb44'], 'nofp': {'sgarb44': [NM, 819]}}
R = [rec('sgarb90', NM, 830), rec('sgarb91', 'Other Place', 819), rec('wsa9', NM, 819)]
nov, notes = KR.follow_gone_no(OVN, lambda i: i in {'sgarb90', 'sgarb91', 'wsa9'}, rf(R))
check(nov['no'] == ['sgarb44', 'sgarb90'] and nov['nofp']['sgarb90'] == [NM, 819] and notes == [('no followed', 'sgarb44', ['sgarb90'], NM, 819)],
      'a gone NO id follows the one same-layer record with its name and acres within 10%')
check(OVN == {'no': ['sgarb44'], 'nofp': {'sgarb44': [NM, 819]}}, 'the saved answer itself is not changed (a copy)')
nov, notes = KR.follow_gone_no(OVN, lambda i: True, rf(R))
check(nov == OVN and not notes, 'a NO id still in the read is left to D1 (nothing here)')
nov, notes = KR.follow_gone_no({'no': ['sgarb44'], 'nofp': {'sgarb44': [NM, 2000]}}, lambda i: False, rf(R))
check(nov['no'] == ['sgarb44'] and notes[0][0] == 'no not found', 'acres more than 10% off: nothing is ruled out, it is said')
nov, notes = KR.follow_gone_no({'no': ['wsa44'], 'nofp': {'wsa44': [NM, 819]}}, lambda i: False, rf([rec('sgarb90', NM, 819)]))
check(nov['no'] == ['wsa44'] and notes[0][0] == 'no not found', 'another layer never fits (the id family, as the join re-find)')
nov, notes = KR.follow_gone_no(OVN, lambda i: False, rf(R + [rec('sgarb92', NM.upper(), 800)]))
check(nov['no'] == ['sgarb44', 'sgarb90', 'sgarb92'], 'two copies of one land: a NO only removes, so both are ruled out')
nov, notes = KR.follow_gone_no({'join': ['sgarb90'], **OVN}, lambda i: False, rf(R))
check(nov['no'] == ['sgarb44'] and notes == [('no meets join', 'sgarb44', ['sgarb90'], NM, 819)], 'a fit the same park joins by id is never ruled out here; it is said')
nov, notes = KR.follow_gone_no({'no': ['sgarb44']}, lambda i: False, rf(R))
check(not notes, 'a NO with no saved fingerprint: nothing to follow')

# the build steps themselves: D1 + this step (before the parks loop), then the saved answers of one park
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
pre = re.search(r"^    D1_CHECK = \{\}\n.*?(?=^    parks, used = \{\}, set\(\))", src, re.S | re.M)
mm = re.search(r"^        ov = OVR\.get\(ref\) or \{\}\n.*?(?=^        _sct, _sfirst)", src, re.S | re.M)
check(bool(pre) and bool(mm), 'the two build steps are found in kpc_us_key.py')
check(bool(pre) and "_kr('KPC_NO_FOLLOWS_FP')" in pre.group(0), 'the US key has the NO-follows step, behind the switch, before the parks are matched')

def build(sw, ov, recs, m):
    notes = []
    ns = {'KR': KR, 're': re, 'st': 'AR', 'ref': 'US-1080', 'name': NM, 'P': {'US-1080': [NM, '', 'State Park', '', '', 34.2, -93.1]},
          'OVR': {'US-1080': ov}, 'recs': recs, 'm': [list(x) for x in m], 'c': [], 'la': 34.2, 'lo': -93.1,
          'near': lambda la, lo, bb, d: True, 'pins': lambda: {}, 'notice': lambda t, x: notes.append(x),
          '_oid': lambda a: str(a['OBJECTID']), '_nf': KR.nf, '_no_all': lambda ov, a: False, 'SAVED_SAY': [], 'FAR_JOIN': [],
          '_kr': lambda n: (sw and n == 'KPC_NO_FOLLOWS_FP') or n in ('KPC_NO_ALL_PATHS', 'KPC_FAR_JOIN', 'KPC_SAVED_ID_LAND')}
    exec(textwrap.dedent(pre.group(0)) if pre else '', ns)
    ns['ov'] = None
    exec(textwrap.dedent(mm.group(0)) if mm else '', ns)
    return [str(x[0]) for x in ns['m']], notes
# the land a person said NO to (12,342.6 ac) came back under a new id after a refresh; the name path found it again
OV = {'no': ['sgarb44'], 'nofp': {'sgarb44': [NM, 12342.6]}}
READ = [rec('sgarb990', NM, 12300), rec('sgarb7', 'Other Place', 50)]
M = [['sgarb990', NM, 12300, 'name']]
j, notes = build(False, dict(OV), READ, M)
check(j == ['sgarb990'] and not notes, 'OFF (today): the renumbered NO land joins again (the bug)')
j, notes = build(True, dict(OV), READ, M)
check(j == [] and any('no followed 1' in x and 'sgarb44->sgarb990' in x for x in notes), 'ON: the NO follows its record by fingerprint: nothing joins, it is said')
j, notes = build(True, dict(OV), [rec('sgarb44', NM, 819), rec('sgarb990', NM, 12300)], [['sgarb44', NM, 819, 'name'], ['sgarb990', NM, 12300, 'name']])
check(j == ['sgarb44'] and not any('follows' in x for x in notes) and any('no moved 1' in x for x in notes),
      'ON: a NO id still in the read that now holds other land is D1\'s (the NO moves to its land), this step does nothing')
j, notes = build(True, {'join': ['sgarb990'], **OV}, READ, M)
check(j == ['sgarb990'] and any('no meets join 1' in x for x in notes), 'ON: a person\'s join by id of the re-found record stands, and it is said')
j, notes = build(True, dict(OV), [rec('sgarb990', NM, 819)], [['sgarb990', NM, 819, 'name']])
check(j == ['sgarb990'] and any('no not found 1' in x for x in notes), 'ON: other acres (the park\'s own record): not ruled out, it is said')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
