#!/usr/bin/env python3
"""Nov 19 (job C, N1 + N3; KPC owner, 2026-11-19): the Release guard refuses a US state in the cases the outside review found silent.
N1 (finding F1): three made-up outlines must each refuse the state, with the reason in plain words:
  1. an outline with no real record id, only row numbers (row219)
  2. an outline that shares no id with the records the key joined
  3. a short outline that misses a key record with a different name (a missing piece with the SAME name still passes)
N3: one test each:
  1. an outline sits in a state's file whose key does not list the park (another state's key does): refused
  2. an outline made by name + pin refuses unless a person approved it on the named list (.github/release-name-pin-approved.json)
  3. the park on kpc_release.MUST_FIX_FIRST refuses its state until it is fixed (the key no longer joins the bad record and the
     outline does not hold it) or held (the key grades it PIN, no outline ships)
And the wiring: outline_refuse_why (why_not_promote, build) and trim_built_outlines (release) both refuse. Refuse only: nothing is
rebuilt. Made-up parks only (US-999xx), temp folders only, offline. No rules file is touched.
"""
import json, pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M
import kpc_release as R

ok = True
def check(name, cond, extra=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + (f'  [{str(extra)[:500]}]' if extra and not cond else ''))
    ok = ok and bool(cond)

SQ = {'type': 'Polygon', 'coordinates': [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}
def rec(ref, ids, via='key', g='official'):
    return M.make_record(ref, ref, g, SQ, 'agency', 'file:US-ZZ.json.gz', ids, 10, '2026-11-19', '', via)
def keyfile(kd, st, parks):
    kd.mkdir(parents=True, exist_ok=True)
    (kd / f'{st}.json').write_text(json.dumps({'parks': parks}))
def probs(st, recs, kd, approved=None):
    recs, _, _ = M.key_fix(st, recs, kd)
    return R.us_release_guard_problems(st, recs, kd, approved=approved or {})
def has(ps, ref, words): return any(p.startswith(ref + ':') and words in p for p in ps)

# ------------------------------------------------------------------ N1: the three blind spots
with tempfile.TemporaryDirectory() as t:
    kd = pathlib.Path(t) / 'us-key'
    keyfile(kd, 'US-KY', {
        'US-99901': {'g': 'official', 'n': 'Clean Lake', 'm': [['a1', 'Clean Lake', 10, 'name'], ['a2', 'Clean Lake', 5, 'name']]},
        'US-99902': {'g': 'official', 'n': 'Row Woods', 'm': [['b1', 'Row Woods', 10, 'name']]},
        'US-99903': {'g': 'official', 'n': 'Other Forest', 'm': [[2658, 'Other Forest', 10, 'reviewed']]},
        'US-99904': {'g': 'official', 'n': 'Short Park', 'm': [['d1', 'Short Park', 10, 'name'], ['d2', 'Short Park Annex', 4, 'name']]},
        'US-99905': {'g': 'official', 'n': 'Two Piece', 'm': [['e1', 'Two Piece', 10, 'name'], ['e2', 'Two Piece', 4, 'name']]},
        'US-99915': {'g': 'official', 'n': 'Twin Park', 'm': [['t1', 'Twin Park', 10, 'name'], ['t2', 'TWIN  park', 4, 'name']]},   # Fable, 20 Nov
        'US-99906': {'g': 'official', 'n': 'Line Trail', 'm': [['trl99906', 'Line Trail', 0, 'official trail line']]},
    })
    clean = {'US-99901': rec('US-99901', ['a1', 'a2'])}
    check('control: an outline built from exactly the key records passes', probs('US-KY', clean, kd) == [], probs('US-KY', clean, kd))

    p = probs('US-KY', {'US-99902': rec('US-99902', ['row219'], via='key')}, kd)
    check('N1 case 1: a row-only outline (row219) refuses, in plain words', has(p, 'US-99902', 'only row numbers (row219)') and len(p) == 1, p)
    check('N1 case 1: before this change the held-record check said nothing about it',
          M.held_record_refs('US-KY', {'US-99902': rec('US-99902', ['row219'])}, kd) == {})

    p = probs('US-KY', {'US-99903': rec('US-99903', ['sgmtd744'])}, kd)
    check('N1 case 2: an outline that shares no id with the key (holds sgmtd744, key joined 2658) refuses',
          has(p, 'US-99903', 'shares no record id with the 1 record(s) the US-KY key joined (it holds sgmtd744)'), p)
    check('N1 case 2: before this change the held-record check said nothing about it',
          M.held_record_refs('US-KY', {'US-99903': rec('US-99903', ['sgmtd744'])}, kd) == {})
    p = probs('US-KY', {'US-99903': rec('US-99903', ['trl99903'])}, kd)
    check('N1 case 2: an outline with only a trail id while the key joined land records refuses too', has(p, 'US-99903', 'shares no record id'), p)

    p = probs('US-KY', {'US-99906': rec('US-99906', ['3552'])}, kd)
    check('N1 case 2: a land outline for a park the key joined only as a trail line refuses',
          has(p, 'US-99906', 'which joined only a trail line (no land record) (it holds 3552)'), p)
    check('N1 case 2 control: the trail outline itself (trl id) for that park passes', probs('US-KY', {'US-99906': rec('US-99906', ['trl99906'])}, kd) == [])

    p = probs('US-KY', {'US-99904': rec('US-99904', ['d1'])}, kd)
    check('N1 case 3: a short outline that misses a different-named record (d2 Short Park Annex) refuses',
          has(p, 'US-99904', 'holds 1 of the key\'s 2 records and misses d2 (Short Park Annex)'), p)
    p = probs('US-KY', {'US-99905': rec('US-99905', ['e1'])}, kd)
    check('N1 case 3 control: a short outline whose missing piece has the same name as a piece it holds passes', p == [], p)
    p = probs('US-KY', {'US-99915': rec('US-99915', ['t1'])}, kd)
    check('N1 case 3 control: a missing twin whose name differs only in letter case or spacing passes (Fable, 20 Nov)', p == [], p)

# ------------------------------------------------------------------ N3 item 1: only in the file of a state whose key lists the park
with tempfile.TemporaryDirectory() as t:
    kd = pathlib.Path(t) / 'us-key'
    keyfile(kd, 'US-KY', {'US-99911': {'g': 'official', 'n': 'Home Park', 'm': [['k1', 'Home Park', 1, 'name']]}})
    keyfile(kd, 'US-TN', {'US-99912': {'g': 'official', 'n': 'Neighbour Park', 'm': [['t1', 'Neighbour Park', 1, 'name']]}})
    recs = {'US-99911': rec('US-99911', ['k1']), 'US-99912': rec('US-99912', ['t1'])}
    kept, drop, _ = M.key_fix('US-KY', recs, kd)
    check('N3 item 1: the trim keeps a park another state\'s key lists (so the release must catch it)', 'US-99912' in kept and not drop)
    p = probs('US-KY', recs, kd)
    check('N3 item 1: an outline in US-KY\'s file whose park only US-TN\'s key lists refuses US-KY',
          has(p, 'US-99912', 'sits in the US-KY file, but the US-KY key does not list it') and not has(p, 'US-99911', ''), p)
    check('N3 item 1: the same outline in US-TN\'s own file passes', probs('US-TN', {'US-99912': rec('US-99912', ['t1'])}, kd) == [])

# ------------------------------------------------------------------ N3 item 2: name+pin only on the approved list
with tempfile.TemporaryDirectory() as t:
    kd = pathlib.Path(t) / 'us-key'
    keyfile(kd, 'US-KY', {'US-99921': {'g': 'official', 'n': 'Pin Park', 'm': [['p1', 'Pin Park', 1, 'name']]}})
    recs = {'US-99921': rec('US-99921', ['p1'], via='name+pin')}
    p = probs('US-KY', recs, kd)
    check('N3 item 2: a name+pin outline that is not on the approved list refuses (even when its ids agree)',
          has(p, 'US-99921', 'made by name + pin (via name+pin) and not on the approved name+pin list') and len(p) == 1, p)
    lst = pathlib.Path(t) / 'approved.json'
    good = {'reason': 'checked against the official map', 'approved_by': 'Brandon (KZ4CP)', 'approved_date': '2026-11-19'}
    lst.write_text(json.dumps({'approved': {'US-KY': {'US-99921': good}}}))
    appr = R.load_name_pin_approved(path=lst)
    check('N3 item 2: listed by a person (Brandon (KZ4CP)) with a reason and a date, it passes', probs('US-KY', recs, kd, appr) == [], appr)
    for label, bad in (('a Quality note', dict(good, approved_by='Quality')), ('a bot', dict(good, approved_by='KPC owner bot')),
                       ('a forged display name', dict(good, approved_by='not Brandon (KZ4CP)')),
                       ('an invalid date', dict(good, approved_date='2026-02-31')), ('a future date', dict(good, approved_date='2999-01-01')),
                       ('no reason', dict(good, reason='')), ('no date', dict(good, approved_date='')),
                       ('another state', None)):
        body = {'US-TN': {'US-99921': good}} if bad is None else {'US-KY': {'US-99921': bad}}
        lst.write_text(json.dumps({'approved': body}))
        check(f'N3 item 2: an entry with {label} does not count (still refused)',
              has(probs('US-KY', recs, kd, R.load_name_pin_approved(path=lst)), 'US-99921', 'via name+pin'))
    check('N3 item 2: a missing list file = an empty list (fail closed)', R.load_name_pin_approved(path=pathlib.Path(t) / 'none.json') == {})
    shipped = json.loads((ROOT / R.NAME_PIN_APPROVED_AT).read_text(encoding='utf-8'))
    check('N3 item 2: the shipped list is empty: nobody has approved a name+pin outline yet', shipped.get('approved') == {}, shipped)

# ------------------------------------------------------------------ N3 item 3: the must-fix park is fixed or held first
ref, (st, bad, _why) = sorted(R.MUST_FIX_FIRST.items())[0]
with tempfile.TemporaryDirectory() as t:
    kd = pathlib.Path(t) / 'us-key'
    good_id = 'sgx1'
    def nv(m, g='official'): keyfile(kd, st, {ref: {'g': g, 'n': 'Must Fix Park', 'm': m}})
    nv([[bad[0], 'Wrong Big Area', 9, 'name'], [good_id, 'Must Fix Park', 1, 'name']])
    p = probs(st, {ref: rec(ref, [bad[0], good_id])}, kd)
    check(f'N3 item 3: the must-fix park refuses {st} while the key joins the bad record and the outline holds it',
          has(p, ref, f'must be fixed or held before {st} is released') and 'the key still joins' in ' '.join(p) and 'the outline still holds' in ' '.join(p), p)
    nv([[good_id, 'Must Fix Park', 1, 'name']])
    check(f'N3 item 3: fixed (the key no longer joins it, the outline does not hold it) = {st} passes',
          probs(st, {ref: rec(ref, [good_id])}, kd) == [])
    nv([[good_id, 'Must Fix Park', 1, 'name']])
    p = probs(st, {ref: rec(ref, [bad[0], good_id])}, kd)
    check('N3 item 3: a fixed key with an old outline that still holds the bad record still refuses', has(p, ref, 'the outline still holds'), p)
    nv([[bad[0], 'Wrong Big Area', 9, 'name']], g='pin')
    check(f'N3 item 3: held (the key grades it PIN, the trim drops the outline) = {st} passes', probs(st, {ref: rec(ref, [bad[0]])}, kd) == [])
    check('N3 item 3: another state is not touched by it', R.us_release_guard_problems('US-KY', {}, kd) == [])

# ------------------------------------------------------------------ wiring: outline_refuse_why + trim_built_outlines refuse
def sh(d, *a): return subprocess.run(a, cwd=d, capture_output=True, text=True)
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t)
    sh(d, 'git', 'init', '-q'); sh(d, 'git', 'config', 'user.name', 't'); sh(d, 'git', 'config', 'user.email', 't@t')
    keyfile(d / 'data/us-key', 'US-KY', {'US-99902': {'g': 'official', 'n': 'Row Woods', 'm': [['b1', 'Row Woods', 10, 'name']]}})
    keyfile(d / 'data/us-key', 'US-OH', {'US-99931': {'g': 'official', 'n': 'Fine Park', 'm': [['o1', 'Fine Park', 1, 'name']]}})
    M.save_area('US-KY', {'US-99902': rec('US-99902', ['row219'])}, d / 'data/outlines', key_dir=d / 'data/us-key')
    M.save_area('US-OH', {'US-99931': rec('US-99931', ['o1'])}, d / 'data/outlines', key_dir=d / 'data/us-key')
    sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', 'c')
    sha = sh(d, 'git', 'rev-parse', 'HEAD').stdout.strip()
    why = R.outline_refuse_why(d, 'US', 'US-KY', sha)
    check('wiring: outline_refuse_why refuses the state with the row-only outline, in plain words',
          why.startswith('US-KY: refused by the release guards, 1 outline problem(s): US-99902: the outline has no real record id'), why)
    check('wiring: a clean neighbour (US-OH) is not blocked by it', R.outline_refuse_why(d, 'US', 'US-OH', sha) == '')
    check('wiring: build() refuses to pack the refused state (build_source_refuse_why)',
          'refused by the release guards' in R.build_source_refuse_why(d, 'US', sha, units=['US-KY']))
    built = {'outlines/US-KY.geojson.gz': [('outlines/US-KY.geojson.gz', b'')]}
    try: R.trim_built_outlines(d, sha, built, units=['US-KY']); raised = ''
    except R.ReleaseError as e: raised = str(e)
    check('wiring: trim_built_outlines (the release step) raises the same refusal', 'refused by the release guards' in raised, raised)

# ------------------------------------------------------------------ no rules hash moves
import kpc_key_freeze as KF
rule_files = {f for v in KF.RULE_FILES.values() for f in v}
check('no rules file: kpc_release.py and the approved list are not rule files of any key or the 2-fers',
      '.github/scripts/kpc_release.py' not in rule_files and R.NAME_PIN_APPROVED_AT not in rule_files)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
