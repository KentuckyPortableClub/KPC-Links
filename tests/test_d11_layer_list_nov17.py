#!/usr/bin/env python3
"""D11 (KPC owner, 2026-11-17; owner ruling D11): the US key's layer list goes under the frozen hash, and every layer says what it is.
  1. data/state-gis.json is in kpc_key_freeze RULE_FILES['us-key'] (and kpc_area_hash reads the same list); not in Canada, world or fers
  2. every layer has one more field, 'what', right after 'kind': owned, designation, water, register or compilation; all 131 layers
     filed as kind 'land' are labelled, and the labels follow the layer (an ACEC is a designation, the NRHP a register, a lake layer water)
  3. the hash moves ONCE: the last US scope entry (2026-11-17-d11-layer-list, scope none) names as 'from' the hash this tree has
     without the list, without the labels and without that entry; and that pending scope rebuilds no area
  4. no join changes: no US key rule file reads 'what'; with the labels taken out, every field the builder reads is the file as it was
     (checked against origin/main while main has no labels)
  5. no area moves: the per-area input hash slices state-gis.json per state (as the area tables are) and leaves the unread label out,
     so labelling moves no US state and no province; a rule that starts reading 'what' must take it off kpc_area_hash.SGIS_UNREAD
Prints PASS / FAIL lines, ends ALL PASS / SOME FAILED."""
import copy, hashlib, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_area_hash as K  # noqa: E402
import kpc_key_freeze as F  # noqa: E402

ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)


SG = 'data/state-gis.json'
WHAT = {'owned', 'designation', 'water', 'register', 'compilation'}
doc = json.loads((ROOT / SG).read_text(encoding='utf-8'))
layers = [(st, l) for st, L in doc['states'].items() for l in L]

# 1
check('1. data/state-gis.json is a US key rule file (kpc_key_freeze RULE_FILES)', SG in F.RULE_FILES['us-key'])
check('1. not a Canada, world or 2-fer rule file', all(SG not in F.RULE_FILES[k] for k in ('ca-key', 'world-key', 'fers')))
rf, _sf, _vf = K.freeze_lists(K.Tree(ROOT))
check('1. kpc_area_hash reads the same RULE_FILES (the literal append is seen)', SG in rf['us-key'] and sorted(rf['us-key']) == sorted(F.RULE_FILES['us-key']))

# 2
check(f'2. every one of the {len(layers)} layers has what in {sorted(WHAT)}', layers and all(l.get('what') in WHAT for _, l in layers))
check('2. what comes right after kind in every layer', all(list(l)[list(l).index('kind') + 1] == 'what' for _, l in layers))
land = [l for _, l in layers if l.get('kind') == 'land']
check(f'2. the {len(land)} layers filed as kind land are all labelled (131 on 17 Nov)', len(land) == 131 and all(l.get('what') in WHAT for l in land))
def by(rx): return {l['what'] for _, l in layers if re.search(rx, l['url'] + ' ' + l['ag'], re.I)}
check('2. BLM ACECs, national monuments / NCAs, heritage areas and NPS legal boundaries are designation lines',
      by(r'BLM_Natl_ACEC') == {'designation'} and by(r'National_Heritage_Areas') == {'designation'} and by(r'NPS_Land_Resources_Division_Boundary') == {'designation'}
      and by(r'Wild_Horse') == {'designation'})
check('2. the NRHP polygons and historic-places layers are registers', by(r'nrhp_locations') == {'register'} and by(r'Historic Places\)') == {'register'})
check('2. lake / reservoir / waterbody layers are water (and every layer flagged water)', by(r'Hydrography_Public|NHD/FeatureServer') == {'water'}
      and all(l['what'] == 'water' for _, l in layers if l.get('water')))
check('2. many-owner gatherings are compilations (KS heritage inventory, MassGIS open space, NH conservation lands)',
      by(r'rest/services/protected_areas/FeatureServer') == {'compilation'} and by(r'AGOL/openspace') == {'compilation'} and by(r'EC/Conservation/MapServer') == {'compilation'})
check('2. a state park layer is owned land', by(r'ParkBoundaries/FeatureServer|PARKS_BOUNDARIES') == {'owned'})

# 3
sc = json.loads((ROOT / '.github/us-key-rule-scope.json').read_text(encoding='utf-8'))
# HQ, 2026-11-17: the D11 entry is found by its id. While D11 is the NEWEST US change the hash checks below run as written; once a
# later change is declared on top (D1 first), they are branch-time checks that no longer apply and say so.
last = next((c for c in sc['changes'] if c.get('id') == '2026-11-17-d11-layer-list'), {})
D11_NEWEST = bool(sc['changes']) and sc['changes'][-1].get('id') == '2026-11-17-d11-layer-list'
check('3. the US scope file holds the D11 entry, scope none (no approval written by a bot)',
      last.get('id') == '2026-11-17-d11-layer-list' and last.get('scope') == 'none' and 'approved' not in last)


