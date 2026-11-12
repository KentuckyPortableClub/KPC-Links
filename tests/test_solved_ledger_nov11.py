#!/usr/bin/env python3
"""Nov 11 2026 records PR: the answers / solved ledger under data/research-inbox/answers/, the "solved refs are skipped" wiring in
.github/scripts/kpc_research_inbox.py, the settled negatives, the sources ledger, and the WDPA / Protected Planet guard.
Zero network (sockets are blocked below). Run like the other tests:  python3 tests/test_solved_ledger_nov11.py   (exit 0 = all ok)"""
import csv, json, pathlib, re, shutil, socket, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts')); sys.path.insert(0, str(HERE / 'tools'))
ok = True


def check(c, m):
    global ok; print(('ok   ' if c else 'FAIL ') + m); ok &= bool(c)


def _no_net(*a, **k): raise AssertionError('network call in an offline test')


socket.socket.connect = _no_net; socket.create_connection = _no_net   # any attempt fails the test
import kpc_research_inbox as RI  # noqa: E402
import kpc_build_solved_ledger as BL  # noqa: E402

ANS = HERE / 'data/research-inbox/answers'


def rd(p):
    with open(p, encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))


# ---------------------------------------------------------------- 1. the one rule for "solved"
C = RI.classify_solved
check(C('match', 'PADUS:1', '', '', '') == (True, 'settled-match'), 'match + official id = solved')
check(C('match', '', 'https://example.gov/page', '', '') == (True, 'settled-match'), 'match + official source url (no id) = solved')
check(C('match', '', '', '', '') == (False, 'match-without-official-id'), 'match with no id and no url is NOT solved')
check(C('match', '', 'https://example.gov/x', '', '', wdpa_removed=True) == (False, 'match-rested-on-removed-wdpa-lead'), 'a match that rested on a removed WDPA lead is NOT solved')
check(C('match', 'ZNIEFF:1', '', '', '', wdpa_removed=True)[0], 'a WDPA strip does not unsolve a row that still has another official id')
check(C('no boundary exists') == (True, 'settled-no-boundary'), 'no boundary exists = solved')
check(C('wrong pin') == (False, 'wrong-pin'), 'wrong pin is NOT solved')
check(C('other') == (False, 'other-needs-person'), 'other is NOT solved')
check(C('') == (False, 'blank-nothing-found'), 'blank is NOT solved')
check(C('maybe')[0] is False, 'a word outside the vocabulary is never solved')
check(C('', '', '', 'released-US', 'official') == (True, 'released-key'), 'released key grades it official = solved, whatever the answer')
check(C('other', '', '', 'released-CA', 'official') == (True, 'released-key'), 'released key official beats an old "other"')
check(C('match', 'X:1', '', 'released-US', 'pin') == (True, 'settled-match'), 'released key still on a pin does not count as the key basis')
check(C('', '', '', 'working-world-key (not released)', 'official')[0] is False, 'a working (unreleased) key never counts')
check(RI.ANSWER_WORDS == ('match', 'no boundary exists', 'wrong pin', 'other', ''), 'answer vocabulary is exactly match | no boundary exists | wrong pin | other | blank')

# ---------------------------------------------------------------- 2. the filed ledger
L = rd(ANS / 'solved-ledger.csv'); LD = {r['ref']: r for r in L}
check(len(L) == 832 and len(LD) == 832, f'ledger has the 832 Nov 5 parks once each ({len(L)})')
check(all(r['answer'] in RI.ANSWER_WORDS for r in L), 'every ledger answer uses the exact vocabulary')
def _again(r):
    K = RI.classify_row(r['answer'], r['official_id'], r['official_source_url'], r['key_location'], r['key_status'], 'WDPA lead removed' in r['flags'], r['confirm'], r['match_strength'], r['ref'])
    return (r['solved'] == 'yes', r['solved_basis'], r['owner_decision'], r['owner_decision_why'], r.get('owner_answer', ''), r['join_ready'], r['join_note']) == \
           (K['skip_search'], K['solved_basis'], K['owner_decision'], K['owner_decision_why'], K.get('owner_answer', ''), K['join_ready'], K['join_note'])
