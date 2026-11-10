#!/usr/bin/env python3
"""Nov 6 follow-up key / 2-fer patch (Brandon [pt449u], from the KY GIS Workbench v2 'FIND NEW', BDW-Coils PR #2):
the 0.25 mi pin coverage report, the workbench name matcher in the two-name check, the 'also in' layer notes, and the recorded-acres
field order checked against the workbench's candInfo() (GIS_Acres -> ACRES_CAL -> ACRES -> ABSOLUTE_ACREAGE, case-insensitive).
All four are REPORT ONLY: none is a rules file of any key, and the post-key check runs them with continue-on-error."""
import pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_freeze as KZ
import kpc_source_fields as SF
ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)

NEW = ('kpc_pin_cover.py', 'kpc_also_in.py', 'kpc_name_match.py', 'kpc_two_name_check.py')
for s in NEW:
    r = subprocess.run([sys.executable, '-B', str(ROOT / '.github/scripts' / s), '--selftest'], capture_output=True, text=True, timeout=120, cwd=ROOT)
    check(f'{s} --selftest: ' + (r.stdout.strip().splitlines() or ['?'])[-1], r.returncode == 0 and 'OK' in r.stdout)
    check(f'{s}: not a rules file of any key (no rules hash change)', all(s not in ' '.join(v) for v in KZ.RULE_FILES.values()))
for s in NEW[:3]:
    check(f'{s}: listed in NOT_RULES', s in KZ.NOT_RULES)
# Nov 7 world rebuild (B1 B2 B3 B4 B6, world-failed-diagnosis.md section 7; Brandon OK'd the world hash move): kpc_world_key.py
# changed on purpose, so the world rules hash moved 1b50faf1dfe8 -> 6a5969a25d2c. US and CA stay; this check still pins all three.
check('rules hashes stay us bbdcc89f8120, ca 570b09c3cb52, world 6444287722b9',
      (KZ.rules_hash('us-key'), KZ.rules_hash('ca-key'), KZ.rules_hash('world-key')) == ('bbdcc89f8120', '570b09c3cb52', '6444287722b9'))
for b in ('kpc_us_key.py', 'kpc_ca_key.py', 'kpc_world_key.py', 'kpc_fers.py', 'kpc_fers_count.py', 'kpc_join_check.py'):
    t = (ROOT / '.github/scripts' / b).read_text(encoding='utf-8')
    check(f'{b} imports none of the new report helpers (joins cannot change)', not any(n[:-3] in t for n in NEW[:3]))
y = (ROOT / '.github/workflows/kpc-key-postcheck.yml').read_text()
i = y.find('- name: Key trend + two-name parks'); st = y[i:].split('\n      - name:', 1)[0] if i >= 0 else ''
check('post-key check runs pin cover + also-in in the report-only step', 'kpc_pin_cover.py' in st and 'kpc_also_in.py' in st and 'continue-on-error: true' in st)
check('the report-only step pushes nothing itself', 'git push' not in st and 'kpc_push' not in st and 'secrets.' not in st)

# (d) recorded-acres order: the workbench reads the FIRST of these that the record has (fieldVal is case-insensitive)
WB_ORDER = ['GIS_Acres', 'ACRES_CAL', 'ACRES', 'ABSOLUTE_ACREAGE']
# the workbench's own layer list (BDW-Coils tools/ky-gis-layers.json, Nov 6): id, url, the acre fields it lists
WB_LAYERS = [
    ('kyl_kdfwr_hunting', 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Public_Hunting_Areas_WGS84WM/MapServer/1', ['ACRES_CAL']),
    ('kyl_state_parks_boundary', 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_State_Parks_Features_WGS84WM/MapServer/8', ['ABSOLUTE_ACREAGE', 'STATE_OWNED_ACREAGE', 'LEASED_ACREAGE', 'TERRA_FIRMA_ACREAGE']),
    ('kyl_snp', 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0', ['ACRES']),
    ('kyl_sna', 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_KNP_Natural_Areas_WGS84WM/MapServer/0', ['ACRES']),
    ('ky_wild_rivers', 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_KNP_Wild_River_Corridors_WGS84WM/MapServer/0', ['ACRES']),
    ('ky_state_forests', 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_StateForests_WGS84WM/MapServer/1', ['ACRES']),
    ('ky_hlcf', 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_KNP_Heritage_Land_Conservation_Fund_WGS84WM/MapServer/0', ['ACRES']),
    ('ky_dbnf_boundary', 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_DBNF_Boundary_Polygon_WGS84WM/MapServer/0', ['GIS_ACRES']),
    ('padus_fee', 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0', ['GIS_Acres']),
    ('usfs_forest_boundaries', 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_ForestSystemBoundaries_01/MapServer/0', ['gis_acres']),
    ('fws_interest', 'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0', ['SUM_GISACRES']),
]
for lid, url, fs in WB_LAYERS:
    lo = {f.lower(): f for f in fs}
    wb = next((lo[w.lower()] for w in WB_ORDER if w.lower() in lo), None)
    ours = SF.mapping(url, fields=fs).get('acres')
    if lid == 'fws_interest':   # the workbench has no FWS acres field and measures the shape; we read FWS's own SUM_GISACRES (better)
        check('fws_interest: workbench reads no recorded acres, the key reads SUM_GISACRES (documented difference)', wb is None and ours == 'SUM_GISACRES')
    else:
        check(f'{lid}: recorded-acres field is the same as the workbench ({wb})', wb == ours)
# a record with BOTH a 'GIS_Acres' and an 'ACRES': the workbench takes GIS_Acres first; so does the table's AUTO reader
mp = SF.mapping('https://example.gov/arcgis/rest/services/X/MapServer/0', fields=['OBJECTID', 'NAME', 'GIS_Acres', 'ACRES'])
check('AUTO layer with GIS_Acres + ACRES picks GIS_Acres (workbench order)', mp.get('acres') == 'GIS_Acres')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
