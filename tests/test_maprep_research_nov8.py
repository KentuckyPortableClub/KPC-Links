#!/usr/bin/env python3
"""Nov 8 (Brandon 11:19 AM CST): the Mapping Rep Tool Box is a research tool first. "Find new parks to add" sits at the top and
checks every official place by itself (same record in the answer key, key outlines over it, pins inside, same name nearby),
gives a verdict and a summary to copy; the published key list is folded below with a plain explanation; "Possible new parks"
rows can run the same full checks. Every earlier feature is still there (inventory taken on main before this change)."""
import json, pathlib, re, subprocess, sys, importlib.util
ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)

html = (ROOT / 'kpc-maprep-reps.html').read_text(encoding='utf-8')
js = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
chk = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
cand = (ROOT / 'kpc-maprep-candidates.js').read_text(encoding='utf-8')
# 1. layout: research first, check-a-place after, script loaded, gate kept
check(0 < html.find('id="mrResearch"') < html.find('id="mrCheckCard"'), 'Find new parks is above Check a place')
check(html.find('id="mrResearch"') > html.find('id="mrApp"'), 'the research section is inside the password-locked app')
for i in ('mrRsPlace', 'mrRsFind', 'mrRsNear', 'mrRsQ', 'mrRsTest', 'mrRsMsg', 'mrRsOut'):
    check(f'id="{i}"' in html, f'control {i}')
check('kpc-maprep-research.js?v=' in html and 'kpc-maprep-gate.js' in html and 'id="mrLock"' in html, 'research script loaded; both password doors kept')
check('Find new parks first.' in html, 'how-to starts with finding new parks')
# 2. published key folded, with an explanation; agency links and possible new parks stay open above it
check('function foldKey' in chk and chk.count('foldKey(box, stAll.name)') == 2, 'both published-key lists are folded')
check('bonus reference, not the research tool' in chk and "['mrAgDrop', 'mrCandsWrap']" in chk, 'fold explains itself; agency links and possible new parks stay outside the fold')
check('data-rstest=' in cand and 'RUN THE FULL NEW-PARK CHECKS' in cand, 'possible new parks rows run the full checks, not only pins')
check('async function areaLayers' in chk and chk.count('areaLayers(stAll, box)') == 3 and 'id="mrAreaFilters"' in chk and 'R.classify(stAll.code' in chk,
      'Check All everywhere works like Kentucky: official layers first, Yes / Maybe / No / Already filters')
