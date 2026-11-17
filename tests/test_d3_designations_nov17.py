#!/usr/bin/env python3
"""D3 (KPC owner, 2026-11-17 10:00 AM): a park that IS a designation. Switch KPC_DESIGNATION_SPLIT, OFF.
Run:  python3 tests/test_d3_designations_nov17.py   (reads kpc_us_key.py as text: importing it would start a build)"""
import sys as _sys; _sys.dont_write_bytecode = True
import ast, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ns = {'re': re}
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('KINDS', 'DESIG_PRE', 'DESIG_KIND', 'HERITAGE_RX', 'DESIG_WORDS') for t in node.targets):
        exec(compile(ast.Module([node], []), 'x', 'exec'), ns)
    if isinstance(node, ast.FunctionDef) and node.name in ('kinds', '_dcore'):
        exec(compile(ast.Module([node], []), 'x', 'exec'), ns)
kinds, H, D = ns['kinds'], ns['HERITAGE_RX'], ns['DESIG_PRE']
check(not KR.on('KPC_DESIGNATION_SPLIT', {}), 'the switch is OFF unless set')
check(D == {'fsod', 'nca', 'wld', 'wbl', 'wsa'}, 'federal designation layers only (state ones wait for D7: reading D11 labels is a rebuild)')
for s in ('National Heritage Area', 'Kenai Mountains-Turnagain Arm National Heritage Area', 'Ohio & Erie Canalway National Heritage Corridor'):
    check(bool(H.search(s)), f'heritage area: {s}')
for s in ('State Historic Site', 'Natural Heritage Preserve'):
    check(not H.search(s), f'not a heritage area: {s}')
DK = ns['DESIG_KIND']
def is_it(rec, pn, pt, pre=''):
    rn, p_ = KR._full(rec), KR._full(pn)
    if rn and (p_ == rn or p_.startswith(rn + ' ')): return True
    if rn and ns['_dcore'](rn) and ns['_dcore'](rn) == ns['_dcore'](p_): return True
    return bool((kinds(rec) or DK.get(pre, set())) & (kinds(pn) | kinds(pt)))
check(is_it('Red Rock Canyon National Conservation Area', 'Red Rock Canyon National Conservation Area', 'National Conservation Area'), 'the NCA line stays on the NCA park')
check(is_it('Grand Staircase-Escalante National Monument', 'Grand Staircase-Escalante National Monument', 'National Monument'), 'the monument line stays on the monument park')
check(not is_it('Box-Death Hollow Wilderness', 'Dixie National Forest', 'National Forest'), 'a wilderness line is not lent to a national forest park')
check(not is_it('Grand Staircase-Escalante National Monument', 'Escalante Petrified Forest State Park', 'State Park'), 'a monument line is not lent to a state park')
check(is_it('Mount St. Helens National Volcanic Monument', 'Mount St. Helens National Volcanic Monument', 'National Monument'), 'a record with no kind word: its full name must be the park\'s')
check(not is_it('Mount St. Helens National Volcanic Monument', 'Gifford Pinchot National Forest', 'National Forest'), '... and is not lent to another park')
check(is_it('Bears Ears', 'Bears Ears BLM National Monument', 'National Monument', 'nca'), 'a bare record name that begins the park name is that park (Bears Ears)')
check(is_it("Scott's Basin", "Scott's Basin WSA BLM Wilderness Area", 'Wilderness Area', 'wsa'), 'a bare study-area record on its own WSA park')
check(is_it('Mt. Ellen-Blue Hills', 'Mt. Ellen-Blue Hills BLM Wilderness Area', 'BLM Wilderness Area', 'wsa'), 'POTA calls a study area a wilderness: same name, same land')
check(not is_it('Box-Death Hollow', 'Dixie National Forest', 'National Forest', 'wld'), 'a bare wilderness record is not lent to a national forest (layer kind)')
check(is_it('Phipps - Death Hollow ISA', 'Phipps-Death Hollow BLM Wilderness Area', 'Wilderness Area', 'wsa'), 'same name without the type words (an ISA on its wilderness park)')
check(not is_it('Black Ridge Canyons West', 'Black Ridge Canyons Wilderness Area', 'Wilderness Area', 'wsa'), 'a neighbouring study area (West) is not the park: a person decides')
blk = src[src.index('# D3 (KPC owner, 2026-11-17 10:00 AM, switch KPC_DESIGNATION_SPLIT)'):]
blk = blk[:blk.index("weak = [x for x in m if str(x[3]).split(' · ')[0] in WEAK")]
check("_kr('KPC_DESIGNATION_SPLIT')" in blk and 'name_only(x[3])' in blk, 'behind the switch, name joins only (a person\'s join stands)')
check("p['on'] = " in blk and "== 'Designation'" in blk, 'heritage parks list what they sit on; PAD-US Designation records count as designation lines')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
