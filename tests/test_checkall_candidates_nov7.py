#!/usr/bin/env python3
"""Nov 7: Check all "possible new parks" (kpc-maprep-candidates.js) and the official agency-link dropdown.
Brandon's rules (Nov 7, rounds 1-3): list OFF by default (candidatesOn), dropdown ON; MIT left out; LP/LREC/LHCA kept and
flagged; university land kept and flagged (Moundville stays); Unknown manager flagged; Corps land kept; "Mobile" shown raw
unless the manager/owner text says Corps; acre floor default 5 and adjustable; kind check (Little River WMA vs Little River
State Forest); the one Alabama State Parks finder link hidden; no row cap ("Show more" paging).
Runs the UMD module under node on the real Alabama key (data/us-key/US-AL.json). Writes nothing."""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


NODE = r'''
const fs = require('fs'), path = require('path');
const root = process.argv[1];
const L = require(path.join(root, 'kpc-maprep-logic.js'));
const C = require(path.join(root, 'kpc-maprep-candidates.js'));
L.loadRows(JSON.parse(fs.readFileSync(path.join(root, 'data/maprep/abbreviations.json'), 'utf8')).rows);
L.loadAgencies(JSON.parse(fs.readFileSync(path.join(root, 'data/maprep/agencies.json'), 'utf8')));
const src = fs.readFileSync(path.join(root, 'kpc-maprep.js'), 'utf8');
const m = src.match(/const FEDA = (\[[^\n]*\]);/);
const FEDA = m ? eval(m[1]) : [];
const key = JSON.parse(fs.readFileSync(path.join(root, 'data/us-key/US-AL.json'), 'utf8'));
const out = {};
out.offDefault = C.candidatesOn();
globalThis.location = { search: '?x=1&candidates=1' };
out.onByUrl = C.candidatesOn();
globalThis.location = { search: '?candidates=0' };
out.offByUrl0 = C.candidatesOn();
globalThis.localStorage = { getItem: k => (k === 'kpcMapCandidates' ? '1' : null) };
out.onByStorage = C.candidatesOn();
delete globalThis.location; delete globalThis.localStorage;
out.offAgain = C.candidatesOn();

const res = C.fromNonum(key, null, {});
const by = n => res.rows.find(r => r.name === n) || null;
const slim = r => r && { name: r.name, acres: r.acres, flags: r.flags, flagText: r.flagText, managers: r.managers, des: r.des, ids: r.ids, similar: r.similar };
out.al = { floor: res.floor, from: res.from, inFile: res.inFile, total: res.total, dropped: res.dropped, droppedRows: res.droppedRows,
  groups: res.groups, same: res.sameAsKey.length, hiddenSmall: res.hiddenSmall, rows: res.rows.length, flags: C.flagCounts(res.rows),
  ids: [].concat.apply([], res.rows.map(r => r.ids.map(String))) };
out.named = {};
['Moundville Archeological Park', 'Metro Kiwanis Sportsplex', 'Eco Park at University Lake', 'Foscue Creek Park',
 'Walter F. George Recreation Area', 'Little River Wildlife Management Area', 'East Pinson Valley Community Park',
 'Weeks Bay Harris And Worcester Tracts', 'UAB Campus Green'].forEach(n => { out.named[n] = slim(by(n)); });
out.sameNames = res.sameAsKey.map(x => x.name);
out.floors = [0, 1, 5, 10, 40, 100].map(f => C.fromNonum(key, null, { floor: f }).rows.length);
out.floor0Gibbin = !!C.fromNonum(key, null, { floor: 0 }).rows.find(r => r.name === 'Gibbin Park');
out.listHtml = C.listHtml(res, 0, 'AL');
out.judge = {
  lrec: C.judgeRow([1, 'X Park', 'LREC', 'Shelby County', 50]),
  lhca: C.judgeRow([1, 'X Site', 'LHCA', 'Town of Y', 50]),
  lpCity: C.judgeRow([1, 'X Park', 'LP', 'Huntsville, City of', 50]),
  cityNoLocal: C.judgeRow([1, 'X Area', 'SCA', 'City of Montgomery', 50]),
  mit: C.judgeRow([1, 'X Bank', 'MIT', 'ADCNR, State Lands Division', 500]),
  dot: C.judgeRow([1, 'X Area', 'SCA', 'Alabama Department of Transportation', 500]),
  college: C.judgeRow([1, 'X Field', 'SOTH', 'Jefferson State Junior College', 50]),
  corps: C.judgeRow([1, 'X Lake', 'REC', 'US Army Corps of Engineers', 500]),
  mobile: C.judgeRow([1, 'X Lake', 'REC', 'Mobile', 500]),
  blank: C.judgeRow([1, 'X Lake', 'SCA', '', 500])
};
const UNIV_CASES = JSON.parse(process.argv[2]);
out.univ = { words: C.UNIV_WORDS_RE.source, wordsFlags: C.UNIV_WORDS_RE.flags, abbr: C.UNIV_ABBR_RE.source, abbrFlags: C.UNIV_ABBR_RE.flags,
  hits: UNIV_CASES.map(s => C.isUniversity(s)),
  judged: UNIV_CASES.map(s => C.judgeRow([1, 'X', 'SCA', s, 50]).flags.indexOf('university') >= 0) };
out.mgr = {
  raw: C.displayManager('Mobile'),
  rawOwnerNotCorps: C.displayManager('Mobile', 'State of Alabama'),
  confirmed: C.displayManager('Mobile District, U.S. Army Corps of Engineers'),
  ownerConfirms: C.displayManager('Mobile', 'US Army Corps of Engineers'),
  usace: C.displayManager('USACE Mobile'),
  other: C.displayManager('Tennessee Valley Authority (TVA)')
};
const syn = { st: 'US-ZZ', counts: { nonum: 700 }, parks: { 'US-9999': { n: 'Little River State Forest', m: [], c: [] } }, nonum: [] };
syn.nonum.push(['a1', 'Little River Wildlife Management Area', '', 'State Fish and Wildlife', 900]);
for (let i = 0; i < 699; i++) syn.nonum.push([100000 + i, 'Zz Candidate Number ' + i + ' Tract', 'SCA', 'State Lands', 1000 - i]);
const big = C.fromNonum(syn, null, { floor: 5 });
const pages = [];
let shown = C.PAGE;
for (let guard = 0; guard < 40; guard++) { const p = C.pageOf(big.rows, shown); pages.push(p.length); if (p.length >= big.rows.length) break; shown += C.PAGE; }
out.big = { rows: big.rows.length, first: C.pageOf(big.rows, 0).length, pages: pages, more: /SHOW MORE \(50 of 700\)/.test(C.listHtml(big, 0, 'ZZ')),
  littleKept: !!big.rows.find(r => r.name === 'Little River Wildlife Management Area'), littleSim: (big.rows.find(r => r.name === 'Little River Wildlife Management Area') || {}).similar };
const side = { state: 'ZZ', rows: 701, nonum: syn.nonum.concat([[999999, 'Zz Extra Small Piece', 'SCA', 'State Lands', 0]]), joined_since_cut: ['a1'] };
const viaSide = C.fromNonum(syn, side, { floor: 0 });
out.side = { from: viaSide.from, rows: viaSide.rows.length, little: !!viaSide.rows.find(r => r.name === 'Little River Wildlife Management Area') };
const keyOnly = C.fromNonum({ st: 'US-ZZ', counts: { nonum: 309 }, parks: {}, nonum: syn.nonum.slice(1, 301) }, null, { floor: 5 });
out.cutNote = /holds 300 of 309 rows/.test(C.listHtml(keyOnly, 0, 'ZZ'));
out.noNonum = { avail: C.fromNonum({ parks: {} }, null, {}).available, html: C.listHtml(null) };

const al = C.agencyOptions('AL', 'US', FEDA);
out.agAL = { groups: al.groups.map(g => ({ label: g.label, items: g.items.map(i => ({ label: i.label, url: i.url, verified: i.verified, slot: i.slot })) })), hidden: al.hidden };
out.agMB = C.agencyOptions('MB', 'CA', FEDA);
out.agGB = C.agencyOptions('GB', 'world', FEDA);
out.allFinders = 0; out.keptFinders = 0;
Object.keys(JSON.parse(fs.readFileSync(path.join(root, 'data/maprep/agencies.json'), 'utf8')).places).forEach(code => {
  const reg = L.placeByCode(code) ? L.placeByCode(code).region : 'US';
  const o = C.agencyOptions(code, reg, FEDA);
  L.agencyMatches(code, '').forEach(a => { if (a.finder && a.finder.url && !L.isBanned(a.finder.url)) out.allFinders++; });
  o.groups.forEach(g => g.items.forEach(i => { if (i.slot === 'finder') out.keptFinders++; }));
});
out.dropAL = C.dropdownHtml('AL', 'US', FEDA, 'Alabama');
out.dropGB = C.dropdownHtml('FR', 'world', FEDA, 'France');
out.feda = FEDA.map(f => f[1]);
process.stdout.write(JSON.stringify(out));
'''