check("code === 'KY'" in js and 'No national list of protected places is wired' in js, 'Kentucky keeps its own layers; world places without a national list say so')
check('padExact' in chk[chk.find('async function areaLayers'):] and "'ALREADY'" in chk[chk.find('async function areaLayers'):], 'area rows use the same rules checklist as Kentucky, refs count as already')
# 3. sources: only the two approved official services, nothing banned, no secrets
hosts = set(re.findall(r'https://([a-z0-9.-]+)', js))
check(hosts <= {'edits.nationalmap.gov', 'maps-cartes.ec.gc.ca', 'tile.openstreetmap.org'}, f'only approved hosts in the research script {sorted(hosts)}')
check('ncnhde' not in js.replace('ncnhde\\.natureserve', '') and 'BANNED' in js, 'banned hosts are refused, never requested')
check(not re.search(r'(api[_-]?key|token|secret|password)\s*[:=]', js, re.I), 'no keys or secrets')
check(not re.search(r'\b(bot|AI|agent)\b', re.sub(r'<[^>]+>', ' ', html[html.find('id="mrResearch"'):html.find('id="mrCheckCard"')])), 'no bot wording in the new section')
# 4. logic, under node
node = r"""
const R = require('./kpc-maprep-research.js');
const sq = (x, y, d) => ({ type: 'Polygon', coordinates: [[[x, y], [x + d, y], [x + d, y + d], [x, y + d], [x, y]]] });
const out = {};
out.same = R.sameName('Appalachian National Scenic Trail', 'Appalachian Trail National Scenic Trail');
out.diff = R.sameName('Wolf Run Wild Area', 'Wolf Run State Park') === true && R.sameName('Quehanna Wild Area', 'Moshannon State Forest') === false;
out.cover1 = R.coverShare(sq(0, 0, 1), [sq(-1, -1, 3)]);
out.cover0 = R.coverShare(sq(0, 0, 1), [sq(5, 5, 1)]);
out.half = R.coverShare(sq(0, 0, 1), [sq(0, 0, 0.5).coordinates ? { type: 'Polygon', coordinates: [[[0, 0], [0.5, 0], [0.5, 1], [0, 1], [0, 0]]] } : null]);
out.v1 = R.verdict({ same: ['US-1'] }).v;
out.v2 = R.verdict({ cover: [{ ref: 'US-2', share: 0.8, same: true }] }).v;
out.v3 = R.verdict({ cover: [{ ref: 'US-3', share: 0.95, same: false }] }).v;
out.v4 = R.verdict({ named: [{ ref: 'US-4', km: 3 }] }).v;
out.v5 = R.verdict({ pinIn: ['US-5'] }).v;
out.v6 = R.verdict({ cover: [{ ref: 'US-6', share: 0.2 }] });
out.v7 = R.verdict({ acc: 'restricted' }).v;
out.v8 = R.verdict({ nearest: { ref: 'US-8', km: 4.2 } });
out.g = R.groupRecords([{ id: 1, name: 'A Wild Area', manager: 'X', acres: 10 }, { id: 2, name: 'A Wild Area', manager: 'X', acres: 5 }, { id: 3, name: 'B', manager: 'X', acres: 50 }]).map(p => [p.name, p.ids, p.acres]);
out.ky = 0; out.sum = R.summaryText({ name: 'Test', place: 'Pennsylvania', designation: 'Wild Area', manager: '', owner: 'PA Bureau of Forestry (State)', access: 'open', acres: 1234, source: 'USGS PAD-US 4.0', ids: [9], link: 'L', verdict: { label: 'Possible candidate', why: 'w' } });
console.log(JSON.stringify(out));
"""
r = subprocess.run(['node', '-e', node], cwd=ROOT, capture_output=True, text=True)
o = json.loads(r.stdout or '{}') if r.returncode == 0 else {}
check(r.returncode == 0, 'research logic loads under node ' + r.stderr[-200:])
check(o.get('same') is True and o.get('diff') is True, 'name match: same words in any order, or one name inside the other (distance limits it); different names do not match')
check(o.get('cover1') == 1 and o.get('cover0') == 0 and 0.3 < (o.get('half') or 0) < 0.7, 'outline cover share (all, none, about half)')
check([o.get(k) for k in ('v1', 'v2', 'v3', 'v4', 'v5', 'v7')] == ['already', 'already', 'person', 'probably', 'probably', 'person'],
      'verdicts: same record / same-name outline = already; inside another park = possible 2-fer; same name or pin inside = probably; restricted = person')
check((o.get('v6') or {}).get('v') == 'person' and '2-fer' in (o.get('v6') or {}).get('why', ''), 'partial overlap = needs a person (part of a park or a 2-fer)')
check((o.get('v8') or {}).get('v') == 'new' and 'US-8, 4.2 km' in (o.get('v8') or {}).get('why', ''), 'possible candidate names the nearest POTA park and distance')
check(o.get('g') == [['B', [3], 50], ['A Wild Area', [1, 2], 15]], 'records of one place are grouped, largest first')
s = o.get('sum') or ''
check(all(x in s for x in ('Proposed park: Test', 'Managed by: not stated', 'Official record: USGS PAD-US 4.0, id 9', 'POTA check: Possible candidate', 'Confirm with the managing agency')), 'copy-ready summary')
# 5. feature inventory: every item listed on main before this change is still there
spec = importlib.util.spec_from_file_location('fi', ROOT / '.github/scripts/kpc_feature_inventory.py'); fi = importlib.util.module_from_spec(spec); spec.loader.exec_module(fi)
base = json.loads((ROOT / 'tests/features-maprep.json').read_text(encoding='utf-8'))
gone = [f'{f}: {x}' for f, xs in base.items() for x in xs if x not in fi.items((ROOT / f).read_text(encoding='utf-8'))]
check(sum(map(len, base.values())) >= 400 and not gone, f'feature inventory: {sum(map(len, base.values()))} items, none gone {gone[:5]}')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