bad = [r['ref'] for r in L if not _again(r)]
check(not bad, f'solved, owner_decision and join_ready in the file equal the rule recomputed from the row ({bad[:3]})')
# the split: skip_search (research finished) is not the same as "no owner decision waiting"
K = RI.classify_row
k = K('match', 'X:1', '', '', '', False, 'needs_brandon', 'nov5-proposed', 'US-1')
check(k['owner_decision'] == 'yes' and k['skip_search'] and k['join_ready'] == 'yes', 'a Nov 5 match that asked the owner to confirm is now settled yes, join ready')
check(K('match', 'NRHP:1', '', '', '', False, '', 'nrhp-listing-boundary-pin-inside', 'US-2')['owner_decision'] == 'pending', 'a National Register listing boundary still held: pending')
k = K('other', '260014888', '', '', '', False, '', '', 'FR-14979')
check(k['owner_decision'] == 'no' and k['skip_search'] is False, 'FR-14979: owner no, not solved')
k = K('other', 'NRHP:93000266', '', '', '', False, '', '', 'US-10274')
check(k['owner_decision'] == 'no' and k['skip_search'] is False and '6,908-acre' in k['owner_decision_why'], 'US-10274 Palmito: owner no, needs the THC site outline')
k = K('match', 'DO-Ley:202-04', '', '', '', False, '', 'boundary-in-law-no-map-file', 'DO-0027')
check(k['skip_search'] and k['owner_decision'] == '' and k['join_ready'] == 'no', 'a law-only match: no owner yes needed, but join_ready = no')
k = K('match', 'ZNIEFF:1', '', '', '', False, '', 'agency-layer-pin-tested', 'FR-1')
check(k['skip_search'] and k['owner_decision'] == '' and k['join_ready'] == 'yes', 'a plain strong match is join ready')
k = K('match', 'X:1', '', 'released-US', 'official', False, 'needs_brandon', 'nov5-proposed', 'US-3')
check(k['solved_basis'] == 'released-key' and k['owner_decision'] == '', 'a released-key park never waits on the owner')
check(K('other', '', '', '', '', False, 'needs_brandon', '', 'US-4')['owner_decision'] == '', 'an unsolved park has no owner_decision flag (it is still on the search list)')
for ref in ('US-11820', 'US-12735', 'US-13474', 'US-8142', 'US-3493', 'US-10521', 'US-7975'):
    check(LD[ref]['solved'] == 'yes' and LD[ref]['owner_decision'] == 'pending', f'{ref}: research finished AND owner decision pending')
check(sum(r['owner_decision'] == 'pending' for r in L if r['match_strength'].startswith('nrhp-listing')) == 7, 'the 7 still-held National Register listing-boundary matches are pending')
check(LD['US-10274']['solved'] == 'no' and LD['US-10274']['owner_decision'] == 'no' and LD['US-10274']['answer'] == 'other', 'US-10274 Palmito is not a match; needs the THC site outline')
check(LD['FR-14979']['solved'] == 'no' and LD['FR-14979']['owner_decision'] == 'no', 'FR-14979: owner no to the 13 km join')
check(sum(r['owner_decision'] == 'yes' for r in L) == 56 and all(r['solved'] == 'yes' and r['join_ready'] == 'yes' for r in L if r['owner_decision'] == 'yes'), 'the 56 Nov 5 confirms are settled yes and join ready')
for ref in ('ZA-0085', 'ZA-0156', 'ZA-0157'):
    check(LD[ref]['solved'] == 'no' and LD[ref]['solved_basis'] == 'match-rested-on-removed-wdpa-lead' and 'stays unsolved' in LD[ref]['owner_decision_why'], f'{ref}: stays unsolved (WDPA id removed)')
ANS_FILE = ANS / 'OWNER-ANSWERS-nov11.md'
Q_FILE = ANS / 'OWNER-QUESTIONS.md'
check(ANS_FILE.is_file() and 'Yes, go with your answers' in ANS_FILE.read_text(encoding='utf-8'),
      'OWNER-ANSWERS-nov11.md is filed and records the widget answer')
