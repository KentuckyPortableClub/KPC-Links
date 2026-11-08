#!/usr/bin/env python3
"""Nov 8 (Brandon 8:49 / 8:50 AM CST): the Tool Box lists the PAD-US record in plain words near the top of the place card,
and a one-line PAD-US summary under each name-search result. Every code shows its meaning; a source line names PAD-US 4.0."""
import json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
js = r"""
global.KPCMapLogic = require('./kpc-maprep-logic.js');
const X = require('./kpc-maprep-extras.js');
const yb = { OBJECTID: 201323, Category: 'Fee', Own_Type: 'JNT', Own_Name: 'JNT', Loc_Own: 'Kentucky Department of Fish and Wildlife Resources; Breckenridge County Fiscal Court',
  Mang_Type: 'STAT', Mang_Name: 'SFW', Loc_Mang: 'Kentucky Department of Fish and Wildlife Resources', Des_Tp: 'SCA', Loc_Ds: 'Wildlife Management Area',
  Unit_Nm: 'Yellowbank Wildlife Management Area', State_Nm: 'KY', Agg_Src: 'KSNPC_PADUS1_4_KY', GIS_Src: 'KDFWR_Wildlife_Management_Area (2012-shapefile)',
  Src_Date: '2012/08/15', GIS_Acres: 1112, Source_PAID: 'KY0000140', Pub_Access: 'RA', GAP_Sts: '2', Date_Est: '2009', Comments: '' };
const open = Object.assign({}, yb, { Own_Type: 'STAT', Own_Name: 'SFW', Pub_Access: 'OA' });
console.log(JSON.stringify({ card: X.padCard(yb, 'https://x/query?objectIds=201323'), line: X.padLine(yb), lineOpen: X.padLine(open), hintOpen: X.padHint(open), none: X.padLine(null) }));
"""
r = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, timeout=60)
check(r.returncode == 0, 'node ran ' + r.stderr[:300])
o = json.loads(r.stdout or '{}'); c = o.get('card', '')
for lab in ['Owner', 'Manager', 'Designation', 'Public access', 'GAP status', 'GIS acres', 'Date established', 'State', 'Source', 'Data provider', 'Comments', 'Joint ownership', 'Record ID']:
    check('<th>' + lab + '</th>' in c, 'card row: ' + lab)
check('RA = Restricted Access' in c and 'SFW = State Fish and Wildlife' in c and 'JNT = Joint' in c and 'SCA = State Conservation Area' in c, 'codes shown with their meaning')
check('GAP 2 = managed for biodiversity' in c and '1,112 acres' in c and '2009' in c, 'GAP in words, acres, date established')
check('objectIds=201323' in c and 'OBJECTID 201323' in c and 'KY0000140' in c, 'record id with a link')
check('USGS PAD-US 4.0' in c and 'federal inventory of public lands' in c and 'confirm with the managing agency' in c, 'where this comes from')
check('Public access: Open, which counts toward the public-access rule.' in o['hintOpen'], 'plain hint for open access')
check(o['line'].startswith('PAD-US: Owner Kentucky Department of Fish and Wildlife Resources; Breckenridge County Fiscal Court (Joint)') and 'Access Restricted' in o['line'] and o['line'].endswith('Wildlife Management Area'), 'compact result line')
check('Access Open' in o['lineOpen'] and o['none'] == 'PAD-US: no matching record', 'compact line variants')
low = c.lower()
check(not any(w in low for w in [' bot', 'automat', 'robot']), 'no bot wording on the card')
chk = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
check('mr-padtop' in chk and 'KPCMapExtras.padCard(ctx.padExact' in chk, 'card shows the record right under the heading')
check('data-padline' in chk and 'padLines(exact, st, my)' in chk and 'KPCMapExtras.padLine(a)' in chk, 'results list shows one PAD-US line per result')
check('Date_Est,Comments,Agg_Src,GIS_Src,Src_Date' in chk and 'function padTable' in chk, 'new fields asked for; old record table kept')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
