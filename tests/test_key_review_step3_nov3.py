#!/usr/bin/env python3
"""Nov 3 step 3 (code review of the key builders against the proposed rules): offline checks, no network.
- kpc_host_pace: two requests to one host are at least 2 s apart; other hosts are not held up; KPC_HOST_GAP never goes below 2.
- kpc_key_answers KPC_ANSWERS_TO=sheet: a checker YES / NO becomes an answer-sheet row, overrides.json is not touched, the
  newest answer for a (park, record) wins (rules sort conflict 1, proposed rule 21).
- kpc_key_rules.piece_ok: the record layer's own type phrase ('Land Use Zone' on Alberta's PLUZ layer, CA-6125) is not a piece.
Run: python3 tests/test_key_review_step3_nov3.py"""
import csv, json, os, pathlib, subprocess, sys, tempfile, time, urllib.request
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
ok = True
def check(c, label):
    global ok
    print(('ok   ' if c else 'FAIL ') + label); ok = ok and bool(c)

# 1. host pacing (urlopen replaced by a stub BEFORE install, so nothing goes to the network)
calls = []
urllib.request.urlopen = lambda req, *a, **k: calls.append((req, time.monotonic()))
os.environ['KPC_HOST_GAP'] = '0.5'
import kpc_host_pace as HP
check(HP.GAP == 2.0, 'KPC_HOST_GAP=0.5 is raised to 2.0 s')
HP.GAP = 0.3   # test only: a short gap so the test is quick; the logic is the same
HP.install()
urllib.request.urlopen('https://a.example/x'); urllib.request.urlopen('https://b.example/x'); urllib.request.urlopen('https://a.example/y')
t = [c[1] for c in calls]
check(t[1] - t[0] < 0.2, 'another host is not held up')
check(t[2] - t[0] >= 0.29, 'the same host waits the full gap')
HP.install(); check(len(calls) == 3, 'install() twice wraps only once')

# 2. kpc_key_answers sheet mode
with tempfile.TemporaryDirectory() as t:
    k = pathlib.Path(t, 'key'); k.mkdir(); d = pathlib.Path(t, 'data/data/waiting/questions'); d.mkdir(parents=True)
    ovr = {'parks': {'US-1': {'join': ['111'], 'why': 'hand'}}}
    (k / 'overrides.json').write_text(json.dumps(ovr))
    (d / 'gis-hunter.json').write_text(json.dumps({'questions': [
        {'ref': 'US-1', 'record': 222, 'record_name': 'Alpha WMA', 'acres': 50, 'answer': 'YES', 'area': 'US-DE'},
        {'ref': 'US-2', 'record': 333, 'record_name': 'Beta Forest', 'acres': 9, 'answer': 'NO', 'area': 'US-DE'},
        {'ref': 'US-2', 'record': 333, 'record_name': 'Beta Forest', 'acres': 9, 'answer': 'YES', 'area': 'US-DE'},
        {'ref': 'US-3', 'record': 444, 'record_name': 'Gamma', 'answer': 'NOT SURE', 'area': 'US-DE'}]}))
    env = dict(os.environ, KEY_DIR=str(k), DATA=str(pathlib.Path(t, 'data')), KPC_ANSWERS_TO='sheet')
    r = subprocess.run([sys.executable, str(HERE / '.github/scripts/kpc_key_answers.py')], env=env, capture_output=True, text=True, cwd=t)
    check(json.loads((k / 'overrides.json').read_text()) == ovr, 'sheet mode: overrides.json is not touched')
    rows = list(csv.DictReader(open(k / 'answers-for-sheet.csv', encoding='utf-8'))) if (k / 'answers-for-sheet.csv').exists() else []
    by = {(x['ref'], x['key_id']): x for x in rows}
    check(len(rows) == 2, 'sheet mode: one row per answered (park, record); NOT SURE writes nothing')
    check(by.get(('US-1', '222'), {}).get('status') == 'YES' and by[('US-1', '222')]['approved_by'] == '', 'a checker YES is a row, not signed')
    check(by.get(('US-2', '333'), {}).get('status') == 'YES', 'the newest answer in a file wins')
    if not ok: print(r.stdout[-800:], r.stderr[-800:])

