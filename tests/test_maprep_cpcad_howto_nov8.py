#!/usr/bin/env python3
"""Nov 8 (Brandon 8:57 AM CST, "Cpcad and 6"): the CPCAD record card for Canadian places (card + result line + rules), and a
collapsible "How to use this page" panel for new reps on the Tool Box and the reps page. No bot wording."""
import json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
js = r"""
global.KPCMapLogic = require('./kpc-maprep-logic.js');
const X = require('./kpc-maprep-extras.js');
const alg = { NAME_E: 'Algonquin Provincial Park (Natural Environment Class)', NAME_IND: null, PA_OECM_DF: 1, IUCN_CAT: 3, STATUS: 1, QUALYEAR: 1893, ESTYEAR: 1893, BIOME: 'T', LOC: 9,
  O_AREA_HA: 264674, PARENT_ID: 350036900, ZONE_ID: 350036900, ZONEDESC_E: null, MECH_E: 'Provincial Parks and Conservation Reserves Act, 2006', TYPE_E: 'Provincial Park',
  OWNER_TYPE: 2, OWNER_E: 'Province of Ontario', GOV_TYPE: 2, MGMT_E: 'Ontario Parks', JUR_ID: 'P1915', MPLAN: 1, MPLAN_REF: 'https://www.ontario.ca/page/provincial-park-management-direction', OBJECTID: 16243 };
const jnt = Object.assign({}, alg, { OWNER_TYPE: 9, STATUS: 0 });
console.log(JSON.stringify({ card: X.caCard(alg, 'https://maps-cartes.ec.gc.ca/x?objectIds=16243'), line: X.caLine(alg), hint: X.caHint(alg), jcard: X.caCard(jnt, ''), jhint: X.caHint(jnt), none: X.caLine(null) }));
"""
r = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, timeout=60)
check(r.returncode == 0, 'node ran ' + r.stderr[:300])
o = json.loads(r.stdout or '{}'); c = o.get('card', '')
for lab in ['Name', 'Owner / authority', 'Manager / governance', 'Type / designation', 'IUCN category', 'Status and year', 'Area', 'Biome / zone', 'Record ID']:
    check('<th>' + lab + '</th>' in c, 'card row: ' + lab)
check('2 = Provincial / territorial' in c and '2 = Sub-national (provincial / territorial) government' in c, 'owner and governance codes in words')
check('II = national park' in c and '1 = Designated' in c and 'established 1893' in c, 'IUCN in words, status and year')
check('264,674 ha (654,023 acres)' in c and 'T = Terrestrial / freshwater' in c and '9 = Ontario' in c, 'area in ha and acres, biome and zone')
check('ZONE_ID 350036900' in c and 'objectIds=16243' in c, 'record id with a link')
check('Environment and Climate Change Canada' in c and 'Open Government Licence - Canada' in c and 'confirm with the managing agency' in c and 'CPCAD, December 2025' in c, 'where this comes from')
check('counts toward the government-owned rule' in o['hint'] and 'no public-access field' in o['hint'], 'plain rule hints')
check('<th>Joint ownership</th>' in o['jcard'] and 'Delisted' in o['jhint'], 'joint ownership row and delisted hint')
check(o['line'].startswith('CPCAD: Owner Province of Ontario (Provincial / territorial) · Manager Ontario Parks · Provincial Park · Designated 1893') and o['none'] == 'CPCAD: no matching record', 'compact result line')
chk = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
check('maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0/query' in chk and 'ncnhde' not in chk, 'CPCAD from the catalog source; ncnhde never asked')
check("'CPCAD OWNER_TYPE'" in chk and "'CPCAD GOV_TYPE'" in chk and "'CPCAD TYPE_E'" in chk and "CPCAD ZONE_ID" in chk, 'rules checklist reads CPCAD for Canadian places')
check('KPCMapExtras.caCard(ctx.caExact' in chk and 'X.caLine(c)' in chk and 'CPCAD records with this name' in chk and 'cpcadAt(la, lo).then' in chk, 'card, result lines, could-this-be-a-park list, pin')
cat = json.loads((ROOT / 'data/maprep/catalog.json').read_text(encoding='utf-8'))
src = [s for s in cat['sources'] if s.get('id') == 'ca-cpcad']
check(src and src[0].get('live') and src[0].get('enabled'), 'ca-cpcad is a live, enabled catalog source')
for f in ['kpc-maprep.html', 'kpc-maprep-reps.html', '.claude/build/maprep/main.html']:
    t = (ROOT / f).read_text(encoding='utf-8')
    i = t.find('id="mrHowTo"'); h = t[i:t.find('</details>', i)]
    check(i > 0 and 'HOW TO USE THIS PAGE' in h and all(w in h for w in ['state or province', 'drop a pin', 'official record card', 'CHECK ALL', 'official links', 'Research on this place', 'limited-maps note', 'not the final word']), f + ': how-to panel with every step and the disclaimer')
    check(not any(w in h.lower() for w in [' bot', 'automat', 'robot', ' ai ']), f + ': no bot wording in the how-to')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