check(Q_FILE.is_file() and Q_FILE.read_text(encoding='utf-8').count('**Answered**') >= 10,
      'OWNER-QUESTIONS.md is filed and marks the questions as answered')
check(all('item 10' in r['owner_answer'] and r['owner_answer'].startswith('owner chat 2026-11-11 21:16 CT') for r in L if r['owner_decision'] == 'yes'),
      'the 56 Nov 5 yes rows cite OWNER-ANSWERS-nov11.md item 10')
check('item 7' in LD['US-10274']['owner_answer'] and 'item 2' in LD['FR-14979']['owner_answer'],
      'Palmito cites item 7 and FR-14979 cites item 2')
check(all('item 10' in LD[ref]['owner_answer'] for ref in ('ZA-0085', 'ZA-0156', 'ZA-0157')),
      'ZA-0085/0156/0157 cite item 10')
law = [r for r in L if r['match_strength'] == 'boundary-in-law-no-map-file']
check(len(law) == 9 and all(r['join_ready'] == 'no' and not r['owner_decision'] for r in law), 'the 9 law-only matches: join_ready = no, no owner decision')
check(all(r['owner_decision'] == '' for r in L if r['solved_basis'] == 'released-key'), 'no released-key park is pending')
n11 = rd(ANS / 'nov11/answers-nov11.csv')
cnt = {}
for r in n11: cnt[r['answer']] = cnt.get(r['answer'], 0) + 1
check(len(n11) == 256 and cnt == {'match': 47, 'no boundary exists': 15, 'wrong pin': 5, 'other': 174, '': 15}, f'Nov 11 answers filed whole: {cnt}')
check({'official_point_lat', 'official_point_lon', 'official_point_kind', 'official_point_id', 'official_point_source_url', 'official_point_km_from_pota_pin'} <= set(n11[0]),
      'Nov 11 official_point_* columns kept')
check(sum(1 for r in n11 if r['official_point_lat']) == 53, 'Nov 11 official points kept (53 rows with coordinates)')
check(all(not r['correct_lat'] and not r['correct_lon'] for r in n11), 'no corrected pin anywhere in the Nov 11 file (official points are not moved pins)')
check(all(not any(c in r for c in ('correct_lat', 'correct_lon', 'pota_lat', 'pota_lon')) for r in L), 'the ledger carries no pin columns at all')
n5 = rd(ANS / 'nov5/answers-nov5.csv')
check(len(n5) == 832, 'Nov 5 answers filed whole (832)')
check(all(r['official_id'] or r['official_source_url'] for r in L if r['solved_basis'] == 'settled-match'), 'every settled match carries an official id or url a join can read')
check(sum(1 for r in L if r['solved_basis'] == 'released-key') == 178, '178 parks solved by the released key')
check(sum(1 for r in L if r['solved_basis'] == 'settled-no-boundary') == 15, '15 settled no-boundary rows')
check(all(r['solved'] == 'no' for r in L if r['answer'] in ('other', 'wrong pin', '') and r['solved_basis'] != 'released-key'), 'other / wrong pin / blank are never solved (unless the released key is)')
check(all(r['official_id'] == '' for r in L if r['answer'] != 'match'), 'official_id only on a match; leads sit in candidate_id')
for ref in ('US-10184', 'FR-10548', 'RO-0880', 'US-13474'):
    check(LD[ref]['solved'] == 'yes' and LD[ref]['official_id'] and LD[ref]['match_strength'], f'{ref}: Nov 11 strong match is solved, id readable ({LD[ref]["official_id"]})')

# ---------------------------------------------------------------- 3. rebuilt from the filed files, byte for byte (no drift)
tmp = pathlib.Path(tempfile.mkdtemp()); shutil.copytree(ANS, tmp / 'answers')
for f in ('solved-ledger.csv', 'search-list.csv'): (tmp / 'answers' / f).unlink()
BL.build_ledger(tmp / 'answers')
check((tmp / 'answers/solved-ledger.csv').read_bytes() == (ANS / 'solved-ledger.csv').read_bytes(), 'solved-ledger.csv is exactly what the builder makes from the filed files')
check((tmp / 'answers/search-list.csv').read_bytes() == (ANS / 'search-list.csv').read_bytes(), 'search-list.csv is exactly what the builder makes')