# Nov 7 round 4: the shared university rule (same source strings as the pile-solver design's Python copy)
UNIV_YES = ['UAB', 'UA', 'UNA', 'UAH', 'University of Alabama', 'University of North Alabama', 'Auburn University', 'Jacksonville State',
            'Jacksonville State University', 'Troy University', 'Jefferson State Junior College', 'Hendrix College', 'Bismarck State College',
            'State University', 'Univ. of Kentucky', 'Univ of Kentucky', 'UK', 'Board of Regents', 'University System of Georgia Board of Regents',
            'Univeristy of Texas A & M', 'SUNY College of Environmental Science and Forestry', 'MSU', 'WASHINGTON UNIVERSITY',
            'Michigan College of Mining and Technology', 'University of Maine System']
UNIV_NO = ['Universal', 'Universal Studios', 'Collegeville', 'Borough of Collegeville', 'College Street Park', 'College Park, City of',
           'City of College Station', 'Borough of State College', 'State College Area School District', 'College Avenue Greenway',
           'USA', 'US Army Corps of Engineers', 'Texas A&M Forest Service', 'INDEPENDENT SCHOOL DIST NO 1', 'Milford School District',
           'Texas General Land Office - School Land Board', 'The State of Utah School and Institutional Trust Lands Administration',
           'Ohio DNR, Office of Information Technology', 'Baxter State Park Authority', 'Jacksonville State Park', 'City of Jacksonville',
           'Una Lake', 'Ua', 'Au Sable River', 'AU SABLE RIVER', 'Unknown', 'UNK', 'UNKL', 'Huntsville, City of', 'Mobile']
