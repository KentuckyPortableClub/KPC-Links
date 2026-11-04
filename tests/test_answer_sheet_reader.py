"""Answer-sheet reader tests (Nov 3, remade after Quality grade-answer-sheet R1-R5). Offline, no network.
Run from the KPC-Links root: python3 tests/test_answer_sheet_reader.py"""
import csv, datetime, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.github', 'scripts'))
import run_match_tests as T  # noqa: E402
import kpc_answer_words as AW  # noqa: E402

us = T._load('kpc_us_key.py', '\nidx = {}\n')
WHO = AW.persons(None)
COLS = ['ref', 'key_id', 'status', 'approved_by', 'approved_date', 'fp']


def sheet(rows):
    f = tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, newline='', encoding='utf-8')
    w = csv.DictWriter(f, COLS); w.writeheader()
    for r in rows: w.writerow(dict(zip(COLS, r)))
    f.close(); return f.name


def read(rows, appr='B', chk=None):
    us.SHEET_STAT.clear(); return us._sheet_rows(sheet(rows), appr, WHO, chk or {})


def test_shared_words():
    assert AW.word('yes') == ('YES', True) and AW.word("CAN'T TELL") == ('NOT SURE', True) and AW.word('can’t tell') == ('NOT SURE', True)
    assert AW.word('APPROVED') == ('YES', True) and AW.word('STALE') == ('NOT SURE', True) and AW.word('') == ('PROPOSED', True)
    assert AW.word('maybe?') == ('NOT SURE', False)
    assert [AW.use(w) for w in ('YES', 'NO', 'PIN', 'FIXED', 'NOT SURE', 'PROPOSED', 'typo')] == ['join', 'ignore', 'not sure', 'not sure', 'not sure', 'proposed', 'not sure']


def test_R1_every_status_word():
    ok = ('Brandon', '2026-11-01', '["Big Park", 100]')
    rows = [('US-1', '11', w) + ok for w in ('YES', 'APPROVED')] + [('US-2', '12', w) + ok for w in ("CAN'T TELL", 'NOT SURE', 'PIN', 'FIXED', 'STALE', 'whatever')]
    rows += [('US-3', '13', 'NO') + ok, ('US-4', '14', 'PROPOSED') + ok]
    S = read(rows)
    assert [r['st'] for r in S['US-1']] == ['OK', 'OK']
    assert [r['st'] for r in S['US-2']] == ['NOT SURE'] * 6, S['US-2']   # never "ignore" -> never a fallback to a guess
    assert 'US-3' not in S and 'US-4' not in S
    assert '13' in us.SHEET_NO.get('US-3', {})            # R5: the NO row is kept as a 'no' for that record
    assert us.SHEET_STAT.get('unknown status word: NOT SURE') == 1


def test_R2_sign_off_is_whole_names_and_a_date():
    fp = '["Big Park", 100]'
    bad = ['not Brandon', 'waiting for Brandon', 'Brandon (TEST ROW, not real)', 'Brandonx', '']
    for who in bad: assert not AW.signed_off(who, '2026-11-01', WHO), who
    assert AW.signed_off('Quality; Brandon', '2026-11-01', WHO) and AW.signed_off('kz4cp', '2026-11-01', WHO)
    assert not AW.signed_off('Brandon', '', WHO) and not AW.signed_off('Brandon', 'soon', WHO)
    future = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
    assert not AW.signed_off('Brandon', future, WHO)
    S = read([('US-1', '11', 'YES', w, '2026-11-01', fp) for w in bad] + [('US-1', '12', 'YES', 'Brandon', '', fp)])
    assert 'US-1' not in S
    assert 'US-1' in read([('US-1', '11', 'YES', 'Brandon (TEST ROW)', '2026-11-01', fp)], appr='A')   # option A: no person needed


def test_R3_bad_cells_hit_only_their_row():
    S = read([('US-1', '11', 'YES', 'Brandon', '2026-11-01', '"x"'), ('US-1', '12', 'YES', 'Brandon', '2026-11-01', '["X","12"]'),
              ('US-1', '13', 'YES', 'Brandon', '2026-11-01', '{bad json'), ('US-2', '21', 'YES', 'Brandon', '2026-11-01', '["Good", 50]')])
    assert [(r['id'], r['st']) for r in S['US-1']] == [('11', 'NOT SURE'), ('12', 'OK'), ('13', 'NOT SURE')]
    assert S['US-1'][1]['fp'] == ['X', 12.0]            # acres stored as a string become a number
    assert S['US-2'][0]['st'] == 'OK'                   # one bad row never switches the sheet off


def test_nightly_check_vanished_or_changed_is_not_sure():
    S = read([('US-1', '11', 'YES', 'Brandon', '2026-11-01', '["A", 1]'), ('US-1', '12', 'YES', 'Brandon', '2026-11-01', '["B", 1]')],
             chk={'US-1|11': {'state': 'VANISHED'}, 'US-1|12': {'state': 'OK'}})
    assert [r['st'] for r in S['US-1']] == ['NOT SURE', 'OK']


def test_R5_a_typed_NO_is_enforced():
    us.SHEET_NO.clear()
    read([('US-9', '77', 'NO', '', '', '["Wolf River Bottoms Wildlife Area", 120]'), ('US-9', '78', 'no', '', '', '"bad"')])
    ovr = {'US-9': {'join': ['5'], 'no': ['1']}}
    us._sheet_no_into(ovr, us.SHEET_NO)
    assert ovr['US-9']['no'] == ['1', '77', '78'] and ovr['US-9']['join'] == ['5']
    assert ovr['US-9']['nofp'] == {'77': ['Wolf River Bottoms Wildlife Area', 120.0]}
    a = {'OBJECTID': 77, 'Unit_Nm': 'Something Else', 'GIS_Acres': 3}
    assert us._sheet_no(ovr['US-9'], a)                   # the builder can no longer join record 77 by its own name match
    ovr2 = {}
    us._sheet_no_into(ovr2, {'US-8': {'5': None}})
    assert ovr2 == {'US-8': {'no': ['5']}}                # a park with no overrides entry gets one in memory
    us.SHEET_NO.clear()


def test_R4_no_by_name_beats_the_sheet_without_the_switch():
    a = {'OBJECTID': 5, 'Unit_Nm': 'Wolf River Bottoms Wildlife Area', 'GIS_Acres': 10}
    old = os.environ.get('KPC_NO_ALL_PATHS'); os.environ['KPC_NO_ALL_PATHS'] = '0'
    try:
        assert us._sheet_no({'no': ['Wolf River Bottoms Wildlife Area']}, a)
        assert us._sheet_no({'no': ['5']}, a)
        assert not us._sheet_no({'no': ['Other']}, a)
    finally:
        if old is None: os.environ.pop('KPC_NO_ALL_PATHS', None)
        else: os.environ['KPC_NO_ALL_PATHS'] = old


def test_switch_off_by_default():
    assert us.SHEET_MODE == (os.environ.get('KPC_ANSWER_SHEET') or 'off') and (us.SHEET == {} or us.SHEET_MODE != 'off')


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(f'{n} tests passed')