# ---------------------------------------------------------------- 4. search list: a solved park is never handed out again
S = rd(ANS / 'search-list.csv'); SD = {r['ref'] for r in S}
ledger = RI.load_ledger(HERE)
check(len(ledger) == 832 and RI.solved_refs(ledger) == {r['ref'] for r in L if r['solved'] == 'yes'}, 'load_ledger / solved_refs read the filed ledger')
check(not (SD & RI.solved_refs(ledger)), 'no solved ref is on the search list')
check(SD == {r['ref'] for r in L if r['solved'] == 'no'} and len(S) == 278, 'the search list is exactly the unsolved parks (278)')
check({'US-10274', 'FR-14979'} <= SD, 'Palmito and FR-14979 are on the search list (not a match / owner no)')
open_rows = rd(ANS / 'lists/mystery-parks-open.csv')
kept, skipped = RI.filter_unsolved(open_rows, ledger, key='ref')
check(len(kept) + len(skipped) == 366 and skipped and all(RI.is_skipped(r['ref'], ledger) for r in skipped) and not any(RI.is_skipped(r['ref'], ledger) for r in kept),
      f'the Nov 11 open list loses its skipped refs ({len(skipped)} skipped, {len(kept)} kept)')
check(not any(RI.owner_pending(r['ref'], ledger) for r in skipped), 'filter_unsolved never skips a park with an owner decision pending')
check({'US-11820', 'US-12735'} <= {r['ref'] for r in L if r['solved'] == 'yes'} and not ({'US-11820', 'US-12735'} & SD), 'US-11820 and US-12735 are NOT on search-list.csv (not re-researched)')
check(not any(RI.owner_pending(r, ledger) and r in SD for r in ledger), 'no owner-pending park is on the search list')
check([r['ref'] for r in kept] == [r['ref'] for r in open_rows if r['ref'] not in {s['ref'] for s in skipped}], 'filter keeps the order')
check(RI.load_ledger(tempfile.mkdtemp()) == {} and not RI.is_solved('US-1', {}), 'no ledger file = nothing is solved (older checkouts keep working)')

# ---------------------------------------------------------------- 5. inbox wiring: answers/ is never an inbox batch; solved rows are skipped
d = pathlib.Path(tempfile.mkdtemp()); ib = d / 'data/research-inbox'
for rel in ('batch1.csv', 'batch2.json', 'needs-another-look.json', 'brandon-list.md', 'answers/solved-ledger.csv', 'answers/settled-negatives.json', 'answers/nov5/x.csv',
            'results/old.json', 'sub/inner.csv'):
    (ib / rel).parent.mkdir(parents=True, exist_ok=True); (ib / rel).write_text('x')
check([pathlib.Path(f).name for f in RI.inbox_files(d)] == ['batch1.csv', 'batch2.json'], 'inbox_files reads only the batches straight in data/research-inbox/')
real = [pathlib.Path(f).name for f in RI.inbox_files(HERE)]
check(real and all(n.startswith('nov9-') for n in real) and not any('answers' in n or 'ledger' in n or 'negatives' in n for n in real), f'on the real repo the inbox still sees only the Nov 9 batches ({real})')
ps = (HERE / '.github/scripts/kpc_problem_solver.py').read_text(encoding='utf-8')
check('RI.inbox_files(ROOT)' in ps and "glob.glob(str(ROOT / 'data/research-inbox/*.csv'))" not in ps, 'the problem solver --inbox uses the same file list')

root = pathlib.Path(tempfile.mkdtemp()); ib = root / 'data/research-inbox'; ib.mkdir(parents=True)
FIELDS = RI.COLS
rows = [dict(pota_ref='US-0754', park_name='Rosie the Riveter WWII Home Front National Historical Park'),
        dict(pota_ref='US-9999', park_name='Unsolved Park WDPA:123456 test'),
        dict(pota_ref='US-7436', park_name='Southwest Trail State Trail')]