UNIV_CASES = UNIV_YES + UNIV_NO

r = subprocess.run(['node', '-e', NODE, str(ROOT), json.dumps(UNIV_CASES)], cwd=ROOT, capture_output=True, text=True, timeout=120)
if r.returncode != 0:
    check('node ran the candidates module: ' + (r.stderr.strip().splitlines() or ['?'])[-1], False)
    print('SOME FAILED')
    sys.exit(1)
o = json.loads(r.stdout)
al = o['al']
nm = o['named']

# 1. switch
check('candidatesOn() is off by default', o['offDefault'] is False and o['offAgain'] is False)
check('?candidates=1 turns it on, ?candidates=0 does not', o['onByUrl'] is True and o['offByUrl0'] is False)
check('localStorage kpcMapCandidates=1 turns it on', o['onByStorage'] is True)
chk = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
check('the page adds the candidate list only when candidatesOn() is true',
      "if (C.candidatesOn()) html += '<div id=\"mrCandsWrap\">" in chk and 'if (!C.candidatesOn()) return;' in chk)
check('abbreviations are fetched for the list only after the switch check',
      chk.find('if (!C.candidatesOn()) return;') < chk.find('await ensureAbbr();'))

# 2. MIT
key = json.loads((ROOT / 'data/us-key/US-AL.json').read_text(encoding='utf-8'))
mit_ids = {str(x[0]) for x in key['nonum'] if x[2] == 'MIT'}
check(f"Alabama MIT rows are left out ({al['dropped'].get('MIT')} of {len(mit_ids)})", al['dropped'].get('MIT') == len(mit_ids) == 10 and not mit_ids & set(al['ids']))
check('MIT is left out by the row rule', o['judge']['mit']['drop'] == 'MIT')

