#!/usr/bin/env python3
"""Next round C7 (Nov 5; Brandon's yes relayed via Super; outside research round 2): 332 Queensland state-forest parks had no
outline. Their outlines are in the DESI layer 'Protected areas and forests of Queensland' as esttype='SF' (402 features, Nov 5).
kpc_world_key.py now reads QLD state forests from that layer with where esttype='SF' (label unchanged), and the two published copies
of the same layer that extra-layers.json lists are read WITHOUT their SF, so no state forest is read twice. Runs the source-list
part of kpc_world_key.py (everything before COUNTRIES; no network). This moves the world rules hash."""
import os, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
os.chdir(HERE); sys.path.insert(0, str(HERE / '.github/scripts'))
ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)
src = open('.github/scripts/kpc_world_key.py', encoding='utf-8').read()
g = {'__name__': 'kpc_world_key_prefix', '__file__': '.github/scripts/kpc_world_key.py'}
exec(compile(src[:src.index('COUNTRIES = (os.environ')], 'kpc_world_key.py', 'exec'), g)
AU = g['SRC']['AU']
PAF = 'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Boundaries/AdminBoundariesFramework/FeatureServer/77'
MS10 = 'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Environment/ParksTerrestrialProtectedAreas/MapServer/10'
sf = [s for s in AU if s[0] == 'QLD State Forest (Queensland Government)']
check(len(sf) == 1 and sf[0][1:] == ('arcgis', PAF, ["esttype='SF'"]), f'QLD state forests: one arcgis source on the DESI layer, where esttype=\'SF\' ({sf})')
check(not any('LandParcelPropertyFramework' in str(s[2]) for s in AU), 'the old cadastre layer-name search is gone (it matched no park)')
for u in (PAF, MS10):
    rest = [s for s in AU if str(s[2]).rstrip('/').lower() == u.lower() and s[0] != 'QLD State Forest (Queensland Government)']
    # v2 C12 (Brandon's item 6): MapServer/10, the duplicate copy, is no longer in extra-layers.json; if it is listed again it is
    # still read without its SF
    check((len(rest) == 1 or (u == MS10 and not rest)) and all(r[3] == ["esttype<>'SF' OR esttype IS NULL"] for r in rest),
          f'{u.split("/services/")[1]}: the approved whole layer is read at most once, without its SF ({rest})')
sf_reads = [s for s in AU if 'qld.gov.au' in str(s[2]) and any("esttype='SF'" == w for w in (s[3] if len(s) > 3 else ['1=1']))]
check(len(sf_reads) == 1, 'a state forest is read from one source only')
others = [s for s in AU if 'qld.gov.au' not in str(s[2])]
check(any(s[0] == 'CAPAD (DCCEEW)' for s in others) and any(s[0].startswith('VIC DEECA') and s[3] == ["mmtgen='STATE FOREST' AND name<>' '"] for s in others)
      and any(s[0].startswith('WA DBCA state forests') and s[3] == ["leg_category='State Forest'"] for s in others), 'the other AU sources are unchanged')
# the where reaches the query: an 'arcgis' source passes its where list to pull_arcgis, which sends each as the query's where
check("got = pull_arcgis(s[0], s[2], s[3] if len(s) > 3 and s[1] != 'arcgisfind' else None) if s[1] in ('arcgis', 'arcgis_alt')" in src
      and "qq = {'where': where," in src and 'for w in (wheres or [\'1=1\']):' in src, 'an arcgis source with a where list is queried with that where')
check("re.search(r'name|enw|nombre|_nme$', k, re.I)" in src, "the park name comes from the layer's 'estatename' field (pick_name: first *name* field)")
import kpc_key_freeze as KF
# v2 re-cut (Nov 5): checked by file, not by pinned values, so the test also holds when v2 C10 (kpc_key_rules.py) moves the US
# hash in the stack: this patch changes kpc_world_key.py only, which is a world-key rule file and no US / CA rule file.
h = {k: KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key')}
_rf = {k: ' '.join(map(str, v)) for k, v in KF.RULE_FILES.items()}
check('kpc_world_key' in _rf.get('world-key', '') and not any('kpc_world_key' in _rf.get(k, '') for k in ('us-key', 'ca-key'))
      and h['world-key'] != '487a51327b86', f'only the world rules hash moves ({h})')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
