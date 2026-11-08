#!/usr/bin/env python3
"""Nov 8 (Brandon 4:31 PM CST, t764u): the Tool Box searches PAD-US / CPCAD AND the state / province layers, merges the same land,
keeps state-only finds as their own places, one status line per source. Nov 8 4:33 PM (t765u): 'Looks new' is now 'Possible candidate'."""
import json, re, subprocess, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
js = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
reg = json.loads((ROOT / 'data/maprep-state-layers.json').read_text(encoding='utf-8'))['areas']
L = [x for a in reg.values() for x in a]
BAN = re.compile(r'ncnhde\.natureserve\.org|services\.arcgis\.com/33TOOklri9xpic7U|maps\.gov\.bc\.ca', re.I)
check(len(L) > 100 and any(x['ok'] for x in L), 'layer list built (%d layers, %d usable)' % (len(L), sum(x['ok'] for x in L)))
check(not any(x['ok'] and re.match(r'https://services\d*\.arcgis\.com/', x['url'], re.I) for x in L), 'no services*.arcgis.com layer is used (robots 403 = disallow)')
check(not any(x['ok'] and BAN.search(x['url']) for x in L), 'no banned host is used')
check(not any(x['ok'] and re.search(r'hub\.arcgis\.com|opendata\.arcgis\.com', x['url']) for x in L), 'no hub portal is read live')
check(all(x['ok'] is False or (x['field'] and x['url'].startswith('https://')) for x in L), 'every usable layer has a name field and https')
check(all(x.get('why') for x in L), 'every layer says why it is used or skipped')
check('BANNED.test(L.url)' in js and 'Math.min(4, LS.length)' in js and 'slQuery(o.L, params(o.L), 25000)' in js, 'layers: banned hosts refused, 4 at a time, 25 s each')
check(js.count('await mergeSources(places') == 2, 'Search and Check all both merge the state layers')
check("stLine(o.L.label + ': '" in js and 'data-rsretry' in js, 'one status line per source; a failed one gets TRY AGAIN and the search goes on')
check("label: 'Possible candidate'" in js and "new: 'Possible candidate'" in js and not re.search(r'[Ll]ooks? new', js), "'Looks new' renamed 'Possible candidate'")
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html', '.claude/build/maprep/main.html'):
    h = (ROOT / f).read_text(encoding='utf-8')
    check(not re.search(r'[Ll]ooks? new', h) and '“Possible candidate”' in h and 'kpc-maprep-research.js?v=20261108u' in h, f + ': help text renamed, new script version')
check(not re.search(r'just opened|newly opened park|new(ly)? open', js.replace('not newly opened land', '')), 'no wording says the place just opened')
node = r"""
global.window = {}; const R = require(%s);
const sq = (x0, y0, d) => ({ type: 'Polygon', coordinates: [[[x0, y0], [x0 + d, y0], [x0 + d, y0 + d], [x0, y0 + d], [x0, y0]]] });
const pad = [{ kind: 'pad', name: 'Red Rock Wildlife Management Area', source: 'USGS PAD-US 4.0', ids: [1], acres: 30000, geoms: [sq(-93, 41, 0.1)] },
             { kind: 'pad', name: 'Lake Macbride State Park', source: 'USGS PAD-US 4.0', ids: [2], acres: 2000, geoms: [sq(-91.6, 41.8, 0.03)] }];
const st = [{ kind: 'state', name: 'Red Rock WMA', source: 'Iowa DNR', layer: 'sgiaa', id: 'sgiaa5', acres: 29000, geom: sq(-92.995, 41.005, 0.09), link: 'x' },
            { kind: 'state', name: 'Lake Macbride State Park', source: 'Iowa DNR', layer: 'sgiaa', id: 'sgiaa6', acres: 2000, geom: sq(-91.6, 41.8, 0.03), link: 'y' },
            { kind: 'state', name: 'Hidden Prairie Area', source: 'Iowa DNR', layer: 'sgiaa', id: 'sgiaa7', acres: 300, geom: sq(-94, 42, 0.02), link: 'z' },
            { kind: 'state', name: 'Hidden Prairie Area', source: 'Iowa DNR 2', layer: 'sgiab', id: 'sgiab1', acres: 300, geom: sq(-94, 42, 0.02), link: 'w' },
            { kind: 'state', name: 'Tiny Lot', source: 'Iowa DNR', layer: 'sgiaa', id: 'sgiaa8', acres: 3, geom: sq(-95, 42, 0.001), link: 'v' }];
(async () => {
  const m = await R.mergeSources(pad, st), S = R.srcStats(m);
  console.log(JSON.stringify({ names: m.map(p => p.name + '|' + p.kind + '|' + (p.sources || []).join('+')), S, xids: m[0].xids, acres: Math.round(R.geomAcres(sq(-93, 41, 0.1))), cap: R.capName("DEWEY'S PASTURE-NORTH UNIT") }));
})();
""" % json.dumps(str(ROOT / 'kpc-maprep-research.js'))
r = subprocess.run(['node', '-e', node], capture_output=True, text=True, timeout=30)
check(r.returncode == 0, 'node ran the merge ' + r.stderr[:200])
o = json.loads((r.stdout or '{}').strip().splitlines()[-1] if r.stdout else '{}')
check(o.get('names') == ['Red Rock Wildlife Management Area|pad|USGS PAD-US 4.0+Iowa DNR', 'Lake Macbride State Park|pad|USGS PAD-US 4.0+Iowa DNR', 'Hidden Prairie Area|state|Iowa DNR+Iowa DNR 2'],
      'same land merged (name + overlap), state-only kept as its own place with its source, two layers of one place merged, under 20 acres dropped: ' + str(o.get('names')))