# 3. local codes
j = o['judge']
check('LP, LREC and LHCA are kept and flagged "check local rules"',
      all(j[k]['drop'] == '' and 'local' in j[k]['flags'] for k in ('lrec', 'lhca', 'lpCity')))
check('local codes skip the "city of" rule; city land without a local code is left out', j['lpCity']['drop'] == '' and j['cityNoLocal']['drop'] == 'city')
check('Metro Kiwanis Sportsplex (LP, Huntsville, City of) is kept with "check local rules"',
      nm['Metro Kiwanis Sportsplex'] and nm['Metro Kiwanis Sportsplex']['flagText'] == ['check local rules'])

# 4. university
mv = nm['Moundville Archeological Park']
check('Moundville Archeological Park (LHCA, University of Alabama, real row) is kept, flagged local + university',
      mv and mv['flags'] == ['local', 'university'] and 'check, university land' in mv['flagText'] and round(mv['acres']) == 271)
ep = nm['East Pinson Valley Community Park']
check('Jefferson State Junior College is a university flag, not an exclusion', j['college']['drop'] == '' and 'university' in j['college']['flags'] and ep and 'university' in ep['flags'])
check('no university or college manager is in the exclusion list',
      not re.search(r'universit|college', (ROOT / 'kpc-maprep-candidates.js').read_text(encoding='utf-8').split('const MANAGER_EXCLUDE', 1)[1].split('];', 1)[0], re.I))

u = o['univ']
miss = [c for c, h in zip(UNIV_CASES, u['hits']) if h != (c in UNIV_YES)]
check(f'university rule: {len(UNIV_YES)} names match (UAB, UA, UNA, Univ., Board of Regents, Jacksonville State...), '
      f'{len(UNIV_NO)} do not (Universal, Collegeville, College Street Park, USA, Texas A&M Forest Service...)' + (f'; wrong: {miss}' if miss else ''), not miss)
check('judgeRow flags exactly the names the rule matches', u['judged'] == u['hits'])
py = [bool(re.search(u['words'], c, re.I) or re.search(u['abbr'], c)) for c in UNIV_CASES]
check('the same source strings give the same answers in Python (re.I for WORDS only; ABBR is case-sensitive)',
      py == u['hits'] and u['wordsFlags'] == 'i' and u['abbrFlags'] == '')
uab = nm['UAB Campus Green']
check('UAB Campus Green (LP, manager "UAB", real row) is kept, flagged local + university',
      uab and uab['flags'] == ['local', 'university'] and 'check, university land' in uab['flagText'])
old_rx = re.compile(r'\buniversit(?:y|ies)\b|\bcollege\b', re.I)
al_mgr = sorted({str(x[3]) for x in key['nonum']})
new_hits = [m_ for m_ in al_mgr if re.search(u['words'], m_, re.I) or re.search(u['abbr'], m_)]
check(f'Alabama managers: the new rule adds only UAB to the old rule ({new_hits})',
      sorted(set(new_hits) - {m_ for m_ in al_mgr if old_rx.search(m_)}) == ['UAB'] and all(m_ in new_hits for m_ in al_mgr if old_rx.search(m_)))

