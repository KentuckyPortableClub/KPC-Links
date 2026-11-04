#!/usr/bin/env python3
"""Offline test for .github/scripts/kpc_key_postcheck.py (Nov 4 2026). A tiny git repo in a temp folder with two 'Canada answer key'
builds and one 'World answer key' build. Checks: gained / lost / outline->pin / pin->outline / outline changed; CA-2218 and SE-0797
'must be pins' (NOT YET PIN, then PASS); 0,0 pin; pin outside the outline file (listed) vs 'edge' (counted only); a flat outline vs a
1-acre park; a person's signed sheet answer the key ignores (listed) vs a PROPOSED row and a fake sign-off (not); overrides 'no' still
joined (listed) vs an old 'join' a later 'no' replaced (not); no new build -> nothing written; a broken key file or no key never fails
(exit 0); only the report folder is written."""
import csv, json, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
TOOL = HERE / '.github/scripts/kpc_key_postcheck.py'
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def sh(root, *a): return subprocess.run(list(a), cwd=root, capture_output=True, text=True)
def wj(p, d): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(d, ensure_ascii=False))
def square(lo, la, d): return {'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Polygon', 'coordinates': [[[lo, la], [lo + d, la], [lo + d, la + d], [lo, la + d], [lo, la]]]}}


def run(root, **env):
    e = dict(os.environ, OUT_DIR='out', ANSWER_SHEET=str(root / 'sheet'), PRECHECK_OUT=str(root / 'pre'), KPC_PERSONS='Brandon,KZ4CP', **env)
    for k in ('PREV_REF', 'NEW_REF', 'FORCE', 'BUILD', 'FERS_DIR'):
        if k not in env: e.pop(k, None)
    return subprocess.run([sys.executable, str(TOOL)], cwd=root, env=e, capture_output=True, text=True)