# 2b. Nov 3 guard (Brandon Q6, relayed by Super 6:52 PM CST): a bot's answer never changes a park a person already answered
with tempfile.TemporaryDirectory() as t:
    k = pathlib.Path(t, 'key'); k.mkdir(); d = pathlib.Path(t, 'data/data/waiting/questions'); d.mkdir(parents=True)
    ovr = {'parks': {
        'US-4118': {'join': ['sgild9'], 'no': ['sgila1404'], 'why': "2026-10-29 23:15: gis-hunter row NO 'Pere Marquette State Park' (chat 11 (Oct 29-30); applied by kpc_key_answers)"},
        'US-11217': {'none': True, 'why': 'a different place, not this park; no outline of its own on file (hand review Oct 22 (waiting list))'},
        'US-6': {'join': ['666']},
        'US-7': {'join': ['777'], 'why': "2026-11-03 12:26: layers row YES 'Seven' (auto (T1 map-match STRONG); applied by kpc_key_answers)"},
        # addendum (Super relayed Brandon 7:11-7:12 PM CST, item 4): Mapping's own notes / calls are never a person's answer
        'US-9': {'no': ['999'], 'why': "2026-11-03: NO 999: zero-area shape (Mapping, Nov 3 (sampled by Quality 12/12 A+B); remade on fresh main)"},
        'US-10': {'join': ['1010'], 'why': "PROPOSED Nov 3 2026 (Mapping addendum, for Quality to grade): same place"}}}
    (k / 'overrides.json').write_text(json.dumps(ovr))
    A = 'auto (T1 map-match STRONG)'
    (d / 'gis-hunter.json').write_text(json.dumps({'questions': [
        {'ref': 'US-4118', 'record': 'sgila1404', 'record_name': 'Pere Marquette', 'acres': 8000, 'answer': 'YES', 'area': 'US-IL', 'checked_by': A},
        {'ref': 'US-11217', 'record': 'sgmtd2999', 'record_name': 'Bluewater Springs Trout Hatchery', 'acres': 50, 'answer': 'YES', 'area': 'US-MT', 'checked_by': A},
        {'ref': 'US-6', 'record': '666', 'record_name': 'Six', 'acres': 6, 'answer': 'NO', 'area': 'US-DE', 'auto': True},
        {'ref': 'US-7', 'record': '778', 'record_name': 'Seven B', 'acres': 7, 'answer': 'YES', 'area': 'US-DE', 'checked_by': A},
        {'ref': 'US-8', 'record': '888', 'record_name': 'Eight', 'acres': 8, 'answer': 'YES', 'area': 'US-DE', 'checked_by': A},
        {'ref': 'US-6', 'record': '667', 'record_name': 'Six B', 'acres': 6, 'answer': 'YES', 'area': 'US-DE', 'checked_by': 'chat 11'},
        {'ref': 'US-9', 'record': '9999', 'record_name': 'Nine B', 'acres': 9, 'answer': 'YES', 'area': 'US-DE', 'checked_by': A},
        {'ref': 'US-10', 'record': '1011', 'record_name': 'Ten B', 'acres': 10, 'answer': 'YES', 'area': 'US-DE', 'checked_by': A}]}))
    env = dict(os.environ, KEY_DIR=str(k), DATA=str(pathlib.Path(t, 'data')), KPC_ANSWERS_TO='overrides')
    r = subprocess.run([sys.executable, str(HERE / '.github/scripts/kpc_key_answers.py')], env=env, capture_output=True, text=True, cwd=t)
    P = json.loads((k / 'overrides.json').read_text())['parks']
    check('sgila1404' in P['US-4118']['no'] and 'sgila1404' not in P['US-4118'].get('join', []), 'guard: a bot YES does not overturn a NO on US-4118')
    check(P['US-11217'].get('none') and not P['US-11217'].get('join'), "guard: a bot YES does not replace a hand review's 'none' (US-11217)")
    check('666' in P['US-6']['join'] and '667' in P['US-6']['join'], "guard: a bot NO does not remove a person's join; a person's (chat 11) YES still applies")
    check('778' in P['US-7']['join'], 'a park that only a bot answered can still take a bot answer')
    check('888' in (P.get('US-8') or {}).get('join', []), 'a blank park still takes a bot YES (Oct 31 "wire them")')
    check('bot (auto) answers NOT applied' in r.stdout, 'the run summary lists the bot answers it held back')
    check('9999' in P['US-9'].get('join', []) and '1011' in P['US-10']['join'], "guard: a park with only Mapping's notes / calls is not a person's answer, so a bot answer still applies (addendum item 4)")
    sys.path.insert(0, str(HERE / '.github/scripts'))
    import importlib.util as _iu
    _ka = _iu.spec_from_file_location('ka', HERE / '.github/scripts/kpc_key_answers.py'); KA = _iu.module_from_spec(_ka); _ka.loader.exec_module(KA)
    _pc = _iu.spec_from_file_location('pcx', HERE / '.github/scripts/kpc_precheck.py'); PCX = _iu.module_from_spec(_pc); _pc.loader.exec_module(PCX)
    check(not KA.has_person_answer({'join': ['1'], 'why': "x (Mapping, Nov 3); y: Mapping's call"}) and KA.has_person_answer({'join': ['1'], 'why': 'Brandon: YES (Mapping found the record)'})
          and KA.has_person_answer({'join': ['1'], 'why': 'Oct 22 review · 2026-11-03: NO 2 (Mapping, Nov 3)'}), "has_person_answer: Mapping's own notes never count; a person's note next to them still does")
    check(KA.DESK_RX.pattern == PCX.DESK.pattern, 'the guard and the pre-check use the same Mapping-desk words')
    if not ok: print(r.stdout[-800:], r.stderr[-800:])

# 3. rule 18 and the layer's own type word
import kpc_key_rules as KR
check(KR.piece_ok('Porcupine Hills Public Land Use Zone', 'Porcupine Hills', None, 'Alberta Public Land Use Zones')[0], "CA-6125: 'zone' on the PLUZ layer is not a piece")
check(not KR.piece_ok('Las Palomas WMA Anacua Unit', 'Las Palomas WMA', None, 'Wildlife Management Units')[0], "'Anacua Unit' stays a piece on a '... Units' layer")
check(not KR.piece_ok('Salinas Pueblo Missions, Abo Unit National Monument', 'Salinas Pueblo Missions National Monument')[0], 'Abo Unit is still refused')

# 4. a NO fingerprint stays inside its own layer (US-7896) and never beats a person's join by id
ov7896 = {'fp': {'sggab59': ['Standing Boy Creek State Park', 1579]}, 'join': ['sggab59'], 'no': ['195158'],
          'nofp': {'195158': ['Standing Boy Creek State Park', 1582.3]}}
check(not KR.is_no(ov7896, 'sggab59', 'Standing Boy Creek State Park', 1579, by_name=True), "US-7896: the NO on PAD-US 195158 does not knock out the state's sggab59")
check(KR.is_no(ov7896, '201234', 'Standing Boy Creek State Park', 1580, by_name=True), 'a renumbered PAD-US copy of 195158 is still NO')
check(KR.is_no(ov7896, '195158', 'x', 0), 'the NO id itself is NO')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
