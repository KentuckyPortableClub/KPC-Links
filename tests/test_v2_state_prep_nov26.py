#!/usr/bin/env python3
"""26 Nov 2026: tests of the state prep tool (tools/pc-keys/kpc_v2_state_prep.py). Tiny made-up fixtures only (no real data).
Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import builtins, contextlib, csv, gzip, io, json, pathlib, shutil, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'pc-keys'))
import kpc_v2_state_prep as P  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def wjson(p, d):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(p, 'wb', mtime=0) as g: g.write(json.dumps(d).encode())


def sq(x0, y0, s=10000): return [x0, y0, s, 0, 0, s, -s, 0, 0, -s]


def rec(layer, i, name, x0, y0, attrs):
    return {'key': f'{layer}{i}', 'layer': layer, 'record_id': str(i), 'record_name': name, 'attributes': dict(attrs), 'q': 6, 'rings': [sq(x0, y0)]}


def park(name, lat, lon, kind=None, val=None, page=None, web=None, own=True):
    p = {'name': name, 'area': 'US-ZZ', 'pin': [lat, lon], 'link': {}, 'page': page or {}}
    if kind: p['link'] = {'usable': True, 'id_kind': kind, 'id_value': val, 'page_kind': 'own page', 'web_name': web}
    return p


NAMES = [f'Zq{chr(97 + i)}rt' for i in range(25)]


def make_world(t, zy_gap=False):
    """repo (rule table copy, link ties, park list), store, facts."""
    repo, store = t / 'repo', t / 'store'
    (repo / '.github').mkdir(parents=True)
    for n in ('us-key-v2-rules.json', 'link-id-ties.json'): shutil.copyfile(ROOT / '.github' / n, repo / '.github' / n)
    recs, facts, refs = [], {}, []
    for i in range(25):
        x0 = -85000000 + i * 30000
        recs.append(rec('sgzza', i + 1, f'{NAMES[i]} Park', x0, 38000000,
                        {'objectid': i + 1, 'unit': f'PRJ-{100 + i}', 'cls': 'ABC'[i % 3], 'agid': 5000 + i * 7, 'rowfield': i + 1, 'web': f'https://zz.example/lands/{100 + i}.html'}))
        r = f'US-{9000 + i}'; refs.append(r)
        facts[r] = park(f'{NAMES[i]} Park', 38.005, -85.0 + i * 0.03 + 0.005, 'ZZ unit id', f'PRJ-{100 + i}')
    for j in range(6):                     # a coincidence: six parks share one value, the field has 3 values
        r = f'US-{9100 + j}'; refs.append(r); facts[r] = park(f'Far{chr(97 + j)}wood Park', 38.5, -86.0, 'ZZ class', 'B')
    for j, v in enumerate('ABC'):          # 3 parks, 3 different values, pins far away from those records
        r = f'US-{9150 + j}'; refs.append(r); facts[r] = park(f'Dist{chr(97 + j)}ant Park', 38.6, -86.1 - j, 'ZZ tier', v)
    for j in range(5):                     # an id inside a web address
        r = f'US-{9200 + j}'; refs.append(r); facts[r] = park(f'{NAMES[j]} Park', 38.005, -85.0 + j * 0.03 + 0.005, 'ZZ web id', str(100 + j))
    pat = [('Alpha Marsh', 'Alpha Marsh Lowlands'), ('Bravo Lake', 'Bravo Lake and Park'), ('Charlie State Park', 'Charlie'),
           ('Delta State Park', 'Delta State Forest'), ('Echo Lake Park', 'Echo Lake Preserve'), ('J. Foxtrot Park', 'John Foxtrot Park'), ('Golf Hotel Park', 'Hotel Golf Park')]
    for k, (pn, rn) in enumerate(pat):
        x0 = -84000000 + k * 30000
        recs.append(rec('sgzzb', k + 1, rn, x0, 39000000, {}))
        r = f'US-{9300 + k}'; refs.append(r); facts[r] = park(pn, 39.005, -84.0 + k * 0.03 + 0.005)
    r = 'US-9399'; refs.append(r); facts[r] = park('Lonely Island Park', 40.5, -80.0)      # no record under its pin at all
    man = {'sgzza': {'complete': True, 'why': ''}, 'sgzzb': {'complete': True, 'why': ''}}
    wjson(store / 'US-ZZ.layer-records.json.gz', {'manifest': man, 'made': 'x', 'records': recs})
    gap = dict(man, sgzzc={'complete': False, 'why': 'the download failed'})
    wjson(store / 'US-ZY.layer-records.json.gz', {'manifest': gap, 'made': 'x', 'records': recs[:3]})
    for st in ('ZZ', 'ZY'):
        wjson(repo / 'data' / 'pota' / 'saved' / 'parks' / f'US-{st}.json.gz', {'data': [{'reference': r} for r in refs]})
    wjson(t / 'facts.json.gz', {'parks': facts})
    return repo, store, t / 'facts.json.gz'


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    repo, store, facts = make_world(t)
    table = repo / '.github' / 'us-key-v2-rules.json'
    tb_before = (table.read_bytes(), table.stat().st_mtime_ns)
    opened = []
    real_open = builtins.open

    def spy(file, mode='r', *a, **k):
        if any(c in str(mode) for c in 'wax+'): opened.append(str(file))
        return real_open(file, mode, *a, **k)
    import io as _io
    real_io = _io.open
    builtins.open = spy; _io.open = spy
    before = {str(p.relative_to(t)): (p.stat().st_size, p.stat().st_mtime_ns) for p in t.rglob('*') if p.is_file()}
    out = t / 'out'
    try:
        with contextlib.redirect_stdout(io.StringIO()): rc, rep = P.run('ZZ', store, facts, None, out, repo)
        with contextlib.redirect_stdout(io.StringIO()): rc2, rep2 = P.run('ZY', store, facts, None, out, repo)
    finally:
        builtins.open = real_open; _io.open = real_io
    after = {str(p.relative_to(t)): (p.stat().st_size, p.stat().st_mtime_ns) for p in t.rglob('*') if p.is_file()}
    new = [k for k in after if k not in before]
    check('nothing is written outside its own new folders (two runs = two v2-prep-<ST>-<time> folders)',
          rc == 0 and new and all(k.startswith('out/v2-prep-') for k in new) and not [k for k in before if after.get(k) != before[k]])
    check('the rule table is never opened for writing and is byte for byte the same', (table.read_bytes(), table.stat().st_mtime_ns) == tb_before
          and not [f for f in opened if f.endswith('us-key-v2-rules.json') or '/.github/' in f])
    check('every write goes to its own report folder', all('/out/v2-prep-' in f for f in opened) and opened)
    txt = (rep / 'STATE-PREP-ZZ.txt').read_text(encoding='utf-8')
    det = list(csv.DictReader(open(rep / 'prep-details.csv', encoding='utf-8')))
    prop = json.load(open(rep / 'proposed-rows.json', encoding='utf-8'))
    ids = [r for r in det if r['section'] == '2 id fields']
    row = lambda kind, field: next((r for r in ids if r['kind'] == kind and r['field'] == field), None)
    check('a true id field is PROPOSEd (24 or 25 parks hit, the pin on the land, 25 different values)',
          row('ZZ unit id', 'unit') and row('ZZ unit id', 'unit')['verdict'] == 'PROPOSE' and row('ZZ unit id', 'unit')['parks'] == '25' and row('ZZ unit id', 'unit')['distinct'] == '25')
    pr = [x for x in prop['tables']['id_ties']['value'] if x['kind'] == 'ZZ unit id']
    check('the proposed id_ties row has the real table\'s shape (kind, layer, field, measured) plus why, and test TODO',
          pr and pr[0]['layer'] == 'sgzza' and pr[0]['field'] == 'unit' and pr[0]['test'] == 'TODO' and pr[0]['why'] and pr[0]['measured'] and pr[0]['verdict'] == 'PROPOSE')
    cls = row('ZZ class', 'cls')
    check('a coincidence field with 3 values that six parks share is NO, and not proposed', cls and cls['verdict'] == 'NO' and 'share' in cls['reason']
          and not [x for x in prop['tables']['id_ties']['value'] if x['kind'] == 'ZZ class'])
    tier = row('ZZ tier', 'cls')
    check('3 parks, 3 values, pins far from the records (a coincidence) is NO, with the plain reason', tier and tier['verdict'] == 'NO' and 'only 0 of 3' in tier['reason'])
    web = [x for x in prop['link_id_ties'] if x['kind'] == 'ZZ web id' and x['field'] == 'web']
    check('an id inside a web address is found (way: inside a web address) and goes to the web-address ties', web and web[0]['test'] == 'TODO'
          and any(r['kind'] == 'ZZ web id' and r['way'] == 'inside a web address' for r in ids))
    ag = [r for r in det if r['section'] == '3 agency record ids' and r['layer'] == 'sgzza']
    check('an agency record id: the unique id-like field is PROPOSEd; a field equal to the row number is not a candidate',
          any(r['field'] == 'agid' and r['verdict'] == 'PROPOSE' for r in ag) and not any(r['field'] in ('rowfield', 'objectid') for r in ag)
          and prop['tables']['record_id_fields']['value'] == {'sgzza': 'agid'})
    names = {r['reason']: r for r in det if r['section'] == '4 name patterns'}
    want = ['official name has extra last word(s)', 'official name adds a kind word: park', "official name lacks the park's kind word: state park",
            'kind word differs: state park vs state forest', 'kind word differs: park vs preserve', 'initial vs full word', 'same words, other order',
            'no record under the pin at all']
    check('each name pattern is recognised on the fixture parks: ' + '; '.join(want[:3]) + ' ...', all(w in names for w in want))
    check('name patterns carry up to 3 examples in the csv (names there) and are all LOOK', all(r['verdict'] == 'LOOK' and r['examples'] for r in names.values()))
    check('the "no record under the pin" park is counted apart', 'have no record under the pin at all' in txt and names['no record under the pin at all']['parks'] == '10')
    check('the txt has counts only (no park names) and fits one screen', 'Zq' not in txt and 'Alpha' not in txt and len(txt.splitlines()) <= 50 and 'WHAT TO DO NEXT' in txt)
    check('the txt says v2 can build the state', 'v2 can build ZZ' in txt)
    zy = (rep2 / 'STATE-PREP-ZY.txt').read_text(encoding='utf-8')
    check('a state with a failed layer says "cannot build until: <layer>"', 'v2 cannot build ZY until: sgzzc' in zy)

# the name rules
R = P.Rules(ROOT)
cn = lambda a, b: P.compare_names(a, b, R)
check('names: same / same after the table rules (possessive, short form, run together) / differs',
      cn('Knox State Park', 'KNOX STATE PARK')[0] == 'same' and cn("Devil's Track", 'Devils Track')[0] == 'same' and cn('Mt Hope SP', 'Mount Hope State Park')[0] == 'after rules'
      and cn('Echo Lake Park', 'Echolake Park')[0] == 'same' and cn('Foo State Park', 'Foo State Forest')[0] == 'differs')
check('names: kind swap from the table (state park = state marine park)', cn('Hope State Park', 'Hope State Marine Park')[0] == 'after rules')
check('names: initial vs full word ("A." vs "Alexandra"), also against a name with no kind word',
      cn('Elizabeth A. Morton National Wildlife Refuge', 'Elizabeth Alexandra Morton National Wildlife Refuge') == ('differs', 'initial vs full word')
      and cn('Elizabeth A. Morton National Wildlife Refuge', 'Elizabeth Alexandra Morton') == ('differs', 'initial vs full word'))
check('names: a second name in front (Alfred E. Smith/Sunken Meadow State Park)', cn('Sunken Meadow State Park', 'Alfred E. Smith/Sunken Meadow State Park') == ('differs', 'a second name in front'))
check('names: extra word, other order, completely different', cn('Philipse Manor State Historic Site', 'Philipse Manor Hall State Historic Site')[1] == 'official name has extra word(s)'
      and cn('Golf Hotel Park', 'Hotel Golf Park')[1] == 'same words, other order' and cn('Alpha Creek Park', 'Zulu Ridge Park')[1] == 'a completely different name')
check('web names (words run together): same after rules / initial vs full / extra last word / completely different',
      P.compare_web('Sunken Meadow State Park', 'sunkenmeadow', R)[0] == 'after rules' and P.compare_web('Elizabeth A. Morton National Wildlife Refuge', 'elizabeth alexandra morton', R)[1] == 'initial vs full word'
      and P.compare_web('Philipse Manor State Historic Site', 'philipsemanorhall', R)[1].startswith('official name has extra') and P.compare_web('Alpha Creek Park', 'managed land', R)[1] == 'a completely different name')

# 4b: sources, junk, and the two-sources rule
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    repo, store, facts_f = make_world(t)
    f = json.load(open(gzip.open(facts_f, 'rt') and None or '/dev/null')) if False else None
    facts = json.load(gzip.open(facts_f, 'rt', encoding='utf-8'))
    pk = facts['parks']
    # park 9000: page name differs (another spelling) AND the record under its pin has the same other spelling -> two sources agree
    pk['US-9000']['name'] = 'Zqart Park'
    pk['US-9000']['page'] = {'own_page': 'own', 'unofficial': False, 'name_on_page': 'Zqart Park Lowlands'}
    # make the record carry that name
    d = json.load(gzip.open(store / 'US-ZZ.layer-records.json.gz', 'rt', encoding='utf-8'))
    d['records'][0]['record_name'] = 'Zqart Park Lowlands'
    # park 9001: page name differs, the record says something else -> one source only
    pk['US-9001']['name'] = 'Zqbrt Park'; pk['US-9001']['page'] = {'own_page': 'own', 'unofficial': False, 'name_on_page': 'Zqbrt Park Lowlands'}
    # park 9002: a page title that is not a name; park 9003: an unofficial page; park 9004: same name
    pk['US-9002']['page'] = {'own_page': 'own', 'unofficial': False, 'name_on_page': 'Sign up for our newsletter'}
    pk['US-9003']['page'] = {'own_page': 'own', 'unofficial': True, 'name_on_page': 'Totally Else'}
    pk['US-9004']['page'] = {'own_page': 'own', 'unofficial': False, 'name_on_page': pk['US-9004']['name']}
    wjson(store / 'US-ZZ.layer-records.json.gz', d); wjson(facts_f, facts)
    with contextlib.redirect_stdout(io.StringIO()): rc, rep = P.run('ZZ', store, facts_f, None, t / 'out', repo)
    nc = list(csv.DictReader(open(rep / 'name-compare.csv', encoding='utf-8')))
    g = lambda ref, src: next((r for r in nc if r['ref'] == ref and r['source'] == src), None)
    check('4b: page name that differs = differs; same name = same; record under pin with the same other spelling = differs',
          g('US-9000', 'page')['verdict'] == 'differs' and g('US-9004', 'page')['verdict'] == 'same' and g('US-9000', 'record under pin')['verdict'] == 'differs')
    check('4b: a title that shares no place word is "title is not a name", never a difference; an unofficial page is skipped',
          g('US-9002', 'page')['verdict'] == 'junk' and g('US-9003', 'page') is None)
    prop = json.load(open(rep / 'proposed-rows.json', encoding='utf-8'))
    osp = {x['ref']: x for x in prop['other_spellings']}
    check('4b: two official sources that agree with each other but differ from POTA go to other_spellings (LOOK, test TODO, why, both sources named)',
          'US-9000' in osp and osp['US-9000']['verdict'] == 'LOOK' and osp['US-9000']['test'] == 'TODO' and osp['US-9000']['official'] == 'Zqart Park Lowlands'
          and osp['US-9000']['pota'] == 'Zqart Park' and sorted(osp['US-9000']['sources']) == ['page', 'record under pin'] and osp['US-9000']['why'])
    check('4b: one differing source alone is not listed; the park whose sources disagree with each other is not listed', 'US-9001' not in osp and 'US-9004' not in osp)
    txt = (rep / 'STATE-PREP-ZZ.txt').read_text(encoding='utf-8')
    check('4b: the txt says the plain sentence, has the per-source counts, and no names',
          "An other-spelling row only says this is another way to write the park's name. The pin or the size must still prove the land." in txt
          and 'page: ' in txt and 'title is not a name 1' in txt and 'Zqaart' not in txt)
    rows = [{'ref': 'A', 'pota': 'Foo Park', 'source': 'page', 'official': 'Foo Parkland', 'verdict': 'differs', 'pattern': 'x'},
            {'ref': 'A', 'pota': 'Foo Park', 'source': 'web address', 'official': 'fooparkland', 'verdict': 'differs', 'pattern': 'x'},
            {'ref': 'B', 'pota': 'Bar Park', 'source': 'page', 'official': 'Bar Land', 'verdict': 'differs', 'pattern': 'x'},
            {'ref': 'B', 'pota': 'Bar Park', 'source': 'record under pin', 'official': 'Bar Hill', 'verdict': 'differs', 'pattern': 'x'},
            {'ref': 'C', 'pota': 'Baz Park', 'source': 'page', 'official': 'Baz Land', 'verdict': 'differs', 'pattern': 'x'},
            {'ref': 'C', 'pota': 'Baz Park', 'source': 'record under pin', 'official': 'Baz Land', 'verdict': 'same', 'pattern': ''}]
    check('the two-sources rule alone: a page and a web address that write it alike (run together) count; unlike official names do not; a source that equals POTA does not',
          [x['ref'] for x in P.two_source_rows(rows, R)] == ['A'])

# ---- several states / US: one child process each, a parent folder, a summary, merged rows
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    repo, store, facts = make_world(t)
    wjson(store / 'US-ZX.layer-records.json.gz', json.load(gzip.open(store / 'US-ZZ.layer-records.json.gz', 'rt', encoding='utf-8')))   # a second, same-looking state
    wjson(repo / 'data' / 'pota' / 'saved' / 'parks' / 'US-ZX.json.gz', {'data': [{'reference': r} for r in json.load(gzip.open(facts, 'rt'))['parks']]})
    (store / 'NOTES.txt').write_text('x'); wjson(store / 'US-ZZZ.layer-records.json.gz', {})   # not states
    check('US (and ALL) pick exactly the states that have a layer file', P.parse_states(['US'], store)[:2] == (['ZX', 'ZY', 'ZZ'], True) and P.parse_states(['all'], store)[0] == ['ZX', 'ZY', 'ZZ'])
    check('typed states: commas and spaces both work, a repeat is dropped; one state is not "many"', P.parse_states(['zz, zx', 'ZZ'], store)[:2] == (['ZZ', 'ZX'], True) and P.parse_states(['ZZ'], store)[:2] == (['ZZ'], False))
    calls = []
    real_run = subprocess_run = P.subprocess.run

    class Done:
        def __init__(s, rc, out): s.returncode, s.stdout, s.stderr = rc, out, ''

    def fake(cmd, **kw):
        calls.append(cmd)
        st = cmd[cmd.index('--out') - 1]
        if st == 'ZY': return Done(1, 'Traceback: boom')
        with contextlib.redirect_stdout(io.StringIO()): rc, _ = P.run(st, store, facts, None, pathlib.Path(cmd[cmd.index('--out') + 1]), repo, flat=True)
        return Done(rc, '')
    P.subprocess.run = fake
    msgs = []
    out = t / 'out'
    try:
        before = {str(p.relative_to(t)) for p in t.rglob('*')}
        rc, parent = P.many(['ZZ', 'ZY', 'ZX', 'QQ'], 'ZZ-ZY-ZX-QQ', store, facts, repo, None, out, say=msgs.append)
    finally: P.subprocess.run = real_run
    new = {str(p.relative_to(t)) for p in t.rglob('*')} - before
    check('each state runs in its own child process, one after another (python -X utf8 <this file> <ST> --out <parent>/<ST> ... --flat)',
          len(calls) == 3 and all(c[0] == sys.executable and c[1:3] == ['-X', 'utf8'] and c[3].endswith('kpc_v2_state_prep.py') and '--flat' in c and c[c.index('--out') + 1].endswith(c[4]) for c in calls)
          and [c[4] for c in calls] == ['ZZ', 'ZY', 'ZX'])
    check('several states make one parent folder with a sub-folder per state holding the four usual files, and the four parent files',
          parent.parent == out and all((parent / s / f).is_file() for s in ('ZZ', 'ZX') for f in ('STATE-PREP-' + s + '.txt', 'proposed-rows.json', 'prep-details.csv', 'name-compare.csv'))
          and all((parent / f).is_file() for f in ('STATE-PREP-SUMMARY.txt', 'summary.csv', 'proposed-rows-all.json', 'name-patterns-all.csv')))
    check('nothing is written outside the new parent folder', all(n == 'out' or n.startswith('out/') for n in new) and all(n.startswith('out/' + parent.name) for n in new if n != 'out'))
    sm = (parent / 'STATE-PREP-SUMMARY.txt').read_text(encoding='utf-8').splitlines()
    check('a failing state (a crash; a missing layer file) does not stop the others and is named in the summary; exit code 1',
          rc == 1 and (parent / 'ZY' / 'prep-error.txt').is_file() and 'boom' in (parent / 'ZY' / 'prep-error.txt').read_text() and any(l.startswith('ZY  the prep stopped with an error, see ZY\\prep-error.txt') for l in sm)
          and any(l.startswith('QQ  the layer file was not found') for l in sm) and any(l.startswith('ZZ  can build') for l in sm) and any(l.startswith('ZX  can build') for l in sm))
    check('the summary starts with how many states v2 can build and how many it cannot; progress lines say "1 of 4  ZZ  N s"', sm[0] == 'v2 can build 2 of 4 states today.' and sm[1].startswith('v2 cannot build 0')
          and msgs[0].startswith('1 of 4  ZZ  ') and msgs[1].startswith('2 of 4  ZY  ') and msgs[3].startswith('4 of 4  QQ  '))
    al = json.load(open(parent / 'proposed-rows-all.json', encoding='utf-8'))
    ties = [r for r in al['id_ties'] if r['kind'] == 'ZZ unit id']
    check('an identical proposed row in two states appears once, with both states and the summed counts', len(ties) == 1 and sorted(ties[0]['states']) == ['ZX', 'ZZ'] and ties[0]['parks_hit'] == 50
          and set(ties[0]['measured_by_state']) == {'ZX', 'ZZ'})
    pc = list(csv.DictReader(open(parent / 'summary.csv', encoding='utf-8')))
    npc = list(csv.DictReader(open(parent / 'name-patterns-all.csv', encoding='utf-8')))
    check('summary.csv has one row per state with the numbers; name-patterns-all.csv sums the patterns over states, most common first',
          [r['state'] for r in pc] == ['ZZ', 'ZY', 'ZX', 'QQ'] and pc[0]['id_propose'] == '2' and pc[1]['problem'] and npc and npc[0]['states'] == '2'
          and [int(r['parks']) for r in npc] == sorted((int(r['parks']) for r in npc), reverse=True))
    # exit codes: nothing could run = 2
    P.subprocess.run = lambda cmd, **kw: Done(1, 'x')
    try: rc2, _ = P.many(['ZZ'], 'ZZ', store, facts, repo, None, t / 'out2', say=lambda m: None)
    finally: P.subprocess.run = real_run
    check('exit code 2 when no state could run', rc2 == 2)
    # the real child, once (a real process)
    with contextlib.redirect_stdout(io.StringIO()): rc3 = P.main(['ZZ', 'ZX', '--store', str(store), '--facts', str(facts), '--repo', str(repo), '--out', str(t / 'out3')])
    check('a real run of two states (real child processes) exits 0 and writes the summary', rc3 == 0 and list((t / 'out3').glob('v2-prep-ZZ-ZX-*/STATE-PREP-SUMMARY.txt')))
    with contextlib.redirect_stdout(io.StringIO()): rc4 = P.main(['ZZ', '--store', str(store), '--facts', str(facts), '--repo', str(repo), '--out', str(t / 'out4')])
    check('one state alone keeps its own folder name and files (v2-prep-ZZ-<time>\\STATE-PREP-ZZ.txt)', rc4 == 0 and list((t / 'out4').glob('v2-prep-ZZ-*/STATE-PREP-ZZ.txt')) and not list((t / 'out4').glob('**/STATE-PREP-SUMMARY.txt')))

# ---- Canada: CA-<XX> areas
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    repo, store, facts = make_world(t)
    shutil.copyfile(store / 'US-ZZ.layer-records.json.gz', store / 'CA-ZQ.layer-records.json.gz')
    shutil.copyfile(store / 'US-ZY.layer-records.json.gz', store / 'CA-ZR.layer-records.json.gz')
    shutil.copyfile(repo / 'data' / 'pota' / 'saved' / 'parks' / 'US-ZZ.json.gz', repo / 'data' / 'pota' / 'saved' / 'parks' / 'CA-ZQ.json.gz')
    check('CA picks only the Canadian areas with a layer file; US only the states; ALL both; CA-ZQ and US-ZZ typed in full are the same as typed short',
          P.parse_states(['CA'], store)[0] == ['CA-ZQ', 'CA-ZR'] and P.parse_states(['US'], store)[0] == ['ZY', 'ZZ'] and len(P.parse_states(['ALL'], store)[0]) == 4
          and P.parse_states(['CA-ZQ', 'US-ZZ'], store)[0] == ['CA-ZQ', 'ZZ'] and P.parse_states(['CA'], store)[2] == 'CA')
    with contextlib.redirect_stdout(io.StringIO()): rc, rep = P.run('CA-ZQ', store, facts, None, t / 'out', repo)
    txt = (rep / 'STATE-PREP-CA-ZQ.txt').read_text(encoding='utf-8')
    check('Canada: an area runs on its own layer file and park list (no neighbours): the same measurements, named by the area', rc == 0 and 'v2 can build CA-ZQ' in txt and 'PROPOSE 2' in txt and rep.name.startswith('v2-prep-CA-ZQ-'))
    with contextlib.redirect_stdout(io.StringIO()): rc, rep2 = P.run('CA-ZR', store, facts, None, t / 'out', repo)
    check('Canada: a layer that is not complete says "cannot build CA-ZR until"', 'v2 cannot build CA-ZR until: sgzzc' in (rep2 / 'STATE-PREP-CA-ZR.txt').read_text(encoding='utf-8'))
    with contextlib.redirect_stdout(io.StringIO()): rc, parent = P.many(['CA-ZQ', 'CA-ZR'], 'CA', store, facts, repo, None, t / 'out2', call=lambda st, sub, *a: (lambda r: (r[0], ''))(P.run(st, a[0], a[1], a[3], sub, a[2], flat=True)), say=lambda m: None)
    check('Canada: a CA run makes the parent v2-prep-CA-<time> with a folder per province', parent.name.startswith('v2-prep-CA-') and (parent / 'CA-ZQ' / 'STATE-PREP-CA-ZQ.txt').is_file() and 'CA-ZR  cannot build' in (parent / 'STATE-PREP-SUMMARY.txt').read_text(encoding='utf-8'))
    d_ = P.neighbour_areas(type('R', (), {'neighbours': {'CA-ON': ['CA-QC', 'US-NY'], 'MN': 'WI ND'}})(), 'CA-ON')
    check('neighbours: a Canadian area takes the rule table\'s list when A adds one (areas or letters); none until then; a US state gives US- areas',
          d_ == ['CA-QC', 'US-NY'] and P.neighbour_areas(type('R', (), {'neighbours': {'MN': 'WI ND'}})(), 'MN') == ['US-ND', 'US-WI'] and P.neighbour_areas(type('R', (), {'neighbours': {}})(), 'CA-ON') == [])

bat = (ROOT / 'tools' / 'pc-keys' / 'V2-STATE-PREP.bat').read_bytes() if (ROOT / 'tools' / 'pc-keys' / 'V2-STATE-PREP.bat').exists() else b''
check('the .bat has CRLF line ends, asks for the states, tries Python 3.12 first, has no pip step',
      b'\r\n' in bat and b'\n' not in bat.replace(b'\r\n', b'') and b'States (for example SC, or MN NY SC, or US for every state):' in bat and b'py -3.12' in bat and b'pip' not in bat and b'kpc_v2_state_prep.py' in bat)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