with tempfile.TemporaryDirectory() as t:
    R = pathlib.Path(t)
    sh(R, 'git', 'init', '-q'); sh(R, 'git', 'config', 'user.email', 't@t'); sh(R, 'git', 'config', 'user.name', 't')
    OUT = lambda ref, nm: [[ref + '-id', nm, 100, 'reviewed']]   # noqa: E731
    old = {'CA-0001': {'n': 'Alpha PP', 'g': 'official', 'm': OUT('a', 'Alpha PP')},
           'CA-0002': {'n': 'Bravo PP', 'g': 'pin', 'm': []},
           'CA-0003': {'n': 'Charlie PP', 'g': 'official', 'm': OUT('c', 'Charlie PP')},
           'CA-0004': {'n': 'Delta PP', 'g': 'official', 'm': OUT('d', 'Delta PP')},
           'CA-0009': {'n': 'Lost PP', 'g': 'official', 'm': OUT('l', 'Lost PP')},
           'CA-2218': {'n': 'Rimouski', 'g': 'official', 'm': [['Québec Réser:n-Réserve faunique de Rimouski', 'Réserve faunique de Rimouski', 180344, 'reviewed']]}}
    wj(R / 'data/ca-key/CA-QC.json', {'parks': old}); wj(R / 'data/ca-key/index.json', {'build': 'CA-1', 'built': '2026-11-01 10:00 UTC'})
    wj(R / 'data/ca-key/overrides.json', {'parks': {}})
    wj(R / 'data/world-key/SE.json', {'parks': {'SE-0797': {'n': 'Kungsberget Nature Reserve', 'm': [[32410, '2000283 Kungsberget', 'EEA', 'name']]}}})
    wj(R / 'data/world-key/overrides.json', {'parks': {'SE-0797': {'no': ['32410', '2000283 Kungsberget'], 'none': True}}})
    sh(R, 'git', 'add', '-A'); sh(R, 'git', 'commit', '-qm', 'Canada answer key')
    sh(R, 'git', 'commit', '-q', '--allow-empty', '-m', 'unrelated')
    sh(R, 'git', 'add', '-A'); sh(R, 'git', 'commit', '-qm', 'World answer key', '--allow-empty')
    new = {'CA-0001': {'n': 'Alpha PP', 'g': 'pin', 'm': []},                                   # outline -> pin
           'CA-0002': {'n': 'Bravo PP', 'g': 'official', 'm': OUT('b', 'Bravo PP')},          # pin -> outline (pin inside: not listed)
           'CA-0003': {'n': 'Charlie PP', 'g': 'official', 'm': OUT('c2', 'Charlie PP')},     # outline changed; flat outline file
           'CA-0004': {'n': 'Delta PP', 'g': 'official', 'm': OUT('d', 'Delta PP'), 'far': 'edge'},   # pin just outside: edge
           'CA-0005': {'n': 'Echo PP', 'g': 'official', 'm': OUT('e', 'Echo PP')},            # gained; 0,0 pin; 1-acre park
           'CA-0006': {'n': 'Fox PP', 'g': 'official', 'm': OUT('f', 'Fox PP')},              # gained; pin outside, key says nothing
           'CA-0007': {'n': 'Golf PP', 'g': 'pin', 'm': []},                                 # overrides: an old join a later no replaced
           'CA-2218': old['CA-2218']}                                                          # still joined: NOT YET PIN
    wj(R / 'data/ca-key/CA-QC.json', {'parks': new}); wj(R / 'data/ca-key/index.json', {'build': 'CA-2', 'built': '2026-11-03 23:49 UTC'})
    wj(R / 'data/ca-key/overrides.json', {'parks': {'CA-2218': {'none': True, 'no': ['Québec Réser:n-Réserve faunique de Rimouski', 'Réserve faunique de Rimouski']},
                                                    'CA-0007': {'join': ['g-id'], 'no': ['g-id'], 'when': '2026-11-02'},
                                                    'CA-0004': {'no': ['d-id'], 'when': '2026-11-02'}}})
    wj(R / 'data/canada-bounds/CA-0002.json', square(-70, 46, .1))
    wj(R / 'data/canada-bounds/CA-0003.json', square(-70, 47, 1e-6))        # ~0.01 m2: flat
    wj(R / 'data/canada-bounds/CA-0004.json', square(-70, 48, .1))
    wj(R / 'data/canada-bounds/CA-0005.json', square(-70, 49, .0006))       # ~1 acre: NOT flat (the key rounds it to 0 acres)
    wj(R / 'data/canada-bounds/CA-0006.json', square(-70, 50, .1))
    wj(R / 'data/canada.json', {'rows': [['POTA', 'CA-0002', 'Bravo PP', 46.05, -69.95], ['POTA', 'CA-0004', 'Delta PP', 48.2, -69.95],
                                         ['POTA', 'CA-0005', 'Echo PP', 0, 0], ['POTA', 'CA-0006', 'Fox PP', 51.5, -69.95]]})
    (R / 'sheet').mkdir()
    cols = ['ref', 'pota_name', 'area', 'key_id', 'record_name', 'status', 'approved_by', 'approved_date']
    with open(R / 'sheet/CA.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, cols); w.writeheader()
        w.writerow({'ref': 'CA-0001', 'key_id': 'a-id', 'record_name': 'Alpha PP', 'status': 'YES', 'approved_by': 'Brandon', 'approved_date': '2026-11-02'})   # ignored by the key
        w.writerow({'ref': 'CA-0002', 'key_id': 'zzz', 'record_name': 'Other', 'status': 'PROPOSED'})                                                       # bot proposal: counted only
        w.writerow({'ref': 'CA-0003', 'key_id': 'c2-id', 'record_name': 'Charlie PP', 'status': 'NO', 'approved_by': 'Brandon (TEST ROW, not real)', 'approved_date': '2026-11-02'})
    (R / 'pre').mkdir()
    with open(R / 'pre/review-pile.csv', 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['park', 'area', 'name', 'type', 'outline', 'check', 'flags', 'why', 'joined ids', 'pota_lat', 'pota_lon', 'action'])
        w.writerow(['CA-0006', 'CA-QC', 'Fox PP', '', 'official', 'full', 'PIN_WAY_OUT', 'the POTA pin is well outside', 'f-id', '', '', 'HOLD: drop from the key until a person looks'])
        w.writerow(['CA-0003', 'CA-QC', 'Charlie PP', '', 'official', 'full', 'RULE18_PIECE', 'a piece name differs', 'c2-id', '', '', 'RULE 18: check the piece'])
    sh(R, 'git', 'add', '-A'); sh(R, 'git', 'commit', '-qm', 'Canada answer key')
    before = sh(R, 'git', 'status', '--porcelain').stdout

    p = run(R, KEY='ca')
    check(p.returncode == 0, f'exit 0 (got {p.returncode}; {p.stderr[-300:]})')
    files = sorted(x.name for x in (R / 'out').glob('*'))
    check(files == ['ca-CA-2.json', 'ca-CA-2.md', 'last-ca.json'], f'writes <key>-<build>.json/.md + last-ca.json: {files}')
    J = json.load(open(R / 'out/ca-CA-2.json')); c = J['changes']
    check(c['gained'] == ['CA-0005', 'CA-0006', 'CA-0007'] and c['lost'] == ['CA-0009'], f"gained {c['gained']} lost {c['lost']}")
    check(c['outline_to_pin'] == ['CA-0001'] and c['pin_to_outline'] == ['CA-0002'] and c['outline_changed'] == ['CA-0003'], f'outline<->pin and changed: {c}')
    mp = {x['park']: x['result'] for x in J['must_pin']}
    check(mp == {'CA-2218': 'NOT YET PIN', 'CA-2227': 'MISSING from the key'}, f'must-be-pins: {mp}')
    check([x['park'] for x in J['bad_pins']] == ['CA-0005'], f"0,0 pin listed: {J['bad_pins']}")
    po = {x['park'] for x in J['pins_outside']}
    check(po == {'CA-0006'} and J['pins_at_edge'] == ['CA-0004'], f"pin outside listed only for CA-0006, edge counted: {po} / {J['pins_at_edge']}")
    check([x['park'] for x in J['flat']] == ['CA-0003'], f"flat outline file listed, 1-acre park not: {J['flat']}")
    sd = J['answer_sheet']['signed_disagree']
    check([x['park'] for x in sd] == ['CA-0001'] and J['answer_sheet']['proposed_disagree'] == 1 and J['answer_sheet']['signed'] == 1,
          f"signed YES ignored by the key listed; PROPOSED counted; fake sign-off not a person: {sd} {J['answer_sheet']}")
    ov = {(x['park'], x['problem'][:20]) for x in J['overrides']}
    check(('CA-2218', "an id/name in overri") in ov and ('CA-0004', "an id/name in overri") in ov and not any(x[0] == 'CA-0007' for x in ov), f'overrides: {ov}')
    check(next(x for x in J['overrides'] if x['park'] == 'CA-0004')['newer_than_build'] is False, 'an override dated before the build is a real miss')
    check([x['park'] for x in J['precheck']['hold_still_outline']] == ['CA-0006'] and [x['park'] for x in J['precheck']['rule18']] == ['CA-0003'], 'pre-check HOLD + RULE 18 rows read')
    md = (R / 'out/ca-CA-2.md').read_text()
    check('NOT YET PIN' in md and '## Gained (3)' in md and 'never fails the build' in md, 'the .md has the sections')
    after = sh(R, 'git', 'status', '--porcelain').stdout
    check(after.replace('?? out/\n', '') == before, f'only out/ was written: {after!r}')

    p = run(R, KEY='ca')
    check(p.returncode == 0 and 'no new build' in p.stdout, 'second run on the same build: no new build, nothing written')
    p = run(R, WORKFLOW_NAME='KPC Canada answer key', FORCE='yes', BUILD='41739774609')
    check(p.returncode == 0 and (R / 'out/ca-CA-2.json').exists() and not (R / 'out/ca-run-41739774609.json').exists(), "WORKFLOW_NAME maps to the key; the key's own build stamp names the files")

    p = run(R, KEY='world', FORCE='yes', BUILD='777')
    check((R / 'out/world-run-777.json').exists(), 'no build stamp in the world index: the run id names the files')
    W = json.load(open(R / 'out' / json.load(open(R / 'out/last-world.json'))['report']))
    check([x['result'] for x in W['must_pin']] == ['NOT YET PIN'] and W['prev_ref'] == '', f"SE-0797 NOT YET PIN, no previous world build: {W['must_pin']}")

    new['CA-2218'] = {'n': 'Rimouski', 'g': 'pin', 'm': []}
    wj(R / 'data/ca-key/CA-QC.json', {'parks': new}); wj(R / 'data/ca-key/index.json', {'build': 'CA-3', 'built': '2026-11-05 01:00 UTC'})
    sh(R, 'git', 'add', 'data'); sh(R, 'git', 'commit', '-qm', 'Canada answer key')
    p = run(R, KEY='ca')
    J3 = json.load(open(R / 'out/ca-CA-3.json'))
    check({x['park']: x['result'] for x in J3['must_pin']}['CA-2218'] == 'PASS (pin)' and J3['changes']['outline_to_pin'] == ['CA-2218'], 'after a rebuild CA-2218 is PASS (pin) and shows as outline -> pin')

    (R / 'data/ca-key/CA-QC.json').write_text('{broken')
    p = run(R, KEY='ca', FORCE='yes', BUILD='broken')
    check(p.returncode == 0, 'a broken key file never fails the build (exit 0)')
    p = run(R)
    check(p.returncode == 0 and 'nothing checked' in p.stdout, 'no key given: exit 0 with a warning')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