with open(ib / 'b1.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator='\n'); w.writeheader(); w.writerows([{k: r.get(k, '') for k in FIELDS} for r in rows])
nal = {'about': 'x', 'parks': {'US-0754': {'status': 'needs another look', 'reason': 'r', 'row': {'pota_ref': 'US-0754', 'park_name': 'Rosie'}, 'wait_on': 'layer', 'since': 's', 'last': 'l'},
                              'US-9998': {'status': 'needs another look', 'reason': 'see https://www.protectedplanet.net/555 and WDPA 555', 'row': {'pota_ref': 'US-9998', 'park_name': 'Left Over', 'layer_url': ''}, 'wait_on': 'layer', 'since': 's', 'last': 'l'}},
       'brandon_flip': {'US-11820': {'status': RI.SFN, 'reason': 'r', 'earlier_no': {}, 'row': {'pota_ref': 'US-11820', 'park_name': 'Miller'}, 'record_id': '1', 'record_name': 'n'}}}
for hold in ('US-11820', 'US-12735', 'CA-1164'):   # two Nov 9 agency-alias holds waiting on an owner yes, and one plain released-key park
    nal['parks'][hold] = {'status': 'needs another look', 'reason': 'agency alias', 'row': {'pota_ref': hold, 'park_name': 'Held ' + hold}, 'wait_on': 'person', 'since': 's', 'last': 'l'}
(ib / 'needs-another-look.json').write_text(json.dumps(nal))
(ib / 'results').mkdir()
(ib / 'results/alias.json').write_text(json.dumps({'rows': [dict(pota_ref=h, park_name='Held ' + h, status='NEEDS PERSON', alias=True, record_name='Agency Name', record_id='7') for h in ('US-11820', 'US-12735', 'CA-1164')]}))
res = RI.run(RI.inbox_files(root), root=root, kpcdata=root / 'nokpcdata', cache=root / 'cache', offline=True, retry=True, ledger=ledger)
b1 = {r['pota_ref']: r for r in res['b1']}
check(b1['US-0754']['status'] == 'SOLVED' and b1['US-0754']['record_id'] == 'PADUS-PAID:RORI', 'a solved row is reported SOLVED with its official id and is not judged')
check(b1['US-7436']['status'] == 'SOLVED' and 'settled-no-boundary' in b1['US-7436']['reason'], 'a settled no-boundary row is skipped too')
check(b1['US-9999']['status'] == 'NEEDS PERSON', 'an unsolved row is still judged (no layer: back to research, no network)')
out_nal = json.loads((ib / 'needs-another-look.json').read_text())
check('US-0754' not in out_nal['parks'], 'a solved park is dropped from the retry list')
check('CA-1164' not in out_nal['parks'], '(c) a plain released-key solved park drops from the retry list')
check('US-9998' in out_nal['parks'] and 'US-9998' not in [r['pota_ref'] for rs in res.values() for r in rs if r['status'] == 'SOLVED'], 'an unsolved retry entry stays')
bl = (ib / 'brandon-list.md').read_text()
check('CA-1164' not in bl, '(c) a plain released-key solved park is left off the owner short list')
check('US-11820' in bl and 'US-12735' in bl, '(a) US-11820 and US-12735 stay on the owner short list (owner decision pending)')
check({'US-11820', 'US-12735'} <= set(out_nal['parks']) and out_nal['parks']['US-11820']['wait_on'] == 'person' and out_nal['parks']['US-12735']['reason'] == 'agency alias',
      '(a) US-11820 and US-12735 stay on the retry list with their hold intact')
check('US-11820' in out_nal['brandon_flip'], 'their owner-flip entry is kept too')
check(not any(r['pota_ref'] in ('US-11820', 'US-12735') and r['status'] == 'SOLVED' for rs in res.values() for r in rs), 'they are not reported SOLVED')
written = [p for p in (root).rglob('*') if p.is_file() and p.suffix in ('.json', '.md', '.csv')]
check(not any(RI.has_wdpa_data(p.read_text(encoding='utf-8')) for p in written if p.name != 'b1.csv'), 'a run writes no WDPA id or Protected Planet address (results, retry list, short list)')
check(RI.WDPA_MARK in json.dumps(out_nal), 'the WDPA text in a retry entry was replaced by the plain marker')
# nothing but the inbox folder and point-circles.json were written
tops = {p.relative_to(root).parts[0] for p in root.rglob('*') if p.is_file()}
check(tops <= {'data'}, f'a run touches only data/ in the repo root ({tops})')
check(not any('key' in x for p in root.rglob('*') if p.is_file() for x in p.relative_to(root).parts), 'a run writes no key, override or pin file')

# ---------------------------------------------------------------- 6. settled negatives
N = json.loads((ANS / 'settled-negatives.json').read_text(encoding='utf-8'))
ids = {e['id']: e for e in N['negatives']}
check(all({'id', 'kind', 'scope', 'statement', 'miss_proves_nothing', 'do_not'} <= set(e) for e in N['negatives']), 'each settled negative has id, kind, scope, statement, do_not')
check(set(ids['no-boundary-exists-15']['refs']) == {r['ref'] for r in L if r['answer'] == 'no boundary exists'} and len(ids['no-boundary-exists-15']['refs']) == 15,
      'the 15 no-boundary refs in the JSON are exactly the 15 in the ledger')
check(all(LD[r]['solved'] == 'yes' for r in ids['no-boundary-exists-15']['refs']), 'those 15 are solved in the ledger')
for k in ('tn-natural-areas-incomplete', 'nrhp-withholds-sensitive-sites'): check(ids[k]['miss_proves_nothing'] is True, f'{k}: a miss proves nothing')
need = ['blm-no-site-polygons', 'nv-dot-scenic-byways'] + ['no-named-polygon-' + s for s in ('wa-dnr', 'sfwmd', 'ar-gf', 'nj-dep', 'mo-mdc', 'mi-state', 'vt-anr', 'ut-dwr')]
check(all(k in ids for k in need), 'every negative named in the brief is on file')
check(set(ids['blm-no-site-polygons']['states']) == {'US-ID', 'US-WY', 'US-UT', 'US-NV', 'US-CA'}, 'BLM negative names ID WY UT NV CA')
check((ANS / 'settled-negatives.md').exists() and (ANS / 'settled-negatives.md').stat().st_size < 3000, 'the short human note exists')

# ---------------------------------------------------------------- 7. sources ledger: Nov 11 additions appended once
SRC = rd(ANS / 'sources/research-sources-all.csv'); ADD = rd(ANS / 'sources/research-sources-nov11-additions.csv')
COLS12 = ['country', 'region', 'place_or_agency', 'layer_name', 'url', 'format', 'license', 'has_boundaries', 'id_field', 'name_field', 'notes', 'last_checked']
with open(ANS / 'sources/research-sources-all.csv', encoding='utf-8-sig', newline='') as f: hdr = next(csv.reader(f))
check(hdr == COLS12 and len(ADD) == 22, 'sources ledger has the same 12 columns; 22 Nov 11 additions')
tup = lambda r: tuple(sorted(r.items()))
cnt = {}
for r in SRC: cnt[tup(r)] = cnt.get(tup(r), 0) + 1
check(all(cnt.get(tup(a)) == 1 for a in ADD), 'every Nov 11 addition is in the sources ledger exactly once')
again, added = BL.append_sources(SRC, ADD)
check(added == 0 and again == SRC, 'appending the additions again adds nothing (no duplicates)')
fresh = dict(ADD[0], url='https://example.gov/new-layer'); more, added = BL.append_sources(SRC, [fresh, ADD[1], fresh])
check(added == 1 and len(more) == len(SRC) + 1, 'a genuinely new source row is appended once')
check(not any(re.search(r'protected\s*planet', r['url'] + r['layer_name'], re.I) for r in SRC), 'the Thailand Protected Planet row is not in the sources ledger')

# ---------------------------------------------------------------- 8. WDPA / Protected Planet: data is banned, the plain word is not
ID_COLS = re.compile(r'(^|_)(id|ids|id_type|url|link)($|_)|official_id|source_url', re.I)   # (id_field names a layer's field, e.g. WDPA_Cd: a column name, not an id)


def wdpa_problems(folder):
    """every WDPA id / Protected Planet address in the ledger files (csv, md, json, txt), or a WDPA word in an id / type / url column"""
    out = []
    for p in sorted(pathlib.Path(folder).rglob('*')):
        if not p.is_file(): continue
        t = p.read_text(encoding='utf-8-sig')
        if RI.has_wdpa_data(t) or re.search(r'protected[\s_-]?planet\.net|protectedplanet', t, re.I): out.append(f'{p.name}: id or address in text')
        if p.suffix == '.csv':
            for i, r in enumerate(csv.DictReader(open(p, encoding='utf-8-sig', newline='')), 2):
                for c, v in r.items():
                    if c and v and c not in ('id_field', 'name_field') and ID_COLS.search(c) and re.search(r'wdpa|protected\s*planet', v, re.I): out.append(f'{p.name} row {i} column {c}')
    return out


check(wdpa_problems(ANS) == [], f'no WDPA id and no Protected Planet address in any filed ledger file ({wdpa_problems(ANS)[:3]})')
check(not any(re.search(r'wdpa', r['id_type'], re.I) for r in n5), 'no id_type is WDPA in the Nov 5 answers')
check('WDPA lead removed' in LD['AU-0436']['flags'] and LD['AU-0436']['official_id'] == '' and LD['AU-0436']['answer'] == 'match', 'a stripped row keeps its answer and says a WDPA lead was removed')
check(sum('WDPA lead removed' in r['flags'] for r in L) == 10, '10 ledger rows carry the WDPA removed flag')
# the word alone is allowed; ids and addresses are not
for good in ('WDPA is a lead only', 'OSM/WDPA/Google are leads, never sources', 'PAD-US WDPA_Cd column', 'the WDPAID field', 'WDPA lead removed'):
    check(not RI.has_wdpa_data(good), f'plain words allowed: {good!r}')
for badtxt in ('WDPA:354593', 'SAPAD-WDPAID:555579298', 'WDPA 354593', 'WDPA id (62381)', 'https://protectedplanet.net/354593', 'www.protectedplanet.net/en/country/THA'):
    check(RI.has_wdpa_data(badtxt) and not RI.has_wdpa_data(RI.scrub_wdpa(badtxt)), f'data caught, and scrub removes it: {badtxt!r}')
# adding one back makes the guard fail
inj = pathlib.Path(tempfile.mkdtemp()) / 'answers'; shutil.copytree(ANS, inj)
p = inj / 'nov5/answers-nov5.csv'
rows5 = rd(p); rows5[0]['official_id'] = 'WDPA:354593'; rows5[0]['id_type'] = 'WDPA'
with open(p, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows5[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows5)
check(wdpa_problems(inj) != [], 'GUARD FAILS when a WDPA id is added back to a ledger csv')
inj2 = pathlib.Path(tempfile.mkdtemp()) / 'answers'; shutil.copytree(ANS, inj2)
p = inj2 / 'sources/research-sources-all.csv'; p.write_text(p.read_text(encoding='utf-8') + 'TH,,UNEP-WCMC,Thailand profile,https://protectedplanet.net/en/country/THA,page,x,unknown,,,,2026-11-04\n', encoding='utf-8')
check(wdpa_problems(inj2) != [], 'GUARD FAILS when a Protected Planet address is added back to the sources ledger')
inj3 = pathlib.Path(tempfile.mkdtemp()) / 'answers'; shutil.copytree(ANS, inj3)
p = inj3 / 'settled-negatives.md'; p.write_text(p.read_text(encoding='utf-8') + '\nsee WDPA 12345\n', encoding='utf-8')
check(wdpa_problems(inj3) != [], 'GUARD FAILS when a WDPA id is added to a note')
inj4 = pathlib.Path(tempfile.mkdtemp()) / 'answers'; shutil.copytree(ANS, inj4)
p = inj4 / 'settled-negatives.md'; p.write_text(p.read_text(encoding='utf-8') + '\nWDPA is a lead only.\n', encoding='utf-8')
check(wdpa_problems(inj4) == [], 'the guard lets a plain sentence such as "WDPA is a lead only" through')
# tracked files: ask git when this is a checkout (offline command); every tracked file under answers/ must be clean
try:
    tracked = subprocess.run(['git', '-C', str(HERE), 'ls-files', 'data/research-inbox/answers'], capture_output=True, text=True, timeout=30).stdout.split()
except Exception: tracked = []
check(all(not RI.has_wdpa_data((HERE / f).read_text(encoding='utf-8-sig')) for f in tracked), f'git: {len(tracked)} tracked answers files, none with WDPA data')
# older inbox files (Nov 9) already hold WDPA text from before this PR; the count may only go down (the owner decides the clean-up)
BASE = {'data/research-inbox/needs-another-look.json': 135, 'data/research-inbox/nov9-brandon-no-id-world-high-med.csv': 135,
        'data/research-inbox/results/nov9-brandon-no-id-world-high-med.json': 82}
for f in sorted(p.relative_to(HERE).as_posix() for p in (HERE / 'data/research-inbox').rglob('*') if p.is_file() and 'answers' not in p.parts):
    n = len(RI.WDPA_DATA.findall((HERE / f).read_text(encoding='utf-8-sig', errors='replace')))
    check(n <= BASE.get(f, 0), f'{f}: WDPA data count {n} not above its Nov 11 baseline {BASE.get(f, 0)}')

# ---------------------------------------------------------------- 8b. no sentence attributes words to the owner
# OWNER-ANSWERS-nov11.md is the recorded source (the owner accepted the recommendations in chat) and may name him; nothing else under answers/ may.
named = [f.relative_to(ANS).as_posix() for f in ANS.rglob('*') if f.is_file() and f.name != 'OWNER-ANSWERS-nov11.md' and re.search(r'\bBrandon\b|\bKZ4CP\b', f.read_text(encoding='utf-8-sig'))]
check(not named, f'no filed text names the owner, or quotes him ({named[:3]}); file names such as held-for-brandon are convention')
check(re.search(r'\bBrandon\b', ANS_FILE.read_text(encoding='utf-8')) and 'Yes, go with your answers' in ANS_FILE.read_text(encoding='utf-8'),
      'the recorded answers file names the source chat and the widget choice')
SRCN = [r['notes'] for r in SRC + ADD if 'BLM' in r['place_or_agency'] and 'OFFICIAL POINTS' in r['notes']]
check(SRCN and all('(club rule: where no outline is published, record the official point)' in n for n in SRCN), 'the BLM official-points sources row uses the club-rule wording')

check('by an outside agent (Fable)' in (ANS / 'nov5/HANDOFF.md').read_text(encoding='utf-8'), 'the Nov 5 hand-off byline names an outside agent, not a tool')

# ---------------------------------------------------------------- 9. size cap and "this job writes no key / hash"
big = [f for f in ANS.rglob('*') if f.is_file() and f.stat().st_size >= 1_000_000]
check(not big, 'every file under answers/ is under 1,000,000 bytes')
import kpc_key_freeze as KF  # noqa: E402
# KPC owner, 2026-11-11 (job 6, world rules change approved): the world hash moved 9358c2ede2d5 -> 889d37136cf8 (three French PatriNat layers); US and CA are as before; fers is main's cef323de4c9a (#157)
want = {'us-key': '46ef34a04ab0', 'ca-key': '4b4176190334', 'world-key': '889d37136cf8', 'fers': 'cef323de4c9a'}
check({k: KF.rules_hash(k) for k in want} == want, f'rules hashes unchanged: {want}')
fed = {pathlib.Path(x).name for v in KF.RULE_FILES.values() for x in v}
check('kpc_research_inbox.py' not in fed and 'kpc_problem_solver.py' not in fed and 'kpc_build_solved_ledger.py' not in fed, 'no file this job touches feeds a rules hash')
check('kpc_research_inbox.py' in KF.NOT_RULES and 'kpc_problem_solver.py' in KF.NOT_RULES, 'the inbox and the problem solver are on the not-a-rule list')
src = (HERE / 'tools/kpc_build_solved_ledger.py').read_text(encoding='utf-8')
check(not re.search(r'urllib|requests|http\.client|socket|subprocess', src), 'the builder imports no network or process module')
check(RI.selftest() == 0, 'inbox selftest')
print('ALL OK' if ok else 'FAILED'); sys.exit(0 if ok else 1)