def hash_without_d11():
    """The US rules hash of this tree with the D11 change taken out: no state-gis.json in RULE_FILES and no D11 scope entry."""
    h = hashlib.sha256()
    sc0 = copy.deepcopy(sc); sc0['changes'] = [c for c in sc0['changes'] if c.get('id') != '2026-11-17-d11-layer-list']
    for rel in sorted(r for r in F.RULE_FILES['us-key'] if r != SG):
        if rel == F.SCOPE_FILES['us-key']: b = (json.dumps(sc0, indent=1, ensure_ascii=False) + '\n').encode()
        else:
            f = ROOT / rel
            if rel in F.SCOPE_FILES.values() and not f.is_file(): continue
            b = F.same_lines(f.read_bytes()) if f.is_file() else b'missing'
        h.update(rel.encode() + b'\0' + b + b'\0')
    ver = json.load(open(ROOT / F.VERSION_FILE, encoding='utf-8')).get('us-key')
    h.update(b'version\0' + str(ver).encode())
    return h.hexdigest()[:12]


if D11_NEWEST:
    now, before = F.rules_hash('us-key'), hash_without_d11()
    check(f'3. the hash moves once: {before} (no list, no labels) -> {now}, and the D11 entry is from {last.get("from")}', last.get('from') == before and now != before)
    ps = F.pending_scope('us-key', last.get('from'))
    check(f'3. from the last build on {before}, the declared change rebuilds no area (pending scope {ps})', ps == (set(), False, set()))
else:
    print('NOTE 3. a later US rule change is declared on top of D11: its own branch-time hash checks no longer apply')
check('3. Canada, world and 2-fer hashes are not D11\'s (state-gis.json is not their rule file)', all(SG not in F.RULE_FILES[k] for k in ('ca-key', 'world-key', 'fers')))

# 4
READS = [ROOT / r for r in F.RULE_FILES['us-key'] if r.endswith('.py')] + [ROOT / '.github/scripts/kpc_ca_key.py']
readers = [p.name for p in READS if re.search(r"""\[\s*['"]what['"]\s*\]|\.get\(\s*['"]what['"]""", p.read_text(encoding='utf-8'))]
# HQ 17 Nov: the US key reads 'what' (D3 by labels, D7); Canada still does not
check(f"4. only the US key reads what ({readers}); Canada's key does not", readers == ['kpc_us_key.py'] and 'what' in K.SGIS_READ_BY_US)
def strip(d):
    d = copy.deepcopy(d); d.pop('what_note', None)
    for L in d['states'].values():
        for l in L: l.pop('what', None)
    return d
r = subprocess.run(['git', 'show', 'origin/main:' + SG], cwd=ROOT, capture_output=True, text=True)
main_doc = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
if main_doc is not None and not any('what' in l for L in main_doc['states'].values() for l in L):
    check('4. with the labels taken out the file equals origin/main (labels only: no layer added, dropped or changed)', strip(doc) == main_doc)
else:
    print('NOTE 4. origin/main already has the labels (or is not here): the before / after file check is for the D11 branch only')

# 5
check('5. the per-area hash slices state-gis.json per state, not as shared code', SG in K.SLICED_RULE_FILES)
us_areas = set(K.US_ALL); ca_areas = {st for st in doc['states'] if st not in K.US_ALL}
# HQ 17 Nov: D3 (labels) and D7 (compilation) read 'what', so it left SGIS_UNREAD: a label now moves its own state, like any layer field
check('5. labelling moves no province (Canada reads no label); a US state keeps its labels in its slice (the US key reads them)',
      K.sgis_slice(doc, ca_areas) == K.sgis_slice(strip(doc), ca_areas) and K.sgis_slice(doc, us_areas) != K.sgis_slice(strip(doc), us_areas))
moved = copy.deepcopy(doc); moved['states']['TN'][0]['url'] += '0'
check('5. a real layer change still moves its own state only', K.sgis_slice(moved, {'TN'}) != K.sgis_slice(doc, {'TN'}) and K.sgis_slice(moved, {'KY', 'GA'}) == K.sgis_slice(doc, {'KY', 'GA'}))
check('5. a key that reads what keeps it in its slice (guard)', all(r != 'kpc_ca_key.py' for r in readers) or 'what' not in K.SGIS_UNREAD)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