check(o.get('S') and o['S']['both'] == 2 and o['S']['stateOnly'] == 1 and o['S']['padOnly'] == 0, 'counts: in both / PAD-US only / state only')
check(o.get('xids') == ['sgiaa5'], 'a merged place keeps the state record id (the answer key can match it)')
check(o.get('acres') and 20000 < o['acres'] < 26000, 'acres from the outline (0.1 degree square in Iowa ~ 23,000 acres)')
check(o.get('cap') == "Dewey's Pasture-North Unit", 'ALL CAPS names shown in normal case')
# Nov 8 (t766u): owner / manager / designation / acres / website from the state layers, each fact named by its layer
check(sum(1 for x in L if x['ok'] and (x.get('facts') or {}).get('owner')) >= 20 and sum(1 for x in L if x['ok'] and (x.get('facts') or {}).get('manager')) >= 20, 'fact fields found on the state layers')
check(not any(re.search(r'(_st|_id|syst|placename|code)$', str((x.get('facts') or {}).get(k) or ''), re.I) for x in L for k in ('owner', 'manager', 'agency')), 'no id, state-code or place-name field is taken for an owner or manager')
node2 = r"""
global.window = {}; const R = require(%s);
const sq = (x0, y0, d) => ({ type: 'Polygon', coordinates: [[[x0, y0], [x0 + d, y0], [x0 + d, y0 + d], [x0, y0 + d], [x0, y0]]] });
const Lr = { pre: 'sgiac', url: 'https://x/query', field: 'NAME', label: 'Iowa DNR \u00b7 Public Lands', facts: { owner: 'OWNER', manager: 'MANAGER', designation: 'TYPE', acres: 'ACRES', website: 'More_Info' } };
const r = R.slRec(Lr, { id: 5, geometry: sq(-93, 41, 0.1), properties: { NAME: 'RED ROCK WMA', OWNER: 'US Army Corps of Engineers', MANAGER: 'Iowa DNR', TYPE: 'Wildlife Area', ACRES: '29,800', More_Info: 'https://www.iowadnr.gov/redrock' } });
const pad = [{ kind: 'pad', name: 'Red Rock Wildlife Management Area', source: 'USGS PAD-US 4.0', ids: [1], acres: 30000, owner: 'Private Landowner (Private)', manager: 'DNR - Wildlife', designation: 'State Wildlife Management Area', geoms: [sq(-93, 41, 0.1)] }];
const st = [Object.assign({}, r)];
(async () => { const m = await R.mergeSources(pad, st);
  const only = await R.mergeSources([], [Object.assign({}, r)]);
  console.log(JSON.stringify({ rec: [r.owner, r.manager, r.designation, Math.round(r.acres)], rows: R.factRows(m[0]).map(x => [x.k, x.vals.map(v => v.v + '@' + v.src), x.differ]), only: R.factRows(only[0]).map(x => x.k), sum: R.summaryText(Object.assign(m[0], { verdict: { label: 'x', why: 'y' } })) })); })();
""" % json.dumps(str(ROOT / 'kpc-maprep-research.js'))
r2 = subprocess.run(['node', '-e', node2], capture_output=True, text=True, timeout=30)
check(r2.returncode == 0, 'node ran the facts ' + r2.stderr[:200])
o2 = json.loads(r2.stdout.strip().splitlines()[-1]) if r2.stdout.strip() else {}
check(o2.get('rec') == ['US Army Corps of Engineers', 'Iowa DNR', 'Wildlife Area', 29800], 'state record: owner, manager, designation and acres from the layer fields')
rows = {x[0]: x for x in o2.get('rows', [])}
check(rows.get('owner') and rows['owner'][2] is True and 'US Army Corps of Engineers@Iowa DNR \u00b7 Public Lands' in rows['owner'][1] and any('USGS PAD-US' in v for v in rows['owner'][1]), 'PAD-US and the state layer disagree on the owner: both shown, sources differ')
check(rows.get('acres') and rows['acres'][2] is False, 'acres within 25%%: no differ flag'.replace('%%', '%'))
check(rows.get('website') and 'https://www.iowadnr.gov/redrock@Iowa DNR \u00b7 Public Lands' in rows['website'][1], 'website from the layer')
check(o2.get('only') and 'owner' in o2['only'] and 'manager' in o2['only'], 'state-only place lists its owner and manager by source')
check('[sources differ]' in o2.get('sum', '') and 'Owner: ' in o2.get('sum', ''), 'the summary to copy names each source and marks sources differ')
cj = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
check("'owner field on ' + SF.owner.src" in cj and "'manager field on ' + SF.manager.src" in cj and cj.count('(sources differ).') == 2 and 'stateFacts: (sf.owner || sf.manager) ? sf : null' in cj, 'rules: state owner / manager used when PAD-US has none, a disagreement is noted as sources differ')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
