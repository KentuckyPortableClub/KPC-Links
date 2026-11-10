#!/usr/bin/env python3
"""POTA's 'sub-parks' rule is gone (Brandon Nov 9, 2026, 6:43 PM CST, t944u). Offline: no network, no run started.
1 the Tool Box rep check: a park inside a bigger POTA park of the SAME agency is INFO (allowed, needs its own web page + boundary
  map, a possible 2-fer), never a NO that makes the verdict 'LIKELY NOT ELIGIBLE'
2 the Kentucky new-lands watch no longer leaves such a land out (it is listed with a note)
3 the 2-fer finder already treats a same-agency nested pair like any other pair: one public owner = ok (no 2-fer rule file changed)
4 point 2 of the rule: a park with only a point (no official boundary of its own) inside the bigger park is NOT tested as a 2-fer;
  it goes on the 'Missing boundary: check the official map' list, and the bigger park's shape is never its outline
5 rule 12 text in mapping.md / RULES-NOW.md says the new rule; the rule hashes did not move"""
import json, os, pathlib, sys, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S))
os.environ.setdefault('PASS', '5')
try: import cv2  # noqa: F401
except Exception: sys.modules['cv2'] = types.ModuleType('cv2')  # noqa: BLE001
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


# 1 Tool Box
js = (HERE / 'kpc-maprep.js').read_text(encoding='utf-8')
check("add(sameAgency.length ? 'NO'" not in js, "Tool Box: a same-agency parent no longer gives a NO")
check("add(sameAgency.length ? 'INFO' : 'YES', 'Inside a bigger POTA park? (POTA allows a park inside a park now)'," in js, 'Tool Box: same-agency parent = INFO')
check('POTA does not make a separate park inside an existing park' not in js and 'Not a "sub-park"' not in js, 'Tool Box: the old sub-park sentence is gone')
_i = js.index("'Inside a bigger POTA park?"); _seg = js[_i:_i + 1400]
check('own official web page' in _seg and 'published boundary map' in _seg and 'a dot on a map is not enough' in _seg,
      'Tool Box: it still needs its own web page and its own published boundary map (point 2)')
check('possible 2-fer' in _seg and 'Forest Service campground inside a national forest' in _seg, 'Tool Box: says it would be a possible 2-fer, with the campground example')
check("const nNo = res.filter(r => r.v === 'NO').length" in js, 'Tool Box: only NO rows make LIKELY NOT ELIGIBLE (INFO does not count)')

# 2 Kentucky new-lands watch
import kpc_new_lands as NL
nl = (S / 'kpc_new_lands.py').read_text(encoding='utf-8')
check('same-agency sub-park' not in nl, 'new-lands watch: the sub-park exclusion is gone')
n = NL.subpark_note('Natural Bridge State Park State Nature Preserve')
check(bool(n) and 'boundary map' in n and '2-fer' in n and 'web page' in n, f'new-lands watch: a preserve inside a state park gets the note ({n[:60]}...)')
check(NL.subpark_note('Clay WMA') == '' and NL.subpark_note('') == '', 'new-lands watch: other lands get no note')
check("if not w and subpark_note(n): line += ' · _%s_' % subpark_note(n)" in nl, 'new-lands watch: the note is added to the promising row')

# 3 2-fer ownership: a same-agency nested pair is public ground (unchanged code, pinned here)
import kpc_fers as K
K.REGION = 'na'
parks = {'NF': {'st': 'US-CO', 'ids': [1], 'names': {'1': 'Arapaho and Roosevelt National Forests'}},
         'CG': {'st': 'US-CO', 'ids': [2], 'names': {'2': 'Brainard Lake Recreation Area'}},
         'SP': {'st': 'US-KY', 'ids': [3], 'names': {'3': 'Natural Bridge State Resort Park'}},
         'NP': {'st': 'US-KY', 'ids': [4], 'names': {'4': 'Natural Bridge State Park State Nature Preserve'}}}
K.OWN.update({'NF': ({'FED:USFS'}, False), 'CG': ({'FED:USFS'}, False), 'SP': ({'STATE'}, False), 'NP': ({'STATE'}, False)})
PIN = {r: [p['names'][str(p['ids'][0])]] for r, p in parks.items()}
K.PINS.update(PIN)
for a, b, what in (('NF', 'CG', 'Forest Service campground inside a national forest'), ('SP', 'NP', 'state nature preserve inside a state park')):
    s = {'refs': [a, b]}; v = K.ownership_step(s, parks, PIN)
    check(v[0] == 'ok' and 'mixed_owners' not in s, f'2-fer ownership: {what} = one public owner, ok ({v})')

# 3b the nested link (kpc_tracts) still finds the park inside the park
import kpc_tracts as TR
sq = lambda x0, y0, x1, y1: [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]
nest = TR.nested_geometry({'US-cg': sq(-105.6, 40.06, -105.55, 40.09), 'US-nf': sq(-106, 39.8, -105.2, 40.6)})
check(nest == [{'child': 'US-cg', 'parent': 'US-nf', 'share': 1.0, 'how': 'geometry'}], f'a campground inside the forest links as a nested park ({nest})')

# 4 point 2: a point-only campground is not a 2-fer half; it is on the Missing boundary list
src = (S / 'kpc_fers.py').read_text(encoding='utf-8')
_ml = src[src.index('def missing_list'):src.index('# ------------------------------------------------------------------ rasters')]
check("(ref in G)" in _ml and "'Missing boundary: check the official map'" in _ml,
      'point-only park inside another park = Missing boundary list, never a tested 2-fer (it has no outline in G)')

# 5 rule text + hashes
m = (HERE / '.claude/notes/mapping.md').read_text(encoding='utf-8'); rn = (HERE / '.claude/RULES-NOW.md').read_text(encoding='utf-8')
for t, nm in ((m, 'mapping.md'), (rn, 'RULES-NOW.md')):
    i = t.index('12. CAN A PARK BE INSIDE ANOTHER PARK OF THE SAME AGENCY?'); r12 = t[i:t.index('\n', i)]
    check(r12.startswith('12. CAN A PARK BE INSIDE ANOTHER PARK OF THE SAME AGENCY? YES') and 'published boundary map' in r12 and 't944u' in r12, f'{nm}: rule 12 says the new rule')
    check("'same land, two park numbers'" in r12 and 'a dot on a map is not a boundary' in r12, f'{nm}: rule 12 keeps same-land rows and point 2')
check(rn.count('12. CAN A PARK BE INSIDE ANOTHER PARK OF THE SAME AGENCY? YES') == 1, 'RULES-NOW.md was regenerated from mapping.md')
import kpc_key_freeze as F
want = {'us-key': '19d219f37114', 'ca-key': '22f16bc69b96', 'world-key': '10e4092cc97f', 'fers': 'eb92de7a5f65'}
got = {k: F.rules_hash(k, HERE) for k in want}
check(got == want, f'no rule hash moved ({got})')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