# 5. Unknown
eco = nm['Eco Park at University Lake']
check('Unknown manager kept and flagged "manager unknown, check" (Eco Park at University Lake)', eco and eco['flagText'] == ['manager unknown, check'])
check('a blank manager is flagged unknown, not left out', j['blank']['drop'] == '' and 'unknown' in j['blank']['flags'])

# 6. Corps
fc = nm['Foscue Creek Park']
check('Corps land is kept (Foscue Creek Park, US Engineer Corps) with "Corps land: check with the district"',
      fc and fc['flagText'] == ['Corps land: check with the district'])
check('a Corps of Engineers manager is never left out', j['corps']['drop'] == '' and 'corps' in j['corps']['flags'])

# 7. Mobile
wf = nm['Walter F. George Recreation Area']
check('Walter F. George (manager "Mobile") shows the raw text and no Corps flag', wf and wf['managers'] == ['Mobile'] and 'corps' not in wf['flags'])
check('"Mobile" alone stays "Mobile" and is kept', o['mgr']['raw'] == 'Mobile' and o['mgr']['rawOwnerNotCorps'] == 'Mobile' and j['mobile']['drop'] == '' and j['mobile']['flags'] == [])
check('"USACE Mobile District" only when the manager or owner text says Corps',
      o['mgr']['confirmed'] == 'USACE Mobile District' and o['mgr']['ownerConfirms'] == 'USACE Mobile District' and o['mgr']['usace'] == 'USACE Mobile District' and o['mgr']['other'] == 'Tennessee Valley Authority (TVA)')
check('no manager text in the Alabama list is rewritten to USACE (no row says Corps beside "Mobile")', 'USACE Mobile District' not in o['listHtml'])

# 8. floor
f = o['floors']
check(f'default floor is 5 acres ({al["floor"]})', al['floor'] == 5 and f[2] == al['rows'])
check(f'floor is adjustable and only hides rows (0/1/5/10/40/100 acres -> {f})', f == sorted(f, reverse=True) and f[0] > f[2] > f[-1] and o['floor0Gibbin'])
check('the page shows the floor as a control with 5 selected and the hidden count',
      'id="mrCandFloor"' in o['listHtml'] and '<option value="5" selected>' in o['listHtml'] and f"{al['hiddenSmall']} hidden under 5 acres" in o['listHtml'])

# 9. kind check
lr = nm['Little River Wildlife Management Area']
check('Little River WMA is not dropped against Little River State Forest (kind check)',
      lr is not None and any(s['ref'] == 'US-4598' and s['otherKind'] for s in lr['similar']) and 'Little River Wildlife Management Area' not in o['sameNames'])
check('the same check on a made-up key keeps the WMA beside a state forest', o['big']['littleKept'] and o['big']['littleSim'][0]['otherKind'])
check('same-kind names still match the key (DeSoto State Park is left out as a key park)', 'DeSoto State Park' in o['sameNames'])

# 10. agency dropdown
ag = o['agAL']
urls = [i['url'] for g in ag['groups'] for i in g['items']]
check('Alabama State Parks finder (one park page) is hidden', 'https://alapark.com/parks/gulf-state-park' not in urls and 'gulf-state-park' not in o['dropAL'])
check('the hidden link is the only one, with its note',
      ag['hidden'] == [{'name': 'Alabama State Parks', 'slot': 'finder', 'url': 'https://alapark.com/parks/gulf-state-park', 'note': 'finder: stored link is one park page, hidden'}]
      and 'finder: stored link is one park page, hidden' in o['dropAL'])
