#!/usr/bin/env python3
"""Nov 3 addendum (Mapping): CA-2359 ZEC de la Rivière-Petit-Saguenay showed 1,891 acres in the Canada key against the official
0.52 km2 (52 ha, 128 ac). Cause: arc_pull in kpc_ca_key.py stored 'ha': 0 for every record it read from a province map service,
so acres() fell back to the area of the 0.02-degree (about 2 km) saved shape, which blows a narrow river strip up many times.
The fix reads the layer's own area field (SUPERFICIE_KM2, HA_LEGAL ...), also when the server answers with field aliases.
Offline; run from the repo root:  python3 tests/test_ca_acres_nov3.py"""
import pathlib, re, sys, types
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = (ROOT / '.github/scripts/kpc_ca_key.py').read_text(encoding='utf-8')
m = types.ModuleType('ca'); m.__dict__['__file__'] = str(ROOT / '.github/scripts/kpc_ca_key.py')
exec(compile(SRC.split('\nrecs = cload()')[0], 'kpc_ca_key.py', 'exec'), m.__dict__)
bad = []
def check(ok, msg):
    print(('PASS ' if ok else 'FAIL ') + msg)
    if not ok: bad.append(msg)
# the MRNF TRQ_WMS/16 (ZEC) layer as Quality read it live on Nov 3 (evidence/zec_petit_saguenay.json), and with alias keys
li16 = {'fields': [{'name': 'ID', 'alias': 'ID'}, {'name': 'SUPERFICIE_KM2', 'alias': 'Superficie (km2)'}, {'name': 'NOM_OFFICIEL', 'alias': 'Nom officiel'},
                   {'name': 'ESRI_OID', 'alias': 'ESRI_OID'}]}
check(m.rec_ha({'SUPERFICIE_KM2': 0.52, 'NOM_OFFICIEL': 'Zec de la Rivière-Petit-Saguenay'}, li16) == 52.0, 'ZEC Z-031D: SUPERFICIE_KM2 0.52 -> 52 ha')
check(m.rec_ha({'Superficie (km2)': 0.52, 'Nom officiel': 'Zec de la Rivière-Petit-Saguenay'}, li16) == 52.0, 'the same record answered with field ALIASES as keys -> 52 ha')
check(round(m.rec_ha({'SUPERFICIE_KM2': 0.52}, li16) * 2.47105) == 128, 'acres() gives 128 ac (was 1,891 ac from the coarse shape)')
li23 = {'fields': [{'name': 'TOPONYME', 'alias': 'Toponyme'}, {'name': 'HA_LEGAL', 'alias': 'Superficie (ha)'}, {'name': 'OBJECTID', 'alias': 'Clé interne'}]}
check(m.rec_ha({'TOPONYME': 'Réserve naturelle du Marais-Kergus', 'HA_LEGAL': 301.1}, li23) == 301.1, 'MELCCFP register: HA_LEGAL (legal hectares) is read')
check(m.area_fields(li16) == ['SUPERFICIE_KM2'] and m.area_fields(li23) == ['HA_LEGAL'], 'the area field is asked for with the name fields')
check(m.rec_ha({'TOPONYME': 'x'}, li23) == 0 and m.rec_ha({'SUPERFICIE_KM2': None}, li16) == 0, 'no area field -> 0 (acres() then uses the shape, as before)')
check(m.rec_ha({'SHAPE_Area': 5e9}, {'fields': [{'name': 'SHAPE_Area'}]}) == 0, 'a projection-unit SHAPE_Area is never taken as hectares')
check("'ha': 0, '_g': g, '_bb': bbox(g), 'src': label}\n                    r['_k'] = kinds(nm) | next" not in SRC, "arc_pull no longer writes 'ha': 0")
print('ALL PASS' if not bad else f'{len(bad)} FAILED'); sys.exit(1 if bad else 0)