check('Alabama State Parks home and the wildlife finder stay', 'https://alapark.com/' in urls and 'https://outdooralabama.com/public-lands' in urls)
check(f"every other finder link stays ({o['keptFinders']} of {o['allFinders']} kept)", o['keptFinders'] == o['allFinders'] - 1)
check('Manitoba keeps its finder link', any(i['slot'] == 'finder' for g in o['agMB']['groups'] for i in g['items']))
fed = next((g for g in ag['groups'] if g['label'] == 'Federal land agencies'), None)
fu = {i['url']: i['verified'] for i in (fed or {'items': []})['items']}
check('US dropdown has the fixed federal set from FEDA', fed is not None and all(u in fu for u in (
    'https://www.nps.gov/', 'https://www.fs.usda.gov/', 'https://www.fws.gov/', 'https://www.blm.gov/', 'https://www.usace.army.mil/', 'https://www.usbr.gov/')))
check('BLM and Reclamation are marked unverified', fu.get('https://www.blm.gov/') is False and fu.get('https://www.usbr.gov/') is False and '(unverified)' in o['dropAL'])
src = (ROOT / 'kpc-maprep-candidates.js').read_text(encoding='utf-8')
check('BLM and Reclamation URLs carry an UNVERIFIED code comment', all(re.search(re.escape(h) + r".*UNVERIFIED", src) for h in ("'blm.gov'", "'usbr.gov'")))
check('federal names and hosts come from FEDA in kpc-maprep.js (no second table)', {'nps.gov', 'fws.gov', 'fs.usda.gov', 'blm.gov', 'usbr.gov', 'usace.army.mil'} <= set(o['feda']))
check('Canada and world get no federal US group', all(g['label'] != 'Federal land agencies' for g in o['agMB']['groups'] + o['agGB']['groups']))
check('FR (no directory row) says so instead of an empty menu', 'No agency directory row for this place.' in o['dropGB'] and 'mrAgSel' not in o['dropGB'])
check('the dropdown is added to Check all without the switch', "let html = C.dropdownHtml(" in chk and chk.count('${extrasHtml(stAll)}') == 2)

# 11. no cap
b = o['big']
check(f"no cap: 700 rows in, {b['rows']} rows out", b['rows'] == 700)
check(f"first page is 50, Show more reaches every row ({b['pages'][:3]}...{b['pages'][-1]})", b['first'] == 50 and b['pages'][-1] == 700 and len(b['pages']) == 14 and b['more'])
check('the full side file is used when present (joined-since rows left out, 0-acre rows kept at floor 0)', o['side'] == {'from': 'side', 'rows': 700, 'little': False})
check('with only the key, the page says how many rows the key file holds', o['cutNote'])
check('no nonum (Canada, world) -> "not available", no error', o['noNonum']['avail'] is False and 'not available for this place yet' in o['noNonum']['html'])

# page wiring
html = (ROOT / 'kpc-maprep.html').read_text(encoding='utf-8')
order = [html.find(s) for s in ('kpc-maprep-logic.js?v=20261107t', 'kpc-maprep-candidates.js?v=20261107t', 'kpc-maprep-check.js?v=20261107t')]
check('page loads logic, then candidates, then check, with bumped ?v=', all(i > 0 for i in order) and order == sorted(order))
check('wording: research leads, not parks', 'Research leads, not parks.' in o['listHtml'])

# selftest
st = subprocess.run(['node', str(ROOT / 'kpc-maprep-candidates.js')], cwd=ROOT, capture_output=True, text=True, timeout=60)
check('candidates selftest: ' + (st.stdout.strip().splitlines() or ['?'])[-1], st.returncode == 0 and 'PASS maprep candidates selftest' in st.stdout)

print(f"Alabama, floor {al['floor']}: {al['rows']} possible new parks from {al['inFile']} of {al['total']} rows "
      f"(left out {al['droppedRows']}: {al['dropped']}; {al['groups']} groups; {al['same']} same as a key park; {al['hiddenSmall']} under the floor); "
      f"flags {al['flags']}; floors 0/1/5/10/40/100 -> {f}")
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
